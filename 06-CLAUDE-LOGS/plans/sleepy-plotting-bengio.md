# Plan: BingX Dashboard v1-3 Patches 6 + 7

**Date**: 2026-03-02
**Session log**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md`

---

## Context

Patch 5 applied comprehensive class-based dark CSS. One root cause remained: Dash 2.x injects CSS custom properties (variables) into `:root` via its own `dcc.css`, overriding all class-based rules. The white backgrounds (date pickers, dropdown menus, calendar popups) come from `--Dash-Fill-Inverse-Strong: #fff`. Class-level `!important` cannot override CSS variables — must override at `:root`.

Separately, user wants a live bot status feed in the Operational tab showing startup lifecycle messages ("Connecting", "Warmup 50/100", "Strategy loaded", etc.).

---

## Patch 6 — CSS Variables Override

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch6.py`

**Files changed**: `assets/dashboard.css` only. No Python changes.

### Steps

1. Read `assets/dashboard.css`
2. Guard check: if `--Dash-Fill-Inverse-Strong` already in file → skip, print "already applied"
3. Create timestamped backup: `dashboard.{YYYYMMDD_HHMMSS}.bak.css`
4. Append this block (with a section comment):

```css
/* === Patch 6: Override Dash 2.x :root CSS variables (dark theme) === */
:root {
    --Dash-Fill-Inverse-Strong: #21262d !important;
    --Dash-Fill-Inverse-Weak: rgba(33, 38, 45, 0.9) !important;
    --Dash-Fill-Interactive-Weak: rgba(33, 38, 45, 0.5) !important;
    --Dash-Fill-Primary-Hover: rgba(88, 166, 255, 0.1) !important;
    --Dash-Fill-Primary-Active: rgba(88, 166, 255, 0.2) !important;
    --Dash-Text-Primary: #c9d1d9 !important;
    --Dash-Text-Weak: #8b949e !important;
    --Dash-Stroke-Strong: #484f58 !important;
    --Dash-Stroke-Weak: rgba(72, 79, 88, 0.3) !important;
    --Dash-Fill-Interactive-Strong: #58a6ff !important;
    --Dash-Text-Disabled: #484f58 !important;
}
```

5. Report PASS/FAIL

### Verification
Run `python scripts/build_dashboard_v1_3_patch6.py` → check output is PASS.
Restart dashboard → open any date picker or dropdown → confirm dark background.

---

## Patch 7 — Bot Status Feed

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch7.py`

**Files changed** (4 files):
- `main.py` — add `write_bot_status()` helper + 7 calls at startup milestones
- `data_fetcher.py` — add `progress_callback=None` param to `warmup()` for per-symbol progress
- `bingx-live-dashboard-v1-3.py` — add Interval, Store, UI panel, 2 callbacks
- `assets/dashboard.css` — append status feed panel styles

---

### `bot-status.json` Schema

Written to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bot-status.json`:

```json
{
    "bot_start": "2026-03-02T14:00:00.000000+00:00",
    "messages": [
        {"ts": "2026-03-02T14:00:00.123456+00:00", "msg": "Starting bot..."},
        {"ts": "2026-03-02T14:00:01.234567+00:00", "msg": "Config loaded: 47 coins, 5m"},
        {"ts": "2026-03-02T14:00:02.345678+00:00", "msg": "Strategy loaded: four_pillars_v384"},
        {"ts": "2026-03-02T14:00:03.456789+00:00", "msg": "Connected to BingX API"},
        {"ts": "2026-03-02T14:00:04.567890+00:00", "msg": "Warming up 47 symbols..."},
        {"ts": "2026-03-02T14:00:05.678901+00:00", "msg": "Warmup 10/47"},
        {"ts": "2026-03-02T14:00:30.789012+00:00", "msg": "Warmup complete (47 symbols)"},
        {"ts": "2026-03-02T14:00:31.890123+00:00", "msg": "Bot running"}
    ]
}
```

Written atomically (write to temp file → `os.replace()`) to avoid partial reads during dashboard poll.

---

### `main.py` Changes

Add helper function near top of file (after imports):

```python
def write_bot_status(msg, status_path):
    """Append a timestamped message to bot-status.json. Atomic write."""
    now = datetime.now(timezone.utc).isoformat()
    data = {"bot_start": now, "messages": []}
    if status_path.exists():
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    if "messages" not in data:
        data["messages"] = []
    data["messages"].append({"ts": now, "msg": msg})
    tmp = status_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, status_path)
