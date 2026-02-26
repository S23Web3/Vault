"""
Full sweep: ALL cached coins on BOTH 1m and 5m with v3.8 Cloud 3 filter.
Uses BE$2 (overall winner from sweep_v38).
Saves all results to PostgreSQL, ranks by expectancy.
Output: data/output/sweep_all_coins/ (CSV + JSON + log)

Usage: python scripts/sweep_all_coins.py [--dry-run] [--no-db] [--top N]
"""
import sys
import os
import time
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from data.fetcher import BybitFetcher
from data.db import save_backtest_run
from signals.four_pillars import compute_signals
from engine.backtester import Backtester

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'output' / 'sweep_all_coins'
TIMEFRAMES = ['1m', '5m']

BT_PARAMS = {
    'sl_mult': 1.0, 'tp_mult': 1.5, 'cooldown': 3,
    'b_open_fresh': True, 'notional': 10000.0,
    'commission_rate': 0.0008, 'rebate_pct': 0.70,
    'initial_equity': 10000.0, 'be_raise_amount': 2.0,
}


def ensure_output_dir():
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        test_file = OUTPUT_DIR / '.write_test'
        test_file.write_text('ok')
        test_file.unlink()
        return True
    except PermissionError:
        print(f'[FATAL] No write permission to {OUTPUT_DIR}')
        return False
    except Exception as e:
        print(f'[FATAL] Cannot create output dir: {e}')
        return False


def resample_5m(df_1m):
    df = df_1m.copy()
    if 'datetime' not in df.columns:
        if df.index.name == 'datetime':
            df = df.reset_index()
    df = df.set_index('datetime')
    ohlcv = df.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
        'base_vol': 'sum', 'quote_vol': 'sum', 'timestamp': 'first'
    }).dropna()
    ohlcv = ohlcv.reset_index()
    return ohlcv


def run_single(sym, df_1m, tf, args, log_fn):
    if tf == '5m':
        df = resample_5m(df_1m)
        if len(df) < 200:
            return None
    else:
        df = df_1m.copy()
        if len(df) < 500:
            return None

    df_sig = compute_signals(df.copy())

    bt = Backtester(BT_PARAMS.copy())
    result = bt.run(df_sig)
    m = result['metrics']
    trades = result['trades']

    if m['total_trades'] == 0:
        return None

    true_net = m['equity_curve'][-1] - 10000.0
    exp = true_net / m['total_trades']

    db_status = 'skipped'
    if not args.no_db and not args.dry_run:
        try:
            run_id = save_backtest_run(
                symbol=sym, timeframe=tf, params=BT_PARAMS,
                metrics=m, trades=trades,
                equity_curve=m.get('equity_curve'),
                notes=f'v3.8 full sweep: BE$2 {tf}',
            )
            db_status = f'run_id={run_id}'
        except Exception as e:
            db_status = f'DB: {e}'

    return {
        'Symbol': sym, 'TF': tf, 'Trades': m['total_trades'],
        'WR': m['win_rate'] * 100, 'Net_PnL': true_net,
        'Exp': exp, 'LSG': m['pct_losers_saw_green'] * 100,
        'BE_n': m['be_raised_count'],
        'MFE': m['avg_mfe'], 'MAE': m['avg_mae'],
        'MaxDD': m['max_drawdown_pct'],
        'Sharpe': m['sharpe'], 'PF': m['profit_factor'],
        'db_status': db_status,
    }


