"""
v3.8.2 Failure Analysis - RIVERUSDT
Analyzes TradingView strategy export to identify why -99.14% P&L
"""
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter

# === LOAD DATA ===
csv_path = Path(r'C:\Users\User\Downloads\v3.8.2-S_BYBIT_RIVERUSDT.P_2026-02-11_5181c.csv')
df = pd.read_csv(csv_path, encoding='utf-8-sig')
df.columns = df.columns.str.strip()

# Parse datetime
df['DateTime'] = pd.to_datetime(df['Date and time'])

# Save as parquet
parquet_path = csv_path.with_suffix('.parquet')
df.to_parquet(parquet_path, index=False)
print(f"Parquet saved: {parquet_path}")
print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
print()

# === SEPARATE ENTRIES AND EXITS ===
entries = df[df['Type'].str.contains('Entry', case=False)].copy()
exits = df[df['Type'].str.contains('Exit', case=False)].copy()

print("="*70)
print("OVERVIEW")
print("="*70)
print(f"Total trades (Trade #): {df['Trade #'].nunique()}")
print(f"Entry rows: {len(entries)}")
print(f"Exit rows: {len(exits)}")
print(f"Date range: {df['DateTime'].min()} to {df['DateTime'].max()}")
days = (df['DateTime'].max() - df['DateTime'].min()).days
print(f"Trading days: {days}")
print(f"Trades per day: {df['Trade #'].nunique() / max(days, 1):.1f}")
print()

# === P&L ANALYSIS ===
# Use exit rows for P&L (each trade has one exit row)
trades = exits.copy()
trades['PnL'] = trades['Net P&L USD'].astype(float)
trades['PnL_pct'] = trades['Net P&L %'].astype(float)
trades['MFE'] = trades['Favorable excursion USD'].astype(float)
trades['MFE_pct'] = trades['Favorable excursion %'].astype(float)
trades['MAE'] = trades['Adverse excursion USD'].astype(float)
trades['MAE_pct'] = trades['Adverse excursion %'].astype(float)
trades['Position_Value'] = trades['Position size (value)'].astype(float)

winners = trades[trades['PnL'] > 0]
losers = trades[trades['PnL'] < 0]
breakeven = trades[trades['PnL'] == 0]

print("="*70)
print("P&L BREAKDOWN")
print("="*70)
print(f"Winners: {len(winners)} ({len(winners)/len(trades)*100:.1f}%)")
print(f"Losers:  {len(losers)} ({len(losers)/len(trades)*100:.1f}%)")
print(f"BE:      {len(breakeven)}")
print()
print(f"Avg Winner:  ${winners['PnL'].mean():.2f} ({winners['PnL_pct'].mean():.2f}%)")
print(f"Avg Loser:   ${losers['PnL'].mean():.2f} ({losers['PnL_pct'].mean():.2f}%)")
print(f"Largest Win: ${winners['PnL'].max():.2f}")
print(f"Largest Loss:${losers['PnL'].min():.2f}")
print(f"Total P&L:   ${trades['PnL'].sum():.2f}")
print(f"Profit Factor: {abs(winners['PnL'].sum() / losers['PnL'].sum()):.3f}" if losers['PnL'].sum() != 0 else "N/A")
print()

# === EXIT SIGNAL ANALYSIS ===
print("="*70)
print("EXIT SIGNALS (what's closing trades?)")
print("="*70)
exit_signals = trades['Signal'].value_counts()
for sig, count in exit_signals.items():
    subset = trades[trades['Signal'] == sig]
    pnl = subset['PnL'].sum()
    avg = subset['PnL'].mean()
    wr = (subset['PnL'] > 0).mean() * 100
    print(f"  {sig:20s}: {count:4d} trades | Total ${pnl:>10.2f} | Avg ${avg:>7.2f} | WR {wr:.0f}%")
print()

# === MARGIN CALLS ===
margin_calls = trades[trades['Signal'].str.contains('Margin', case=False, na=False)]
print("="*70)
print(f"MARGIN CALLS: {len(margin_calls)}")
print("="*70)
if len(margin_calls) > 0:
    print(f"Total loss from margin calls: ${margin_calls['PnL'].sum():.2f}")
    print(f"Avg margin call loss: ${margin_calls['PnL'].mean():.2f}")
    print(f"Position sizes at margin call:")
    print(f"  Min: ${margin_calls['Position_Value'].min():.2f}")
    print(f"  Max: ${margin_calls['Position_Value'].max():.2f}")
    print(f"  Avg: ${margin_calls['Position_Value'].mean():.2f}")
    print()
    print("First 10 margin calls:")
    for _, row in margin_calls.head(10).iterrows():
        print(f"  Trade #{row['Trade #']:4d} | {row['DateTime']} | PnL ${row['PnL']:>8.2f} | Pos ${row['Position_Value']:>10.2f}")
print()

# === ENTRY SIGNAL ANALYSIS ===
print("="*70)
print("ENTRY SIGNALS (what's opening trades?)")
print("="*70)
entry_signals = entries['Signal'].value_counts()
for sig, count in entry_signals.head(20).items():
    print(f"  {sig:20s}: {count:4d} entries")

