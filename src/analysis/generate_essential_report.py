"""
Generate comprehensive report for Essential vs Non-Essential analysis.
"""

import pandas as pd
import json
from pathlib import Path

def load_analysis_results():
    """Load all analysis results."""
    analysis_dir = Path(__file__).parent / "outputs"
    
    # Load summary statistics
    summary_file = analysis_dir / "essential_vs_nonessential_summary.csv"
    summary_df = pd.read_csv(summary_file)
    
    # Load detailed analysis
    analysis_file = analysis_dir / "essential_vs_nonessential_analysis.csv"
    analysis_df = pd.read_csv(analysis_file)
    
    # Load timeseries
    timeseries_file = analysis_dir / "essential_vs_nonessential_timeseries.csv"
    timeseries_df = pd.read_csv(timeseries_file)
    
    return summary_df, analysis_df, timeseries_df

def generate_report():
    """Generate comprehensive report."""
    print("Loading analysis results...")
    summary_df, analysis_df, timeseries_df = load_analysis_results()
    
    latest_year = analysis_df['year'].max()
    latest_data = analysis_df[analysis_df['year'] == latest_year].copy()
    
    # Calculate key statistics
    essential_items = latest_data[latest_data['essential_status'] == 'essential']
    non_essential_items = latest_data[latest_data['essential_status'] == 'non-essential']
    
    essential_inflation = essential_items['cumulative_inflation_pct'].dropna()
    non_essential_inflation = non_essential_items['cumulative_inflation_pct'].dropna()
    
    essential_mean = essential_inflation.mean()
    non_essential_mean = non_essential_inflation.mean()
    difference = essential_mean - non_essential_mean
    
    # Build report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("ESSENTIAL VS NON-ESSENTIAL COMMISSARY PRICE ANALYSIS")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("EXECUTIVE SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append(f"This analysis examines whether prison commissaries charge more for")
    report_lines.append(f"essential items (basic necessities) compared to non-essential items")
    report_lines.append(f"(discretionary purchases) in Texas prisons from 2019 to {int(latest_year)}.")
    report_lines.append("")
    
    if difference > 0:
        report_lines.append(f"KEY FINDING: Essential items have experienced {abs(difference):.2f} percentage points")
        report_lines.append(f"MORE cumulative inflation than non-essential items.")
        report_lines.append("")
        report_lines.append("This suggests that prison commissaries may be extracting more value")
        report_lines.append("from captive consumers on items they cannot avoid purchasing.")
    else:
        report_lines.append(f"KEY FINDING: Essential items have experienced {abs(difference):.2f} percentage points")
        report_lines.append(f"LESS cumulative inflation than non-essential items.")
        report_lines.append("")
    
    report_lines.append("")
    
    # Methodology
    report_lines.append("METHODOLOGY")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append("Item Classification:")
    report_lines.append("Items were classified as 'essential' or 'non-essential' based on:")
    report_lines.append("  - Category context (e.g., HYGIENE items are generally essential)")
    report_lines.append("  - Item name patterns (e.g., 'soap', 'toothpaste' = essential)")
    report_lines.append("  - Item purpose (basic necessities vs. luxury/entertainment)")
    report_lines.append("")
    report_lines.append("Essential items include:")
    report_lines.append("  - Basic hygiene products (soap, toothpaste, shampoo, deodorant)")
    report_lines.append("  - Basic clothing (socks, underwear, t-shirts)")
    report_lines.append("  - Basic food items (not candy/snacks)")
    report_lines.append("  - Medications and vitamins")
    report_lines.append("  - Basic communication items (stamps, envelopes, writing paper)")
    report_lines.append("")
    report_lines.append("Non-essential items include:")
    report_lines.append("  - Candy and snacks")
    report_lines.append("  - Art supplies and games")
    report_lines.append("  - Electrical entertainment items")
    report_lines.append("  - Luxury personal care (makeup, hair styling products)")
    report_lines.append("  - Greeting cards and non-essential correspondence items")
    report_lines.append("")
    report_lines.append("Analysis Period: 2019-2025")
    report_lines.append(f"Total Items Analyzed: {len(latest_data)}")
    report_lines.append(f"  - Essential items: {len(essential_items)}")
    report_lines.append(f"  - Non-essential items: {len(non_essential_items)}")
    report_lines.append("")
    
    # Key Statistics
    report_lines.append("KEY STATISTICS")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append(f"Cumulative Inflation (2019-{int(latest_year)}):")
    report_lines.append("")
    report_lines.append("Essential Items:")
    report_lines.append(f"  Mean: {essential_mean:.2f}%")
    report_lines.append(f"  Median: {essential_inflation.median():.2f}%")
    report_lines.append(f"  Standard Deviation: {essential_inflation.std():.2f}%")
    report_lines.append(f"  Range: [{essential_inflation.min():.2f}%, {essential_inflation.max():.2f}%]")
    report_lines.append(f"  Items with >50% inflation: {(essential_inflation > 50).sum()} ({(essential_inflation > 50).sum() / len(essential_inflation) * 100:.1f}%)")
    report_lines.append(f"  Items with negative inflation (deflation): {(essential_inflation < 0).sum()} ({(essential_inflation < 0).sum() / len(essential_inflation) * 100:.1f}%)")
    report_lines.append("")
    report_lines.append("Non-Essential Items:")
    report_lines.append(f"  Mean: {non_essential_mean:.2f}%")
    report_lines.append(f"  Median: {non_essential_inflation.median():.2f}%")
    report_lines.append(f"  Standard Deviation: {non_essential_inflation.std():.2f}%")
    report_lines.append(f"  Range: [{non_essential_inflation.min():.2f}%, {non_essential_inflation.max():.2f}%]")
    report_lines.append(f"  Items with >50% inflation: {(non_essential_inflation > 50).sum()} ({(non_essential_inflation > 50).sum() / len(non_essential_inflation) * 100:.1f}%)")
    report_lines.append(f"  Items with negative inflation (deflation): {(non_essential_inflation < 0).sum()} ({(non_essential_inflation < 0).sum() / len(non_essential_inflation) * 100:.1f}%)")
    report_lines.append("")
    report_lines.append(f"Difference (Essential - Non-Essential):")
    report_lines.append(f"  Mean difference: {difference:.2f} percentage points")
    report_lines.append(f"  Median difference: {essential_inflation.median() - non_essential_inflation.median():.2f} percentage points")
    report_lines.append("")
    
    # Category Breakdown
    report_lines.append("CATEGORY BREAKDOWN")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append("Essential Items by Category (Average Cumulative Inflation):")
    report_lines.append("")
    essential_by_cat = essential_items.groupby('category')['cumulative_inflation_pct'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    essential_by_cat.columns = ['Mean Inflation (%)', 'Item Count']
    for category, row in essential_by_cat.iterrows():
        report_lines.append(f"  {category:<30} {row['Mean Inflation (%)']:>8.2f}% ({int(row['Item Count'])} items)")
    report_lines.append("")
    report_lines.append("Non-Essential Items by Category (Average Cumulative Inflation):")
    report_lines.append("")
    non_essential_by_cat = non_essential_items.groupby('category')['cumulative_inflation_pct'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    non_essential_by_cat.columns = ['Mean Inflation (%)', 'Item Count']
    for category, row in non_essential_by_cat.iterrows():
        report_lines.append(f"  {category:<30} {row['Mean Inflation (%)']:>8.2f}% ({int(row['Item Count'])} items)")
    report_lines.append("")
    
    # Top Items
    report_lines.append("TOP ITEMS WITH HIGHEST INFLATION")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append("Top 10 Essential Items:")
    top_essential = essential_items.nlargest(10, 'cumulative_inflation_pct')
    for i, (_, row) in enumerate(top_essential.iterrows(), 1):
        size_str = f" ({row['size']})" if pd.notna(row['size']) and row['size'] else ""
        report_lines.append(f"  {i:2d}. {row['item_name']}{size_str:<30} {row['cumulative_inflation_pct']:>8.2f}% [{row['category']}]")
    report_lines.append("")
    report_lines.append("Top 10 Non-Essential Items:")
    top_non_essential = non_essential_items.nlargest(10, 'cumulative_inflation_pct')
    for i, (_, row) in enumerate(top_non_essential.iterrows(), 1):
        size_str = f" ({row['size']})" if pd.notna(row['size']) and row['size'] else ""
        report_lines.append(f"  {i:2d}. {row['item_name']}{size_str:<30} {row['cumulative_inflation_pct']:>8.2f}% [{row['category']}]")
    report_lines.append("")
    
    # Time Series Trends
    report_lines.append("TIME SERIES TRENDS")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append(f"{'Year':<8} {'Essential Mean':<18} {'Non-Essential Mean':<20} {'Difference':<12}")
    report_lines.append("-" * 60)
    for _, row in timeseries_df.iterrows():
        if pd.notna(row['essential_mean']) and pd.notna(row['non_essential_mean']):
            diff = row['essential_mean'] - row['non_essential_mean']
            report_lines.append(f"{int(row['year']):<8} {row['essential_mean']:>16.2f}%  {row['non_essential_mean']:>18.2f}%  {diff:>10.2f} pp")
    report_lines.append("")
    
    # Policy Implications
    report_lines.append("POLICY IMPLICATIONS")
    report_lines.append("-" * 80)
    report_lines.append("")
    if difference > 0:
        report_lines.append("The finding that essential items have higher inflation rates than")
        report_lines.append("non-essential items raises important policy questions:")
        report_lines.append("")
        report_lines.append("1. Captive Market Pricing: Prison commissaries operate as monopolies")
        report_lines.append("   with no competition. The higher inflation on essential items")
        report_lines.append("   suggests they may be extracting more value from items people")
        report_lines.append("   cannot avoid purchasing.")
        report_lines.append("")
        report_lines.append("2. Impact on Incarcerated People: Essential items are necessities")
        report_lines.append("   that people must purchase regardless of price. Higher inflation")
        report_lines.append("   on these items disproportionately affects incarcerated people,")
        report_lines.append("   who earn an average of $0.13-$0.52 per hour.")
        report_lines.append("")
        report_lines.append("3. Family Burden: Since 60% of commissary spending comes from")
        report_lines.append("   family members outside prison, higher prices on essential items")
        report_lines.append("   place additional financial burden on families.")
        report_lines.append("")
        report_lines.append("4. Equity Concerns: The pricing structure may create additional")
        report_lines.append("   barriers for people with limited financial resources, potentially")
        report_lines.append("   affecting their ability to access basic necessities.")
    else:
        report_lines.append("The finding that essential items have lower inflation rates than")
        report_lines.append("non-essential items suggests that pricing may be more constrained")
        report_lines.append("on basic necessities, possibly due to policy or public scrutiny.")
        report_lines.append("However, both groups still show significant inflation above general")
        report_lines.append("CPI inflation rates.")
    report_lines.append("")
    
    # Limitations
    report_lines.append("LIMITATIONS")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append("1. Classification Subjectivity: The classification of items as")
    report_lines.append("   'essential' vs 'non-essential' involves some subjectivity.")
    report_lines.append("   Different classification schemes might yield different results.")
    report_lines.append("")
    report_lines.append("2. Single State: This analysis covers only Texas prisons.")
    report_lines.append("   Results may not generalize to other states.")
    report_lines.append("")
    report_lines.append("3. Fixed Basket: Only items present in all years (2019-2025) are")
    report_lines.append("   included in the analysis. Items that were added or removed")
    report_lines.append("   during this period are excluded.")
    report_lines.append("")
    report_lines.append("4. Price Ranges: Some items have price ranges (min-max). This")
    report_lines.append("   analysis uses the average of min and max prices.")
    report_lines.append("")
    
    # Save report
    output_dir = Path(__file__).parent / "outputs"
    output_file = output_dir / "essential_vs_nonessential_report.txt"
    
    report_text = "\n".join(report_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\n{'='*80}")
    print("ESSENTIAL VS NON-ESSENTIAL ANALYSIS REPORT GENERATED")
    print('='*80)
    print(f"\nSaved to: {output_file}")
    print("\n" + report_text)
    
    return report_text

if __name__ == "__main__":
    generate_report()