def run_sweep(args):
    if not ensure_output_dir():
        sys.exit(1)

    fetcher = BybitFetcher(cache_dir=str(PROJECT_ROOT / 'data' / 'cache'))
    symbols = sorted(fetcher.list_cached())
    total_jobs = len(symbols) * len(TIMEFRAMES)
    print(f'Found {len(symbols)} cached coins x {len(TIMEFRAMES)} timeframes = {total_jobs} backtests')
    print(f'Output: {OUTPUT_DIR}')
    print(f'DB save: {"OFF" if args.no_db else "ON"}')
    if args.dry_run:
        print('DRY RUN -- will not save to DB')
    print()

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    log_path = OUTPUT_DIR / f'sweep_{timestamp}.log'
    log_file = open(log_path, 'w', encoding='utf-8')

    def log(msg):
        print(msg)
        log_file.write(msg + '\n')
        log_file.flush()

    all_results = []
    errors = []
    skipped = []
    job = 0
    t0 = time.time()

    for idx, sym in enumerate(symbols, 1):
        try:
            df_1m = fetcher.load_cached(sym)
            if df_1m is None or len(df_1m) < 500:
                for tf in TIMEFRAMES:
                    job += 1
                    skipped.append((sym, tf, '< 500 1m bars'))
                log(f'[{idx}/{len(symbols)}] {sym:>25}  SKIP (< 500 bars)')
                continue

            for tf in TIMEFRAMES:
                job += 1
                elapsed = time.time() - t0
                eta = (elapsed / job) * (total_jobs - job) if job > 0 else 0

                r = run_single(sym, df_1m, tf, args, log)
                if r is None:
                    skipped.append((sym, tf, '0 trades or too few bars'))
                    log(f'[{job}/{total_jobs}] {sym:>25} {tf:>3}  SKIP')
                    continue

                log(f'[{job}/{total_jobs}] {sym:>25} {tf:>3}  {r["Trades"]:>5} tr  '
                    f'WR {r["WR"]:>5.1f}%  Net ${r["Net_PnL"]:>10,.2f}  '
                    f'Exp ${r["Exp"]:>7.2f}  LSG {r["LSG"]:>5.1f}%  '
                    f'{r["db_status"]}  ETA {eta/60:.1f}m')

                all_results.append(r)

        except Exception as e:
            errors.append((sym, str(e)))
            log(f'[{job}/{total_jobs}] {sym:>25}  ERROR: {e}')

    elapsed_total = time.time() - t0

    rdf = pd.DataFrame(all_results)
    if rdf.empty:
        log('\nNo results.')
        log_file.close()
        sys.exit(0)

    # Per-timeframe rankings
    for tf in TIMEFRAMES:
        tf_df = rdf[rdf['TF'] == tf].sort_values('Exp', ascending=False)
        if tf_df.empty:
            continue

        top_n = args.top
        profitable = tf_df[tf_df['Net_PnL'] > 0]
        unprofitable = tf_df[tf_df['Net_PnL'] <= 0]

        log(f'\n\n{"="*120}')
        log(f'TOP {top_n} COINS BY EXPECTANCY -- {tf} -- v3.8 Cloud3 + BE$2')
        log(f'{"="*120}')
        log(f'{"#":>3} {"Symbol":>25} {"Trades":>7} {"WR%":>6} {"Net P&L":>12} '
            f'{"Exp$/tr":>9} {"LSG%":>6} {"BE_n":>5} {"MaxDD%":>7} {"Sharpe":>7} {"PF":>7}')
        for i, (_, row) in enumerate(tf_df.head(top_n).iterrows(), 1):
            log(f'{i:>3} {row["Symbol"]:>25} {int(row["Trades"]):>7} '
                f'{row["WR"]:>6.1f} {row["Net_PnL"]:>12,.2f} {row["Exp"]:>9.2f} '
                f'{row["LSG"]:>6.1f} {int(row["BE_n"]):>5} {row["MaxDD"]:>7.1f} '
                f'{row["Sharpe"]:>7.3f} {row["PF"]:>7.2f}')

        log(f'\n  {tf} Summary: {len(tf_df)} coins | '
            f'{len(profitable)} profitable ({len(profitable)/len(tf_df)*100:.1f}%) | '
            f'{int(tf_df["Trades"].sum()):,} trades | '
            f'Net ${tf_df["Net_PnL"].sum():,.2f} | '
            f'Avg Exp ${tf_df["Exp"].mean():.2f}/tr')

    # 1m vs 5m comparison for coins that have both
    log(f'\n\n{"="*120}')
    log('1m vs 5m COMPARISON (coins with both timeframes)')
    log(f'{"="*120}')
    log(f'{"Symbol":>25} {"1m Trades":>10} {"1m Net":>12} {"1m Exp":>9} {"5m Trades":>10} {"5m Net":>12} {"5m Exp":>9} {"Winner":>7}')
    syms_both = set(rdf[rdf['TF'] == '1m']['Symbol']) & set(rdf[rdf['TF'] == '5m']['Symbol'])
    wins_1m = 0
    wins_5m = 0
    for sym in sorted(syms_both):
        r1 = rdf[(rdf['Symbol'] == sym) & (rdf['TF'] == '1m')].iloc[0]
        r5 = rdf[(rdf['Symbol'] == sym) & (rdf['TF'] == '5m')].iloc[0]
        winner = '1m' if r1['Exp'] > r5['Exp'] else '5m'
        if winner == '1m':
            wins_1m += 1
        else:
            wins_5m += 1
        log(f'{sym:>25} {int(r1["Trades"]):>10} {r1["Net_PnL"]:>12,.2f} {r1["Exp"]:>9.2f} '
            f'{int(r5["Trades"]):>10} {r5["Net_PnL"]:>12,.2f} {r5["Exp"]:>9.2f} {winner:>7}')
    log(f'\n  1m wins: {wins_1m} | 5m wins: {wins_5m}')

    # Grand summary
    log(f'\n\n{"="*120}')
    log('GRAND SUMMARY')
    log(f'{"="*120}')
    profitable_all = rdf[rdf['Net_PnL'] > 0]
    log(f'Total backtests:      {len(rdf)}')
    log(f'Profitable:           {len(profitable_all)} ({len(profitable_all)/len(rdf)*100:.1f}%)')
    log(f'Skipped:              {len(skipped)}')
    log(f'Errors:               {len(errors)}')
    log(f'Total trades:         {int(rdf["Trades"].sum()):,}')
    log(f'Total Net P&L:        ${rdf["Net_PnL"].sum():,.2f}')
    log(f'Elapsed:              {elapsed_total/60:.1f} minutes')

    if errors:
        log(f'\nERRORS:')
        for sym, err in errors:
            log(f'  {sym}: {err}')

    # Save CSV (full ranked, both timeframes)
    rdf_sorted = rdf.sort_values(['TF', 'Exp'], ascending=[True, False])
    csv_path = OUTPUT_DIR / f'sweep_{timestamp}.csv'
    rdf_sorted.to_csv(csv_path, index=False)
    log(f'\nCSV: {csv_path}')

    # Save JSON summary
    summary = {
        'timestamp': timestamp,
        'version': 'v3.8',
        'be_config': 'BE$2',
        'timeframes': TIMEFRAMES,
        'total_backtests': len(rdf),
        'profitable': len(profitable_all),
        'skipped': len(skipped),
        'errors': len(errors),
        'total_trades': int(rdf['Trades'].sum()),
        'total_net_pnl': round(float(rdf['Net_PnL'].sum()), 2),
        'elapsed_minutes': round(elapsed_total / 60, 1),
        '1m_wins': wins_1m,
        '5m_wins': wins_5m,
        'per_tf': {},
    }
    for tf in TIMEFRAMES:
        tf_df = rdf[rdf['TF'] == tf]
        if not tf_df.empty:
            tf_prof = tf_df[tf_df['Net_PnL'] > 0]
            summary['per_tf'][tf] = {
                'coins': len(tf_df),
                'profitable': len(tf_prof),
                'total_trades': int(tf_df['Trades'].sum()),
                'total_net_pnl': round(float(tf_df['Net_PnL'].sum()), 2),
                'avg_exp': round(float(tf_df['Exp'].mean()), 2),
                'top_10': tf_df.sort_values('Exp', ascending=False).head(10)[
                    ['Symbol', 'Trades', 'Net_PnL', 'Exp', 'Sharpe']
                ].to_dict('records'),
            }

    json_path = OUTPUT_DIR / f'sweep_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    log(f'JSON: {json_path}')

    rdf_sorted.to_csv(OUTPUT_DIR / 'latest.csv', index=False)
    with open(OUTPUT_DIR / 'latest.json', 'w') as f:
        json.dump(summary, f, indent=2)
    log(f'Latest: {OUTPUT_DIR / "latest.csv"}')

    log_file.close()
    print(f'\nLog: {log_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Full coin sweep v3.8 (1m + 5m)')
    parser.add_argument('--dry-run', action='store_true', help='Run without DB saves')
    parser.add_argument('--no-db', action='store_true', help='Skip all DB operations')
    parser.add_argument('--top', type=int, default=20, help='Top N coins to display (default 20)')
    args = parser.parse_args()
    run_sweep(args)
