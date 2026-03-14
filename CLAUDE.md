# Claude Code Instructions — Obsidian Vault

## Plan Storage

When in plan mode, always write plans to TWO locations:
1. The system-required path (e.g. `C:\Users\User\.claude\plans\<name>.md`) — required by plan mode
2. **Also write a copy to:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\<YYYY-MM-DD>-<short-description>.md`

Name the vault copy with today's date and a short kebab-case description of what the plan covers.
Both files should have identical content.

## UI Interactivity Rule

- **"Management" = interactive. "Monitor/view/display" = read-only. Ambiguous = ASK before planning.**
- Plans for any UI must explicitly list what actions ARE included. Anything not listed is OUT — not silently added, not silently assumed excluded.
- Never assume a dashboard is read-only unless the user says "monitor", "view only", or "display only".
- LESSON (2026-02-28): User said "position management" — I built read-only twice. Logs confirmed user never said read-only. Rule violation.

## Skill Loading Rules

- **DASH SKILL MANDATORY** — Before writing ANY Dash code (vince/app.py, vince/layout.py, vince/pages/*.py), ALWAYS load the Dash skill first. No exceptions. Triggers: any file in vince/ directory, `dash.Dash`, `@app.callback`, "Vince dashboard", "B6", `register_page`, `dcc.Store`, `dag.AgGrid`.
- **WEEX SKILL MANDATORY** — Before writing ANY WEEX connector code, ALWAYS load the WEEX skill first. No exceptions. Triggers: any file in `PROJECTS/weex-connector/` directory, `weex_auth`, `api-contract.weex.com`, "WEEX connector", "WEEX API".
- **RUST SKILL MANDATORY** — Before writing ANY Rust code, ALWAYS load the Rust skill first. No exceptions. Triggers: any file in `PROJECTS/quickpaste/` directory, `Cargo.toml`, `.rs` files, `windows` crate, `egui`, `eframe`, `tray-icon`, `SendInput`, "QuickPaste", "Rust".
