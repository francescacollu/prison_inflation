#!/usr/bin/env python3
"""
Simple parser for HEB search results text file.
Extracts product information from the structured text.
"""

import re
import pandas as pd
from pathlib import Path

def parse_heb_file(file_path):
    """Parse HEB text file and extract product information."""

    products = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find where "X results" appears
    start_idx = -1
    for i, line in enumerate(lines):
        if 'results' in line and any(char.isdigit() for char in line):
            start_idx = i
            break

    if start_idx == -1:
        print("Could not find results line")
        return []

    print(f"Found results line at index {start_idx}")

    i = start_idx + 1  # Start after the results line

    while i < len(lines):
        line = lines[i].strip()

        # Look for "Add [item] to list" pattern
        if line.startswith('Add ') and ' to list' in line:
            # Extract item name from this line
            item_name = line.replace('Add ', '').replace(' to list', '').strip()

            # Move to next line (should be item name with size)
            i += 1
            if i >= len(lines):
                break

            size_line = lines[i].strip()
            item_name_with_size = size_line

            # Extract size from the line
            size = None
            if ', ' in size_line:
                parts = size_line.split(', ', 1)
                item_name_clean = parts[0].strip()
                size = parts[1].strip()
            else:
                item_name_clean = size_line

            # Continue reading to find price
            price = None
            unit_price = None
            unit_type = None

            # Read next few lines looking for price info
            for j in range(10):  # Look ahead up to 10 lines
                if i + j + 1 >= len(lines):
                    break

                check_line = lines[i + j + 1].strip()

                # Look for price line
                if check_line.startswith('$') and price is None:
                    price_match = re.search(r'\$([0-9]+\.[0-9]+)', check_line)
                    if price_match:
                        price = float(price_match.group(1))

                # Look for unit price line like ($0.66 / ct)
                elif check_line.startswith('($') and unit_price is None:
                    unit_match = re.search(r'\(\$\s*([0-9]+\.[0-9]+)\s*/\s*(\w+)\)', check_line)
                    if unit_match:
                        unit_price = float(unit_match.group(1))
                        unit_type = unit_match.group(2)

                # If we found both price and unit price, we can stop looking
                if price is not None and unit_price is not None:
                    break

            # Create product entry if we have essential info
            if price is not None:
                product = {
                    'item_name': item_name_clean,
                    'item_price': price,
                    'price_per_unit': unit_price,
                    'price_per_unit_type': unit_type,
                    'item_size': size,
                    'full_item_name': item_name
                }
                products.append(product)
                print(f"Found: {item_name_clean} - ${price}")

            # Skip ahead to avoid reprocessing
            i += 5

        i += 1

    return products

def main():
    # Parse the HEB text file
    project_root = Path(__file__).parent.parent.parent
    text_file = project_root / "data" / "retail" / "heb_webpage_to_scrape.txt"

    print(f"Parsing file: {text_file}")

    products = parse_heb_file(text_file)

    if products:
        # Create DataFrame
        df = pd.DataFrame(products)

        # Save to CSV
        output_file = project_root / "data" / "retail" / "heb_parsed_colombian_coffee.csv"
        df.to_csv(output_file, index=False)

        print(f"\nExtracted {len(products)} products")
        print(f"Saved to: {output_file}")
        print("\nFirst few products:")
        print(df.head().to_string(index=False))
    else:
        print("No products found")

if __name__ == "__main__":
    main()