# Check if same signal ID opens multiple trades (pyramiding issue)
signal_ids = entries['Signal'].str.extract(r'([A-Z]+\d+)', expand=False)
signal_counts = signal_ids.value_counts()
multi_entries = signal_counts[signal_counts > 1]
print(f"\nSignals used for multiple entries: {len(multi_entries)}")
if len(multi_entries) > 0:
    print(f"Max entries per signal: {multi_entries.max()}")
    print(f"Top repeated signals:")
    for sig, count in multi_entries.head(10).items():
        print(f"  {sig}: {count} entries")
print()

# === POSITION SIZE ANALYSIS ===
print("="*70)
print("POSITION SIZE ANALYSIS")
print("="*70)
print(f"Position values:")
print(f"  Min:    ${trades['Position_Value'].min():.2f}")
print(f"  Max:    ${trades['Position_Value'].max():.2f}")
print(f"  Mean:   ${trades['Position_Value'].mean():.2f}")
print(f"  Median: ${trades['Position_Value'].median():.2f}")
print()

# Tiny positions (margin depleted)
tiny = trades[trades['Position_Value'] < 100]
normal = trades[trades['Position_Value'] >= 2000]
mid = trades[(trades['Position_Value'] >= 100) & (trades['Position_Value'] < 2000)]
print(f"Normal positions (>=$2000): {len(normal)} ({len(normal)/len(trades)*100:.1f}%)")
print(f"Reduced positions ($100-$2000): {len(mid)} ({len(mid)/len(trades)*100:.1f}%)")
print(f"Tiny positions (<$100): {len(tiny)} ({len(tiny)/len(trades)*100:.1f}%)")
if len(tiny) > 0:
    print(f"  Tiny position total PnL: ${tiny['PnL'].sum():.2f}")
    print(f"  First tiny trade: #{tiny.iloc[0]['Trade #']}")
print()

# === TRADE DURATION ===
print("="*70)
print("TRADE DURATION")
print("="*70)
# Match entries to exits by Trade #
for _, exit_row in trades.iterrows():
    trade_num = exit_row['Trade #']
    entry_row = entries[entries['Trade #'] == trade_num]
    if len(entry_row) > 0:
        entry_time = entry_row.iloc[0]['DateTime']
        exit_time = exit_row['DateTime']
        duration = (exit_time - entry_time).total_seconds() / 60  # minutes
        trades.loc[trades['Trade #'] == trade_num, 'Duration_min'] = duration

if 'Duration_min' in trades.columns:
    durations = trades['Duration_min'].dropna()
    print(f"Duration (minutes):")
    print(f"  Min:    {durations.min():.0f}")
    print(f"  Max:    {durations.max():.0f}")
    print(f"  Mean:   {durations.mean():.1f}")
    print(f"  Median: {durations.median():.0f}")
    
    very_short = (durations <= 2).sum()
    short = ((durations > 2) & (durations <= 10)).sum()
    medium = ((durations > 10) & (durations <= 60)).sum()
    long_trades = (durations > 60).sum()
    print(f"\n  <= 2 min:   {very_short} ({very_short/len(durations)*100:.1f}%)")
    print(f"  2-10 min:   {short} ({short/len(durations)*100:.1f}%)")
    print(f"  10-60 min:  {medium} ({medium/len(durations)*100:.1f}%)")
    print(f"  > 60 min:   {long_trades} ({long_trades/len(durations)*100:.1f}%)")
print()

# === MFE/MAE ANALYSIS ===
print("="*70)
print("MFE/MAE ANALYSIS (Maximum Favorable/Adverse Excursion)")
print("="*70)
print(f"Winners:")
print(f"  Avg MFE: ${winners['MFE'].mean():.2f} ({winners['MFE_pct'].mean():.2f}%)")
print(f"  Avg MAE: ${winners['MAE'].mean():.2f} ({winners['MAE_pct'].mean():.2f}%)")
print(f"Losers:")
print(f"  Avg MFE: ${losers['MFE'].mean():.2f} ({losers['MFE_pct'].mean():.2f}%)")
print(f"  Avg MAE: ${losers['MAE'].mean():.2f} ({losers['MAE_pct'].mean():.2f}%)")
print()

# Losers that saw green (LSG)
losers_saw_green = losers[losers['MFE'] > 0]
print(f"Losers that saw green (MFE > 0): {len(losers_saw_green)}/{len(losers)} ({len(losers_saw_green)/len(losers)*100:.1f}%)")
if len(losers_saw_green) > 0:
    print(f"  Avg MFE before losing: ${losers_saw_green['MFE'].mean():.2f}")
    print(f"  These losers could have been saved with tighter exit")
print()

# === EQUITY CURVE ANALYSIS ===
print("="*70)
print("EQUITY CURVE - KEY DRAWDOWN EVENTS")
print("="*70)
trades['CumPnL'] = trades['Cumulative P&L USD'].astype(float)
trades['CumPnL_pct'] = trades['Cumulative P&L %'].astype(float)

