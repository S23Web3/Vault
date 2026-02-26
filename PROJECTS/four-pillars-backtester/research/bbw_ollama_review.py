
"""Layer 6: Ollama LLM review of BBW simulator outputs.

Reads report CSVs from Layer 5 and sends to Ollama for analysis.
Output: .md files in reports/bbw/ollama/.

All functions return strings. ollama_chat NEVER raises.
Imported by: scripts/run_bbw_simulator.py
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

log = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:8b"
OFFLINE_PREFIX = "OLLAMA_OFFLINE: "

AVAILABLE_MODELS = [
    "qwen3:8b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    "qwen3-coder:30b",
    "gpt-oss:20b",
]


def ollama_chat(prompt, model=DEFAULT_MODEL, temperature=0.3, timeout=120):
    """Send prompt to Ollama; return response string or OLLAMA_OFFLINE on error.

    Never raises -- all errors return OFFLINE_PREFIX + description.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False,
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except requests.exceptions.ConnectionError:
        return OFFLINE_PREFIX + "Cannot connect to Ollama at " + OLLAMA_URL
    except requests.exceptions.Timeout:
        return OFFLINE_PREFIX + "Request timed out after " + str(timeout) + "s"
    except json.JSONDecodeError as e:
        return OFFLINE_PREFIX + "JSONDecodeError: " + str(e)
    except Exception as e:
        return OFFLINE_PREFIX + str(e)


def _read_csv_sample(csv_path, max_rows=20):
    """Read CSV file and return string table; return empty string on any error."""
    import pandas as pd
    path = Path(csv_path)
    if not path.exists():
        log.warning("CSV not found: %s", path)
        return ""
    try:
        df = pd.read_csv(path)
        if df.empty:
            log.warning("CSV empty: %s", path)
            return ""
        return df.head(max_rows).to_string(index=False)
    except Exception as e:
        log.warning("Failed to read CSV %s: %s", path, e)
        return ""


def analyze_state_stats(state_stats_csv, mc_summary_csv, model=DEFAULT_MODEL):
    """Analyze BBW state statistics CSVs using Ollama; return markdown string."""
    state_text = _read_csv_sample(state_stats_csv)
    mc_text = _read_csv_sample(mc_summary_csv)
    if not state_text and not mc_text:
        return "## State Analysis\n\nNo CSV data available."
    context = (
        "SYSTEM CONTEXT (read carefully before analysing):\n"
        "You are reviewing output from a BBW (Bollinger Band Width) Simulator for a "
        "crypto futures trading system called Four Pillars.\n\n"
        "KEY DEFINITIONS:\n"
        "- BBW = Bollinger Band Width. Measures volatility expansion/contraction.\n"
        "- BBWP = BBW Percentile (0-100 relative to lookback). High = expanding, Low = compressing.\n"
        "- bbwp_state values: NORMAL (mid-range), BLUE (high BBWP, expansion), "
        "RED (low BBWP, compression), BLUE_DOUBLE (extreme expansion).\n"
        "- The simulator ran a grid search: for each state it tested every combination of "
        "leverage (5/10/15/20x), position size (0.25/0.5/0.75/1.0 of $250 base), "
        "TP target (1-6 ATR), SL (1.0/1.5/2.0/3.0 ATR), and forward window (10/20 bars).\n"
        "- Commission: 0.08% taker per side on notional. Blended rate ~0.05%/side.\n"
        "- expectancy: Expected net USD PnL per trade after commission.\n"
        "- win_rate_long / win_rate_short: % trades profitable for that direction.\n"
        "- net_pnl: Total net PnL over the dataset.\n"
        "- max_dd: Maximum drawdown in USD.\n"
        "- MCL / max_consecutive_loss: Worst losing streak length.\n"
        "- profit_factor: Gross profit / Gross loss (>1 = edge).\n"
        "- n_trades: Sample size. Below 30 = unreliable.\n"
        "- LSG = Loser Saw Green: % of losing trades that were briefly profitable "
        "(high LSG means TP too tight or exits too slow).\n"
        "- robust verdict: Monte Carlo CI for expectancy stayed > 0 across 95% of sims.\n"
        "- fragile verdict: passed backtest but failed MC permutation (likely curve-fit).\n\n"
    )
    prompt = (
        context
        + "STATE STATS (one row per bbwp_state x direction x lever/size/TP/SL combo):\n"
        + (state_text or "N/A") + "\n\n"
        "MONTE CARLO SUMMARY (per state: verdict, CI bounds, equity band):\n"
        + (mc_text or "N/A") + "\n\n"
        "Based on the above data, provide a concise analysis covering:\n"
        "1. Which bbwp_state shows the strongest edge (highest expectancy per trade)?\n"
        "2. Which states have a ROBUST Monte Carlo verdict (genuine edge vs lucky backtest)?\n"
        "3. Which direction (long vs short) performs better per state?\n"
        "4. Key risk metrics to watch (max_dd, MCL, low n_trades warnings).\n"
        "Format as markdown with headers. Be specific -- reference state names and numbers."
    )
    return ollama_chat(prompt, model=model)


