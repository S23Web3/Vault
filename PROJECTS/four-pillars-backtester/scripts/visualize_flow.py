"""
Generate interactive VINCE flow diagram.
Opens in browser with clickable nodes.
"""

import plotly.graph_objects as go
from pathlib import Path

def create_vince_flow():
    """Create interactive Sankey flow diagram."""
    
    # Define nodes (0-indexed)
    labels = [
        # Data Layer (0-2)
        "Market Data", "Bybit/WEEX API", "PostgreSQL",
        
        # Signal Layer (3-6)
        "OHLCV Data", "Stochastics", "Ripster Clouds", "State Machine",
        
        # Backtest Engine (7-10)
        "A/B/C Signals", "Backtester", "Position Manager", "Commission",
        
        # ML Layer (11-15)
        "Trade Results", "Feature Extraction", "XGBoost", "SHAP", "Loser Analysis",
        
        # Decision (16-19)
        "VINCE Brain", "Skip Trade", "Take Trade", "Exit Strategy",
        
        # Visualization (20-24)
        "Dashboard", "Overview", "Trade Analysis", "ML Meta-Label", "Validation"
    ]
    
    # Define flows (source, target, value)
    source = [
        0, 1, 2,           # Data ingestion
        3, 3, 4, 5,        # Signal generation
        6, 7, 8, 9,        # Backtest engine
        10, 11, 12, 13,    # ML layer
        14, 15, 15, 15,    # VINCE decisions
        16, 16, 16,        # Take trade paths
        20, 20, 20, 20     # Dashboard tabs
    ]
    
    target = [
        1, 2, 3,           # → API → DB → OHLCV
        4, 5, 6, 6,        # → Stoch/Clouds → State Machine
        7, 8, 9, 10,       # → Backtester → Position → Commission → Results
        11, 12, 13, 14,    # → Features → XGBoost → SHAP → Loser
        15, 16, 17, 18,    # → VINCE → Skip/Take/Exit
        18, 19, 20,        # → Exit → Strategy → Dashboard
        21, 22, 23, 24     # → Tabs
    ]
    
    value = [
        100, 100, 100,     # Data flow
        50, 50, 50, 100,   # Signal flow
        100, 100, 100, 100,# Backtest flow
        100, 100, 100, 100,# ML flow
        100, 30, 70, 70,   # VINCE decisions (30% skip, 70% take)
        70, 70, 70,        # Take → Exit → Dashboard
        25, 25, 25, 25     # Dashboard distribution
    ]
    
    # Colors
    colors = [
        '#1f77b4',  # Data layer (blue)
        '#ff7f0e',  # Signal layer (orange)
        '#2ca02c',  # Backtest engine (green)
        '#d62728',  # ML layer (red)
        '#9467bd',  # Decision (purple)
        '#8c564b',  # Dashboard (brown)
    ]
    
    node_colors = []
    for i, label in enumerate(labels):
        if i <= 2:
            node_colors.append(colors[0])
        elif i <= 6:
            node_colors.append(colors[1])
        elif i <= 10:
            node_colors.append(colors[2])
        elif i <= 15:
            node_colors.append(colors[3])
        elif i <= 19:
            node_colors.append(colors[4])
        else:
            node_colors.append(colors[5])
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color='rgba(0,0,0,0.2)'
        )
    )])
    
    fig.update_layout(
        title_text="VINCE Architecture Flow - Interactive",
        font_size=10,
        height=800
    )
    
    # Save
    output_path = Path("data/output/vince_flow.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    
    print(f"✅ Interactive flow saved to: {output_path}")
    print(f"   Open in browser: file:///{output_path.absolute()}")
    
    # Also show in default browser
    fig.show()

if __name__ == "__main__":
    create_vince_flow()
