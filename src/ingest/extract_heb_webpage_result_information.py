"""
Manual parser for HEB text file - simple line-by-line extraction
"""

import argparse
import re

def extract_product_info(lines, start_idx, end_idx):
    """Extract product information from a section of lines between start_idx and end_idx."""
    price = None
    unit_price = None
    unit_type = None
    item_name_clean = None
    item_size = None
    price_cut_mode = False
    first_price_seen = False
    
    # Find "Add ... to list" line
    add_to_list_idx = None
    for i in range(start_idx, end_idx):
        line = lines[i].strip()
        if line.startswith('Add ') and line.endswith(' to list'):
            add_to_list_idx = i
            break
    
    if add_to_list_idx is None:
        return None
    
    # Next line should be item name with size
    if add_to_list_idx + 1 < end_idx:
        size_line = lines[add_to_list_idx + 1].strip()
        
        # Parse size
        if ', ' in size_line:
            name_part, size_part = size_line.rsplit(', ', 1)
            item_name_clean = name_part.strip()
            item_size = size_part.strip()
        else:
            item_name_clean = size_line
            item_size = None
    
    # Look for price and unit price in the section
    for j in range(add_to_list_idx + 1, end_idx):
        check_line = lines[j].strip()
        
        # Check for "Price cut" indicator
        if check_line == 'Price cut':
            price_cut_mode = True
            first_price_seen = False
            continue
        
        # Price line - handle both "$X.XX" and "X for $Y.YY" patterns
        if '$' in check_line:
            # Try "X for $Y.YY" pattern first
            for_pattern = re.search(r'(\d+)\s+for\s+\$([0-9]+\.[0-9]+)', check_line, re.IGNORECASE)
            if for_pattern:
                quantity = int(for_pattern.group(1))
                total_price = float(for_pattern.group(2))
                found_price = total_price / quantity  # Price per unit
            else:
                # Regular "$X.XX" pattern
                price_match = re.search(r'\$([0-9]+\.[0-9]+)', check_line)
                if price_match:
                    found_price = float(price_match.group(1))
                else:
                    found_price = None
            
            if found_price is not None:
                if price_cut_mode:
                    # In price cut mode, first price is old (strikethrough), second is current
                    if not first_price_seen:
                        first_price_seen = True
                        continue
                    else:
                        # This is the second price, which is the current discounted price
                        price = found_price
                        price_cut_mode = False
                        first_price_seen = False
                else:
                    price = found_price
        
        # Check for "each" - unit price should be on next line
        elif check_line == 'each':
            # Look for unit price on the next line
            if j + 1 < end_idx:
                next_line = lines[j + 1].strip()
                unit_match = re.search(r'\(\$\s*([0-9]+\.[0-9]+)\s*/\s*(\w+)\)', next_line)
                if unit_match:
                    unit_price = float(unit_match.group(1))
                    unit_type = unit_match.group(2)
        
        # Unit price line (fallback for cases where it's not after "each")
        elif check_line.startswith('($'):
            unit_match = re.search(r'\(\$\s*([0-9]+\.[0-9]+)\s*/\s*(\w+)\)', check_line)
            if unit_match and unit_price is None:  # Only set if not already found
                unit_price = float(unit_match.group(1))
                unit_type = unit_match.group(2)
    
    if price and item_name_clean:
        return {
            'item_name': item_name_clean,
            'item_price': price,
            'price_per_unit': unit_price,
            'price_per_unit_type': unit_type,
            'item_size': item_size
        }
    return None

def main(item_category):
    # Read the file
    with open('data/retail/heb_webpage_to_scrape.txt', 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

    print(f"Read {len(lines)} lines")
    
    # Extract expected number of results
    expected_count = None
    for i, line in enumerate(lines):
        match = re.match(r'^(\d+)\s+results', line)
        if match:
            expected_count = int(match.group(1))
            print(f"Expected {expected_count} results")
            break
    
    # Find "Best match" to start from
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == 'Best match':
            start_idx = i + 1
            print(f"Found 'Best match' at line {i+1}, starting search from line {start_idx+1}")
            break
    
    if start_idx is None:
        print("Error: Could not find 'Best match'")
        return
    
    # Find all section markers ("Add to cart" and "Out of stock")
    section_markers = []
    for i in range(start_idx, len(lines)):
        line_stripped = lines[i].strip()
        if line_stripped == 'Add to cart' or line_stripped == 'Out of stock':
            section_markers.append(i)
    
    # Sort markers by line number
    section_markers.sort()
    
    cart_count = sum(1 for i in section_markers if lines[i].strip() == 'Add to cart')
    stock_count = sum(1 for i in section_markers if lines[i].strip() == 'Out of stock')
    print(f"Found {len(section_markers)} section markers ({cart_count} 'Add to cart', {stock_count} 'Out of stock')")
    
    products = []
    
    # First item: from start_idx to first section marker
    if section_markers:
        first_end = section_markers[0]
        product = extract_product_info(lines, start_idx, first_end)
        if product:
            product['item_category'] = item_category
            products.append(product)
            print(f"Found product 1: {product['item_name']}")
        
        # Subsequent items: between section markers
        for idx in range(len(section_markers) - 1):
            section_start = section_markers[idx] + 1
            section_end = section_markers[idx + 1]
            product = extract_product_info(lines, section_start, section_end)
            if product:
                product['item_category'] = item_category
                products.append(product)
                print(f"Found product {idx + 2}: {product['item_name']}")
    
    print(f"\nTotal products found: {len(products)}")
    if expected_count is not None:
        if len(products) == expected_count:
            print(f"✓ Successfully found all {expected_count} expected products")
        else:
            print(f"⚠ Warning: Expected {expected_count} products but found {len(products)}")

    if products:
        import pandas as pd
        import os
        
        # Convert products list to DataFrame
        new_df = pd.DataFrame(products)
        
        # Check if file exists, if so read and append, otherwise create new
        csv_path = 'data/retail/processed/heb_parsed_results.csv'
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = new_df
        
        df.to_csv(csv_path, index=False)
        print("Saved to CSV")

        print("\nFirst 3 products:")
        for p in products[:3]:
            print(f"- {p['item_name']}: ${p['item_price']}, size: {p['item_size']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract HEB webpage result information')
    parser.add_argument('item_category', type=str, help='Item category (e.g., "Colombian coffee")')
    args = parser.parse_args()
    main(args.item_category)
