import pandas as pd
from pathlib import Path

def filter_by_year_coverage(df, min_years=5):
    """Filter dataset to items appearing in at least min_years."""
    
    # Count years per item
    item_year_count = df.groupby('item_name')['year'].nunique()
    
    # Get items meeting threshold
    common_items = item_year_count[item_year_count >= min_years].index
    
    # Filter dataset
    filtered_df = df[df['item_name'].isin(common_items)].copy()
    
    return filtered_df, item_year_count

def main():
    # Read cleaned data
    input_file = Path('data/commissary/processed/texas/texas_commissary_cleaned.csv')
    output_dir = Path('data/commissary/processed/texas')
    
    print("Reading cleaned data...")
    df = pd.read_csv(input_file)
    
    print(f"Original dataset: {len(df)} observations, {df['item_name'].nunique()} unique items")
    
    # Filter for items in at least 5 years
    min_years = 5
    filtered_df, item_coverage = filter_by_year_coverage(df, min_years)
    
    print(f"\n{'='*60}")
    print(f"FILTERED DATASET (items in {min_years}+ years)")
    print('='*60)
    
    print(f"\nFiltered dataset: {len(filtered_df)} observations, {filtered_df['item_name'].nunique()} unique items")
    print(f"Kept: {100*len(filtered_df)/len(df):.1f}% of observations")
    print(f"Kept: {100*filtered_df['item_name'].nunique()/df['item_name'].nunique():.1f}% of unique items")
    
    # Statistics by category
    print(f"\n{'='*60}")
    print("ITEMS PER CATEGORY")
    print('='*60)
    
    cat_comparison = pd.DataFrame({
        'Original': df.groupby('category')['item_name'].nunique(),
        'Filtered': filtered_df.groupby('category')['item_name'].nunique()
    }).fillna(0).astype(int)
    cat_comparison['Kept %'] = (100 * cat_comparison['Filtered'] / cat_comparison['Original']).round(1)
    cat_comparison = cat_comparison.sort_values('Filtered', ascending=False)
    
    print(cat_comparison.to_string())
    
    # Show coverage distribution for filtered items
    print(f"\n{'='*60}")
    print("YEAR COVERAGE OF KEPT ITEMS")
    print('='*60)
    
    filtered_coverage = item_coverage[item_coverage >= min_years]
    for n_years in range(7, min_years-1, -1):
        count = (filtered_coverage == n_years).sum()
        pct = 100 * count / len(filtered_coverage)
        print(f"  {n_years} years: {count:3d} items ({pct:.1f}%)")
    
    # Save filtered dataset
    output_file = output_dir / f'texas_commissary_filtered_{min_years}plus_years.csv'
    filtered_df.to_csv(output_file, index=False)
    
    print(f"\n{'='*60}")
    print(f"Saved filtered dataset to:")
    print(f"{output_file}")
    print('='*60)
    
    # Show examples
    print("\nExamples of kept items:")
    sample_items = filtered_df.groupby('item_name').first().head(20)
    print(sample_items[['category', 'size']].to_string())
    
    print("\nFiltering complete!")

if __name__ == '__main__':
    main()

