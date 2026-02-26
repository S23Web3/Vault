#!/usr/bin/env python3
"""
Capital Utilization Analyzer for v3.8.2 Multi-Coin

Parses TradingView strategy CSV exports. Builds 5-min bar timeline
of concurrent positions. Computes capital efficiency, scaled P&L,
rate-based commission, and rebate for multi-coin deployment.

CSV Net P&L % = pure price return (no commission baked in).
Commission computed rate-based on scaled notional. Rebate settles daily.

Usage: python scripts/capital_utilization.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# ── Configuration ───────────────────────────────────────────────────────
NOTIONAL_SCALE   = 20           # TV ran ~$250/pos, target $5000/pos
TARGET_NOTIONAL  = 5000         # Per position level
LEVERAGE         = 20
MARGIN_PER_LEVEL = TARGET_NOTIONAL / LEVERAGE   # $250
COMMISSION_RATE  = 0.0008       # 0.08% taker per side
REBATE_PCT       = 0.50         # 50% commission rebate (settles daily 5pm UTC)
ACCOUNT_SIZE     = 10_000       # $10K account

CSV_FILES = {
    'BERA':  Path(r"C:\Users\User\Downloads\bera new.csv"),
    'RIVER': Path(r"C:\Users\User\Downloads\river new.csv"),
}


# ── Parsing ─────────────────────────────────────────────────────────────

def parse_trades(path: Path) -> pd.DataFrame:
    """Parse TradingView strategy CSV into trade records.

    TV exports 2 rows per trade: Exit first, Entry second, same Trade #.
    Position size (value) = notional at TV settings (~$250).
    Net P&L % = pure price return, no commission.
    """
    raw = pd.read_csv(path)
    raw.columns = [c.strip().lstrip('\ufeff') for c in raw.columns]

    records = []
    for tnum, grp in raw.groupby('Trade #'):
        entry_rows = grp[grp['Type'].str.startswith('Entry')]
        exit_rows  = grp[grp['Type'].str.startswith('Exit')]

        if entry_rows.empty or exit_rows.empty:
            continue

        e = entry_rows.iloc[0]
        x = exit_rows.iloc[0]

        t_entry = pd.to_datetime(e['Date and time'])
        t_exit  = pd.to_datetime(x['Date and time'])

        if t_entry >= t_exit:
            continue

        records.append({
            'trade_num':      int(tnum),
            'entry_time':     t_entry,
            'exit_time':      t_exit,
            'position_value': float(str(e['Position size (value)']).replace(',', '')),
            'net_pnl_usd':    float(str(e['Net P&L USD']).replace(',', '')),
            'net_pnl_pct':    float(str(e['Net P&L %']).replace(',', '')),
        })

    return pd.DataFrame(records)


# ── Timeline ────────────────────────────────────────────────────────────

def build_timeline(trades: pd.DataFrame) -> tuple:
    """Build 5-min bar timeline with position count and raw notional.

    Position count = round(sum_notional / 250). Handles dust trades
    from pyramiding fills that TV splits into main + remainder.
    """
    if trades.empty:
        empty = pd.Series(dtype=float)
        return empty, empty

    t0 = trades['entry_time'].min().floor('5min')
    t1 = trades['exit_time'].max().ceil('5min')
    bars = pd.date_range(t0, t1, freq='5min')

    notional = np.zeros(len(bars))

    for _, tr in trades.iterrows():
        mask = (bars >= tr['entry_time']) & (bars < tr['exit_time'])
        notional[mask] += tr['position_value']

    notional_s = pd.Series(notional, index=bars)
    pos_count  = (notional_s / 250).round().astype(int)

    return pos_count, notional_s


# ── Metrics ─────────────────────────────────────────────────────────────

def compute_metrics(trades: pd.DataFrame, pos_count: pd.Series, label: str) -> dict:
    """Compute all capital utilization metrics for one coin."""
    n = len(trades)
    m = {'label': label, 'trades': n}

    # Position distribution
    m['avg_conc']  = pos_count.mean()
    m['max_conc']  = int(pos_count.max())
    m['pct_flat']  = (pos_count == 0).mean() * 100
    m['pct_1']     = (pos_count == 1).mean() * 100
    m['pct_2']     = (pos_count == 2).mean() * 100
    m['pct_3']     = (pos_count == 3).mean() * 100
    m['pct_4']     = (pos_count >= 4).mean() * 100

    # Margin at scaled notional ($250 margin per position level)
    scaled_margin    = pos_count * MARGIN_PER_LEVEL
    m['avg_margin']  = scaled_margin.mean()
    m['peak_margin'] = float(scaled_margin.max())

    # Hold time
    hold_hrs    = (trades['exit_time'] - trades['entry_time']).dt.total_seconds() / 3600
    m['avg_hold'] = hold_hrs.mean()

    # P&L at scaled notional
    # net_pnl_pct is pure price return; scale each trade's notional by 20x
    scaled_val     = trades['position_value'] * NOTIONAL_SCALE
    m['gross_pnl'] = (trades['net_pnl_pct'] / 100 * scaled_val).sum()

    # Commission: 0.08% per side on scaled notional, both entry and exit
    per_trade_comm    = scaled_val * COMMISSION_RATE * 2
    m['commission']   = per_trade_comm.sum()
    m['avg_comm_rt']  = per_trade_comm.mean() if n > 0 else 0

    # Rebate (settles daily 5pm UTC)
    m['rebate']        = m['commission'] * REBATE_PCT
    m['net_pnl']       = m['gross_pnl'] - m['commission'] + m['rebate']
    m['net_per_trade'] = m['net_pnl'] / n if n > 0 else 0
    m['idle_avg']      = ACCOUNT_SIZE - m['avg_margin']
    m['max_coins']     = int(ACCOUNT_SIZE / m['peak_margin']) if m['peak_margin'] > 0 else 0

    return m


# ── Output ──────────────────────────────────────────────────────────────

def fmt_dlr(v, decimals=2):
    return f"${v:,.{decimals}f}"


def print_report(mb, mr, combined_pos):
    ct   = mb['trades'] + mr['trades']
    cg   = mb['gross_pnl'] + mr['gross_pnl']
    cc   = mb['commission'] + mr['commission']
    cre  = mb['rebate'] + mr['rebate']
    cn   = mb['net_pnl'] + mr['net_pnl']
    cnpt = cn / ct if ct else 0

    c_avg_m  = combined_pos.mean() * MARGIN_PER_LEVEL
    c_peak_m = float(combined_pos.max()) * MARGIN_PER_LEVEL
    c_idle   = ACCOUNT_SIZE - c_avg_m
    c_flat   = (combined_pos == 0).mean() * 100
    c_max    = int(ACCOUNT_SIZE / c_peak_m) if c_peak_m > 0 else 0

    t0   = combined_pos.index.min().strftime('%Y-%m-%d')
    t1   = combined_pos.index.max().strftime('%Y-%m-%d')
    days = (combined_pos.index.max() - combined_pos.index.min()).days

    W   = 16
    sep = '=' * 78

    print()
    print(sep)
    print(f"  CAPITAL UTILIZATION: v3.8.2 Multi-Coin")
    print(f"  {t0} to {t1} ({days} days)")
    print(f"  ${TARGET_NOTIONAL:,} notional/pos | {LEVERAGE}x leverage | ${MARGIN_PER_LEVEL:,.0f} margin/pos")
    print(f"  Commission: {COMMISSION_RATE*100:.2f}%/side (rate-based) | Rebate: {REBATE_PCT*100:.0f}% (daily settle)")
    print(f"  Account: ${ACCOUNT_SIZE:,}")
    print(sep)

    def fv(v, fmt_type):
        """Format a single value."""
        if isinstance(v, str):
            return v
        if v is None:
            return "--"
        if fmt_type == 'd':
            return f"{int(v):,d}"
        if fmt_type == 'f1':
            return f"{v:.1f}"
        if fmt_type == 'pct':
            return f"{v:.1f}%"
        if fmt_type == '$':
            return fmt_dlr(v)
        if fmt_type == '$0':
            return fmt_dlr(v, 0)
        return str(v)

    def hdr():
        print(f"\n  {'':30}{'BERA':>{W}}  {'RIVER':>{W}}  {'COMBINED':>{W}}")
        print(f"  {'':30}{'-'*W}  {'-'*W}  {'-'*W}")

    def row(lbl, a, b, c, fmt='s'):
        sa, sb, sc = fv(a, fmt), fv(b, fmt), fv(c, fmt)
        print(f"  {lbl:<30}{sa:>{W}}  {sb:>{W}}  {sc:>{W}}")

    # -- Positions --
    hdr()
    row('Trades',             mb['trades'],   mr['trades'],   ct,                       'd')
    row('Avg concurrent pos', mb['avg_conc'], mr['avg_conc'], combined_pos.mean(),       'f1')
    row('Max concurrent pos', mb['max_conc'], mr['max_conc'], int(combined_pos.max()),   'd')

    # -- Distribution --
    print()
    row('% time flat',  mb['pct_flat'], mr['pct_flat'], c_flat, 'pct')
    row('% time 1 pos', mb['pct_1'],    mr['pct_1'],    None,   'pct')
    row('% time 2 pos', mb['pct_2'],    mr['pct_2'],    None,   'pct')
    row('% time 3 pos', mb['pct_3'],    mr['pct_3'],    None,   'pct')
    row('% time 4+ pos',mb['pct_4'],    mr['pct_4'],    None,   'pct')

    # -- Capital --
    print()
    row('Avg margin in use',   mb['avg_margin'],  mr['avg_margin'],  c_avg_m,  '$0')
    row('Peak margin in use',  mb['peak_margin'], mr['peak_margin'], c_peak_m, '$0')
    row('Avg hold time (hrs)', mb['avg_hold'],    mr['avg_hold'],    '--',     'f1')

    # -- P&L --
    print()
    row('Gross P&L (scaled)',     mb['gross_pnl'],    mr['gross_pnl'],    cg,                       '$')
    row('Commission (rate-based)',mb['commission'],    mr['commission'],   cc,                       '$')
    row('  avg $/RT',             mb['avg_comm_rt'],  mr['avg_comm_rt'],  cc / ct if ct else 0,     '$')
    row(f'Rebate ({REBATE_PCT*100:.0f}%)',
                                  mb['rebate'],       mr['rebate'],       cre,                      '$')
    row('Net P&L',                mb['net_pnl'],      mr['net_pnl'],      cn,                       '$')
    row('Net $/trade',            mb['net_per_trade'],mr['net_per_trade'],cnpt,                      '$')

    # -- Utilization --
    print()
    row('Idle capital (avg)',       mb['idle_avg'],   mr['idle_avg'],   c_idle, '$0')
    row('Max coins @ $250 margin',  mb['max_coins'],  mr['max_coins'],  c_max,  'd')

    print()
    print(sep)
    print()


# ── Main ────────────────────────────────────────────────────────────────

def main():
    for label, path in CSV_FILES.items():
        if not path.exists():
            print(f"ERROR: {path} not found")
            sys.exit(1)

    results   = {}
    timelines = {}

    for label, path in CSV_FILES.items():
        print(f"Parsing {label}...")
        trades = parse_trades(path)
        print(f"  {len(trades)} trades  |  {trades['entry_time'].min()} to {trades['exit_time'].max()}")

        pos_count, _ = build_timeline(trades)
        metrics = compute_metrics(trades, pos_count, label)

        results[label]   = metrics
        timelines[label] = pos_count

    # Combined timeline: align both coins on union of 5-min bars
    all_bars = timelines['BERA'].index.union(timelines['RIVER'].index)
    combined = (
        timelines['BERA'].reindex(all_bars, fill_value=0) +
        timelines['RIVER'].reindex(all_bars, fill_value=0)
    )

    print_report(results['BERA'], results['RIVER'], combined)


if __name__ == '__main__':
    main()
