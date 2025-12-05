"""
Fetch BLS Average Price Data for the South region.

Average Price Data shows actual average prices of specific items (e.g., 
"bread per lb", "milk per gallon") rather than index values.

Series ID format: APU[area][item_code]
- APU = Average Price Urban
- Area codes: 0000 = U.S. City Average, 0100 = Northeast, 0200 = Midwest, 
               0300 = South, 0400 = West
- Item codes identify specific products

Reference: https://data.bls.gov/PDQWeb/ap
"""

import requests
import pandas as pd
from pathlib import Path
import json
import time
from typing import List, Dict, Optional

# BLS API endpoint (same as CPI API)
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# South region code
SOUTH_REGION = "0300"

# Common Average Price series IDs for South region
# Format: APU0300[item_code]
# You can find more series IDs at: https://data.bls.gov/PDQWeb/ap
AVERAGE_PRICE_SERIES = {
    # Food items
    "Bread, white, per lb": "APU0300701111",  # Bread, white, per lb (South)
    "Milk, whole, per gallon": "APU0300702111",  # Milk, whole, per gallon (South)
    "Eggs, grade A, large, per doz": "APU0300703111",  # Eggs, grade A, large, per doz (South)
    "Ground beef, 100% beef, per lb": "APU0300704111",  # Ground beef, per lb (South)
    "Chicken breast, boneless, per lb": "APU0300705111",  # Chicken breast, per lb (South)
    "Coffee, 100%, ground roast, per lb": "APU0300706111",  # Coffee, per lb (South)
    "Bananas, per lb": "APU0300707111",  # Bananas, per lb (South)
    "Orange juice, frozen concentrate, per 16 oz": "APU0300708111",  # Orange juice (South)
    
    # Personal care items
    "Toothpaste, standard tube, per 6.4 oz": "APU0300711111",  # Toothpaste (South)
    "Shampoo, per 15 oz": "APU0300712111",  # Shampoo (South)
    "Soap, bar, per 3.5 oz": "APU0300713111",  # Soap, bar (South)
    
    # Note: These are example series IDs. You'll need to find the exact 
    # series IDs for items that match your commissary items.
}

