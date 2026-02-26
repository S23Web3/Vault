#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-generate Python files using Ollama with automatic file saving.

Usage:
    python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md

This script:
1. Reads the prompt file
2. Sends it to Ollama API
3. Parses generated code
4. Automatically saves each file to disk
"""

import re
import requests
import json
import sys
import os
import py_compile
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple, Set

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    os.system('')  # Enable ANSI escape codes
    sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OUTPUT_BASE_DIR = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")


def send_to_ollama(prompt: str, model: str = "qwen2.5-coder:14b", checkpoint_file: Path = Path("generation_checkpoint.txt")) -> str:
    """
    Send prompt to Ollama and get generated response with checkpointing.

    Args:
        prompt: The full prompt text
        model: Ollama model to use
        checkpoint_file: File to save progress continuously

    Returns:
        Generated text from Ollama
    """
    print(f"[*] Sending prompt to Ollama ({model})...")
    print(f"[*] Prompt length: {len(prompt)} characters")
    print()

    # System prompt: Tell Qwen it's a Python coding expert
    system_prompt = """You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
You are an expert Python developer specializing in trading systems and backtesting platforms.

Your task is to generate complete, production-ready Python code.

CRITICAL OUTPUT FORMAT:
- Each file MUST be in its own separate ```python code block
- The FIRST line inside each code block MUST be a comment with the file path: # path/to/file.py
- Example:

```python
# strategies/base_strategy.py
from abc import ABC, abstractmethod
...
```

```python
# engine/position_manager.py
import pandas as pd
...
```

RULES:
- Generate ONLY valid, working Python code
- Include all necessary imports
- Add type hints and comprehensive docstrings
- Implement proper error handling
- Write clean, efficient, well-commented code
- Do NOT use placeholder comments like "# TODO" or "# IMPLEMENT HERE"
- Each function must be complete and ready to run
- NEVER put multiple files in the same code block
- After each file, start the next file immediately"""

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True,
        "options": {
            "temperature": 0.3,
            "num_ctx": 32768,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        }
    }

    response_text = ""
    last_save_length = 0

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=7200)  # 2 hour timeout
        response.raise_for_status()

        # Stream response and show progress
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if not chunk.get('done'):
                        token = chunk.get('response', '')
                        response_text += token
                        print(token, end='', flush=True)

                        # Save checkpoint every 1000 chars
                        if len(response_text) - last_save_length > 1000:
                            checkpoint_file.write_text(response_text, encoding='utf-8')
                            last_save_length = len(response_text)

                except json.JSONDecodeError:
                    continue  # Skip malformed chunks

        # Final save
        checkpoint_file.write_text(response_text, encoding='utf-8')

        print("\n\n[OK] Generation complete!")
        return response_text

    except requests.exceptions.Timeout:
        print("\n[WARN] Request timed out (>2 hours)")
        print(f"[*] Partial response saved ({len(response_text)} chars)")
        checkpoint_file.write_text(response_text, encoding='utf-8')
        return response_text  # Return partial response
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Lost connection to Ollama")
        print(f"[*] Partial response saved ({len(response_text)} chars)")
        if response_text:
            checkpoint_file.write_text(response_text, encoding='utf-8')
        return response_text
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user")
        print(f"[*] Partial response saved ({len(response_text)} chars)")
        checkpoint_file.write_text(response_text, encoding='utf-8')
        return response_text
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        print(f"[*] Partial response saved ({len(response_text)} chars)")
        if response_text:
            checkpoint_file.write_text(response_text, encoding='utf-8')
        return response_text


def parse_generated_files(text: str) -> List[Tuple[str, str]]:
    """
    Parse generated text to extract individual Python files.

    Supports multiple formats:
    1. File X.Y: path/to/file.py  (original format)
    2. # path/to/file.py inside code block  (Qwen format)
    3. Completion markers with checkmark

    Returns:
        List of (file_path, code) tuples
    """
    files = []
    found_paths = set()

    # Pattern 1: Explicit file markers (original format)
    # File X.Y: path/to/file.py
    # ```python
    # [code]
    # ```
    pattern1 = r"File \d+[\.\d]*:\s*([^\n]+\.py)[^\n]*\n+```python\n(.*?)```"
    for match in re.finditer(pattern1, text, re.DOTALL):
        file_path = match.group(1).strip()
        code = match.group(2).strip()
        if file_path not in found_paths:
            files.append((file_path, code))
            found_paths.add(file_path)
            print(f"[*] Found (marker): {file_path} ({len(code)} chars)")

    # Pattern 2: Qwen format -- # path/to/file.py as first line inside code block
    # ```python
    # # path/to/file.py
    # [code]
    # ```
    pattern2 = r"```python\n\s*#+\s*([^\n]*?\.py)\s*\n(.*?)```"
    for match in re.finditer(pattern2, text, re.DOTALL):
        file_path = match.group(1).strip()
        code = match.group(2).strip()
        if file_path not in found_paths:
            files.append((file_path, code))
            found_paths.add(file_path)
            print(f"[*] Found (comment): {file_path} ({len(code)} chars)")

    # Pattern 3: Filename in heading before code block
    # ### path/to/file.py
    # ```python
    # [code]
    # ```
    pattern3 = r"#{1,4}\s*`?([^\n`]+\.py)`?\s*\n+```python\n(.*?)```"
    for match in re.finditer(pattern3, text, re.DOTALL):
        file_path = match.group(1).strip()
        code = match.group(2).strip()
        if file_path not in found_paths:
            files.append((file_path, code))
            found_paths.add(file_path)
            print(f"[*] Found (heading): {file_path} ({len(code)} chars)")

    # Pattern 4: Completion markers (checkmark after code block)
    pattern4 = r"```python\n(.*?)```[^\n]*\n[^\n]*[*]\s*([^\s]+\.py)\s*COMPLETE"
    for match in re.finditer(pattern4, text, re.DOTALL):
        code = match.group(1).strip()
        filename = match.group(2).strip()
        if filename not in found_paths and not any(f[0].endswith(filename) for f in files):
            files.append((filename, code))
            found_paths.add(filename)
            print(f"[*] Found (complete): {filename} ({len(code)} chars)")

    return files


