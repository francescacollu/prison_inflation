#!/usr/bin/env python3
"""
Parse HEB search results from text file to extract product information.

Expected structure per item:
1. "Add [item name] to list"
2. "[item name], [size]"
3. "$[price]"
4. "each"
5. "([unit_price] / [unit])"
6. "[item name], [size]" (repeated)
7. "Aisle [number]"
"""

import re
import pandas as pd
from pathlib import Path
import sys

def parse_price(price_str):
    """Extract numeric price from string like '$7.98'."""
    match = re.search(r'\$?(\d+\.?\d*)', price_str)
    return float(match.group(1)) if match else None

def parse_unit_price(unit_price_str):
    """Extract unit price and unit from string like '($0.66 / ct)'."""
    match = re.search(r'\(\$(\d+\.?\d*)\s*/\s*(\w+)\)', unit_price_str)
    if match:
        price = float(match.group(1))
        unit = match.group(2)
        return price, unit
    return None, None

def parse_item_size(item_line):
    """Extract item name and size from line like 'CAFE Olé by H-E-B Medium Roast Colombian Coffee Single Serve Cups, 12 ct'."""
    if ',' in item_line:
        parts = item_line.split(',', 1)
        item_name = parts[0].strip()
        size_part = parts[1].strip()
        return item_name, size_part
    return item_line.strip(), None

def parse_heb_text_file(file_path):
    """
    Parse HEB search results text file.

    Args:
        file_path: Path to the text file containing HEB search results

    Returns:
        List of dictionaries with product information
    """
    products = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Read {len(lines)} lines from file", flush=True)

    # Find the line with "X results" to know where to start parsing
    start_idx = -1
    for i, line in enumerate(lines):
        line = line.strip()
        if re.search(r'\d+\s+results', line):
            start_idx = i + 1  # Start parsing from the next line
            print(f"Found results line at index {i}: '{line}'", flush=True)
            break

    if start_idx == -1:
        print("Could not find 'X results' line in the file", flush=True)
        return []

    print(f"Starting to parse from line {start_idx + 1}", flush=True)

    i = start_idx
    while i < len(lines):
        line = lines[i].strip()

        # Look for the "Add [item] to list" pattern to start a new product
        if line.startswith('Add ') and line.endswith(' to list'):
            product = {}

            # Extract item name from "Add [name] to list"
            add_line = line
            item_name_start = add_line.find('Add ') + 4
            item_name_end = add_line.find(' to list')
            if item_name_end > item_name_start:
                full_item_name = add_line[item_name_start:item_name_end].strip()
                product['full_item_name'] = full_item_name

            # Move to next line - should be "[item name], [size]"
            i += 1
            if i >= len(lines):
                break
            line = lines[i].strip()

            if ',' in line:
                item_name, size = parse_item_size(line)
                product['item_name'] = item_name
                product['item_size'] = size

            # Continue looking for price information
            found_price = False
            found_unit_price = False

            # Look ahead for price and unit price
            look_ahead = 0
            max_look_ahead = 10

            while look_ahead < max_look_ahead and i + look_ahead < len(lines):
                check_line = lines[i + look_ahead].strip()

                # Look for price line starting with $
                if check_line.startswith('$') and not found_price:
                    product['item_price'] = parse_price(check_line)
                    found_price = True

                # Look for unit price line with ($X.XX / unit)
                elif check_line.startswith('($') and '/ ' in check_line and not found_unit_price:
                    unit_price, unit = parse_unit_price(check_line)
                    product['price_per_unit'] = unit_price
                    product['price_per_unit_type'] = unit
                    found_unit_price = True

                # Look for "each" line
                elif check_line == 'each':
                    pass  # Just skip this line

                # If we found both price and unit price, we can stop looking ahead
                if found_price and found_unit_price:
                    break

                look_ahead += 1

            # If we found a complete product, add it to the list
            if 'item_name' in product and product.get('item_price') is not None:
                products.append(product)
                print(f"Found product: {product['item_name']} - ${product['item_price']}")
            else:
                print(f"Incomplete product found: {product}")

            # Skip ahead to avoid reprocessing lines
            i += max(1, look_ahead)

        i += 1

    return products

def process_heb_search_results(text_file_path, output_csv_path=None):
    """
    Process HEB search results text file and save to CSV.

    Args:
        text_file_path: Path to the text file with search results
        output_csv_path: Path to save the CSV (optional)
    """
    # Parse the text file
    products = parse_heb_text_file(text_file_path)

    if not products:
        print("No products found in the text file")
        return

    # Create DataFrame
    df = pd.DataFrame(products)

    # Reorder columns to match desired output
    desired_columns = [
        'item_name', 'item_price', 'price_per_unit', 'price_per_unit_type',
        'item_size', 'full_item_name'
    ]

    # Only include columns that exist
    available_columns = [col for col in desired_columns if col in df.columns]
    df = df[available_columns]

    print(f"\n{'='*60}")
    print("HEB PARSING RESULTS")
    print(f"{'='*60}")
    print(f"Total products found: {len(df)}")
    print(f"Products with prices: {df['item_price'].notna().sum()}")

    if 'price_per_unit' in df.columns:
        print(f"Products with unit prices: {df['price_per_unit'].notna().sum()}")

    if 'item_size' in df.columns:
        print(f"Products with sizes: {df['item_size'].notna().sum()}")

    print(f"\nSample results:")
    print(df.head(5).to_string(index=False))

    # Save to CSV if output path provided
    if output_csv_path:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv_path, index=False)
        print(f"\nSaved results to: {output_csv_path}")

    return df

def main():
    print("Starting HEB text parser...", flush=True)

    # Process the provided text file
    project_root = Path(__file__).parent.parent.parent
    text_file_path = project_root / "data" / "retail" / "heb_webpage_to_scrape.txt"

    print(f"Looking for file at: {text_file_path}", flush=True)
    print(f"File exists: {text_file_path.exists()}", flush=True)

    if not text_file_path.exists():
        print(f"Error: Text file not found at {text_file_path}", flush=True)
        return

    print(f"Processing HEB search results from: {text_file_path}", flush=True)

    # Process and optionally save to CSV
    output_csv_path = project_root / "data" / "retail" / "heb_parsed_colombian_coffee.csv"
    print(f"Will save to: {output_csv_path}", flush=True)

    df = process_heb_search_results(text_file_path, output_csv_path)

    if df is not None:
        print(f"Successfully processed {len(df)} products", flush=True)
    else:
        print("Processing failed", flush=True)

if __name__ == "__main__":
    main()
