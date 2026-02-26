import pandas as pd, numpy as np

files = {
    'AXS':   r'C:\Users\User\Downloads\4Pv3.7.1-S_BYBIT_AXSUSDT.P_2026-02-07_740ab.csv',
    'RIVER': r'C:\Users\User\Downloads\4Pv3.7.1-S_BYBIT_RIVERUSDT.P_2026-02-07_902f1.csv',
}
LEVERAGE = 20

for sym, path in files.items():
    df = pd.read_csv(path, encoding='utf-8-sig')
    exits = df[df['Type'].str.contains('Exit', case=False)].copy()
    entries = df[df['Type'].str.contains('Entry', case=False)].copy()

    trades = exits[['Trade #','Signal','Net P&L USDT','Net P&L %','Favorable excursion USDT','Adverse excursion USDT']].copy()
    ei = entries[['Trade #','Type']].copy()
    ei.columns = ['Trade #','Entry Type']
    trades = trades.merge(ei, on='Trade #', how='left')
    trades['PnL'] = trades['Net P&L USDT'] * LEVERAGE
    trades['MFE'] = trades['Favorable excursion USDT'] * LEVERAGE
    trades['MAE'] = trades['Adverse excursion USDT'] * LEVERAGE
    trades['Win'] = trades['PnL'] > 0

    print(f'\n=== {sym} — EXIT SIGNAL DEEP DIVE ===')
    for sig in trades['Signal'].unique():
        s = trades[trades['Signal'] == sig]
        w = s[s['Win']]
        l = s[~s['Win']]
        print(f'\n  [{sig}]  {len(s)} trades  |  WR: {len(w)/len(s)*100:.0f}%  |  Total: ${s["PnL"].sum():.0f}')
        print(f'    Avg PnL: ${s["PnL"].mean():.2f}  |  Avg MFE: ${s["MFE"].mean():.1f}  |  Avg MAE: ${s["MAE"].mean():.1f}')
        if len(l) > 0:
            losers_had_mfe2 = (l['MFE'] >= 2).sum()
            print(f'    Losers with MFE >= $2: {losers_had_mfe2}/{len(l)} ({losers_had_mfe2/len(l)*100:.0f}%)')
            losers_had_mfe5 = (l['MFE'] >= 5).sum()
            print(f'    Losers with MFE >= $5: {losers_had_mfe5}/{len(l)} ({losers_had_mfe5/len(l)*100:.0f}%)')

    w = trades[trades['Win']]
    if len(w) > 0:
        w_leftover = w['MFE'] - w['PnL']
        print(f'\n  WINNERS — Money left on table:')
        print(f'    Avg MFE capture: {(w["PnL"].mean()/w["MFE"].mean())*100:.0f}%')
        print(f'    Avg left on table: ${w_leftover.mean():.1f} per winner')
        print(f'    Total left on table: ${w_leftover.sum():.0f}')

    print(f'\n  MFE DISTRIBUTION (all trades):')
    for thresh in [1, 2, 3, 5, 10, 20, 50]:
        pct = (trades['MFE'] >= thresh).mean() * 100
        print(f'    MFE >= ${thresh}: {pct:.1f}%')

    l = trades[~trades['Win']]
    if len(l) > 0:
        print(f'\n  LOSER MAE DISTRIBUTION:')
        for thresh in [1, 2, 5, 10, 20, 50]:
            pct = (l['MAE'].abs() >= thresh).mean() * 100
            print(f'    MAE >= ${thresh}: {pct:.1f}% of losers')
