"""
Ollama Vault Sweep — AFK Code Review
=====================================
Scans entire Obsidian vault for code files, reviews each via Ollama,
and builds a manifest of active vs dead files for Claude Code.

Hardware target: 12GB VRAM, 32GB RAM
Recommended model: qwen2.5-coder:7b-instruct-q8_0 (best quality at 12GB)
                   or qwen2.5-coder:14b-instruct-q4_K_M (more capability, tighter fit)

Usage:
    python vault_sweep.py                          # Full sweep, default settings
    python vault_sweep.py --ext .py .pine .js      # Multiple file types
    python vault_sweep.py --skip-review             # Only build manifest, no Ollama
    python vault_sweep.py --model qwen2.5-coder:14b # Use specific model

Output (all in 06-CLAUDE-LOGS):
    YYYY-MM-DD-vault-sweep-review.md    — Ollama review per file
    YYYY-MM-DD-vault-sweep-manifest.md  — File index with dependency map
    YYYY-MM-DD-vault-sweep-manifest.json — Machine-readable for Claude Code

Requirements:
    pip install requests
"""

import requests
import json
import time
import argparse
import re
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# === CONFIG ===
VAULT = Path(r'C:\Users\User\Documents\Obsidian Vault')
LOG_DIR = VAULT / '06-CLAUDE-LOGS'
ACTIVE_DIR = VAULT / '07-ACTIVE-CODE'  # Folder Claude Code reads
OLLAMA_URL = 'http://localhost:11434/api/generate'
DEFAULT_MODEL = 'qwen2.5-coder:7b'
MAX_FILE_SIZE = 50_000
TODAY = datetime.now().strftime('%Y-%m-%d')

# Directories to skip (node_modules, .git, venvs, etc.)
SKIP_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    'env', '.obsidian', '.trash', '.mypy_cache', '.pytest_cache'
}

REVIEW_PROMPT = """You are a senior Python developer reviewing trading automation code.
This code is part of a cryptocurrency trading system. Review and provide:

1. **Critical Issues** — Bugs that WILL cause failures or wrong trades
2. **Security** — Exposed API keys, secrets, unsafe eval/exec
3. **Error Handling** — Missing try/except, no retries on API calls, unhandled None
4. **Logic** — Off-by-one, wrong comparisons, race conditions
5. **Improvements** — Concrete code snippets for top 3 fixes

Be specific with line numbers. If the file is solid, say "No critical issues" and move on.
Keep response under 500 words. Do NOT rewrite the entire file."""


# =============================================================================
# PHASE 1: FILE DISCOVERY & DEPENDENCY MAPPING
# =============================================================================

def find_code_files(root: Path, extensions: list) -> list:
    """Recursively find all code files, skipping irrelevant dirs."""
    files = []
    for f in root.rglob('*'):
        # Skip excluded directories
        if any(skip in f.parts for skip in SKIP_DIRS):
            continue
        if f.is_file() and f.suffix in extensions:
            files.append(f)
    return sorted(files)


def extract_imports(filepath: Path) -> list:
    """Extract import statements from a Python file."""
    imports = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        # Match: import x, from x import y, from .x import y
        patterns = [
            r'^import\s+([\w.]+)',
            r'^from\s+([\w.]+)\s+import',
        ]
        for line in content.splitlines():
            line = line.strip()
            for pat in patterns:
                m = re.match(pat, line)
                if m:
                    imports.append(m.group(1))
    except Exception:
        pass
    return imports


def extract_functions_classes(filepath: Path) -> dict:
    """Extract defined functions and classes from a Python file."""
    defs = {'functions': [], 'classes': []}
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith('def '):
                name = stripped.split('(')[0].replace('def ', '')
                defs['functions'].append(name)
            elif stripped.startswith('class '):
                name = stripped.split('(')[0].split(':')[0].replace('class ', '')
                defs['classes'].append(name)
    except Exception:
        pass
    return defs


