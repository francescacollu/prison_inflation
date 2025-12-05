"""
Compare commissary prices to average/median retail prices (HEB) for 2025.

This script compares each commissary item to the average or median retail price
for its category, normalizes sizes, and calculates price differences and markups.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from essential_classification import classify_item_essential
from category_mapping import get_cpi_category


def normalize_size_to_oz(size_str):
    """
    Normalize size string to ounces for comparison.
    
    Handles: oz, lb, ct (count), pk (pack), etc.
    Returns: (size_in_oz, unit_type) or (None, None) if cannot parse
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
        # For count-based items, we can't convert to weight
        # Return as-is with count unit
        return number, 'ct'
    elif 'sheet' in size_str or 'sheet' in size_str:
        return number, 'ct'
    else:
        # Try to infer - if it's a small number (< 50), might be count
        # If larger, might be ounces
        if number < 50:
            return number, 'ct'
        else:
            return number, 'oz'  # Assume ounces if unclear


def extract_size_number(size_str):
    """Extract just the numeric size value."""
    if pd.isna(size_str) or size_str == '':
        return None
    
    size_str = str(size_str).strip()
    number_match = re.search(r'(\d+\.?\d*)', size_str)
    if number_match:
        try:
            return float(number_match.group(1))
        except ValueError:
            return None
    return None


def compare_to_average_retail_prices(commissary_df, retail_df, comparison_categories, use_median=False):
    """
    Compare each commissary item to average/median retail prices for its category.
    
    Args:
        commissary_df: DataFrame with commissary items
        retail_df: DataFrame with retail items
        comparison_categories: List of comparison category names
        use_median: If True, use median; if False, use mean
    
    Returns:
        List of comparisons with average/median retail prices
    """
    matches = []
    
    # Create mapping from comparison categories to commissary search terms
    category_to_commissary = {
        'Colombian coffee': ['colombian', 'coffee'],
        'Instant coffee': ['instant coffee', 'coffee instant'],
        'Instant ramen': ['ramen', 'noodle'],
        'Peanut butter': ['peanut butter'],
        'Oatmeal': ['oatmeal'],
        'Snickers bar': ['snickers'],
        'Bar soap': ['soap', 'bar soap'],
        'Shampoo': ['shampoo'],
        'Toothpaste': ['toothpaste', 'colgate'],
        'Deodorant stick': ['deodorant'],
        'Body lotion': ['lotion'],
        "Men's boxer briefs": ['boxer', 'briefs'],
        "Women's sweatpants": ['sweatpants', 'pants'],
        'White crew socks': ['socks', 'crew socks'],
        'Basic white t-shirt': ['t-shirt', 'tshirt', 'shirt'],
    }
    
    for comp_category, search_terms in category_to_commissary.items():
        # Find all retail items in this category
        retail_category_items = retail_df[
            retail_df['item_category'].str.lower() == comp_category.lower()
        ].copy()
        
        if len(retail_category_items) == 0:
            continue
        
        # Calculate price per unit for all retail items
        retail_prices_per_unit = []
        for _, retail_row in retail_category_items.iterrows():
            retail_size = retail_row['item_size']
            retail_price = retail_row['item_price']
            
            # Normalize retail size
            retail_size_oz, retail_unit = normalize_size_to_oz(retail_size)
            
            # Calculate price per unit
            if retail_size_oz and retail_unit == 'oz' and retail_size_oz > 0:
                price_per_oz = retail_price / retail_size_oz
                retail_prices_per_unit.append(price_per_oz)
            elif retail_row.get('price_per_unit') and pd.notna(retail_row['price_per_unit']):
                if retail_row.get('price_per_unit_type') == 'oz':
                    retail_prices_per_unit.append(retail_row['price_per_unit'])
        
        if len(retail_prices_per_unit) == 0:
            continue
        
        # Calculate average or median retail price per unit
        if use_median:
            avg_retail_price_per_oz = np.median(retail_prices_per_unit)
        else:
            avg_retail_price_per_oz = np.mean(retail_prices_per_unit)
        
        # Find matching commissary items
        for _, comm_row in commissary_df.iterrows():
            item_name_lower = str(comm_row['item_name']).lower()
            if any(term in item_name_lower for term in search_terms):
                comm_size = comm_row['size']
                comm_price_avg = (comm_row['price_min'] + comm_row['price_max']) / 2
                
                # Normalize commissary size
                comm_size_oz, comm_unit = normalize_size_to_oz(comm_size)
                
                # Calculate commissary price per unit
                if comm_size_oz and comm_unit == 'oz' and comm_size_oz > 0:
                    comm_price_per_oz = comm_price_avg / comm_size_oz
                else:
                    comm_price_per_oz = None
                
                # Calculate markup if we have comparable prices
                markup_pct = None
                price_diff = None
                if comm_price_per_oz and avg_retail_price_per_oz > 0:
                    price_diff = comm_price_per_oz - avg_retail_price_per_oz
                    markup_pct = ((comm_price_per_oz - avg_retail_price_per_oz) / avg_retail_price_per_oz) * 100
                
                matches.append({
                    'comparison_category': comp_category,
                    'commissary_item_name': comm_row['item_name'],
                    'commissary_category': comm_row['category'],
                    'commissary_size': comm_size,
                    'commissary_size_oz': comm_size_oz,
                    'commissary_unit': comm_unit,
                    'commissary_price': comm_price_avg,
                    'commissary_price_per_oz': comm_price_per_oz,
                    'retail_items_count': len(retail_category_items),
                    'retail_price_per_oz_avg': avg_retail_price_per_oz,
                    'retail_price_per_oz_median': np.median(retail_prices_per_unit) if len(retail_prices_per_unit) > 0 else None,
                    'retail_price_per_oz_min': np.min(retail_prices_per_unit) if len(retail_prices_per_unit) > 0 else None,
                    'retail_price_per_oz_max': np.max(retail_prices_per_unit) if len(retail_prices_per_unit) > 0 else None,
                    'price_difference_per_oz': price_diff,
                    'markup_percentage': markup_pct,
                    'essential_status': classify_item_essential(comm_row['item_name'], comm_row['category'])
                })
    
    return matches