def save_file(file_path: str, code: str, base_dir: Path = OUTPUT_BASE_DIR):
    """
    Save generated code to file.

    Args:
        file_path: Relative path (e.g., "strategies/base_strategy.py")
        code: Python code content
        base_dir: Base output directory
    """
    full_path = base_dir / file_path

    # Skip if file already exists
    if full_path.exists():
        print(f"[SKIP] Already exists: {full_path}")
        return False

    # Create parent directories
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"[OK] Saved: {full_path} ({len(code)} bytes)")
    return True


def review_code_with_ollama(code: str, filename: str, model: str = "qwen2.5-coder:14b") -> dict:
    """
    Use Ollama to review generated code for errors and improvements.

    Args:
        code: The Python code to review
        filename: Name of the file being reviewed
        model: Ollama model to use

    Returns:
        dict with 'has_errors': bool, 'issues': list, 'suggestions': str
    """
    system_prompt_review = """You are a Senior Principal Python Engineer and Security Auditor with 20+ years of experience reviewing production code for Fortune 500 companies.

Your expertise includes:
- Python best practices (PEP 8, PEP 484, PEP 585)
- Security vulnerabilities (OWASP Top 10, injection attacks, data validation)
- Performance optimization and memory management
- Type safety and runtime error prevention
- Trading systems and financial software (risk management, precision, edge cases)

You conduct thorough code reviews focusing on:
1. Critical security vulnerabilities
2. Runtime errors and exception handling
3. Type safety and data validation
4. Resource leaks and performance issues
5. Logic errors and edge cases
6. Production readiness"""

    review_prompt = f"""Conduct a comprehensive security and quality review of this Python code:

**Filename**: {filename}

```python
{code}
```

**Review Checklist**:
1. **SECURITY**: SQL injection, command injection, path traversal, unsafe deserialization, hardcoded credentials
2. **ERRORS**: Syntax errors, logic bugs, unhandled exceptions, division by zero, None-type errors
3. **TYPE SAFETY**: Missing type hints, incorrect types, type mismatches
4. **IMPORTS**: Missing imports, unused imports, circular dependencies
5. **DATA VALIDATION**: Input validation, boundary checks, NaN/Inf handling (critical for trading)
6. **RESOURCE MANAGEMENT**: File handles, database connections, memory leaks
7. **BEST PRACTICES**: PEP 8 violations, code smells, anti-patterns
8. **PRODUCTION READINESS**: Error logging, graceful degradation, testability

**Output Format**:
CRITICAL_ERRORS: [any bugs that will cause crashes or security issues, or "None"]
WARNINGS: [non-critical issues that should be addressed, or "None"]
SECURITY_ISSUES: [any security vulnerabilities found, or "None"]
TYPE_ISSUES: [type hint problems or type safety concerns, or "None"]
RECOMMENDATIONS: [brief suggestions for improvement]

Be specific and reference line numbers or code snippets where possible."""

    try:
        payload = {
            "model": model,
            "prompt": review_prompt,
            "system": system_prompt_review,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Very low for deterministic security review
                "num_ctx": 8192,
                "top_p": 0.9,
            }
        }

        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        review_text = result.get('response', '')

        # Parse review
        has_errors = 'ERRORS: None' not in review_text and 'ERRORS:' in review_text

        return {
            'has_errors': has_errors,
            'review': review_text,
            'filename': filename
        }

    except Exception as e:
        print(f"    [WARN] Code review failed: {e}")
        return {'has_errors': False, 'review': f'Review failed: {e}', 'filename': filename}