def investigate_anomalies(overfit_flags_csv, per_tier_dir, model="qwen3-coder:30b"):
    """Investigate overfit flags and per-tier anomalies; return markdown string."""
    overfit_text = _read_csv_sample(overfit_flags_csv)
    per_tier_dir = Path(per_tier_dir)
    tier_texts = []
    if per_tier_dir.exists():
        for f in sorted(per_tier_dir.glob("*.csv"))[:5]:
            t = _read_csv_sample(f, max_rows=10)
            if t:
                tier_texts.append("TIER " + f.stem + ":\n" + t)
    tier_summary = "\n\n".join(tier_texts) if tier_texts else "N/A"
    if not overfit_text and not tier_texts:
        return "## Anomaly Investigation\n\nNo data available."
    context2 = (
        "SYSTEM CONTEXT:\n"
        "You are reviewing overfitting diagnostics for a crypto futures BBW Simulator.\n\n"
        "WHAT THIS DATA REPRESENTS:\n"
        "- The simulator tested 4 volatility states (NORMAL/BLUE/RED/BLUE_DOUBLE) "
        "on historical data across multiple coins.\n"
        "- Coins are grouped into volatility tiers by KMeans on ATR%: "
        "Tier 0 = calmest (smallest ATR%), Tier 3 = wildest (largest ATR%).\n"
        "- OVERFIT FLAGS come from Monte Carlo permutation tests: a state is flagged if "
        "its edge disappears when trade order is randomly shuffled.\n"
        "- mc_pvalue: permutation test p-value (below 0.05 = statistically significant edge).\n"
        "- overfit_score: composite 0-1 (1.0 = fully overfit / no real edge).\n"
        "- is_fragile: True if edge fails under MC permutation despite passing backtest.\n"
        "- PER-TIER STATS show the same metrics split by coin volatility tier.\n\n"
    )
    prompt = (
        context2
        + "OVERFIT FLAGS:\n" + (overfit_text or "N/A") + "\n\n"
        "PER-TIER STATS:\n" + tier_summary + "\n\n"
        "Based on this data:\n"
        "1. Which states or coin tiers show clear curve-fitting (is_fragile=True, "
        "high overfit_score, or mc_pvalue > 0.05)?\n"
        "2. Are differences between tiers physically justified by volatility differences "
        "(wilder coins have bigger ATR so TP is worth more in dollar terms)?\n"
        "3. For each flagged state/tier, suggest a concrete parameter fix "
        "(wider TP, lower leverage, higher minimum n_trades threshold).\n"
        "Format as markdown. Reference state names, tier numbers, and specific values."
    )
    return ollama_chat(prompt, model=model)


def generate_executive_summary(all_results, model="qwen3-coder:30b"):
    """Generate executive summary of all BBW results; return markdown string."""
    if not all_results:
        return "## Executive Summary\n\nNo results to summarize."
    results_text = json.dumps(all_results, indent=2, default=str)[:4000]
    context3 = (
        "SYSTEM CONTEXT (essential background):\n"
        "You are reviewing a quantitative trading research project called BBW Simulator.\n\n"
        "THE STRATEGY: Four Pillars is a crypto futures momentum strategy that uses "
        "multi-timeframe stochastics (9/14/40/60-period Kurisko Raw K) and Ripster EMA clouds "
        "to generate long/short entry signals graded A (strongest) to D (weakest).\n\n"
        "THE SIMULATOR PURPOSE: Determine the optimal leverage, position size, TP (take-profit), "
        "and SL (stop-loss) for each Bollinger Band Width (BBW) volatility state, so the "
        "strategy can adapt position sizing to market conditions.\n\n"
        "BBW STATES: NORMAL (ordinary volatility), BLUE (expanding - BBW rising), "
        "RED (compressing - BBW falling), BLUE_DOUBLE (extreme expansion - top 1% BBW).\n\n"
        "ECONOMICS: Commission is 0.08% taker per side on notional. At 10x leverage on "
        "$250 margin, one round-trip costs ~$4. Expectancy must beat commission per trade.\n\n"
        "KNOWN INSIGHT: Low-price coins (RIVER, KITE, PEPE) are profitable because their "
        "ATR is large relative to commission. BTC/ETH often fail because commission consumes "
        "too much of the TP. This is not a bug -- it is structural.\n\n"
        "RESULTS JSON:\n"
    )
    prompt = (
        context3
        + results_text + "\n\n"
        "Write a 3-paragraph executive summary covering:\n"
        "1. Overall edge quality: which BBW states have genuine, Monte-Carlo-confirmed edge?\n"
        "2. Best-performing states and the recommended leverage/size/TP/SL for each.\n"
        "3. Key risks (commission sensitivity, MCL, low sample sizes) and next research steps.\n"
        "Format as markdown with a header for each paragraph. Be direct and quantitative."
    )
    return ollama_chat(prompt, model=model)


