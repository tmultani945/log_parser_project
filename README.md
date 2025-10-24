# NR5G Log Parser Project

A Python-based system for parsing technical PDF documents containing ~100 log codes with multiple versions and related tables. The system extracts logcode data, stores it in a structured format (SQLite/JSON), and provides a query interface.

## 🎯 Features

- **PDF Parsing**: Extracts log codes, versions, and table structures from technical PDFs
- **Table Continuation Handling**: Automatically merges tables split across pages
- **Version Management**: Maps versions to specific tables
- **Dependency Tracking**: Identifies and includes sub-tables referenced by main tables
- **Dual Storage**: SQLite for queries + JSON export
- **CLI Interface**: Easy-to-use command-line tool
- **Robust Extraction**: Handles layout variations, header repetitions, and continuations

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

```bash
# Clone or navigate to project directory
cd log_parser_project

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Parse a PDF

```bash
cd src
python app.py parse /path/to/your/document.pdf
```

This will:
- Extract all log codes and tables from the PDF
- Store everything in `data/parsed_logcodes.db`
- Take a few minutes depending on PDF size

### 2. Query a Log Code

```bash
python app.py query 0x1C07 2
```

This retrieves **Table 4-4** (version 2 of logcode 0x1C07) plus any dependent tables like **Table 4-5**.

### 3. List All Log Codes

```bash
python app.py list
```

### 4. Search for Log Codes

```bash
python app.py search TxAGC
```

## 📖 Detailed Usage

### Parse Command

Parse a PDF and create the database:

```bash
python app.py parse <pdf_file> [options]

Options:
  -j, --export-json FILE    Also export to JSON format
  -d, --database FILE       Database path (default: data/parsed_logcodes.db)

Examples:
  python app.py parse document.pdf
  python app.py parse document.pdf --export-json output.json
```

### Query Command

Query for a specific logcode and version:

```bash
python app.py query <logcode> <version> [options]

Options:
  -o, --output FILE         Save output to file instead of printing
  -d, --database FILE       Database path

Examples:
  python app.py query 0x1C07 2
  python app.py query 0x1C07 2 --output result.txt
```

**Output includes:**
- Main table for the specified version
- All dependent sub-tables
- Formatted with headers: Name | Type Name | Cnt | Off | Len | Description

### List Command

List all available logcodes:

```bash
python app.py list [options]

Example:
  python app.py list
```

### Search Command

Search for logcodes by code or name:

```bash
python app.py search <term> [options]

Examples:
  python app.py search TxAGC
  python app.py search 0x1C
```

### Versions Command

Show all available versions for a logcode:

```bash
python app.py versions <logcode> [options]

Example:
  python app.py versions 0x1C07
```

## 🏗️ Architecture

### Components

```
log_parser_project/
├── data/                      # Generated data
│   ├── parsed_logcodes.db    # SQLite database
│   └── parsed_logcodes.json  # JSON export
├── src/
│   ├── pdf_extractor.py      # PDF extraction layer
│   ├── parser.py             # Parsing & structuring layer
│   ├── datastore.py          # SQLite storage layer
│   ├── query_engine.py       # Query interface layer
│   └── app.py                # CLI application
└── requirements.txt
```

### Data Flow

1. **PDF Extractor** → Extracts raw tables with metadata
2. **Parser** → Structures data into logcodes with version mappings
3. **Datastore** → Persists to SQLite with proper indexing
4. **Query Engine** → Provides formatted query results

### Database Schema

- **logcodes**: Logcode metadata (code, name, section)
- **versions**: Version → table number mappings
- **tables**: Table metadata (title, pages, etc.)
- **table_rows**: Actual table data (6 standard columns)
- **table_deps**: Table dependencies

## 🔒 Domain Rules Implementation

### Canonical Sectioning
- Detects section numbers (e.g., "4.1") and logcodes (e.g., "0x1C07")
- Associates all tables with their parent logcode

### Table Headers
- Normalizes to: `Name | Type Name | Cnt | Off | Len | Description`
- Handles variations in spacing and case

### Versions Table Convention
- Detects tables ending with `_Versions`
- Parses version → table number mappings
- Example: "Version 2 → Table 4-4"

### Version Lookup Behavior
- Query: `get_table("0x1C07", "2")` → Returns Table 4-4
- Automatically includes dependent tables (e.g., Table 4-5)

### Multi-Page Continuation Merge
- Detects "(cont.)" in captions
- Merges continuation pages
- Removes duplicate header rows

### Cross-Table References
- Detects references in "Type Name" column (e.g., "Table 4-5")
- Builds dependency graph
- Returns complete view with all sub-tables

## 🧪 Testing

Test individual components:

```bash
# Test PDF extractor
python src/pdf_extractor.py

# Test parser
python src/parser.py

# Test datastore
python src/datastore.py

# Test query engine
python src/query_engine.py
```

## 📝 Example Output

Query: `python app.py query 0x1C07 2`

```
================================================================================
Table 4-4: Nr5g_Sub6TxAgc_V2
Logcode: 0x1C07 - NR5G Sub6 TxAGC
Section: 4.1
================================================================================

Name           | Type Name | Cnt | Off | Len | Description
----------------------------------------------------------------
Version        | Uint32    | 1   | 0   | 32  |
Systime        | Table 4-5 | 1   | 32  | 32  | systime
Sym Index      | Uint32    | 1   | 64  | 4   | Symbol number having Tx activity
...

================================================================================
Table 4-5: Nr5g_SystemTime
Logcode: 0x1C07 - NR5G Sub6 TxAGC
Section: 4.1
================================================================================

Name    | Type Name    | Cnt | Off | Len | Description
--------------------------------------------------------
Sys FN  | Uint16       | 1   | 0   | 10  | Sysframe Number, range [0 to 1023]
...
```

## 🔧 Advanced Usage

### Programmatic API

```python
from query_engine import QueryEngine

# Initialize
engine = QueryEngine("data/parsed_logcodes.db")

# Query
tables = engine.get_table("0x1C07", "2")
formatted = engine.format_output(tables)
print(formatted)

# Search
results = engine.search_logcode("TxAGC")

# Close
engine.close()
```

### JSON Export

```bash
python app.py parse document.pdf --export-json output.json
```

JSON structure:
```json
{
  "0x1C07": {
    "name": "NR5G Sub6 TxAGC",
    "section": "4.1",
    "versions": ["1", "2", "3"],
    "version_to_table": {
      "2": "4-4"
    },
    "tables": {
      "4-4": {
        "title": "Nr5g_Sub6TxAgc_V2",
        "page_span": [18, 19],
        "rows": [...],
        "dep_tables": ["4-5"]
      }
    }
  }
}
```

## 🐛 Troubleshooting

### PDF Not Parsing Correctly

- Ensure PDF is text-based (not scanned images)
- Check if table structure follows expected format
- Try using OCR fallback for scanned PDFs

### Missing Tables

- Verify table captions follow "Table X-Y Title" format
- Check if continuation pages use "(cont.)" notation
- Ensure headers match standard format

### Query Not Found

- List all logcodes: `python app.py list`
- Check available versions: `python app.py versions <logcode>`
- Search for similar: `python app.py search <term>`

## 📄 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please follow standard practices:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📧 Contact

[Your Contact Information]
