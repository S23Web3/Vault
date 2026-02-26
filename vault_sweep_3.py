"""
Ollama Vault Sweep v2 — AFK Code Review
========================================
Streaming progress, retry logic, crash-safe auto-save.

Usage:
    python vault_sweep.py --ext .py .pine .js
    python vault_sweep.py --skip-review
    python vault_sweep.py --active-only
    python vault_sweep.py --retries 5

Requirements: pip install requests
"""

import requests
import json
import time
import argparse
import re
import os
import sys
import threading
from pathlib import Path
from datetime import datetime


# === CONFIG ===
VAULT = Path(r'C:\Users\User\Documents\Obsidian Vault')
LOG_DIR = VAULT / '06-CLAUDE-LOGS'
ACTIVE_DIR = VAULT / '07-ACTIVE-CODE'
OLLAMA_URL = 'http://localhost:11434/api/generate'
DEFAULT_MODEL = 'qwen2.5-coder:14b'
MAX_FILE_SIZE = 50_000
MAX_RETRIES = 3
RETRY_DELAY = 10
TODAY = datetime.now().strftime('%Y-%m-%d')

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


class ProgressTracker:
    """Live token counter and timer during Ollama streaming."""

    def __init__(self):
        self.tokens = 0
        self.start_time = time.time()
        self._stop = False
        self._thread = None

    def start(self):
        self.tokens = 0
        self.start_time = time.time()
        self._stop = False
        self._thread = threading.Thread(target=self._tick, daemon=True)
        self._thread.start()

    def _tick(self):
        while not self._stop:
            elapsed = time.time() - self.start_time
            tps = self.tokens / elapsed if elapsed > 0 else 0
            sys.stdout.write(f'\r    > {elapsed:.0f}s | {self.tokens} tokens | {tps:.1f} tok/s   ')
            sys.stdout.flush()
            time.sleep(1)

    def update(self, n: int = 1):
        self.tokens += n

    def stop(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=2)
        elapsed = time.time() - self.start_time
        tps = self.tokens / elapsed if elapsed > 0 else 0
        sys.stdout.write(f'\r    OK {elapsed:.0f}s | {self.tokens} tokens | {tps:.1f} tok/s\n')
        sys.stdout.flush()
        return elapsed

    def stop_error(self, msg: str):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=2)
        elapsed = time.time() - self.start_time
        sys.stdout.write(f'\r    FAIL {msg} after {elapsed:.0f}s\n')
        sys.stdout.flush()
        return elapsed


def find_code_files(root: Path, extensions: set) -> list:
    files = []
    for f in root.rglob('*'):
        if any(skip in f.parts for skip in SKIP_DIRS):
            continue
        if f.is_file() and f.suffix in extensions:
            files.append(f)
    return sorted(files)


def extract_imports(filepath: Path) -> list:
    imports = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        for line in content.splitlines():
            line = line.strip()
            m = re.match(r'^import\s+([\w.]+)', line)
            if m:
                imports.append(m.group(1))
            m = re.match(r'^from\s+([\w.]+)\s+import', line)
            if m:
                imports.append(m.group(1))
    except Exception:
        pass
    return imports


def extract_functions_classes(filepath: Path) -> dict:
    defs = {'functions': [], 'classes': []}
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        for line in content.splitlines():
            s = line.strip()
            if s.startswith('def '):
                defs['functions'].append(s.split('(')[0].replace('def ', ''))
            elif s.startswith('class '):
                defs['classes'].append(s.split('(')[0].split(':')[0].replace('class ', ''))
    except Exception:
        pass
    return defs