# Find steepest drawdown periods
peak = trades['CumPnL'].expanding().max()
drawdown = trades['CumPnL'] - peak

# Rolling 50-trade P&L
if len(trades) >= 50:
    trades['Rolling50'] = trades['PnL'].rolling(50).sum()
    worst_50 = trades['Rolling50'].min()
    worst_50_idx = trades['Rolling50'].idxmin()
    worst_50_trade = trades.loc[worst_50_idx, 'Trade #']
    print(f"Worst 50-trade streak: ${worst_50:.2f} ending at trade #{worst_50_trade}")

# When did the account cross key thresholds?
for threshold in [-1000, -2500, -5000, -7500, -9000]:
    cross = trades[trades['CumPnL'] <= threshold]
    if len(cross) > 0:
        first = cross.iloc[0]
        print(f"Crossed ${threshold}: Trade #{first['Trade #']} at {first['DateTime']}")

print()

# === DIRECTION ANALYSIS ===
print("="*70)
print("DIRECTION ANALYSIS")
print("="*70)
longs = trades[trades['Type'].str.contains('long', case=False)]
shorts = trades[trades['Type'].str.contains('short', case=False)]
print(f"Long exits:  {len(longs)} | PnL ${longs['PnL'].sum():.2f} | WR {(longs['PnL']>0).mean()*100:.1f}%")
print(f"Short exits: {len(shorts)} | PnL ${shorts['PnL'].sum():.2f} | WR {(shorts['PnL']>0).mean()*100:.1f}%")
print()

# === CONSECUTIVE LOSSES ===
print("="*70)
print("CONSECUTIVE LOSSES")
print("="*70)
is_loss = (trades['PnL'] < 0).astype(int).values
max_streak = 0
current_streak = 0
streaks = []
for val in is_loss:
    if val == 1:
        current_streak += 1
    else:
        if current_streak > 0:
            streaks.append(current_streak)
        current_streak = 0
if current_streak > 0:
    streaks.append(current_streak)

if streaks:
    print(f"Max consecutive losses: {max(streaks)}")
    print(f"Avg losing streak: {np.mean(streaks):.1f}")
    print(f"Streaks > 10: {sum(1 for s in streaks if s > 10)}")
    print(f"Streaks > 20: {sum(1 for s in streaks if s > 20)}")
print()

# === COMMISSION IMPACT ===
print("="*70)
print("COMMISSION IMPACT")
print("="*70)
total_commission = len(trades) * 16  # $8 per side x 2
gross_pnl = trades['PnL'].sum() + total_commission  # estimate gross
print(f"Estimated total commission ($16 RT x {len(trades)} trades): ${total_commission:,.2f}")
print(f"Net P&L: ${trades['PnL'].sum():,.2f}")
print(f"Estimated gross P&L: ${gross_pnl:,.2f}")
print(f"Commission as % of losses: {total_commission / abs(trades['PnL'].sum()) * 100:.1f}%")
print()

# === HOURLY ANALYSIS ===
print("="*70)
print("HOURLY P&L (worst hours)")
print("="*70)
trades['Hour'] = trades['DateTime'].dt.hour
hourly = trades.groupby('Hour').agg(
    count=('PnL', 'count'),
    total_pnl=('PnL', 'sum'),
    avg_pnl=('PnL', 'mean'),
    win_rate=('PnL', lambda x: (x > 0).mean() * 100)
).sort_values('total_pnl')
print(hourly.to_string())
print()

# === SUMMARY DIAGNOSIS ===
print("="*70)
print("ROOT CAUSE DIAGNOSIS")
print("="*70)

problems = []

if len(margin_calls) > 0:
    problems.append(f"MARGIN CALLS: {len(margin_calls)} trades hit margin call — pyramiding is overleveraging")

if len(tiny) > 0:
    problems.append(f"POSITION DEGRADATION: {len(tiny)} trades with <$100 position — account depleted but still trading")

if len(winners)/len(trades) < 0.25:
    problems.append(f"WIN RATE CRITICAL: {len(winners)/len(trades)*100:.1f}% — 3-stage SL may be too wide, entries too frequent")

if total_commission > abs(gross_pnl) * 0.3:
    problems.append(f"COMMISSION BLEED: ${total_commission:,.0f} in commissions on {len(trades)} trades")

avg_winner = winners['PnL'].mean() if len(winners) > 0 else 0
avg_loser = abs(losers['PnL'].mean()) if len(losers) > 0 else 1
if avg_winner < avg_loser:
    problems.append(f"NEGATIVE EXPECTANCY: Avg win ${avg_winner:.2f} < Avg loss ${avg_loser:.2f} — SL wider than profits captured")

if 'Duration_min' in trades.columns:
    if durations.median() <= 5:
        problems.append(f"TRADES TOO SHORT: Median duration {durations.median():.0f} min — not enough time to run")

for i, p in enumerate(problems, 1):
    print(f"  {i}. {p}")

print()
print("="*70)
print("ANALYSIS COMPLETE")
print("="*70)
