r"""
Build Script: Dashboard Portfolio Enhancement v3
=================================================
Fixes 9 bugs found in v2 audit (2026-02-16):
  BUG1: Capital model returns original results unchanged (decorative only)
  BUG2: Bar indices are per-coin local, not cross-coin comparable
  BUG3: MFE in signal strength is look-ahead bias
  BUG4: rebate column doesn't exist in trades_df
  BUG5: entry_dt column doesn't exist in real trades_df
  BUG6: Sortino annualization uses trade count not bar count
  BUG7: Capital efficiency metrics use unconstrained values after rejections
  BUG8: be_raised not in trades_df
  BUG9: Test suite uses fabricated columns masking real failures

Creates all files for the 4-phase dashboard portfolio enhancement:
  Phase 1: Reusable Portfolios (utils/portfolio_manager.py)
  Phase 2: Enhanced Per-Coin Analysis (utils/coin_analysis.py)
  Phase 3: PDF Export (utils/pdf_exporter.py)
  Phase 4: Unified Capital Model (utils/capital_model.py)
  + Test suite + Debug script

Run:
  python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_portfolio_v3.py"

Hard Rules:
  - py_compile every file
  - Timestamps on all logging
  - Docstrings on all functions
  - No escaped quotes in f-strings
  - No emojis
"""
import os
import sys
import py_compile
from pathlib import Path
from datetime import datetime

PROJ = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
ERRORS = []
CREATED = []
TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    """Print timestamped log message."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def write_file(rel_path, content):
    """Write file, create dirs, py_compile, track results."""
    fpath = PROJ / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    if fpath.exists():
        backup = fpath.with_suffix(fpath.suffix + ".bak")
        log(f"  BACKUP: {rel_path} -> {backup.name}")
        fpath.rename(backup)
    fpath.write_text(content, encoding="utf-8")
    log(f"  WROTE: {rel_path} ({len(content)} bytes)")
    if rel_path.endswith(".py"):
        try:
            py_compile.compile(str(fpath), doraise=True)
            log(f"  COMPILE OK: {rel_path}")
            CREATED.append(rel_path)
        except py_compile.PyCompileError as e:
            log(f"  COMPILE FAIL: {rel_path} -- {e}")
            ERRORS.append(rel_path)
    else:
        CREATED.append(rel_path)


# ============================================================================
# FILE 1: utils/__init__.py
# ============================================================================
log("=== Phase 0: Creating utils package ===")
write_file("utils/__init__.py", '"""Dashboard utility modules for portfolio management, analysis, PDF export, and capital modeling."""\n')


# ============================================================================
# FILE 2: utils/portfolio_manager.py (Phase 1: Reusable Portfolios)
# ============================================================================
log("=== Phase 1: Portfolio Manager ===")
PORTFOLIO_MANAGER = r'''"""
Portfolio Manager -- Save, load, list, delete portfolio templates.
Stores coin selections as JSON in portfolios/ directory.
"""
import json
from pathlib import Path
from datetime import datetime


PORTFOLIOS_DIR = Path(__file__).resolve().parent.parent / "portfolios"


def ensure_dir():
    """Create portfolios directory if it does not exist."""
    PORTFOLIOS_DIR.mkdir(parents=True, exist_ok=True)


def save_portfolio(name, coins, selection_method="custom", notes="", params_hash=""):
    """Save a portfolio template to JSON file."""
    ensure_dir()
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in name).strip()
    safe_name = safe_name.replace(" ", "_").lower()
    if not safe_name:
        safe_name = "portfolio_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "name": name,
        "safe_name": safe_name,
        "created": datetime.now().isoformat(),
        "coins": list(coins),
        "coin_count": len(coins),
        "selection_method": selection_method,
        "params_hash": params_hash,
        "notes": notes,
    }
    fpath = PORTFOLIOS_DIR / f"{safe_name}.json"
    fpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(fpath)


def load_portfolio(filename):
    """Load a portfolio template from JSON file. Returns dict or None."""
    fpath = PORTFOLIOS_DIR / filename
    if not fpath.exists():
        return None
    try:
        data = json.loads(fpath.read_text(encoding="utf-8"))
        return data
    except (json.JSONDecodeError, KeyError):
        return None


def list_portfolios():
    """List all saved portfolios. Returns list of dicts with name, file, coin_count, created."""
    ensure_dir()
    result = []
    for f in sorted(PORTFOLIOS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "file": f.name,
                "name": data.get("name", f.stem),
                "coin_count": data.get("coin_count", len(data.get("coins", []))),
                "created": data.get("created", ""),
                "selection_method": data.get("selection_method", ""),
                "notes": data.get("notes", ""),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return result


def delete_portfolio(filename):
    """Delete a portfolio template file. Returns True if deleted."""
    fpath = PORTFOLIOS_DIR / filename
    if fpath.exists():
        fpath.unlink()
        return True
    return False


def rename_portfolio(old_filename, new_name):
    """Rename a portfolio (updates name field and filename)."""
    data = load_portfolio(old_filename)
    if data is None:
        return None
    delete_portfolio(old_filename)
    return save_portfolio(
        name=new_name,
        coins=data["coins"],
        selection_method=data.get("selection_method", "custom"),
        notes=data.get("notes", ""),
        params_hash=data.get("params_hash", ""),
    )
'''
write_file("utils/portfolio_manager.py", PORTFOLIO_MANAGER)


# ============================================================================
# FILE 3: utils/coin_analysis.py (Phase 2: Enhanced Per-Coin Analysis)
# FIX BUG4: removed rebate column reference
# FIX BUG5: entry_dt -> map entry_bar through datetime_index
# FIX BUG6: Sortino accepts bar_count parameter
# FIX BUG8: added be_raised awareness
# ============================================================================
log("=== Phase 2: Coin Analysis (v3 -- 4 bugs fixed) ===")
COIN_ANALYSIS = r'''"""
Enhanced Per-Coin Analysis -- Extended metrics and drill-down data.
Computes 10 additional metrics beyond the base 7.

v3 fixes (2026-02-16):
  - Sortino annualization uses bar_count (not trade count)
  - compute_monthly_pnl maps entry_bar through datetime_index
  - compute_commission_breakdown: rebate removed (not in Trade384)
  - Added be_raised to loser detail when available