def run_ollama_review(reports_dir="reports/bbw", output_dir="reports/bbw/ollama",
                      model=DEFAULT_MODEL, verbose=False):
    """Run all Ollama review steps; write .md files; return status dict.

    Returns dict: files_written (list), errors (list), summary (dict).
    Never raises -- all errors are logged and collected.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    t0 = time.time()
    reports_dir = Path(reports_dir)
    output_dir = Path(output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {
            "files_written": [],
            "errors": ["Cannot create output dir: " + str(e)],
            "summary": {"timestamp": ts, "runtime_sec": 0},
        }

    files_written = []
    errors = []

    # Step 1: State stats analysis
    state_csv = reports_dir / "aggregate" / "bbw_state_stats.csv"
    mc_csv = reports_dir / "monte_carlo" / "mc_summary_by_state.csv"
    if verbose:
        log.info("[%s] Analyzing state stats...", ts)
    try:
        analysis = analyze_state_stats(str(state_csv), str(mc_csv), model=model)
        out_path = output_dir / "state_analysis.md"
        out_path.write_text("# BBW State Analysis\n\n" + analysis + "\n",
                            encoding="utf-8")
        files_written.append(str(out_path))
        if verbose:
            log.info("  WROTE: %s", out_path.name)
    except PermissionError as e:
        errors.append("state_analysis.md: PermissionError: " + str(e))
        log.error("Cannot write state_analysis.md: %s", e)
    except Exception as e:
        errors.append("state_analysis.md: " + str(e))
        log.warning("State analysis failed: %s", e)

    # Step 2: Anomaly investigation
    overfit_csv = reports_dir / "monte_carlo" / "mc_overfit_flags.csv"
    per_tier_dir = reports_dir / "per_tier"
    if verbose:
        log.info("  Investigating anomalies...")
    try:
        anomaly = investigate_anomalies(str(overfit_csv), str(per_tier_dir), model=model)
        out_path = output_dir / "anomaly_investigation.md"
        out_path.write_text("# Anomaly Investigation\n\n" + anomaly + "\n",
                            encoding="utf-8")
        files_written.append(str(out_path))
        if verbose:
            log.info("  WROTE: %s", out_path.name)
    except PermissionError as e:
        errors.append("anomaly_investigation.md: PermissionError: " + str(e))
        log.error("Cannot write anomaly_investigation.md: %s", e)
    except Exception as e:
        errors.append("anomaly_investigation.md: " + str(e))
        log.warning("Anomaly investigation failed: %s", e)

    # Step 3: Executive summary
    all_results = {
        "state_stats_csv": str(state_csv),
        "mc_summary_csv": str(mc_csv),
        "files_written": files_written,
        "errors": errors,
        "timestamp": ts,
    }
    if verbose:
        log.info("  Generating executive summary...")
    try:
        summary_text = generate_executive_summary(all_results, model=model)
        out_path = output_dir / "executive_summary.md"
        out_path.write_text("# Executive Summary\n\n" + summary_text + "\n",
                            encoding="utf-8")
        files_written.append(str(out_path))
        if verbose:
            log.info("  WROTE: %s", out_path.name)
    except PermissionError as e:
        errors.append("executive_summary.md: PermissionError: " + str(e))
        log.error("Cannot write executive_summary.md: %s", e)
    except Exception as e:
        errors.append("executive_summary.md: " + str(e))
        log.warning("Executive summary failed: %s", e)

    runtime = time.time() - t0
    return {
        "files_written": files_written,
        "errors": errors,
        "summary": {
            "timestamp": ts,
            "n_files": len(files_written),
            "n_errors": len(errors),
            "runtime_sec": round(runtime, 2),
        },
    }
