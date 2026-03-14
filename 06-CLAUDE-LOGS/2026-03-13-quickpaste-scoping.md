# 2026-03-13 — QuickPaste Text Expander Scoping

## Summary
Scoped and planned **QuickPaste** — an open-source, privacy-first Windows 11 text expander to replace TypeItIn (wavget.com, now paid/closed-source). Context was lost twice before final plan locked.

## Decisions Made
- **Language**: Rust (not C++, not C#, not Python). Single `.exe`, no runtime, ~12-20MB.
- **Text injection**: SendInput Windows API — zero clipboard use, zero clipboard history contamination.
- **UI**: egui (immediate-mode GUI, pure Rust) + tray-icon crate for system tray.
- **Storage**: `%APPDATA%\QuickPaste\phrases.json` — plain JSON, local only.
- **Ethics**: Building an open-source calculator when you can see a Casio is ethical. Text expanders are a tool category, not proprietary logic.

## Research Completed
- TypeItIn functionality analysis (hotkey/abbreviation text expansion)
- 5 tech approaches compared (AutoHotkey, C# WPF, C++ Win32, Python, Rust)
- Privacy analysis: SendInput vs clipboard injection
- Windows 11 compatibility (SendInput broken in new Notepad — known workaround)
- Espanso (leading open-source text expander) confirmed as Rust precedent

## Prerequisites Identified
1. **Rust toolchain NOT installed** — `winget install Rustlang.Rustup` needed
2. **rust-analyzer VSCode extension** — status unknown, user to check
3. **Rust skill for Claude Code** — does not exist at `C:\Users\User\.claude\skills\rust\SKILL.md`, noted as in-the-making
4. **CLAUDE.md rule** — Rust/QuickPaste trigger rule to be added
5. **Project directory** — `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\` does not exist yet

## Plan Location
- System: `C:\Users\User\.claude\plans\robust-moseying-lark.md`
- Vault: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-13-quickpaste-windows-text-expander.md`

## Session 2 — 2026-03-13 (continued)

### Script Audit (setup_rust.ps1) — 8 issues found and fixed
- CRITICAL: No MSVC Build Tools check — added Step 1 warning with VS Build Tools URL
- CRITICAL: `$ErrorActionPreference = "Stop"` at global scope — removed, each section now handles its own errors
- HIGH: PATH reload ran before rustup-init finished — fixed with proper cargo bin addition after install
- HIGH: Duplicate PATH additions — consolidated to single Add-CargoBin helper function
- MEDIUM: `Invoke-Expression` for version checks — replaced with direct cmd calls
- MEDIUM: Project path inside Obsidian Vault — moved to `C:\Users\User\Documents\quickpaste\` (separate repo)
- MEDIUM: No git init — added Step 5 with git init + initial commit
- LOW: Redundant `rustup target add` after `rustup default` — removed

### Repo Structure Created
Separate git repo at `C:\Users\User\Documents\quickpaste\` (outside Obsidian Vault)

Files created:
- `C:\Users\User\Documents\quickpaste\setup_rust.ps1` (fixed, 6 steps)
- `C:\Users\User\Documents\quickpaste\build_quickpaste.py` (overnight build script)
- `C:\Users\User\Documents\quickpaste\docs\QUICKPASTE-UML.md` (10-section UML)
- `C:\Users\User\Documents\quickpaste\docs\BUILD-JOURNAL.md` (phase tracker)
- `C:\Users\User\Documents\quickpaste\.gitignore`

### Key Correction from Rust Skill
Plan referenced `winapi` crate — WRONG. Skill mandates `windows` crate (Microsoft official, 0.58+). UML updated.

### Rust Skill Status
Skill at `C:\Users\User\.claude\skills\rust\SKILL.md` — READ and confirmed complete.
CLAUDE.md trigger rule already added by another session.

## Next Steps
1. User runs `setup_rust.ps1` (as Admin PowerShell)
2. User opens new terminal, verifies `rustc --version`
3. User runs overnight build: `python C:\Users\User\Documents\quickpaste\build_quickpaste.py`
4. Check `docs/BUILD-JOURNAL.md` for phase results
5. Test: `C:\Users\User\Documents\quickpaste\target\release\quickpaste.exe`
