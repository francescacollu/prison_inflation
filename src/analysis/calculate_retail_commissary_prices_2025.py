"""
Calculate retail price statistics (mean, median, min, max) per item and match with commissary prices.
All prices are normalized to per-unit prices for comparison.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from difflib import SequenceMatcher


def normalize_size_to_oz(size_str):
    """
    Normalize size string to ounces for comparison.
    
    Handles: oz, lb, ct (count), pk (pack), etc.
    Returns: (size_value, unit_type) or (None, None) if cannot parse
    """
    if pd.isna(size_str) or size_str == '':
        return None, None
    
    size_str = str(size_str).strip().lower()
    
    # Extract number
    number_match = re.search(r'(\d+\.?\d*)', size_str)
    if not number_match:
        return None, None
    
    try:
        number = float(number_match.group(1))
    except ValueError:
        return None, None
    
    # Determine unit
    if 'oz' in size_str or 'ounce' in size_str:
        return number, 'oz'
    elif 'lb' in size_str or 'pound' in size_str or 'lbs' in size_str:
        return number * 16, 'oz'  # Convert pounds to ounces
    elif 'ct' in size_str or 'count' in size_str or 'pk' in size_str or 'pack' in size_str:
        return number, 'ct'
    elif 'sheet' in size_str:
        return number, 'ct'
    else:
        # Try to infer - if it's a small number (< 50), might be count
        if number < 50:
            return number, 'ct'
        else:
            return number, 'oz'  # Assume ounces if unclear


def calculate_commissary_price_per_unit(price_min, price_max, size_str):
    """
    Calculate price per unit for commissary items.
    Returns: (price_per_unit_min, price_per_unit_max, unit_type) or (None, None, None)
    """
    if pd.isna(size_str) or size_str == '':
        return None, None, None
    
    size_value, unit_type = normalize_size_to_oz(size_str)
    
    if size_value is None or size_value == 0:
        return None, None, None
    
    price_per_unit_min = price_min / size_value
    price_per_unit_max = price_max / size_value
    
    return price_per_unit_min, price_per_unit_max, unit_type


def similarity_score(str1, str2):
    """Calculate similarity score between two strings."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def match_commissary_category(retail_category, commissary_df):
    """
    Match a retail item category to commissary items using exact match.
    The commissary item_name should exactly match the retail item_category.
    Returns all matching commissary rows for that category.
    """
    matches = []
    for _, comm_row in commissary_df.iterrows():
        comm_name = str(comm_row['item_name']).strip()
        retail_category_stripped = str(retail_category).strip()
        
        # Exact match (case-insensitive)
        if comm_name.lower() == retail_category_stripped.lower():
            matches.append(comm_row)
    
    return matches


