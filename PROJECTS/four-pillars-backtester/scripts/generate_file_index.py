"""
generate_file_index.py
Scans the ENTIRE Obsidian Vault and produces FILE-INDEX-v2.md
with full path, inferred version, created datetime, and modified datetime.

Run from VS Code / Claude Code:
    python scripts/generate_file_index.py

Output: C:\\Users\\User\\Documents\\Obsidian Vault\\FILE-INDEX-v2.md
"""

import os
import re
from datetime import datetime
from pathlib import Path

# --- Config ---
VAULT = Path(r"C:\Users\User\Documents\Obsidian Vault")
OUTPUT = VAULT / "FILE-INDEX-v2.md"

EXCLUDE_DIRS = {
    '.git', '__pycache__', '.obsidian', '.vscode', '.idea',
    '.claude', 'node_modules', '.aider',
    'data',        # parquet cache - too large / not code
    'results',     # generated outputs
    'models',      # trained model binaries
    '.git',
}

EXCLUDE_EXTS = {
    '.parquet', '.mp4', '.avi', '.mov',
    '.pdf',
    '.json',        # config/data files - include selectively if needed
    '.ipynb',
    '.backup', '.bak', '.pre_bugfix_bak',
    '.gitkeep', '.lock',
    '.pyc', '.pyo', '.pyd',
    '.bin', '.pkl', '.pt', '.pth',  # model weights
    '.zip', '.tar', '.gz',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.mp3', '.wav',
    '.db', '.sqlite',
}

EXCLUDE_FILES = {
    'nul', '.gitkeep', '.aider.input.history',
    'Untitled.canvas', 'Untitled 1.canvas',
}

# Version extraction — applied to filename stem
VERSION_PATTERNS = [
    (r'v(\d+\.\d+\.\d+)',  lambda m: f"v{m.group(1)}"),   # v3.8.4
    (r'v(\d+\.\d+)',       lambda m: f"v{m.group(1)}"),   # v3.8 / v1.0
    (r'_v(\d+)$',          lambda m: f"v{m.group(1)}"),   # suffix _v2
    (r'-v(\d+)$',          lambda m: f"v{m.group(1)}"),   # suffix -v2
    (r'v(\d+)$',           lambda m: f"v{m.group(1)}"),   # v2 at end
    (r'_(\d{3,4})$',       lambda m: f"v{m.group(1)}"),   # _383 / _384
]

def infer_version(name: str) -> str:
    stem = Path(name).stem
    for pattern, fmt in VERSION_PATTERNS:
        m = re.search(pattern, stem, re.IGNORECASE)
        if m:
            return fmt(m)
    return "—"

def top_category(rel_path: str) -> str:
    """Returns the top-level folder name relative to vault root."""
    parts = Path(rel_path).parts
    if len(parts) == 1:
        return "_root"
    return parts[0]

def collect_files():
    rows = []
    for root, dirs, files in os.walk(VAULT):
        # Prune excluded dirs in-place
        dirs[:] = sorted([
            d for d in dirs
            if d not in EXCLUDE_DIRS and not d.startswith('.')
        ])
        for fname in sorted(files):
            if fname in EXCLUDE_FILES:
                continue
            if fname.startswith('.'):
                continue
            ext = Path(fname).suffix.lower()
            if ext in EXCLUDE_EXTS:
                continue
            full = Path(root) / fname
            try:
                stat = full.stat()
                created  = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M')
                modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                size_kb  = round(stat.st_size / 1024, 1)
            except Exception:
                created = modified = "ERR"
                size_kb = 0
            rel = str(full).replace(str(VAULT) + os.sep, "")
            rows.append({
                "full_path": str(full),
                "rel":       rel,
                "category":  top_category(rel),
                "version":   infer_version(fname),
                "created":   created,
                "modified":  modified,
                "size_kb":   size_kb,
            })
    return rows

def build_md(rows):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        "# VAULT FILE INDEX v2",
        f"**Generated:** {now}  ",
        f"**Vault:** {VAULT}  ",
        f"**Script:** PROJECTS\\four-pillars-backtester\\scripts\\generate_file_index.py  ",
        f"**Total files indexed:** {len(rows)}  ",
        "",
        "> Re-run script to refresh. Do not edit manually.",
        "",
        "---",
        "",
    ]

    # Summary table of categories
    categories = sorted(set(r["category"] for r in rows))
    lines.append("## Summary")
    lines.append("")
    lines.append("| Folder | File Count |")
    lines.append("|--------|-----------|")
    for cat in categories:
        count = sum(1 for r in rows if r["category"] == cat)
        lines.append(f"| `{cat}` | {count} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Full index grouped by top-level folder
    for cat in categories:
        cat_rows = [r for r in rows if r["category"] == cat]
        display = "Vault Root" if cat == "_root" else cat
        lines.append(f"## {display}")
        lines.append("")
        lines.append("| Full Path | Version | Size (KB) | Created | Modified |")
        lines.append("|-----------|---------|-----------|---------|----------|")
        for r in cat_rows:
            lines.append(
                f"| `{r['full_path']}` | {r['version']} | {r['size_kb']} | {r['created']} | {r['modified']} |"
            )
        lines.append("")

    return "\n".join(lines)

if __name__ == "__main__":
    print(f"Scanning vault: {VAULT}")
    rows = collect_files()
    print(f"Files found: {len(rows)}")
    md = build_md(rows)
    OUTPUT.write_text(md, encoding="utf-8")
    print(f"Written: {OUTPUT}")
    print(f"Categories: {sorted(set(r['category'] for r in rows))}")
