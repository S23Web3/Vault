"""
Build script for dashboard v3.9.3 - CORRECTED VERSION.

The first build had a bug: after setting _pd = None, the code immediately tries to
access _pd["pf"] which would crash. This version adds the nested if check.

Run: python scripts/build_dashboard_v393_fix.py
"""
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V393_BROKEN = ROOT / "scripts" / "dashboard_v393.py"
V393 = ROOT / "scripts" / "dashboard_v393_fixed.py"

print("=" * 60)
print("Building dashboard v3.9.3 - CORRECTED")
print("=" * 60)

# Check source exists
if not V393_BROKEN.exists():
    print("ERROR: Source file not found: " + str(V393_BROKEN))
    sys.exit(1)

print("Reading v393 (broken)...")
content = V393_BROKEN.read_text(encoding="utf-8")

print("Applying nested if check fix...")

# Fix: add nested if _pd is not None check after setting to None
OLD = """        if _stored_hash and (_current_hash != _stored_hash or _cap_changed or _margin_changed):
            # BUG FIX v3.9.3: Clear stale portfolio data when settings change
            # Prevents displaying equity curves from previous date ranges
            st.session_state["portfolio_data"] = None
            _pd = None  # Update local var to trigger natural skip below
            st.info("Settings changed. Click **Run Portfolio Backtest** to generate new results.")
        pf = _pd["pf"]"""

NEW = """        if _stored_hash and (_current_hash != _stored_hash or _cap_changed or _margin_changed):
            # BUG FIX v3.9.3: Clear stale portfolio data when settings change
            # Prevents displaying equity curves from previous date ranges
            st.session_state["portfolio_data"] = None
            _pd = None  # Update local var to trigger natural skip below
            st.info("Settings changed. Click **Run Portfolio Backtest** to generate new results.")

        if _pd is not None:  # Only proceed if cache is still valid
            pf = _pd["pf"]"""

if OLD not in content:
    print("ERROR: Could not find target code to replace.")
    print("Expected to find:")
    print(OLD)
    sys.exit(1)

content = content.replace(OLD, NEW, 1)

# Need to indent all subsequent lines by 4 spaces until we hit the mode switch section
# Find the end of the portfolio rendering block
MARKER_START = "        if _pd is not None:  # Only proceed if cache is still valid"
MARKER_END = "# --- MODE ROUTING ---"

start_idx = content.find(MARKER_START)
if start_idx == -1:
    print("ERROR: Could not find start marker")
    sys.exit(1)

end_idx = content.find(MARKER_END, start_idx)
if end_idx == -1:
    print("ERROR: Could not find end marker")
    sys.exit(1)

# Split content into before, middle, and after
before = content[:start_idx]
middle_section = content[start_idx:end_idx]
after = content[end_idx:]

# Indent the middle section (except the first line which is the if statement)
lines = middle_section.split("\\n")
indented_lines = [lines[0]]  # Keep first line as-is
for line in lines[1:]:
    if line and not line.startswith("# ---"):
        indented_lines.append("    " + line)  # Add 4 spaces
    else:
        indented_lines.append(line)

middle_indented = "\\n".join(indented_lines)

# Reconstruct
content = before + middle_indented + after

print("Writing v393 (fixed)...")
V393.write_text(content, encoding="utf-8")

print("Syntax check...")
try:
    py_compile.compile(str(V393), doraise=True)
    print("SYNTAX OK: " + str(V393))
except py_compile.PyCompileError as e:
    print("SYNTAX ERROR:")
    print(str(e))
    V393.unlink()  # Delete broken file
    sys.exit(1)

print("=" * 60)
print("BUILD SUCCESS")
print("=" * 60)
print("")
print("Created: " + str(V393))
print("Size: " + str(V393.stat().st_size) + " bytes")
print("")
print("Run dashboard:")
print('  streamlit run "' + str(V393) + '"')