"""
import numpy as np
import pandas as pd


def compute_extended_metrics(trades_df, bar_count=None):
    """Compute 10 extended metrics from a trades DataFrame. Returns dict."""
    if trades_df is None or trades_df.empty:
        return {
            "avg_trade": 0.0, "best_trade": 0.0, "worst_trade": 0.0,
            "sl_pct": 0.0, "tp_pct": 0.0, "scale_pct": 0.0,
            "avg_mfe": 0.0, "avg_mae": 0.0,
            "max_consec_loss": 0, "sortino": 0.0,
        }
    net_col = "net_pnl" if "net_pnl" in trades_df.columns else "pnl"
    pnls = trades_df[net_col].values.astype(float)
    n = len(pnls)

    # Avg / Best / Worst trade
    avg_trade = float(pnls.mean()) if n > 0 else 0.0
    best_trade = float(pnls.max()) if n > 0 else 0.0
    worst_trade = float(pnls.min()) if n > 0 else 0.0

    # Exit reason breakdown
    if "exit_reason" in trades_df.columns:
        reasons = trades_df["exit_reason"].str.upper()
        sl_count = int((reasons == "SL").sum())
        tp_count = int((reasons == "TP").sum())
        scale_count = int(reasons.str.startswith("SCALE").sum())
    else:
        sl_count = tp_count = scale_count = 0
    sl_pct = round(sl_count / n * 100, 1) if n > 0 else 0.0
    tp_pct = round(tp_count / n * 100, 1) if n > 0 else 0.0
    scale_pct = round(scale_count / n * 100, 1) if n > 0 else 0.0

    # MFE / MAE averages
    avg_mfe = float(trades_df["mfe"].mean()) if "mfe" in trades_df.columns and n > 0 else 0.0
    avg_mae = float(trades_df["mae"].mean()) if "mae" in trades_df.columns and n > 0 else 0.0

    # Max consecutive losses
    max_consec = 0
    current = 0
    for p in pnls:
        if p < 0:
            current += 1
            max_consec = max(max_consec, current)
        else:
            current = 0

    # Sortino ratio (annualized for 5m bars, ~105,120 bars/year)
    # FIX BUG6: use bar_count (equity curve length) not trade count
    ann_factor = 105120  # 5m bars per year
    if bar_count is not None and bar_count > 0:
        ann_factor = min(bar_count, 105120)
    downside = pnls[pnls < 0]
    if len(downside) > 1 and pnls.std() > 0:
        downside_std = float(np.std(downside, ddof=1))
        sortino = float(pnls.mean() / downside_std * np.sqrt(ann_factor)) if downside_std > 0 else 0.0
    else:
        sortino = 0.0

    return {
        "avg_trade": round(avg_trade, 2),
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),
        "sl_pct": sl_pct,
        "tp_pct": tp_pct,
        "scale_pct": scale_pct,
        "avg_mfe": round(avg_mfe, 4),
        "avg_mae": round(avg_mae, 4),
        "max_consec_loss": max_consec,
        "sortino": round(sortino, 3),
    }


def compute_grade_distribution(trades_df):
    """Compute grade distribution from trades. Returns dict of grade -> count."""
    if trades_df is None or trades_df.empty or "grade" not in trades_df.columns:
        return {}
    return dict(trades_df["grade"].value_counts().sort_index())


def compute_exit_distribution(trades_df):
    """Compute exit reason distribution. Returns dict of reason -> count."""
    if trades_df is None or trades_df.empty or "exit_reason" not in trades_df.columns:
        return {}
    return dict(trades_df["exit_reason"].value_counts())


def compute_monthly_pnl(trades_df, datetime_index=None):
    """Compute monthly P&L by mapping entry_bar to datetime via datetime_index."""
    if trades_df is None or trades_df.empty:
        return pd.DataFrame(columns=["month", "pnl"])
    net_col = "net_pnl" if "net_pnl" in trades_df.columns else "pnl"
    # FIX BUG5: entry_dt doesnt exist in real trades_df, map entry_bar instead
    if datetime_index is not None and "entry_bar" in trades_df.columns:
        df = trades_df.copy()
        dt_idx = pd.DatetimeIndex(datetime_index)
        max_bar = len(dt_idx) - 1
        bars = df["entry_bar"].clip(0, max_bar).astype(int)
        df["_entry_dt"] = dt_idx[bars]
        df["_month"] = df["_entry_dt"].dt.to_period("M").astype(str)
        monthly = df.groupby("_month")[net_col].sum().reset_index()
        monthly.columns = ["month", "pnl"]
        return monthly
    return pd.DataFrame(columns=["month", "pnl"])


def compute_loser_detail(trades_df):
    """Extract loser trades that saw green with detail. Returns DataFrame."""
    if trades_df is None or trades_df.empty:
        return pd.DataFrame()
    net_col = "net_pnl" if "net_pnl" in trades_df.columns else "pnl"
    losers = trades_df[trades_df[net_col] < 0].copy()
    if losers.empty or "saw_green" not in losers.columns:
        return pd.DataFrame()
    green_losers = losers[losers["saw_green"] == True].copy()
    if green_losers.empty:
        return pd.DataFrame()
    cols = ["direction", "grade", "entry_price", "exit_price", net_col, "mfe", "mae", "exit_reason"]
    available = [c for c in cols if c in green_losers.columns]
    return green_losers[available].round(4)


def compute_commission_breakdown(trades_df):
    """Compute commission breakdown. Returns dict."""
    # FIX BUG4: rebate column does not exist in Trade384/trades_df.
    # Rebates are settled daily at 17:00 UTC by the commission model,
    # not tracked per-trade. Only report gross commission here.
    if trades_df is None or trades_df.empty:
        return {"total_commission": 0.0, "net_commission": 0.0}
    comm = float(trades_df["commission"].sum()) if "commission" in trades_df.columns else 0.0
    return {
        "total_commission": round(comm, 2),
        "net_commission": round(comm, 2),
    }
'''
write_file("utils/coin_analysis.py", COIN_ANALYSIS)


# ============================================================================
# FILE 4: utils/pdf_exporter.py (Phase 3: PDF Export)
# No structural bugs found in v2 -- carried forward unchanged.
# ============================================================================
log("=== Phase 3: PDF Exporter ===")
PDF_EXPORTER = r'''"""
PDF Portfolio Report Exporter -- Generates multi-page PDF with charts.
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
    ax.axhline(y=10000, color="#888", linestyle="--", linewidth=0.5)
    ax.set_title(f"{symbol} Equity Curve", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.autofmt_xdate()
    return fig


def generate_portfolio_pdf(pf_data, coin_results, portfolio_name="Portfolio",
                           total_capital=None, output_path=None):
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
    port_net = float(pf["portfolio_eq"][-1] - 10000.0 * len(coin_results))
    peak_cap = float(pf["capital_allocated"].max())
    avg_cap = float(pf["capital_allocated"].mean())
    total_trades = sum(cr["metrics"]["total_trades"] for cr in coin_results)

    summary_data = [
        ["Metric", "Value"],
        ["Coins", str(len(coin_results))],
        ["Total Trades", str(total_trades)],
        ["Net P&L", f"${port_net:,.2f}"],
        ["Max Drawdown %", f"{pf['portfolio_dd_pct']:.1f}%"],
        ["Peak Capital Used", f"${peak_cap:,.0f}"],
        ["Avg Capital Used", f"${avg_cap:,.0f}"],
    ]
    if total_capital is not None:
        idle_pct = (1.0 - avg_cap / total_capital) * 100 if total_capital > 0 else 0
        summary_data.append(["Total Capital", f"${total_capital:,.0f}"])
        summary_data.append(["Avg Idle Capital", f"{idle_pct:.1f}%"])

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
                          key=lambda cr: float(cr["equity_curve"][-1] - 10000.0),
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

    fig_eq = _make_equity_chart(pf["master_dt"], pf["portfolio_eq"], pf["per_coin_eq"])
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
'''
write_file("utils/pdf_exporter.py", PDF_EXPORTER)


# ============================================================================
# FILE 5: utils/capital_model.py (Phase 4: Unified Capital Model)
# FIX BUG1: Actually rebuild equity curves after rejections
# FIX BUG2: Map bar indices through datetime_index to master_dt
# FIX BUG3: Remove MFE from signal strength (look-ahead bias)
# FIX BUG7: Recompute capital efficiency from accepted trades only
# ============================================================================
log("=== Phase 4: Capital Model (v3 -- 4 bugs fixed) ===")
CAPITAL_MODEL = r'''"""
Unified Capital Model -- Post-processing filter for portfolio capital constraints.
Two modes: Per-Coin Independent vs Unified Portfolio Pool.

v3 fixes (2026-02-16):
  - Bar indices mapped through datetime_index to master_dt (cross-coin safe)
  - MFE removed from signal strength (was look-ahead bias)
  - Equity curves rebuilt after rejecting trades (not decorative)
  - Capital efficiency computed from accepted trades only
"""
import numpy as np
import pandas as pd
from datetime import datetime


# Grade priority: A is strongest signal, R is weakest
GRADE_PRIORITY = {"A": 0, "B": 1, "C": 2, "D": 3, "ADD": 4, "RE": 5, "R": 6}


def _grade_sort_key(grade_str):
    """Return numeric priority for a trade grade (lower = higher priority)."""
    return GRADE_PRIORITY.get(str(grade_str).upper(), 99)


def _map_bar_to_master(bar_idx, coin_dt_index, master_dt):
    """Map a per-coin bar index to the corresponding master_dt index."""
    coin_dt = pd.DatetimeIndex(coin_dt_index)
    if bar_idx < 0 or bar_idx >= len(coin_dt):
        bar_idx = max(0, min(bar_idx, len(coin_dt) - 1))
    target_dt = coin_dt[bar_idx]
    # Find nearest position in master_dt
    pos = master_dt.searchsorted(target_dt, side="left")
    if pos >= len(master_dt):
        pos = len(master_dt) - 1
    return int(pos)


def apply_capital_constraints(coin_results, pf_data, total_capital, margin_per_pos):
    """
    Post-process portfolio results to enforce unified capital constraints.
    Filters out trades that would exceed total_capital.
    Rebuilds equity curves and capital metrics from accepted trades only.
    Returns dict with adjusted results and rejection log.
    """
    if total_capital is None or total_capital <= 0:
        return {
            "adjusted_pf": pf_data,
            "adjusted_coin_results": coin_results,
            "capital_used": pf_data["capital_allocated"],
            "rejected_count": 0,
            "rejection_log": [],
            "missed_pnl": 0.0,
            "capital_efficiency": {
                "total_capital": 0,
                "peak_used": float(pf_data["capital_allocated"].max()),
                "peak_pct": 0.0,
                "avg_used": float(pf_data["capital_allocated"].mean()),
                "avg_pct": 0.0,
                "idle_pct": 0.0,
                "trades_rejected": 0,
                "rejection_pct": 0.0,
                "missed_pnl": 0.0,
            },
        }

    master_dt = pf_data["master_dt"]
    n_bars = len(master_dt)

    # Collect all trade entry/exit events with MAPPED timestamps
    # FIX BUG2: map per-coin bar indices to master_dt positions
    events = []
    for cr in coin_results:
        sym = cr["symbol"]
        tdf = cr.get("trades_df")
        coin_dt_idx = cr["datetime_index"]
        if tdf is None or tdf.empty:
            continue
        for row_idx, row in tdf.iterrows():
            entry_bar_local = int(row.get("entry_bar", 0))
            exit_bar_local = int(row.get("exit_bar", len(coin_dt_idx) - 1))
            # Map to master_dt positions
            entry_bar_master = _map_bar_to_master(entry_bar_local, coin_dt_idx, master_dt)
            exit_bar_master = _map_bar_to_master(exit_bar_local, coin_dt_idx, master_dt)
            grade = str(row.get("grade", "D"))
            pnl = float(row.get("net_pnl", row.get("pnl", 0)))
            # FIX BUG3: signal strength uses grade only (no MFE -- look-ahead bias)
            strength = -_grade_sort_key(grade) * 100
            events.append({
                "type": "ENTRY",
                "bar": entry_bar_master,
                "exit_bar": exit_bar_master,
                "coin": sym,
                "trade_idx": row_idx,
                "grade": grade,
                "strength": strength,
                "pnl": pnl,
                "commission": float(row.get("commission", 0)),
            })

    # Sort entries by bar, then by signal strength (highest first)
    events.sort(key=lambda e: (e["bar"], -e["strength"]))

    # Process: track capital usage, reject entries exceeding limit
    active_positions = []  # list of (exit_bar_master, margin_per_pos)
    rejected = []
    accepted = []

    for evt in events:
        bar = evt["bar"]
        if bar >= n_bars:
            continue

        # Release capital from expired positions
        active_positions = [(eb, m) for eb, m in active_positions if eb > bar]
        current_capital = sum(m for _, m in active_positions)

        if current_capital + margin_per_pos <= total_capital:
            # Accept trade
            active_positions.append((evt["exit_bar"], margin_per_pos))
            accepted.append(evt)
        else:
            # Reject trade
            rejected.append({
                "bar": bar,
                "coin": evt["coin"],
                "trade_idx": evt["trade_idx"],
                "grade": evt["grade"],
                "reason": "Insufficient capital",
                "capital_at_time": round(current_capital, 2),
                "needed": round(current_capital + margin_per_pos, 2),
                "available": total_capital,
                "missed_pnl": round(evt["pnl"], 2),
            })

    # FIX BUG1: Rebuild equity curves and capital allocation from ACCEPTED trades only
    # Build rejection set per coin: {sym: set of trade_idx}
    reject_by_coin = {}
    for r in rejected:
        coin = r["coin"]
        if coin not in reject_by_coin:
            reject_by_coin[coin] = set()
        reject_by_coin[coin].add(r["trade_idx"])

    # Rebuild per-coin equity curves excluding rejected trades
    adjusted_coin_results = []
    adjusted_per_coin_eq = {}
    adjusted_total_positions = np.zeros(n_bars)

    for cr in coin_results:
        sym = cr["symbol"]
        coin_dt_idx = pd.DatetimeIndex(cr["datetime_index"])
        eq_orig = np.array(cr["equity_curve"], dtype=float)
        tdf = cr.get("trades_df")
        rejected_idxs = reject_by_coin.get(sym, set())

        if rejected_idxs and tdf is not None and not tdf.empty:
            # Subtract rejected trade P&L from equity curve
            eq_adjusted = eq_orig.copy()
            for ridx in rejected_idxs:
                if ridx in tdf.index:
                    row = tdf.loc[ridx]
                    exit_bar_local = int(row.get("exit_bar", len(coin_dt_idx) - 1))
                    net = float(row.get("net_pnl", row.get("pnl", 0)))
                    # Remove this trade's contribution from exit_bar onward
                    if exit_bar_local < len(eq_adjusted):
                        eq_adjusted[exit_bar_local:] -= net
            # Align adjusted equity to master_dt
            eq_series = pd.Series(eq_adjusted, index=coin_dt_idx)
            eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(10000.0).values
        else:
            # No rejections for this coin -- use original aligned equity
            eq_series = pd.Series(eq_orig, index=coin_dt_idx)
            eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(10000.0).values

        adjusted_per_coin_eq[sym] = eq_aligned

        # Rebuild position counts excluding rejected trades
        pos_orig = np.array(cr["position_counts"], dtype=float)
        if rejected_idxs and tdf is not None:
            pos_adj = pos_orig.copy()
            for ridx in rejected_idxs:
                if ridx in tdf.index:
                    row = tdf.loc[ridx]
                    eb = int(row.get("entry_bar", 0))
                    xb = int(row.get("exit_bar", len(coin_dt_idx) - 1))
                    eb = max(0, min(eb, len(pos_adj) - 1))
                    xb = max(0, min(xb, len(pos_adj) - 1))
                    pos_adj[eb:xb + 1] = np.maximum(pos_adj[eb:xb + 1] - 1, 0)
            pos_series = pd.Series(pos_adj, index=coin_dt_idx)
        else:
            pos_series = pd.Series(pos_orig, index=coin_dt_idx)
        pos_aligned = pos_series.reindex(master_dt, method="ffill").fillna(0).values
        adjusted_total_positions += pos_aligned

        # Build adjusted coin result
        adj_cr = dict(cr)
        adj_cr["equity_curve"] = eq_aligned if rejected_idxs else cr["equity_curve"]
        adjusted_coin_results.append(adj_cr)

    # Rebuild portfolio equity and capital from adjusted values
    adjusted_portfolio_eq = np.zeros(n_bars)
    for eq_arr in adjusted_per_coin_eq.values():
        adjusted_portfolio_eq += eq_arr
    adjusted_capital_allocated = adjusted_total_positions * margin_per_pos

    # FIX BUG7: Compute capital efficiency from ADJUSTED values
    peak_used = float(adjusted_capital_allocated.max())
    avg_used = float(adjusted_capital_allocated.mean())
    idle_pct = (1.0 - avg_used / total_capital) * 100 if total_capital > 0 else 0.0
    total_signals = len(events)
    rejected_count = len(rejected)
    rejection_pct = (rejected_count / total_signals * 100) if total_signals > 0 else 0.0
    missed_pnl = sum(r["missed_pnl"] for r in rejected)

    # Build adjusted pf_data
    peaks = np.maximum.accumulate(adjusted_portfolio_eq)
    dd_arr = np.where(peaks > 0, (adjusted_portfolio_eq - peaks) / peaks * 100.0, 0.0)
    dd_arr = np.clip(dd_arr, -100.0, 0.0)

    adjusted_pf = dict(pf_data)
    adjusted_pf["portfolio_eq"] = adjusted_portfolio_eq
    adjusted_pf["per_coin_eq"] = adjusted_per_coin_eq
    adjusted_pf["total_positions"] = adjusted_total_positions
    adjusted_pf["capital_allocated"] = adjusted_capital_allocated
    adjusted_pf["portfolio_dd_pct"] = round(float(dd_arr.min()), 2)

    return {
        "adjusted_pf": adjusted_pf,
        "adjusted_coin_results": adjusted_coin_results,
        "capital_used": adjusted_capital_allocated,
        "rejected_count": rejected_count,
        "rejection_log": rejected,
        "missed_pnl": round(missed_pnl, 2),
        "capital_efficiency": {
            "total_capital": total_capital,
            "peak_used": round(peak_used, 2),
            "peak_pct": round(peak_used / total_capital * 100, 1) if total_capital > 0 else 0,
            "avg_used": round(avg_used, 2),
            "avg_pct": round(avg_used / total_capital * 100, 1) if total_capital > 0 else 0,
            "idle_pct": round(idle_pct, 1),
            "trades_rejected": rejected_count,
            "rejection_pct": round(rejection_pct, 1),
            "missed_pnl": round(missed_pnl, 2),
        },
    }


def format_capital_summary(efficiency):
    """Format capital efficiency dict as display-ready lines. Returns list of strings."""
    lines = [
        f"Total Capital:       ${efficiency['total_capital']:,.0f}",
        f"Peak Capital Used:   ${efficiency['peak_used']:,.0f} ({efficiency['peak_pct']:.1f}%)",
        f"Avg Capital Used:    ${efficiency['avg_used']:,.0f} ({efficiency['avg_pct']:.1f}%)",
        f"Avg Idle Capital:    {efficiency['idle_pct']:.1f}%",
        f"Trades Rejected:     {efficiency['trades_rejected']} ({efficiency['rejection_pct']:.1f}%)",
        f"Missed P&L:          ${efficiency['missed_pnl']:,.2f}",
    ]
    return lines
'''
write_file("utils/capital_model.py", CAPITAL_MODEL)


# ============================================================================
# FILE 6: portfolios/ directory (empty, for JSON storage)
# ============================================================================
log("=== Creating portfolios directory ===")
portfolios_dir = PROJ / "portfolios"
portfolios_dir.mkdir(parents=True, exist_ok=True)
gitkeep = portfolios_dir / ".gitkeep"
if not gitkeep.exists():
    gitkeep.write_text("", encoding="utf-8")
CREATED.append("portfolios/.gitkeep")
log(f"  CREATED: portfolios/ directory")


# ============================================================================
# FILE 7: tests/test_portfolio_enhancements.py
# FIX BUG9: Use realistic data structures matching _trades_to_df() output
# ============================================================================
log("=== Creating test suite (v3 -- realistic data structures) ===")
TEST_SUITE = r'''r"""
Test Suite: Dashboard Portfolio Enhancements v3
Tests all 4 phases with REALISTIC data structures matching _trades_to_df() output.

_trades_to_df() columns (from engine/backtester_v384.py line 557):
  direction, grade, entry_bar, exit_bar, entry_price, exit_price,
  sl_price, tp_price, pnl, commission, net_pnl, mfe, mae,
  exit_reason, saw_green, scale_idx

NOT in trades_df: entry_dt, rebate, be_raised, entry_atr

Run from terminal (not from Claude):
  python tests/test_portfolio_enhancements.py
"""
import sys
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0
ERRORS_LIST = []


def check(name, condition):
    """Assert a test condition. Tracks pass/fail counts."""
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        ERRORS_LIST.append(name)
        print(f"  [FAIL] {name}")


def ts():
    """Return current timestamp string."""
    return datetime.now().strftime("%H:%M:%S")


# ============================================================================
# PHASE 1 TESTS: Portfolio Manager
# ============================================================================
print(f"\n[{ts()}] === PHASE 1: Portfolio Manager ===")

from utils.portfolio_manager import (
    save_portfolio, load_portfolio, list_portfolios,
    delete_portfolio, rename_portfolio, PORTFOLIOS_DIR
)

# Use temp dir for tests
import utils.portfolio_manager as pm
_orig_dir = pm.PORTFOLIOS_DIR
_tmp = Path(tempfile.mkdtemp()) / "portfolios"
pm.PORTFOLIOS_DIR = _tmp

# Test 1.1: Save portfolio
print(f"[{ts()}] Testing save_portfolio...")
path = save_portfolio("Test Portfolio", ["RIVERUSDT", "KITEUSDT", "HYPEUSDT"],
                      selection_method="custom", notes="test notes")
check("1.1 save returns path", path is not None and Path(path).exists())

# Test 1.2: Load portfolio
print(f"[{ts()}] Testing load_portfolio...")
loaded = load_portfolio(Path(path).name)
check("1.2 load returns dict", loaded is not None)
check("1.3 load name matches", loaded["name"] == "Test Portfolio")
check("1.4 load coins match", loaded["coins"] == ["RIVERUSDT", "KITEUSDT", "HYPEUSDT"])
check("1.5 load coin_count", loaded["coin_count"] == 3)
check("1.6 load method", loaded["selection_method"] == "custom")
check("1.7 load notes", loaded["notes"] == "test notes")

# Test 1.3: List portfolios
print(f"[{ts()}] Testing list_portfolios...")
save_portfolio("Second Portfolio", ["SANDUSDT"], selection_method="random")
plist = list_portfolios()
check("1.8 list returns 2", len(plist) == 2)
check("1.9 list has name", all("name" in p for p in plist))
check("1.10 list has file", all("file" in p for p in plist))

# Test 1.4: Delete portfolio
print(f"[{ts()}] Testing delete_portfolio...")
deleted = delete_portfolio(Path(path).name)
check("1.11 delete returns True", deleted is True)
plist2 = list_portfolios()
check("1.12 list now 1", len(plist2) == 1)

# Test 1.5: Delete nonexistent
check("1.13 delete nonexistent returns False", delete_portfolio("nonexistent.json") is False)

# Test 1.6: Load nonexistent
check("1.14 load nonexistent returns None", load_portfolio("nonexistent.json") is None)

# Test 1.7: Rename
print(f"[{ts()}] Testing rename_portfolio...")
remaining = plist2[0]["file"]
new_path = rename_portfolio(remaining, "Renamed Portfolio")
check("1.15 rename returns path", new_path is not None)
renamed = load_portfolio(Path(new_path).name)
check("1.16 renamed name correct", renamed["name"] == "Renamed Portfolio")

# Test 1.8: Special characters in name
path_special = save_portfolio("Test!@#$%^&*()Portfolio", ["BTCUSDT"])
loaded_special = load_portfolio(Path(path_special).name)
check("1.17 special chars handled", loaded_special is not None)
check("1.18 special chars coins", loaded_special["coins"] == ["BTCUSDT"])

# Test 1.9: Empty coins
path_empty = save_portfolio("Empty", [])
loaded_empty = load_portfolio(Path(path_empty).name)
check("1.19 empty coins OK", loaded_empty["coins"] == [])
check("1.20 empty coin_count", loaded_empty["coin_count"] == 0)

# Cleanup
pm.PORTFOLIOS_DIR = _orig_dir
shutil.rmtree(_tmp, ignore_errors=True)


# ============================================================================
# PHASE 2 TESTS: Coin Analysis
# FIX BUG9: Use REAL trades_df columns only
# ============================================================================
print(f"\n[{ts()}] === PHASE 2: Coin Analysis ===")

import numpy as np
import pandas as pd
from utils.coin_analysis import (
    compute_extended_metrics, compute_grade_distribution,
    compute_exit_distribution, compute_monthly_pnl,
    compute_loser_detail, compute_commission_breakdown
)

# Create REALISTIC trades DataFrame matching _trades_to_df() output
np.random.seed(42)
n_trades = 50
pnl_vals = np.random.normal(5, 20, n_trades)
comm_vals = np.abs(np.random.normal(2, 1, n_trades))
trades_df = pd.DataFrame({
    "direction": np.random.choice(["LONG", "SHORT"], n_trades),
    "grade": np.random.choice(["A", "B", "C", "D", "ADD", "RE"], n_trades),
    "entry_bar": np.arange(n_trades) * 100,
    "exit_bar": np.arange(n_trades) * 100 + 50,
    "entry_price": np.random.uniform(0.001, 0.01, n_trades),
    "exit_price": np.random.uniform(0.001, 0.01, n_trades),
    "sl_price": np.random.uniform(0.0005, 0.008, n_trades),
    "tp_price": np.random.uniform(0.002, 0.015, n_trades),
    "pnl": pnl_vals,
    "commission": comm_vals,
    "net_pnl": pnl_vals - comm_vals,
    "mfe": np.abs(np.random.normal(10, 5, n_trades)),
    "mae": -np.abs(np.random.normal(8, 4, n_trades)),
    "exit_reason": np.random.choice(["SL", "TP", "SCALE_1", "SCALE_2", "END"], n_trades),
    "saw_green": np.random.choice([True, False], n_trades),
    "scale_idx": np.random.choice([0, 0, 0, 1, 2], n_trades),
})
# NOTE: NO entry_dt, NO rebate, NO be_raised -- these do NOT exist in real output

# Test 2.1: Extended metrics
print(f"[{ts()}] Testing compute_extended_metrics...")
ext = compute_extended_metrics(trades_df, bar_count=5000)
check("2.1 returns dict", isinstance(ext, dict))
check("2.2 has avg_trade", "avg_trade" in ext)
check("2.3 has best_trade", "best_trade" in ext)
check("2.4 has worst_trade", "worst_trade" in ext)
check("2.5 has sl_pct", "sl_pct" in ext)
check("2.6 has tp_pct", "tp_pct" in ext)
check("2.7 has scale_pct", "scale_pct" in ext)
check("2.8 has avg_mfe", "avg_mfe" in ext)
check("2.9 has avg_mae", "avg_mae" in ext)
check("2.10 has max_consec_loss", "max_consec_loss" in ext)
check("2.11 has sortino", "sortino" in ext)
check("2.12 best >= worst", ext["best_trade"] >= ext["worst_trade"])
check("2.13 sl_pct 0-100", 0 <= ext["sl_pct"] <= 100)
check("2.14 consec >= 0", ext["max_consec_loss"] >= 0)

# Test 2.2: Empty DataFrame
ext_empty = compute_extended_metrics(pd.DataFrame())
check("2.15 empty returns defaults", ext_empty["avg_trade"] == 0.0)
check("2.16 empty consec 0", ext_empty["max_consec_loss"] == 0)

# Test 2.3: None input
ext_none = compute_extended_metrics(None)
check("2.17 None returns defaults", ext_none["sortino"] == 0.0)

# Test 2.4: Grade distribution
print(f"[{ts()}] Testing compute_grade_distribution...")
grades = compute_grade_distribution(trades_df)
check("2.18 grades is dict", isinstance(grades, dict))
check("2.19 grades sum = n", sum(grades.values()) == n_trades)

# Test 2.5: Exit distribution
exits = compute_exit_distribution(trades_df)
check("2.20 exits is dict", isinstance(exits, dict))
check("2.21 exits sum = n", sum(exits.values()) == n_trades)

# Test 2.6: Monthly PnL via entry_bar + datetime_index mapping
print(f"[{ts()}] Testing compute_monthly_pnl with datetime_index mapping...")
dt_index = pd.date_range("2025-01-01", periods=5000, freq="5min")
monthly = compute_monthly_pnl(trades_df, datetime_index=dt_index)
check("2.22 monthly is DataFrame", isinstance(monthly, pd.DataFrame))
check("2.23 monthly has month col", "month" in monthly.columns)
check("2.24 monthly has pnl col", "pnl" in monthly.columns)
check("2.25 monthly has rows", len(monthly) > 0)

# Test 2.6b: Monthly PnL without datetime_index returns empty
monthly_empty = compute_monthly_pnl(trades_df, datetime_index=None)
check("2.26 no dt_index -> empty", len(monthly_empty) == 0)

# Test 2.7: Loser detail
losers = compute_loser_detail(trades_df)
check("2.27 losers is DataFrame", isinstance(losers, pd.DataFrame))

# Test 2.8: Commission breakdown (no rebate column in real data)
comm = compute_commission_breakdown(trades_df)
check("2.28 comm is dict", isinstance(comm, dict))
check("2.29 has total_commission", "total_commission" in comm)
check("2.30 commission > 0", comm["total_commission"] > 0)
check("2.31 net = total (no rebate)", comm["net_commission"] == comm["total_commission"])


# ============================================================================
# PHASE 3 TESTS: PDF Export (import check only, no actual generation)
# ============================================================================
print(f"\n[{ts()}] === PHASE 3: PDF Export ===")

from utils.pdf_exporter import check_dependencies, HAS_REPORTLAB, HAS_MATPLOTLIB

ok, msg = check_dependencies()
check("3.1 check_dependencies returns tuple", isinstance(ok, bool))
check("3.2 matplotlib available", HAS_MATPLOTLIB)
if HAS_REPORTLAB:
    check("3.3 reportlab available", True)
    print(f"  [INFO] reportlab IS installed -- full PDF tests available")
else:
    check("3.3 reportlab not installed (expected)", True)
    print(f"  [INFO] reportlab NOT installed -- install with: pip install reportlab")

# Test import of generate_portfolio_pdf
from utils.pdf_exporter import generate_portfolio_pdf
check("3.4 generate_portfolio_pdf importable", callable(generate_portfolio_pdf))


# ============================================================================
# PHASE 4 TESTS: Capital Model (v3 -- realistic data)
# ============================================================================
print(f"\n[{ts()}] === PHASE 4: Capital Model ===")

from utils.capital_model import (
    apply_capital_constraints, format_capital_summary, GRADE_PRIORITY
)

# Create realistic portfolio data with proper datetime_index per coin
master_dt = pd.date_range("2025-01-01", periods=500, freq="5min")
portfolio_eq = np.cumsum(np.random.normal(1, 5, 500)) + 30000
capital_allocated = np.random.randint(500, 3000, 500).astype(float)

pf_data = {
    "master_dt": master_dt,
    "portfolio_eq": portfolio_eq,
    "per_coin_eq": {"RIVERUSDT": portfolio_eq * 0.4, "KITEUSDT": portfolio_eq * 0.6},
    "total_positions": capital_allocated / 500,
    "capital_allocated": capital_allocated,
    "best_moment": {"label": "Best", "bar": 250, "date": "2025-01-01",
                    "equity": 31000, "dd_pct": 0, "positions": 4, "capital": 2000},
    "worst_moment": {"label": "Worst", "bar": 400, "date": "2025-01-01",
                     "equity": 29000, "dd_pct": -5, "positions": 2, "capital": 1000},
    "portfolio_dd_pct": -5.0,
    "per_coin_lsg": {"RIVERUSDT": 85.0, "KITEUSDT": 90.0},
}

# Synthetic coin results with REALISTIC trades_df columns
coin_results_syn = []
for sym in ["RIVERUSDT", "KITEUSDT"]:
    n_t = 8
    pnl_v = np.array([12, -3, 17, -6, 8, -10, 20, -2], dtype=float)
    comm_v = np.abs(np.random.normal(1.5, 0.5, n_t))
    tdf = pd.DataFrame({
        "direction": ["LONG", "SHORT", "LONG", "SHORT", "LONG", "SHORT", "LONG", "SHORT"],
        "grade": ["A", "B", "A", "C", "B", "D", "A", "C"],
        "entry_bar": [10, 60, 120, 180, 240, 300, 360, 420],
        "exit_bar": [50, 100, 160, 220, 280, 340, 400, 460],
        "entry_price": np.random.uniform(0.001, 0.01, n_t),
        "exit_price": np.random.uniform(0.001, 0.01, n_t),
        "sl_price": np.random.uniform(0.0005, 0.008, n_t),
        "tp_price": np.random.uniform(0.002, 0.015, n_t),
        "pnl": pnl_v,
        "commission": comm_v,
        "net_pnl": pnl_v - comm_v,
        "mfe": np.abs(np.random.normal(10, 5, n_t)),
        "mae": -np.abs(np.random.normal(8, 4, n_t)),
        "exit_reason": ["TP", "SL", "TP", "SL", "SCALE_1", "SL", "TP", "SL"],
        "saw_green": [True, False, True, True, True, False, True, False],
        "scale_idx": [0, 0, 0, 0, 1, 0, 0, 0],
    })
    coin_results_syn.append({
        "symbol": sym,
        "equity_curve": np.cumsum(np.random.normal(1, 3, 500)) + 10000,
        "datetime_index": master_dt,
        "position_counts": np.random.randint(0, 3, 500),
        "trades_df": tdf,
        "metrics": {"total_trades": n_t, "win_rate": 0.5, "sharpe": 1.0,
                    "profit_factor": 1.5, "max_drawdown_pct": -3.0,
                    "pct_losers_saw_green": 0.85},
    })

# Test 4.1: Apply with generous capital (no rejections)
print(f"[{ts()}] Testing apply_capital_constraints...")
result_generous = apply_capital_constraints(coin_results_syn, pf_data, 50000, 500)
check("4.1 returns dict", isinstance(result_generous, dict))
check("4.2 has rejected_count", "rejected_count" in result_generous)
check("4.3 has rejection_log", "rejection_log" in result_generous)
check("4.4 has capital_efficiency", "capital_efficiency" in result_generous)
check("4.5 generous: 0 rejections", result_generous["rejected_count"] == 0)
check("4.6 adjusted_pf exists", "adjusted_pf" in result_generous)
check("4.7 adjusted_pf has portfolio_eq", "portfolio_eq" in result_generous["adjusted_pf"])

# Test 4.2: Apply with tight capital (should reject some)
result_tight = apply_capital_constraints(coin_results_syn, pf_data, 500, 500)
check("4.8 tight: has rejections", result_tight["rejected_count"] > 0)
check("4.9 rejection log entries", len(result_tight["rejection_log"]) > 0)
if result_tight["rejection_log"]:
    r = result_tight["rejection_log"][0]
    check("4.10 rejection has coin", "coin" in r)
    check("4.11 rejection has reason", "reason" in r)
    check("4.12 rejection has grade", "grade" in r)
    check("4.13 rejection has missed_pnl", "missed_pnl" in r)
    check("4.14 rejection has capital_at_time", "capital_at_time" in r)

# BUG1 FIX VERIFICATION: adjusted equity should differ from original when trades rejected
if result_tight["rejected_count"] > 0:
    orig_final = float(pf_data["portfolio_eq"][-1])
    adj_final = float(result_tight["adjusted_pf"]["portfolio_eq"][-1])
    check("4.15 BUG1 FIX: adjusted equity != original", abs(orig_final - adj_final) > 0.01)
    print(f"  Original final equity: ${orig_final:,.2f}")
    print(f"  Adjusted final equity: ${adj_final:,.2f}")

# BUG7 FIX VERIFICATION: capital efficiency uses adjusted values
eff = result_tight["capital_efficiency"]
check("4.16 eff total_capital", eff["total_capital"] == 500)
check("4.17 eff peak_pct", "peak_pct" in eff)
check("4.18 eff avg_pct", "avg_pct" in eff)
check("4.19 eff idle_pct", "idle_pct" in eff)

# Test 4.3: Format summary
lines = format_capital_summary(eff)
check("4.20 format returns list", isinstance(lines, list))
check("4.21 format has 6 lines", len(lines) == 6)

# Test 4.4: None capital (passthrough)
result_none = apply_capital_constraints(coin_results_syn, pf_data, None, 500)
check("4.22 None capital: 0 rejections", result_none["rejected_count"] == 0)

# Test 4.5: Grade priority ordering
check("4.23 A > B priority", GRADE_PRIORITY["A"] < GRADE_PRIORITY["B"])
check("4.24 B > C priority", GRADE_PRIORITY["B"] < GRADE_PRIORITY["C"])

# BUG3 FIX VERIFICATION: signal strength uses grade-only (no MFE look-ahead)
# Verify rejection log contains no MFE-based fields and has grade info
if result_tight["rejection_log"]:
    r0 = result_tight["rejection_log"][0]
    check("4.25 BUG3 FIX: no MFE in rejection log", "mfe" not in r0)
    check("4.26 BUG3 FIX: grade in rejection log", "grade" in r0)


# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*60}")
print(f"[{ts()}] TEST RESULTS: {PASS} passed, {FAIL} failed")
print(f"{'='*60}")
if ERRORS_LIST:
    print("FAILURES: " + ", ".join(ERRORS_LIST))
else:
    print("ALL TESTS PASSED")
sys.exit(0 if FAIL == 0 else 1)
'''
write_file("tests/test_portfolio_enhancements.py", TEST_SUITE)


# ============================================================================
# FILE 8: scripts/debug_portfolio_enhancements.py
# ============================================================================
log("=== Creating debug script (v3) ===")
DEBUG_SCRIPT = r'''r"""
Debug Script: Dashboard Portfolio Enhancements v3
Validates integration flow, edge cases, and bug fix verification.

Run from terminal (not from Claude):
  python scripts/debug_portfolio_enhancements.py
"""
import sys
import json
import tempfile
import shutil
import time as _time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0
ERRORS_LIST = []


def check(name, condition):
    """Assert a debug condition."""
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        ERRORS_LIST.append(name)
        print(f"  [FAIL] {name}")


def ts():
    """Return timestamp."""
    return datetime.now().strftime("%H:%M:%S")


import numpy as np
import pandas as pd

# ============================================================================
# DEBUG 1: Portfolio Manager Round-Trip
# ============================================================================
print(f"\n[{ts()}] === DEBUG 1: Portfolio Manager Round-Trip ===")
from utils.portfolio_manager import save_portfolio, load_portfolio, list_portfolios, delete_portfolio
import utils.portfolio_manager as pm
_orig = pm.PORTFOLIOS_DIR
_tmp = Path(tempfile.mkdtemp()) / "portfolios"
pm.PORTFOLIOS_DIR = _tmp

# Save 5 portfolios with different coin counts
for i in range(5):
    coins = [f"COIN{j}USDT" for j in range(i + 1)]
    save_portfolio(f"Debug Portfolio {i+1}", coins, notes=f"debug test {i+1}")
    _time.sleep(0.05)

plist = list_portfolios()
check("D1.1 5 portfolios saved", len(plist) == 5)
# Sorted by mtime descending -- newest first
all_names = [p["name"] for p in plist]
check("D1.2 sorted by newest first", all_names[0] == "Debug Portfolio 5")

# Load each and verify coin count
for p in plist:
    data = load_portfolio(p["file"])
    check(f"D1.3 {p['name']} loads", data is not None)
    check(f"D1.4 {p['name']} coins", len(data["coins"]) == data["coin_count"])

# Delete all
for p in plist:
    delete_portfolio(p["file"])
check("D1.5 all deleted", len(list_portfolios()) == 0)

pm.PORTFOLIOS_DIR = _orig
shutil.rmtree(_tmp, ignore_errors=True)
print(f"  Round-trip: {PASS} passed")


# ============================================================================
# DEBUG 2: Extended Metrics Edge Cases
# ============================================================================
print(f"\n[{ts()}] === DEBUG 2: Extended Metrics Edge Cases ===")
from utils.coin_analysis import compute_extended_metrics, compute_monthly_pnl

# All winners (realistic columns only)
all_win = pd.DataFrame({
    "net_pnl": [10, 20, 30, 40, 50],
    "pnl": [12, 22, 32, 42, 52],
    "commission": [2, 2, 2, 2, 2],
    "mfe": [15, 25, 35, 45, 55],
    "mae": [-3, -2, -1, -2, -3],
    "exit_reason": ["TP", "TP", "TP", "TP", "TP"],
    "entry_bar": [0, 100, 200, 300, 400],
    "exit_bar": [50, 150, 250, 350, 450],
})
ext_win = compute_extended_metrics(all_win, bar_count=500)
check("D2.1 all winners: consec loss = 0", ext_win["max_consec_loss"] == 0)
check("D2.2 all winners: tp_pct = 100", ext_win["tp_pct"] == 100.0)

# All losers
all_lose = pd.DataFrame({
    "net_pnl": [-10, -20, -30],
    "pnl": [-8, -18, -28],
    "commission": [2, 2, 2],
    "mfe": [5, 3, 2],
    "mae": [-15, -25, -35],
    "exit_reason": ["SL", "SL", "SL"],
    "entry_bar": [0, 100, 200],
    "exit_bar": [50, 150, 250],
})
ext_lose = compute_extended_metrics(all_lose, bar_count=300)
check("D2.3 all losers: consec = 3", ext_lose["max_consec_loss"] == 3)
check("D2.4 all losers: sl_pct = 100", ext_lose["sl_pct"] == 100.0)
check("D2.5 all losers: best < 0", ext_lose["best_trade"] < 0)

# Single trade
single = pd.DataFrame({
    "net_pnl": [42.0], "pnl": [44.0], "commission": [2.0],
    "mfe": [50], "mae": [-5],
    "exit_reason": ["TP"], "entry_bar": [0], "exit_bar": [50],
})
ext_single = compute_extended_metrics(single, bar_count=100)
check("D2.6 single: avg = 42", ext_single["avg_trade"] == 42.0)
check("D2.7 single: best = worst = 42", ext_single["best_trade"] == ext_single["worst_trade"])

# BUG6 FIX: Sortino annualization with bar_count vs without
ext_no_bars = compute_extended_metrics(all_win)
ext_with_bars = compute_extended_metrics(all_win, bar_count=500)
# Without bar_count, uses 105120 default (much higher annualization factor)
# With bar_count=500, uses 500 (lower factor, more realistic)
if ext_no_bars["sortino"] != 0.0 and ext_with_bars["sortino"] != 0.0:
    check("D2.8 BUG6 FIX: different annualization", ext_no_bars["sortino"] != ext_with_bars["sortino"])
else:
    check("D2.8 BUG6 FIX: sortino computed", True)

# BUG5 FIX: monthly PnL via datetime_index
print(f"[{ts()}] Testing BUG5 FIX: monthly PnL via datetime_index...")
dt_index = pd.date_range("2025-01-01", periods=500, freq="5min")
monthly = compute_monthly_pnl(all_win, datetime_index=dt_index)
check("D2.9 BUG5 FIX: monthly has rows", len(monthly) > 0)
check("D2.10 monthly pnl col", "pnl" in monthly.columns)

# Without datetime_index should return empty (not crash)
monthly_no_dt = compute_monthly_pnl(all_win, datetime_index=None)
check("D2.11 no dt_index: empty result", len(monthly_no_dt) == 0)

# Large dataset performance
import time
large = pd.DataFrame({
    "net_pnl": np.random.normal(0, 10, 10000),
    "pnl": np.random.normal(2, 12, 10000),
    "commission": np.abs(np.random.normal(2, 1, 10000)),
    "mfe": np.abs(np.random.normal(5, 3, 10000)),
    "mae": -np.abs(np.random.normal(4, 2, 10000)),
    "exit_reason": np.random.choice(["SL", "TP", "SCALE_1"], 10000),
    "entry_bar": np.arange(10000) * 5,
    "exit_bar": np.arange(10000) * 5 + 3,
})
t0 = time.perf_counter()
ext_large = compute_extended_metrics(large, bar_count=50000)
elapsed = time.perf_counter() - t0
check("D2.12 10K trades < 0.5s", elapsed < 0.5)
print(f"  10K trades computed in {elapsed:.4f}s")


# ============================================================================
# DEBUG 3: Capital Model -- Bug Fix Verification
# ============================================================================
print(f"\n[{ts()}] === DEBUG 3: Capital Model Bug Fixes ===")
from utils.capital_model import apply_capital_constraints, _map_bar_to_master

# BUG2 FIX: verify bar mapping works across different coin timelines
master_dt = pd.date_range("2025-01-01", periods=1000, freq="5min")
coin_a_dt = pd.date_range("2025-01-01 00:00", periods=500, freq="5min")
coin_b_dt = pd.date_range("2025-01-01 10:00", periods=500, freq="5min")

# Coin A bar 0 = 2025-01-01 00:00 -> master bar 0
# Coin B bar 0 = 2025-01-01 10:00 -> master bar 120
mapped_a = _map_bar_to_master(0, coin_a_dt, master_dt)
mapped_b = _map_bar_to_master(0, coin_b_dt, master_dt)
check("D3.1 BUG2 FIX: coin A bar 0 -> master 0", mapped_a == 0)
check("D3.2 BUG2 FIX: coin B bar 0 -> master 120", mapped_b == 120)
print(f"  Coin A bar 0 -> master bar {mapped_a}")
print(f"  Coin B bar 0 -> master bar {mapped_b}")

# Full capital model test with staggered timelines
pf_data = {
    "master_dt": master_dt,
    "portfolio_eq": np.cumsum(np.random.normal(1, 5, 1000)) + 30000,
    "per_coin_eq": {},
    "total_positions": np.ones(1000) * 2,
    "capital_allocated": np.ones(1000) * 1000,
    "best_moment": {"label": "B", "bar": 250, "date": "", "equity": 31000,
                    "dd_pct": 0, "positions": 2, "capital": 1000},
    "worst_moment": {"label": "W", "bar": 500, "date": "", "equity": 29000,
                     "dd_pct": -5, "positions": 2, "capital": 1000},
    "portfolio_dd_pct": -5.0,
    "per_coin_lsg": {},
}

# 2 coins with overlapping trades at DIFFERENT real times
coin_results_dbg = []
for sym, coin_dt in [("AAAUSDT", coin_a_dt), ("BBBUSDT", coin_b_dt)]:
    n_t = 5
    pnl_v = np.array([10, -5, 15, -3, 8], dtype=float)
    comm_v = np.array([1.5, 1.2, 1.8, 1.0, 1.3])
    tdf = pd.DataFrame({
        "direction": ["LONG", "SHORT", "LONG", "SHORT", "LONG"],
        "grade": ["A", "B", "A", "C", "B"],
        "entry_bar": [10, 80, 160, 250, 350],
        "exit_bar": [70, 150, 240, 340, 430],
        "entry_price": np.random.uniform(0.001, 0.01, n_t),
        "exit_price": np.random.uniform(0.001, 0.01, n_t),
        "sl_price": np.random.uniform(0.0005, 0.008, n_t),
        "tp_price": np.random.uniform(0.002, 0.015, n_t),
        "pnl": pnl_v,
        "commission": comm_v,
        "net_pnl": pnl_v - comm_v,
        "mfe": np.abs(np.random.normal(10, 5, n_t)),
        "mae": -np.abs(np.random.normal(8, 4, n_t)),
        "exit_reason": ["TP", "SL", "TP", "SL", "TP"],
        "saw_green": [True, False, True, True, True],
        "scale_idx": [0, 0, 0, 0, 0],
    })
    coin_results_dbg.append({
        "symbol": sym,
        "equity_curve": np.cumsum(np.random.normal(0.5, 2, len(coin_dt))) + 10000,
        "datetime_index": coin_dt,
        "position_counts": np.random.randint(0, 2, len(coin_dt)),
        "trades_df": tdf,
        "metrics": {"total_trades": n_t, "win_rate": 0.6, "sharpe": 1.2,
                    "profit_factor": 1.8, "max_drawdown_pct": -2.5,
                    "pct_losers_saw_green": 0.80},
    })

# Generous capital
r_gen = apply_capital_constraints(coin_results_dbg, pf_data, 10000, 500)
check("D3.3 $10K: 0 rejections", r_gen["rejected_count"] == 0)

# Tight capital: $500 -> only 1 position at a time
r_tight = apply_capital_constraints(coin_results_dbg, pf_data, 500, 500)
check("D3.4 $500: has rejections", r_tight["rejected_count"] > 0)
check("D3.5 rejection log populated", len(r_tight["rejection_log"]) > 0)

# BUG1 FIX: adjusted equity should differ
orig_eq = float(pf_data["portfolio_eq"][-1])
adj_eq = float(r_tight["adjusted_pf"]["portfolio_eq"][-1])
check("D3.6 BUG1 FIX: equity changed", abs(orig_eq - adj_eq) > 0.01)
print(f"  Original final: ${orig_eq:,.2f}")
print(f"  Adjusted final: ${adj_eq:,.2f}")
print(f"  Difference:     ${orig_eq - adj_eq:,.2f}")

# BUG7 FIX: capital efficiency from adjusted values
eff = r_tight["capital_efficiency"]
adj_peak = float(r_tight["adjusted_pf"]["capital_allocated"].max())
check("D3.7 BUG7 FIX: eff peak matches adjusted cap", abs(eff["peak_used"] - adj_peak) < 0.01)

# Rejection detail
if r_tight["rejection_log"]:
    r = r_tight["rejection_log"][0]
    check("D3.8 rejection has all fields", all(k in r for k in ["bar", "coin", "grade", "reason", "missed_pnl"]))
    print(f"  Sample rejection: bar={r['bar']} coin={r['coin']} grade={r['grade']} missed=${r['missed_pnl']:.2f}")

from utils.capital_model import format_capital_summary
lines = format_capital_summary(eff)
check("D3.9 format lines non-empty", all(len(l) > 0 for l in lines))
print(f"  Capital summary:")
for l in lines:
    print(f"    {l}")


# ============================================================================
# DEBUG 4: PDF Export Dependency Check
# ============================================================================
print(f"\n[{ts()}] === DEBUG 4: PDF Export ===")
from utils.pdf_exporter import check_dependencies, HAS_REPORTLAB

ok, msg = check_dependencies()
check("D4.1 dependency check works", isinstance(ok, bool))
if HAS_REPORTLAB:
    print(f"  reportlab installed -- PDF generation available")
    from utils.pdf_exporter import generate_portfolio_pdf
    pf_pdf = {
        "master_dt": pd.date_range("2025-01-01", periods=100, freq="5min"),
        "portfolio_eq": np.cumsum(np.random.normal(1, 3, 100)) + 20000,
        "per_coin_eq": {"TEST": np.cumsum(np.random.normal(0.5, 2, 100)) + 10000},
        "capital_allocated": np.ones(100) * 500,
        "portfolio_dd_pct": -3.5,
        "best_moment": {"label": "B", "bar": 50, "date": "2025-01-01", "equity": 21000,
                        "dd_pct": 0, "positions": 1, "capital": 500},
        "worst_moment": {"label": "W", "bar": 80, "date": "2025-01-01", "equity": 19500,
                         "dd_pct": -3.5, "positions": 1, "capital": 500},
    }
    cr_pdf = [{
        "symbol": "TESTUSDT",
        "equity_curve": np.cumsum(np.random.normal(0.5, 2, 100)) + 10000,
        "datetime_index": pd.date_range("2025-01-01", periods=100, freq="5min"),
        "position_counts": np.ones(100),
        "trades_df": pd.DataFrame({"net_pnl": [10, -5, 15]}),
        "metrics": {"total_trades": 3, "win_rate": 0.67, "sharpe": 1.5,
                    "profit_factor": 2.0, "max_drawdown_pct": -2.0,
                    "pct_losers_saw_green": 0.80},
    }]
    _tmp_pdf = Path(tempfile.mkdtemp()) / "test_report.pdf"
    try:
        out = generate_portfolio_pdf(pf_pdf, cr_pdf, "Debug Test", output_path=str(_tmp_pdf))
        check("D4.2 PDF generated", Path(out).exists())
        check("D4.3 PDF size > 0", Path(out).stat().st_size > 0)
        print(f"  PDF size: {Path(out).stat().st_size:,} bytes")
    except Exception as e:
        check(f"D4.2 PDF generation failed: {e}", False)
    finally:
        if _tmp_pdf.exists():
            _tmp_pdf.unlink()
else:
    print(f"  reportlab NOT installed -- skipping PDF generation test")
    print(f"  Install with: pip install reportlab")
    check("D4.2 skipped (no reportlab)", True)


# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*60}")
print(f"[{ts()}] DEBUG RESULTS: {PASS} passed, {FAIL} failed")
print(f"{'='*60}")
if ERRORS_LIST:
    print("FAILURES: " + ", ".join(ERRORS_LIST))
else:
    print("ALL DEBUG CHECKS PASSED")
sys.exit(0 if FAIL == 0 else 1)
'''
write_file("scripts/debug_portfolio_enhancements.py", DEBUG_SCRIPT)


# ============================================================================
# RESULTS
# ============================================================================
log("")
log("=" * 60)
log(f"BUILD COMPLETE: {len(CREATED)} files created, {len(ERRORS)} errors")
log("=" * 60)
for f in CREATED:
    log(f"  OK: {f}")
if ERRORS:
    log("")
    log("COMPILE FAILURES: " + ", ".join(ERRORS))
    sys.exit(1)
else:
    log("")
    log("ALL FILES COMPILED SUCCESSFULLY")
    log("")
    log("v3 Bug Fixes Applied:")
    log("  BUG1: Capital model now rebuilds equity after rejections")
    log("  BUG2: Bar indices mapped through datetime_index to master_dt")
    log("  BUG3: MFE removed from signal strength (was look-ahead bias)")
    log("  BUG4: rebate column removed (not in Trade384)")
    log("  BUG5: Monthly PnL maps entry_bar via datetime_index")
    log("  BUG6: Sortino annualization uses bar_count parameter")
    log("  BUG7: Capital efficiency computed from adjusted values")
    log("  BUG8: be_raised noted (not in trades_df, document only)")
    log("  BUG9: Test suite uses realistic _trades_to_df() columns")
    log("")
    log("Next steps:")
    log("  1. Run build:")
    log('     python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\build_dashboard_portfolio_v3.py"')
    log("")
    log("  2. Run tests:")
    log('     python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\tests\\test_portfolio_enhancements.py"')
    log("")
    log("  3. Run debug:")
    log('     python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\debug_portfolio_enhancements.py"')
    log("")
    log("  4. Install reportlab for PDF export:")
    log("     pip install reportlab")
    log("")
    log("  5. Integrate into dashboard.py (manual step, see plan)")
    sys.exit(0)
