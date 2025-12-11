"""
Scrape BLS website to discover all available Average Price series IDs for South region.

This script attempts to extract all available series IDs from the BLS Average Price
Data website: https://data.bls.gov/PDQWeb/ap
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
import time
from typing import List, Set

def scrape_bls_series_ids(region: str = "0300") -> List[str]:
    """
    Scrape BLS website to find all series IDs for a given region.
    
    Args:
        region: Region code (0300 = South)
    
    Returns:
        List of series IDs
    """
    print(f"Scraping BLS website for South region (0300) series IDs...")
    print("This may take a few minutes...\n")
    
    series_ids = set()
    
    # BLS Average Price Data URL
    base_url = "https://data.bls.gov/PDQWeb/ap"
    
    try:
        # Try to access the website
        print("Accessing BLS website...")
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for series IDs in the page
        # Series IDs follow pattern: APU0300XXXXX
        pattern = re.compile(r'APU' + region + r'\d{4,7}')
        
        # Search in all text
        text = soup.get_text()
        found_ids = pattern.findall(text)
        series_ids.update(found_ids)
        
        # Also search in script tags (data might be loaded via JavaScript)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                found_ids = pattern.findall(script.string)
                series_ids.update(found_ids)
        
        # Search in data attributes
        for element in soup.find_all(attrs={'data-series-id': True}):
            series_id = element.get('data-series-id')
            if series_id and series_id.startswith('APU' + region):
                series_ids.add(series_id)
        
        print(f"Found {len(series_ids)} series IDs from initial page")
        
        # Note: The BLS website uses JavaScript to load data dynamically
        # We might need to use Selenium for full discovery
        print("\nNote: BLS website uses dynamic loading.")
        print("For complete discovery, you may need to:")
        print("1. Use browser developer tools to inspect network requests")
        print("2. Use Selenium to interact with the website")
        print("3. Manually export the list from the website")
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing BLS website: {e}")
        print("\nAlternative: Manual discovery")
        print("1. Visit: https://data.bls.gov/PDQWeb/ap")
        print("2. Select 'South' as area")
        print("3. Use browser developer tools (F12)")
        print("4. Look for API calls or data in the Network/Console tabs")
        print("5. Extract series IDs from the responses")
    
    return sorted(list(series_ids))

def save_series_ids(series_ids: List[str], output_file: Path):
    """Save series IDs to a JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(series_ids, f, indent=2)
    
    print(f"\n✓ Saved {len(series_ids)} series IDs to: {output_file}")

def main():
    """Main function."""
    project_root = Path(__file__).parent.parent.parent
    
    # Scrape series IDs
    series_ids = scrape_bls_series_ids(region="0300")
    
    if series_ids:
        # Save to file
        output_file = project_root / "data" / "retail" / "bls_south_series_ids.json"
        save_series_ids(series_ids, output_file)
        
        print(f"\nSample series IDs found:")
        for sid in series_ids[:10]:
            print(f"  - {sid}")
        if len(series_ids) > 10:
            print(f"  ... and {len(series_ids) - 10} more")
    else:
        print("\n⚠️  No series IDs found via scraping.")
        print("\nManual method:")
        print("1. Visit: https://data.bls.gov/PDQWeb/ap")
        print("2. Select 'South' as area")
        print("3. Open browser developer tools (F12)")
        print("4. Go to Network tab")
        print("5. Filter by 'XHR' or 'Fetch'")
        print("6. Browse items on the website")
        print("7. Look for API calls containing series IDs")
        print("8. Extract all APU0300XXXXX patterns")

if __name__ == "__main__":
    main()







