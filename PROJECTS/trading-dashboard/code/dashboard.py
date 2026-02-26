"""
Trading Dashboard V2 - Bybit PnL Analysis
Single-file Streamlit dashboard with dark theme
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

COLORS = {
    "background": "#0f1419",
    "card_bg": "#1a1f26",
    "text": "#e7e9ea",
    "text_muted": "#8b98a5",
    "green": "#10b981",
    "red": "#ef4444",
    "accent": "#3b82f6",
    "border": "#2f3336",
}

DATA_PATH = Path(__file__).parent.parent / "data" / "trades.csv"

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="Trading Dashboard V2",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"""
<style>
    /* Main background */
    .stApp {{
        background-color: {COLORS['background']};
    }}

    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLORS['text']} !important;
    }}

    /* Text */
    p, span, label {{
        color: {COLORS['text_muted']};
    }}

    /* Metric cards */
    .metric-card {{
        background: {COLORS['card_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }}

    .metric-value {{
        font-size: 28px;
        font-weight: 700;
        margin: 8px 0;
    }}

    .metric-label {{
        font-size: 14px;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .profit {{
        color: {COLORS['green']};
    }}

    .loss {{
        color: {COLORS['red']};
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS['card_bg']};
        border-radius: 8px;
        padding: 8px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {COLORS['text_muted']};
        border-radius: 6px;
        padding: 10px 20px;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['accent']};
        color: white;
    }}

    /* DataFrames */
    .stDataFrame {{
        background-color: {COLORS['card_bg']};
        border-radius: 8px;
    }}

    /* Selectbox and inputs */
    .stSelectbox, .stMultiSelect {{
        background-color: {COLORS['card_bg']};
    }}

    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA LOADING & PROCESSING
# ============================================================================

@st.cache_data
def load_data():
    """Load and process trade data."""
    df = pd.read_csv(DATA_PATH)

    # Parse trade time
    df['Trade time'] = pd.to_datetime(df['Trade time'], format='%H:%M %Y-%m-%d')
    df = df.sort_values('Trade time').reset_index(drop=True)

    # Convert numeric columns
    numeric_cols = ['Order Quantity', 'Entry Price', 'Exit Price',
                    'Opening Fee', 'Closing Fee', 'Funding Fee', 'Realized P&L']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate additional metrics
    df['Total Fees'] = df['Opening Fee'] + df['Closing Fee']
    df['Gross P&L'] = df['Realized P&L'] + df['Total Fees'] - df['Funding Fee']
    df['Is Winner'] = df['Realized P&L'] > 0
    df['Trade Size'] = df['Order Quantity'] * df['Entry Price']
    df['Return %'] = (df['Realized P&L'] / df['Trade Size']) * 100
    df['Cumulative P&L'] = df['Realized P&L'].cumsum()
    df['Date'] = df['Trade time'].dt.date

    return df


def calculate_metrics(df):
    """Calculate dashboard KPIs."""
    total_pnl = df['Realized P&L'].sum()
    total_trades = len(df)
    winners = df[df['Realized P&L'] > 0]
    losers = df[df['Realized P&L'] <= 0]

    win_rate = (len(winners) / total_trades * 100) if total_trades > 0 else 0

    gross_profit = winners['Realized P&L'].sum() if len(winners) > 0 else 0
    gross_loss = abs(losers['Realized P&L'].sum()) if len(losers) > 0 else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    # Max Drawdown calculation
    cumulative = df['Cumulative P&L'].values
    running_max = np.maximum.accumulate(cumulative)
    drawdown = running_max - cumulative
    max_drawdown = drawdown.max()

    # Sharpe Ratio (simplified - daily)
    if len(df) > 1:
        daily_returns = df.groupby('Date')['Realized P&L'].sum()
        if daily_returns.std() > 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe = 0
    else:
        sharpe = 0

    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'total_trades': total_trades,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe,
        'avg_winner': winners['Realized P&L'].mean() if len(winners) > 0 else 0,
        'avg_loser': losers['Realized P&L'].mean() if len(losers) > 0 else 0,
        'total_fees': df['Total Fees'].sum(),
        'total_funding': df['Funding Fee'].sum(),
    }


# ============================================================================
# COMPONENTS
# ============================================================================

def render_metric_card(label, value, prefix="", suffix="", is_currency=False, show_color=False):
    """Render a styled metric card."""
    if is_currency:
        formatted_value = f"${value:,.2f}"
        color_class = "profit" if value >= 0 else "loss"
    elif isinstance(value, float):
        formatted_value = f"{prefix}{value:.2f}{suffix}"
        color_class = "profit" if show_color and value >= 0 else ("loss" if show_color and value < 0 else "")
    else:
        formatted_value = f"{prefix}{value}{suffix}"
        color_class = ""

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{formatted_value}</div>
    </div>
    """, unsafe_allow_html=True)


def create_equity_curve(df):
    """Create equity curve chart."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Trade time'],
        y=df['Cumulative P&L'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color=COLORS['green'], width=2),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor=f"rgba(16, 185, 129, 0.1)",
    ))

    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Trade Time",
        yaxis_title="Cumulative P&L ($)",
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        hovermode='x unified',
    )

    return fig