```

Add `STATUS_PATH = BOT_ROOT / "bot-status.json"` constant near top.

**7 call sites in `main()` startup sequence** (mapped to known line ranges):

| After line | Status message |
|-----------|----------------|
| Config loaded (~186) | `"Config loaded: {n} coins, {tf}"` |
| `StrategyAdapter()` (~202) | `"Strategy loaded: {plugin_name}"` |
| `fetch_commission_rate()` (~215) | `"Connected to BingX API"` |
| `StateManager.reconcile()` (~239) | `"Positions reconciled"` |
| Before `feed.warmup()` (241) | `"Warming up {n} symbols..."` |
| After `feed.warmup()` | `"Warmup complete ({n} symbols)"` |
| After threads started (~268) | `"Bot running"` |

Also: overwrite `bot-status.json` fresh at process start (before any messages) so stale messages from last run are cleared.

---

### `data_fetcher.py` Changes

Add `progress_callback=None` to `warmup()` signature. After each successful symbol fetch, call `progress_callback(i+1, total)` if not None:

```python
def warmup(self, progress_callback=None):
    """Initial fetch for all symbols at startup."""
    total = len(self.symbols)
    for i, symbol in enumerate(self.symbols):
        df = self._fetch_klines(symbol)
        if df is not None:
            self.buffers[symbol] = df
            if len(df) >= 2:
                self.last_bar_ts[symbol] = int(df.iloc[-2]["time"])
            logger.info("Warmup %s: %d bars", symbol, len(df))
        else:
            logger.warning("Warmup failed for %s", symbol)
        if progress_callback and (i + 1) % 5 == 0:
            progress_callback(i + 1, total)
```

Call in `main.py`: `feed.warmup(progress_callback=lambda i, n: write_bot_status(f"Warmup {i}/{n}", STATUS_PATH))`

Progress fires every 5 symbols (not every symbol, to avoid flooding the file).

---

### Dashboard Changes (`bingx-live-dashboard-v1-3.py`)

**Layout additions** (same `safe_replace` pattern):

1. Add to `dcc.Store` list: `dcc.Store(id='store-bot-status', data=[])`
2. Add to layout: `dcc.Interval(id='status-interval', interval=5000, n_intervals=0)` (5s poll)
3. In `make_operational_tab()`: add status feed panel below positions grid:

```python
html.Div([
    html.H4("Bot Status", style={'color': COLORS['muted'], 'fontSize': '13px',
                                  'marginTop': '16px', 'marginBottom': '6px'}),
    html.Div(id='status-feed', className='status-feed-panel'),
])
```

**New callback CB-S1** — load status from file:
- Input: `status-interval.n_intervals`
- Output: `store-bot-status.data`
- Reads `bot-status.json`, returns messages list (last 20 reversed = newest first)
- Returns `[]` if file missing (bot offline)

**New callback CB-S2** — render status feed:
- Input: `store-bot-status.data`
- Output: `status-feed.children`
- If empty → `html.P("Bot offline", style={'color': COLORS['muted']})`
- Else: list of `html.P([html.Span(ts, class='status-ts'), " ", msg])` per entry, newest first

---

### CSS additions for status feed (appended to `assets/dashboard.css`):

```css
/* === Patch 7: Bot status feed panel === */
.status-feed-panel {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 10px 14px;
    font-family: monospace;
    font-size: 12px;
    max-height: 180px;
    overflow-y: auto;
    color: #c9d1d9;
}
.status-feed-panel p {
    margin: 2px 0;
    line-height: 1.5;
}
.status-ts {
    color: #484f58;
    margin-right: 8px;
}
```

---

## Run Commands

```
# Patch 6 (CSS variables)
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch6.py"

# Restart dashboard to verify dark date pickers/dropdowns
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-3.py"

# Patch 7 (bot status feed)
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch7.py"

# Restart bot to generate bot-status.json
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"

# Restart dashboard to see status feed
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-3.py"
```

## Critical Files

| File | Role |
|------|------|
| `scripts/build_dashboard_v1_3_patch6.py` | NEW — CSS-only patch script |
| `scripts/build_dashboard_v1_3_patch7.py` | NEW — bot status feed patch script |
| `assets/dashboard.css` | Modified by both patches (append only) |
| `bingx-live-dashboard-v1-3.py` | Modified by patch7 (2 stores, 1 interval, 2 callbacks, 1 UI div) |
| `main.py` | Modified by patch7 (1 helper fn + 7 calls + STATUS_PATH constant) |
| `data_fetcher.py` | Modified by patch7 (progress_callback param in warmup) |