def verify_python_file(file_path: Path) -> bool:
    """
    Verify Python file syntax, structure, AND test imports.

    Args:
        file_path: Path to Python file to verify

    Returns:
        True if valid, False if errors found
    """
    try:
        # Test 1: Syntax check using py_compile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(file_path.read_text(encoding='utf-8'))
            tmp_path = tmp.name

        try:
            py_compile.compile(tmp_path, doraise=True)
            print(f"    [OK] Syntax valid: {file_path.name}")

            # Test 2: Check for basic Python structure
            code = file_path.read_text(encoding='utf-8')

            # Check for common issues
            issues = []
            if 'import' not in code and 'from' not in code:
                issues.append("No imports found (might be intentional)")

            if 'def ' not in code and 'class ' not in code:
                issues.append("No functions or classes defined")

            # Check for TODO/placeholder comments
            if 'TODO' in code or 'FIXME' in code or '# [GENERATE' in code:
                issues.append("Contains TODO or placeholder comments")

            if issues:
                print(f"    [WARN] Potential issues in {file_path.name}:")
                for issue in issues:
                    print(f"           - {issue}")

            # Test 3: Try importing the module (actual runtime test)
            try:
                # Add parent directory to sys.path temporarily
                import importlib.util
                import sys

                parent_path = str(file_path.parent.parent.absolute())
                if parent_path not in sys.path:
                    sys.path.insert(0, parent_path)

                # Create module spec and load
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    print(f"    [OK] Import test passed: {file_path.name}")
                else:
                    print(f"    [WARN] Could not create module spec for {file_path.name}")

                # Clean up sys.path
                if parent_path in sys.path:
                    sys.path.remove(parent_path)

            except ImportError as ie:
                print(f"    [WARN] Import test failed (may need dependencies): {ie}")
            except Exception as ie:
                print(f"    [WARN] Import test error: {ie}")

            return True

        finally:
            os.unlink(tmp_path)

    except py_compile.PyCompileError as e:
        print(f"    [ERROR] Syntax error in {file_path.name}:")
        print(f"            {str(e)}")
        return False
    except Exception as e:
        print(f"    [ERROR] Verification failed for {file_path.name}: {e}")
        return False


def extract_dependencies(code: str) -> Set[str]:
    """
    Extract all import statements from Python code.

    Args:
        code: Python source code

    Returns:
        Set of package names imported
    """
    imports = set()

    # Match: import package
    for match in re.finditer(r'^import\s+([a-zA-Z0-9_]+)', code, re.MULTILINE):
        imports.add(match.group(1))

    # Match: from package import ...
    for match in re.finditer(r'^from\s+([a-zA-Z0-9_]+)', code, re.MULTILINE):
        imports.add(match.group(1))

    return imports


