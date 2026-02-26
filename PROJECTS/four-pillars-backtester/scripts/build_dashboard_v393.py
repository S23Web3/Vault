"""
Build script for dashboard v3.9.3 - Equity curve date filter bug fix.

Applies a 4-line patch to dashboard_v392.py:
- Clears stale session state when settings change
- Prevents displaying equity curves from previous date ranges
- Maintains clean UX by using natural control flow skip

Run: python scripts/build_dashboard_v393.py
"""
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V392 = ROOT / "scripts" / "dashboard_v392.py"
V393 = ROOT / "scripts" / "dashboard_v393.py"

print("=" * 60)
print("Building dashboard v3.9.3")
print("=" * 60)

# Check source exists
if not V392.exists():
    print("ERROR: Source file not found: " + str(V392))
    sys.exit(1)

# Check target doesn't exist
if V393.exists():
    print("ERROR: Target already exists: " + str(V393))
    print("Delete it first or use a different version number.")
    sys.exit(1)

print("Reading v392 source...")
content = V392.read_text(encoding="utf-8")

print("Applying bug fix...")

# Apply fix (replace lines 1963-1964)
OLD = """        if _stored_hash and (_current_hash != _stored_hash or _cap_changed or _margin_changed):
            st.warning("Sidebar settings changed since last run. Click **Run Portfolio Backtest** to update results.")
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

content = content.replace(OLD, NEW, 1)  # Replace only first occurrence

# Update version in header
content = content.replace("v3.9.2", "v3.9.3", 1)  # First occurrence in docstring
content = content.replace("Four Pillars v3.9.2", "Four Pillars v3.9.3", 1)

print("Writing v393...")
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
print("")
print("Test scenario:")
print("1. Run portfolio with All dates")
print("2. Change to custom: 2025-07-09 to 2025-07-25")
print("3. VERIFY: Info message appears, stale charts cleared")
print("4. Click 'Run Portfolio Backtest'")
print("5. VERIFY: Equity curve shows Jul 9-25 dates only")