def generate_comparison_report(matches_df, output_dir, use_median=False):
    """Generate a comprehensive comparison report."""
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("COMMISSARY vs RETAIL PRICE COMPARISON (2025)")
    report_lines.append("=" * 80)
    report_lines.append(f"Comparing commissary prices to {'median' if use_median else 'average'} retail prices by category")
    report_lines.append("")
    
    # Summary statistics
    valid_matches = matches_df[matches_df['markup_percentage'].notna()]
    
    if len(valid_matches) > 0:
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Total commissary items compared: {len(matches_df)}")
        report_lines.append(f"Items with comparable prices: {len(valid_matches)}")
        report_lines.append("")
        
        report_lines.append(f"Average markup: {valid_matches['markup_percentage'].mean():.1f}%")
        report_lines.append(f"Median markup: {valid_matches['markup_percentage'].median():.1f}%")
        report_lines.append(f"Minimum markup: {valid_matches['markup_percentage'].min():.1f}%")
        report_lines.append(f"Maximum markup: {valid_matches['markup_percentage'].max():.1f}%")
        report_lines.append("")
        
        # By category
        report_lines.append("MARKUP BY COMPARISON CATEGORY")
        report_lines.append("-" * 80)
        category_stats = valid_matches.groupby('comparison_category').agg({
            'markup_percentage': ['count', 'mean', 'median', 'min', 'max'],
            'retail_items_count': 'first',
            'retail_price_per_oz_avg': 'first',
            'retail_price_per_oz_min': 'first',
            'retail_price_per_oz_max': 'first'
        }).round(2)
        
        for category in category_stats.index:
            row = category_stats.loc[category]
            count = int(row[('markup_percentage', 'count')])
            avg_markup = row[('markup_percentage', 'mean')]
            median_markup = row[('markup_percentage', 'median')]
            retail_count = int(row[('retail_items_count', 'first')])
            retail_avg = row[('retail_price_per_oz_avg', 'first')]
            retail_min = row[('retail_price_per_oz_min', 'first')]
            retail_max = row[('retail_price_per_oz_max', 'first')]
            
            report_lines.append(f"{category}:")
            report_lines.append(f"  Commissary items: {count}")
            report_lines.append(f"  Retail items used for comparison: {retail_count}")
            report_lines.append(f"  Average markup: {avg_markup:.1f}%")
            report_lines.append(f"  Median markup: {median_markup:.1f}%")
            report_lines.append(f"  Retail price range: ${retail_min:.2f}/oz - ${retail_max:.2f}/oz (avg: ${retail_avg:.2f}/oz)")
            report_lines.append("")
        
        # Essential vs Non-essential
        report_lines.append("MARKUP BY ESSENTIAL STATUS")
        report_lines.append("-" * 80)
        essential_stats = valid_matches.groupby('essential_status')['markup_percentage'].agg([
            'count', 'mean', 'median'
        ]).round(1)
        essential_stats.columns = ['Count', 'Avg Markup %', 'Median Markup %']
        for status, row in essential_stats.iterrows():
            report_lines.append(f"{status.title()}:")
            report_lines.append(f"  Count: {int(row['Count'])}")
            report_lines.append(f"  Average markup: {row['Avg Markup %']:.1f}%")
            report_lines.append(f"  Median markup: {row['Median Markup %']:.1f}%")
            report_lines.append("")
        
        # Top 10 highest markups
        report_lines.append("TOP 10 HIGHEST MARKUPS")
        report_lines.append("-" * 80)
        top_markups = valid_matches.nlargest(10, 'markup_percentage')[
            ['commissary_item_name', 'comparison_category', 'markup_percentage', 
             'commissary_price_per_oz', 'retail_price_per_oz_avg']
        ]
        for idx, row in top_markups.iterrows():
            report_lines.append(f"{row['commissary_item_name']} ({row['comparison_category']})")
            report_lines.append(f"  Markup: {row['markup_percentage']:.1f}%")
            report_lines.append(f"  Commissary: ${row['commissary_price_per_oz']:.2f}/oz | Retail avg: ${row['retail_price_per_oz_avg']:.2f}/oz")
            report_lines.append("")
        
        # Top 10 lowest markups (best deals)
        report_lines.append("TOP 10 LOWEST MARKUPS (Best Deals)")
        report_lines.append("-" * 80)
        bottom_markups = valid_matches.nsmallest(10, 'markup_percentage')[
            ['commissary_item_name', 'comparison_category', 'markup_percentage', 
             'commissary_price_per_oz', 'retail_price_per_oz_avg']
        ]
        for idx, row in bottom_markups.iterrows():
            report_lines.append(f"{row['commissary_item_name']} ({row['comparison_category']})")
            report_lines.append(f"  Markup: {row['markup_percentage']:.1f}%")
            report_lines.append(f"  Commissary: ${row['commissary_price_per_oz']:.2f}/oz | Retail avg: ${row['retail_price_per_oz_avg']:.2f}/oz")
            report_lines.append("")
    
    # Write report
    report_text = "\n".join(report_lines)
    report_file = output_dir / "commissary_retail_comparison_report.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\nReport saved to: {report_file}")


