"""
Fetch ALL available Average Price Data for South region from BLS API.

This script attempts to retrieve all available items for the South region
and get the last month's price data available for 2025.

Since BLS doesn't provide a catalog API, we'll need to either:
1. Try common series ID patterns
2. Scrape the BLS website to discover series IDs
3. Use a known list of series IDs

For now, we'll try to discover series IDs by attempting common patterns
and also provide a way to load series IDs from a file.
"""

import requests
import pandas as pd
from pathlib import Path
import json
import time
from typing import List, Dict, Optional
import re

# BLS API endpoint
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# South region code
SOUTH_REGION = "0300"

def discover_series_ids_by_pattern(api_key: Optional[str] = None) -> List[str]:
    """
    Attempt to discover series IDs by testing common patterns.
    
    This tests a range of common item code patterns to find valid series IDs.
    Note: This is slow and may hit rate limits, but can discover many items.
    
    Args:
        api_key: BLS API key
    
    Returns:
        List of discovered series IDs
    """
    print("Attempting to discover series IDs by testing patterns...")
    print("This will test common item code ranges. This may take a while...\n")
    
    discovered = []
    
    # Common item code patterns for Average Price Data
    # Food items typically: 701XXX, 702XXX, etc.
    # Personal care: 711XXX, 712XXX, etc.
    
    # Test ranges (this is a sample - you can expand)
    test_ranges = [
        # Food items (701XXX - 709XXX)
        range(701111, 701999, 100),  # Bread, milk, eggs, etc.
        range(702111, 702999, 100),  # More food items
        range(703111, 703999, 100),
        # Personal care (711XXX - 719XXX)
        range(711111, 711999, 100),  # Toothpaste, shampoo, etc.
        range(712111, 712999, 100),
    ]
    
    # Test in batches
    all_test_ids = []
    for test_range in test_ranges:
        for code in test_range:
            series_id = f"APU0300{code}"
            all_test_ids.append(series_id)
    
    print(f"Testing {len(all_test_ids)} potential series IDs...")
    print("(This is a sample - for complete discovery, use manual method)\n")
    
    # Test in batches of 50 (API limit)
    batch_size = 50
    for i in range(0, min(200, len(all_test_ids)), batch_size):  # Limit to first 200 for speed
        batch = all_test_ids[i:i+batch_size]
        
        payload = {
            "seriesid": batch,
            "startyear": "2024",
            "endyear": "2025",
        }
        if api_key:
            payload["registrationkey"] = api_key
        
        try:
            response = requests.post(
                BLS_API_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "REQUEST_SUCCEEDED":
                    results = data.get("Results", {}).get("series", [])
                    for series in results:
                        discovered.append(series.get("seriesID"))
                    print(f"  Batch {i//batch_size + 1}: Found {len(results)} valid series")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"  Batch {i//batch_size + 1}: Error - {e}")
            continue
    
    print(f"\n✓ Discovered {len(discovered)} series IDs")
    return discovered

