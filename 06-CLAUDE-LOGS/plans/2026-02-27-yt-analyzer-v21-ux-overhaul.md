# YT Analyzer v2.1 — UX Overhaul: Cancel, Activity Log, Settings, Speed

**Date:** 2026-02-27
**Purpose:** Fix usability problems discovered during first real run (211 videos, 201 transcripts, 50+ min summarize stage).

---

## Problems

1. **No cancel** — Can't stop the pipeline. Summarize stage = 50-100 min with no abort.
2. **Invisible progress** — `detail_text.text()` overwrites itself. Events flash by unreadable.
3. **No output preview** — Can't see report content until the very end.
4. **No output folder control** — User can't choose where files save. No visibility into defaults.
5. **Channels mix together** — All channels dump into the same `output/` subdirectories.
6. **Summarize is slow with no opt-out** — 201 videos x 15-30 sec = forced 50-100 min wait even if you just want transcripts.
7. **No ETA** — Staring at "70/201" with no idea how long is left.
8. **No resume awareness** — If you cancel at 70/201 and restart, no indication that 70 are already done.
9. **No re-run without re-download** — Can't re-process existing VTTs without hitting YouTube again.
10. **No download button** — Report saved to disk but no way to download it from the browser.

## Implementation Status

- Per-channel namespacing (problem 5) **deferred** — requires refactoring all module imports from `from config import X` to `import config` + `config.X`.
- All other problems addressed in v2.1 build.

## Files Modified

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\gui.py` — Full rewrite
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\fetcher.py` — Added on_process_started callback
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\summarizer.py` — Extended callback + _cached tag
