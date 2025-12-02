import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from category_mapping import get_cpi_category
from essential_classification import classify_item_essential

def calculate_cpi_inflation(cpi_df):
    """
    Calculate year-over-year and cumulative inflation rates for CPI data.
    
    Args:
        cpi_df: DataFrame with columns: year, cpi_type, value
    
    Returns:
        DataFrame with inflation rates
    """
    results = []
    
    for cpi_type in cpi_df['cpi_type'].unique():
        type_data = cpi_df[cpi_df['cpi_type'] == cpi_type].sort_values('year')
        
        # Get baseline year (2019)
        baseline = type_data[type_data['year'] == 2019]['value'].values
        if len(baseline) == 0:
            continue
        baseline_value = baseline[0]
        
        for idx, row in type_data.iterrows():
            year = row['year']
            value = row['value']
            
            # Year-over-year inflation
            yoy_inflation = None
            if year > 2019:
                prev_year_data = type_data[type_data['year'] == year - 1]
                if len(prev_year_data) > 0:
                    prev_value = prev_year_data['value'].values[0]
                    yoy_inflation = ((value - prev_value) / prev_value) * 100
            
            # Cumulative inflation from 2019 baseline
            cumulative_inflation = ((value - baseline_value) / baseline_value) * 100
            
            results.append({
                'year': year,
                'cpi_type': cpi_type,
                'cpi_value': value,
                'yoy_inflation_pct': yoy_inflation,
                'cumulative_inflation_pct': cumulative_inflation
            })
    
    return pd.DataFrame(results)

def identify_fixed_basket_items(commissary_df, required_years):
    """
    Identify items that are present in ALL required years (fixed basket).
    
    Args:
        commissary_df: DataFrame with columns: year, item_name, size
        required_years: List of years that items must be present in (e.g., [2019, 2020, 2021, 2022, 2023, 2024, 2025])
    
    Returns:
        List of item_ids that appear in all required years
    """
    # Create item_id (item_name + size)
    commissary_df = commissary_df.copy()
    commissary_df['item_id'] = commissary_df['item_name'] + '|' + commissary_df['size'].fillna('')
    
    # Count years per item
    item_year_counts = commissary_df.groupby('item_id')['year'].apply(set).reset_index()
    item_year_counts['years_present'] = item_year_counts['year']
    
    # Check which items have all required years
    required_years_set = set(required_years)
    fixed_basket_items = []
    
    for _, row in item_year_counts.iterrows():
        item_years = row['years_present']
        if required_years_set.issubset(item_years):
            fixed_basket_items.append(row['item_id'])
    
    return fixed_basket_items

