# Increasing Windows Virtual Memory - Quick Guide

## Visual Step-by-Step Guide

### Step 1: Open Run Dialog
Press: `Win + R`

Type: `sysdm.cpl`

Press: `Enter`

---

### Step 2: System Properties → Advanced
- You should see "System Properties" window
- Click the **"Advanced"** tab at the top
- Look for "Performance" section
- Click **"Settings..."** button

---

### Step 3: Performance Options → Advanced
- New window "Performance Options" opens
- Click **"Advanced"** tab
- Look for "Virtual memory" section (at bottom)
- Current size is shown
- Click **"Change..."** button

---

### Step 4: Configure Virtual Memory

**IMPORTANT: Follow each step exactly!**

1. ☐ **UNCHECK** "Automatically manage paging file size for all drives"
2. ☐ Click on **C:** drive (or your Windows drive) to select it
3. ☐ Select **"Custom size"** (radio button)
4. ☐ Enter **Initial size**: `8192`
5. ☐ Enter **Maximum size**: `16384`
6. ☐ Click **"Set"** button (DON'T SKIP THIS!)
7. ☐ Click **"OK"**
8. ☐ Click **"OK"** on Performance Options
9. ☐ Click **"OK"** on System Properties

---

### Step 5: Restart Computer

**You MUST restart for changes to take effect!**

Save all your work, then restart:
- Start Menu → Power → Restart

---

### Step 6: Verify After Restart

After your computer restarts, verify the changes worked:

**Option A: Run PowerShell Script**
```powershell
cd C:\Users\proca\ICD_code_for_version_ch\log_parser_project
powershell -ExecutionPolicy Bypass -File verify_memory.ps1
```

**Option B: Check Manually**
```powershell
Get-CimInstance Win32_PageFileSetting | Select-Object Name, InitialSize, MaximumSize
```

You should see:
- InitialSize: 8192
- MaximumSize: 16384

---

## What These Numbers Mean

| Setting | Value | Explanation |
|---------|-------|-------------|
| Initial size | 8192 MB | 8 GB - Starting size of virtual memory |
| Maximum size | 16384 MB | 16 GB - Maximum the system can expand to |

This gives Windows enough virtual memory to load large PDF processing libraries.

---

## Troubleshooting

### "Set" button is greyed out
- Make sure you **unchecked** "Automatically manage"
- Make sure you **selected the C: drive**
- Make sure you **clicked "Custom size"**

### Not enough disk space
If you get an error about disk space:
- Use smaller values: Initial=4096, Maximum=8192
- Or free up disk space (delete temp files, etc.)
- Check available space: `dir C:\`

### Changes don't show after restart
- Make sure you clicked **"Set"** before clicking OK
- Try the process again
- Check if you have administrator rights

---

## After Virtual Memory is Increased

Once verified, run the parser:

```bash
cd C:\Users\proca\ICD_code_for_version_ch\log_parser_project\src

python large_pdf_parser.py "../data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" "../data/parsed_logcodes.db" 100
```

Expected output:
```
2025-10-26 14:30:15 - INFO - Starting parse of 5209 pages (batch size: 100)
2025-10-26 14:30:15 - INFO - PDF: ../data/input/80-PC674-2_REV...
2025-10-26 14:30:15 - INFO - Database: ../data/parsed_logcodes.db

=== PHASE 1: Table Extraction ===
2025-10-26 14:30:20 - INFO - Processing batch: pages 0-99 (100 pages)
...
```

---

## Alternative: If You Can't Change Virtual Memory

If you don't have admin rights or can't change settings:

1. **Close all other applications** before parsing
2. **Use ultra-light parser** (uses less memory):
   ```bash
   cd src
   python ultra_light_parser.py "../data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"
   ```
3. **Run on another machine** with more RAM
4. **Ask your IT admin** to increase virtual memory

---

## Quick Reference Commands

```powershell
# Open virtual memory settings
sysdm.cpl

# Check current settings
Get-CimInstance Win32_PageFileSetting | Select Name, InitialSize, MaximumSize

# Check disk space
Get-PSDrive C | Select Used, Free

# Run verification script
powershell -ExecutionPolicy Bypass -File verify_memory.ps1
```

---

## Need More Help?

If you're stuck on any step, let me know which step and I'll provide more detailed guidance!