def generate_requirements_txt(all_files_code: List[Tuple[str, str]], base_dir: Path = OUTPUT_BASE_DIR):
    """
    Generate requirements.txt from all imported packages.

    Args:
        all_files_code: List of (filename, code) tuples
        base_dir: Base output directory
    """
    # Common import -> pip package mapping
    IMPORT_TO_PIP = {
        'pandas': 'pandas>=2.0.0',
        'numpy': 'numpy>=1.24.0',
        'talib': 'ta-lib>=0.4.0',  # Note: Requires TA-Lib C library
        'requests': 'requests>=2.31.0',
        'optuna': 'optuna>=3.4.0',
        'xgboost': 'xgboost>=2.0.0',
        'sklearn': 'scikit-learn>=1.3.0',
        'plotly': 'plotly>=5.17.0',
        'streamlit': 'streamlit>=1.28.0',
        'fuzzywuzzy': 'fuzzywuzzy>=0.18.0',
        'tqdm': 'tqdm>=4.66.0',
        'shap': 'shap>=0.43.0',
        'torch': 'torch>=2.0.0',
        'matplotlib': 'matplotlib>=3.7.0',
        'seaborn': 'seaborn>=0.12.0',
        'scipy': 'scipy>=1.11.0',
        'colorama': 'colorama>=0.4.6',
        'pytest': 'pytest>=7.4.0',
        'black': 'black>=23.0.0',
        'mypy': 'mypy>=1.5.0',
    }

    all_imports = set()

    # Extract all imports from all files
    for filename, code in all_files_code:
        imports = extract_dependencies(code)
        all_imports.update(imports)

    # Map to pip packages
    requirements = []
    for imp in sorted(all_imports):
        if imp in IMPORT_TO_PIP:
            requirements.append(IMPORT_TO_PIP[imp])
        elif imp not in ['abc', 'sys', 'os', 'json', 're', 'pathlib', 'typing',
                         'datetime', 'collections', 'itertools', 'functools',
                         'logging', 'tempfile', 'copy', 'math']:  # stdlib
            # Unknown package, add without version
            requirements.append(imp)

    if requirements:
        requirements_file = base_dir / 'requirements.txt'
        requirements_content = '\n'.join(requirements) + '\n'
        requirements_file.write_text(requirements_content, encoding='utf-8')

        print(f"[*] Created: {requirements_file}")
        print(f"[*] Dependencies found: {len(requirements)}")
        print()
        print("    To install dependencies:")
        print(f"    pip install -r {requirements_file}")
        print()

        # Special note for TA-Lib
        if any('ta-lib' in req.lower() for req in requirements):
            print("    [!] NOTE: TA-Lib requires C library installation first:")
            print("        Windows: https://github.com/cgohlke/talib-build/releases")
            print("        Linux: sudo apt-get install ta-lib")
            print("        Mac: brew install ta-lib")
            print()


