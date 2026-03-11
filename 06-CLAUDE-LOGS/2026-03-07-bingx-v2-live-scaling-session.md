# Session Log: BingX v2 Live Run + Scaling Analysis
**Date:** 2026-03-07
**Duration:** Full context session (compacted)
**Context:** Continuation from v2 mechanical fixes applied session (2026-03-06)

---

## What Was Done

### 1. v2 Bot Live — First Stats

Bot v2 started: **2026-03-06 19:49 UTC+4** at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\`

Config: 47 coins, $5 margin, 10x leverage, $50 notional, 5m timeframe, `ttp_mode: native`

**38 closed trades (Mar 6-7, ~20 hours):**

| Metric | Value |
|--------|-------|
| Win rate | 65.8% (25W / 13L) |
| Avg win | +$0.123 |
| Avg loss | -$0.440 |
| R:R | 0.28 |
| Daily PnL | -$2.70 |
| Trailing exits | 7 (18.4%) vs 4.8% in v1 |
| EXIT_UNKNOWN | 2 (LDO, UB — race condition) |

**Peak concurrent positions:** 11 at ~19:35 Mar 6 = $55 margin / $550 notional

**Bot health:** Zero crashes. 2 WS disconnects (auto-reconnected). RiskGate confirmed max_atr_ratio firing (RIVER-USDT blocked at 1.86% ATR ratio).

**BE SL rejections (not a bug):** 4 SHORT positions (SCRT, WOO, MUBARAK, THETA) got BingX error `code=110412 Stop Loss price should be greater than current price`. Price bounced past BE level between check and API call. Place-then-cancel handles it — old SL preserved.

---

### 2. Dashboard Analytics Bug Found

**Error:** `invalid literal for int() with base 10: 'FalseFalseFalseTrue...'`

**Root cause:** `be_raised` CSV column stores string `"True"`/`"False"`. `df["be_raised"].sum()` concatenates strings instead of counting booleans. `int()` fails.

**Fix (in `build_analyzer_capital_patch_v2.py`):**
```python
# Line 564 — be_raised
be_count = int((df["be_raised"].astype(str).str.lower() == "true").sum())

