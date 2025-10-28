# Parallel PDF Parser Guide

## Problem Solved

The original `large_pdf_parser.py` was hanging on a 5000-page PDF due to:
1. **Sequential processing**: Pages were processed one-by-one in a single thread
2. **Memory accumulation**: All tables were kept in memory before processing
3. **No timeout mechanisms**: Could hang indefinitely on problematic pages
4. **Slow section scanning**: Scanning 5000 pages sequentially for logcode sections took too long

## Solution: Parallel Processing

The new `parallel_pdf_parser.py` implements:

### 1. Multi-Process Architecture
- Uses Python's `multiprocessing.Pool` to process pages in parallel
- Automatically detects CPU cores and uses `CPU_COUNT - 1` workers (leaves one core for system)
- Each worker processes a subset of pages independently

### 2. Parallel Table Extraction
- Divides page batches among multiple workers
- Each worker extracts tables from its assigned pages
- Results are collected and merged efficiently

### 3. Parallel Logcode Section Detection
- Splits the 5000 pages into chunks (e.g., 100-page chunks)
- Multiple workers scan pages simultaneously for logcode headers
- Falls back to sequential scanning if parallel approach fails

### 4. Memory Management
- Workers explicitly close PDF resources after processing their batch
- Garbage collection is forced after each batch
- Temporary data is freed as soon as it's no longer needed

### 5. Timeout Protection
- Each worker task has a configurable timeout (default: 5 minutes)
- Prevents indefinite hanging on problematic pages
- Failed batches are logged but don't stop the entire process

### 6. Enhanced Progress Tracking
- Real-time progress updates showing:
  - Current page range
  - Percentage complete
  - Time per page
  - Estimated time to completion
  - Worker performance metrics

### 7. Resumable Processing
- Checkpoint system saves progress after each batch
- Can resume from last checkpoint if interrupted
- Checkpoint file is automatically removed on successful completion

## Usage

### Basic Usage
```bash
cd src
python parallel_pdf_parser.py <pdf_path> [db_path] [batch_size] [num_workers] [timeout]
```

### Using the Batch Script (Windows)
```bash
parse_large_parallel.bat
```

### Examples

1. **Default settings** (auto-detect workers, 200 pages per batch, 5-min timeout):
   ```bash
   python parallel_pdf_parser.py ../data/input/large.pdf
   ```

2. **Custom batch size and workers**:
   ```bash
   python parallel_pdf_parser.py ../data/input/large.pdf ../data/parsed.db 300 6
   ```