def build_dependency_map(files: list, root: Path) -> dict:
    file_map = {}
    module_index = {}
    for f in files:
        if f.suffix == '.py':
            rel = f.relative_to(root)
            module_index[str(rel.with_suffix('')).replace(os.sep, '.')] = f
            module_index[f.stem] = f

    for f in files:
        rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        imports = extract_imports(f) if f.suffix == '.py' else []
        defs = extract_functions_classes(f) if f.suffix == '.py' else {'functions': [], 'classes': []}
        try:
            size = f.stat().st_size
            modified = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            line_count = len(f.read_text(encoding='utf-8', errors='ignore').splitlines())
        except Exception as e:
            print(f'  WARN: {rel}: {e}')
            size, modified, line_count = 0, 'unknown', 0

        file_map[rel] = {
            'path': str(f), 'relative': rel, 'size': size,
            'modified': modified, 'imports': imports, 'imported_by': [],
            'functions': defs['functions'], 'classes': defs['classes'],
            'is_active': False, 'lines': line_count,
        }

    for rel, info in file_map.items():
        for imp in info['imports']:
            for mod_name, mod_path in module_index.items():
                if imp == mod_name or imp.endswith(f'.{mod_name}'):
                    t = str(mod_path.relative_to(root)) if mod_path.is_relative_to(root) else str(mod_path)
                    if t in file_map:
                        file_map[t]['imported_by'].append(rel)

    for rel, info in file_map.items():
        f = Path(info['path'])
        try:
            content = f.read_text(encoding='utf-8', errors='ignore') if f.suffix == '.py' else ''
        except Exception:
            content = ''
        has_main = '__main__' in content or 'if __name__' in content
        is_imported = len(info['imported_by']) > 0
        is_recent = info['modified'] >= datetime.now().replace(day=1).strftime('%Y-%m-%d')
        info['is_active'] = has_main or is_imported or is_recent
        info['activity_reason'] = []
        if has_main: info['activity_reason'].append('has __main__')
        if is_imported: info['activity_reason'].append(f'imported by {len(info["imported_by"])} files')
        if is_recent: info['activity_reason'].append('recently modified')

    return file_map


def check_ollama() -> tuple:
    try:
        resp = requests.get('http://localhost:11434/api/tags', timeout=10)
        return True, [m['name'] for m in resp.json().get('models', [])]
    except Exception:
        return False, []


def resolve_model(requested: str, available: list) -> str:
    if requested in available:
        return requested
    matches = [m for m in available if requested.split(':')[0] in m]
    return matches[0] if matches else None


def review_file_streaming(filepath: Path, model: str, max_retries: int) -> dict:
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return {'review': f'_Error reading: {e}_', 'time': 0, 'error': True}

    if not content.strip():
        return {'review': '_Empty file._', 'time': 0, 'error': False}
    if len(content) > MAX_FILE_SIZE:
        return {'review': f'_Skipped: {len(content):,} chars > {MAX_FILE_SIZE:,} limit._', 'time': 0, 'error': False}

    numbered = '\n'.join(f'{i+1:4d} | {line}' for i, line in enumerate(content.splitlines()))
    payload = {
        'model': model,
        'prompt': f'{REVIEW_PROMPT}\n\nFile: {filepath.name}\n\n```python\n{numbered}\n```',
        'stream': True,
        'options': {'temperature': 0.2, 'num_predict': 2048, 'num_ctx': 8192}
    }

    for attempt in range(1, max_retries + 1):
        tracker = ProgressTracker()
        tracker.start()
        chunks = []

        try:
            resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=600)
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    tok = data.get('response', '')
                    if tok:
                        chunks.append(tok)
                        tracker.update()
                    if data.get('done'):
                        break
                except json.JSONDecodeError:
                    continue

            elapsed = tracker.stop()
            text = ''.join(chunks)
            if not text.strip():
                raise ValueError('Empty response')
            return {'review': text, 'time': elapsed, 'error': False}

        except requests.ConnectionError:
            tracker.stop_error(f'Connection lost ({attempt}/{max_retries})')
            if attempt < max_retries:
                print(f'    RETRY in {RETRY_DELAY}s...')
                time.sleep(RETRY_DELAY)
                ok, _ = check_ollama()
                if not ok:
                    print(f'    Ollama down. Waiting {RETRY_DELAY * 3}s...')
                    time.sleep(RETRY_DELAY * 3)
            else:
                return {'review': f'_Failed: Connection error after {max_retries} tries._', 'time': 0, 'error': True}

        except requests.Timeout:
            tracker.stop_error(f'Timeout ({attempt}/{max_retries})')
            if attempt < max_retries:
                print(f'    RETRY in {RETRY_DELAY}s...')
                time.sleep(RETRY_DELAY)
            else:
                return {'review': '_Failed: Timeout._', 'time': 0, 'error': True}

        except requests.HTTPError:
            tracker.stop_error(f'HTTP error ({attempt}/{max_retries})')
            if attempt < max_retries:
                print(f'    RETRY in {RETRY_DELAY}s...')
                time.sleep(RETRY_DELAY)
            else:
                return {'review': '_Failed: HTTP error._', 'time': 0, 'error': True}

        except Exception as e:
            tracker.stop_error(f'{type(e).__name__} ({attempt}/{max_retries})')
            if attempt < max_retries:
                print(f'    RETRY in {RETRY_DELAY}s...')
                time.sleep(RETRY_DELAY)
            else:
                return {'review': f'_Failed: {e}_', 'time': 0, 'error': True}

    return {'review': '_Exhausted retries._', 'time': 0, 'error': True}