def main():
    """Main function to run the comparison."""
    project_root = Path(__file__).parent.parent.parent
    
    # Load data
    print("Loading data...")
    commissary_file = project_root / "data" / "commissary" / "processed" / "texas" / "texas_commissary_2025.csv"
    retail_file = project_root / "data" / "retail" / "processed" / "heb_parsed_results.csv"
    comparison_categories_file = project_root / "data" / "retail" / "comparison_item_list.csv"
    
    if not commissary_file.exists():
        print(f"Error: Commissary file not found at {commissary_file}")
        return
    
    if not retail_file.exists():
        print(f"Error: Retail file not found at {retail_file}")
        return
    
    commissary_df = pd.read_csv(commissary_file)
    retail_df = pd.read_csv(retail_file)
    comparison_categories_df = pd.read_csv(comparison_categories_file)
    
    print(f"Loaded {len(commissary_df)} commissary items")
    print(f"Loaded {len(retail_df)} retail items")
    print(f"Loaded {len(comparison_categories_df)} comparison categories")
    
    # Compare items to average/median retail prices
    print("\nComparing commissary items to average retail prices by category...")
    comparison_categories = comparison_categories_df['item'].tolist()
    use_median = False  # Set to True to use median instead of mean
    matches = compare_to_average_retail_prices(commissary_df, retail_df, comparison_categories, use_median=use_median)
    
    if len(matches) == 0:
        print("No matches found. Check your matching logic.")
        return
    
    print(f"Found {len(matches)} commissary items to compare")
    
    # Convert to DataFrame
    matches_df = pd.DataFrame(matches)
    
    # Create output directory
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed matches
    output_file = output_dir / "commissary_retail_comparison.csv"
    matches_df.to_csv(output_file, index=False)
    print(f"\nSaved detailed comparisons to: {output_file}")
    
    # Generate report
    print("\nGenerating comparison report...")
    generate_comparison_report(matches_df, output_dir, use_median=use_median)
    
    # Save summary statistics
    valid_matches = matches_df[matches_df['markup_percentage'].notna()]
    if len(valid_matches) > 0:
        summary_stats = {
            'total_matches': len(matches_df),
            'comparable_matches': len(valid_matches),
            'avg_markup_pct': valid_matches['markup_percentage'].mean(),
            'median_markup_pct': valid_matches['markup_percentage'].median(),
            'min_markup_pct': valid_matches['markup_percentage'].min(),
            'max_markup_pct': valid_matches['markup_percentage'].max(),
        }
        
        summary_df = pd.DataFrame([summary_stats])
        summary_file = output_dir / "commissary_retail_comparison_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"Saved summary statistics to: {summary_file}")


if __name__ == "__main__":
    main()