3. **With custom timeout** (10 minutes):
   ```bash
   python parallel_pdf_parser.py ../data/input/large.pdf ../data/parsed.db 200 4 600
   ```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pdf_path` | (required) | Path to the PDF file to parse |
| `db_path` | `../data/parsed_logcodes.db` | Output database path |
| `batch_size` | 200 | Pages per batch (higher = more memory, fewer checkpoints) |
| `num_workers` | CPU count - 1 | Number of parallel worker processes |
| `timeout` | 300 | Timeout per worker task in seconds |

## Performance Comparison

### Large PDF Parser (Sequential)
- **5000 pages**: Would hang or take 8+ hours
- **Memory usage**: Accumulates linearly with pages
- **CPU usage**: Single core only (~12-25%)
- **Failure recovery**: Limited

### Parallel PDF Parser
- **5000 pages**: Estimated 2-4 hours (depending on CPU cores)
- **Memory usage**: Controlled per batch with cleanup
- **CPU usage**: Multi-core (~80-90% on all cores)
- **Failure recovery**: Robust with checkpoints and timeouts

## Tuning for Your System

### For systems with more RAM (16GB+)
Increase batch size for fewer checkpoints:
```bash
python parallel_pdf_parser.py input.pdf output.db 500
```

### For systems with many CPU cores (8+)
Use more workers:
```bash
python parallel_pdf_parser.py input.pdf output.db 200 8
```

### For systems with limited RAM (8GB or less)
Reduce batch size and workers:
```bash
python parallel_pdf_parser.py input.pdf output.db 100 2
```

### For unreliable PDFs with many errors
Increase timeout to avoid premature failures:
```bash
python parallel_pdf_parser.py input.pdf output.db 200 4 600
```

## Monitoring Progress

1. **Console output**: Real-time progress with ETA
2. **Log file**: `data/parsing_progress.log` contains detailed logs
3. **Checkpoint file**: `data/parse_checkpoint.json` shows last completed page

### Example Progress Output
```
2025-01-27 10:30:15 - INFO - Processing batch: pages 0-200 with 4 workers
2025-01-27 10:31:42 - INFO - Worker 0: Found 45 tables in pages 0-50
2025-01-27 10:31:43 - INFO - Worker 1: Found 52 tables in pages 50-100
2025-01-27 10:31:44 - INFO - Worker 2: Found 48 tables in pages 100-150
2025-01-27 10:31:45 - INFO - Worker 3: Found 51 tables in pages 150-200
2025-01-27 10:31:45 - INFO - Batch complete: 200 pages in 90.2s (0.45s/page) | Progress: 4.0% | ETA: 96.2 min | Total tables: 196
```

## Troubleshooting

### Issue: Parser hangs on specific pages
**Solution**: Increase timeout or check log file for specific page errors

### Issue: Out of memory errors
**Solution**: Reduce batch_size and/or num_workers
```bash
python parallel_pdf_parser.py input.pdf output.db 50 2
```

### Issue: Parser slower than expected
**Solution**:
- Check CPU usage - if low, increase num_workers
- Check disk usage - ensure database has enough space
- Check log file for repeated errors on specific pages

### Issue: Need to resume after crash
**Solution**: Just run the same command again - it will automatically resume from checkpoint

### Issue: Workers timing out frequently
**Solution**: Increase timeout value or reduce batch size
```bash
python parallel_pdf_parser.py input.pdf output.db 100 4 900
```

## After Parsing

Once parsing is complete, use the query engine:

```bash
cd src

# Query a specific logcode and version
python app.py query 0x1C07 2

# List all logcodes
python app.py list

# Search for logcodes
python app.py search TxAGC

# Show versions for a logcode
python app.py versions 0x1C07
```

## Technical Details

### Worker Function Requirements
- Worker functions must be top-level functions (not class methods)
- Must be picklable for multiprocessing serialization
- Each worker opens its own PDF connection
- Workers explicitly close resources to prevent leaks

### Checkpoint Format
```json
{
  "last_page_processed": 1000,
  "tables_extracted": 2450,
  "timestamp": 1737986415.123
}
```

### Memory Management Strategy
1. Each worker processes its batch independently
2. Worker closes PDF after batch completion
3. Parent process collects results and frees worker data
4. Garbage collection forced after each batch
5. Checkpoint saves state and allows memory reset on resume

## Comparison with Original large_pdf_parser.py

| Feature | large_pdf_parser.py | parallel_pdf_parser.py |
|---------|---------------------|------------------------|
| Page processing | Sequential | Parallel |
| Logcode scanning | Sequential | Parallel |
| Memory management | Accumulative | Batch-based with cleanup |
| Timeout protection | No | Yes (configurable) |
| Worker isolation | N/A | Yes (separate processes) |
| Error handling | Basic | Robust (per-worker + fallback) |
| Progress detail | Moderate | Detailed (per-worker metrics) |
| Resource cleanup | Basic | Explicit close() + gc |
| Resume capability | Yes | Yes (enhanced) |

## Best Practices

1. **Start with defaults**: Let the parser auto-detect optimal workers
2. **Monitor first run**: Watch logs to tune batch_size and timeout
3. **Use batch script**: Easier than remembering parameters
4. **Check logs regularly**: Identify problematic pages early
5. **Clean checkpoint on failure**: If parser behaves oddly, delete checkpoint file
6. **Backup database**: Before re-parsing over existing database

## Future Enhancements

Potential improvements for even better performance:
- Distributed processing across multiple machines
- GPU acceleration for OCR-heavy PDFs
- Streaming processing for unlimited PDF sizes
- Real-time database updates during parsing
- Web dashboard for monitoring progress