def calculate_commissary_inflation(commissary_df, required_years=None):
    """
    Calculate inflation rates for commissary items using fixed basket approach.
    Only items present in ALL required years are included.
    
    Args:
        commissary_df: DataFrame with columns: year, category, item_name, size, price_min, price_max
        required_years: List of years items must be present in (default: [2019, 2020, 2021, 2022, 2023, 2024, 2025])
    
    Returns:
        Dictionary with:
        - 'item_level': DataFrame with item-level inflation rates
        - 'category_level': DataFrame with category-level inflation rates
        - 'cpi_category_level': DataFrame with CPI category-level inflation rates
        - 'overall': DataFrame with overall inflation rates
        - 'fixed_basket_info': Dictionary with fixed basket statistics
    """
    if required_years is None:
        required_years = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    
    # Use average of price_min and price_max
    commissary_df = commissary_df.copy()
    commissary_df['price_avg'] = (commissary_df['price_min'] + commissary_df['price_max']) / 2
    
    # Add CPI category mapping
    commissary_df['cpi_category'] = commissary_df['category'].apply(get_cpi_category)
    
    # Create item_id (item_name + size)
    commissary_df['item_id'] = commissary_df['item_name'] + '|' + commissary_df['size'].fillna('')
    
    # Identify fixed basket items (present in all required years)
    fixed_basket_items = identify_fixed_basket_items(commissary_df, required_years)
    
    # Filter to only fixed basket items
    original_item_count = commissary_df['item_id'].nunique()
    commissary_df = commissary_df[commissary_df['item_id'].isin(fixed_basket_items)].copy()
    fixed_basket_item_count = len(fixed_basket_items)
    
    # Store fixed basket info for reporting
    fixed_basket_info = {
        'total_items_original': original_item_count,
        'fixed_basket_items': fixed_basket_item_count,
        'items_excluded': original_item_count - fixed_basket_item_count,
        'required_years': required_years
    }
    
    # Item-level inflation
    item_results = []
    
    for item_id in fixed_basket_items:
        item_data = commissary_df[commissary_df['item_id'] == item_id].sort_values('year')
        
        # Fixed basket items are guaranteed to have all years, but check anyway
        if len(item_data) < len(required_years):
            continue
        
        # Use 2019 as consistent baseline for all items
        baseline_year = 2019
        baseline_data = item_data[item_data['year'] == baseline_year]
        if len(baseline_data) == 0:
            continue
        baseline_price = baseline_data['price_avg'].values[0]
        
        category = item_data['category'].iloc[0]
        cpi_category = item_data['cpi_category'].iloc[0]
        item_name = item_data['item_name'].iloc[0]
        size = item_data['size'].iloc[0]
        
        # Classify item as essential or non-essential
        essential_status = classify_item_essential(item_name, category)
        
        for idx, row in item_data.iterrows():
            year = row['year']
            price = row['price_avg']
            
            # Year-over-year inflation
            yoy_inflation = None
            if year > min(required_years):
                prev_year_data = item_data[item_data['year'] == year - 1]
                if len(prev_year_data) > 0:
                    prev_price = prev_year_data['price_avg'].values[0]
                    yoy_inflation = ((price - prev_price) / prev_price) * 100
            
            # Cumulative inflation from 2019 baseline
            cumulative_inflation = ((price - baseline_price) / baseline_price) * 100
            
            item_results.append({
                'year': year,
                'category': category,
                'cpi_category': cpi_category,
                'item_name': item_name,
                'size': size,
                'price': price,
                'essential_status': essential_status,
                'yoy_inflation_pct': yoy_inflation,
                'cumulative_inflation_pct': cumulative_inflation
            })
    
    item_df = pd.DataFrame(item_results)
    
    # Category-level inflation (average across items in category)
    category_results = []
    
    for year in sorted(commissary_df['year'].unique()):
        year_data = commissary_df[commissary_df['year'] == year]
        
        for category in year_data['category'].unique():
            cat_data = year_data[year_data['category'] == category]
            cpi_category = cat_data['cpi_category'].iloc[0]
            
            # Calculate average price for this category in this year
            avg_price = cat_data['price_avg'].mean()
            
            # Get baseline year average for this category
            baseline_data = commissary_df[
                (commissary_df['category'] == category) & 
                (commissary_df['year'] == 2019)
            ]
            if len(baseline_data) > 0:
                baseline_price = baseline_data['price_avg'].mean()
                cumulative_inflation = ((avg_price - baseline_price) / baseline_price) * 100
            else:
                cumulative_inflation = None
            
            # Year-over-year
            yoy_inflation = None
            if year > 2019:
                prev_year_data = commissary_df[
                    (commissary_df['category'] == category) & 
                    (commissary_df['year'] == year - 1)
                ]
                if len(prev_year_data) > 0:
                    prev_avg_price = prev_year_data['price_avg'].mean()
                    yoy_inflation = ((avg_price - prev_avg_price) / prev_avg_price) * 100
            
            category_results.append({
                'year': year,
                'category': category,
                'cpi_category': cpi_category,
                'avg_price': avg_price,
                'yoy_inflation_pct': yoy_inflation,
                'cumulative_inflation_pct': cumulative_inflation
            })
    
    category_df = pd.DataFrame(category_results)
    
    # CPI category-level inflation (aggregate by CPI category)
    cpi_category_results = []
    
    for year in sorted(commissary_df['year'].unique()):
        year_data = commissary_df[commissary_df['year'] == year]
        
        for cpi_category in year_data['cpi_category'].unique():
            cpi_cat_data = year_data[year_data['cpi_category'] == cpi_category]
            
            avg_price = cpi_cat_data['price_avg'].mean()
            
            # Baseline
            baseline_data = commissary_df[
                (commissary_df['cpi_category'] == cpi_category) & 
                (commissary_df['year'] == 2019)
            ]
            if len(baseline_data) > 0:
                baseline_price = baseline_data['price_avg'].mean()
                cumulative_inflation = ((avg_price - baseline_price) / baseline_price) * 100
            else:
                cumulative_inflation = None
            
            # Year-over-year
            yoy_inflation = None
            if year > 2019:
                prev_year_data = commissary_df[
                    (commissary_df['cpi_category'] == cpi_category) & 
                    (commissary_df['year'] == year - 1)
                ]
                if len(prev_year_data) > 0:
                    prev_avg_price = prev_year_data['price_avg'].mean()
                    yoy_inflation = ((avg_price - prev_avg_price) / prev_avg_price) * 100
            
            cpi_category_results.append({
                'year': year,
                'cpi_category': cpi_category,
                'avg_price': avg_price,
                'yoy_inflation_pct': yoy_inflation,
                'cumulative_inflation_pct': cumulative_inflation
            })
    
    cpi_category_df = pd.DataFrame(cpi_category_results)
    
    # Overall commissary inflation
    overall_results = []
    
    for year in sorted(commissary_df['year'].unique()):
        year_data = commissary_df[commissary_df['year'] == year]
        avg_price = year_data['price_avg'].mean()
        
        # Baseline
        baseline_data = commissary_df[commissary_df['year'] == 2019]
        baseline_price = baseline_data['price_avg'].mean()
        cumulative_inflation = ((avg_price - baseline_price) / baseline_price) * 100
        
        # Year-over-year
        yoy_inflation = None
        if year > 2019:
            prev_year_data = commissary_df[commissary_df['year'] == year - 1]
            prev_avg_price = prev_year_data['price_avg'].mean()
            yoy_inflation = ((avg_price - prev_avg_price) / prev_avg_price) * 100
        
        overall_results.append({
            'year': year,
            'level': 'overall',
            'avg_price': avg_price,
            'yoy_inflation_pct': yoy_inflation,
            'cumulative_inflation_pct': cumulative_inflation
        })
    
    overall_df = pd.DataFrame(overall_results)
    
    return {
        'item_level': item_df,
        'category_level': category_df,
        'cpi_category_level': cpi_category_df,
        'overall': overall_df,
        'fixed_basket_info': fixed_basket_info
    }

