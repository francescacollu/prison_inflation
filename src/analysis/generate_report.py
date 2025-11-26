import pandas as pd
from pathlib import Path
import numpy as np

def generate_summary_report():
    """Generate a comprehensive summary report of inflation analysis."""
    
    # Load data (relative to script location)
    analysis_dir = Path(__file__).parent / "outputs"
    
    comparisons_file = analysis_dir / "inflation_comparisons.csv"
    commissary_item_file = analysis_dir / "commissary_inflation_item_level.csv"
    commissary_category_file = analysis_dir / "commissary_inflation_category_level.csv"
    commissary_overall_file = analysis_dir / "commissary_inflation_overall.csv"
    cpi_inflation_file = analysis_dir / "cpi_inflation.csv"
    
    if not comparisons_file.exists():
        print(f"Error: Analysis data not found. Please run calculate_inflation.py first.")
        return
    
    comparisons_df = pd.read_csv(comparisons_file)
    commissary_item_df = pd.read_csv(commissary_item_file)
    commissary_category_df = pd.read_csv(commissary_category_file)
    commissary_overall_df = pd.read_csv(commissary_overall_file)
    cpi_inflation_df = pd.read_csv(cpi_inflation_file)
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("PRISON COMMISSARY INFLATION ANALYSIS - SUMMARY REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Overall Summary
    report_lines.append("OVERALL SUMMARY")
    report_lines.append("-" * 80)
    
    overall_comps = comparisons_df[comparisons_df['level'] == 'overall']
    latest_year = overall_comps['year'].max()
    latest_overall = overall_comps[overall_comps['year'] == latest_year].iloc[0]
    
    report_lines.append(f"\nStudy Period: 2019 - {int(latest_year)}")
    report_lines.append(f"\nOverall Commissary Inflation (Cumulative): {latest_overall['commissary_cum_pct']:.2f}%")
    report_lines.append(f"CPI-U Inflation (Cumulative): {latest_overall['cpi_cum_pct']:.2f}%")
    report_lines.append(f"Difference: {latest_overall['cum_diff_pct']:.2f} percentage points")
    
    if latest_overall['cum_diff_pct'] > 0:
        report_lines.append(f"\nCommissary prices have risen {abs(latest_overall['cum_diff_pct']):.2f} percentage points MORE than general inflation.")
    else:
        report_lines.append(f"\nCommissary prices have risen {abs(latest_overall['cum_diff_pct']):.2f} percentage points LESS than general inflation.")
    
    # Average Annual Inflation
    report_lines.append("\n\nAVERAGE ANNUAL INFLATION RATES")
    report_lines.append("-" * 80)
    
    # Calculate average YoY inflation (excluding first year which has no YoY)
    commissary_yoy = commissary_overall_df[commissary_overall_df['yoy_inflation_pct'].notna()]['yoy_inflation_pct']
    cpi_yoy = cpi_inflation_df[
        (cpi_inflation_df['cpi_type'] == 'CPI-U') & 
        (cpi_inflation_df['yoy_inflation_pct'].notna())
    ]['yoy_inflation_pct']
    
    if len(commissary_yoy) > 0:
        avg_commissary_yoy = commissary_yoy.mean()
        report_lines.append(f"\nAverage Commissary YoY Inflation: {avg_commissary_yoy:.2f}%")
    
    if len(cpi_yoy) > 0:
        avg_cpi_yoy = cpi_yoy.mean()
        report_lines.append(f"Average CPI-U YoY Inflation: {avg_cpi_yoy:.2f}%")
    
    if len(commissary_yoy) > 0 and len(cpi_yoy) > 0:
        report_lines.append(f"Average Difference: {avg_commissary_yoy - avg_cpi_yoy:.2f} percentage points")
    
    # Category Analysis
    report_lines.append("\n\nCATEGORY-LEVEL ANALYSIS")
    report_lines.append("-" * 80)
    
    category_comps = comparisons_df[comparisons_df['level'] == 'cpi_category']
    latest_category = category_comps[category_comps['year'] == latest_year].copy()
    latest_category = latest_category.sort_values('cum_diff_pct', ascending=False)
    
    report_lines.append(f"\nCumulative Inflation by Category ({int(latest_year)}):")
    report_lines.append("")
    report_lines.append(f"{'Category':<25} {'Commissary':<15} {'CPI':<15} {'Difference':<15}")
    report_lines.append("-" * 70)
    
    for _, row in latest_category.iterrows():
        report_lines.append(
            f"{row['cpi_type']:<25} "
            f"{row['commissary_cum_pct']:>13.2f}%  "
            f"{row['cpi_cum_pct']:>13.2f}%  "
            f"{row['cum_diff_pct']:>13.2f}%"
        )
    
    # Highest and Lowest Inflation Categories
    report_lines.append("\n\nHIGHEST INFLATION CATEGORIES (Commissary)")
    report_lines.append("-" * 80)
    
    top_categories = latest_category.nlargest(3, 'commissary_cum_pct')
    for idx, (_, row) in enumerate(top_categories.iterrows(), 1):
        report_lines.append(f"{idx}. {row['cpi_type']}: {row['commissary_cum_pct']:.2f}%")
    
    report_lines.append("\n\nLOWEST INFLATION CATEGORIES (Commissary)")
    report_lines.append("-" * 80)
    
    bottom_categories = latest_category.nsmallest(3, 'commissary_cum_pct')
    for idx, (_, row) in enumerate(bottom_categories.iterrows(), 1):
        report_lines.append(f"{idx}. {row['cpi_type']}: {row['commissary_cum_pct']:.2f}%")
    
    # Categories with Largest Differences from CPI
    report_lines.append("\n\nCATEGORIES WITH LARGEST DIFFERENCE FROM CPI")
    report_lines.append("-" * 80)
    
    largest_diff = latest_category.nlargest(5, 'cum_diff_pct')
    report_lines.append("\nCategories where commissary inflation exceeds CPI the most:")
    for idx, (_, row) in enumerate(largest_diff.iterrows(), 1):
        report_lines.append(
            f"{idx}. {row['cpi_type']}: "
            f"Commissary {row['commissary_cum_pct']:.2f}% vs CPI {row['cpi_cum_pct']:.2f}% "
            f"(+{row['cum_diff_pct']:.2f} pp)"
        )
    
    # Item-Level Analysis
    report_lines.append("\n\nITEM-LEVEL ANALYSIS")
    report_lines.append("-" * 80)
    
    item_2024 = commissary_item_df[commissary_item_df['year'] == latest_year].copy()
    
    # Items with highest inflation
    report_lines.append(f"\nTop 10 Items with Highest Cumulative Inflation ({int(latest_year)}):")
    top_items = item_2024.nlargest(10, 'cumulative_inflation_pct')
    for idx, (_, row) in enumerate(top_items.iterrows(), 1):
        size_str = f" ({row['size']})" if pd.notna(row['size']) and row['size'] else ""
        report_lines.append(
            f"{idx}. {row['item_name']}{size_str}: {row['cumulative_inflation_pct']:.2f}% "
            f"({row['category']})"
        )
    
    # Items with lowest inflation (or deflation)
    report_lines.append(f"\nTop 10 Items with Lowest Cumulative Inflation ({int(latest_year)}):")
    bottom_items = item_2024.nsmallest(10, 'cumulative_inflation_pct')
    for idx, (_, row) in enumerate(bottom_items.iterrows(), 1):
        size_str = f" ({row['size']})" if pd.notna(row['size']) and row['size'] else ""
        report_lines.append(
            f"{idx}. {row['item_name']}{size_str}: {row['cumulative_inflation_pct']:.2f}% "
            f"({row['category']})"
        )
    
    # Year-over-Year Trends
    report_lines.append("\n\nYEAR-OVER-YEAR TRENDS")
    report_lines.append("-" * 80)
    
    report_lines.append("\nOverall Commissary vs CPI-U (Year-over-Year Inflation):")
    report_lines.append("")
    report_lines.append(f"{'Year':<10} {'Commissary':<15} {'CPI-U':<15} {'Difference':<15}")
    report_lines.append("-" * 55)
    
    overall_yoy = overall_comps[overall_comps['commissary_yoy_pct'].notna()].sort_values('year')
    for _, row in overall_yoy.iterrows():
        report_lines.append(
            f"{int(row['year']):<10} "
            f"{row['commissary_yoy_pct']:>13.2f}%  "
            f"{row['cpi_yoy_pct']:>13.2f}%  "
            f"{row['yoy_diff_pct']:>13.2f}%"
        )
    
    # Statistical Summary
    report_lines.append("\n\nSTATISTICAL SUMMARY")
    report_lines.append("-" * 80)
    
    report_lines.append(f"\nTotal Items Analyzed: {commissary_item_df['item_name'].nunique()}")
    report_lines.append(f"Total Categories: {commissary_category_df['category'].nunique()}")
    report_lines.append(f"Years Covered: {sorted(commissary_item_df['year'].unique())}")
    
    # Items with extreme price changes
    extreme_high = item_2024[item_2024['cumulative_inflation_pct'] > 50]
    extreme_low = item_2024[item_2024['cumulative_inflation_pct'] < -10]
    
    if len(extreme_high) > 0:
        report_lines.append(f"\nItems with >50% cumulative inflation: {len(extreme_high)}")
    if len(extreme_low) > 0:
        report_lines.append(f"Items with <-10% cumulative inflation (deflation): {len(extreme_low)}")
    
    # Save report (to analysis/outputs)
    output_file = analysis_dir / "inflation_summary.txt"
    report_text = "\n".join(report_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\n{'='*80}")
    print("SUMMARY REPORT GENERATED")
    print('='*80)
    print(f"\nSaved to: {output_file}")
    print("\n" + report_text)
    
    return report_text

if __name__ == "__main__":
    generate_summary_report()