def build_dependency_map(files: list, root: Path) -> dict:
    """
    Map which files import which other files.
    Returns dict: {filepath: {imports: [], imported_by: [], is_active: bool}}
    """
    file_map = {}
    # Index: module name -> filepath
    module_index = {}
    for f in files:
        if f.suffix == '.py':
            # Convert path to possible module name
            rel = f.relative_to(root)
            module_name = str(rel.with_suffix('')).replace(os.sep, '.')
            module_index[module_name] = f
            # Also index just the filename without extension
            module_index[f.stem] = f

    for f in files:
        rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        imports = extract_imports(f) if f.suffix == '.py' else []
        defs = extract_functions_classes(f) if f.suffix == '.py' else {'functions': [], 'classes': []}
        size = f.stat().st_size
        modified = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')

        file_map[rel] = {
            'path': str(f),
            'relative': rel,
            'size': size,
            'modified': modified,
            'imports': imports,
            'imported_by': [],  # Filled in second pass
            'functions': defs['functions'],
            'classes': defs['classes'],
            'is_active': False,  # Determined after mapping
            'lines': len(f.read_text(encoding='utf-8', errors='ignore').splitlines()),
        }

    # Second pass: find who imports whom
    for rel, info in file_map.items():
        for imp in info['imports']:
            # Check if this import matches any file in our vault
            for mod_name, mod_path in module_index.items():
                if imp == mod_name or imp.endswith(f'.{mod_name}'):
                    target_rel = str(mod_path.relative_to(root)) if mod_path.is_relative_to(root) else str(mod_path)
                    if target_rel in file_map:
                        file_map[target_rel]['imported_by'].append(rel)

    # Determine active files: imported by others, recently modified, or has main guard
    for rel, info in file_map.items():
        f = Path(info['path'])
        content = f.read_text(encoding='utf-8', errors='ignore') if f.suffix == '.py' else ''

        has_main = '__main__' in content or 'if __name__' in content
        is_imported = len(info['imported_by']) > 0
        is_recent = info['modified'] >= (datetime.now().replace(day=1)).strftime('%Y-%m-%d')  # This month

        info['is_active'] = has_main or is_imported or is_recent
        info['activity_reason'] = []
        if has_main:
            info['activity_reason'].append('has __main__')
        if is_imported:
            info['activity_reason'].append(f'imported by {len(info["imported_by"])} files')
        if is_recent:
            info['activity_reason'].append('recently modified')

    return file_map


# =============================================================================
# PHASE 2: OLLAMA REVIEW
# =============================================================================

def check_ollama() -> tuple:
    """Check Ollama is running, return (ok, models)."""
    try:
        resp = requests.get('http://localhost:11434/api/tags', timeout=5)
        models = [m['name'] for m in resp.json().get('models', [])]
        return True, models
    except Exception:
        return False, []


def resolve_model(requested: str, available: list) -> str:
    """Find best matching model from available list."""
    if requested in available:
        return requested
    # Partial match
    matches = [m for m in available if requested.split(':')[0] in m]
    if matches:
        return matches[0]
    return None


def review_file(filepath: Path, model: str) -> dict:
    """Send file to Ollama for review."""
    content = filepath.read_text(encoding='utf-8', errors='ignore')

    if not content.strip():
        return {'review': '_Empty file._', 'time': 0, 'error': False}

    if len(content) > MAX_FILE_SIZE:
        return {'review': f'_Skipped: {len(content):,} chars exceeds limit._', 'time': 0, 'error': False}

    # Add line numbers
    numbered = '\n'.join(f'{i+1:4d} | {line}' for i, line in enumerate(content.splitlines()))

    payload = {
        'model': model,
        'prompt': f'{REVIEW_PROMPT}\n\nFile: {filepath.name}\n\n```python\n{numbered}\n```',
        'stream': False,
        'options': {
            'temperature': 0.2,
            'num_predict': 2048,
            'num_ctx': 8192,       # Context window — safe for 12GB
        }
    }

    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=600)  # 10 min max per file
        resp.raise_for_status()
        result = resp.json()
        return {
            'review': result.get('response', '_No response._'),
            'time': time.time() - start,
            'error': False
        }
    except requests.Timeout:
        return {'review': '_Timeout after 10 minutes._', 'time': 0, 'error': True}
    except Exception as e:
        return {'review': f'_Error: {e}_', 'time': 0, 'error': True}


# =============================================================================
# PHASE 3: OUTPUT GENERATION
# =============================================================================

def write_review_markdown(reviews: list, model: str, total_time: float) -> Path:
    """Write Ollama review results as markdown."""
    out = LOG_DIR / f'{TODAY}-vault-sweep-review.md'
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        '# Vault Code Review — Ollama Sweep',
        '',
        f'- **Date:** {TODAY}',
        f'- **Model:** {model}',
        f'- **Files reviewed:** {len(reviews)}',
        f'- **Total time:** {total_time:.0f}s ({total_time/60:.1f} min)',
        f'- **Purpose:** Feed to Claude Code for targeted fixes',
        '',
        '> **How to use:** Open this file + the code file side by side in Claude Code.',
        '> Ask: "Review these findings and apply fixes where valid."',
        '',
        '---',
        '',
    ]

    for r in reviews:
        status = '🔴' if r.get('has_issues') else '🟢'
        lines.append(f'## {status} `{r["relative"]}`')
        lines.append(f'*{r["lines"]} lines | Reviewed in {r["time"]:.1f}s*\n')
        lines.append(r['review'])
        lines.append('\n---\n')

    out.write_text('\n'.join(lines), encoding='utf-8')
    return out