def fetch_series_data(
    series_ids: List[str],
    api_key: Optional[str] = None,
    start_year: int = 2024,
    end_year: int = 2025
) -> Optional[pd.DataFrame]:
    """
    Fetch data for multiple series IDs.
    
    Args:
        series_ids: List of BLS series IDs
        api_key: BLS API key
        start_year: Start year
        end_year: End year
    
    Returns:
        DataFrame with all data
    """
    all_data = []
    
    # BLS API allows up to 50 series per request
    batch_size = 50
    series_batches = [
        series_ids[i:i + batch_size] 
        for i in range(0, len(series_ids), batch_size)
    ]
    
    headers = {"Content-Type": "application/json"}
    
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
            response = requests.post(BLS_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "REQUEST_SUCCEEDED":
                results = data.get("Results", {}).get("series", [])
                
                for series in results:
                    series_id = series.get("seriesID")
                    series_name = series.get("catalogData", {}).get("series_title", series_id)
                    
                    monthly_data = series.get("data", [])
                    
                    for month_data in monthly_data:
                        year = int(month_data.get("year"))
                        period = month_data.get("period")
                        value = month_data.get("value")
                        
                        if value and value != "-":
                            try:
                                price_value = float(value)
                                all_data.append({
                                    "year": year,
                                    "period": period,
                                    "month": period_to_month(period),
                                    "series_id": series_id,
                                    "item_name": series_name,
                                    "value": price_value
                                })
                            except (ValueError, TypeError):
                                continue
                
                print(f"  ✓ Successfully fetched data for {len(results)} series")
                
            else:
                error_msg = data.get("message", ["Unknown error"])
                if isinstance(error_msg, list):
                    error_msg = error_msg[0]
                print(f"  ✗ API Error: {error_msg}")
                continue
                
            # Rate limiting
            if batch_idx < len(series_batches) - 1:
                time.sleep(0.5)
                
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request error: {e}")
            continue
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    if not all_data:
        return None
    
    df = pd.DataFrame(all_data)
    return df

def period_to_month(period: str) -> Optional[int]:
    """Convert BLS period code (e.g., 'M01') to month number (1-12)."""
    if period and period.startswith("M"):
        try:
            return int(period[1:])
        except ValueError:
            return None
    return None

def get_latest_2025_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the last available month's price for each item in 2025.
    
    Args:
        df: DataFrame with all price data
    
    Returns:
        DataFrame with latest 2025 prices
    """
    # Filter to 2025 only
    df_2025 = df[df['year'] == 2025].copy()
    
    if df_2025.empty:
        print("No 2025 data available. Trying 2024...")
        df_2025 = df[df['year'] == 2024].copy()
        if df_2025.empty:
            return pd.DataFrame()
    
    # For each series, get the latest month
    latest_prices = []
    
    for series_id in df_2025['series_id'].unique():
        series_data = df_2025[df_2025['series_id'] == series_id].copy()
        
        # Sort by year and month
        series_data = series_data.sort_values(['year', 'month'], ascending=[False, False])
        
        if not series_data.empty:
            latest = series_data.iloc[0]
            latest_prices.append({
                'series_id': latest['series_id'],
                'item_name': latest['item_name'],
                'year': latest['year'],
                'month': latest['month'],
                'period': latest['period'],
                'price': latest['value']
            })
    
    result_df = pd.DataFrame(latest_prices)
    result_df = result_df.sort_values('item_name')
    
    return result_df

def load_series_ids_from_file(file_path: Path) -> List[str]:
    """Load series IDs from a JSON or text file."""
    if not file_path.exists():
        return []
    
    if file_path.suffix == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return list(data.values())
    elif file_path.suffix == '.txt':
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and line.strip().startswith('APU')]
    elif file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
        if 'series_id' in df.columns:
            return df['series_id'].tolist()
    
    return []

def main():
    """Main function."""
    import os
    
    project_root = Path(__file__).parent.parent.parent
    
    # Check for API key
    api_key = os.environ.get("BLS_API_KEY")
    
    if not api_key:
        print("⚠️  WARNING: No BLS_API_KEY environment variable found.")
        print("Register for a free key at: https://www.bls.gov/developers/api_signature.htm")
        print("Without a key, you may hit rate limits.\n")
        response = input("Continue without API key? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Try to load series IDs from file
    series_id_file = project_root / "data" / "retail" / "bls_south_series_ids.json"
    series_ids = load_series_ids_from_file(series_id_file)
    
    if not series_ids:
        print("\n" + "="*60)
        print("NO SERIES IDs FILE FOUND")
        print("="*60)
        print("\nTo retrieve ALL items for South region, you need to provide series IDs.")
        print("\nOPTION 1: Manual Collection (Most Comprehensive)")
        print("1. Visit: https://data.bls.gov/PDQWeb/ap")
        print("2. Select 'South' as the area")
        print("3. Browse all available items")
        print("4. Use browser developer tools (F12) -> Network tab")
        print("5. Look for API calls or data containing series IDs")
        print("6. Extract all APU0300XXXXX patterns")
        print("7. Save to: data/retail/bls_south_series_ids.json")
        print("   Format: [\"APU0300701111\", \"APU0300702111\", ...]")
        
        print("\nOPTION 2: Pattern-Based Discovery (Limited)")
        print("Attempting to discover common series IDs...")
        response = input("Try pattern-based discovery? (y/n): ")
        
        if response.lower() == 'y':
            series_ids = discover_series_ids_by_pattern(api_key)
            if series_ids:
                # Save discovered IDs
                series_id_file.parent.mkdir(parents=True, exist_ok=True)
                with open(series_id_file, 'w') as f:
                    json.dump(series_ids, f, indent=2)
                print(f"\n✓ Saved discovered series IDs to: {series_id_file}")
        else:
            print("\nUsing example series IDs for demonstration...")
            # Common food items for South region
            common_series = [
                "APU0300701111",  # Bread
                "APU0300702111",  # Milk
                "APU0300703111",  # Eggs
                "APU0300704111",  # Ground beef
                "APU0300705111",  # Chicken
            ]
            series_ids = common_series
            print(f"Using {len(series_ids)} example series IDs...")
            print("(For all items, please collect series IDs manually)")
        
        print("\n" + "="*60)
    
    print(f"\nFetching data for {len(series_ids)} series...")
    print(f"Years: 2024-2025 (to ensure we get latest 2025 data)")
    print(f"Region: South (0300)\n")
    
    # Fetch all data
    df = fetch_series_data(
        series_ids=series_ids,
        api_key=api_key,
        start_year=2024,
        end_year=2025
    )
    
    if df is None or df.empty:
        print("\n❌ Failed to fetch data. Please check:")
        print("  1. Your API key (if using one)")
        print("  2. Series IDs are correct")
        print("  3. Internet connection")
        return
    
    print(f"\n✓ Successfully fetched {len(df)} data points")
    
    # Get latest 2025 prices
    latest_df = get_latest_2025_prices(df)
    
    if latest_df.empty:
        print("\n⚠️  No 2025 data found. Showing latest available data...")
        # Get latest overall
        latest_df = df.sort_values(['year', 'month'], ascending=[False, False])
        latest_df = latest_df.groupby('series_id').first().reset_index()
        latest_df = latest_df[['series_id', 'item_name', 'year', 'month', 'period', 'value']]
        latest_df.columns = ['series_id', 'item_name', 'year', 'month', 'period', 'price']
    
    # Save results
    output_dir = project_root / "data" / "cpi"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save latest prices
    latest_file = output_dir / "bls_average_prices_south_latest_2025.csv"
    latest_df.to_csv(latest_file, index=False)
    
    # Save all data
    all_data_file = output_dir / "bls_average_prices_south_all.csv"
    df.to_csv(all_data_file, index=False)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print('='*60)
    print(f"\nTotal items: {len(latest_df)}")
    print(f"Latest prices saved to: {latest_file}")
    print(f"All data saved to: {all_data_file}")
    
    print(f"\nLatest 2025 prices (last available month):")
    print(latest_df.to_string(index=False))
    
    # Summary by category
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Items with 2025 data: {len(latest_df[latest_df['year'] == 2025])}")
    print(f"Items with 2024 data only: {len(latest_df[latest_df['year'] == 2024])}")
    print(f"\nPrice range: ${latest_df['price'].min():.2f} - ${latest_df['price'].max():.2f}")

if __name__ == "__main__":
    main()

