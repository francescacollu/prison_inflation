import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Read the data
df = pd.read_csv('data/retail/processed/retail_vs_commissary_2025_prices.csv')

# Filter out items without commissary matches
df = df[df['commissary_match_count'] > 0].copy()

# Clean up data types
numeric_cols = [
    'retail_price_per_unit_mean', 'retail_price_per_unit_median',
    'retail_price_per_unit_min', 'retail_price_per_unit_max',
    'commissary_price_min', 'commissary_price_max',
    'commissary_price_per_unit_min', 'commissary_price_per_unit_max'
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Extract commissary size numeric value and unit
def parse_size(size_str):
    if pd.isna(size_str):
        return None, None
    # Handle various formats like "6 oz", "12 pk", "1.79oz", etc.
    import re
    match = re.match(r'([\d.]+)\s*(\w+)', str(size_str).replace('oz', 'oz').replace('pk', 'pk').replace('ct', 'ct').replace('tabs', 'tabs'))
    if match:
        return float(match.group(1)), match.group(2)
    return None, None

df[['commissary_size_value', 'commissary_size_unit']] = df['commissary_size'].apply(lambda x: pd.Series(parse_size(x)))

# Calculate retail prices for commissary sizes
def calculate_retail_price_for_commissary_size(row):
    if pd.isna(row['commissary_size_value']) or pd.isna(row['retail_price_per_unit_mean']):
        return None, None, None

    # Convert units if needed (simplified - assuming oz/ct are compatible)
    retail_per_unit = row['retail_price_per_unit_mean']

    # Calculate price range for the commissary size
    min_price = row['retail_price_per_unit_min'] * row['commissary_size_value']
    max_price = row['retail_price_per_unit_max'] * row['commissary_size_value']
    mean_price = retail_per_unit * row['commissary_size_value']

    return min_price, max_price, mean_price

df[['retail_price_for_commissary_min', 'retail_price_for_commissary_max', 'retail_price_for_commissary_mean']] = df.apply(
    calculate_retail_price_for_commissary_size, axis=1, result_type='expand'
)

# Create subplots
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Unit Price Comparison', 'Total Price Comparison (Commissary Sizes)'),
    vertical_spacing=0.1
)

# Colors
retail_color = '#000814'
commissary_color = '#ffc300'

