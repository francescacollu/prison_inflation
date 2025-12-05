"""
Helper script to find BLS Average Price series IDs for commissary items.

Since BLS doesn't provide a programmatic search API, this script helps you:
1. Generate a list of items to search for on the BLS website
2. Store series IDs once you find them
3. Create a mapping file for use with fetch_bls_average_prices.py
"""

import pandas as pd
from pathlib import Path
import json

def load_commissary_items() -> pd.DataFrame:
    """Load commissary items from the priority list."""
    project_root = Path(__file__).parent.parent.parent
    priority_file = project_root / "data" / "retail" / "price_collection_priority_list.csv"
    
    if priority_file.exists():
        return pd.read_csv(priority_file)
    else:
        # Fallback to full commissary list
        commissary_file = project_root / "data" / "retail" / "commissary_items_2025.csv"
        if commissary_file.exists():
            return pd.read_csv(commissary_file)
        else:
            print("Error: Could not find commissary items file")
            return pd.DataFrame()

def generate_search_list():
    """Generate a list of items to search for on BLS website."""
    df = load_commissary_items()
    
    if df.empty:
        return
    
    project_root = Path(__file__).parent.parent.parent
    output_file = project_root / "data" / "retail" / "bls_series_id_search_list.csv"
    
    # Create search suggestions for BLS website
    search_data = []
    
    # Map categories to BLS search terms
    category_mapping = {
        'HYGIENE': {
            'Colgate Toothpaste': 'toothpaste',
            'Toothbrush': 'toothbrush',
            'Shampoo': 'shampoo',
            'Dial Soap': 'soap bar',
            'Toilet Tissue': 'toilet paper',
            'Razor Disposable': 'razor',
            'Deodorant': 'deodorant',
        },
        'CONDIMENTS': {
            'Ketchup': 'ketchup',
            'Mustard': 'mustard',
            'Peanut Butter': 'peanut butter',
            'Grape Jelly': 'jelly',
        },
        'INSTANT FOODS': {
            'Ramen Noodles': 'noodles',
            'Oatmeal': 'oatmeal',
            'Cereal': 'cereal',
            'Rice': 'rice',
        },
        'PACKAGED MEAT': {
            'Tuna': 'tuna canned',
            'Chicken': 'chicken canned',
            'Vienna Sausage': 'vienna sausage',
        },
        'BEVERAGES': {
            'Water': 'bottled water',
            'Coffee': 'coffee',
            'Tea': 'tea',
            'Coca Cola': 'cola',
        },
        'OTC MEDICATIONS, VITAMINS, ETC': {
            'Aspirin': 'aspirin',
            'Ibuprofen': 'ibuprofen',
            'Vitamin': 'vitamin',
        },
    }
    
    # Generate search list
    for _, row in df.iterrows():
        category = row['category']
        item_name = row['item_name']
        
        # Get search term
        search_term = None
        if category in category_mapping:
            for key, term in category_mapping[category].items():
                if key.lower() in item_name.lower():
                    search_term = term
                    break
        
        if not search_term:
            # Generic search term
            search_term = item_name.lower()
        
        search_data.append({
            'category': category,
            'item_name': item_name,
            'size': row.get('size', ''),
            'bls_search_term': search_term,
            'series_id': '',  # To be filled manually
            'notes': ''
        })
    
    # Create DataFrame and save
    search_df = pd.DataFrame(search_data)
    search_df = search_df.drop_duplicates(subset=['item_name'])
    search_df.to_csv(output_file, index=False)
    
    print(f"Generated search list: {output_file}")
    print(f"\nTotal items: {len(search_df)}")
    print(f"\nNext steps:")
    print("1. Open https://data.bls.gov/PDQWeb/ap")
    print("2. Select 'South' as the area")
    print("3. For each item, search using the 'bls_search_term'")
    print("4. Find the matching series ID (format: APU0300XXXXX)")
    print("5. Fill in the 'series_id' column in the CSV")
    print("6. Save the file")
    print(f"\nSample items to search:")
    print(search_df[['item_name', 'bls_search_term']].head(10).to_string(index=False))

def load_series_id_mapping() -> dict:
    """Load series ID mapping from file if it exists."""
    project_root = Path(__file__).parent.parent.parent
    mapping_file = project_root / "data" / "retail" / "bls_series_id_mapping.json"
    
    if mapping_file.exists():
        with open(mapping_file, 'r') as f:
            return json.load(f)
    return {}

def save_series_id_mapping(mapping: dict):
    """Save series ID mapping to file."""
    project_root = Path(__file__).parent.parent.parent
    mapping_file = project_root / "data" / "retail" / "bls_series_id_mapping.json"
    
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Saved series ID mapping to: {mapping_file}")

if __name__ == "__main__":
    generate_search_list()





