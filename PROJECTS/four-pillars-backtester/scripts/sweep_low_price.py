"""
BE sweep on low-price coins: 1000PEPEUSDT, RIVERUSDT, KITEUSDT, HYPEUSDT, SANDUSDT
Both 1m and 5m timeframes, BE levels $0/$2/$4/$6/$8/$10
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from data.fetcher import BybitFetcher
from signals.four_pillars import compute_signals
from engine.backtester import Backtester

fetcher = BybitFetcher(cache_dir='data/cache')
symbols = ['1000PEPEUSDT', 'RIVERUSDT', 'KITEUSDT', 'HYPEUSDT', 'SANDUSDT']
be_levels = [0, 2, 4, 6, 8, 10]


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
    print(f'Loading {sym}...')
    df_1m = fetcher.load_cached(sym)
    if df_1m is None:
        print(f'  SKIP - no cached data')
        continue

    print(f'  Computing 1m signals ({len(df_1m)} bars)...')
    df_1m_sig = compute_signals(df_1m.copy())

    print(f'  Resampling to 5m...')
    df_5m = resample_5m(df_1m)
    print(f'  Computing 5m signals ({len(df_5m)} bars)...')
    df_5m_sig = compute_signals(df_5m.copy())

    for tf_label, df_sig in [('1m', df_1m_sig), ('5m', df_5m_sig)]:
        for be in be_levels:
            bt = Backtester({
                'sl_mult': 1.0, 'tp_mult': 1.5, 'cooldown': 3,
                'b_open_fresh': True, 'notional': 10000.0,
                'commission_rate': 0.0008, 'rebate_pct': 0.70,
                'initial_equity': 10000.0, 'be_raise_amount': float(be),
            })
            result = bt.run(df_sig)
            m = result['metrics']
            trades = result['trades']

            if m['total_trades'] == 0:
                continue

            longs = [t for t in trades if t.direction == 'LONG']
            shorts = [t for t in trades if t.direction == 'SHORT']
            long_net = sum(t.pnl - t.commission for t in longs)
            short_net = sum(t.pnl - t.commission for t in shorts)
            long_wr = sum(1 for t in longs if t.pnl - t.commission > 0) / len(longs) * 100 if longs else 0
            short_wr = sum(1 for t in shorts if t.pnl - t.commission > 0) / len(shorts) * 100 if shorts else 0

            notional_size = 10000.0
            comm_per_side = notional_size * 0.0008
            vol_per_trade = notional_size * 2  # entry + exit notional
            total_vol = vol_per_trade * m['total_trades']
            true_net = m['equity_curve'][-1] - 10000.0
            gross_comm = m['total_trades'] * comm_per_side * 2  # 2 sides per RT
            rebate = gross_comm * 0.70
            net_comm = gross_comm - rebate

            all_results.append({
                'Symbol': sym, 'TF': tf_label, 'BE': be,
                'Trades': m['total_trades'],
                'WR': m['win_rate'] * 100,
                'Net_PnL': true_net,
                'Gross_Comm': gross_comm,
                'Rebate': rebate,
                'Net_Comm': net_comm,
                'Exp': true_net / m['total_trades'],
                'Longs': len(longs), 'L_WR': long_wr, 'L_Net': long_net,
                'Shorts': len(shorts), 'S_WR': short_wr, 'S_Net': short_net,
                'LSG': m['pct_losers_saw_green'] * 100,
                'LSG_n': m['saw_green_losers'],
                'Losers': m['total_losers'],
                'BE_n': m['be_raised_count'],
                'MFE': m['avg_mfe'],
                'MAE': m['avg_mae'],
                'MaxDD': m['max_drawdown_pct'],
                'Vol': total_vol,
            })

    print(f'  Done: {sym}')

rdf = pd.DataFrame(all_results)

# Print 1m results
print()
print('=' * 140)
print('RESULTS - 1-MINUTE CANDLES')
print('=' * 140)
df1 = rdf[rdf['TF'] == '1m']
for sym in symbols:
    ds = df1[df1['Symbol'] == sym]
    if ds.empty:
        continue
    print(f'\n--- {sym} (1m) ---')
    print(f'{"BE":>4} {"Trades":>7} {"WR%":>6} {"Net P&L":>12} {"Exp$/tr":>9} {"LSG%":>6} {"LSG_n":>6} {"BE_n":>5} {"MaxDD%":>7} {"L":>5}/{"S":>5} {"L_WR":>5}/{"S_WR":>5} {"Volume":>14}')
    for _, r in ds.iterrows():
        print(f'{r["BE"]:>4} {r["Trades"]:>7} {r["WR"]:>6.1f} {r["Net_PnL"]:>12,.2f} {r["Exp"]:>9.2f} {r["LSG"]:>6.1f} {r["LSG_n"]:>6} {r["BE_n"]:>5} {r["MaxDD"]:>7.1f} {r["Longs"]:>5}/{r["Shorts"]:>5} {r["L_WR"]:>5.1f}/{r["S_WR"]:>5.1f} {r["Vol"]:>14,.0f}')

# Print 5m results
print()
print('=' * 140)
print('RESULTS - 5-MINUTE CANDLES')
print('=' * 140)
df5 = rdf[rdf['TF'] == '5m']
for sym in symbols:
    ds = df5[df5['Symbol'] == sym]
    if ds.empty:
        continue
    print(f'\n--- {sym} (5m) ---')
    print(f'{"BE":>4} {"Trades":>7} {"WR%":>6} {"Net P&L":>12} {"Exp$/tr":>9} {"LSG%":>6} {"LSG_n":>6} {"BE_n":>5} {"MaxDD%":>7} {"L":>5}/{"S":>5} {"L_WR":>5}/{"S_WR":>5} {"Volume":>14}')
    for _, r in ds.iterrows():
        print(f'{r["BE"]:>4} {r["Trades"]:>7} {r["WR"]:>6.1f} {r["Net_PnL"]:>12,.2f} {r["Exp"]:>9.2f} {r["LSG"]:>6.1f} {r["LSG_n"]:>6} {r["BE_n"]:>5} {r["MaxDD"]:>7.1f} {r["Longs"]:>5}/{r["Shorts"]:>5} {r["L_WR"]:>5.1f}/{r["S_WR"]:>5.1f} {r["Vol"]:>14,.0f}')

# Best BE per coin
print()
print('=' * 140)
print('BEST BE LEVEL PER COIN (by Net P&L)')
print('=' * 140)
print(f'{"Symbol":>15} {"TF":>4} {"BE":>4} {"Trades":>7} {"WR%":>6} {"Net P&L":>12} {"Exp$/tr":>9} {"LSG%":>6} {"Volume":>14}')
for sym in symbols:
    for tf in ['1m', '5m']:
        ds = rdf[(rdf['Symbol'] == sym) & (rdf['TF'] == tf)]
        if ds.empty:
            continue
        best = ds.loc[ds['Net_PnL'].idxmax()]
        print(f'{best["Symbol"]:>15} {best["TF"]:>4} {best["BE"]:>4} {best["Trades"]:>7} {best["WR"]:>6.1f} {best["Net_PnL"]:>12,.2f} {best["Exp"]:>9.2f} {best["LSG"]:>6.1f} {best["Vol"]:>14,.0f}')

# Grand totals
print()
print('=' * 140)
print('GRAND TOTALS (best BE per coin)')
print('=' * 140)
for tf in ['1m', '5m']:
    total_net = 0
    total_trades = 0
    total_vol = 0
    for sym in symbols:
        ds = rdf[(rdf['Symbol'] == sym) & (rdf['TF'] == tf)]
        if ds.empty:
            continue
        best = ds.loc[ds['Net_PnL'].idxmax()]
        total_net += best['Net_PnL']
        total_trades += best['Trades']
        total_vol += best['Vol']
    if total_trades > 0:
        print(f'{tf}: Net=${total_net:>12,.2f}  Trades={total_trades:>6,}  Vol=${total_vol:>14,.0f}  Exp/tr=${total_net/total_trades:.2f}')
