# Python Skill Update — 2026-02-17

## Session Summary

**Task**: Review and update Python coding skill across all locations. Add filename etiquette, debugging, testing enhancements, and syntax error prevention sections.

---

## Changes Made

### 1. Vault SKILL.md — Sections Added
**File**: `C:/Users/User/Documents/Obsidian Vault/.claude/skills/python/SKILL.md`

New sections added:
- **Filename Etiquette & Location**: naming convention table, project directory structure, `safe_write_path()` versioning helper
- **Debugging**: `logging` over `print`, structured exception handling with `traceback.format_exc()`, debug script template (`debug_<module>.py`), log level discipline table
- **Testing (Enhanced)**: programmatic `py_compile.compile()` in build scripts with `ERRORS` list + `sys.exit(1)`, `unittest` structure template, `make_ohlcv()` mock data helper (deterministic seed), assert patterns with `msg=`
- **Syntax Error Prevention**: f-string join trap, triple-quoted string escaping rules table, `ast.parse()` secondary validator, common gotchas table
- **Code Patterns**: input validation, graceful degradation, API rate limiting with confirmation, OHLCV data validation, incremental processing/checkpoints, performance (parquet/vectorized)
- **Trading System Specifics**: commission calculation (rate-based), UTC timestamps
- **Common Bugs**: off-by-one, date calc, naive vs aware datetime, set_index, bare except, import *
- **Complete Script Template**: full production-ready script with logging, pathlib, checkpoints, rate limit, error collection
- **Code Review Checklist** expanded: 11 → 28 items across 5 categories (Filename, Syntax, Testing, Debugging, Quality)

### 2. User-Level SKILL.md — Created
**File**: `C:/Users/User/.claude/skills/python/SKILL.md`

- New file created (did not overwrite)
- Identical content to vault SKILL.md (full merged content)
- Legacy file `python-trading-development.md` left in place — can be deleted

### 3. MEMORY.md — Rule Added
**File**: `C:/Users/User/.claude/projects/C--Users-User-Documents-Obsidian-Vault/memory/MEMORY.md`

Added hard rule:
```
PYTHON SKILL MANDATORY — Before writing ANY Python code, scripts, or backtester work, ALWAYS load the Python skill first (/python). No exceptions. Triggers: any .py file, scripts/, tests/, build scripts, data processing.
```

MEMORY.md line count: 161 lines (under 200 limit).

---

## File Inventory

| File | Action | Status |
|------|--------|--------|
| `Vault/.claude/skills/python/SKILL.md` | Updated (sections added) | DONE |
| `C:/Users/User/.claude/skills/python/SKILL.md` | Created (new) | DONE |
| `C:/Users/User/.claude/skills/python/python-trading-development.md` | Left untouched (legacy) | DELETE WHEN READY |
| `MEMORY.md` | Rule appended | DONE |

---

## Notes
- Only 2 Python skill locations found (user expected 3 — confirmed only 2 exist)
- Filename convention: `SKILL.md` inside typed directory (e.g., `python/SKILL.md`) matches all other skills
- Both skill files now synchronized with identical content
