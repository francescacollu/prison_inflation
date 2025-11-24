import pandas as pd
import re
from pathlib import Path

def standardize_size(size_str):
    """Standardize size format: lowercase, consistent spacing."""
    if not size_str:
        return ''
    
    size_str = str(size_str).strip()
    
    # Convert to lowercase first
    size_str = size_str.lower()
    
    # Handle dimensions - normalize to "x" with no spaces (do this FIRST)
    size_str = re.sub(r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)', r'\1x\2', size_str)
    
    # Normalize spacing: ensure one space between number and unit (for measurements, but NOT for dimensions)
    # Exclude 'x' from letter matching to avoid breaking dimensions
    size_str = re.sub(r'(\d+\.?\d*)\s*([a-wy-z]+)', r'\1 \2', size_str)
    
    # Remove extra spaces
    size_str = ' '.join(size_str.split())
    
    return size_str

def clean_item_name(row):
    """Clean item name by removing prices and extracting sizes."""
    item_name = row['item_name']
    size = row['size'] if pd.notna(row['size']) else ''
    
    # Remove price patterns from item name (e.g., "7.00-", "0.60-", "$5.00-")
    item_name = re.sub(r'\s*\$?\d+\.\d{2}-\s*$', '', item_name)
    item_name = re.sub(r'\s*\d+\.\d{2}-\s*$', '', item_name)
    
    # Extract size patterns from item name BEFORE removing standalone numbers
    # (to avoid removing numbers that are part of dimensions)
    if not size:
        # More comprehensive size patterns (case-insensitive)
        size_patterns = [
            # Dimensions with various separators (handle "9 X 12", "8x11", etc.)
            r'\s+(\d+\s*[xX]\s*\d+)',  # 9 X 12, 8x11, 9 x 12
            r'\s+(\d+x\d+(?:\s*["\'])?)',  # 8x11", 14"x8"
            # With parentheses
            r'\((\d+\.?\d*\s*(?:oz|lb|gal|ml|kg|g|mg|l))\)',  # (12 oz), (3.5 oz)
            r'\((\d+\s*(?:pk|ct|piece|tab|tablet|sheet|bag|color|sht)s?)\)',  # (10 pk), (50 sheets)
            # With hyphen or space at end
            r'[-\s](\d+\.?\d*\s*(?:oz|lb|gal|ml|kg|g|mg|l))\s*(?:bottle|can|jar|pack)?$',  # -12 oz, 12 oz Bottle
            r'[-\s](\d+\s*(?:pk|ct|piece|tab|tablet|sheet|bag|color|sht)s?)\s*$',  # -10 pk, 100 ct
            # At end without separator
            r'\s+(\d+\.?\d*\s*(?:oz|lb|gal|ml|kg|g|mg|l))$',  # 12 oz
            r'\s+(\d+\s*(?:pk|ct|piece|tab|tablet|sheet|bag|color|sht)s?)$',  # 10 pk
            # Inches/dimensions at end
            r'\s+(\d+\.?\d*\s*["\'])$',  # 3"
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, item_name, re.IGNORECASE)
            if match:
                size = match.group(1).strip()
                # Remove the matched size from item name
                item_name = re.sub(pattern, '', item_name, flags=re.IGNORECASE).strip()
                break
    
    # NOW remove standalone numbers at the end that look like prices
    # (after extracting sizes, so we don't remove numbers from dimensions)
    # Only remove if it doesn't look like part of a dimension (not preceded by X)
    if not re.search(r'[xX]\s*$', item_name):
        item_name = re.sub(r'\s+\d+$', '', item_name)
    
    # Standardize size format
    if size:
        size = standardize_size(size)
    
    # Clean up whitespace in item name
    item_name = ' '.join(item_name.split())
    
    return pd.Series({'item_name': item_name, 'size': size})

def main():
    # Read the data
    input_file = Path('data/commissary/processed/texas/texas_commissary_all_years_combined.csv')
    output_file = Path('data/commissary/processed/texas/texas_commissary_cleaned.csv')
    
    print(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    print(f"Original data: {len(df)} items")
    print(f"\nCleaning item names and sizes...")
    
    # Apply cleaning
    df[['item_name', 'size']] = df.apply(clean_item_name, axis=1)
    
    # Remove any rows with empty item names
    original_count = len(df)
    df = df[df['item_name'].str.strip() != '']
    removed_count = original_count - len(df)
    
    if removed_count > 0:
        print(f"Removed {removed_count} items with empty names")
    
    # Sort by year, category, and item name
    df = df.sort_values(['year', 'category', 'item_name'])
    
    # Save cleaned data
    df.to_csv(output_file, index=False)
    
    print(f"\nCleaned data: {len(df)} items")
    print(f"Saved to: {output_file}")
    
    # Show some examples of cleaned data
    print(f"\nSample of cleaned data:")
    print(df.head(30).to_string(index=False))
    
    # Show items that had changes
    print(f"\n{'='*60}")
    print("Checking for remaining issues...")
    print('='*60)
    
    # Check for items with numbers that might be prices
    suspicious = df[df['item_name'].str.contains(r'\d+\.\d{2}$', regex=True, na=False)]
    if len(suspicious) > 0:
        print(f"\nFound {len(suspicious)} items that might still have prices in name:")
        print(suspicious[['year', 'item_name', 'price_min', 'price_max']].head(10).to_string(index=False))
    else:
        print("\nOK - No items with price patterns in names")
    
    # Show items with price ranges
    print(f"\n{'='*60}")
    print("Price range statistics:")
    print('='*60)
    ranges = df[df['price_min'] != df['price_max']]
    print(f"Items with price ranges: {len(ranges)}")
    print(f"Items with single price: {len(df) - len(ranges)}")
    
    if len(ranges) > 0:
        print(f"\nExamples of items with price ranges:")
        print(ranges[['year', 'item_name', 'price_min', 'price_max']].head(10).to_string(index=False))
    
    # Show size distribution
    print(f"\n{'='*60}")
    print("Size column statistics:")
    print('='*60)
    print(f"Items with size: {df['size'].notna().sum()}")
    print(f"Items without size: {df['size'].isna().sum()}")
    
if __name__ == '__main__':
    main()

