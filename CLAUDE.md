# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NR5G Log Parser - A Python system for parsing technical PDF documents containing ~100 log codes with multiple versions and complex table structures. Extracts logcode data, stores in SQLite, and provides a CLI query interface.

## Key Commands

### Development Commands

```bash
# Parse a PDF document
cd src
python app.py parse /path/to/document.pdf

# Query a specific logcode and version
python app.py query 0x1C07 2

# List all available logcodes
python app.py list

# Search for logcodes by term
python app.py search TxAGC

# Show available versions for a logcode
python app.py versions 0x1C07

# Parse and export to JSON
python app.py parse document.pdf --export-json output.json
```

### Testing Individual Components

```bash
# Test each layer independently
python src/pdf_extractor.py
python src/parser.py
python src/datastore.py
python src/query_engine.py
```

## Architecture

### 5-Layer Modular Design

The system uses a strict layered architecture where each layer has a single responsibility:

1. **PDF Extraction Layer** (`pdf_extractor.py`)
   - Extracts raw tables from PDF pages
   - Handles table continuations across pages (detects "(cont.)" in captions)
   - De-duplicates repeated headers
   - Normalizes table headers to standard 6-column format: `Name | Type Name | Cnt | Off | Len | Description`

2. **Parsing Layer** (`parser.py`)
   - Detects logcode sections using pattern: `^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)`
   - Parses "_Versions" tables to extract version→table mappings
   - Builds dependency graph by detecting table references in "Type Name" column
   - Groups tables by their parent logcode

3. **Data Storage Layer** (`datastore.py`)
   - Persists data to SQLite with 6-table normalized schema
   - Tables: `documents`, `logcodes`, `versions`, `tables`, `table_rows`, `table_deps`
   - Provides JSON export functionality
   - Includes indexes on `(logcode)`, `(logcode, version)`, and `(logcode, table_number)`

4. **Query Engine Layer** (`query_engine.py`)
   - High-level query interface
   - Automatically resolves table dependencies recursively
   - Formats output with aligned columns and clear boundaries
   - Provides search and list functionality

5. **Application Layer** (`app.py`)
   - CLI interface using argparse
   - Commands: `parse`, `query`, `list`, `search`, `versions`
   - Error handling and user feedback

### Data Flow

```
PDF → PDFExtractor → LogcodeParser → LogcodeDatastore → QueryEngine → CLI Output
```

### Critical Design Patterns

**Version Mapping**: Tables ending with `_Versions` contain mappings like "Version 2 → Table 4-4". The parser explicitly detects these tables and stores mappings in the `versions` database table.

**Dependency Resolution**: When querying a version (e.g., `query 0x1C07 2`):
1. Look up version "2" → finds table "4-4"
2. Get dependencies of table "4-4" → finds ["4-5"]
3. Return main table + all dependencies in order

**Table Continuation Merging**: Multi-page tables are detected by "(cont.)" in caption and merged during extraction:
- Group tables by table number
- Remove duplicate header rows between continuations
- Preserve page span metadata

## Important Implementation Rules

### When Working with Tables

- All tables must have exactly 6 columns: `Name`, `Type Name`, `Cnt`, `Off`, `Len`, `Description`
- Table numbers follow format: `X-Y` (e.g., "4-4", "4-5")
- Table references in "Type Name" column are parsed to build dependency graph
- Continuation tables are merged at extraction time, not query time

### When Working with Logcodes

- Logcode format: `0x[0-9A-F]+` (e.g., "0x1C07")
- Always uppercase and include "0x" prefix
- Section format: `\d+\.\d+` (e.g., "4.1")
- Each logcode has a name extracted from section header
- **CRITICAL**: Only logcodes from Section 4 "Log Items" should be extracted
- Other sections (MAC, ML1, RRC, NAS, etc.) contain log codes but are NOT part of the primary "Log Items" section
- The parser filters by checking if section starts with "4." (e.g., 4.1, 4.2, 4.3, etc.)

### When Working with Versions

- Versions are strings, not integers (e.g., "2", not 2)
- Version-to-table mappings are stored separately from table data
- A single table can be referenced by multiple versions
- Not all versions may exist for a logcode

### Database Referential Integrity

- Foreign key constraints enforce relationships
- Cascade deletes maintain consistency
- Always use transactions when modifying multiple related records
- The database is the source of truth after parsing

## Common Development Tasks

### Adding Support for New Table Format

1. Modify `pdf_extractor.py`: Update header detection regex
2. Update `STANDARD_HEADERS` constant if column names change
3. Adjust normalization logic in `_normalize_headers()`
4. Test with `python src/pdf_extractor.py`

### Extending Database Schema

1. Modify schema in `datastore.py`: `_create_schema()`
2. Update indexes in `_create_indexes()`
3. Add migration logic if needed
4. Update corresponding query methods
5. Test with in-memory database: `:memory:`

### Adding New CLI Command

1. Add command parser in `app.py`: `subparsers.add_parser()`
2. Create command handler function
3. Add to `main()` command routing
4. Update help text
5. Document in README.md

### Debugging PDF Parsing Issues

1. Run PDF extractor independently: `python src/pdf_extractor.py`
2. Check raw table captions and structure
3. Verify table continuation detection with debug prints
4. Ensure headers match `STANDARD_HEADERS` after normalization
5. Check for unicode/encoding issues in table text

### Performance Optimization

- Parsing is intentionally slow (2-5 min for 100 pages) - accuracy over speed
- Queries are fast (<100ms) due to SQLite indexes
- Don't add caching to parser - parse once, query many times
- For large PDFs, consider processing pages in parallel (not implemented)

## Dependencies

Required packages (install with pip):
- `PyMuPDF==1.23.8` (fitz) - Fast PDF text extraction
- `pdfplumber==0.10.3` - Better table detection
- `pandas==2.1.4` - Optional, for advanced table manipulation

Note: The project has no `requirements.txt` in the repository. Dependencies are documented in README.md and QUICKSTART.md.

## Working Directory

The CLI application (`app.py`) expects to be run from the `src/` directory:
```bash
cd src
python app.py <command>
```

Database and JSON files are stored in `data/` directory relative to project root:
```
log_parser_project/
├── data/
│   ├── parsed_logcodes.db
│   └── parsed_logcodes.json
└── src/
    └── *.py
```

## Testing Strategy

Each module has a test function at the bottom that can be run directly:
```python
if __name__ == "__main__":
    test_extractor()  # Or test_parser(), test_datastore(), etc.
```

Integration testing: Parse a test PDF and verify end-to-end workflow works correctly.

No formal test framework (pytest, unittest) is used - tests are manual via direct execution.

## Code Style

- Type hints on all function signatures
- Docstrings for all classes and public methods
- Dataclasses for data structures
- f-strings for formatting
- List comprehensions preferred over loops where readable
- Explicit is better than implicit - no magic behavior