def save_review(reviews: list, model: str, total_time: float, is_final: bool = False):
    out = LOG_DIR / f'{TODAY}-vault-sweep-review.md'
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    status = "COMPLETE" if is_final else "IN PROGRESS"
    issues = sum(1 for r in reviews if r.get('has_issues'))
    errs = sum(1 for r in reviews if r.get('error'))

    lines = [
        f'# Vault Code Review [{status}]', '',
        f'- **Date:** {TODAY}', f'- **Model:** {model}',
        f'- **Files:** {len(reviews)}', f'- **Issues:** {issues}', f'- **Errors:** {errs}',
        f'- **Time:** {total_time:.0f}s ({total_time/60:.1f} min)', '', '---', '',
    ]
    for r in reviews:
        icon = '⚠️' if r.get('error') else ('🔴' if r.get('has_issues') else '🟢')
        lines.append(f'## {icon} `{r["relative"]}`')
        lines.append(f'*{r["lines"]} lines | {r["time"]:.1f}s*\n')
        lines.append(r['review'])
        lines.append('\n---\n')

    out.write_text('\n'.join(lines), encoding='utf-8')
    return out


def write_manifest(file_map: dict) -> tuple:
    md_out = LOG_DIR / f'{TODAY}-vault-sweep-manifest.md'
    json_out = LOG_DIR / f'{TODAY}-vault-sweep-manifest.json'
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    active = {k: v for k, v in file_map.items() if v['is_active']}
    inactive = {k: v for k, v in file_map.items() if not v['is_active']}

    lines = [
        '# Vault Code Manifest', '',
        f'- **Date:** {TODAY}', f'- **Total:** {len(file_map)}',
        f'- **Active:** {len(active)}', f'- **Inactive:** {len(inactive)}',
        '', '---', '', '## Active Files', '',
    ]
    for rel, info in sorted(active.items()):
        lines.append(f'### `{rel}`')
        lines.append(f'- **Why:** {", ".join(info["activity_reason"])}')
        lines.append(f'- **Modified:** {info["modified"]} | **Lines:** {info["lines"]}')
        if info['functions']: lines.append(f'- **Functions:** {", ".join(info["functions"][:10])}')
        if info['imports']: lines.append(f'- **Imports:** {", ".join(info["imports"][:10])}')
        if info['imported_by']: lines.append(f'- **Imported by:** {", ".join(info["imported_by"])}')
        lines.append('')

    lines.extend(['---', '', '## Inactive', ''])
    for rel, info in sorted(inactive.items()):
        lines.append(f'- `{rel}` — {info["lines"]} lines, {info["modified"]}')

    md_out.write_text('\n'.join(lines), encoding='utf-8')

    json_data = {
        'generated': TODAY, 'total_files': len(file_map),
        'active_count': len(active), 'inactive_count': len(inactive),
        'files': {rel: {
            'path': i['path'], 'lines': i['lines'], 'size': i['size'],
            'modified': i['modified'], 'is_active': i['is_active'],
            'activity_reason': i['activity_reason'], 'functions': i['functions'],
            'classes': i['classes'], 'imports': i['imports'], 'imported_by': i['imported_by'],
        } for rel, i in file_map.items()}
    }
    json_out.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
    return md_out, json_out


def setup_active_folder(file_map: dict) -> Path:
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    for old in ACTIVE_DIR.glob('*.md'):
        old.unlink()

    active = {k: v for k, v in file_map.items() if v['is_active']}
    index_lines = ['# Active Code Files', '', f'Generated {TODAY}', '', '## Index', '']

    for rel, info in sorted(active.items()):
        # Use full relative path as name to avoid collisions (e.g. multiple __init__.py)
        safe_name = rel.replace(os.sep, '_').replace('.', '_').replace(' ', '_')
        reason = ', '.join(info['activity_reason'])
        pointer = ACTIVE_DIR / f'{safe_name}.md'
        pointer.write_text(f"""---
source: "{info['path']}"
modified: "{info['modified']}"
lines: {info['lines']}
---
# {Path(rel).name}
**Source:** `{info['path']}`
**Why active:** {reason}
**Functions:** {', '.join(info['functions'][:15]) or 'None'}
**Imports:** {', '.join(info['imports'][:15]) or 'None'}
**Imported by:** {', '.join(info['imported_by']) or 'standalone'}
""", encoding='utf-8')
        index_lines.append(f'- [{Path(rel).name}]({safe_name}.md) — {reason}')

    (ACTIVE_DIR / '_INDEX.md').write_text('\n'.join(index_lines), encoding='utf-8')
    return ACTIVE_DIR


