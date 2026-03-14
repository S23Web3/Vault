# 2026-03-13 -- Rust Genius Skill Creation

**Context**: User lost context TWICE before this session on the same task. Logged as lesson.

## What Was Done

Created a comprehensive Rust skill for Claude Code, designed to support building QuickPaste (open-source Windows text expander) and future Rust projects.

### Research Phase
- Searched GitHub for Rust text expander projects
- **Espanso** (13,400+ stars, MIT) confirmed as reference architecture
- Catalogued all relevant crates: `windows` (Microsoft official, replaces `winapi`), `egui`/`eframe`, `tray-icon`, `muda`, `willhook`, `win-hotkeys`, `rdev`, `enigo`, `InputBot`
- Researched Windows API patterns: SendInput, WH_KEYBOARD_LL, UTF-16 handling, DPI awareness
- Researched release profile optimization, static linking, Windows Defender false positive mitigation

### Files Created
1. `C:\Users\User\.claude\skills\rust\SKILL.md` (~310 lines) -- Primary skill file with:
   - 10 hard rules (no `winapi`, `// SAFETY:` on unsafe, clippy zero-warn, etc.)
   - 18-crate decision matrix with version pins + 4 deprecated-DO-NOT-USE entries
   - Project structure template
   - Cargo.toml template (speed priority: lto=fat, codegen-units=1, panic=abort, strip=true)
   - Copy-paste ready patterns: SendInput, system tray, keyboard hook thread, egui phrase list
   - Error handling with anyhow
   - Performance patterns: mimalloc, THREAD_PRIORITY_TIME_CRITICAL, static linking
   - Build & distribution checklist
   - 13-pitfall table with symptoms + fixes
   - Code review checklist

2. `C:\Users\User\.claude\skills\rust\rust-windows-development.md` (~650 lines) -- Deep reference with:
   - Espanso architecture lessons
   - `windows` crate feature flag system
   - SendInput complete reference (Unicode + virtual keys + timing + UIPI)
   - Keyboard hooks complete reference (SetWindowsHookEx + message pump + willhook)
   - egui/eframe lifecycle (layout, widgets, theming, minimize-to-tray)
   - tray-icon + muda event handling
   - JSON persistence with atomic save
   - Thread model (UI + hook + mpsc + shutdown)
   - build.rs + app.rc + app.manifest complete files
   - Static linking & binary size expectations
   - Windows Defender mitigation
   - Debugging on Windows

3. `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` -- Added Rust skill mandatory trigger rule

### Key Decisions
- `windows` crate over deprecated `winapi` -- non-negotiable
- `egui` over Tauri/iced/slint -- best for system utilities, minimal deps
- `tray-icon` + `muda` over systray -- actively maintained by Tauri team
- Direct `SendInput` over `enigo` wrapper -- Windows-only app, no abstraction needed
- `anyhow` for error handling (app, not library)
- `tracing` over `log` -- modern structured logging
- `mimalloc` global allocator -- 5-15% faster

### Context Loss Note
User attempted this task in two prior sessions, both lost to context window exhaustion before completion. This session succeeded by: (1) reading the existing QuickPaste plan first, (2) running research agents in parallel, (3) writing skill files directly without unnecessary exploration.
