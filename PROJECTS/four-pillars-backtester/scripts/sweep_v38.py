"""
v3.8 sweep: 5 low-price coins on 5m with Cloud 3 filter (always-on).
Tests both legacy fixed-$ BE and ATR-based BE.
Saves all results to PostgreSQL.

Usage: python scripts/sweep_v38.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from data.fetcher import BybitFetcher
from data.db import save_backtest_run
from signals.four_pillars import compute_signals
from engine.backtester import Backtester

fetcher = BybitFetcher(cache_dir=str(Path(__file__).resolve().parent.parent / 'data' / 'cache'))
symbols = ['1000PEPEUSDT', 'RIVERUSDT', 'KITEUSDT', 'HYPEUSDT', 'SANDUSDT']

# BE configurations to test
be_configs = [
    # Legacy fixed-dollar BE
    {'label': 'BE$0',  'be_raise_amount': 0,  'be_trigger_atr': 0, 'be_lock_atr': 0},
    {'label': 'BE$2',  'be_raise_amount': 2,  'be_trigger_atr': 0, 'be_lock_atr': 0},
    {'label': 'BE$4',  'be_raise_amount': 4,  'be_trigger_atr': 0, 'be_lock_atr': 0},
    {'label': 'BE$6',  'be_raise_amount': 6,  'be_trigger_atr': 0, 'be_lock_atr': 0},
    {'label': 'BE$8',  'be_raise_amount': 8,  'be_trigger_atr': 0, 'be_lock_atr': 0},
    {'label': 'BE$10', 'be_raise_amount': 10, 'be_trigger_atr': 0, 'be_lock_atr': 0},
    # ATR-based BE (v3.8)
    {'label': 'ATR0.3/0.1', 'be_raise_amount': 0, 'be_trigger_atr': 0.3, 'be_lock_atr': 0.1},
    {'label': 'ATR0.5/0.2', 'be_raise_amount': 0, 'be_trigger_atr': 0.5, 'be_lock_atr': 0.2},
    {'label': 'ATR0.5/0.3', 'be_raise_amount': 0, 'be_trigger_atr': 0.5, 'be_lock_atr': 0.3},
    {'label': 'ATR0.7/0.3', 'be_raise_amount': 0, 'be_trigger_atr': 0.7, 'be_lock_atr': 0.3},
    {'label': 'ATR0.7/0.5', 'be_raise_amount': 0, 'be_trigger_atr': 0.7, 'be_lock_atr': 0.5},
    {'label': 'ATR1.0/0.5', 'be_raise_amount': 0, 'be_trigger_atr': 1.0, 'be_lock_atr': 0.5},
]


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


all_results = []

for sym in symbols:
    print(f'\n{"="*60}')
    print(f'  {sym}')
    print(f'{"="*60}')

    df_1m = fetcher.load_cached(sym)
    if df_1m is None:
        print(f'  SKIP - no cached data')
        continue

    print(f'  Resampling {len(df_1m)} 1m bars to 5m...')
    df_5m = resample_5m(df_1m)
    print(f'  Computing signals on {len(df_5m)} 5m bars...')
    df_5m_sig = compute_signals(df_5m.copy())

    for cfg in be_configs:
        bt = Backtester({
            'sl_mult': 1.0, 'tp_mult': 1.5, 'cooldown': 3,
            'b_open_fresh': True, 'notional': 10000.0,
            'commission_rate': 0.0008, 'rebate_pct': 0.70,
            'initial_equity': 10000.0,
            'be_raise_amount': float(cfg['be_raise_amount']),
            'be_trigger_atr': cfg['be_trigger_atr'],
            'be_lock_atr': cfg['be_lock_atr'],
        })
        result = bt.run(df_5m_sig)
        m = result['metrics']
        trades = result['trades']

        if m['total_trades'] == 0:
            continue

        true_net = m['equity_curve'][-1] - 10000.0
        notional_size = 10000.0
        comm_per_side = notional_size * 0.0008
        gross_comm = m['total_trades'] * comm_per_side * 2
        rebate = gross_comm * 0.70
        net_comm = gross_comm - rebate

        # Save to PostgreSQL
        bt_params = {
            'sl_mult': 1.0, 'tp_mult': 1.5, 'cooldown': 3,
            'b_open_fresh': True, 'notional': 10000.0,
            'commission_rate': 0.0008, 'rebate_pct': 0.70,
            'be_raise_amount': float(cfg['be_raise_amount']),
        }
        try:
            run_id = save_backtest_run(
                symbol=sym, timeframe='5m', params=bt_params,
                metrics=m, trades=trades,
                equity_curve=m.get('equity_curve'),
                notes=f"v3.8 sweep: {cfg['label']}",
            )
            db_status = f'run_id={run_id}'
        except Exception as e:
            db_status = f'DB ERROR: {e}'

        exp = true_net / m['total_trades']
        lsg = m['pct_losers_saw_green'] * 100

        print(f"  {cfg['label']:>12}  {m['total_trades']:>5} trades  WR {m['win_rate']*100:>5.1f}%  "
              f"Net ${true_net:>10,.2f}  Exp ${exp:>7.2f}  LSG {lsg:>5.1f}%  "
              f"BE_n {m['be_raised_count']:>4}  DD {m['max_drawdown_pct']:>5.1f}%  {db_status}")

        all_results.append({
            'Symbol': sym, 'BE_Config': cfg['label'],
            'Trades': m['total_trades'], 'WR': m['win_rate'] * 100,
            'Net_PnL': true_net, 'Exp': exp,
            'Gross_Comm': gross_comm, 'Rebate': rebate, 'Net_Comm': net_comm,
            'LSG': lsg, 'BE_n': m['be_raised_count'],
            'MFE': m['avg_mfe'], 'MAE': m['avg_mae'],
            'MaxDD': m['max_drawdown_pct'],
            'Sharpe': m['sharpe'], 'PF': m['profit_factor'],
        })

# Summary table
print(f'\n\n{"="*120}')
print('BEST BE CONFIG PER COIN (by Net P&L, 5m)')
print(f'{"="*120}')
rdf = pd.DataFrame(all_results)
print(f'{"Symbol":>15} {"Config":>12} {"Trades":>7} {"WR%":>6} {"Net P&L":>12} '
      f'{"Exp$/tr":>9} {"LSG%":>6} {"BE_n":>5} {"MaxDD%":>7} {"Sharpe":>7} {"PF":>7}')
for sym in symbols:
    ds = rdf[rdf['Symbol'] == sym]
    if ds.empty:
        continue
    best = ds.loc[ds['Net_PnL'].idxmax()]
    print(f'{best["Symbol"]:>15} {best["BE_Config"]:>12} {best["Trades"]:>7} '
          f'{best["WR"]:>6.1f} {best["Net_PnL"]:>12,.2f} {best["Exp"]:>9.2f} '
          f'{best["LSG"]:>6.1f} {best["BE_n"]:>5} {best["MaxDD"]:>7.1f} '
          f'{best["Sharpe"]:>7.3f} {best["PF"]:>7.2f}')

# ATR-based vs fixed-$ comparison
print(f'\n\n{"="*120}')
print('ATR-BASED vs FIXED-$ BE COMPARISON')
print(f'{"="*120}')
for sym in symbols:
    ds = rdf[rdf['Symbol'] == sym]
    if ds.empty:
        continue
    fixed = ds[~ds['BE_Config'].str.startswith('ATR')]
    atr_based = ds[ds['BE_Config'].str.startswith('ATR')]
    if fixed.empty or atr_based.empty:
        continue
    best_fixed = fixed.loc[fixed['Net_PnL'].idxmax()]
    best_atr = atr_based.loc[atr_based['Net_PnL'].idxmax()]
    delta = best_atr['Net_PnL'] - best_fixed['Net_PnL']
    print(f'{sym:>15}  Best Fixed: {best_fixed["BE_Config"]:>6} ${best_fixed["Net_PnL"]:>10,.2f}  |  '
          f'Best ATR: {best_atr["BE_Config"]:>12} ${best_atr["Net_PnL"]:>10,.2f}  |  '
          f'Delta: ${delta:>+10,.2f}')

# Grand totals
print(f'\n\n{"="*120}')
print('GRAND TOTALS (best config per coin)')
print(f'{"="*120}')
total_net = 0
total_trades = 0
for sym in symbols:
    ds = rdf[rdf['Symbol'] == sym]
    if ds.empty:
        continue
    best = ds.loc[ds['Net_PnL'].idxmax()]
    total_net += best['Net_PnL']
    total_trades += best['Trades']
if total_trades > 0:
    print(f'Total: Net=${total_net:>12,.2f}  Trades={total_trades:>6,}  Exp/tr=${total_net/total_trades:.2f}')

# Save CSV
csv_path = Path(__file__).resolve().parent.parent / 'data' / 'sweep_v38_results.csv'
rdf.to_csv(csv_path, index=False)
print(f'\nResults saved to {csv_path}')