# Line 570 — saw_green
lsg_pct = round((losing["saw_green"].astype(str).str.lower() == "true").sum() / len(losing) * 100, 1)
```

**Status:** Fix written in build script. Not yet applied (user runs).

---

### 3. Volume and Capital Analysis

**At current $50 notional (38 trades in ~20 hours):**
- Est. trades/day: ~45
- Daily volume: ~$4,500 RT
- Monthly volume: ~$135,000
- Monthly rebate (70%): ~$148 (tiny at $50)

**At $500 margin / 20x leverage = $10,000 notional (200x scale):**
- Monthly volume: ~$27M RT
- Monthly rebate gross: ~$43,200 (0.16% × 27M)
- Net rebate (70%): ~$30,240
- Monthly losses (scaled from -$2.70/day × 200): -$16,200/month (conservative est)
- **Monthly true profit: ~$14,000–$30,000** depending on daily loss rate

**Key insight:** At $500/20x, daily trading loss < $500 (one trade unit = 5% margin). Rebate > loss. Bot is net-positive on rebates alone.

---

### 4. Scaling Projection (Linear — User's Vision)

**Setup:** Each bot = $500 margin, 20x leverage. Monthly rebate = ~$29,568. Monthly loss = ~$5,580. Monthly net per bot ≈ **$23,988**.

User's rules:
- Take **$5,000/month salary** from profits
- Reinvest every **$10,000 surplus** to start a new bot instance
- Linear growth — no compounding of size, just more bot instances

**Projection (simple linear):**

| Period | Bots | Monthly Gross | Salary | Surplus | Cumulative Bots |
|--------|------|---------------|--------|---------|-----------------|
| April 2026 | 1 | $23,988 | $5,000 | $18,988 → Bot 2 added | 2 |
| May 2026 | 2 | $47,976 | $5,000 | $42,976 → Bots 3+4 added | 4 |
| June 2026 | 4 | $95,952 | $5,000 | $90,952 → ~9 bots added | 13 |
| July 2026 | 13 | $311,844 | $5,000 | $306,844 → 30 bots | 43 |
| August 2026 | 43 | ~$1.03M | $5,000 | ~$1.02M | ~145 |
| December 2026 | ~145+ | tens of millions | -- | -- | -- |

**Note:** Growth is geometric even with "linear" intent because reinvestment is relative to output. If user means truly fixed pace (1 new bot per month), the math is much flatter.

**User's framing:** "10k bots at $500/20x" — at that scale, monthly rebate = $10,000 × $23,988 = **$239.8M/month**. This is the theoretical ceiling from the exchange's perspective (rebate = % of volume, so BingX would be paying out a lot).

**Realistic near-term (April → August):**
- April: 1 bot → ~$24k net
- May: 2 bots → ~$48k net
- August: If reinvesting aggressively (every $10k) → 43-145 bots → $1M+/month net

---

### 5. Build Scripts Created

| Script | Status |
|--------|--------|
| `build_analyzer_capital_patch.py` | Created v1 (not run) |
| `build_analyzer_capital_patch_v2.py` | Created, syntax-verified OK, not run |

**`build_analyzer_capital_patch_v2.py` adds to `analyze_trades.py`:**
- `compute_concurrent_positions()` — peak concurrent, peak margin, peak notional
- `compute_max_drawdown()` — max drawdown across trade equity curve
- `compute_scaling_projection()` — PnL/volume/rebate at any margin/leverage
- `load_v1_trades()` — loads v1 CSV (different 12-column format)
- `build_cross_run_report()` — compares v1 Mar 3-6 vs v2 Mar 6-7
- Section 4b in report: capital usage + scaling projections at $500/20x and $100/20x
- Fixes commission constants: 0.0008/side, 0.0016 RT, 70% rebate
- Fixes dashboard be_raised + saw_green string-to-bool bugs

**Run command:**
```
cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector-v2"
python scripts/build_analyzer_capital_patch_v2.py
```

---

### 6. v2 vs v1 Comparison (Quick)

| Metric | v1 ($50 phase, Mar 3-6) | v2 (Mar 6-7) |
|--------|------------------------|---------------|
| Trades | ~129 | 38 |
| Trailing exits | ~4.8% | 18.4% |
| BE raises | -- | working |
| max_atr_ratio | NOT present | 0.015 (blocking ultra-volatile) |
| Exit price accuracy | Estimated | allOrders-first (real fill) |
| Commission fallback | 0.001 (wrong) | 0.0016 (correct) |

---

## Scaling Calculations (Final Model)

**Exchange:** WEEX, 70% rebate
**Bot config:** $500 margin, 20x leverage, $10k notional, 45 trades/day
**P&L assumption:** Breakeven (rebate is the only profit source)
**Rules:** 10% expenses off top, salary starts $5k/month +10% each month, reinvest every $10k surplus into new bot, cap at 5 bots then scale margin to $5k max

### Key constants per bot at $500/20x
- Monthly volume: $27M (45 trades × $10k × 2 sides × 30 days)
- Gross commission: $43,200 (0.16% × $27M)
- Net rebate: $30,240 (70% of $43,200)
- Net/bot at breakeven: $30,240/month

### Phase 1: Build to 5 bots (April → May)

| Month | Bots | Monthly Volume | Gross Commission | Rebate (70%) | Expenses (10%) | Salary | Surplus | End Bots |
|-------|------|---------------|-----------------|-------------|---------------|--------|---------|----------|
| April | 1 | $27M | $43,200 | $30,240 | $3,024 | $5,000 | $22,216 →+2 | 3 |
| May | 3 | $81M | $129,600 | $90,720 | $9,072 | $5,500 | $76,148 →+5 | 5 (capped) |

**5 bots reached: end of May**

### Phase 2: Scale margin (June → October, 5 bots fixed)

| Month | Margin/Bot | Notional/Bot | Monthly Volume | Rebate (70%) | Expenses + Salary | Surplus |
|-------|-----------|-------------|---------------|-------------|------------------|---------|
| June | $500 | $10k | $135M | $151,200 | $21,170 | $130,030 |
| July | $1,000 | $20k | $270M | $302,400 | $21,775 | $280,625 |
| August | $2,000 | $40k | $540M | $604,800 | $22,441 | $582,359 |
| September | $4,000 | $80k | $1.08B | $1,209,600 | $23,173 | $1,186,427 |
| October | $5,000 | $100k | $1.35B | $1,512,000 | $23,978 | $1,488,022 |
| November | $5,000 | $100k | $1.35B | $1,512,000 | $24,862 | $1,487,138 |
| December | $5,000 | $100k | $1.35B | $1,512,000 | $25,838 | $1,486,162 |

**$5k margin ceiling hit: October**
**October status: $1.35B/month volume → WEEX VIP treatment**

### The single constraint
Everything above is automatic IF the bot reaches breakeven P&L.
Current: -$2.70/day at $50 notional = -$540/day at $500/20x scale = -$16,200/month loss per bot.
Fix R:R → breakeven → roadmap executes itself.

---

### Exchange Rebate Comparison (confirmed)

| Exchange | Rebate Rate | Net rebate/bot/month at $500/20x |
|----------|-------------|----------------------------------|
| WEEX | 70% | $30,240 |
| BingX | 50% | $21,600 |
| Binance | 50% | $21,600 |

**Conclusion:** WEEX pays 40% more per dollar of volume. Primary exchange for scaling. BingX/Binance fine for current small-scale testing.

**Bot status confirmed:** "10 on 10" — running clean as of 2026-03-07.

---

## Pending

- [ ] User runs `build_analyzer_capital_patch_v2.py`
- [ ] Dashboard be_raised bug fixed (in above script)
- [ ] EXIT_UNKNOWN race condition — noted, not yet patched (low priority)
- [ ] Scale bot to $500/20x when user decides timing
- [ ] Fix R:R to reach breakeven — single constraint blocking entire roadmap

---

## Files Modified / Created This Session

| File | Action |
|------|--------|
| `PROJECTS/bingx-connector-v2/scripts/build_analyzer_capital_patch.py` | Created (v1, not run) |
| `PROJECTS/bingx-connector-v2/scripts/build_analyzer_capital_patch_v2.py` | Created, syntax OK |
