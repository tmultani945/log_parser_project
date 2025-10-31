# Prompt for ICD Metadata Extractor Script

## Task Overview
Create a Python script that extracts structured metadata from an ICD (Interface Control Document) PDF for a specific telecom logcode and version. The script should find the logcode in the PDF's table of contents, extract relevant tables, identify version mappings, and export everything to JSON format.

## Requirements

### 1. Configuration and Command Line Interface
- **Target logcode**: `0xB823` (hardcoded)
- **Target version**: `196610` (decimal representation of 0x00030002, which is version 3.2)
- **Default paths**:
  - Input PDF: `data/input/ICD.pdf`
  - Output JSON: `data/output/metadata_0xB823_v196610.json`
- **CLI arguments**:
  - Positional: `pdf_path` (optional, uses default if not provided)
  - Optional: `-o/--output` for output JSON path
- Use `argparse` for command-line parsing

### 2. Dependencies
- `pdfplumber` - for PDF table extraction
- `json`, `re`, `argparse`, `pathlib`, `datetime`, `typing` - standard library

### 3. Processing Pipeline (5 Steps)

#### Step 1: Find Logcode in Table of Contents
**Function**: `find_logcode_in_toc(pdf_path: str, target_logcode: str) -> Optional[Dict]`

- Scan the first 50 pages of the PDF to find the Table of Contents
- Look for entries matching pattern: `^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)[\s.]*(\d+)`
  - Example: `4.1 LTE/NR5G RRC OTA Packet (0xB823) ......... 45`
  - Captures: section_number, title, logcode_id, page_number
- Build a dictionary mapping logcode → (page_number, section_number, title)
- Convert page numbers from 1-indexed (PDF page numbers) to 0-indexed (pdfplumber array indices)
- Find the end page by looking up the next logcode's start page
- Return dictionary with:
  ```python
  {
      'logcode_id': '0xB823',
      'section_number': '4.1',
      'section_title': 'LTE/NR5G RRC OTA Packet',
      'start_page': 44,  # 0-indexed
      'end_page': 52      # 0-indexed
  }
  ```

#### Step 2: Extract All Tables from Section
**Function**: `extract_tables_from_section(pdf_path: str, section: Dict) -> List[Dict]`

- Iterate through pages from `start_page` to `end_page`
- For each page:
  - Use `page.extract_tables()` to get table data
  - Use `page.extract_text()` to find table captions
  - Match tables to captions by order of appearance
- Extract table captions using pattern: `Table\s+(\d+-\d+)[:\s]*(.+?)(?:\n|$)`
- Handle duplicate table captions intelligently:
  - Skip captions that are just numbers (e.g., "Table 11-55: 0 360")
  - Skip captions that look like table rows (e.g., "1 0 32 ...")
  - Prefer captions that:
    - Start with a letter (not a digit)
    - Don't contain conditional text ("shown only when")
    - Are shorter and cleaner
- For each table, extract:
  - Headers (first row)
  - Data rows (all subsequent non-empty rows)
  - Caption and table number
  - Page number
- Return list of table dictionaries:
  ```python
  [{
      'caption': 'Table 11-55: NR5G Serving Cell Info',
      'headers': ['Name', 'Type Name', 'Cnt', 'Off', 'Len', 'Description'],
      'rows': [[...]],
      'page_number': 45,
      'table_number': '11-55'
  }]
  ```

#### Step 3: Identify and Parse Version Table
**Function**: `find_version_table(tables: List[Dict]) -> Optional[Dict]`

Use a **priority-based detection** approach:

1. **Priority 1**: Check for "Cond" column format (most reliable)
   - Look for tables with a "Cond" column header
   - Also verify that the Name column contains "Version" entries
   - This format is more reliable than caption-based detection

2. **Priority 2**: Check caption for "_Versions" keyword
   - Look for tables with "_version" in the caption (case-insensitive)

**Function**: `parse_version_table(version_table: Dict) -> Dict[int, str]`

Support two different version table formats:

**Format 1: Traditional**
- Columns: `Version | Details`
- Example row: `196610 | Defined in Table 11-55`
- Parse version as integer (supports hex with 0x prefix or decimal)
- Extract table number using regex: `(\d+-\d+)`

**Format 2: Cond Format**
- Columns: `Name | Type Name | Cnt | Off | Len | Cond | Description`
- Example row: `Version | Table 11-55 | 1 | 0 | 32 | 196610 | ...`
- The Cond column contains the version number (in decimal)
- The Type Name column contains the table reference
- Extract table number from Type Name column

Return mapping: `{196610: '11-55', ...}`

#### Step 3.5: Parse Pre-Version Tables
**Function**: `parse_tables_before_version(all_tables: List[Dict], version_table: Optional[Dict]) -> List[Dict]`

- Find all tables that appear **before** the version table in the extracted tables list
- These are typically structure definition tables (like Table 11-43: MajorMinorVersion)
- Parse each table into field definitions
- Return list of parsed tables with:
  ```python
  [{
      'table_number': '11-43',
      'table_name': 'Table 11-43: MajorMinorVersion',
      'page_number': 42,
      'fields': [...]
  }]
  ```

#### Step 4: Parse Tables for Target Version
**Function**: `parse_tables_for_version(...) -> Tuple[Dict, List[Dict]]`

- Look up the main table number for the target version from the version map
- If not found, use fallback: find the last table in the section
- Parse the main table into field definitions
- Find dependencies by scanning field `Type Name` columns for table references
- Parse each dependent table recursively
- If a dependent table is not in the extracted tables, fetch it from the PDF using `fetch_table_from_pdf()`

**Function**: `parse_table_to_fields(table: Dict) -> List[Dict]`