def write_manifest(file_map: dict) -> tuple:
    """Write manifest as both markdown and JSON."""
    md_out = LOG_DIR / f'{TODAY}-vault-sweep-manifest.md'
    json_out = LOG_DIR / f'{TODAY}-vault-sweep-manifest.json'
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Separate active vs inactive
    active = {k: v for k, v in file_map.items() if v['is_active']}
    inactive = {k: v for k, v in file_map.items() if not v['is_active']}

    # Markdown manifest
    lines = [
        '# Vault Code Manifest',
        '',
        f'- **Date:** {TODAY}',
        f'- **Total files:** {len(file_map)}',
        f'- **Active files:** {len(active)}',
        f'- **Inactive/legacy:** {len(inactive)}',
        '',
        '> **Active** = has `__main__`, is imported by other files, or modified this month.',
        '',
        '---',
        '',
        '## Active Files',
        '',
    ]

    for rel, info in sorted(active.items()):
        reason = ', '.join(info['activity_reason'])
        lines.append(f'### `{rel}`')
        lines.append(f'- **Why active:** {reason}')
        lines.append(f'- **Modified:** {info["modified"]}')
        lines.append(f'- **Lines:** {info["lines"]} | **Size:** {info["size"]:,} bytes')
        if info['functions']:
            lines.append(f'- **Functions:** {", ".join(info["functions"][:10])}')
        if info['classes']:
            lines.append(f'- **Classes:** {", ".join(info["classes"][:10])}')
        if info['imports']:
            lines.append(f'- **Imports:** {", ".join(info["imports"][:10])}')
        if info['imported_by']:
            lines.append(f'- **Imported by:** {", ".join(info["imported_by"])}')
        lines.append('')

    lines.append('---\n')
    lines.append('## Inactive / Legacy Files\n')

    for rel, info in sorted(inactive.items()):
        lines.append(f'- `{rel}` — {info["lines"]} lines, last modified {info["modified"]}')

    md_out.write_text('\n'.join(lines), encoding='utf-8')

    # JSON manifest (for Claude Code to parse)
    json_data = {
        'generated': TODAY,
        'total_files': len(file_map),
        'active_count': len(active),
        'inactive_count': len(inactive),
        'files': {}
    }
    for rel, info in file_map.items():
        json_data['files'][rel] = {
            'path': info['path'],
            'lines': info['lines'],
            'size': info['size'],
            'modified': info['modified'],
            'is_active': info['is_active'],
            'activity_reason': info['activity_reason'],
            'functions': info['functions'],
            'classes': info['classes'],
            'imports': info['imports'],
            'imported_by': info['imported_by'],
        }

    json_out.write_text(json.dumps(json_data, indent=2), encoding='utf-8')

    return md_out, json_out


