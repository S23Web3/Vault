# Plan: Git Push — Include All .claude Plans

**Date:** 2026-03-14

## Context
Vault has uncommitted changes across session logs, plans, scripts, and projects. The `.claude/plans/` folder also contains plan files that are NOT yet copied to the vault's `06-CLAUDE-LOGS/plans/` directory. The goal is to copy those missing plans into the vault, then commit and push everything.

## Missing Plans (in .claude/plans but NOT in vault)
- `imperative-tumbling-bentley.md`
- `misty-sniffing-quail.md`
- `temporal-nibbling-mist.md`
- `warm-waddling-wren.md`
- `witty-wiggling-forest.md`
- `recursive-dazzling-hedgehog.md` (current session plan — skip or include once finalized)

## Steps

### 1. Copy missing plan files into vault
For each missing file, copy from `C:\Users\User\.claude\plans\<name>.md` to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\<name>.md`.

Use Bash:
```bash
for f in imperative-tumbling-bentley misty-sniffing-quail temporal-nibbling-mist warm-waddling-wren witty-wiggling-forest; do
  cp "/c/Users/User/.claude/plans/${f}.md" "/c/Users/User/Documents/Obsidian Vault/06-CLAUDE-LOGS/plans/${f}.md"
done
```

### 2. Git add all changes
```bash
cd "/c/Users/User/Documents/Obsidian Vault"
git add \
  "06-CLAUDE-LOGS/" \
  "CLAUDE.md" \
  "PRODUCT-BACKLOG.md" \
  "PROJECT-OVERVIEW.md" \
  "PROJECTS/bingx-connector-v2/scripts/run_trade_chart_report.py" \
  "PROJECTS/bingx-connector-v2/scripts/run_trade_chart_report_v2.py" \
  "PROJECTS/bingx-connector-v2/scripts/run_trade_chart_report_v3.py" \
  "PROJECTS/bingx-connector-v3/" \
  "PROJECTS/four-pillars-backtester/BUILD-VINCE-MARKOV.md" \
  "PROJECTS/four-pillars-backtester/python" \
  "PROJECTS/four-pillars-backtester/scripts/test_tdi.py" \
  "PROJECTS/four-pillars-backtester/signals/tdi.py" \
  "PROJECTS/quickpaste/" \
  "PROJECTS/weex-connector/" \
  "scripts/"
```

Note: Exclude `.claude/scheduled_tasks.lock` (lock file, not repo content). Exclude the txt files in `PROJECTS/bingx-connector/` unless user wants them.

### 3. Commit
```bash
git commit -m "$(cat <<'EOF'
Vault update: session logs 2026-03-12 to 2026-03-14, plans, WEEX connector, QuickPaste, bingx-v3, TDI module, trade chart v2/v3, migration scripts

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
EOF
)"
```

### 4. Push
```bash
git push
```

## Files NOT included (intentionally)
- `.claude/scheduled_tasks.lock` — lock file, ephemeral
- `PROJECTS/bingx-connector/*.txt` — scratch notes (confirm with user if wanted)

## Verification
- `git log --oneline -1` should show the new commit
- `git status` should be clean after push
