import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

def create_overall_comparison_chart(comparisons_df, output_dir):
    """Create line chart comparing CPI-U vs overall commissary inflation."""
    overall = comparisons_df[comparisons_df['level'] == 'overall'].copy()
    
    # Prepare data for plotting
    plot_data = []
    for _, row in overall.iterrows():
        plot_data.append({
            'year': row['year'],
            'Inflation Rate (%)': row['commissary_yoy_pct'],
            'Type': 'Commissary'
        })
        plot_data.append({
            'year': row['year'],
            'Inflation Rate (%)': row['cpi_yoy_pct'],
            'Type': 'CPI-U'
        })
    
    plot_df = pd.DataFrame(plot_data)
    plot_df = plot_df.dropna()
    
    fig = px.line(
        plot_df,
        x='year',
        y='Inflation Rate (%)',
        color='Type',
        title='Year-over-Year Inflation: Commissary vs CPI-U',
        labels={'year': 'Year', 'Inflation Rate (%)': 'Inflation Rate (%)'},
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(tickmode='linear', tick0=2019, dtick=1),
        yaxis_title='Inflation Rate (%)'
    )
    
    output_file = output_dir / "overall_inflation_comparison.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_cumulative_inflation_chart(comparisons_df, output_dir):
    """Create chart showing cumulative inflation from 2019 baseline."""
    overall = comparisons_df[comparisons_df['level'] == 'overall'].copy()
    
    plot_data = []
    for _, row in overall.iterrows():
        plot_data.append({
            'year': row['year'],
            'Cumulative Inflation (%)': row['commissary_cum_pct'],
            'Type': 'Commissary'
        })
        plot_data.append({
            'year': row['year'],
            'Cumulative Inflation (%)': row['cpi_cum_pct'],
            'Type': 'CPI-U'
        })
    
    plot_df = pd.DataFrame(plot_data)
    plot_df = plot_df.dropna()
    
    fig = px.line(
        plot_df,
        x='year',
        y='Cumulative Inflation (%)',
        color='Type',
        title='Cumulative Inflation Since 2019: Commissary vs CPI-U',
        labels={'year': 'Year', 'Cumulative Inflation (%)': 'Cumulative Inflation (%)'},
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(tickmode='linear', tick0=2019, dtick=1),
        yaxis_title='Cumulative Inflation (%)'
    )
    
    output_file = output_dir / "cumulative_inflation_comparison.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_category_comparison_chart(comparisons_df, output_dir):
    """Create multi-line chart comparing each commissary category to its CPI category."""
    category_comps = comparisons_df[comparisons_df['level'] == 'cpi_category'].copy()
    
    # Get unique CPI categories
    cpi_categories = sorted(category_comps['cpi_type'].unique())
    
    fig = go.Figure()
    
    for cpi_cat in cpi_categories:
        cat_data = category_comps[category_comps['cpi_type'] == cpi_cat].sort_values('year')
        
        # Commissary line
        fig.add_trace(go.Scatter(
            x=cat_data['year'],
            y=cat_data['commissary_yoy_pct'],
            mode='lines+markers',
            name=f'{cpi_cat} (Commissary)',
            line=dict(dash='solid'),
            hovertemplate=f'{cpi_cat} (Commissary)<br>Year: %{{x}}<br>Inflation: %{{y:.2f}}%<extra></extra>'
        ))
        
        # CPI line
        fig.add_trace(go.Scatter(
            x=cat_data['year'],
            y=cat_data['cpi_yoy_pct'],
            mode='lines+markers',
            name=f'{cpi_cat} (CPI)',
            line=dict(dash='dash'),
            hovertemplate=f'{cpi_cat} (CPI)<br>Year: %{{x}}<br>Inflation: %{{y:.2f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        title='Year-over-Year Inflation by Category: Commissary vs CPI',
        xaxis_title='Year',
        yaxis_title='Inflation Rate (%)',
        hovermode='x unified',
        xaxis=dict(tickmode='linear', tick0=2019, dtick=1),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    output_file = output_dir / "category_inflation_comparison.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_inflation_difference_chart(comparisons_df, output_dir):
    """Create chart showing the difference (commissary - CPI) by category."""
    category_comps = comparisons_df[comparisons_df['level'] == 'cpi_category'].copy()
    
    # Get latest year data
    latest_year = category_comps['year'].max()
    latest_data = category_comps[category_comps['year'] == latest_year].copy()
    latest_data = latest_data.sort_values('cum_diff_pct', ascending=False)
    
    fig = px.bar(
        latest_data,
        x='cpi_type',
        y='cum_diff_pct',
        title=f'Cumulative Inflation Difference (Commissary - CPI) by Category ({int(latest_year)})',
        labels={'cpi_type': 'Category', 'cum_diff_pct': 'Inflation Difference (percentage points)'},
        color='cum_diff_pct',
        color_continuous_scale='RdBu_r',
        text='cum_diff_pct'
    )
    
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        xaxis_title='Category',
        yaxis_title='Inflation Difference (percentage points)',
        showlegend=False,
        yaxis=dict(zeroline=True, zerolinecolor='black', zerolinewidth=2)
    )
    
    output_file = output_dir / "inflation_difference_by_category.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_item_level_analysis(commissary_inflation_df, cpi_inflation_df, output_dir):
    """Create interactive scatter plot showing individual item price changes vs CPI."""
    # Get 2024 data for items
    item_2024 = commissary_inflation_df[commissary_inflation_df['year'] == 2024].copy()
    
    # Get CPI-U cumulative inflation for 2024
    cpi_u_2024 = cpi_inflation_df[
        (cpi_inflation_df['cpi_type'] == 'CPI-U') & 
        (cpi_inflation_df['year'] == 2024)
    ]
    
    if len(cpi_u_2024) == 0:
        print("Warning: No CPI-U data for 2024, skipping item-level analysis")
        return None
    
    cpi_u_value = cpi_u_2024['cumulative_inflation_pct'].iloc[0]
    
    # Add difference from CPI-U
    item_2024['diff_from_cpi'] = item_2024['cumulative_inflation_pct'] - cpi_u_value
    
    # Create scatter plot
    fig = px.scatter(
        item_2024,
        x='cumulative_inflation_pct',
        y='diff_from_cpi',
        color='cpi_category',
        hover_data=['item_name', 'category', 'size'],
        title='Individual Item Price Changes vs CPI-U (2024 Cumulative Inflation)',
        labels={
            'cumulative_inflation_pct': 'Item Cumulative Inflation (%)',
            'diff_from_cpi': 'Difference from CPI-U (percentage points)',
            'cpi_category': 'CPI Category'
        },
        size_max=10
    )
    
    # Add vertical line at CPI-U value
    fig.add_vline(
        x=cpi_u_value,
        line_dash="dash",
        line_color="red",
        annotation_text=f"CPI-U: {cpi_u_value:.1f}%",
        annotation_position="top"
    )
    
    # Add horizontal line at zero
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray"
    )
    
    fig.update_layout(
        hovermode='closest',
        xaxis_title='Item Cumulative Inflation (%)',
        yaxis_title='Difference from CPI-U (percentage points)'
    )
    
    output_file = output_dir / "item_level_analysis.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_inflation_difference_over_time(comparisons_df, output_dir):
    """Create line chart showing inflation difference over time by category."""
    category_comps = comparisons_df[comparisons_df['level'] == 'cpi_category'].copy()
    
    fig = px.line(
        category_comps,
        x='year',
        y='yoy_diff_pct',
        color='cpi_type',
        title='Year-over-Year Inflation Difference (Commissary - CPI) Over Time',
        labels={
            'year': 'Year',
            'yoy_diff_pct': 'Inflation Difference (percentage points)',
            'cpi_type': 'Category'
        },
        markers=True
    )
    
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="CPI baseline"
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(tickmode='linear', tick0=2019, dtick=1),
        yaxis_title='Inflation Difference (percentage points)'
    )
    
    output_file = output_dir / "inflation_difference_over_time.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def main():
    # Load data (relative to project root)
    project_root = Path(__file__).parent.parent
    print("Loading inflation data...")
    analysis_dir = project_root / "analysis" / "outputs"
    
    comparisons_file = analysis_dir / "inflation_comparisons.csv"
    commissary_item_file = analysis_dir / "commissary_inflation_item_level.csv"
    cpi_inflation_file = analysis_dir / "cpi_inflation.csv"
    
    if not comparisons_file.exists():
        print(f"Error: Comparison data not found at {comparisons_file}")
        print("Please run calculate_inflation.py first.")
        return
    
    comparisons_df = pd.read_csv(comparisons_file)
    commissary_inflation_df = pd.read_csv(commissary_item_file)
    cpi_inflation_df = pd.read_csv(cpi_inflation_file)
    
    # Create output directory (relative to project root)
    output_dir = project_root / "viz" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Creating visualizations...")
    print('='*60)
    
    # Create all visualizations
    create_overall_comparison_chart(comparisons_df, output_dir)
    create_cumulative_inflation_chart(comparisons_df, output_dir)
    create_category_comparison_chart(comparisons_df, output_dir)
    create_inflation_difference_chart(comparisons_df, output_dir)
    create_inflation_difference_over_time(comparisons_df, output_dir)
    create_item_level_analysis(commissary_inflation_df, cpi_inflation_df, output_dir)
    
    print(f"\n{'='*60}")
    print("All visualizations created successfully!")
    print(f"Output directory: {output_dir}")
    print('='*60)

if __name__ == "__main__":
    main()

