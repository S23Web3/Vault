# ni9htw4lker — Pine Script Trading Indicators

A collection of TradingView Pine Script v6 indicators built around the **Four Pillars** trading framework. These indicators work together to provide a systematic approach to trade entry, position management, and risk control for crypto and equities.

---

## Four Pillars Framework

| Pillar | Concept | Indicator |
|--------|---------|-----------|
| 1 | **Price Structure** | Ripster EMA Clouds |
| 2 | **Directional Bias** | AVWAP Anchor Assistant |
| 3 | **Momentum** | Quad Rotation Stochastic |
| 4 | **Volatility** | BBWP (Bollinger Band Width Percentile) |

---

## Repository Structure

```
indicators/
  four-pillars/          # Core entry system — combines all 4 pillars
  quad-rotation-stochastic/  # Momentum rotation detection (Pillar 3)
  supporting/            # Individual pillar indicators + utilities
  experimental/          # Work-in-progress indicators
docs/                    # Build guidance and specifications
```

---

## Indicators

### Four Pillars (Entry System)

| File | Version | Description |
|------|---------|-------------|
| `four_pillars_v3_4.pine` | **v3.4 (Latest)** | Dynamic ATR position management with phased SL/TP, Cloud 2 hard close, ADD signals, A/B trade grading |
| `four_pillars_v3.pine` | v3.3 | Clean quad rotation entry logic with static SL/TP |
| `four_pillars_v2.pine` | v2.0 | Original combined indicator — all 4 pillars in one |
| `four_pillars_v2_strategy.pine` | v2.0 | Strategy version of v2 for backtesting |

**v3.4 Features:**
- **A trades** (4/4 stochastic alignment) and **B trades** (3/4 alignment) with distinct labels
- **Phased SL/TP management:**
  - Phase 0: Static SL/TP at entry (2x / 4x ATR)
  - Phase 1: Cloud 2 (EMA 5/12) cross — SL anchored to candle, TP expands
  - Phase 2: Cloud 3 (EMA 34/50) fresh cross — SL + TP shift 1 ATR
  - Phase 3: Cloud 3 + Cloud 4 sync — continuous cloud-based ATR trail, TP removed
- **Cloud 2 hard close** — EMA 5/12 flip against trade = immediate exit
- **ADD signals** — 9-3 stochastic pullback within trend (pyramiding)
- Ripster Clouds 2/3/4 with toggle visibility
- Full dashboard with phase, entries, trade grade, cloud status

### Quad Rotation Stochastic (Momentum — Pillar 3)

| File | Version | Description |
|------|---------|-------------|
| `Quad-Rotation-Stochastic-v4-CORRECTED.pine` | **v4.3 (Latest)** | Fixed agreement logic, smoothing, flip detection |
| `Quad-Rotation-Stochastic-v4.pine` | v4.1 | Original v4 release |
| `Quad-Rotation-Stochastic-FAST-v1.4.pine` | v1.4 | Fast variant with divergence detection and price chart visuals |
| `Quad-Rotation-Stochastic-FAST-v1.3.pine` | v1.3 | Fast variant without trend filter |
| `Quad-Rotation-Stochastic-FAST.pine` | v1.4 | Fast variant (duplicate of v1.4) |

**Stochastic Settings (John Kurisko / DayTraderRockStar HPS):**

| Stochastic | K | Smooth | Type | Role |
|------------|---|--------|------|------|
| 9-3 | 9 | 3 | Fast | Entry timing trigger |
| 14-3 | 14 | 3 | Fast | Confirmation |
| 40-3 | 40 | 3 | Fast | Primary divergence |
| 60-10 | 60 | 10 | Full | Macro filter |

### Supporting Indicators

| File | Pillar | Description |
|------|--------|-------------|
| `ripster_ema_clouds_v6.pine` | 1 — Structure | 5 EMA cloud pairs for multi-timeframe trend analysis |
| `avwap_anchor_assistant_v1.pine` | 2 — Bias | Identifies high-quality AVWAP anchor points (Brian Shannon + Wyckoff VSA) |
| `bbwp_v2.pine` | 4 — Volatility | BBWP with 6 volatility states (Blue Double to Red Double) |
| `bbwp_caretaker_v6.pine` | 4 — Volatility | The_Caretaker's BBWP upgraded to Pine Script v6 |
| `atr_position_manager_v1.pine` | Utility | ATR-based position sizing and SL/TP management |
| `Dashboard-Framework-v3.pine` | Utility | Visual trade entry checklist and grading dashboard |

### Experimental

| File | Description |
|------|-------------|
| `liquidity-farming-detector.pine` | Detects liquidity farming patterns using Ripster EMA Cloud parameters |

---

## Ripster EMA Cloud Reference

Used throughout the system for phase triggers and trend confirmation:

| Cloud | Short EMA | Long EMA | Role |
|-------|-----------|----------|------|
| Cloud 1 | EMA 8 | EMA 9 | Entry timing |
| Cloud 2 | EMA 5 | EMA 12 | Fast momentum / Phase 1 trigger / Exit signal |
| Cloud 3 | EMA 34 | EMA 50 | Medium trend / Phase 2 trigger / Ripster filter |
| Cloud 4 | EMA 72 | EMA 89 | Slow trend / Phase 3 trigger |
| Cloud 5 | EMA 180 | EMA 200 | Macro trend reference |

---

## Setup

1. Open TradingView and go to Pine Editor
2. Copy the contents of a `.pine` file
3. Paste into the Pine Editor and click "Add to Chart"
4. Configure settings via the indicator's Settings panel

**Recommended chart setup:**
- Start with `four_pillars_v3_4.pine` as the core indicator
- Add `Quad-Rotation-Stochastic-v4-CORRECTED.pine` in a separate pane for momentum visualization
- Optionally add `bbwp_v2.pine` for volatility context

---

## Docs

- [ATR SL/TP Movement Build Guidance](docs/ATR-SL-MOVEMENT-BUILD-GUIDANCE.md) — Specification for the phased position management system in Four Pillars v3.4

---

## Platform

- **Pine Script v6** — All indicators target the latest TradingView Pine Script version
- **TradingView** — Designed for TradingView charting platform
- **Asset class** — Primarily crypto, also applicable to equities and futures

---

## License

Private repository. All rights reserved.
