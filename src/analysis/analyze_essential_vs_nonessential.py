"""
Essential vs Non-Essential Commissary Price Analysis

This script analyzes whether essential items (basic necessities) have different
inflation rates compared to non-essential items (discretionary purchases).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

def load_data():
    """Load item-level inflation data."""
    analysis_dir = Path(__file__).parent / "outputs"
    item_file = analysis_dir / "commissary_inflation_item_level.csv"
    
    if not item_file.exists():
        raise FileNotFoundError(
            f"Item-level inflation data not found at {item_file}. "
            "Please run calculate_inflation.py first."
        )
    
    df = pd.read_csv(item_file)
    return df

def analyze_essential_vs_nonessential(item_df):
    """
    Perform statistical analysis comparing essential vs non-essential items.
    
    Args:
        item_df: DataFrame with item-level inflation data including essential_status column
    
    Returns:
        Dictionary with analysis results
    """
    # Get latest year data (2025)
    latest_year = item_df['year'].max()
    latest_data = item_df[item_df['year'] == latest_year].copy()
    
    # Separate essential and non-essential items
    essential_items = latest_data[latest_data['essential_status'] == 'essential'].copy()
    non_essential_items = latest_data[latest_data['essential_status'] == 'non-essential'].copy()
    
    # Calculate summary statistics
    essential_inflation = essential_items['cumulative_inflation_pct'].dropna()
    non_essential_inflation = non_essential_items['cumulative_inflation_pct'].dropna()
    
    results = {
        'latest_year': latest_year,
        'essential': {
            'count': len(essential_inflation),
            'mean': essential_inflation.mean(),
            'median': essential_inflation.median(),
            'std': essential_inflation.std(),
            'min': essential_inflation.min(),
            'max': essential_inflation.max(),
            'q25': essential_inflation.quantile(0.25),
            'q75': essential_inflation.quantile(0.75),
            'pct_over_50': (essential_inflation > 50).sum() / len(essential_inflation) * 100,
            'pct_negative': (essential_inflation < 0).sum() / len(essential_inflation) * 100,
        },
        'non_essential': {
            'count': len(non_essential_inflation),
            'mean': non_essential_inflation.mean(),
            'median': non_essential_inflation.median(),
            'std': non_essential_inflation.std(),
            'min': non_essential_inflation.min(),
            'max': non_essential_inflation.max(),
            'q25': non_essential_inflation.quantile(0.25),
            'q75': non_essential_inflation.quantile(0.75),
            'pct_over_50': (non_essential_inflation > 50).sum() / len(non_essential_inflation) * 100,
            'pct_negative': (non_essential_inflation < 0).sum() / len(non_essential_inflation) * 100,
        }
    }
    
    # Calculate difference
    results['difference'] = {
        'mean_diff': results['essential']['mean'] - results['non_essential']['mean'],
        'median_diff': results['essential']['median'] - results['non_essential']['median'],
    }
    
    # Statistical tests
    # T-test (assumes normal distribution)
    t_stat, t_pvalue = stats.ttest_ind(essential_inflation, non_essential_inflation)
    results['statistical_tests'] = {
        't_test': {
            'statistic': t_stat,
            'pvalue': t_pvalue,
            'significant': t_pvalue < 0.05
        }
    }
    
    # Mann-Whitney U test (non-parametric, doesn't assume normal distribution)
    u_stat, u_pvalue = stats.mannwhitneyu(
        essential_inflation, 
        non_essential_inflation,
        alternative='two-sided'
    )
    results['statistical_tests']['mann_whitney'] = {
        'statistic': u_stat,
        'pvalue': u_pvalue,
        'significant': u_pvalue < 0.05
    }
    
    # Top items in each category
    results['top_items'] = {
        'essential_highest': essential_items.nlargest(10, 'cumulative_inflation_pct')[
            ['item_name', 'size', 'category', 'cumulative_inflation_pct']
        ].to_dict('records'),
        'essential_lowest': essential_items.nsmallest(10, 'cumulative_inflation_pct')[
            ['item_name', 'size', 'category', 'cumulative_inflation_pct']
        ].to_dict('records'),
        'non_essential_highest': non_essential_items.nlargest(10, 'cumulative_inflation_pct')[
            ['item_name', 'size', 'category', 'cumulative_inflation_pct']
        ].to_dict('records'),
        'non_essential_lowest': non_essential_items.nsmallest(10, 'cumulative_inflation_pct')[
            ['item_name', 'size', 'category', 'cumulative_inflation_pct']
        ].to_dict('records'),
    }
    
    # Category breakdown
    essential_by_category = essential_items.groupby('category').agg({
        'cumulative_inflation_pct': ['mean', 'count']
    }).round(2)
    essential_by_category.columns = ['mean_inflation', 'item_count']
    essential_by_category = essential_by_category.sort_values('mean_inflation', ascending=False)
    
    non_essential_by_category = non_essential_items.groupby('category').agg({
        'cumulative_inflation_pct': ['mean', 'count']
    }).round(2)
    non_essential_by_category.columns = ['mean_inflation', 'item_count']
    non_essential_by_category = non_essential_by_category.sort_values('mean_inflation', ascending=False)
    
    results['category_breakdown'] = {
        'essential': essential_by_category.to_dict('index'),
        'non_essential': non_essential_by_category.to_dict('index'),
    }
    
    # Time series analysis (inflation over time for each group)
    time_series = []
    for year in sorted(item_df['year'].unique()):
        year_data = item_df[item_df['year'] == year]
        essential_year = year_data[year_data['essential_status'] == 'essential']['cumulative_inflation_pct'].mean()
        non_essential_year = year_data[year_data['essential_status'] == 'non-essential']['cumulative_inflation_pct'].mean()
        
        time_series.append({
            'year': year,
            'essential_mean': essential_year,
            'non_essential_mean': non_essential_year,
            'difference': essential_year - non_essential_year if pd.notna(essential_year) and pd.notna(non_essential_year) else None
        })
    
    results['time_series'] = time_series
    
    return results, essential_items, non_essential_items

def save_results(results, essential_items, non_essential_items):
    """Save analysis results to CSV files."""
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed item-level analysis
    latest_year = results['latest_year']
    essential_latest = essential_items[essential_items['year'] == latest_year].copy()
    non_essential_latest = non_essential_items[non_essential_items['year'] == latest_year].copy()
    
    combined_analysis = pd.concat([essential_latest, non_essential_latest], ignore_index=True)
    combined_analysis = combined_analysis.sort_values('cumulative_inflation_pct', ascending=False)
    
    combined_analysis.to_csv(
        output_dir / "essential_vs_nonessential_analysis.csv",
        index=False
    )
    
    # Save summary statistics
    summary_data = {
        'metric': [],
        'essential': [],
        'non_essential': [],
        'difference': []
    }
    
    for key in ['mean', 'median', 'std', 'min', 'max', 'q25', 'q75', 'pct_over_50', 'pct_negative']:
        summary_data['metric'].append(key)
        summary_data['essential'].append(results['essential'][key])
        summary_data['non_essential'].append(results['non_essential'][key])
        if key in ['mean', 'median']:
            summary_data['difference'].append(results['difference'][f'{key}_diff'])
        else:
            summary_data['difference'].append(None)
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(
        output_dir / "essential_vs_nonessential_summary.csv",
        index=False
    )
    
    # Save time series
    time_series_df = pd.DataFrame(results['time_series'])
    time_series_df.to_csv(
        output_dir / "essential_vs_nonessential_timeseries.csv",
        index=False
    )
    
    print(f"Saved analysis results to {output_dir}")
    print(f"  - essential_vs_nonessential_analysis.csv")
    print(f"  - essential_vs_nonessential_summary.csv")
    print(f"  - essential_vs_nonessential_timeseries.csv")

def print_summary(results):
    """Print a summary of the analysis results."""
    print("\n" + "=" * 80)
    print("ESSENTIAL VS NON-ESSENTIAL INFLATION ANALYSIS")
    print("=" * 80)
    
    print(f"\nAnalysis Year: {int(results['latest_year'])}")
    print(f"\nItem Counts:")
    print(f"  Essential items: {results['essential']['count']}")
    print(f"  Non-essential items: {results['non_essential']['count']}")
    
    print(f"\nCumulative Inflation Statistics (2019-{int(results['latest_year'])}):")
    print(f"\nEssential Items:")
    print(f"  Mean: {results['essential']['mean']:.2f}%")
    print(f"  Median: {results['essential']['median']:.2f}%")
    print(f"  Std Dev: {results['essential']['std']:.2f}%")
    print(f"  Range: [{results['essential']['min']:.2f}%, {results['essential']['max']:.2f}%]")
    print(f"  Items with >50% inflation: {results['essential']['pct_over_50']:.1f}%")
    
    print(f"\nNon-Essential Items:")
    print(f"  Mean: {results['non_essential']['mean']:.2f}%")
    print(f"  Median: {results['non_essential']['median']:.2f}%")
    print(f"  Std Dev: {results['non_essential']['std']:.2f}%")
    print(f"  Range: [{results['non_essential']['min']:.2f}%, {results['non_essential']['max']:.2f}%]")
    print(f"  Items with >50% inflation: {results['non_essential']['pct_over_50']:.1f}%")
    
    print(f"\nDifference (Essential - Non-Essential):")
    print(f"  Mean difference: {results['difference']['mean_diff']:.2f} percentage points")
    print(f"  Median difference: {results['difference']['median_diff']:.2f} percentage points")
    
    print(f"\nStatistical Tests:")
    t_test = results['statistical_tests']['t_test']
    print(f"  T-test: t={t_test['statistic']:.3f}, p={t_test['pvalue']:.4f} {'(significant)' if t_test['significant'] else '(not significant)'}")
    
    mw_test = results['statistical_tests']['mann_whitney']
    print(f"  Mann-Whitney U test: U={mw_test['statistic']:.1f}, p={mw_test['pvalue']:.4f} {'(significant)' if mw_test['significant'] else '(not significant)'}")
    
    print(f"\nTop 5 Essential Items with Highest Inflation:")
    for i, item in enumerate(results['top_items']['essential_highest'][:5], 1):
        size_str = f" ({item['size']})" if pd.notna(item['size']) and item['size'] else ""
        print(f"  {i}. {item['item_name']}{size_str}: {item['cumulative_inflation_pct']:.2f}% [{item['category']}]")
    
    print(f"\nTop 5 Non-Essential Items with Highest Inflation:")
    for i, item in enumerate(results['top_items']['non_essential_highest'][:5], 1):
        size_str = f" ({item['size']})" if pd.notna(item['size']) and item['size'] else ""
        print(f"  {i}. {item['item_name']}{size_str}: {item['cumulative_inflation_pct']:.2f}% [{item['category']}]")

def main():
    """Main analysis function."""
    print("Loading data...")
    item_df = load_data()
    
    # Check if essential_status column exists
    if 'essential_status' not in item_df.columns:
        print("Warning: essential_status column not found. Re-running inflation calculation...")
        print("Please run calculate_inflation.py first to generate data with essential classification.")
        return
    
    print(f"Loaded {len(item_df)} item-year records")
    print(f"Unique items: {item_df['item_name'].nunique()}")
    
    print("\nAnalyzing essential vs non-essential items...")
    results, essential_items, non_essential_items = analyze_essential_vs_nonessential(item_df)
    
    print_summary(results)
    
    print("\nSaving results...")
    save_results(results, essential_items, non_essential_items)
    
    return results

if __name__ == "__main__":
    main()