def setup_active_folder(file_map: dict) -> Path:
    """
    Create 07-ACTIVE-CODE folder with .md pointer files.

    Why not symlinks: Windows requires admin for mklink.
    Instead: each file gets a .md pointer with the real path and a summary.
    Claude Code reads this folder to know which files matter.
    """
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Clean old pointers
    for old in ACTIVE_DIR.glob('*.md'):
        old.unlink()

    active = {k: v for k, v in file_map.items() if v['is_active']}

    # Write index
    index_lines = [
        '# Active Code Files',
        '',
        f'Auto-generated {TODAY} by vault_sweep.py',
        f'These are the Python files currently in use.',
        '',
        '## Quick Reference',
        '',
    ]

    for rel, info in sorted(active.items()):
        safe_name = Path(rel).stem
        reason = ', '.join(info['activity_reason'])

        # Pointer file per active script
        pointer = ACTIVE_DIR / f'{safe_name}.md'
        pointer_content = f"""---
source: "{info['path']}"
modified: "{info['modified']}"
lines: {info['lines']}
active_reason: "{reason}"
---

# {Path(rel).name}

**Source:** `{info['path']}`
**Why active:** {reason}
**Functions:** {', '.join(info['functions'][:15]) or 'None'}
**Classes:** {', '.join(info['classes'][:10]) or 'None'}
**Imports:** {', '.join(info['imports'][:15]) or 'None'}
**Imported by:** {', '.join(info['imported_by']) or 'None (standalone)'}

> To edit this file, open: `{info['path']}`
"""
        pointer.write_text(pointer_content, encoding='utf-8')

        index_lines.append(f'- [{Path(rel).name}]({safe_name}.md) — {reason}')

    index = ACTIVE_DIR / '_INDEX.md'
    index.write_text('\n'.join(index_lines), encoding='utf-8')

    return ACTIVE_DIR


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Vault Code Sweep — AFK Ollama Review')
    parser.add_argument('--folder', default=str(VAULT), help='Root folder to scan')
    parser.add_argument('--model', default=DEFAULT_MODEL, help='Ollama model')
    parser.add_argument('--ext', nargs='+', default=['.py'], help='File extensions to scan')
    parser.add_argument('--skip-review', action='store_true', help='Only build manifest, skip Ollama')
    parser.add_argument('--active-only', action='store_true', help='Only review active files')
    args = parser.parse_args()

    root = Path(args.folder)
    extensions = set(args.ext)

    print(f'Vault Sweep — {TODAY}')
    print(f'Root: {root}')
    print(f'Extensions: {", ".join(extensions)}')
    print(f'{"="*60}\n')

    # Phase 1: Discovery
    print('[Phase 1] Scanning files...')
    files = find_code_files(root, extensions)
    print(f'  Found {len(files)} code files')

    print('[Phase 1] Building dependency map...')
    file_map = build_dependency_map(files, root)
    active_count = sum(1 for v in file_map.values() if v['is_active'])
    print(f'  Active: {active_count} | Inactive: {len(file_map) - active_count}')

    # Phase 1 output: manifest + active folder
    md_manifest, json_manifest = write_manifest(file_map)
    active_folder = setup_active_folder(file_map)
    print(f'  Manifest: {md_manifest}')
    print(f'  JSON: {json_manifest}')
    print(f'  Active folder: {active_folder}')

    # Phase 2: Ollama review
    if args.skip_review:
        print('\n[Phase 2] Skipped (--skip-review)')
        print(f'\nDone. Feed manifest to Claude Code:')
        print(f'  "Read {json_manifest} and identify which files need refactoring"')
        return

    ok, models = check_ollama()
    if not ok:
        print('\nERROR: Ollama not running. Start with: ollama serve')
        print('Manifest was still generated — you can run review later.')
        return

    model = resolve_model(args.model, models)
    if not model:
        print(f'\nERROR: Model "{args.model}" not found.')
        print(f'Available: {", ".join(models)}')
        print(f'Install with: ollama pull qwen2.5-coder:7b')
        return

    # Filter files for review
    review_targets = files
    if args.active_only:
        active_paths = {v['path'] for v in file_map.values() if v['is_active']}
        review_targets = [f for f in files if str(f) in active_paths]
        print(f'\n[Phase 2] Reviewing {len(review_targets)} active files with {model}...')
    else:
        print(f'\n[Phase 2] Reviewing {len(review_targets)} files with {model}...')

    reviews = []
    total_start = time.time()

    for i, f in enumerate(review_targets, 1):
        rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        info = file_map.get(rel, {})
        print(f'  [{i}/{len(review_targets)}] {rel}...', end=' ', flush=True)

        result = review_file(f, model)
        reviews.append({
            'relative': rel,
            'path': str(f),
            'lines': info.get('lines', 0),
            'review': result['review'],
            'time': result['time'],
            'has_issues': 'no critical' not in result['review'].lower() and not result['error'],
        })
        print(f'{result["time"]:.1f}s')

    total_time = time.time() - total_start

    # Phase 2 output: review file
    review_path = write_review_markdown(reviews, model, total_time)
    print(f'\n{"="*60}')
    print(f'Review: {review_path}')
    print(f'Manifest: {md_manifest}')
    print(f'JSON: {json_manifest}')
    print(f'Active folder: {active_folder}')
    print(f'Total time: {total_time/60:.1f} minutes')

    issues = sum(1 for r in reviews if r['has_issues'])
    print(f'\nFiles with issues: {issues}/{len(reviews)}')
    print(f'\nNext step — feed to Claude Code:')
    print(f'  "Read {review_path} and {json_manifest}, fix critical issues in active files"')


if __name__ == '__main__':
    main()