def fetch_average_price_data(
    series_ids: List[str],
    api_key: Optional[str] = None,
    start_year: int = 2019,
    end_year: int = 2025
) -> Optional[pd.DataFrame]:
    """
    Fetch Average Price Data from BLS API.
    
    Args:
        series_ids: List of BLS series IDs (e.g., ["APU0300701111"])
        api_key: BLS API key (optional, but recommended)
        start_year: Start year for data
        end_year: End year for data
    
    Returns:
        DataFrame with columns: year, month, series_id, item_name, value, period
    """
    all_data = []
    
    # BLS API allows up to 50 series per request
    # Split into batches if needed
    batch_size = 50
    series_batches = [
        series_ids[i:i + batch_size] 
        for i in range(0, len(series_ids), batch_size)
    ]
    
    headers = {
        "Content-Type": "application/json"
    }
    
    for batch_idx, batch in enumerate(series_batches):
        print(f"Fetching batch {batch_idx + 1}/{len(series_batches)} ({len(batch)} series)...")
        
        payload = {
            "seriesid": batch,
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        
        if api_key:
            payload["registrationkey"] = api_key
        
        try:
            response = requests.post(BLS_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "REQUEST_SUCCEEDED":
                results = data.get("Results", {}).get("series", [])
                
                for series in results:
                    series_id = series.get("seriesID")
                    # Find item name if we have it in our mapping
                    item_name = None
                    for name, sid in AVERAGE_PRICE_SERIES.items():
                        if sid == series_id:
                            item_name = name
                            break
                    
                    # Extract monthly data
                    monthly_data = series.get("data", [])
                    
                    for month_data in monthly_data:
                        year = int(month_data.get("year"))
                        period = month_data.get("period")  # e.g., "M01" for January
                        value = month_data.get("value")
                        
                        # Skip if value is not available
                        if value and value != "-":
                            try:
                                price_value = float(value)
                                all_data.append({
                                    "year": year,
                                    "period": period,
                                    "month": period_to_month(period),
                                    "series_id": series_id,
                                    "item_name": item_name or series_id,
                                    "value": price_value
                                })
                            except (ValueError, TypeError):
                                continue
                
                print(f"  Successfully fetched {len([d for d in all_data if d['series_id'] in batch])} data points")
                
                # Rate limiting: wait between batches
                if batch_idx < len(series_batches) - 1:
                    time.sleep(0.5)
                    
            else:
                error_msg = data.get("message", ["Unknown error"])
                if isinstance(error_msg, list):
                    error_msg = error_msg[0]
                print(f"  API Error: {error_msg}")
                if "registrationkey" in str(error_msg).lower() or "key" in str(error_msg).lower():
                    print("  Note: BLS API key is recommended. Register at: https://www.bls.gov/developers/api_signature.htm")
                continue
                
        except requests.exceptions.RequestException as e:
            print(f"  Request error: {e}")
            continue
        except Exception as e:
            print(f"  Error processing batch: {e}")
            continue
    
    if not all_data:
        print("No data retrieved")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    df = df.sort_values(["series_id", "year", "period"])
    
    return df

def period_to_month(period: str) -> int:
    """Convert BLS period code (e.g., 'M01') to month number (1-12)."""
    if period.startswith("M"):
        try:
            return int(period[1:])
        except ValueError:
            return None
    return None

def find_series_ids_for_items(item_names: List[str], region: str = "0300") -> Dict[str, str]:
    """
    Helper function to find series IDs for specific items.
    
    Note: This requires manual lookup or web scraping from BLS website.
    The BLS doesn't provide a search API, so you'll need to:
    1. Visit https://data.bls.gov/PDQWeb/ap
    2. Search for items manually
    3. Extract series IDs from the results
    
    Args:
        item_names: List of item names to search for
        region: Region code (0300 = South)
    
    Returns:
        Dictionary mapping item names to series IDs
    """
    print("\n" + "="*60)
    print("FINDING SERIES IDs")
    print("="*60)
    print("\nNote: BLS doesn't provide a programmatic way to search for series IDs.")
    print("You'll need to manually find them at: https://data.bls.gov/PDQWeb/ap")
    print("\nSteps:")
    print("1. Go to https://data.bls.gov/PDQWeb/ap")
    print("2. Select 'South' as the area")
    print("3. Browse or search for your items")
    print("4. Note the series ID (format: APU0300XXXXX)")
    print("\nItems to search for:")
    for item in item_names:
        print(f"  - {item}")
    print("\n" + "="*60)
    
    return {}

def main():
    """Main function to fetch Average Price Data."""
    import os
    
    # Check for API key
    api_key = os.environ.get("BLS_API_KEY")
    
    if not api_key:
        print("Note: No BLS_API_KEY environment variable found.")
        print("You can set it with: set BLS_API_KEY=your_key (Windows)")
        print("or: export BLS_API_KEY=your_key (Linux/Mac)")
        print("Register for a free key at: https://www.bls.gov/developers/api_signature.htm")
        print("Continuing without API key (may hit rate limits)...\n")
    
    # Use example series IDs or load from file
    # You can modify this to use your own series IDs
    series_ids = list(AVERAGE_PRICE_SERIES.values())
    
    print(f"Fetching Average Price Data for {len(series_ids)} series...")
    print(f"Years: 2019-2025")
    print(f"Region: South (0300)\n")
    
    # Fetch data
    df = fetch_average_price_data(
        series_ids=series_ids,
        api_key=api_key,
        start_year=2019,
        end_year=2025
    )
    
    if df is not None:
        # Create output directory
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "data" / "cpi"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        output_file = output_dir / "bls_average_prices_south.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*60}")
        print("Average Price Data Summary")
        print('='*60)
        print(f"Total records: {len(df)}")
        print(f"\nYears covered: {sorted(df['year'].unique())}")
        print(f"\nItems: {df['item_name'].nunique()}")
        print(f"\nSample data:")
        print(df.head(20).to_string(index=False))
        print(f"\nSaved to: {output_file}")
        
        # Calculate annual averages
        annual_avg = df.groupby(['year', 'item_name'])['value'].mean().reset_index()
        annual_avg.columns = ['year', 'item_name', 'avg_price']
        annual_file = output_dir / "bls_average_prices_south_annual.csv"
        annual_avg.to_csv(annual_file, index=False)
        print(f"\nAnnual averages saved to: {annual_file}")
    else:
        print("\nFailed to fetch Average Price Data.")

if __name__ == "__main__":
    main()





