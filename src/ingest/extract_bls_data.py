import csv

def extract_bls_data(input_file, output_file):
    """
    Extract Series Id, Series Title, Area, Item, and last average price from BLS data file.
    """
    results = []
    current_record = {}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n\r')
        
        # Check for Series Id
        if 'Series Id:' in line:
            # Save previous record if exists
            if current_record.get('Series Id'):
                results.append(current_record)
            
            # Start new record
            parts = line.split('Series Id:', 1)
            current_record = {
                'Series Id': parts[1].strip() if len(parts) > 1 else '',
                'Series Title': '',
                'Area': '',
                'Item': '',
                'Last Average Price': None
            }
        
        # Check for Series Title
        elif 'Series Title:' in line and current_record.get('Series Id'):
            parts = line.split('Series Title:', 1)
            if len(parts) > 1:
                current_record['Series Title'] = parts[1].strip()
        
        # Check for Area
        elif 'Area:' in line and current_record.get('Series Id'):
            parts = line.split('Area:', 1)
            if len(parts) > 1:
                current_record['Area'] = parts[1].strip()
        
        # Check for Item
        elif 'Item:' in line and current_record.get('Series Id'):
            parts = line.split('Item:', 1)
            if len(parts) > 1:
                current_record['Item'] = parts[1].strip()
        
        # Check for data line (starts with 2025)
        elif line.strip().startswith('2025') and current_record.get('Series Id'):
            if 'No Data Available' in line:
                current_record['Last Average Price'] = 'No Data'
            else:
                # Split by tab and find last non-empty price
                parts = line.split('\t')
                for price_str in reversed(parts[1:]):  # Skip "2025"
                    price_str = price_str.strip()
                    if price_str:
                        try:
                            current_record['Last Average Price'] = float(price_str)
                            break
                        except ValueError:
                            continue
        
        i += 1
    
    # Don't forget the last record
    if current_record.get('Series Id'):
        results.append(current_record)
    
    # Write to CSV
    fieldnames = ['Series Id', 'Series Title', 'Area', 'Item', 'Last Average Price']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in results:
            # Convert None to 'No Data'
            if record['Last Average Price'] is None:
                record['Last Average Price'] = 'No Data'
            writer.writerow(record)
    
    return len(results)

if __name__ == '__main__':
    import sys
    import traceback
    
    input_file = 'data/cpi/bls_average_price_series_id_2025_raw.csv'
    output_file = 'data/cpi/bls_extracted_data.csv'
    
    try:
        count = extract_bls_data(input_file, output_file)
        print(f"Extracted {count} records to {output_file}", file=sys.stdout)
        sys.stdout.flush()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
