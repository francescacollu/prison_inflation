"""
Manual parser for HEB text file - simple line-by-line extraction
"""

import argparse

def main(item_category):
    # Read the file
    with open('data/retail/heb_webpage_to_scrape.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Read {len(lines)} lines")

    products = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for "Add ... to list" pattern
        if line.startswith('Add ') and line.endswith(' to list'):
            print(f"Found product at line {i+1}: {line}")

            # Extract item name
            item_name = line[4:-8].strip()  # Remove "Add " and " to list"

            # Next line should be item name with size
            i += 1
            if i < len(lines): 
                size_line = lines[i].strip()
                print(f"Size line: {size_line}")

                # Parse size
                if ', ' in size_line:
                    name_part, size_part = size_line.split(', ', 1)
                    item_name_clean = name_part.strip()
                    item_size = size_part.strip()
                else:
                    item_name_clean = size_line
                    item_size = None

                # Look for price in next few lines
                price = None
                unit_price = None
                unit_type = None

                for j in range(1, 6):  # Check next 5 lines
                    if i + j < len(lines):
                        check_line = lines[i + j].strip()

                        # Price line
                        if check_line.startswith('$'):
                            import re
                            price_match = re.search(r'\$([0-9]+\.[0-9]+)', check_line)
                            if price_match:
                                price = float(price_match.group(1))
                                print(f"Found price: ${price}")

                        # Unit price line
                        elif check_line.startswith('($'):
                            unit_match = re.search(r'\(\$\s*([0-9]+\.[0-9]+)\s*/\s*(\w+)\)', check_line)
                            if unit_match:
                                unit_price = float(unit_match.group(1))
                                unit_type = unit_match.group(2)
                                print(f"Found unit price: ${unit_price} per {unit_type}")

                if price:
                    product = {
                        'item_category': item_category,
                        'item_name': item_name_clean,
                        'item_price': price,
                        'price_per_unit': unit_price,
                        'price_per_unit_type': unit_type,
                        'item_size': item_size
                    }
                    products.append(product)
                    print(f"Added product: {item_name_clean}")

                # Skip ahead
                i += 5
            else:
                break

        i += 1

    print(f"\nTotal products found: {len(products)}")

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