# Plot 1: Unit Prices
for i, row in df.iterrows():
    item = row['item_category']

    # Retail unit price range
    if not pd.isna(row['retail_price_per_unit_min']) and not pd.isna(row['retail_price_per_unit_max']):
        fig.add_trace(
            go.Scatter(
                x=[row['retail_price_per_unit_min'], row['retail_price_per_unit_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=retail_color, width=3),
                marker=dict(color=retail_color, size=8),
                name='Retail Unit Price Range' if i == 0 else None,
                legendgroup='retail_unit',
                showlegend=i == 0
            ),
            row=1, col=1
        )

    # Commissary unit price range
    if not pd.isna(row['commissary_price_per_unit_min']) and not pd.isna(row['commissary_price_per_unit_max']):
        fig.add_trace(
            go.Scatter(
                x=[row['commissary_price_per_unit_min'], row['commissary_price_per_unit_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=commissary_color, width=3),
                marker=dict(color=commissary_color, size=8),
                name='Commissary Unit Price Range' if i == 0 else None,
                legendgroup='commissary_unit',
                showlegend=i == 0
            ),
            row=1, col=1
        )

# Plot 2: Total Prices (Commissary Sizes)
for i, row in df.iterrows():
    item = row['item_category']

    # Retail total price range (scaled to commissary size)
    if not pd.isna(row['retail_price_for_commissary_min']) and not pd.isna(row['retail_price_for_commissary_max']):
        fig.add_trace(
            go.Scatter(
                x=[row['retail_price_for_commissary_min'], row['retail_price_for_commissary_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=retail_color, width=3),
                marker=dict(color=retail_color, size=8),
                name='Retail Total Price Range' if i == 0 else None,
                legendgroup='retail_total',
                showlegend=i == 0
            ),
            row=2, col=1
        )

    # Commissary total price range
    if not pd.isna(row['commissary_price_min']) and not pd.isna(row['commissary_price_max']):
        fig.add_trace(
            go.Scatter(
                x=[row['commissary_price_min'], row['commissary_price_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=commissary_color, width=3),
                marker=dict(color=commissary_color, size=8),
                name='Commissary Total Price Range' if i == 0 else None,
                legendgroup='commissary_total',
                showlegend=i == 0
            ),
            row=2, col=1
        )

# Update layout
fig.update_layout(
    height=800,
    title_text="Retail vs Commissary Price Comparison",
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Update x-axes labels
fig.update_xaxes(title_text="Price per Unit ($)", row=1, col=1)
fig.update_xaxes(title_text="Total Price ($)", row=2, col=1)

# Update y-axes
fig.update_yaxes(title_text="Item", row=1, col=1)
fig.update_yaxes(title_text="Item", row=2, col=1)

# Save the plot
fig.write_html('src/viz/outputs/price_comparison_plots.html')
print("Plots saved to src/viz/outputs/price_comparison_plots.html")

# Also create individual plots for better viewing
# Unit price plot
fig_unit = go.Figure()

for i, row in df.iterrows():
    item = row['item_category']

    # Retail unit price range
    if not pd.isna(row['retail_price_per_unit_min']) and not pd.isna(row['retail_price_per_unit_max']):
        fig_unit.add_trace(
            go.Scatter(
                x=[row['retail_price_per_unit_min'], row['retail_price_per_unit_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=retail_color, width=3),
                marker=dict(color=retail_color, size=8),
                name='Retail Unit Price Range'
            )
        )

    # Commissary unit price range
    if not pd.isna(row['commissary_price_per_unit_min']) and not pd.isna(row['commissary_price_per_unit_max']):
        fig_unit.add_trace(
            go.Scatter(
                x=[row['commissary_price_per_unit_min'], row['commissary_price_per_unit_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=commissary_color, width=3),
                marker=dict(color=commissary_color, size=8),
                name='Commissary Unit Price Range'
            )
        )

fig_unit.update_layout(
    title="Unit Price Comparison: Retail vs Commissary",
    xaxis_title="Price per Unit ($)",
    yaxis_title="Item",
    height=600
)
fig_unit.write_html('src/viz/outputs/unit_price_comparison.html')

# Total price plot
fig_total = go.Figure()

for i, row in df.iterrows():
    item = row['item_category']

    # Retail total price range
    if not pd.isna(row['retail_price_for_commissary_min']) and not pd.isna(row['retail_price_for_commissary_max']):
        fig_total.add_trace(
            go.Scatter(
                x=[row['retail_price_for_commissary_min'], row['retail_price_for_commissary_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=retail_color, width=3),
                marker=dict(color=retail_color, size=8),
                name='Retail Total Price Range'
            )
        )

    # Commissary total price range
    if not pd.isna(row['commissary_price_min']) and not pd.isna(row['commissary_price_max']):
        fig_total.add_trace(
            go.Scatter(
                x=[row['commissary_price_min'], row['commissary_price_max']],
                y=[item, item],
                mode='lines+markers',
                line=dict(color=commissary_color, width=3),
                marker=dict(color=commissary_color, size=8),
                name='Commissary Total Price Range'
            )
        )

fig_total.update_layout(
    title="Total Price Comparison: Retail vs Commissary (Commissary Sizes)",
    xaxis_title="Total Price ($)",
    yaxis_title="Item",
    height=600
)
fig_total.write_html('src/viz/outputs/total_price_comparison.html')

print("Individual plots also saved to src/viz/outputs/unit_price_comparison.html and src/viz/outputs/total_price_comparison.html")
