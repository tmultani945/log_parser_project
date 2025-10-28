# Parsing Large PDFs (5000+ pages)

## Problem

Standard parsing can take **1.6-4+ hours** for large PDFs (5000+ pages), which can cause:
- VSCode to hang or become unresponsive
- Lost progress if the process is interrupted
- No visibility into parsing progress

## Solution

Use the optimized `large_pdf_parser.py` which includes:

1. **Progress Tracking** - Real-time logging with ETA estimates
2. **Checkpointing** - Saves progress every 100 pages
3. **Resume Capability** - Can resume from last checkpoint if interrupted
4. **Batch Processing** - Processes pages in batches to reduce memory usage
5. **Detailed Logging** - All progress saved to `data/parsing_progress.log`

## Quick Start

### Option 1: Using the Batch Script (Recommended for Windows)

```bash
# Run the batch script - it will start parsing in background
parse_large_pdf.bat
```

The script will:
- Start parsing in background mode
- Not block VSCode or your terminal
- Save progress to log files
- Allow you to close the window without stopping the parser

### Option 2: Manual Command

```bash
cd src
python large_pdf_parser.py "../data/input/YOUR_PDF.pdf" "../data/parsed_logcodes.db" 100
```

Parameters:
- `pdf_path`: Path to your PDF file
- `db_path`: Path to output database (default: `../data/parsed_logcodes.db`)
- `batch_size`: Pages per batch/checkpoint (default: 100)

## Monitoring Progress

### Check Log File

```bash
# View real-time progress (Windows)
type data\parsing_progress.log

# View last 20 lines
powershell -command "Get-Content data\parsing_progress.log -Tail 20"

# Follow log in real-time
powershell -command "Get-Content data\parsing_progress.log -Wait -Tail 20"
```

### Check Checkpoint

```bash
type data\parse_checkpoint.json
```

Example checkpoint:
```json
{
  "last_page_processed": 1500,
  "tables_extracted": 3245,
  "timestamp": 1699564123.45
}
```

## Resuming After Interruption

If the parser is interrupted (Ctrl+C, crash, power loss), simply run it again:

```bash
cd src
python large_pdf_parser.py "../data/input/YOUR_PDF.pdf" "../data/parsed_logcodes.db"
```

It will automatically:
1. Detect the checkpoint file
2. Resume from the last saved page
3. Continue parsing where it left off

## Performance Estimates

Based on 5000-page PDF:

| Metric | Estimate |
|--------|----------|
| Total time | 1.6 - 4 hours |
| Pages/minute | 20-50 |
| Seconds/page | 1.2 - 3.0 |
| Memory usage | ~500MB - 2GB |
| Checkpoint frequency | Every 100 pages (~2-5 min) |

## Progress Output Example

```
2025-10-26 10:30:15 - INFO - Starting parse of 5000 pages (batch size: 100)
2025-10-26 10:30:15 - INFO - PDF: ../data/input/large.pdf
2025-10-26 10:30:15 - INFO - Database: ../data/parsed_logcodes.db

2025-10-26 10:32:45 - INFO - Page 100/5000 (2.0%) | Avg: 1.5s/page | ETA: 122.5 min
2025-10-26 10:32:45 - INFO - Batch complete: 100 pages in 150s (1.5s/page), 145 tables found
2025-10-26 10:32:46 - INFO - Checkpoint saved at page 100

2025-10-26 10:35:15 - INFO - Page 200/5000 (4.0%) | Avg: 1.4s/page | ETA: 112.0 min
...
```

## Phase Breakdown

The parser runs in 5 phases:

1. **Table Extraction** (80% of time) - Extract tables from all pages
2. **Merging Continuations** (5% of time) - Combine multi-page tables
3. **Parsing Logcode Sections** (10% of time) - Identify logcode boundaries
4. **Grouping & Storing** (4% of time) - Organize and save to database
5. **Revision History** (1% of time) - Extract revision information

## Tips for Best Performance

1. **Close other applications** - Free up memory and CPU
2. **Don't resize VSCode** - Keeps terminal responsive
3. **Use batch script** - Prevents VSCode from hanging
4. **Monitor via log file** - Instead of watching terminal
5. **Smaller batch sizes** - More frequent checkpoints (safer) but slightly slower
6. **Larger batch sizes** - Faster but less frequent checkpoints (riskier)

## Troubleshooting

### VSCode is hanging

**Solution**: Use the batch script (`parse_large_pdf.bat`) which runs in background mode.

### Want to stop the parser

**Solution**: Press Ctrl+C in the terminal. The checkpoint will be saved automatically.

### Parser seems stuck

**Solution**: Check the log file to see if it's still making progress:
```bash
powershell -command "Get-Content data\parsing_progress.log -Tail 5"
```

### Out of memory error

**Solution**: Use smaller batch size:
```bash
python large_pdf_parser.py "../data/input/large.pdf" "../data/parsed.db" 50
```

### Want to start fresh

**Solution**: Delete the checkpoint file and database:
```bash
del data\parse_checkpoint.json
del data\parsed_logcodes.db
```

## After Parsing Completes

Once parsing is done, use the normal query commands:

```bash
cd src
python app.py list
python app.py query 0x1C07 2
python app.py search "TxAGC"
python app.py revision FL
```

## Files Generated

- `data/parsed_logcodes.db` - SQLite database with all logcode data
- `data/parsing_progress.log` - Detailed progress log
- `data/parse_checkpoint.json` - Checkpoint file (deleted on completion)