def compare_inflation(cpi_inflation_df, commissary_inflation_dict):
    """
    Compare commissary inflation to CPI inflation.
    
    Args:
        cpi_inflation_df: DataFrame with CPI inflation rates
        commissary_inflation_dict: Dictionary with commissary inflation dataframes
    
    Returns:
        DataFrame with comparison metrics
    """
    comparisons = []
    
    # Overall comparison: Commissary vs CPI-U
    cpi_u_data = cpi_inflation_df[cpi_inflation_df['cpi_type'] == 'CPI-U']
    overall_commissary = commissary_inflation_dict['overall']
    
    for year in sorted(set(cpi_u_data['year'].unique()) & set(overall_commissary['year'].unique())):
        cpi_row = cpi_u_data[cpi_u_data['year'] == year].iloc[0]
        comm_row = overall_commissary[overall_commissary['year'] == year].iloc[0]
        
        cpi_yoy = cpi_row['yoy_inflation_pct']
        comm_yoy = comm_row['yoy_inflation_pct']
        cpi_cum = cpi_row['cumulative_inflation_pct']
        comm_cum = comm_row['cumulative_inflation_pct']
        
        if cpi_yoy is not None and comm_yoy is not None:
            yoy_diff = comm_yoy - cpi_yoy
        else:
            yoy_diff = None
        
        if cpi_cum is not None and comm_cum is not None:
            cum_diff = comm_cum - cpi_cum
        else:
            cum_diff = None
        
        comparisons.append({
            'year': year,
            'level': 'overall',
            'cpi_type': 'CPI-U',
            'commissary_yoy_pct': comm_yoy,
            'cpi_yoy_pct': cpi_yoy,
            'yoy_diff_pct': yoy_diff,
            'commissary_cum_pct': comm_cum,
            'cpi_cum_pct': cpi_cum,
            'cum_diff_pct': cum_diff
        })
    
    # CPI category-level comparisons
    cpi_category_commissary = commissary_inflation_dict['cpi_category_level']
    
    for cpi_category in cpi_category_commissary['cpi_category'].unique():
        if cpi_category == 'CPI-U':
            continue  # Already handled above
        
        cpi_data = cpi_inflation_df[cpi_inflation_df['cpi_type'] == cpi_category]
        comm_data = cpi_category_commissary[cpi_category_commissary['cpi_category'] == cpi_category]
        
        for year in sorted(set(cpi_data['year'].unique()) & set(comm_data['year'].unique())):
            cpi_row = cpi_data[cpi_data['year'] == year]
            comm_row = comm_data[comm_data['year'] == year]
            
            if len(cpi_row) == 0 or len(comm_row) == 0:
                continue
            
            cpi_row = cpi_row.iloc[0]
            comm_row = comm_row.iloc[0]
            
            cpi_yoy = cpi_row['yoy_inflation_pct']
            comm_yoy = comm_row['yoy_inflation_pct']
            cpi_cum = cpi_row['cumulative_inflation_pct']
            comm_cum = comm_row['cumulative_inflation_pct']
            
            if cpi_yoy is not None and comm_yoy is not None:
                yoy_diff = comm_yoy - cpi_yoy
            else:
                yoy_diff = None
            
            if cpi_cum is not None and comm_cum is not None:
                cum_diff = comm_cum - cpi_cum
            else:
                cum_diff = None
            
            comparisons.append({
                'year': year,
                'level': 'cpi_category',
                'cpi_type': cpi_category,
                'commissary_yoy_pct': comm_yoy,
                'cpi_yoy_pct': cpi_yoy,
                'yoy_diff_pct': yoy_diff,
                'commissary_cum_pct': comm_cum,
                'cpi_cum_pct': cpi_cum,
                'cum_diff_pct': cum_diff
            })
    
    return pd.DataFrame(comparisons)

