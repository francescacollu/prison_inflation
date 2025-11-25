import pdfplumber
import pandas as pd
import re
from pathlib import Path

def parse_item_line(line, category):
    """Parse a single item line to extract name, size, and price (including ranges)."""
    line = line.strip()
    
    if not line or line.startswith('E ') or line.startswith('K ') or line.startswith('H ') or line.startswith('G '):
        # Remove facility codes at start
        line = re.sub(r'^[EGHK]+\s+', '', line)
    
    # Check for price range first (pattern: $X.XX-$Y.YY or X.XX-Y.YY)
    price_range_match = re.search(r'\$?(\d+\.?\d{0,2})\s*-\s*\$?(\d+\.?\d{0,2})$', line)
    
    if price_range_match:
        # Price range found
        try:
            min_price = float(price_range_match.group(1))
            max_price = float(price_range_match.group(2))
        except (ValueError, AttributeError):
            return None
        
        # Remove price range from line
        text_without_price = line[:price_range_match.start()].strip()
        
    else:
        # Single price (pattern: $X.XX or X.XX)
        price_match = re.search(r'\$?(\d+\.\d{2})$', line)
        if not price_match:
            # Try with just dollar amount
            price_match = re.search(r'\$?(\d+)$', line)
            if not price_match:
                return None
        
        try:
            price = float(price_match.group(1))
            min_price = price
            max_price = price
        except (ValueError, AttributeError):
            return None
        
        # Remove price from line
        text_without_price = line[:price_match.start()].strip()
    
    # Try to extract size
    size_patterns = [
        r'[-\s](\d+\.?\d*\s*oz)$',
        r'[-\s](\d+\.?\d*\s*lb)$',
        r'[-\s](\d+\s*pk)$',
        r'\((\d+\s*pk)\)$',
        r'\((\d+\s*ct)\)$',
        r'\((\d+\s*piece)\)$',
        r'\((\d+\s*tabs)\)$',
        r'\((\d+\s*tablets)\)$',
        r'\((\d+\s*bags)\)$',
        r'\((\d+\s*sheet)\)$',
        r'\((\d+\s*sht)\)$',
        r'[-\s](\d+\.?\d*")$',
        r'[-\s](\d+x\d+)$',
    ]
    
    size = ''
    item_name = text_without_price
    
    for pattern in size_patterns:
        size_match = re.search(pattern, text_without_price, re.IGNORECASE)
        if size_match:
            size = size_match.group(1).strip()
            item_name = text_without_price[:size_match.start()].strip(' -')
            break
    
    return {
        'category': category,
        'item_name': item_name,
        'size': size,
        'price_min': min_price,
        'price_max': max_price
    }

def extract_items_from_pdf(pdf_path, year):
    """Extract all items from all tables in a PDF."""
    items = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                # First row is category header
                category = table[0][0] if table[0] else 'UNKNOWN'
                category = category.strip()
                
                # Second row contains all items separated by newlines
                if len(table) > 1 and table[1] and table[1][0]:
                    items_text = table[1][0]
                    
                    # Split by newlines to get individual items
                    item_lines = items_text.split('\n')
                    
                    for item_line in item_lines:
                        if not item_line.strip():
                            continue
                        
                        # Skip if line looks like a header
                        if 'TDCJ' in item_line or 'Price List' in item_line:
                            continue
                        
                        # Parse the item
                        item_data = parse_item_line(item_line, category)
                        if item_data and item_data['price_max'] > 0:
                            items.append({
                                'year': year,
                                **item_data
                            })
    
    return items

def main():
    # Process all PDF files
    pdf_dir = Path('data/commissary/texas')
    output_dir = Path('data/commissary/processed/texas')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_items = []
    
    # Get all PDF files and sort them
    pdf_files = sorted(pdf_dir.glob('*.pdf'))
    
    print(f"Found {len(pdf_files)} PDF files to process\n")
    
    for pdf_file in pdf_files:
        year = pdf_file.stem
        print(f"Processing {year}.pdf...")
        
        items = extract_items_from_pdf(pdf_file, year)
        all_items.extend(items)
        
        print(f"  Extracted {len(items)} items")
    
    # Create combined DataFrame
    df = pd.DataFrame(all_items)
    
    if len(df) > 0:
        # Sort by year, category, and item name
        df = df.sort_values(['year', 'category', 'item_name'])
        
        # Save combined CSV
        output_file = output_dir / 'texas_commissary_all_years_combined.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*60}")
        print(f"COMBINED RESULTS")
        print('='*60)
        print(f"Total items extracted: {len(df)}")
        print(f"Saved to: {output_file}")
        
        print(f"\nItems per year:")
        print(df.groupby('year').size())
        
        print(f"\nTop 10 categories:")
        print(df.groupby('category').size().sort_values(ascending=False).head(10))
        
        print(f"\nSample of combined data:")
        print(df.head(20).to_string(index=False))
    else:
        print("No items extracted!")

if __name__ == '__main__':
    main()

