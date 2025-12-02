"""
Create visualizations for Essential vs Non-Essential analysis.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

def create_inflation_comparison_chart(analysis_df, output_dir):
    """
    Create side-by-side box plots or violin plots showing distribution of 
    inflation rates for essential vs non-essential.
    """
    latest_year = analysis_df['year'].max()
    latest_data = analysis_df[analysis_df['year'] == latest_year].copy()
    
    # Prepare data for plotting
    plot_data = []
    for _, row in latest_data.iterrows():
        if pd.notna(row['cumulative_inflation_pct']):
            plot_data.append({
                'Essential Status': row['essential_status'].replace('-', ' ').title(),
                'Cumulative Inflation (%)': row['cumulative_inflation_pct'],
                'Category': row['category']
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    # Create violin plot (shows distribution better than box plot)
    fig = px.violin(
        plot_df,
        x='Essential Status',
        y='Cumulative Inflation (%)',
        color='Essential Status',
        title=f'Distribution of Cumulative Inflation Rates (2019-{int(latest_year)}): Essential vs Non-Essential Items',
        labels={'Essential Status': 'Item Type'},
        box=True,  # Add box plot inside violin
        points='outliers'  # Show outliers
    )
    
    fig.update_layout(
        showlegend=False,
        yaxis_title='Cumulative Inflation (%)',
        xaxis_title='Item Type'
    )
    
    output_file = output_dir / "essential_vs_nonessential_comparison.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_inflation_over_time(timeseries_df, output_dir):
    """
    Create time series chart showing cumulative inflation over time for both groups.
    """
    fig = go.Figure()
    
    # Essential items line
    fig.add_trace(go.Scatter(
        x=timeseries_df['year'],
        y=timeseries_df['essential_mean'],
        mode='lines+markers',
        name='Essential Items',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Non-essential items line
    fig.add_trace(go.Scatter(
        x=timeseries_df['year'],
        y=timeseries_df['non_essential_mean'],
        mode='lines+markers',
        name='Non-Essential Items',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Average Cumulative Inflation Over Time: Essential vs Non-Essential Items',
        xaxis_title='Year',
        yaxis_title='Average Cumulative Inflation (%)',
        hovermode='x unified',
        xaxis=dict(tickmode='linear', tick0=2019, dtick=1),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    output_file = output_dir / "essential_inflation_over_time.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_category_breakdown(analysis_df, output_dir):
    """
    Create chart showing which categories within essential/non-essential have highest inflation.
    """
    latest_year = analysis_df['year'].max()
    latest_data = analysis_df[analysis_df['year'] == latest_year].copy()
    
    # Calculate mean inflation by category and essential status
    category_stats = latest_data.groupby(['category', 'essential_status']).agg({
        'cumulative_inflation_pct': 'mean'
    }).reset_index()
    category_stats = category_stats.rename(columns={'cumulative_inflation_pct': 'mean_inflation'})
    
    # Separate essential and non-essential
    essential_cats = category_stats[category_stats['essential_status'] == 'essential'].sort_values('mean_inflation', ascending=False)
    non_essential_cats = category_stats[category_stats['essential_status'] == 'non-essential'].sort_values('mean_inflation', ascending=False)
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Essential Items by Category', 'Non-Essential Items by Category'),
        horizontal_spacing=0.15
    )
    
    # Essential categories
    fig.add_trace(
        go.Bar(
            x=essential_cats['mean_inflation'],
            y=essential_cats['category'],
            orientation='h',
            name='Essential',
            marker_color='#1f77b4',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Non-essential categories
    fig.add_trace(
        go.Bar(
            x=non_essential_cats['mean_inflation'],
            y=non_essential_cats['category'],
            orientation='h',
            name='Non-Essential',
            marker_color='#ff7f0e',
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="Mean Cumulative Inflation (%)", row=1, col=1)
    fig.update_xaxes(title_text="Mean Cumulative Inflation (%)", row=1, col=2)
    fig.update_yaxes(title_text="Category", row=1, col=1)
    fig.update_yaxes(title_text="Category", row=1, col=2)
    
    fig.update_layout(
        title_text=f'Average Inflation by Category (2019-{int(latest_year)}): Essential vs Non-Essential Items',
        height=600,
        showlegend=False
    )
    
    output_file = output_dir / "essential_category_breakdown.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_statistical_comparison(analysis_df, output_dir):
    """
    Create visual representation of the statistical difference (e.g., difference in means with confidence intervals).
    """
    latest_year = analysis_df['year'].max()
    latest_data = analysis_df[analysis_df['year'] == latest_year].copy()
    
    essential_inflation = latest_data[latest_data['essential_status'] == 'essential']['cumulative_inflation_pct'].dropna()
    non_essential_inflation = latest_data[latest_data['essential_status'] == 'non-essential']['cumulative_inflation_pct'].dropna()
    
    # Calculate means and standard errors
    essential_mean = essential_inflation.mean()
    essential_se = essential_inflation.sem()
    non_essential_mean = non_essential_inflation.mean()
    non_essential_se = non_essential_inflation.sem()
    
    # Create bar chart with error bars
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=['Essential Items', 'Non-Essential Items'],
        y=[essential_mean, non_essential_mean],
        error_y=dict(
            type='data',
            array=[essential_se * 1.96, non_essential_se * 1.96],  # 95% CI
            visible=True
        ),
        marker_color=['#1f77b4', '#ff7f0e'],
        text=[f'{essential_mean:.1f}%', f'{non_essential_mean:.1f}%'],
        textposition='outside',
        showlegend=False
    ))
    
    # Add difference annotation
    diff = essential_mean - non_essential_mean
    fig.add_annotation(
        x=0.5,
        y=max(essential_mean, non_essential_mean) + 10,
        text=f'Difference: {diff:.2f} percentage points',
        showarrow=False,
        font=dict(size=14, color='black')
    )
    
    fig.update_layout(
        title=f'Average Cumulative Inflation (2019-{int(latest_year)}): Essential vs Non-Essential Items<br><sub>Error bars show 95% confidence intervals</sub>',
        yaxis_title='Average Cumulative Inflation (%)',
        xaxis_title='Item Type',
        height=500
    )
    
    output_file = output_dir / "essential_statistical_comparison.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def create_top_items_chart(analysis_df, output_dir):
    """
    Highlight specific items with extreme inflation in each group.
    """
    latest_year = analysis_df['year'].max()
    latest_data = analysis_df[analysis_df['year'] == latest_year].copy()
    
    essential_items = latest_data[latest_data['essential_status'] == 'essential'].nlargest(10, 'cumulative_inflation_pct')
    non_essential_items = latest_data[latest_data['essential_status'] == 'non-essential'].nlargest(10, 'cumulative_inflation_pct')
    
    # Create labels
    essential_labels = [
        f"{row['item_name']}" + (f" ({row['size']})" if pd.notna(row['size']) and row['size'] else "")
        for _, row in essential_items.iterrows()
    ]
    non_essential_labels = [
        f"{row['item_name']}" + (f" ({row['size']})" if pd.notna(row['size']) and row['size'] else "")
        for _, row in non_essential_items.iterrows()
    ]
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Top 10 Essential Items', 'Top 10 Non-Essential Items'),
        horizontal_spacing=0.2
    )
    
    # Essential items
    fig.add_trace(
        go.Bar(
            x=essential_items['cumulative_inflation_pct'],
            y=essential_labels,
            orientation='h',
            marker_color='#1f77b4',
            showlegend=False,
            text=[f"{x:.1f}%" for x in essential_items['cumulative_inflation_pct']],
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Non-essential items
    fig.add_trace(
        go.Bar(
            x=non_essential_items['cumulative_inflation_pct'],
            y=non_essential_labels,
            orientation='h',
            marker_color='#ff7f0e',
            showlegend=False,
            text=[f"{x:.1f}%" for x in non_essential_items['cumulative_inflation_pct']],
            textposition='outside'
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="Cumulative Inflation (%)", row=1, col=1)
    fig.update_xaxes(title_text="Cumulative Inflation (%)", row=1, col=2)
    fig.update_yaxes(title_text="Item", row=1, col=1)
    fig.update_yaxes(title_text="Item", row=1, col=2)
    
    fig.update_layout(
        title_text=f'Top 10 Items with Highest Inflation (2019-{int(latest_year)})',
        height=700,
        showlegend=False
    )
    
    output_file = output_dir / "essential_top_items.html"
    fig.write_html(str(output_file))
    print(f"Created: {output_file}")
    
    return fig

def main():
    """Create all essential vs non-essential visualizations."""
    # Load data
    analysis_dir = Path(__file__).parent.parent / "analysis" / "outputs"
    analysis_file = analysis_dir / "essential_vs_nonessential_analysis.csv"
    timeseries_file = analysis_dir / "essential_vs_nonessential_timeseries.csv"
    
    if not analysis_file.exists():
        print(f"Error: Analysis file not found at {analysis_file}")
        print("Please run analyze_essential_vs_nonessential.py first.")
        return
    
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    analysis_df = pd.read_csv(analysis_file)
    
    if timeseries_file.exists():
        timeseries_df = pd.read_csv(timeseries_file)
    else:
        print("Warning: Timeseries file not found. Creating from analysis data...")
        # Create timeseries from analysis data
        timeseries_data = []
        for year in sorted(analysis_df['year'].unique()):
            year_data = analysis_df[analysis_df['year'] == year]
            essential_mean = year_data[year_data['essential_status'] == 'essential']['cumulative_inflation_pct'].mean()
            non_essential_mean = year_data[year_data['essential_status'] == 'non-essential']['cumulative_inflation_pct'].mean()
            timeseries_data.append({
                'year': year,
                'essential_mean': essential_mean,
                'non_essential_mean': non_essential_mean,
                'difference': essential_mean - non_essential_mean if pd.notna(essential_mean) and pd.notna(non_essential_mean) else None
            })
        timeseries_df = pd.DataFrame(timeseries_data)
    
    print("\nCreating visualizations...")
    create_inflation_comparison_chart(analysis_df, output_dir)
    create_inflation_over_time(timeseries_df, output_dir)
    create_category_breakdown(analysis_df, output_dir)
    create_statistical_comparison(analysis_df, output_dir)
    create_top_items_chart(analysis_df, output_dir)
    
    print("\n" + "=" * 60)
    print("All visualizations created successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()

