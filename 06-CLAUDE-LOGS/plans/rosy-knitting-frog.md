# Plan: File Migration to E: Drive (Jan 19+ files)

## Context
User wants to migrate all files modified since 2026-01-19 from the Obsidian Vault on C: drive to an E: drive (512GB, confirmed sufficient space). This includes ~491 CSV files plus all other file types. The self-destruct/remote wipe request has been declined — only the migration is in scope.

## Scope
- **Source**: `C:\Users\User\Documents\Obsidian Vault\`
- **Destination**: `E:\Obsidian Vault\` (mirror of source structure)
- **Filter**: All files with modification date >= 2026-01-19
- **Post-copy**: Keep originals on C: — user manually confirms deletion after reviewing log
- **File types**: All extensions

## What the script does
1. Walk the entire vault directory tree
2. For each file: check `os.path.getmtime()` >= Jan 19, 2026
3. Recreate the same relative path under `E:\Obsidian Vault\`
4. Copy with `shutil.copy2()` (preserves timestamps)
5. Verify: compare file size source vs destination
6. Log every file: timestamp | status (OK/FAIL) | source path | dest path | size
7. Write log to `E:\migration-log-2026-03-14.txt`
8. Print summary: total files, total size, failures

## Script location
`C:\Users\User\Documents\Obsidian Vault\scripts\migrate_to_e_drive.py`

## Key implementation details
- Cutoff date: `datetime(2026, 1, 19, 0, 0, 0)`
- Use `os.walk()` for traversal
- Skip directories that are git internals (`.git/`) and venv (`/venv/`, `/env/`, `/__pycache__/`)
- `shutil.copy2()` preserves modification timestamps
- Verification: `os.path.getsize(src) == os.path.getsize(dst)`
- Log format: `[YYYY-MM-DD HH:MM:SS] [OK/FAIL] <src_path> -> <dst_path> (<size> bytes)`
- Console progress: print every 50 files with running count
- Final summary printed to console and appended to log

## Run command
```
python "C:\Users\User\Documents\Obsidian Vault\scripts\migrate_to_e_drive.py"
```

## Verification
1. Check `E:\migration-log-2026-03-14.txt` for any FAIL entries
2. Spot-check a few files in `E:\Obsidian Vault\PROJECTS\` match source
3. Review log summary line for total count and size
4. Only delete originals from C: after user is satisfied with the log

## Not in scope
- Remote wipe / self-destruct module (declined)
- Scheduling / automation (one-shot script only)
- Compression or encryption of destination files
