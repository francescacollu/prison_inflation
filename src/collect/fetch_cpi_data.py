import requests
import pandas as pd
from pathlib import Path
import json
import time

# BLS API endpoint
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# CPI Series IDs
CPI_SERIES = {
    "CPI-U": "CUUR0000SA0",  # All Urban Consumers - All Items
    "Food at home": "CUUR0000SAF11",  # Food at home
    "Personal care": "CUUR0000SEGA",  # Personal care products
    "Apparel": "CUUR0000SAA",  # Apparel
    "Medicinal drugs": "CUUR0000SEMD",  # Medicinal drugs
    "Recreation": "CUUR0000SERA",  # Recreation commodities
}

def fetch_cpi_data(api_key=None, start_year=2019, end_year=2025):
    """
    Fetch CPI data from BLS API.
    
    Args:
        api_key: BLS API key (optional, but recommended to avoid rate limits)
        start_year: Start year for data
        end_year: End year for data
    
    Returns:
        DataFrame with columns: year, cpi_type, value
    """
    all_data = []
    
    # Prepare API request
    headers = {
        "Content-Type": "application/json"
    }
    
    # BLS API allows up to 50 series per request
    # We have 6 series, so we can do it in one request
    series_ids = list(CPI_SERIES.values())
    
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": api_key if api_key else None
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    print(f"Fetching CPI data from BLS API for years {start_year}-{end_year}...")
    print(f"Series: {', '.join(CPI_SERIES.keys())}")
    
    try:
        response = requests.post(BLS_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "REQUEST_SUCCEEDED":
            results = data.get("Results", {}).get("series", [])
            
            for series in results:
                series_id = series.get("seriesID")
                # Find the CPI type name for this series ID
                cpi_type = [k for k, v in CPI_SERIES.items() if v == series_id][0]
                
                # Extract monthly data
                monthly_data = series.get("data", [])
                
                # Group by year and calculate annual average
                year_data = {}
                for month_data in monthly_data:
                    year = int(month_data.get("year"))
                    value = float(month_data.get("value", 0))
                    
                    if year not in year_data:
                        year_data[year] = []
                    year_data[year].append(value)
                
                # Calculate annual averages
                for year, values in year_data.items():
                    if values:
                        avg_value = sum(values) / len(values)
                        all_data.append({
                            "year": year,
                            "cpi_type": cpi_type,
                            "value": avg_value
                        })
            
            print(f"Successfully fetched {len(all_data)} data points")
            
        else:
            error_msg = data.get("message", ["Unknown error"])[0] if isinstance(data.get("message"), list) else data.get("message", "Unknown error")
            print(f"API Error: {error_msg}")
            if "registrationkey" in error_msg.lower() or "key" in error_msg.lower():
                print("\nNote: BLS API key is recommended but not required.")
                print("You can register for a free API key at: https://www.bls.gov/developers/api_signature.htm")
                print("Without a key, you may hit rate limits.")
            
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error processing data: {e}")
        return None
    
    if not all_data:
        print("No data retrieved")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    df = df.sort_values(["year", "cpi_type"])
    
    return df

def main():
    # Check for API key in environment variable or prompt user
    import os
    api_key = os.environ.get("BLS_API_KEY")
    
    if not api_key:
        print("Note: No BLS_API_KEY environment variable found.")
        print("You can set it with: set BLS_API_KEY=your_key (Windows) or export BLS_API_KEY=your_key (Linux/Mac)")
        print("Continuing without API key (may hit rate limits)...\n")
    
    # Fetch data
    df = fetch_cpi_data(api_key=api_key, start_year=2019, end_year=2025)
    
    if df is not None:
        # Create output directory (relative to project root)
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "data" / "cpi"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        output_file = output_dir / "cpi_data.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*60}")
        print(f"CPI Data Summary")
        print('='*60)
        print(f"Total records: {len(df)}")
        print(f"\nYears covered: {sorted(df['year'].unique())}")
        print(f"\nCPI types: {sorted(df['cpi_type'].unique())}")
        print(f"\nSample data:")
        print(df.head(20).to_string(index=False))
        print(f"\nSaved to: {output_file}")
    else:
        print("\nFailed to fetch CPI data. Please check your API key and try again.")

if __name__ == "__main__":
    main()

