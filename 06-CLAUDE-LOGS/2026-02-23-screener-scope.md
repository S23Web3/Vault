# Screener — Scope Log
**Date:** 2026-02-23
**Session start:** 2026-02-23 (BingX connector build session)
**Prompted by:** Need to populate `coins:` list in BingX connector config.yaml

---

## Context

BingX connector is live-ready (56/65 tests passing, FourPillarsV384 plugin built).
The immediate problem: which coins go in `config.yaml`? Manual selection is not scalable.
User: "build some kind of screener. vince needs to help with that."

This log tracks the screener concept from initial idea through build.

---

## Initial Concept

A screener is a tool that runs across some or all of the 399 backtested coins and outputs a ranked/filtered list of coins suitable for live trading right now. It bridges Vince (research) and the BingX connector (execution).

Fits naturally into Vince as a new mode or standalone pipeline stage.

---

## Open Questions (to be resolved in this session)

- [ ] Frequency: batch (weekly/monthly re-run) or live (continuous ATR/vol check)?
- [ ] Criteria: what makes a coin suitable? Historical PnL? Current ATR? Volume? All three?
- [ ] Output: suggest coins to user (manual update config.yaml) or auto-update config.yaml?
- [ ] Scope: all 399 coins, or just the coins already backtested with good results?
- [ ] Vince integration: new Vince mode/tab, or standalone script?

---

## Decisions Log

### 2026-02-23 — Initial scope answers
- **Frequency**: Live continuous filter — screener runs at bot startup + daily reset to produce active coin list; connector uses the list
- **Criteria**: ATR ratio (commission viability) + recent performance (last 30/60 days backtest) + volume/liquidity + additional conditions TBD
- **Integration**: Vince dashboard — new Screener tab
- **Historical PnL (all-time)**: NOT selected — recency matters more than full-history average

### Open
- Lookback period: 30 days or 60 days? (user said "30/60" — default TBD)
- Connector integration: reads `active_coins.json` from screener output, or still manual config.yaml update?
- Dashboard version: `dashboard_v391.py` — need to read before touching
