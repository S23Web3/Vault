# Windows Startup Setup Guide

**Goal**: Automatically resume Qwen code generation after crash/restart/blue screen/power outage

---

## Step 1: Enable Auto-Login (netplwiz)

This ensures Windows logs in automatically after a restart (no password prompt).

**⚠️ WARNING**: This reduces security. Only use on a secure, personal computer.

1. Press `Win + R`
2. Type `netplwiz` and press Enter
3. **Uncheck**: "Users must enter a user name and password to use this computer"
4. Click **Apply**
5. Enter your password when prompted
6. Click **OK**

**Result**: Windows will auto-login on next boot

---

## Step 1.5: Disable Lock Screen (Optional)

This bypasses the intermediate lock screen (splash screen) for faster boot-to-desktop.

**Method 1: Registry Edit (Works on Home/Pro/Enterprise)**

1. Press `Win + R`, type `regedit`, and press Enter
2. Navigate to: `HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\Personalization`
3. If `Personalization` key does not exist, create it:
   - Right-click `Windows` → New → Key → Name it `Personalization`
4. Right-click in the right pane → New → DWORD (32-bit) Value
5. Name it `NoLockScreen`
6. Double-click `NoLockScreen` and set its value to `1`
7. Click **OK**
8. Restart your PC

**Method 2: Group Policy Editor (Pro/Enterprise only)**

1. Press `Win + R`, type `gpedit.msc`, press Enter
2. Navigate to: Computer Configuration → Administrative Templates → Control Panel → Personalization
3. Double-click "Do not display the lock screen"
4. Select **Enabled**
5. Click **OK**
6. Restart your PC

**Result**: System will boot directly to login screen (no intermediate splash screen)

---

## Step 2: Add Script to Windows Startup

Two methods (choose one):

### Method A: Startup Folder (Recommended)

1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. **Create shortcut**:
   - Right-click → New → Shortcut
   - Location: `C:\Users\User\Documents\Obsidian Vault\trading-tools\START_GENERATION.bat`
   - Name: `Qwen Generation`
4. Click **Finish**

### Method B: Task Scheduler (More robust)

1. Press `Win + R`, type `taskschd.msc`, press Enter
2. Click **Create Basic Task**
3. Name: `Qwen Auto Resume`
4. Trigger: **When I log on**
5. Action: **Start a program**
6. Program: `C:\Users\User\Documents\Obsidian Vault\trading-tools\START_GENERATION.bat`
7. ✅ Check: "Open Properties after finish"
8. In Properties:
   - **General tab**: Check "Run with highest privileges"
   - **Conditions tab**: Uncheck "Start only if on AC power"
   - **Settings tab**: Check "If task fails, restart every 1 minute" (up to 3 times)
9. Click **OK**

---

## Step 3: Test the Setup

### Test 1: Manual Run

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\trading-tools"
.\startup_generation.ps1
```

**Expected**:
- Ollama starts (or detects existing)
- Qwen model loaded
- nvitop opens in new window
- Python script starts
- If checkpoint exists → resumes

### Test 2: Restart Test

1. Close all windows
2. Restart computer
3. Watch for:
   - Auto-login (no password prompt)
   - Script starts automatically after ~10 seconds
   - All 3 windows open (Ollama, nvitop, generation)

---

## How It Works

### On First Run (No Checkpoint)
```
startup_generation.ps1
  ↓
1. Start Ollama → ollama serve (minimized)
2. Verify Qwen → qwen3-coder:30b ready
3. Start nvitop → New PowerShell window
4. No checkpoint → python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md
  ↓
Generates code → Saves checkpoint every 1000 chars
```

### On Crash/Restart (Checkpoint Exists)
```
Computer restarts/blue screen/power outage
  ↓
Windows auto-login (netplwiz)
  ↓
Startup folder → START_GENERATION.bat runs
  ↓
startup_generation.ps1
  ↓
1. Start Ollama → ollama serve (minimized)
2. Verify Qwen → qwen3-coder:30b ready
3. Start nvitop → New PowerShell window
4. Checkpoint detected! → python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md --resume
  ↓
Resumes from checkpoint → Parses existing output → Continues generation
```

---

## Checkpoint File Structure

**Location**: `generation_checkpoint.txt`

**Contents**: Full Ollama response so far (all generated code)

**Resume Logic**:
- Script parses checkpoint to see which files are complete (looks for `✓ filename.py COMPLETE`)
- Continues generating remaining files
- If file was incomplete, it may regenerate from that file

---

## Monitoring After Restart

After auto-restart, you'll see:

**Window 1** (minimized): Ollama server running
**Window 2**: nvitop (GPU monitor)
**Window 3**: Python generation script (streaming output)

---

## Manual Commands

**Force restart from checkpoint**:
```powershell
python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md --resume
```

**Clear checkpoint and start fresh**:
```powershell
Remove-Item generation_checkpoint.txt -Force
python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md
```

**Check checkpoint size**:
```powershell
Get-Item generation_checkpoint.txt | Select-Object Length, LastWriteTime
```

**View last 50 lines of checkpoint**:
```powershell
Get-Content generation_checkpoint.txt -Tail 50
```

---

## Troubleshooting

### Script doesn't start on boot
- Check Task Scheduler → "Last Run Result" (should be 0x0)
- Check startup folder: `shell:startup` → verify shortcut exists
- Check netplwiz → ensure auto-login is enabled

### Ollama fails to start
- Manually run: `ollama serve`
- Check if port 11434 is in use: `netstat -ano | findstr :11434`
- Check Ollama logs: `%LOCALAPPDATA%\Ollama\logs\`

### Checkpoint not resuming
- Verify checkpoint file exists: `generation_checkpoint.txt`
- Check if `--resume` flag is being passed
- Try manual resume: `python auto_generate_files.py QWEN-MASTER-PROMPT-ALL-TASKS.md --resume`

### GPU not detected
- Check nvitop: `nvitop` (run manually)
- Install nvitop if missing: `pip install nvitop`
- Verify CUDA: `nvidia-smi`

---

## Security Notes

- **Auto-login** reduces security (anyone with physical access can access your PC)
- Only enable on personal/development machines
- Consider using BitLocker drive encryption if using auto-login
- Startup scripts run with your user privileges (not admin unless configured)

---

## Estimated Runtime

**Full generation** (20 files, ~3,500 lines):
- First run: 6-12 hours
- Resume after crash: Depends on checkpoint (e.g., 50% done = 3-6 hours remaining)

**Checkpoint frequency**: Every 1000 characters (~30-50 lines of code)

---

**Ready!** Restart your computer to test the full auto-resume flow. 🌙
