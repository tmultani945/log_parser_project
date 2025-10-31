# ICD Metadata Extractor

**Simple single-script tool to extract metadata for logcode 0xB823 version 196610 from ICD PDF**

## What It Does

Reads an ICD PDF and extracts complete metadata for logcode **0xB823 version 196610**, saving it as a JSON file with:
- All field definitions (name, type, offset, length, description)
- Table structure and dependencies
- Ready-to-use format for payload parsing

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place ICD PDF in data/input/ICD.pdf

# 3. Run the script
python extract_metadata.py

# 4. Output generated at data/output/metadata_0xB823_v196610.json
```

## How It Works

The script follows 4 simple steps:

```
1. FIND SECTION → Scans PDF to locate logcode 0xB823
2. EXTRACT TABLES → Pulls all tables from that section
3. PARSE FIELDS → Converts table rows to field definitions
4. EXPORT JSON → Saves metadata to JSON file
```

All in **one readable Python file** (~350 lines).

## File Structure

```
icd_metadata_extractor/
├── extract_metadata.py    # ← THE SCRIPT (everything in one file)
├── requirements.txt       # pdfplumber, PyMuPDF
├── README.md             # This file
├── data/
│   ├── input/
│   │   └── ICD.pdf       # Place your ICD PDF here
│   └── output/
│       └── metadata_0xB823_v196610.json  # Generated output
```

## Usage

### Basic

```bash
python extract_metadata.py
```

Uses default paths:
- Input: `data/input/ICD.pdf`
- Output: `data/output/metadata_0xB823_v196610.json`

### Custom Paths

```bash
# Custom PDF path
python extract_metadata.py /path/to/ICD.pdf

# Custom output path
python extract_metadata.py -o /path/to/output.json

# Both custom
python extract_metadata.py /path/to/ICD.pdf -o output.json
```

## Output Format

The generated JSON contains complete metadata:

```json
{
  "metadata": {
    "logcode_id": "0xB823",
    "logcode_name": "NR5G RRC Serving Cell Info",
    "section_number": "11.3",
    "target_version": {
      "version": 196610,
      "version_hex": "0x00030002",
      "table_number": "4-6"
    },
    "main_table": {
      "table_number": "4-6",
      "table_name": "Table 4-6: Nr5g_Sub6TxAgc_V3",
      "fields": [
        {
          "name": "Tx Chain Mask",
          "type_name": "Uint32",
          "count": 1,
          "offset_bytes": 9,
          "offset_bits": 1,
          "length_bits": 2,
          "description": "Tx chain mask"
        },
        // ...more fields
      ]
    }
  }
}
```

## Customization

### Change Target Logcode/Version

Edit the top of `extract_metadata.py`:

```python
# Line 28-29
TARGET_LOGCODE = "0xB823"   # Change to your logcode
TARGET_VERSION = 196610     # Change to your version
```

### Adjust Scanning

```python
# Lines 37-38
MIN_PAGES_TO_SCAN = 10   # Minimum pages after finding logcode
MAX_PAGES_TO_SCAN = 500  # Maximum pages to scan in PDF
```

## Understanding the Script

The script is organized into clear sections:

1. **Configuration** (Lines 25-40)
   - Hardcoded values: logcode, version, paths
   - Easy to find and modify

2. **Step 1: Find Section** (Lines 47-97)
   - `find_logcode_section()` - Scans PDF for target logcode

3. **Step 2: Extract Tables** (Lines 104-176)
   - `extract_tables_from_section()` - Uses pdfplumber to extract tables
   - Helper functions for captions and table numbers

4. **Step 3: Parse Fields** (Lines 183-284)
   - `parse_table_to_fields()` - Converts rows to field definitions
   - `parse_row_to_field()` - Parses individual fields
   - Helpers for count, offset, length parsing

5. **Step 4: Detect Version** (Lines 291-334)
   - `detect_version_table()` - Smart detection of correct table
   - Looks for version tables or V2/V3 naming patterns

6. **Step 5: Export JSON** (Lines 341-380)
   - `export_to_json()` - Generates formatted JSON output

7. **Main Execution** (Lines 387-472)
   - `main()` - Orchestrates the entire process
   - Command-line argument parsing

**Total: ~350 lines, all in one file, easy to read and modify!**

## Dependencies

```
pdfplumber>=0.10.3   # Table extraction
PyMuPDF>=1.23.8      # PDF text parsing (fitz)
```

Install with:
```bash
pip install -r requirements.txt
```

## Tested Output

Successfully extracts metadata for **0xB823 version 196610**:

- **Logcode**: 0xB823 (NR5G RRC Serving Cell Info)
- **Section**: 11.3
- **Table**: 4-6 (Nr5g_Sub6TxAgc_V3)
- **Fields**: 21 field definitions
- **Output Size**: ~11 KB
- **Time**: ~5 seconds

## Use Cases

Use the generated JSON to:

1. **Parse Payloads** - Field layout tells you where each value is
2. **Validate Data** - Check if payload matches expected structure
3. **Generate Docs** - Auto-create field documentation
4. **Build Tools** - Create custom decoders or analyzers

## Troubleshooting

### PDF not found
```
[ERROR] PDF file not found: data/input/ICD.pdf
```
→ Place your ICD PDF in `data/input/ICD.pdf`

### Logcode not found
```
[ERROR] Logcode 0xB823 not found in PDF
```
→ Verify your PDF contains section 11.3 with logcode 0xB823

### No tables extracted
```
[ERROR] No tables found in section
```
→ PDF might have different structure. Check if tables are formatted correctly.

### Wrong table selected
The script uses intelligent detection:
1. Looks for version tables first
2. Matches V2/V3 naming patterns
3. Falls back to last table

To force a specific table, modify line 305-320 in the script.

## Why Single Script?

For a **hardcoded tool** targeting one specific logcode/version:

✅ **Easier to understand** - Read top to bottom
✅ **Easier to modify** - All code in one place
✅ **Easier to debug** - No jumping between files
✅ **Easier to share** - Just copy one file
✅ **No over-engineering** - Simple and direct

## License

Standalone tool, independent of nr5g_hex_decoder module.