def create_pnl_bar_chart(df):
    """Create P&L bar chart per trade."""
    colors = [COLORS['green'] if x > 0 else COLORS['red'] for x in df['Realized P&L']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(range(1, len(df) + 1)),
        y=df['Realized P&L'],
        marker_color=colors,
        name='P&L',
        text=[f"${x:.2f}" for x in df['Realized P&L']],
        textposition='outside',
    ))

    fig.update_layout(
        title="P&L by Trade",
        xaxis_title="Trade #",
        yaxis_title="Realized P&L ($)",
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=False,
    )

    return fig


def create_win_loss_pie(df):
    """Create win/loss distribution pie chart."""
    winners = len(df[df['Realized P&L'] > 0])
    losers = len(df[df['Realized P&L'] <= 0])

    fig = go.Figure(data=[go.Pie(
        labels=['Winners', 'Losers'],
        values=[winners, losers],
        marker_colors=[COLORS['green'], COLORS['red']],
        hole=0.6,
        textinfo='label+percent',
        textfont=dict(size=14, color=COLORS['text']),
    )])

    fig.update_layout(
        title="Win/Loss Distribution",
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=False,
        annotations=[dict(text=f'{winners}/{winners+losers}', x=0.5, y=0.5,
                         font_size=20, showarrow=False, font_color=COLORS['text'])]
    )

    return fig


def create_market_breakdown(df):
    """Create P&L by market chart."""
    market_pnl = df.groupby('Market')['Realized P&L'].sum().sort_values(ascending=True)
    colors = [COLORS['green'] if x > 0 else COLORS['red'] for x in market_pnl.values]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=market_pnl.index,
        x=market_pnl.values,
        orientation='h',
        marker_color=colors,
        text=[f"${x:.2f}" for x in market_pnl.values],
        textposition='outside',
    ))

    fig.update_layout(
        title="P&L by Market",
        xaxis_title="Realized P&L ($)",
        yaxis_title="Market",
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=False,
    )

    return fig


def create_daily_pnl(df):
    """Create daily P&L chart."""
    daily = df.groupby('Date')['Realized P&L'].sum().reset_index()
    colors = [COLORS['green'] if x > 0 else COLORS['red'] for x in daily['Realized P&L']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=daily['Date'],
        y=daily['Realized P&L'],
        marker_color=colors,
        text=[f"${x:.2f}" for x in daily['Realized P&L']],
        textposition='outside',
    ))

    fig.update_layout(
        title="Daily P&L",
        xaxis_title="Date",
        yaxis_title="P&L ($)",
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=False,
    )

    return fig


def create_return_distribution(df):
    """Create return % distribution histogram."""
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=df['Return %'],
        nbinsx=20,
        marker_color=COLORS['accent'],
        opacity=0.8,
    ))

    fig.update_layout(
        title="Return % Distribution",
        xaxis_title="Return %",
        yaxis_title="Frequency",
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
    )

    return fig


