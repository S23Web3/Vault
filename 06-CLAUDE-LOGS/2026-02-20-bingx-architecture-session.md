# BingX Live Trading Architecture — Session Log
**Date:** 2026-02-20
**Session:** Architecture planning for live BingX deployment

## Summary

Continuation from previous API connection discussion. Goal: deploy Four Pillars strategy to live trading on BingX with $1,000 account, $50 positions.

## What Was Done

1. Searched all past logs and Obsidian vault to understand current state
2. Confirmed strategy: Four Pillars v3.8.4 (signals/state_machine.py, strategies/four_pillars_v3_8.py)
3. Confirmed existing backtester results: RIVERUSDT 5m is the primary profitable coin confirmed, batch sweep on 50 coins shows most negative at default params
4. Researched BingX Perpetual Futures API — confirmed endpoints, auth method, order structure
5. Created full architecture document

## BingX API Confirmed

- Base URL: `https://open-api.bingx.com`
- Order endpoint: `POST /openApi/swap/v2/trade/order`
- Auth: HMAC-SHA256, signature in query string as `&signature=`, API key in header `X-BX-APIKEY`
- Symbol format: `BTC-USDT` (dash-separated)
- positionSide field required: LONG / SHORT (hedge mode)
- SL/TP: attached as JSON strings in `stopLoss` and `takeProfit` fields at order placement
- Rate limit: 10 orders/second (upgraded Oct 2025)
- VST demo: `https://open-api-vst.bingx.com` (same endpoints, safe for testing)
- No passphrase needed (unlike WEEX)

## Architecture File

Saved to: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BINGX-LIVE-TRADING-ARCHITECTURE.md`

## Decision: No Code Until

1. Dashboard sweep on target coins — lock sl_atr_mult, tp_atr_mult, be_raise, grade filter
2. Coin list confirmed (minimum: positive expectancy > $1/trade at $500 notional)
3. TP vs runner decision made
4. Architecture document approved

## Open Questions (Unresolved)

- Which coins pass the sweep? (RIVER confirmed, others TBD)
- Fixed TP or runner (Cloud 4 trail)?
- Grade A only or A+B for live?
- v3.8.4 or wait for v3.8.5 with Cloud 4 trail?
- n8n needed or standalone Python bot?

## UML Documents Created (Session 2)

**Connector UML:**
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md`

Covers: C4 context, container diagram, component diagram, main loop sequence, position monitor sequence, startup sequence, risk gate decision tree, state ER diagram, config schema, strategy plugin interface, Jacky file structure, BingX API reference table.

**Strategy UML:**
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-STRATEGY-UML.md`

Covers: Silo isolation principle, strategy context, indicator computation layer, state machine statechart, grading rules flowchart, exit price calculation, class diagram (all internal components), full pipeline sequence diagram, independent test paths, variant silo testing plan, connector-strategy boundary contract.

## Key Architectural Decisions Documented

- Strategy is a black-box plugin. Connector calls `plugin.get_signal(ohlcv_df)` and receives a Signal object. That is the entire interface.
- Silo testing: each strategy variant is a separate plugin file, tested via backtester independently. Connector config just points to whichever plugin wins.
- Four test paths for strategy validation: unit tests, backtester, parameter sweep, Vince ML.
- Four strategy variants planned: v384 baseline, v384 grade-A-only, v385 Cloud4 trail, v386 Vince-filtered.

## Next Session

Run dashboard sweep on RIVERUSDT, GUNUSDT, AXSUSDT (5m). Lock sl_mult, tp_mult, grade filter, be_raise. Decide: runner vs fixed TP. That is the strategy config. Then connector build can start.

---
*Tags: #bingx #live-trading #architecture #uml #session-log #2026-02-20*
