"""
PDF Portfolio Report Exporter v2 -- Generates multi-page PDF with charts.
v2: Mode 2 (Shared Pool) awareness -- uses rebased equity and pool_pnl.
Uses matplotlib for charts and reportlab for PDF assembly.
"""
import io
import os
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as RLImage, PageBreak, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


REPORTS_DIR = Path(__file__).resolve().parent.parent / "results" / "pdf_reports"


def check_dependencies():
    """Check if reportlab and matplotlib are installed. Returns tuple (bool, str)."""
    if not HAS_REPORTLAB:
        return False, "reportlab not installed. Run: pip install reportlab"
    if not HAS_MATPLOTLIB:
        return False, "matplotlib not installed. Run: pip install matplotlib"
    return True, "OK"


def _fig_to_image(fig, width=6.5, dpi=150):
    """Convert matplotlib figure to reportlab Image object."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor="#1a1a2e", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    img = RLImage(buf, width=width * inch, height=(width * 0.5) * inch)
    return img


def _make_equity_chart(master_dt, portfolio_eq, per_coin_eq, title="Portfolio Equity"):
    """Create equity curve matplotlib chart. Returns figure."""
    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    step = max(1, len(master_dt) // 2000)
    dt_ds = master_dt[::step]
    for sym, eq in per_coin_eq.items():
        ax.plot(dt_ds, eq[::step], linewidth=0.5, alpha=0.4, label=sym)
    ax.plot(dt_ds, portfolio_eq[::step], linewidth=2, color="#00ff88", label="PORTFOLIO")
    ax.set_title(title, color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=7, loc="upper left", facecolor="#1a1a2e",
              edgecolor="#444", labelcolor="white")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.autofmt_xdate()
    return fig


def _make_capital_chart(master_dt, capital_allocated, total_capital=None):
    """Create capital utilization chart. Returns figure."""
    fig, ax = plt.subplots(figsize=(10, 3), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    step = max(1, len(master_dt) // 2000)
    dt_ds = master_dt[::step]
    ax.fill_between(dt_ds, capital_allocated[::step], alpha=0.5, color="#4488ff")
    ax.plot(dt_ds, capital_allocated[::step], linewidth=1, color="#4488ff")
    if total_capital is not None:
        ax.axhline(y=total_capital, color="#ff4444", linestyle="--", linewidth=1.5,
                   label=f"Total Capital: ${total_capital:,.0f}")
        ax.legend(fontsize=8, facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
    ax.set_title("Capital Utilization Over Time", color="white", fontsize=12)
    ax.set_ylabel("$ Capital", color="white")
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.autofmt_xdate()
    return fig


def _make_coin_equity_chart(dt_index, equity_curve, symbol):
    """Create individual coin equity chart. Returns figure."""
    fig, ax = plt.subplots(figsize=(8, 3), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    step = max(1, len(dt_index) // 1500)
    ax.plot(dt_index[::step], equity_curve[::step], linewidth=1.5, color="#00ff88")
    ax.axhline(y=10000, color="#888", linestyle="--", linewidth=0.5)  # engine baseline
    ax.set_title(f"{symbol} Equity Curve", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.autofmt_xdate()
    return fig


def generate_portfolio_pdf(pf_data, coin_results, portfolio_name="Portfolio",
                           total_capital=None, capital_result=None, output_path=None):
    """Generate multi-page PDF report. Returns output file path."""
    ok, msg = check_dependencies()
    if not ok:
        raise ImportError(msg)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in portfolio_name)
        output_path = REPORTS_DIR / f"portfolio_report_{safe_name}_{date_str}.pdf"
    else:
        output_path = Path(output_path)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"],
                                 fontSize=18, textColor=colors.HexColor("#00ff88"))
    heading_style = ParagraphStyle("CustomH2", parent=styles["Heading2"],
                                   fontSize=14, textColor=colors.HexColor("#4488ff"))
    body_style = ParagraphStyle("CustomBody", parent=styles["Normal"],
                                fontSize=10, textColor=colors.HexColor("#cccccc"))
    metric_style = ParagraphStyle("Metric", parent=styles["Normal"],
                                  fontSize=11, textColor=colors.white)

    elements = []

    # --- PAGE 1: Executive Summary ---
    elements.append(Paragraph(f"Portfolio Report: {portfolio_name}", title_style))
    elements.append(Spacer(1, 12))
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated: {gen_time}", body_style))
    elements.append(Spacer(1, 24))

    pf = pf_data
    _engine_baseline = 10000.0 * len(coin_results)
    if capital_result is not None and total_capital is not None and total_capital > 0:
        port_net = float(capital_result["capital_efficiency"].get("pool_pnl", 0))
    elif "rebased_portfolio_eq" in pf:
        port_net = float(pf["rebased_portfolio_eq"][-1] - total_capital) if total_capital else float(pf["portfolio_eq"][-1] - _engine_baseline)
    else:
        port_net = float(pf["portfolio_eq"][-1] - _engine_baseline)
    peak_cap = float(pf["capital_allocated"].max())
    avg_cap = float(pf["capital_allocated"].mean())
    total_trades = sum(cr["metrics"]["total_trades"] for cr in coin_results)

    total_vol = sum(cr["metrics"].get("total_volume", 0) for cr in coin_results)
    total_reb = sum(cr["metrics"].get("total_rebate", 0) for cr in coin_results)
    total_comm = sum(cr["metrics"].get("total_commission", 0) for cr in coin_results)

    summary_data = [
        ["Metric", "Value"],
        ["Coins", str(len(coin_results))],
        ["Total Trades", str(total_trades)],
        ["Net P&L", f"${port_net:,.2f}"],
        ["Total Volume", f"${total_vol:,.0f}"],
        ["Gross Commission", f"${total_comm:,.2f}"],
        ["Total Rebate", f"${total_reb:,.2f}"],
        ["Net Commission", f"${total_comm - total_reb:,.2f}"],
        ["Max Drawdown %", f"{pf['portfolio_dd_pct']:.1f}%"],
        ["Peak Capital Used", f"${peak_cap:,.0f}"],
        ["Avg Capital Used", f"${avg_cap:,.0f}"],
    ]
    if total_capital is not None:
        idle_pct = (1.0 - avg_cap / total_capital) * 100 if total_capital > 0 else 0
        summary_data.append(["Total Capital", f"${total_capital:,.0f}"])
        summary_data.append(["Avg Idle Capital", f"{idle_pct:.1f}%"])
        if capital_result is not None:
            _eff = capital_result["capital_efficiency"]
            summary_data.append(["Pool P&L", f"${_eff.get('pool_pnl', 0):+,.2f}"])
            summary_data.append(["Trades Rejected", str(_eff["trades_rejected"]) + " (" + f"{_eff['rejection_pct']:.1f}%" + ")"])
            summary_data.append(["Missed P&L", f"${_eff['missed_pnl']:,.2f}"])

    t = Table(summary_data, colWidths=[2.5 * inch, 3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#444")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#1a1a2e")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 24))

    # Best / Worst performers
    sorted_coins = sorted(coin_results,
                          key=lambda cr: float(cr["equity_curve"][-1] - 10000.0),  # engine always starts at 10k
                          reverse=True)
    elements.append(Paragraph("Top 3 Performers", heading_style))
    for cr in sorted_coins[:3]:
        net = float(cr["equity_curve"][-1] - 10000.0)
        elements.append(Paragraph(
            f"  {cr['symbol']}: ${net:,.2f} ({cr['metrics']['total_trades']} trades)", body_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Bottom 3 Performers", heading_style))
    for cr in sorted_coins[-3:]:
        net = float(cr["equity_curve"][-1] - 10000.0)
        elements.append(Paragraph(
            f"  {cr['symbol']}: ${net:,.2f} ({cr['metrics']['total_trades']} trades)", body_style))

    elements.append(PageBreak())

    # --- PAGE 2: Portfolio Charts ---
    elements.append(Paragraph("Portfolio Performance", title_style))
    elements.append(Spacer(1, 12))

    _pdf_chart_eq = pf.get("rebased_chart_eq", pf["portfolio_eq"]) if (total_capital is not None and total_capital > 0) else pf["portfolio_eq"]
    # In Shared Pool mode, rebase per-coin lines to P&L contribution (0-based)
    _pdf_per_coin = pf["per_coin_eq"]
    if total_capital is not None and total_capital > 0:
        _pdf_per_coin = {}
        for _sym, _eq_arr in pf["per_coin_eq"].items():
            _start_val = float(_eq_arr[0]) if len(_eq_arr) > 0 else 10000.0
            _pdf_per_coin[_sym] = _eq_arr - _start_val
    fig_eq = _make_equity_chart(pf["master_dt"], _pdf_chart_eq, _pdf_per_coin)
    elements.append(_fig_to_image(fig_eq))
    elements.append(Spacer(1, 12))

    fig_cap = _make_capital_chart(pf["master_dt"], pf["capital_allocated"], total_capital)
    elements.append(_fig_to_image(fig_cap, width=6.5))

    elements.append(PageBreak())

    # --- PAGE 3: Per-Coin Summary Table ---
    elements.append(Paragraph("Per-Coin Summary", title_style))
    elements.append(Spacer(1, 12))

    table_header = ["Symbol", "Trades", "WR%", "Net", "LSG%", "DD%", "Sharpe", "PF"]
    table_rows = [table_header]
    for cr in sorted_coins:
        m = cr["metrics"]
        net = float(cr["equity_curve"][-1] - 10000.0)
        lsg = m.get("pct_losers_saw_green", 0) * 100
        table_rows.append([
            cr["symbol"],
            str(m["total_trades"]),
            f"{m['win_rate']*100:.1f}",
            f"${net:,.2f}",
            f"{lsg:.1f}",
            f"{m['max_drawdown_pct']:.1f}",
            f"{m['sharpe']:.3f}",
            f"{m['profit_factor']:.2f}",
        ])

    col_widths = [1.2*inch, 0.6*inch, 0.5*inch, 0.9*inch, 0.5*inch, 0.5*inch, 0.6*inch, 0.5*inch]
    t2 = Table(table_rows, colWidths=col_widths)
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#444")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#1a1a2e")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    elements.append(t2)

    elements.append(PageBreak())

    # --- PAGES 4+: Per-Coin Detail ---
    for cr in sorted_coins:
        sym = cr["symbol"]
        m = cr["metrics"]
        net = float(cr["equity_curve"][-1] - 10000.0)
        elements.append(Paragraph(f"{sym} -- Detail", heading_style))
        elements.append(Spacer(1, 6))

        detail_data = [
            ["Metric", "Value"],
            ["Trades", str(m["total_trades"])],
            ["Win Rate", f"{m['win_rate']*100:.1f}%"],
            ["Net P&L", f"${net:,.2f}"],
            ["Sharpe", f"{m['sharpe']:.3f}"],
            ["Profit Factor", f"{m['profit_factor']:.2f}"],
            ["Max DD%", f"{m['max_drawdown_pct']:.1f}%"],
        ]
        td = Table(detail_data, colWidths=[2*inch, 2*inch])
        td.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#444")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#1a1a2e")),
        ]))
        elements.append(td)
        elements.append(Spacer(1, 12))

        # Coin equity chart
        dt_idx = cr.get("datetime_index")
        if dt_idx is not None and len(dt_idx) > 0:
            fig_coin = _make_coin_equity_chart(
                pd.DatetimeIndex(dt_idx), cr["equity_curve"], sym)
            elements.append(_fig_to_image(fig_coin, width=5.5))

        elements.append(PageBreak())

    # --- Build PDF ---
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    doc.build(elements)
    return str(output_path)
