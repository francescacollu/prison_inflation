"""
Recurrent Price Increase and Anomaly Detection Analysis

This script analyzes items with the most recurrent price increases and detects
various types of anomalies in commissary pricing data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

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

def analyze_recurrent_price_increases(item_df, top_percentile=0.25, significant_threshold=10.0):
    """
    Analyze items with the most recurrent price increases.
    
    Args:
        item_df: DataFrame with columns: year, item_name, size, yoy_inflation_pct, category
        top_percentile: Percentile threshold for "top increases" (0.25 = top 25%)
        significant_threshold: Threshold for significant increase (e.g., 10% YoY)
    
    Returns:
        DataFrame with recurrence metrics per item
    """
    # Create item_id
    item_df = item_df.copy()
    item_df['item_id'] = item_df['item_name'] + '|' + item_df['size'].fillna('')
    
    # Filter to only years with YoY data
    yoy_data = item_df[item_df['yoy_inflation_pct'].notna()].copy()
    
    recurrence_metrics = []
    
    for item_id in yoy_data['item_id'].unique():
        item_data = yoy_data[yoy_data['item_id'] == item_id].sort_values('year')
        
        yoy_values = item_data['yoy_inflation_pct'].values
        positive_yoy = yoy_values[yoy_values > 0]
        
        # Basic stats
        mean_yoy = np.mean(yoy_values)
        median_yoy = np.median(yoy_values)
        std_yoy = np.std(yoy_values)
        max_yoy = np.max(yoy_values)
        min_yoy = np.min(yoy_values)
        
        # Recurrence metrics
        num_years = len(yoy_values)
        num_positive = len(positive_yoy)
        num_significant = np.sum(yoy_values > significant_threshold)
        consistency_score = num_positive / num_years if num_years > 0 else 0
        
        # Years in top percentile
        all_yoy_threshold = np.percentile(yoy_data['yoy_inflation_pct'].dropna(), (1 - top_percentile) * 100)
        years_in_top = np.sum(yoy_values > all_yoy_threshold)
        
        # Volatility (coefficient of variation)
        cv = std_yoy / abs(mean_yoy) if mean_yoy != 0 else np.inf
        
        # Trend classification
        if num_positive == num_years:
            trend = "consistent_increaser"
        elif max_yoy > 100 and std_yoy > 50:
            trend = "spiker"
        elif std_yoy > abs(mean_yoy) * 0.5 if mean_yoy != 0 else False:
            trend = "volatile"
        else:
            trend = "steady"
        
        # Item metadata
        first_row = item_data.iloc[0]
        
        # Get latest cumulative inflation
        latest_year = item_data['year'].max()
        latest_row = item_data[item_data['year'] == latest_year].iloc[0]
        cumulative_inflation = latest_row.get('cumulative_inflation_pct', None)
        
        recurrence_metrics.append({
            'item_id': item_id,
            'item_name': first_row['item_name'],
            'size': first_row['size'],
            'category': first_row['category'],
            'cpi_category': first_row.get('cpi_category', ''),
            'essential_status': first_row.get('essential_status', ''),
            'num_years': num_years,
            'mean_yoy_pct': mean_yoy,
            'median_yoy_pct': median_yoy,
            'std_yoy_pct': std_yoy,
            'max_yoy_pct': max_yoy,
            'min_yoy_pct': min_yoy,
            'num_positive_years': num_positive,
            'num_significant_increases': num_significant,
            'consistency_score': consistency_score,
            'years_in_top_percentile': years_in_top,
            'volatility_cv': cv if cv != np.inf else 999.0,
            'trend_type': trend,
            'cumulative_inflation_pct': cumulative_inflation
        })
    
    return pd.DataFrame(recurrence_metrics)

def detect_anomalies(item_df, recurrence_df):
    """
    Detect anomalies in price data.
    
    Returns:
        Dictionary with different types of anomalies
    """
    yoy_data = item_df[item_df['yoy_inflation_pct'].notna()].copy()
    yoy_data['item_id'] = yoy_data['item_name'] + '|' + yoy_data['size'].fillna('')
    
    anomalies = {
        'extreme_spikes': [],
        'high_volatility': [],
        'category_outliers': [],
        'price_corrections': [],
        'data_quality_issues': []
    }
    
    # 1. Extreme single-year spikes
    all_yoy = yoy_data['yoy_inflation_pct'].dropna()
    if len(all_yoy) > 0:
        spike_threshold = np.percentile(all_yoy, 99)
        
        extreme_spikes = yoy_data[yoy_data['yoy_inflation_pct'] > spike_threshold]
        for _, row in extreme_spikes.iterrows():
            anomalies['extreme_spikes'].append({
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'year': row['year'],
                'yoy_inflation_pct': row['yoy_inflation_pct'],
                'category': row['category'],
                'price': row['price'],
                'threshold': spike_threshold
            })
    
    # 2. High volatility items
    if len(recurrence_df) > 0:
        vol_cv_values = recurrence_df['volatility_cv'].replace([np.inf, -np.inf], np.nan).dropna()
        if len(vol_cv_values) > 0:
            volatility_threshold = vol_cv_values.quantile(0.95)
            high_vol = recurrence_df[
                (recurrence_df['volatility_cv'] > volatility_threshold) & 
                (recurrence_df['volatility_cv'] != 999.0)
            ]
            for _, row in high_vol.iterrows():
                anomalies['high_volatility'].append({
                    'item_id': row['item_id'],
                    'item_name': row['item_name'],
                    'volatility_cv': row['volatility_cv'],
                    'std_yoy_pct': row['std_yoy_pct'],
                    'mean_yoy_pct': row['mean_yoy_pct'],
                    'category': row['category']
                })
    
    # 3. Category outliers
    for category in recurrence_df['category'].unique():
        cat_data = recurrence_df[recurrence_df['category'] == category]
        if len(cat_data) < 3:
            continue
        
        cat_median = cat_data['mean_yoy_pct'].median()
        cat_std = cat_data['mean_yoy_pct'].std()
        
        if cat_std > 0:
            outliers = cat_data[cat_data['mean_yoy_pct'] > cat_median + 2 * cat_std]
            for _, row in outliers.iterrows():
                z_score = (row['mean_yoy_pct'] - cat_median) / cat_std
                anomalies['category_outliers'].append({
                    'item_id': row['item_id'],
                    'item_name': row['item_name'],
                    'category': category,
                    'item_mean_yoy': row['mean_yoy_pct'],
                    'category_median_yoy': cat_median,
                    'category_std_yoy': cat_std,
                    'z_score': z_score
                })
    
    # 4. Price corrections (large increase followed by decrease)
    for item_id in yoy_data['item_id'].unique():
        item_data = yoy_data[yoy_data['item_id'] == item_id].sort_values('year')
        if len(item_data) < 2:
            continue
        
        for i in range(len(item_data) - 1):
            curr_yoy = item_data.iloc[i]['yoy_inflation_pct']
            next_yoy = item_data.iloc[i + 1]['yoy_inflation_pct']
            
            if curr_yoy > 50 and next_yoy < -5:  # Large increase then decrease
                anomalies['price_corrections'].append({
                    'item_id': item_id,
                    'item_name': item_data.iloc[i]['item_name'],
                    'year': item_data.iloc[i]['year'],
                    'increase_pct': curr_yoy,
                    'next_year_decrease_pct': next_yoy,
                    'price_before': item_data.iloc[i]['price'],
                    'price_after': item_data.iloc[i + 1]['price'],
                    'category': item_data.iloc[i]['category']
                })
    
    # 5. Data quality issues
    all_data = item_df.copy()
    all_data['item_id'] = all_data['item_name'] + '|' + all_data['size'].fillna('')
    
    # Extreme cumulative inflation
    latest_year = all_data['year'].max()
    latest_data = all_data[all_data['year'] == latest_year]
    extreme_cumulative = latest_data[latest_data['cumulative_inflation_pct'] > 500]
    
    for _, row in extreme_cumulative.iterrows():
        anomalies['data_quality_issues'].append({
            'item_id': row['item_id'],
            'item_name': row['item_name'],
            'year': row['year'],
            'cumulative_inflation_pct': row['cumulative_inflation_pct'],
            'price': row['price'],
            'category': row['category'],
            'issue_type': 'extreme_cumulative_inflation'
        })
    
    # Convert lists to DataFrames
    for key in anomalies:
        if anomalies[key]:
            anomalies[key] = pd.DataFrame(anomalies[key])
        else:
            anomalies[key] = pd.DataFrame()
    
    return anomalies

def generate_recurrence_report(recurrence_df, anomalies, output_dir):
    """Generate a comprehensive report on recurrent price increases and anomalies."""
    
    # Sort by recurrence metrics
    top_recurrent = recurrence_df.nlargest(20, 'years_in_top_percentile')
    top_consistent = recurrence_df.nlargest(20, 'consistency_score')
    top_mean_yoy = recurrence_df.nlargest(20, 'mean_yoy_pct')
    top_cumulative = recurrence_df.nlargest(20, 'cumulative_inflation_pct')
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("RECURRENT PRICE INCREASE ANALYSIS")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    report_lines.append("TOP 20 ITEMS BY YEARS IN TOP 25% OF INCREASES:")
    report_lines.append("-" * 80)
    for _, row in top_recurrent.iterrows():
        report_lines.append(f"{row['item_name']} ({row['size']})")
        report_lines.append(f"  Category: {row['category']}")
        report_lines.append(f"  Years in top 25%: {int(row['years_in_top_percentile'])}/{int(row['num_years'])}")
        report_lines.append(f"  Mean YoY: {row['mean_yoy_pct']:.2f}%")
        report_lines.append(f"  Trend: {row['trend_type']}")
        report_lines.append("")
    
    report_lines.append("\nTOP 20 ITEMS BY MEAN YEAR-OVER-YEAR INFLATION:")
    report_lines.append("-" * 80)
    for _, row in top_mean_yoy.iterrows():
        report_lines.append(f"{row['item_name']} ({row['size']}): {row['mean_yoy_pct']:.2f}% mean YoY")
    
    report_lines.append("\n\nTOP 20 ITEMS BY CONSISTENCY SCORE:")
    report_lines.append("-" * 80)
    for _, row in top_consistent.iterrows():
        report_lines.append(f"{row['item_name']} ({row['size']}): {row['consistency_score']:.2%} ({int(row['num_positive_years'])}/{int(row['num_years'])} years positive)")
    
    report_lines.append("\n\nTOP 20 ITEMS BY CUMULATIVE INFLATION (2019-2025):")
    report_lines.append("-" * 80)
    for _, row in top_cumulative.iterrows():
        report_lines.append(f"{row['item_name']} ({row['size']}): {row['cumulative_inflation_pct']:.2f}% cumulative")
    
    report_lines.append("\n\n" + "=" * 80)
    report_lines.append("ANOMALY DETECTION RESULTS")
    report_lines.append("=" * 80)
    
    if not anomalies['extreme_spikes'].empty:
        report_lines.append(f"\nEXTREME SINGLE-YEAR SPIKES ({len(anomalies['extreme_spikes'])} items):")
        report_lines.append("(Top 99th percentile of year-over-year increases)")
        report_lines.append("-" * 80)
        for _, row in anomalies['extreme_spikes'].iterrows():
            report_lines.append(f"{row['item_name']} in {int(row['year'])}: {row['yoy_inflation_pct']:.2f}% increase")
            report_lines.append(f"  Category: {row['category']}, Price: ${row['price']:.2f}")
    
    if not anomalies['high_volatility'].empty:
        report_lines.append(f"\nHIGH VOLATILITY ITEMS ({len(anomalies['high_volatility'])} items):")
        report_lines.append("(Top 5% by coefficient of variation)")
        report_lines.append("-" * 80)
        for _, row in anomalies['high_volatility'].head(15).iterrows():
            report_lines.append(f"{row['item_name']}: CV={row['volatility_cv']:.2f}, Std={row['std_yoy_pct']:.2f}%, Mean={row['mean_yoy_pct']:.2f}%")
    
    if not anomalies['category_outliers'].empty:
        report_lines.append(f"\nCATEGORY OUTLIERS ({len(anomalies['category_outliers'])} items):")
        report_lines.append("(Items with mean YoY >2 standard deviations above category median)")
        report_lines.append("-" * 80)
        for _, row in anomalies['category_outliers'].head(15).iterrows():
            report_lines.append(f"{row['item_name']} ({row['category']}): {row['item_mean_yoy']:.2f}% vs category median {row['category_median_yoy']:.2f}% (Z={row['z_score']:.2f})")
    
    if not anomalies['price_corrections'].empty:
        report_lines.append(f"\nPOSSIBLE PRICE CORRECTIONS ({len(anomalies['price_corrections'])} items):")
        report_lines.append("(Large increase >50% followed by decrease >5%)")
        report_lines.append("-" * 80)
        for _, row in anomalies['price_corrections'].iterrows():
            report_lines.append(f"{row['item_name']} in {int(row['year'])}: {row['increase_pct']:.2f}% then {row['next_year_decrease_pct']:.2f}%")
            report_lines.append(f"  Price: ${row['price_before']:.2f} -> ${row['price_after']:.2f}")
    
    if not anomalies['data_quality_issues'].empty:
        report_lines.append(f"\nDATA QUALITY ISSUES ({len(anomalies['data_quality_issues'])} items):")
        report_lines.append("(Extreme cumulative inflation >500%)")
        report_lines.append("-" * 80)
        for _, row in anomalies['data_quality_issues'].iterrows():
            report_lines.append(f"{row['item_name']}: {row['cumulative_inflation_pct']:.2f}% cumulative inflation in {int(row['year'])}")
    
    report_text = "\n".join(report_lines)
    
    # Save report
    report_file = output_dir / "recurrent_price_increases_report.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)
    
    print(f"Saved report: {report_file}")
    
    return report_text

def main():
    """Main function to run the analysis."""
    print("Loading item-level inflation data...")
    item_df = load_data()
    
    print(f"Loaded {len(item_df)} records for {item_df['item_name'].nunique()} unique items")
    
    print("\nAnalyzing recurrent price increases...")
    recurrence_df = analyze_recurrent_price_increases(item_df)
    
    print("Detecting anomalies...")
    anomalies = detect_anomalies(item_df, recurrence_df)
    
    # Create output directory
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    print("\nSaving results...")
    recurrence_df.to_csv(output_dir / "recurrent_price_increases.csv", index=False)
    print(f"Saved recurrence analysis: {output_dir / 'recurrent_price_increases.csv'}")
    
    # Save anomaly dataframes
    for anomaly_type, df in anomalies.items():
        if not df.empty:
            df.to_csv(output_dir / f"anomalies_{anomaly_type}.csv", index=False)
            print(f"Saved {anomaly_type}: {len(df)} items")
        else:
            print(f"No {anomaly_type} found")
    
    # Generate report
    print("\nGenerating report...")
    generate_recurrence_report(recurrence_df, anomalies, output_dir)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total items analyzed: {len(recurrence_df)}")
    print(f"Items with extreme spikes: {len(anomalies['extreme_spikes'])}")
    print(f"High volatility items: {len(anomalies['high_volatility'])}")
    print(f"Category outliers: {len(anomalies['category_outliers'])}")
    print(f"Possible price corrections: {len(anomalies['price_corrections'])}")
    print(f"Data quality issues: {len(anomalies['data_quality_issues'])}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