Parse each row into a field definition:
```python
{
    "name": "System Frame Number",
    "type_name": "Uint8",
    "count": 1,
    "offset_bytes": 0,
    "offset_bits": 0,
    "length_bits": 8,
    "description": "System frame number (0-1023)"
}
```

**Field Parsing Rules**:
- Extract columns: Name, Type Name, Cnt, Off, Len, Description
- **Count (Cnt)**: Integer, or -1 for variable/unknown counts ("-", "N/A", "Variable", "Var", "*")
- **Offset (Off)**: Integer in bits → convert to `offset_bytes` (divide by 8) and `offset_bits` (modulo 8)
- **Length (Len)**: Integer in bits

**Dependency Detection**:
- Scan `Type Name` and `Description` fields for pattern: `Table\s+(\d+-\d+)`
- Build set of referenced table numbers

**Function**: `fetch_table_from_pdf(pdf_path: str, table_number: str, section_start: int, section_end: int) -> Optional[Dict]`

Three-tier search strategy when a referenced table is not in extracted tables:
1. Search within the section (most likely location)
2. Expand to ±50 pages from the section
3. Last resort: search entire document

Return the first match found.

#### Step 5: Export to JSON
**Function**: `export_to_json(...)`

Create JSON structure:
```json
{
  "metadata": {
    "logcode_id": "0xB823",
    "logcode_name": "LTE/NR5G RRC OTA Packet",
    "section_number": "4.1",
    "target_version": {
      "version": 196610,
      "version_hex": "0x00030002",
      "table_number": "11-55"
    },
    "version_map": {"196610": "11-55"},
    "pre_version_tables": [...],
    "main_table": {...},
    "dependent_tables": [...]
  },
  "export_info": {
    "generated_at": "2025-01-15T10:30:00",
    "generator": "ICD Metadata Extractor (Corrected)",
    "hardcoded_for": "0xB823 version 196610"
  }
}
```

### 4. Progress Reporting
Print clear progress messages for each step:
```
[1/5] Scanning Table of Contents for 0xB823...
  [OK] Found 0xB823 in ToC
       Section: 4.1 - LTE/NR5G RRC OTA Packet
       Pages: 45 to 53

[2/5] Extracting tables from pages 45 to 53...
  [OK] Extracted 8 tables

[3/5] Looking for version table...
  [OK] Found version table with Cond column: Table 11-54

[3.5/5] Parsing tables before version table...
       Parsed Table 11-43 (page 42) - 2 fields
  [OK] Found 3 tables before version table

[4/5] Parsing tables for version 196610...
  [OK] Version 196610 -> Table 11-55
       Main table: 15 fields
       Dependencies: ['11-56', '11-57']
       Parsed dependency: 11-56 (5 fields)
       Parsed dependency: 11-57 (8 fields)

[5/5] Exporting to JSON...
  [OK] JSON exported successfully!
       File: C:\path\to\metadata_0xB823_v196610.json
       Size: 45,678 bytes
       Pre-version tables: 3
       Main table: 11-55 with 15 fields
       Dependent tables: 2
```

### 5. Error Handling
- Check if PDF exists before processing
- Handle missing logcode in ToC
- Handle missing version in version map
- Handle missing dependent tables (use fallback search)
- Print detailed error messages with traceback
- Return exit code 0 for success, 1 for failure

### 6. Code Structure
Organize code into clear sections:
```python
# Configuration section
TARGET_LOGCODE = "0xB823"
TARGET_VERSION = 196610

# Step 1: Find logcode in ToC
def find_logcode_in_toc(...): ...
def parse_toc(...): ...

# Step 2: Extract tables
def extract_tables_from_section(...): ...
def find_all_table_captions(...): ...
def extract_table_number(...): ...

# Step 3: Parse version table
def find_version_table(...): ...
def parse_version_table(...): ...
def parse_tables_before_version(...): ...

# Step 4: Parse target tables
def parse_tables_for_version(...): ...
def parse_specific_table(...): ...
def parse_table_to_fields(...): ...
def parse_row_to_field(...): ...
def find_dependencies(...): ...
def fetch_table_from_pdf(...): ...

# Step 5: Export
def export_to_json(...): ...

# Main
def main(): ...
```

### 7. Implementation Details
- Use type hints for all function signatures
- Use docstrings for all functions
- Use f-strings for formatting
- Use `Path` objects for file paths
- Handle Unicode properly (`encoding='utf-8'`)
- Use regex with `re.IGNORECASE` where appropriate
- Clean whitespace from extracted text with `.strip()`

### 8. Expected Usage
```bash
# Default paths
python extract_metadata_0xB823_196610.py

# Custom PDF path
python extract_metadata_0xB823_196610.py /path/to/icd.pdf

# Custom output path
python extract_metadata_0xB823_196610.py -o /path/to/output.json

# Both custom
python extract_metadata_0xB823_196610.py /path/to/icd.pdf -o /path/to/output.json
```

## Key Design Decisions

1. **Hardcoded for specific logcode/version**: The script is optimized for 0xB823 version 196610, not a generic solution
2. **ToC-based scanning**: More reliable than text pattern matching across the entire document
3. **Priority-based version table detection**: Cond column format is more reliable than caption-based detection
4. **Smart table merging**: Handles duplicate captions by quality scoring
5. **Lazy table parsing**: Only parses tables needed for the target version (main + dependencies)
6. **Three-tier dependency search**: Efficient strategy for finding referenced tables across the PDF
7. **Pre-version tables**: Captures structure definitions (like MajorMinorVersion) that appear before the version table

## Expected Output Structure
The JSON should contain all the information needed to parse binary payloads without re-reading the PDF.