def main():
    parser = argparse.ArgumentParser(description='Vault Sweep v2')
    parser.add_argument('--folder', default=str(VAULT))
    parser.add_argument('--model', default=DEFAULT_MODEL)
    parser.add_argument('--ext', nargs='+', default=['.py'])
    parser.add_argument('--skip-review', action='store_true')
    parser.add_argument('--active-only', action='store_true')
    parser.add_argument('--retries', type=int, default=MAX_RETRIES)
    args = parser.parse_args()

    root = Path(args.folder)
    extensions = set(args.ext)

    print(f'\n{"="*60}')
    print(f'  Vault Sweep v2 — {TODAY}')
    print(f'  Root: {root}')
    print(f'  Extensions: {", ".join(sorted(extensions))}')
    print(f'  Retries: {args.retries}')
    print(f'{"="*60}\n')

    print('[Phase 1] Scanning...')
    files = find_code_files(root, extensions)
    print(f'  {len(files)} files found')
    if not files:
        print('  Nothing to do.')
        return

    print('[Phase 1] Dependency map...')
    file_map = build_dependency_map(files, root)
    active_count = sum(1 for v in file_map.values() if v['is_active'])
    print(f'  Active: {active_count} | Inactive: {len(file_map) - active_count}')

    md_manifest, json_manifest = write_manifest(file_map)
    setup_active_folder(file_map)
    print(f'  Outputs: {LOG_DIR.name}/')

    if args.skip_review:
        print(f'\n[Phase 2] Skipped.\nFeed to Claude Code:\n  "Read {json_manifest}"')
        return

    ok, models = check_ollama()
    if not ok:
        print('\nOllama not running. Start: ollama serve')
        return

    model = resolve_model(args.model, models)
    if not model:
        print(f'\nModel "{args.model}" not found. Available: {", ".join(models)}')
        return

    targets = files
    if args.active_only:
        active_paths = {v['path'] for v in file_map.values() if v['is_active']}
        targets = [f for f in files if str(f) in active_paths]

    total = len(targets)
    print(f'\n[Phase 2] {total} files with {model}')
    print(f'  Auto-saves after each file (crash-safe)\n')

    reviews = []
    t0 = time.time()

    try:
        for i, f in enumerate(targets, 1):
            rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
            info = file_map.get(rel, {})
            lc = info.get('lines', '?')

            elapsed = time.time() - t0
            if i > 1:
                eta = (elapsed / (i - 1)) * (total - i + 1) / 60
                eta_str = f'ETA {eta:.0f}min'
            else:
                eta_str = 'ETA calculating...'

            print(f'  [{i}/{total}] {rel} ({lc} lines) | {eta_str}')

            result = review_file_streaming(f, model, max_retries=args.retries)

            has_issues = (
                'no critical' not in result['review'].lower()
                and 'no issues' not in result['review'].lower()
                and not result['error']
            )
            reviews.append({
                'relative': rel, 'path': str(f), 'lines': info.get('lines', 0),
                'review': result['review'], 'time': result['time'],
                'has_issues': has_issues, 'error': result['error'],
            })

            save_review(reviews, model, time.time() - t0)

    except KeyboardInterrupt:
        print(f'\n\n  Ctrl+C — saving {len(reviews)} completed reviews...')
        total_time = time.time() - t0
        review_path = save_review(reviews, model, total_time, is_final=False)
        print(f'  Saved: {review_path}')
        print(f'  Re-run to continue (already reviewed files will be re-done)')
        return

    total_time = time.time() - t0
    review_path = save_review(reviews, model, total_time, is_final=True)

    issues = sum(1 for r in reviews if r['has_issues'])
    errors = sum(1 for r in reviews if r.get('error'))
    clean = len(reviews) - issues - errors

    print(f'\n{"="*60}')
    print(f'  DONE — {total_time/60:.1f} min')
    print(f'  {clean} clean | {issues} issues | {errors} errors')
    print(f'  Review: {review_path}')
    print(f'  Manifest: {json_manifest}')
    print(f'{"="*60}')


if __name__ == '__main__':
    main()
