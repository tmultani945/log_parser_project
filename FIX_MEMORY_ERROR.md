# Fixing "Paging File Too Small" Error

## Error Message
```
ImportError: DLL load failed while importing _extra: The paging file is too small for this operation to complete.
```

## What This Means

Windows doesn't have enough virtual memory (page file) to load the PDF processing libraries for large files.

## Quick Fixes (Try in Order)

### Option 1: Increase Windows Virtual Memory (Recommended)

1. **Open System Properties**
   - Press `Win + Pause/Break` OR
   - Right-click "This PC" → Properties → Advanced system settings

2. **Navigate to Virtual Memory Settings**
   - Click "Advanced" tab
   - Under "Performance", click "Settings"
   - Click "Advanced" tab again
   - Under "Virtual memory", click "Change"

3. **Increase Page File Size**
   - Uncheck "Automatically manage paging file size"
   - Select your C: drive
   - Select "Custom size"
   - Set:
     - **Initial size**: 8192 MB (8 GB)
     - **Maximum size**: 16384 MB (16 GB)
   - Click "Set"
   - Click "OK" on all windows

4. **Restart Your Computer**
   - Required for changes to take effect

5. **Try Parsing Again**
   ```bash
   cd src
   python large_pdf_parser.py "../data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" "../data/parsed_logcodes.db" 100
   ```

### Option 2: Close Other Applications

Before parsing:
1. Close all web browsers (Chrome, Edge, Firefox)
2. Close any IDEs or heavy applications
3. Free up RAM

Then try parsing again.

### Option 3: Use Smaller Batch Size (Lower Memory)

This uses less memory but takes longer:

```bash
cd src
python large_pdf_parser.py "../data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" "../data/parsed_logcodes.db" 25
```

The `25` means process only 25 pages at a time (default is 100).

### Option 4: Use Ultra-Light Parser (Coming Next)

I can create an even more memory-efficient version that:
- Processes pages one at a time
- Immediately writes to database
- Uses minimal memory

Let me know if you'd like me to create this version.

## Checking Current Virtual Memory

To see your current paging file size:

```powershell
Get-CimInstance Win32_PageFileUsage | Select-Object Name, AllocatedBaseSize, CurrentUsage
```

## Recommended Settings by RAM

| Physical RAM | Initial Size | Maximum Size |
|-------------|--------------|--------------|
| 4 GB | 6144 MB | 12288 MB |
| 8 GB | 8192 MB | 16384 MB |
| 16 GB | 8192 MB | 16384 MB |
| 32+ GB | 4096 MB | 8192 MB |

## Alternative: Run on Another Machine

If your current machine has limited resources:
1. Copy the project to a machine with more RAM
2. Or use a cloud VM (AWS, Azure, Google Cloud)
3. Or ask a colleague with a more powerful machine

## After Fixing

Once you've fixed the memory issue, run:

```bash
cd src
python large_pdf_parser.py "../data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" "../data/parsed_logcodes.db" 100
```

The parser will:
- Show real-time progress with ETA
- Save checkpoints every 100 pages
- Take approximately 1.7-4 hours for 5209 pages
- Not hang VSCode (runs independently)

## Need Help?

If none of these work, let me know and I can:
1. Create an ultra-light parser that uses even less memory
2. Split the parsing into multiple smaller jobs
3. Suggest alternative approaches
