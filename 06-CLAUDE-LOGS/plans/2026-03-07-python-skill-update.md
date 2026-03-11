# Plan: Python Skill Update
**Date:** 2026-03-07
**Status:** READY TO IMPLEMENT

---

## Context

The Python skill (`SKILL.md`) has two files:
- `C:\Users\User\.claude\skills\python\SKILL.md` — the authoritative working reference (664 lines)
- `C:\Users\User\.claude\skills\python\python-trading-development.md` — an older, weaker version (533 lines) using emojis and print-based patterns

SKILL.md is already solid but is missing several lessons discovered during the research scope (strategy builds, BingX v2 mechanical audit, dashboard v3 build, strategy-catalogue session). This plan captures all gaps and adds them.

---

## What to Update in SKILL.md

### 1. New Build Trap: `\\n` in Triple-Quoted Build Content

Discovered: 2026-03-07 strategy-catalogue session.

When a build script writes Python source as a triple-quoted string, `\\n` inside that string becomes literal `\n` in the output file — producing an unterminated string literal SyntaxError.

```python
# TRAP — \\n in triple-quoted content writes literal \n to output
content = """
title = "S1 ...\nMarket Read: ..."
"""
# Output file: title = "S1 ...\nMarket Read..." — INVALID

# FIX — use inline string concatenation or | separator
content = """
title = "S1 ... | Market Read: ..."
"""
```

**Rule addition:** When build script writes Python source, NEVER use `\\n` inside string literals in the output. Abandon the build script pattern if the output strings require embedded newlines — use Write tool directly instead.

**Also add:** `py_compile` MUST be run on the OUTPUT file, not just the build script. The build script can compile clean while its output is broken.

---

### 2. Dual Validation: py_compile + ast.parse ON THE OUTPUT FILE

Currently documented for build scripts to call `py_compile` on output. Needs emphasis:

- Run `py_compile` on output file (catches syntax errors)
- Run `ast.parse` on output file (catches f-string expression errors)
- BOTH must pass before the session is considered complete

```python
import ast, py_compile
from pathlib import Path

def validate_output(path: str) -> bool:
    """py_compile + ast.parse on a written .py file."""
    # Step 1: py_compile
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        print("SYNTAX ERROR: " + str(e))
        return False
    # Step 2: ast.parse
    try:
        source = Path(path).read_text(encoding="utf-8")
        ast.parse(source, filename=path)
    except SyntaxError as e:
        print("AST ERROR line " + str(e.lineno) + ": " + str(e.msg))
        return False
    print("VALIDATE OK: " + path)
    return True
```

---

### 3. Upgrade the Common Gotchas Table

Add the `\\n` build trap row:

| `\\n` in build content string | `SyntaxError: unterminated string literal` in OUTPUT file | Never use `\\n` inside triple-quoted content; use Write tool directly |

---

### 4. Build Script Pattern Decision Rule

Add a new subsection under "Syntax Error Prevention":

**When to use a build script vs. Write tool directly:**

- Build script is appropriate when: the output files are simple (no embedded newlines in string literals, no complex f-strings with join operations).
- Write tool directly is appropriate when: the output file contains complex multi-line string literals, embedded newlines, or formatting that would require escaping inside triple-quoted build content.
- The cost of a broken build script (debugging escaped content) is higher than the cost of writing the output directly.

---

### 5. BingX/Exchange API Lessons

Add new subsection under "Trading System Specifics":

```python
# Exchange API — always sync server time first
# BingX 109400 "timestamp is invalid" = local clock drift > 5s
# Immediate fix: w32tm /resync /force (Windows)
# Permanent fix: time_sync module that fetches server time and maintains offset

# API rate limit with many positions
# allOrders limit must be >= max_positions * 2
# Default limit=20 breaks when 47+ coins push fills outside the window
# Always set limit explicitly: limit=50 or higher for production bots
```

---

### 6. Common Gotchas Table — Add Two Rows

| `allOrders` limit too low | Missing fills, `EXIT_UNKNOWN` for filled positions | Set `limit >= max_positions * 2` |
| cancel-then-place SL | Naked position window (35-60s) between cancel and new SL | Always place-then-cancel: place new SL first, cancel old after confirming new is live |

---

### 7. Consolidate and Remove the Old File

`python-trading-development.md` duplicates SKILL.md with worse content (uses emojis, uses `print()` instead of `logging`, weaker patterns). Plan: **replace its content with a redirect** pointing to SKILL.md, so the skill loader always gets one authoritative source.

---

## Files to Modify

1. `C:\Users\User\.claude\skills\python\SKILL.md` — add sections 1-6 above
2. `C:\Users\User\.claude\skills\python\python-trading-development.md` — replace content with one-line redirect to SKILL.md

---

## What Is NOT Changing

- All existing content in SKILL.md stays as-is — these are additions only
- Code patterns, checklist, template — unchanged
- No structural reorganization

---

## Verification

After writing:
1. Read SKILL.md back — confirm all 6 additions are present with correct formatting
2. Read python-trading-development.md back — confirm redirect only
3. No py_compile needed (these are .md files)