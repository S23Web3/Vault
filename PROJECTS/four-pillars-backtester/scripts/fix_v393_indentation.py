"""
Fix dashboard_v393.py indentation after adding nested if check.

The v393 file has a new 'if _pd is not None:' at line 1969, but all the subsequent
code in that block needs to be indented by 4 spaces.

This script:
1. Finds the 'if _pd is not None:  # Only proceed' line
2. Indents all following lines by 4 spaces
3. Stops indenting when it hits the next mode section (outside the if _pd block)
4. Writes the corrected file

Run: python scripts/fix_v393_indentation.py
"""
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V393 = ROOT / "scripts" / "dashboard_v393.py"

print("Reading v393...")
lines = V393.read_text(encoding="utf-8").splitlines()

print("Finding nested if check line...")
start_line = None
for i, line in enumerate(lines):
    if "if _pd is not None:  # Only proceed if cache is still valid" in line:
        start_line = i
        print("Found at line " + str(i + 1))
        break

if start_line is None:
    print("ERROR: Could not find 'if _pd is not None:  # Only proceed' line")
    exit(1)

# Find the end of the if _pd block
# The nested 'if _pd is not None:' line is at indent 8 (2 levels in)
# We need to indent everything until we dedent back to column 4 or less
# (which is the level of the OUTER 'if _pd is not None' block)
if_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
print("Nested if statement is at indent level: " + str(if_indent))
print("Looking for dedent to level 4 or less (outer if _pd block level)...")

end_line = None
for i in range(start_line + 1, len(lines)):
    line = lines[i]
    # Empty lines continue
    if not line.strip():
        continue
    # Dedent to column 4 or less ends the block (back to outer if level or less)
    curr_indent = len(line) - len(line.lstrip())
    if curr_indent < 8:
        end_line = i
        print("Block ends at line " + str(i + 1) + " (dedent to level " + str(curr_indent) + ")")
        break

if end_line is None:
    # Block goes to end of file
    end_line = len(lines)
    print("Block extends to end of file")

# Now indent lines from start_line+1 to end_line-1 by 4 spaces
print("Indenting lines " + str(start_line + 2) + " to " + str(end_line) + "...")
indented_count = 0
for i in range(start_line + 1, end_line):
    # Don't indent empty lines
    if lines[i].strip():
        lines[i] = "    " + lines[i]
        indented_count += 1

print("Indented " + str(indented_count) + " lines")

# Write back
print("Writing corrected file...")
V393.write_text("\n".join(lines), encoding="utf-8")

# Syntax check
print("Syntax check...")
try:
    py_compile.compile(str(V393), doraise=True)
    print("SYNTAX OK")
except py_compile.PyCompileError as e:
    print("SYNTAX ERROR:")
    print(str(e))
    exit(1)

print("=" * 60)
print("FIX COMPLETE")
print("=" * 60)
print("File: " + str(V393))
print("Indented: " + str(indented_count) + " lines")