def create_init_files(saved_files: List[Path]):
    """Create __init__.py files only in directories that contain newly saved files."""
    dirs_needing_init = set()
    for f in saved_files:
        dirs_needing_init.add(f.parent)

    for d in sorted(dirs_needing_init):
        init_file = d / '__init__.py'
        if not init_file.exists():
            init_file.write_text('"""Package init file"""\n')
            print(f"[*] Created: {init_file}")


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        print("Usage: python auto_generate_files.py <prompt_file.md> [--resume]")
        print("\nExample:")
        print("  python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md")
        print("  python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md --resume")
        sys.exit(1)

    prompt_file = Path(sys.argv[1])
    resume_mode = '--resume' in sys.argv

    if not prompt_file.exists():
        print(f"[ERROR] File not found: {prompt_file}")
        sys.exit(1)

    # Verify write permissions on output directory
    if not OUTPUT_BASE_DIR.exists():
        print(f"[ERROR] Output directory does not exist: {OUTPUT_BASE_DIR}")
        sys.exit(1)

    try:
        test_file = OUTPUT_BASE_DIR / ".write_test"
        test_file.write_text("write_test", encoding="utf-8")
        test_file.unlink()
        print(f"[OK] Write permissions verified: {OUTPUT_BASE_DIR}")
    except PermissionError:
        print(f"[ERROR] No write permission to: {OUTPUT_BASE_DIR}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Write permission check failed: {e}")
        sys.exit(1)

    # Read prompt
    print("="*60)
    print("AUTO FILE GENERATOR - Ollama + Qwen")
    print("="*60)
    print()

    checkpoint_file = Path("generation_checkpoint.txt")

    # Check for existing checkpoint
    if resume_mode and checkpoint_file.exists():
        print("[RESUME] RESUME MODE DETECTED")
        generated_text = checkpoint_file.read_text(encoding='utf-8')
        print(f"[OK] Loaded checkpoint: {len(generated_text)} characters")
        print(f"[*] Parsing existing output to continue...")
        print()
    else:
        if resume_mode:
            print("[WARN] No checkpoint found, starting fresh")
            print()

        prompt = prompt_file.read_text(encoding='utf-8')
        print(f"[OK] Loaded prompt: {prompt_file}")
        print(f"[*] Prompt size: {len(prompt)} characters")
        print()

        # Generate code via Ollama
        generated_text = send_to_ollama(prompt)

    if not generated_text:
        print("[ERROR] No output generated")
        if checkpoint_file.exists():
            checkpoint_file.rename(checkpoint_file.with_name("generation_checkpoint_empty.txt"))
        sys.exit(0)

    # Save full output for debugging
    output_log = Path("generated_output.log")
    output_log.write_text(generated_text, encoding='utf-8')
    print(f"\n[*] Full output saved to: {output_log}")
    print()

    # Parse files
    print("="*60)
    print("PARSING GENERATED FILES")
    print("="*60)
    print()

    files = parse_generated_files(generated_text)

    if not files:
        print("[WARN] No files found in output. Check generated_output.log")
        # Clean up checkpoint so next reboot doesn't re-parse the same bad output
        if checkpoint_file.exists():
            done_name = checkpoint_file.with_name("generation_checkpoint_failed.txt")
            checkpoint_file.rename(done_name)
            print(f"[*] Checkpoint renamed to {done_name.name} (parse failed, won't retry)")
        sys.exit(0)  # Exit 0 so startup script continues to Phase 2 (test existing files)

    print(f"\n[OK] Found {len(files)} files")
    print()

    # Save files
    print("="*60)
    print("SAVING FILES")
    print("="*60)
    print()

    saved_files = []
    skipped_files = []
    for file_path, code in files:
        try:
            if save_file(file_path, code):
                saved_files.append(OUTPUT_BASE_DIR / file_path)
            else:
                skipped_files.append(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to save {file_path}: {e}")

    if skipped_files:
        print(f"\n[*] Skipped {len(skipped_files)} existing files")
    print(f"[*] Wrote {len(saved_files)} new files")

    # Create __init__.py files
    print()
    print("="*60)
    print("CREATING PACKAGE INIT FILES")
    print("="*60)
    print()

    create_init_files(saved_files)

    # Generate requirements.txt from imports
    print()
    print("="*60)
    print("GENERATING REQUIREMENTS.TXT")
    print("="*60)
    print()

    generate_requirements_txt(files)

    # Verify all generated files
    print()
    print("="*60)
    print("VERIFYING GENERATED CODE")
    print("="*60)
    print()

    valid_count = 0
    error_count = 0

    for file_path in saved_files:
        if verify_python_file(file_path):
            valid_count += 1
        else:
            error_count += 1

    print()
    print(f"[*] Verification complete:")
    print(f"    Valid files: {valid_count}/{len(saved_files)}")
    if error_count > 0:
        print(f"    Files with errors: {error_count}")
        print(f"    [WARN] Some files have syntax errors - review before use")
    else:
        print(f"    [OK] All files passed syntax check!")

    # AI Code Review (Ollama validates its own code)
    print()
    print("="*60)
    print("AI CODE REVIEW (Ollama Self-Check)")
    print("="*60)
    print()

    # Only review newly saved files (not skipped ones)
    new_files = [(fp, code) for fp, code in files if (OUTPUT_BASE_DIR / fp) in saved_files]
    review_issues = []

    if not new_files:
        print("[*] No new files to review (all skipped)")
    else:
        for i, (file_path, code) in enumerate(new_files):
            print(f"[{i+1}/{len(new_files)}] Reviewing {file_path}...")
            review = review_code_with_ollama(code, file_path)

            if review['has_errors']:
                print(f"    [WARN] Issues found:")
                print(f"    {review['review'][:200]}...")
                review_issues.append(file_path)
            else:
                print(f"    [OK] No critical issues")

        if review_issues:
            print()
            print(f"[*] Files with potential issues: {len(review_issues)}")
            print(f"    Review these manually: {', '.join(review_issues)}")
        else:
            print()
            print(f"[OK] All {len(new_files)} new files passed AI review!")

    # Rename checkpoint so next reboot does fresh generation
    if checkpoint_file.exists():
        done_name = checkpoint_file.with_name("generation_checkpoint_done.txt")
        checkpoint_file.rename(done_name)
        print(f"[*] Checkpoint renamed to {done_name.name} (prevents stale resume)")

    # Summary
    print()
    print("="*60)
    print("[OK] GENERATION COMPLETE")
    print("="*60)
    print(f"[*] Output directory: {OUTPUT_BASE_DIR.absolute()}")
    print(f"[*] Files parsed: {len(files)}")
    print(f"[*] Files written: {len(saved_files)}")
    print(f"[*] Files skipped: {len(skipped_files)}")
    print(f"[*] Files verified: {valid_count}/{len(saved_files)}")
    print()
    print("Next steps:")
    print(f"  1. Review generated files in {OUTPUT_BASE_DIR}")
    if error_count > 0:
        print("  2. Fix syntax errors in flagged files")
        print("  3. Run tests: python scripts/test_ml_pipeline.py")
    else:
        print("  2. Run tests: python scripts/test_ml_pipeline.py")


if __name__ == "__main__":
    main()
