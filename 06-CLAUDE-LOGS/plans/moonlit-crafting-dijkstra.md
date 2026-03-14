# Plan: Rust Genius Skill for Windows Desktop Apps

**Date**: 2026-03-13
**Context loss note**: User lost context TWICE before this session. Logging this as a lesson.

---

## Context

QuickPaste (open-source Windows text expander, TypeItIn replacement) was planned in a prior session. The plan specifies Rust + egui + tray-icon + SendInput. Before building, the user wants a comprehensive Rust skill file created -- a "genius" reference packed with performance tips, crate decisions, Windows API patterns, and gotchas. This skill will be loaded automatically whenever Rust work is triggered, ensuring every future Rust build session starts with expert-level context.

Research confirmed: **Espanso** (13,400+ stars, MIT) is the reference architecture. The `windows` crate (Microsoft official) replaces deprecated `winapi`. Key performance insight: dedicated hook threads with `THREAD_PRIORITY_TIME_CRITICAL`, zero-copy UTF-16 via `w!()` macro, and `SendInput` with KEYEVENTF_UNICODE for sub-millisecond text injection.

---

## Deliverables

### 1. `C:\Users\User\.claude\skills\rust\SKILL.md` (~300 lines)

Primary skill file, loaded automatically. Contains:

| Section | Content |
|---------|---------|
| Hard Rules (10) | `windows` not `winapi`, `// SAFETY:` on unsafe, clippy zero-warn, no `unwrap()` in prod, doc comments on pub fns, `dirs` for paths, `w!()` for UTF-16, hook thread model, single-instance, `?` over `unwrap` |
| Crate Decision Matrix | 18 crates with version pins + 4 deprecated-DO-NOT-USE entries |
| Project Structure Template | Standard layout for tray/GUI Rust apps |
| Cargo.toml Templates | Speed profile (`lto=fat, codegen-units=1`) + size profile (`opt-level=z`) |
| SendInput Pattern | Copy-paste ready `send_text()` function with Unicode/surrogate handling |
| System Tray Pattern | `tray-icon` + `muda` menu builder |
| Keyboard Hook Pattern | Dedicated thread + mpsc channel model |
| egui Pattern | Phrase list with add/delete/paste, borrow-checker-safe action collection |
| Error Handling | `anyhow::Result` + `context()` chains |
| Performance Patterns | Thread priority, mimalloc, static linking, release flags |
| Build & Distribution | Icon embed, DPI manifest, Defender avoidance, `cargo-wix` |
| Pitfalls Table | 13 common Windows Rust pitfalls with symptoms + fixes |
| Code Review Checklist | Pre-delivery verification steps |

### 2. `C:\Users\User\.claude\skills\rust\rust-windows-development.md` (~600-800 lines)

Deep reference companion. Full code examples and API details for:

- Espanso architecture lessons (trait-based platform abstraction, multi-process model)
- `windows` crate feature flag system + complete feature list for QuickPaste
- SendInput complete reference (Unicode, virtual keys, timing, UIPI)
- Keyboard hooks complete reference (SetWindowsHookEx, free function requirement, message pump)
- egui/eframe lifecycle (App::update, layout, theming, tray integration, minimize-to-tray)
- tray-icon + muda event handling
- JSON persistence with atomic save (write tmp, rename)
- Thread model (main=UI, hook=dedicated, mpsc comms, AtomicBool shutdown)
- build.rs + .rc + .manifest complete files
- Static linking & distribution (MSVC, static_vcruntime, no UPX)
- Windows Defender mitigation
- Debugging on Windows (RUST_BACKTRACE, tracing, dbgview)

### 3. Edit `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md`

Add to Skill Loading Rules:
```
- **RUST SKILL MANDATORY** -- Before writing ANY Rust code, ALWAYS load the Rust skill first.
  No exceptions. Triggers: any file in `PROJECTS/quickpaste/` directory, `Cargo.toml`,
  `.rs` files, `windows` crate, `egui`, `eframe`, `tray-icon`, `SendInput`, "QuickPaste", "Rust".
```

### 4. Session log + INDEX.md update

- Create `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-rust-skill-creation.md`
- Append to INDEX.md

---

## Key Crate Decisions (locked)

| Job | Crate | Why |
|-----|-------|-----|
| Windows API | `windows` 0.58+ | Microsoft official, replaces deprecated `winapi` |
| UTF-16 literals | `w!()` from `windows` | Zero-cost compile-time conversion |
| GUI | `egui` + `eframe` 0.29+ | Immediate mode, pure Rust, minimal deps, best for utilities |
| System tray | `tray-icon` 0.19+ | Tauri team, works with egui, cross-platform |
| Tray menu | `muda` 0.15+ | Companion to tray-icon |
| Input injection | Direct `SendInput` via `windows` | No wrapper needed, KEYEVENTF_UNICODE for text |
| Keyboard hooks | `willhook` 0.3+ | Safe WH_KEYBOARD_LL wrapper (Phase 2 hotkeys) |
| Serialization | `serde` + `serde_json` 1.0 | Standard, derive macros |
| Paths | `dirs` 6.0+ | Resolves %APPDATA% correctly |
| Error handling | `anyhow` 1.0 | For applications (thiserror for libraries) |
| Logging | `tracing` + `tracing-subscriber` | Modern structured logging |
| Single instance | `single_instance` 0.3+ | Named mutex |
| Icon embed | `embed-resource` 3.0+ | In build.rs |
| Allocator | `mimalloc` 0.1+ | 5-15% faster than default |

**DEPRECATED -- skill will flag these as errors:**
- `winapi` (unmaintained since 2021)
- `systray` (abandoned)
- `native-windows-gui` (stale)

---

## Performance Architecture (speed + response priority)

The user explicitly wants speed and instant response for copy-paste workflows:

1. **Hook thread at TIME_CRITICAL priority** -- keyboard events processed before anything else
2. **SendInput batching** -- all Unicode codepoints for a phrase sent in one `SendInput()` call (not one-at-a-time)
3. **Zero-copy UTF-16** -- `w!()` macro for static strings, `.encode_utf16()` for dynamic
4. **mimalloc allocator** -- eliminates default allocator overhead
5. **Release profile**: `opt-level=3, lto=fat, codegen-units=1, panic=abort, strip=true`
6. **Static linking** -- `RUSTFLAGS="-C target-feature=+crt-static"` for standalone .exe, no runtime deps
7. **egui repaint control** -- `request_repaint_after()` instead of constant 60fps when idle
8. **Phrase store in memory** -- JSON loaded once at startup, kept in Vec, saved on mutation only

---

## Verification

1. Skill files exist and are well-formed markdown
2. `CLAUDE.md` has Rust skill trigger rule
3. Opening a new Claude Code session and mentioning "QuickPaste" or "Cargo.toml" should trigger the Rust skill
4. Skill content matches research findings (crate versions, API patterns, pitfalls)
5. Code snippets in skill are syntactically valid Rust (verified by reading, not compiling -- skill files are .md)
6. Session log created in `06-CLAUDE-LOGS/` and INDEX.md updated

---

## Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `C:\Users\User\.claude\skills\rust\SKILL.md` |
| CREATE | `C:\Users\User\.claude\skills\rust\rust-windows-development.md` |
| EDIT | `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` (add Rust skill rule) |
| CREATE | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-rust-skill-creation.md` |
| EDIT | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md` (append row) |
