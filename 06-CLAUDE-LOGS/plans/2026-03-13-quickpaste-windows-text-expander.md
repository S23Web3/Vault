# Plan: QuickPaste — Open-Source Windows 11 Text Expander

**Date**: 2026-03-13
**Project path**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\`

---

## Context

TypeItIn (wavget.com) was a beloved tool that let users store phrases and paste them with a click or hotkey. It has gone paid and is closed source with questionable privacy (clipboard-based, unknown data handling). The user wants a replacement that is:
- Open source and free forever
- Privacy-first (no clipboard use, no telemetry, no cloud)
- Lightweight Windows 11 tray application
- Built autonomously by Claude in a scoped night session

The analogy is correct: building a better calculator because you can see one is not unethical. Text expanders are a productivity tool category, not proprietary logic.

---

## What This App Does (Scope)

**IN scope:**
- System tray icon (Windows notification area)
- UI panel: user types a label + phrase text, clicks "Add" — stored locally
- List of saved phrases visible in the UI
- Click a phrase button/row to inject the text into whatever window is focused
- Direct keyboard injection (SendInput API) — zero clipboard use
- Delete phrases
- Phrases persist across restarts (local JSON file)
- Single `.exe`, no installer, no runtime required

**OUT of scope (v1):**
- Hotkey/abbreviation triggers (type `:email` and it expands automatically) — Phase 2
- Cloud sync
- Multi-device
- Encryption of phrase store (v2 option)
- Import/export

---

## Technology Choice: Rust + Windows API

**Why Rust:**
- Compiles to a single standalone `.exe` (~12-20MB), zero .NET/Python runtime needed
- Memory safe with no garbage collector pauses
- `winapi` crate gives full access to `SendInput`, `SetWindowsHookEx`, system tray
- Espanso (the leading open-source text expander) is written in Rust — proven approach
- Transparent, auditable, zero-telemetry by design

**Why NOT C# / Python:**
- C# requires .NET runtime (150-300MB), slower cold start
- Python requires interpreter install, 500-2000ms startup, not standalone

**UI approach:**
- Rust + `tray-icon` crate for system tray
- `egui` (immediate-mode GUI, pure Rust, no dependencies) for the phrase manager window
- OR: `wry` (webview) with minimal HTML if egui proves complex for tray integration

**Text injection:**
- `SendInput` Windows API — injects characters directly into the keyboard queue of the focused window
- No clipboard touched. No clipboard history contamination. No Ctrl+V.

**Phrase storage:**
- `%APPDATA%\QuickPaste\phrases.json` — plain JSON, human readable, version-control friendly
- Schema: `[{"label": "Claude summary prompt", "text": "Summarize this chat and give me a prompt..."}]`

---

## Project Structure

```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\
├── Cargo.toml
├── src\
│   ├── main.rs           -- entry point, tray init, message loop
│   ├── phrases.rs        -- load/save phrases.json
│   ├── inject.rs         -- SendInput text injection
│   └── ui.rs             -- egui window (phrase list, add/delete)
├── assets\
│   └── icon.ico          -- tray icon
├── build.rs              -- embed icon as Windows resource
└── README.md
```

---

## Key Crates

| Crate | Purpose |
|-------|---------|
| `winapi` | SendInput, HWND, tray messages, Win32 |
| `tray-icon` | Cross-platform system tray (Tauri project) |
| `eframe` / `egui` | Lightweight immediate-mode GUI |
| `serde` + `serde_json` | phrases.json read/write |
| `dirs` | Resolve `%APPDATA%` path cross-platform |

---

## Architecture Flow

```
Startup
  1. Load phrases from %APPDATA%\QuickPaste\phrases.json (create if missing)
  2. Create system tray icon with right-click menu: [Open | Quit]
  3. Spawn egui window hidden (show on tray click or Open)

User opens UI
  4. egui window shows list of phrases (label + truncated text)
  5. "Add" button: text fields for label + phrase -> save to JSON
  6. "Delete" button per row: remove from list -> save to JSON
  7. "Paste" button per row (or click): call inject::send_text()

inject::send_text(text: &str)
  8. Get foreground window handle (GetForegroundWindow)
  9. Build array of INPUT structs (one per Unicode codepoint)
  10. Call SendInput() — text appears in focused window
  11. Zero clipboard operations. Zero clipboard reads. Zero clipboard writes.
```

---

## Privacy Guarantee

- No network calls anywhere in codebase
- No clipboard read or write
- Phrases stored only in `%APPDATA%\QuickPaste\phrases.json` (user's own machine)
- Single-file exe — user can verify with Process Monitor / Wireshark that no outbound connections exist
- Full source on GitHub (MIT license) — anyone can audit

---

## Build Environment Requirements

The user needs Rust installed:
```
winget install Rustlang.Rustup
rustup toolchain install stable-x86_64-pc-windows-msvc
rustup target add x86_64-pc-windows-msvc
```

VSCode extension: `rust-analyzer` (available in VSCode marketplace, no C++ extension needed for Rust).

Build command:
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste"
cargo build --release
# Output: target\release\quickpaste.exe
```

---

## Autonomous Build Session Plan (Night Session)

The build will be broken into scoped phases, each with a defined time budget and clear deliverable:

| Phase | Task | Deliverable |
|-------|------|-------------|
| Phase 0 | Scaffold: Cargo.toml, main.rs stub, directory structure | Compiles with `cargo check` |
| Phase 1 | phrases.rs: load/save JSON, add/delete operations | Unit-tested with mock data |
| Phase 2 | inject.rs: SendInput Unicode text injection | Tested by injecting "hello" into Notepad |
| Phase 3 | ui.rs: egui phrase list, add/delete/paste buttons | Window opens and renders list |
| Phase 4 | main.rs: tray icon, show/hide window on click, Quit | Full app runs from tray |
| Phase 5 | Polish: icon, app name, window title, error handling | Release build passes |

Each phase is a self-contained commit. If a phase fails, the previous phase's output is still usable.

---

## Verification

1. `cargo build --release` — no errors, produces `target\release\quickpaste.exe`
2. Run `quickpaste.exe` — tray icon appears in system notification area
3. Click tray icon — phrase manager window opens
4. Add phrase: label="test", text="Hello World" — appears in list
5. Open Notepad. Click "Paste" on the phrase. "Hello World" appears in Notepad.
6. Open Windows Settings > Clipboard History — confirm "Hello World" does NOT appear there.
7. Restart `quickpaste.exe` — phrases persist.
8. Process Monitor (Sysinternals): confirm zero network activity from `quickpaste.exe`.

---

## Files Created

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\Cargo.toml`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\src\main.rs`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\src\phrases.rs`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\src\inject.rs`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\src\ui.rs`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\build.rs`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\assets\icon.ico` (placeholder)

---

## Open Questions Resolved

- **Ethics**: Yes — building a better, open-source version of a tool is entirely ethical. It expands access, improves privacy, and benefits users.
- **Language**: Rust (not C++). No VSCode C++ extension needed. Only `rust-analyzer`.
- **Clipboard**: Never used. SendInput only.
- **Night session autonomy**: Claude builds phases sequentially, stops at each phase boundary, reports status.