def main():
    """Main function to calculate and match prices."""
    project_root = Path(__file__).parent.parent.parent
    
    # Load data
    print("Loading data...")
    retail_file = project_root / "data" / "retail" / "processed" / "heb_parsed_results.csv"
    commissary_file = project_root / "data" / "commissary" / "processed" / "texas" / "texas_commissary_2025.csv"
    
    if not retail_file.exists():
        print(f"Error: Retail file not found at {retail_file}")
        return
    
    if not commissary_file.exists():
        print(f"Error: Commissary file not found at {commissary_file}")
        return
    
    retail_df = pd.read_csv(retail_file)
    commissary_df = pd.read_csv(commissary_file)
    
    print(f"Loaded {len(retail_df)} retail items")
    print(f"Loaded {len(commissary_df)} commissary items")
    
    # Calculate price_per_unit if missing
    print("\nCalculating missing price_per_unit values...")
    missing_count = 0
    for idx, row in retail_df.iterrows():
        if pd.isna(row.get('price_per_unit')) or row.get('price_per_unit') == '':
            # Calculate from item_price and item_size
            item_price = row.get('item_price')
            item_size = row.get('item_size')
            
            if pd.notna(item_price) and pd.notna(item_size) and item_size != '':
                size_value, unit_type = normalize_size_to_oz(item_size)
                if size_value is not None and size_value > 0:
                    calculated_price_per_unit = item_price / size_value
                    retail_df.at[idx, 'price_per_unit'] = calculated_price_per_unit
                    if pd.isna(row.get('price_per_unit_type')):
                        retail_df.at[idx, 'price_per_unit_type'] = unit_type
                    missing_count += 1
    
    if missing_count > 0:
        print(f"Calculated price_per_unit for {missing_count} items")
    
    # Filter retail items that have price_per_unit (either from CSV or calculated)
    retail_df = retail_df[retail_df['price_per_unit'].notna()].copy()
    print(f"Retail items with price_per_unit: {len(retail_df)}")
    
    # Group retail items by item_category and calculate statistics
    print("\nCalculating retail price statistics by category...")
    retail_stats = retail_df.groupby('item_category').agg({
        'price_per_unit': ['mean', 'median', 'min', 'max', 'count'],
        'price_per_unit_type': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]  # Most common unit type
    }).reset_index()
    
    # Flatten column names
    retail_stats.columns = [
        'item_category',
        'retail_price_per_unit_mean',
        'retail_price_per_unit_median',
        'retail_price_per_unit_min',
        'retail_price_per_unit_max',
        'retail_item_count',
        'retail_price_per_unit_type'
    ]
    
    print(f"Found {len(retail_stats)} unique retail categories")
    
    # Match with commissary items
    print("\nMatching with commissary items...")
    results = []
    
    for _, retail_row in retail_stats.iterrows():
        retail_category = retail_row['item_category']
        
        # Find matching commissary items for this category
        comm_matches = match_commissary_category(retail_category, commissary_df)
        
        result = {
            'item_category': retail_category,
            'retail_price_per_unit_mean': retail_row['retail_price_per_unit_mean'],
            'retail_price_per_unit_median': retail_row['retail_price_per_unit_median'],
            'retail_price_per_unit_min': retail_row['retail_price_per_unit_min'],
            'retail_price_per_unit_max': retail_row['retail_price_per_unit_max'],
            'retail_item_count': int(retail_row['retail_item_count']),
            'retail_price_per_unit_type': retail_row['retail_price_per_unit_type'],
            'commissary_item_name': None,
            'commissary_category': None,
            'commissary_size': None,
            'commissary_price_min': None,
            'commissary_price_max': None,
            'commissary_price_per_unit_min': None,
            'commissary_price_per_unit_max': None,
            'commissary_price_per_unit_type': None,
            'commissary_match_count': len(comm_matches)
        }
        
        if len(comm_matches) > 0:
            # Calculate price per unit for all matching commissary items
            comm_price_per_unit_mins = []
            comm_price_per_unit_maxs = []
            unit_types = []
            
            for comm_match in comm_matches:
                comm_price_min = comm_match['price_min']
                comm_price_max = comm_match['price_max']
                comm_size = comm_match['size']
                
                price_per_unit_min, price_per_unit_max, unit_type = calculate_commissary_price_per_unit(
                    comm_price_min, comm_price_max, comm_size
                )
                
                if price_per_unit_min is not None and price_per_unit_max is not None:
                    comm_price_per_unit_mins.append(price_per_unit_min)
                    comm_price_per_unit_maxs.append(price_per_unit_max)
                    if unit_type:
                        unit_types.append(unit_type)
            
            if len(comm_price_per_unit_mins) > 0:
                # Use the first match for item details, but calculate min/max across all matches
                first_match = comm_matches[0]
                result['commissary_item_name'] = first_match['item_name']
                result['commissary_category'] = first_match['category']
                result['commissary_size'] = first_match['size']
                result['commissary_price_min'] = first_match['price_min']
                result['commissary_price_max'] = first_match['price_max']
                result['commissary_price_per_unit_min'] = min(comm_price_per_unit_mins)
                result['commissary_price_per_unit_max'] = max(comm_price_per_unit_maxs)
                # Use most common unit type
                if unit_types:
                    result['commissary_price_per_unit_type'] = max(set(unit_types), key=unit_types.count)
        
        results.append(result)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by item_category
    results_df = results_df.sort_values('item_category').reset_index(drop=True)
    
    # Save to CSV
    output_file = project_root / "data" / "retail" / "processed" / "retail_vs_commissary_2025_prices.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_file, index=False)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Total categories: {len(results_df)}")
    print(f"Categories matched with commissary: {len(results_df[results_df['commissary_item_name'].notna()])}")
    
    # Show summary
    print("\nSummary:")
    print(f"  Retail categories with matches: {len(results_df[results_df['commissary_item_name'].notna()])}")
    print(f"  Retail categories without matches: {len(results_df[results_df['commissary_item_name'].isna()])}")
    
    # Show some examples
    print("\nSample of matched categories:")
    matched = results_df[results_df['commissary_item_name'].notna()].head(5)
    for _, row in matched.iterrows():
        print(f"  {row['item_category']}")
        print(f"    Retail ({row['retail_item_count']} items): ${row['retail_price_per_unit_min']:.3f} - ${row['retail_price_per_unit_max']:.3f} per {row['retail_price_per_unit_type']}")
        print(f"      Mean: ${row['retail_price_per_unit_mean']:.3f}, Median: ${row['retail_price_per_unit_median']:.3f}")
        print(f"    Commissary ({row['commissary_match_count']} items): ${row['commissary_price_per_unit_min']:.3f} - ${row['commissary_price_per_unit_max']:.3f} per {row['commissary_price_per_unit_type']}")
        print(f"      Example: {row['commissary_item_name']} ({row['commissary_size']})")
        print()


if __name__ == "__main__":
    main()