def main():
    # Load data (relative to project root)
    project_root = Path(__file__).parent.parent.parent
    print("Loading data...")
    cpi_file = project_root / "data" / "cpi" / "cpi_data.csv"
    commissary_file = project_root / "data" / "commissary" / "processed" / "texas" / "texas_commissary_filtered_5plus_years.csv"
    
    if not cpi_file.exists():
        print(f"Error: CPI data file not found at {cpi_file}")
        print("Please run fetch_cpi_data.py first.")
        return
    
    if not commissary_file.exists():
        print(f"Error: Commissary data file not found at {commissary_file}")
        return
    
    cpi_df = pd.read_csv(cpi_file)
    commissary_df = pd.read_csv(commissary_file)
    
    print(f"Loaded CPI data: {len(cpi_df)} records")
    print(f"Loaded commissary data: {len(commissary_df)} records")
    
    # Calculate inflation rates
    print("\nCalculating CPI inflation rates...")
    cpi_inflation = calculate_cpi_inflation(cpi_df)
    
    print("Calculating commissary inflation rates (using fixed basket methodology)...")
    commissary_inflation_result = calculate_commissary_inflation(commissary_df)
    commissary_inflation = {k: v for k, v in commissary_inflation_result.items() if k != 'fixed_basket_info'}
    fixed_basket_info = commissary_inflation_result['fixed_basket_info']
    
    # Report on fixed basket
    print(f"\n{'='*60}")
    print("FIXED BASKET METHODOLOGY")
    print('='*60)
    print(f"Required years: {fixed_basket_info['required_years']}")
    print(f"Total items in dataset: {fixed_basket_info['total_items_original']}")
    print(f"Items in fixed basket (present in all years): {fixed_basket_info['fixed_basket_items']}")
    print(f"Items excluded: {fixed_basket_info['items_excluded']}")
    if fixed_basket_info['total_items_original'] > 0:
        print(f"Percentage of items included: {100 * fixed_basket_info['fixed_basket_items'] / fixed_basket_info['total_items_original']:.1f}%")
    
    # Breakdown by category using item-level results
    if len(commissary_inflation['item_level']) > 0:
        item_df = commissary_inflation['item_level']
        print(f"\nFixed basket items by category:")
        category_counts = item_df.groupby('category')['item_name'].nunique().sort_values(ascending=False)
        for category, count in category_counts.items():
            print(f"  {category}: {count} items")
    
    print("Comparing inflation rates...")
    comparisons = compare_inflation(cpi_inflation, commissary_inflation)
    
    # Create output directory (relative to script location)
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    print(f"\n{'='*60}")
    print("Saving results...")
    print('='*60)
    
    # Save all results to a single CSV with multiple sheets would require Excel
    # Instead, save separate files for different levels
    cpi_inflation.to_csv(output_dir / "cpi_inflation.csv", index=False)
    commissary_inflation['item_level'].to_csv(output_dir / "commissary_inflation_item_level.csv", index=False)
    commissary_inflation['category_level'].to_csv(output_dir / "commissary_inflation_category_level.csv", index=False)
    commissary_inflation['cpi_category_level'].to_csv(output_dir / "commissary_inflation_cpi_category_level.csv", index=False)
    commissary_inflation['overall'].to_csv(output_dir / "commissary_inflation_overall.csv", index=False)
    comparisons.to_csv(output_dir / "inflation_comparisons.csv", index=False)
    
    print(f"Saved CPI inflation: {output_dir / 'cpi_inflation.csv'}")
    print(f"Saved item-level commissary inflation: {output_dir / 'commissary_inflation_item_level.csv'}")
    print(f"Saved category-level commissary inflation: {output_dir / 'commissary_inflation_category_level.csv'}")
    print(f"Saved CPI category-level commissary inflation: {output_dir / 'commissary_inflation_cpi_category_level.csv'}")
    print(f"Saved overall commissary inflation: {output_dir / 'commissary_inflation_overall.csv'}")
    print(f"Saved inflation comparisons: {output_dir / 'inflation_comparisons.csv'}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("Summary Statistics")
    print('='*60)
    
    print("\nOverall Commissary vs CPI-U (Cumulative Inflation):")
    overall_comps = comparisons[comparisons['level'] == 'overall']
    for _, row in overall_comps.iterrows():
        print(f"  {int(row['year'])}: Commissary {row['commissary_cum_pct']:.2f}% vs CPI-U {row['cpi_cum_pct']:.2f}% (diff: {row['cum_diff_pct']:.2f}%)")
    
    print("\nCPI Category Comparisons (2024 Cumulative Inflation):")
    category_comps = comparisons[
        (comparisons['level'] == 'cpi_category') & 
        (comparisons['year'] == 2024)
    ]
    for _, row in category_comps.iterrows():
        print(f"  {row['cpi_type']}: Commissary {row['commissary_cum_pct']:.2f}% vs CPI {row['cpi_cum_pct']:.2f}% (diff: {row['cum_diff_pct']:.2f}%)")

if __name__ == "__main__":
    main()