def create_funding_chart(df):
    """Create funding fee analysis chart."""
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'bar'}, {'type':'pie'}]],
                        subplot_titles=("Funding by Trade", "Funding by Market"))

    # Funding by trade
    colors = [COLORS['green'] if x <= 0 else COLORS['red'] for x in df['Funding Fee']]
    fig.add_trace(go.Bar(
        x=list(range(1, len(df) + 1)),
        y=df['Funding Fee'],
        marker_color=colors,
        name='Funding Fee',
    ), row=1, col=1)

    # Funding by market
    market_funding = df.groupby('Market')['Funding Fee'].sum().abs()
    fig.add_trace(go.Pie(
        labels=market_funding.index,
        values=market_funding.values,
        marker_colors=[COLORS['accent'], COLORS['green']],
        textinfo='label+percent',
    ), row=1, col=2)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=False,
        height=400,
    )

    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown(f"""
    <h1 style="text-align: center; margin-bottom: 0;">Trading Dashboard V2</h1>
    <p style="text-align: center; color: {COLORS['text_muted']}; margin-top: 5px;">
        Bybit Perpetual Futures | Performance Analysis
    </p>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Load data
    try:
        df = load_data()
        metrics = calculate_metrics(df)
    except FileNotFoundError:
        st.error(f"Data file not found: {DATA_PATH}")
        return

    # ========================================================================
    # KPI METRIC CARDS
    # ========================================================================

    cols = st.columns(6)

    with cols[0]:
        render_metric_card("Total P&L", metrics['total_pnl'], is_currency=True)

    with cols[1]:
        render_metric_card("Win Rate", metrics['win_rate'], suffix="%")

    with cols[2]:
        render_metric_card("Profit Factor", metrics['profit_factor'])

    with cols[3]:
        render_metric_card("Total Trades", metrics['total_trades'])

    with cols[4]:
        render_metric_card("Max Drawdown", -metrics['max_drawdown'], is_currency=True)

    with cols[5]:
        render_metric_card("Sharpe Ratio", metrics['sharpe_ratio'])

    st.markdown("<br>", unsafe_allow_html=True)

    # ========================================================================
    # TABS
    # ========================================================================

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "📈 Charts",
        "📋 Trade Log",
        "🔍 Analysis",
        "💰 Funding"
    ])

    # ------------------------------------------------------------------------
    # TAB 1: OVERVIEW
    # ------------------------------------------------------------------------
    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(create_equity_curve(df), use_container_width=True)

        with col2:
            st.plotly_chart(create_win_loss_pie(df), use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.plotly_chart(create_market_breakdown(df), use_container_width=True)

        with col4:
            st.plotly_chart(create_daily_pnl(df), use_container_width=True)

    # ------------------------------------------------------------------------
    # TAB 2: CHARTS
    # ------------------------------------------------------------------------
    with tab2:
        st.plotly_chart(create_pnl_bar_chart(df), use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(create_return_distribution(df), use_container_width=True)

        with col2:
            # Trade size vs P&L scatter
            fig = px.scatter(
                df, x='Trade Size', y='Realized P&L',
                color='Market',
                size='Order Quantity',
                hover_data=['Trade time', 'Entry Price', 'Exit Price'],
                title="Trade Size vs P&L",
                template="plotly_dark",
            )
            fig.update_layout(
                paper_bgcolor=COLORS['card_bg'],
                plot_bgcolor=COLORS['background'],
                font=dict(color=COLORS['text']),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------------
    # TAB 3: TRADE LOG
    # ------------------------------------------------------------------------
    with tab3:
        st.markdown("### Trade Log")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            market_filter = st.multiselect(
                "Filter by Market",
                options=df['Market'].unique(),
                default=df['Market'].unique()
            )

        with col2:
            pnl_filter = st.selectbox(
                "Filter by P&L",
                options=["All", "Winners Only", "Losers Only"]
            )

        with col3:
            sort_by = st.selectbox(
                "Sort by",
                options=["Trade time", "Realized P&L", "Trade Size"]
            )

        # Apply filters
        filtered_df = df[df['Market'].isin(market_filter)]

        if pnl_filter == "Winners Only":
            filtered_df = filtered_df[filtered_df['Realized P&L'] > 0]
        elif pnl_filter == "Losers Only":
            filtered_df = filtered_df[filtered_df['Realized P&L'] <= 0]

        # Sort
        ascending = sort_by == "Trade time"
        filtered_df = filtered_df.sort_values(sort_by, ascending=ascending)

        # Display columns
        display_cols = ['Trade time', 'Market', 'Order Quantity', 'Entry Price',
                       'Exit Price', 'Total Fees', 'Funding Fee', 'Realized P&L', 'Return %']

        # Format for display
        display_df = filtered_df[display_cols].copy()
        display_df['Realized P&L'] = display_df['Realized P&L'].apply(lambda x: f"${x:.2f}")
        display_df['Return %'] = display_df['Return %'].apply(lambda x: f"{x:.2f}%")
        display_df['Total Fees'] = display_df['Total Fees'].apply(lambda x: f"${x:.2f}")
        display_df['Funding Fee'] = display_df['Funding Fee'].apply(lambda x: f"${x:.2f}")
        display_df['Entry Price'] = display_df['Entry Price'].apply(lambda x: f"${x:.4f}")
        display_df['Exit Price'] = display_df['Exit Price'].apply(lambda x: f"${x:.4f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown(f"**Showing {len(filtered_df)} of {len(df)} trades**")

    # ------------------------------------------------------------------------
    # TAB 4: ANALYSIS
    # ------------------------------------------------------------------------
    with tab4:
        st.markdown("### Performance Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: {COLORS['text']};">Winner Statistics</h4>
                <p><strong>Count:</strong> {len(df[df['Realized P&L'] > 0])}</p>
                <p><strong>Average Win:</strong> <span class="profit">${metrics['avg_winner']:.2f}</span></p>
                <p><strong>Best Trade:</strong> <span class="profit">${df['Realized P&L'].max():.2f}</span></p>
                <p><strong>Total Profit:</strong> <span class="profit">${df[df['Realized P&L'] > 0]['Realized P&L'].sum():.2f}</span></p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: {COLORS['text']};">Loser Statistics</h4>
                <p><strong>Count:</strong> {len(df[df['Realized P&L'] <= 0])}</p>
                <p><strong>Average Loss:</strong> <span class="loss">${metrics['avg_loser']:.2f}</span></p>
                <p><strong>Worst Trade:</strong> <span class="loss">${df['Realized P&L'].min():.2f}</span></p>
                <p><strong>Total Loss:</strong> <span class="loss">${df[df['Realized P&L'] <= 0]['Realized P&L'].sum():.2f}</span></p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col3, col4 = st.columns(2)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: {COLORS['text']};">Fee Analysis</h4>
                <p><strong>Total Fees:</strong> ${metrics['total_fees']:.2f}</p>
                <p><strong>Total Funding:</strong> ${metrics['total_funding']:.2f}</p>
                <p><strong>Avg Fee/Trade:</strong> ${metrics['total_fees']/metrics['total_trades']:.2f}</p>
                <p><strong>Fees % of P&L:</strong> {(metrics['total_fees']/abs(metrics['total_pnl']))*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: {COLORS['text']};">Risk Metrics</h4>
                <p><strong>Max Drawdown:</strong> <span class="loss">-${metrics['max_drawdown']:.2f}</span></p>
                <p><strong>Sharpe Ratio:</strong> {metrics['sharpe_ratio']:.2f}</p>
                <p><strong>Avg Return:</strong> {df['Return %'].mean():.2f}%</p>
                <p><strong>Win/Loss Ratio:</strong> {abs(metrics['avg_winner']/metrics['avg_loser']) if metrics['avg_loser'] != 0 else 0:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Market Analysis
        st.markdown("### Market Performance")

        market_stats = df.groupby('Market').agg({
            'Realized P&L': ['sum', 'mean', 'count'],
            'Return %': 'mean',
            'Is Winner': 'mean'
        }).round(2)

        market_stats.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Avg Return %', 'Win Rate']
        market_stats['Win Rate'] = (market_stats['Win Rate'] * 100).round(1)
        market_stats = market_stats.reset_index()

        st.dataframe(market_stats, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------------
    # TAB 5: FUNDING
    # ------------------------------------------------------------------------
    with tab5:
        st.markdown("### Funding Fee Analysis")

        total_funding = df['Funding Fee'].sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            color_class = "profit" if total_funding <= 0 else "loss"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Funding Paid</div>
                <div class="metric-value {color_class}">${total_funding:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            avg_funding = df['Funding Fee'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Funding/Trade</div>
                <div class="metric-value">${avg_funding:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            funding_pct = (abs(total_funding) / abs(metrics['total_pnl'])) * 100
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Funding % of P&L</div>
                <div class="metric-value">{funding_pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.plotly_chart(create_funding_chart(df), use_container_width=True)

        # Funding breakdown table
        st.markdown("### Funding by Market")

        funding_by_market = df.groupby('Market').agg({
            'Funding Fee': ['sum', 'mean', 'min', 'max']
        }).round(4)

        funding_by_market.columns = ['Total', 'Average', 'Min', 'Max']
        funding_by_market = funding_by_market.reset_index()

        st.dataframe(funding_by_market, use_container_width=True, hide_index=True)

    # ========================================================================
    # FOOTER
    # ========================================================================

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown(f"""
    <p style="text-align: center; color: {COLORS['text_muted']}; font-size: 12px;">
        Trading Dashboard V2 | Total P&L: <span class="profit">${metrics['total_pnl']:.2f}</span> |
        {metrics['total_trades']} Trades | Data: Jan 20-21, 2026
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
