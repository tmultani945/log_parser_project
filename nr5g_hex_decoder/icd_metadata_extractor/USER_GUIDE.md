# User Guide: 0xB823 ICD Metadata Extractor and Payload Parser

## Table of Contents
1. [Overview](#overview)
2. [Workflow Architecture](#workflow-architecture)
3. [File 1: extract_metadata_0xB823_196610.py](#file-1-extract_metadata_0xb823_196610py)
4. [File 2: parse_payload_0xB823.py](#file-2-parse_payload_0xb823py)
5. [Complete Workflow Example](#complete-workflow-example)
6. [Data Structures](#data-structures)
7. [Error Handling](#error-handling)

---

## Overview

This system consists of two Python scripts that work together to:
1. **Extract metadata** from ICD PDF documents for logcode 0xB823
2. **Parse binary payloads** using the extracted metadata

### Purpose
- **Target Logcode**: 0xB823 (NR5G log item)
- **Target Version**: 196610 (0x00030002 = version 3.2)
- **Input**: ICD PDF document + Binary hex payload
- **Output**: Structured JSON with parsed field values

### Key Features
- Table of Contents (ToC) based scanning
- Version-aware table parsing
- Dependency graph resolution
- Bit-level field extraction
- Nested table structure support
- Little-endian byte order handling

---

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 1: METADATA EXTRACTION             │
├─────────────────────────────────────────────────────────────┤
│  PDF Document                                                │
│       ↓                                                      │
│  [1] Scan ToC → Find logcode location                       │
│       ↓                                                      │
│  [2] Extract Tables → Get all tables from section           │
│       ↓                                                      │
│  [3] Parse Version Table → Map versions to tables           │
│       ↓                                                      │
│  [4] Parse Required Tables → Extract field definitions      │
│       ↓                                                      │
│  [5] Export JSON → Save metadata                            │
│       ↓                                                      │
│  metadata_0xB823_v196610.json                               │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 2: PAYLOAD PARSING                 │
├─────────────────────────────────────────────────────────────┤
│  Metadata JSON + Binary Payload (hex)                       │
│       ↓                                                      │
│  [1] Load Metadata → Build table index                      │
│       ↓                                                      │
│  [2] Convert Hex to Bytes                                   │
│       ↓                                                      │
│  [3] Parse Version → Extract Major.Minor                    │
│       ↓                                                      │
│  [4] Parse Main Table → Read fields recursively             │
│       ↓                                                      │
│  [5] Format Output → Structure JSON                         │
│       ↓                                                      │
│  parsed_0xB823.json                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## File 1: extract_metadata_0xB823_196610.py

### Purpose
Extracts structured metadata from ICD PDF documents for a specific logcode and version.

### Libraries Used

```python
import json          # JSON file I/O
import re            # Regular expressions for pattern matching
import argparse      # Command-line argument parsing
from pathlib import Path  # Cross-platform file path handling
from datetime import datetime  # Timestamp for export info
from typing import List, Dict, Optional, Tuple  # Type hints
import pdfplumber    # PDF table extraction (main library)
```

**Key Library: pdfplumber**
- Extracts text and tables from PDF files
- More accurate table detection than PyMuPDF
- Handles multi-column layouts and complex table structures

---

### Configuration (Lines 22-32)

```python
TARGET_LOGCODE = "0xB823"
TARGET_VERSION = 196610  # 0x00030002 = version 3.2
DEFAULT_PDF = "data/input/ICD.pdf"
DEFAULT_OUTPUT = "data/output/metadata_0xB823_v196610.json"
```

**Purpose**: Hardcoded configuration for specific logcode extraction.

---

### STEP 1: Find Logcode in Table of Contents

#### Function: `find_logcode_in_toc()` (Lines 38-80)

**Purpose**: Locate the logcode section in the PDF using ToC entries.

**Logic**:
1. Opens PDF with pdfplumber
2. Calls `parse_toc()` to scan ToC pages
3. Finds target logcode in ToC map
4. Determines start and end pages by finding next logcode

**Returns**: Dictionary with:
- `logcode_id`: "0xB823"
- `section_number`: "4.1" (section in document)
- `section_title`: "NR5G Serving Cell Info"
- `start_page`: 42 (0-indexed)
- `end_page`: 45

**Key Pattern Matching**:
```python
# Pattern: "4.1 Name (0xB823) ......... 45"
toc_pattern = re.compile(
    r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)[\s.]*(\d+)',
    re.MULTILINE
)
```

#### Function: `parse_toc()` (Lines 83-116)

**Purpose**: Build complete ToC mapping for all logcodes.

**Logic**:
1. Scans first 50 pages (ToC usually at beginning)
2. Extracts text from each page
3. Finds all ToC entries matching pattern
4. Builds dict: `logcode_id → (page_num, section_num, title)`

**Why This Matters**: ToC-based scanning is much faster than searching entire PDF.

---

### STEP 2: Extract All Tables from Section

#### Function: `extract_tables_from_section()` (Lines 123-174)

**Purpose**: Extract all tables from the logcode's page range.

**Logic**:
```python
for page_num in range(start_page, end_page + 1):
    page = pdf.pages[page_num]
    tables = page.extract_tables()  # pdfplumber extracts tables

    # Find captions on this page
    all_captions = find_all_table_captions(page_text, page_num)

    for idx, table_data in enumerate(tables):
        # Extract headers and rows
        headers = [str(cell).strip() for cell in table_data[0]]
        rows = [cleaned_row for row in table_data[1:]]

        # Match caption by index
        caption = all_captions[idx]
        table_number = extract_table_number(caption)  # e.g., "11-55"
```

**Returns**: List of table dictionaries with:
- `caption`: "Table 11-55: NR5G Serving Cell Info"
- `headers`: ["Name", "Type Name", "Cnt", "Off", "Len", "Description"]
- `rows`: [["Version", "Table 11-43", "1", "0", "32", "..."]]
- `page_number`: 42
- `table_number`: "11-55"

#### Function: `find_all_table_captions()` (Lines 177-234)

**Purpose**: Extract clean table captions from page text.

**Logic - Smart Caption Detection**:
1. Finds all "Table X-Y: Caption" patterns
2. Filters out false matches (table data that looks like captions)
3. Uses quality scoring to pick best caption for duplicates

**Quality Scoring Algorithm**:
```python
def caption_quality(name):
    score = 0
    if re.match(r'^[A-Za-z]', name):  # Starts with letter
        score += 10
    if not re.search(r'(shown|only|when|<=|>=)', name):  # Not conditional
        score += 5
    if len(name) < 50:  # Shorter is better
        score += 3
    if not re.match(r'^\d', name):  # No digits at start
        score += 2
    return score
```

**Why This Matters**: PDFs often have multiple "Table X-Y" text on same page (captions, references, data). This ensures we get the actual caption.

#### Function: `extract_table_number()` (Lines 237-240)

**Purpose**: Extract "X-Y" format table number from caption.

**Pattern**: `r"Table\s+(\d+-\d+)"`

---

### STEP 3: Identify and Parse Version Table

#### Function: `find_version_table()` (Lines 247-274)

**Purpose**: Find the special table that maps versions to table numbers.

**Logic - Two Detection Methods**:

**Priority 1: Cond Column Format** (Most Reliable)
```python
for table in tables:
    if any('cond' in str(h).lower() for h in headers):
        # Check if Name column has "Version" entries
        for row in table['rows']:
            if 'version' in str(row[0]).lower():
                return table  # Found it!
```

**Priority 2: Caption-Based Detection**
```python
for table in tables:
    if '_version' in table['caption'].lower():
        return table
```

**Why Two Methods**: Different ICD versions use different formats for version tables.

#### Function: `parse_version_table()` (Lines 277-366)

**Purpose**: Parse version table to extract version → table_number mappings.

**Format 1: Traditional _Versions Table**
```
| Version | Details                  |
|---------|--------------------------|
| 2       | Defined in Table 11-55   |
| 3       | Defined in Table 11-56   |
```

**Format 2: Cond Column Table**
```
| Name      | Type Name  | Cnt | Off | Len | Cond   |
|-----------|------------|-----|-----|-----|--------|
| Version 2 | Table 11-55| 1   | 0   | 32  | 196610 |
```

**Logic**:
```python
if cond_idx is not None:
    # Format 2: Cond column table
    for row in rows:
        cond_str = row[cond_idx]  # "196610"
        type_name = row[1]         # "Table 11-55"

        table_number = extract_table_ref(type_name)  # "11-55"
        version_num = int(cond_str)  # 196610

        version_map[version_num] = table_number
else:
    # Format 1: Traditional
    for row in rows:
        version_str = row[0]  # "2" or "0x00030002"
        details = row[1]      # "Defined in Table 11-55"

        table_number = extract_table_ref(details)
        version_num = parse_version(version_str)

        version_map[version_num] = table_number
```

**Returns**: `{196610: "11-55", 196611: "11-56"}`

#### Function: `parse_tables_before_version()` (Lines 369-421)

**Purpose**: Parse all tables that appear BEFORE the version table.

**Why This Matters**:
- These are typically shared structure definitions (like "MajorMinorVersion")
- Used by multiple versions
- Must be parsed to resolve dependencies

**Logic**:
```python
# Find index of version table
version_table_index = all_tables.index(version_table)

# Parse everything before it
for idx in range(version_table_index):
    table = all_tables[idx]
    fields = parse_table_to_fields(table)
    pre_version_tables.append({
        'table_number': table_number,
        'table_name': caption,
        'fields': fields
    })
```

---

### STEP 4: Parse Only Required Tables for Target Version

#### Function: `parse_tables_for_version()` (Lines 460-525)

**Purpose**: Efficiently parse only the tables needed for target version.

**Logic**:
1. Look up main table number from version map
2. Parse main table
3. Find dependencies (tables referenced in Type Name column)
4. Parse dependent tables recursively

```python
# Get main table number
main_table_num = version_map[196610]  # "11-55"

# Parse main table
main_table = parse_specific_table(all_tables, version_table, "11-55")

# Find dependencies
main_deps = find_dependencies(main_table['fields'])  # {"11-43", "11-56"}

# Parse each dependency
for dep_table_num in main_deps:
    dep_table = parse_specific_table(all_tables, version_table, dep_table_num)
    dependent_tables.append(dep_table)
```

**Efficiency**: Only parses ~3-5 tables instead of all ~20 tables in section.

#### Function: `parse_specific_table()` (Lines 428-457)

**Purpose**: Parse a specific table by table number.

**Handles Duplicates**: If multiple tables with same number exist (continuations), picks the one with most rows.

#### Function: `parse_table_to_fields()` (Lines 528-537)

**Purpose**: Convert table rows into structured field definitions.

**Calls**: `parse_row_to_field()` for each row.

#### Function: `parse_row_to_field()` (Lines 540-568)

**Purpose**: Parse a single table row into a field definition.

**Logic**:
```python
# Map row cells to headers
row_dict = {
    "Name": "Version",
    "Type Name": "Table 11-43",
    "Cnt": "1",
    "Off": "0",
    "Len": "32",
    "Description": "Major.Minor version"
}

# Extract field properties
name = "Version"
type_name = "Table 11-43"
count = 1
offset_bits = 0  # "Off" in bits
length_bits = 32  # "Len" in bits

# Convert to bytes
offset_bytes = 0 // 8 = 0
offset_bits_remainder = 0 % 8 = 0

# Return structured field
{
    "name": "Version",
    "type_name": "Table 11-43",
    "count": 1,
    "offset_bytes": 0,
    "offset_bits": 0,
    "length_bits": 32,
    "description": "Major.Minor version"
}
```

#### Function: `parse_count()` (Lines 571-579)

**Purpose**: Parse count field, handling special values.

**Logic**:
- "-", "N/A", "Variable", "Var", "*" → returns -1 (variable count)
- Numeric string → returns integer
- Invalid → returns -1

#### Function: `parse_number()` (Lines 582-590)

**Purpose**: Safely parse numeric strings.

**Returns**: Integer or 0 if unparseable.

#### Function: `find_dependencies()` (Lines 593-608)

**Purpose**: Find all table references in field definitions.

**Logic**:
```python
dependencies = set()
table_pattern = r"Table\s+(\d+-\d+)"

for field in fields:
    # Check Type Name: "Table 11-43"
    if match in field['type_name']:
        dependencies.add("11-43")

    # Check Description: "See Table 11-56 for details"
    if match in field['description']:
        dependencies.add("11-56")

return dependencies  # {"11-43", "11-56"}
```

#### Function: `fetch_table_from_pdf()` (Lines 611-690)

**Purpose**: Fetch a table that wasn't in extracted tables (fallback).

**Search Strategy**:
1. Search within section (most likely)
2. Expand to ±50 pages
3. Search entire document (last resort)

**Why Needed**: Some dependencies may be in different sections.

---

### STEP 5: Export to JSON

#### Function: `export_to_json()` (Lines 697-746)

**Purpose**: Export all extracted metadata to JSON file.

**Output Structure**:
```json
{
  "metadata": {
    "logcode_id": "0xB823",
    "logcode_name": "NR5G Serving Cell Info",
    "section_number": "4.1",
    "target_version": {
      "version": 196610,
      "version_hex": "0x00030002",
      "table_number": "11-55"
    },
    "version_map": {
      "196610": "11-55"
    },
    "pre_version_tables": [
      {
        "table_number": "11-43",
        "table_name": "Table 11-43: MajorMinorVersion",
        "fields": [...]
      }
    ],
    "main_table": {
      "table_number": "11-55",
      "table_name": "Table 11-55: NR5G Serving Cell Info",
      "fields": [...]
    },
    "dependent_tables": [...]
  },
  "export_info": {
    "generated_at": "2025-01-15T10:30:00",
    "generator": "ICD Metadata Extractor (Corrected)",
    "hardcoded_for": "0xB823 version 196610"
  }
}
```

---

### Main Execution Flow (Lines 752-823)

```python
def main():
    # 1. Parse command-line args
    args = argparse.ArgumentParser()
    pdf_path = args.pdf_path or DEFAULT_PDF
    output_path = args.output or DEFAULT_OUTPUT

    # 2. Find logcode in ToC
    section = find_logcode_in_toc(pdf_path, "0xB823")

    # 3. Extract all tables from section
    all_tables = extract_tables_from_section(pdf_path, section)

    # 4. Find and parse version table
    version_table = find_version_table(all_tables)
    version_map = parse_version_table(version_table)

    # 5. Parse pre-version tables
    pre_version_tables = parse_tables_before_version(all_tables, version_table)

    # 6. Parse tables for target version
    main_table, dependent_tables = parse_tables_for_version(
        all_tables, version_table, version_map, 196610, pdf_path, section
    )

    # 7. Export to JSON
    export_to_json(section, main_table, dependent_tables,
                   pre_version_tables, version_map, output_path)
```

**Usage**:
```bash
python extract_metadata_0xB823_196610.py [pdf_path] [-o output.json]
```

---

## File 2: parse_payload_0xB823.py

### Purpose
Parse binary payloads using the metadata extracted by File 1.

### Libraries Used

```python
import sys           # System utilities
import json          # JSON file I/O
from pathlib import Path  # File path handling
from typing import Dict, List, Any, Tuple  # Type hints
import struct        # Binary data packing/unpacking (little-endian)
```

**Key Library: struct**
- Handles binary data unpacking with proper byte order
- `'<'` prefix = little-endian format
- `'B'` = unsigned byte, `'H'` = unsigned short, `'I'` = unsigned int, `'Q'` = unsigned long long

---

### Class: PayloadParser

#### `__init__()` (Lines 22-40)

**Purpose**: Initialize parser with metadata from JSON.

**Logic**:
```python
# Load JSON
with open(metadata_path, 'r') as f:
    data = json.load(f)

# Support two formats
if 'metadata' in data:
    self.metadata = data['metadata']  # Full format from File 1
else:
    self.metadata = data  # Simple format

# Build table lookup index
self._build_table_index()
```

#### `_build_table_index()` (Lines 42-55)

**Purpose**: Build fast lookup dictionary for all tables.

**Logic**:
```python
self.tables = {}

# Add pre-version tables (e.g., 11-43: MajorMinorVersion)
for pre_table in metadata['pre_version_tables']:
    self.tables["11-43"] = pre_table

# Add main table (e.g., 11-55: NR5G Serving Cell Info)
main = metadata['main_table']
self.tables["11-55"] = main

# Add dependent tables
for dep_table in metadata['dependent_tables']:
    self.tables[dep_table['table_number']] = dep_table

# Result: {"11-43": {...}, "11-55": {...}, "11-56": {...}}
```

**Why This Matters**: O(1) table lookup during recursive parsing.

---

### Binary Data Parsing Functions

#### `_hex_string_to_bytes()` (Lines 57-70)

**Purpose**: Convert hex string to bytes object.

**Logic**:
```python
# Input: "02 00 03 00 01 01 00 7B\n00 1A 80 2E"
clean_hex = ''.join(hex_string.split())  # Remove spaces/newlines
# Result: "020003000101007B001A802E"

bytes_obj = bytes.fromhex(clean_hex)
# Result: b'\x02\x00\x03\x00\x01\x01\x00\x7B\x00\x1A\x80\x2E'
```

#### `_read_bits()` (Lines 72-133)

**Purpose**: Read arbitrary bit-length fields from byte array.

**Handles Two Cases**:

**Case 1: Byte-Aligned Fields** (offset_bits = 0, length_bits = multiple of 8)
```python
if offset_bits == 0 and length_bits % 8 == 0:
    num_bytes = length_bits // 8  # 32 bits → 4 bytes
    byte_slice = data[offset_bytes:offset_bytes + num_bytes]

    # Use struct for proper little-endian unpacking
    if num_bytes == 1:
        return struct.unpack('<B', byte_slice)[0]  # unsigned byte
    elif num_bytes == 2:
        return struct.unpack('<H', byte_slice)[0]  # unsigned short
    elif num_bytes == 4:
        return struct.unpack('<I', byte_slice)[0]  # unsigned int
    elif num_bytes == 8:
        return struct.unpack('<Q', byte_slice)[0]  # unsigned long long
```

**Example**:
```python
data = b'\x02\x00\x03\x00'
value = _read_bits(data, offset_bytes=0, offset_bits=0, length_bits=16)
# Reads bytes [0:2] = b'\x02\x00'
# struct.unpack('<H', b'\x02\x00') = 2  (little-endian: 0x0002)
```

**Case 2: Bit-Level Fields** (non-byte-aligned)
```python
# Example: Read 4 bits starting at byte 0, bit 4
# Data: 0xAB (binary: 1010 1011)
# Want bits [4:8] = 1010

total_bit_offset = 0 * 8 + 4 = 4
start_byte = 4 // 8 = 0
end_byte = (4 + 4 + 7) // 8 = 1

# Read bytes in little-endian order
value = data[0] = 0xAB

# Shift right by bit offset
bit_offset_in_byte = 4 % 8 = 4
value >>= 4  # 0xAB >> 4 = 0x0A = 1010

# Mask to get only 4 bits
mask = (1 << 4) - 1 = 0xF = 1111
value &= mask  # 1010 & 1111 = 1010

# Result: 0xA (10 in decimal)
```

**Why Little-Endian**: NR5G protocol uses little-endian byte order.

#### `_parse_field_value()` (Lines 135-172)

**Purpose**: Parse a field value based on its type.

**Logic**:
```python
# Read raw bits
raw_value = self._read_bits(data, offset_bytes, offset_bits, length_bits)

# Parse based on type
if type_name.startswith('Uint'):
    return raw_value, f"Uint{length_bits}"

elif type_name == 'Bool':
    return bool(raw_value), "Bool"

elif type_name == 'Enumeration':
    # Parse enum from description
    enum_str = self._parse_enum_from_description(description, raw_value)
    return enum_str, "Enumeration"

elif type_name.startswith('Table'):
    # Reference to another table - will be parsed recursively
    return raw_value, type_name
```

**Type Examples**:
- `Uint8` → unsigned 8-bit integer
- `Uint16` → unsigned 16-bit integer
- `Bool` → boolean (0 or 1)
- `Enumeration` → named value from description
- `Table 11-43` → nested structure

#### `_parse_enum_from_description()` (Lines 174-205)

**Purpose**: Extract enumeration value name from field description.

**Description Format**:
```
0: IDLE
• 1 – SINGLE STANDBY
• 2 – DUAL STANDBY
- 3 - ACTIVE
```

**Logic**:
```python
for line in description.split('\n'):
    line = line.strip()

    # Look for bullet or dash
    if line.startswith('•') or line.startswith('-'):
        # Split on '–' or '-'
        parts = line.split('–', 1)
        if len(parts) == 2:
            # Extract number: "• 1 " → "1"
            num_str = parts[0].replace('•', '').replace('-', '').strip()
            enum_value = int(num_str)  # 1

            if enum_value == value:
                return parts[1].strip()  # "SINGLE STANDBY"

return str(value)  # Fallback: return number as string
```

**Example**:
```python
description = "• 1 – SINGLE STANDBY\n• 2 – DUAL STANDBY"
value = 1
result = _parse_enum_from_description(description, 1)
# Returns: "SINGLE STANDBY"
```

---

### Table Parsing Functions

#### `_parse_table()` (Lines 207-259)

**Purpose**: Recursively parse a table structure from binary data.

**Logic**:
```python
# Get table definition from metadata
table = self.tables["11-55"]
fields = table['fields']

parsed_fields = {}

for field in fields:
    field_name = field['name']
    type_name = field['type_name']

    # Check if nested table reference
    if type_name.startswith('Table'):
        # Extract table number: "Table 11-43" → "11-43"
        ref_table_number = type_name.replace('Table', '').strip()

        # RECURSIVELY parse nested table
        nested_data = self._parse_table(data, ref_table_number, record_index)

        # Merge nested fields into parent
        for nested_field_name, nested_value in nested_data.items():
            parsed_fields[nested_field_name] = nested_value
    else:
        # Parse simple field
        value, value_type = self._parse_field_value(data, field)

        # Store with record index if needed
        field_key = f"{field_name} (Record {record_index})" if record_index > 0 else field_name

        parsed_fields[field_key] = {
            'value': value,
            'type': value_type,
            'offset_bytes': field['offset_bytes'],
            'length_bits': field['length_bits']
        }

return parsed_fields
```

**Example - Nested Table Parsing**:

Metadata:
```json
{
  "table_number": "11-55",
  "fields": [
    {"name": "Version", "type_name": "Table 11-43", "offset_bytes": 0, "length_bits": 32},
    {"name": "EARFCN", "type_name": "Uint32", "offset_bytes": 4, "length_bits": 32}
  ]
}

{
  "table_number": "11-43",
  "fields": [
    {"name": "Major", "type_name": "Uint16", "offset_bytes": 0, "length_bits": 16},
    {"name": "Minor", "type_name": "Uint16", "offset_bytes": 2, "length_bits": 16}
  ]
}
```

Binary Data: `02 00 03 00 7B 00 00 00`

Parsing:
```python
# Parse Table 11-55
parsed = _parse_table(data, "11-55")

# Field 1: Version (type = Table 11-43)
# → Recursively parse Table 11-43 from data[0:4]
nested = _parse_table(data[0:4], "11-43")
  # Major: read 16 bits at offset 0 → 2
  # Minor: read 16 bits at offset 2 → 3
  # Returns: {"Major": 2, "Minor": 3}

# Merge nested fields
parsed["Major"] = 2
parsed["Minor"] = 3

# Field 2: EARFCN (type = Uint32)
parsed["EARFCN"] = 123

# Final result
{
  "Major": {"value": 2, "type": "Uint16", ...},
  "Minor": {"value": 3, "type": "Uint16", ...},
  "EARFCN": {"value": 123, "type": "Uint32", ...}
}
```

#### `parse_payload()` (Lines 261-321)

**Purpose**: Main entry point to parse complete payload.

**Logic**:
```python
# 1. Convert hex to bytes
data = self._hex_string_to_bytes(payload_hex)

# 2. Parse version from first 4 bytes using Table 11-43
version_fields = self._parse_table(data[0:4], "11-43")
major = version_fields['Major']['value']  # 3
minor = version_fields['Minor']['value']  # 2
version_value = (major << 16) | minor     # 196610

# 3. Verify version matches metadata
target_version = self.metadata['target_version']['version']
if target_version != version_value:
    raise ValueError(f"Version mismatch: expected {target_version}, got {version_value}")

# 4. Get main table for this version
table_number = self.metadata['target_version']['table_number']  # "11-55"

# 5. Parse main table (skipping first 4 version bytes)
parsed_fields = self._parse_table(data[4:], table_number)

# 6. Build result
result = {
    'logcode_id': "0xB823",
    'logcode_name': "NR5G Serving Cell Info",
    'version': {
        'value': 196610,
        'hex': "0x00030002",
        'major': 3,
        'minor': 2
    },
    'fields': parsed_fields
}

return result
```

---

### Output Formatting

#### Function: `format_output()` (Lines 324-376)

**Purpose**: Format parsed data to match expected output structure.

**Logic**:
```python
# Input: Raw parsed data
{
  "version": {"value": 196610, "major": 3, "minor": 2},
  "fields": {
    "Major": {"value": 3},
    "Minor": {"value": 2},
    "EARFCN": {"value": 123},
    "PCI (Record 1)": {"value": 456}
  }
}

# Output: Formatted structure
{
  "Version": 196610,
  "LogRecordDescription": "NR5G Serving Cell Info",
  "MajorMinorVersion": [
    {"MajorMinorVersion": "3.2"}
  ],
  "Serving Cell Info": [
    {
      "Major": "3",
      "Minor": "2",
      "EARFCN": "123",
      "PCI": "456"
    }
  ]
}
```

**Transformations**:
1. Extract version info
2. Remove "(Record N)" suffixes from field names
3. Remove spaces from field names
4. Convert all values to strings
5. Group fields into records

---

### Main Execution Flow (Lines 379-445)

```python
def main():
    # 1. Define paths
    metadata_file = "data/output/metadata_0xB823_v196610.json"

    # 2. Define payload (hardcoded example)
    payload_hex = """
        02 00 03 00 01 01 00 7B 00 1A 80 2E
        DE 40 18 30 01 E0 E5 09 00 4A DE 09
        00 64 00 64 00 1A 80 2E DE 00 00 00
        00 37 01 03 E0 01 00 08 01 16 00 4D
        00
    """

    # 3. Load metadata
    with open(metadata_file, 'r') as f:
        metadata_json = json.load(f)

    # 4. Create parser
    parser = PayloadParser(str(metadata_file))

    # 5. Parse payload
    parsed_data = parser.parse_payload(payload_hex)

    # 6. Format output
    formatted_output = format_output(parsed_data, metadata_json['metadata'])

    # 7. Display
    print(json.dumps(formatted_output, indent=2))

    # 8. Save
    output_file = "data/output/parsed_0xB823.json"
    with open(output_file, 'w') as f:
        json.dump(formatted_output, f, indent=2)
```

**Usage**:
```bash
python parse_payload_0xB823.py
```

---

## Complete Workflow Example

### Step 1: Extract Metadata from PDF

```bash
cd icd_metadata_extractor
python extract_metadata_0xB823_196610.py data/input/ICD.pdf -o data/output/metadata.json
```

**What Happens**:
1. Opens ICD.pdf
2. Scans ToC for "0xB823"
3. Finds section 4.1 on pages 42-45
4. Extracts 8 tables from those pages
5. Identifies "Table 11-42: NR5G_Serving_Cell_Info_Versions" as version table
6. Parses version map: `{196610: "11-55"}`
7. Parses Table 11-43 (MajorMinorVersion) from pre-version tables
8. Parses Table 11-55 (main table for version 196610)
9. Finds dependencies: Table 11-56, Table 11-57
10. Parses dependency tables
11. Exports JSON with all metadata

**Output File**: `metadata_0xB823_v196610.json` (3500 lines, ~180 KB)

---

### Step 2: Parse Binary Payload

```bash
python parse_payload_0xB823.py
```

**Input Payload** (hex):
```
02 00 03 00 01 01 00 7B 00 1A 80 2E DE 40 18 30
01 E0 E5 09 00 4A DE 09 00 64 00 64 00 1A 80 2E
DE 00 00 00 00 37 01 03 E0 01 00 08 01 16 00 4D 00
```

**What Happens**:
1. Loads metadata_0xB823_v196610.json
2. Builds table index (11-43, 11-55, 11-56, 11-57)
3. Converts hex string to bytes (53 bytes)
4. Reads version from bytes [0:4]:
   - Bytes: `02 00 03 00`
   - Little-endian: Major = 3, Minor = 2
   - Version value: (3 << 16) | 2 = 196610 ✓
5. Parses main table (11-55) from bytes [4:53]:
   - Field: RecordType (Uint8) at offset 0 → value: 1
   - Field: CellIdentity (Uint32) at offset 4 → value: 123
   - Field: EARFCN (Uint32) at offset 8 → value: 3146302 (little-endian)
   - Field: PCI (Uint16) at offset 12 → value: 16664
   - ... (35 more fields)
6. Resolves nested tables recursively
7. Formats output structure
8. Saves to parsed_0xB823.json

**Output File**: `parsed_0xB823.json`

```json
{
  "Version": 196610,
  "LogRecordDescription": "NR5G Serving Cell Info",
  "MajorMinorVersion": [
    {"MajorMinorVersion": "3.2"}
  ],
  "Serving Cell Info": [
    {
      "RecordType": "1",
      "CellIdentity": "123",
      "EARFCN": "3146302",
      "PCI": "16664",
      "RSRP": "-80",
      "RSRQ": "-12",
      ...
    }
  ]
}
```

---

## Data Structures

### Metadata JSON Structure

```json
{
  "metadata": {
    "logcode_id": "0xB823",
    "logcode_name": "NR5G Serving Cell Info",
    "section_number": "4.1",
    "target_version": {
      "version": 196610,
      "version_hex": "0x00030002",
      "table_number": "11-55"
    },
    "version_map": {
      "196610": "11-55",
      "196611": "11-56"
    },
    "pre_version_tables": [
      {
        "table_number": "11-43",
        "table_name": "Table 11-43: MajorMinorVersion",
        "page_number": 42,
        "fields": [
          {
            "name": "Major",
            "type_name": "Uint16",
            "count": 1,
            "offset_bytes": 0,
            "offset_bits": 0,
            "length_bits": 16,
            "description": "Major version number"
          },
          {
            "name": "Minor",
            "type_name": "Uint16",
            "count": 1,
            "offset_bytes": 2,
            "offset_bits": 0,
            "length_bits": 16,
            "description": "Minor version number"
          }
        ]
      }
    ],
    "main_table": {
      "table_number": "11-55",
      "table_name": "Table 11-55: NR5G Serving Cell Info",
      "fields": [
        {
          "name": "Version",
          "type_name": "Table 11-43",
          "count": 1,
          "offset_bytes": 0,
          "offset_bits": 0,
          "length_bits": 32,
          "description": "Version information"
        },
        {
          "name": "RecordType",
          "type_name": "Uint8",
          "count": 1,
          "offset_bytes": 0,
          "offset_bits": 0,
          "length_bits": 8,
          "description": "Type of record"
        }
      ]
    },
    "dependent_tables": [...]
  },
  "export_info": {
    "generated_at": "2025-01-15T10:30:00",
    "generator": "ICD Metadata Extractor (Corrected)"
  }
}
```

### Field Definition Structure

```json
{
  "name": "EARFCN",
  "type_name": "Uint32",
  "count": 1,
  "offset_bytes": 8,
  "offset_bits": 0,
  "length_bits": 32,
  "description": "Absolute frequency of DL carrier"
}
```

**Field Properties**:
- `name`: Field name in output
- `type_name`: Data type (Uint8, Uint16, Uint32, Bool, Enumeration, Table X-Y)
- `count`: Number of elements (-1 for variable)
- `offset_bytes`: Byte offset in payload
- `offset_bits`: Bit offset within byte (0-7)
- `length_bits`: Field length in bits
- `description`: Human-readable description (may contain enum values)

---

## Error Handling

### File 1: extract_metadata_0xB823_196610.py

**PDF Not Found**:
```python
if not pdf_path.exists():
    print(f"[ERROR] PDF not found: {pdf_path}")
    return 1
```

**Logcode Not in ToC**:
```python
if target_logcode not in toc_map:
    print(f"[X] Logcode {target_logcode} not found in ToC")
    print(f"Found {len(toc_map)} logcodes")
    return None
```

**No Tables Found**:
```python
if not all_tables:
    print("[ERROR] No tables found")
    return 1
```

**Version Not in Map** (Fallback):
```python
if target_version not in version_map:
    print(f"[!] Version {target_version} not in version map, using fallback")
    # Use last table in section
    main_table_num = sorted(table_numbers)[-1]
```

**Table Not Found** (Fetch from PDF):
```python
if not dep_table:
    print(f"Fetching dependency from PDF: {dep_table_num}")
    dep_table = fetch_table_from_pdf(pdf_path, dep_table_num, ...)
```

### File 2: parse_payload_0xB823.py

**Metadata File Not Found**:
```python
if not metadata_file.exists():
    print(f"ERROR: Metadata file not found: {metadata_file}")
    return 1
```

**Payload Too Short**:
```python
if len(data) < 4:
    raise ValueError("Payload too short to contain version")
```

**Version Mismatch**:
```python
if target_version != version_value:
    raise ValueError(f"Version mismatch: expected {target_version}, got {version_value}")
```

**Not Enough Data**:
```python
if end_byte > len(data):
    raise ValueError(f"Not enough data: need {end_byte} bytes, have {len(data)}")
```

**Table Not Found**:
```python
if table_number not in self.tables:
    raise ValueError(f"Table {table_number} not found in metadata")
```

---

## Key Design Decisions

### 1. **Why Two Separate Scripts?**
- **Separation of Concerns**: Metadata extraction is slow (2-5 min), payload parsing is fast (<100ms)
- **Reusability**: Extract metadata once, parse thousands of payloads
- **Maintainability**: Each script has single responsibility

### 2. **Why Little-Endian?**
- NR5G protocol specification uses little-endian byte order
- x86/x64 processors use little-endian
- Network byte order (big-endian) not used here

### 3. **Why Bit-Level Parsing?**
- Protocol fields don't always align to byte boundaries
- Example: 4-bit field in middle of byte
- Enables precise field extraction as defined in ICD

### 4. **Why Recursive Table Parsing?**
- Tables reference other tables (nested structures)
- Avoids code duplication
- Natural representation of hierarchical data

### 5. **Why Version Table Detection?**
- Different logcode versions have different structures
- Must select correct table based on version in payload
- Future-proof: supports new versions without code changes

---

## Performance Characteristics

### File 1 (Metadata Extraction)
- **Time**: 30-120 seconds (depends on PDF size)
- **Memory**: ~50-100 MB peak (pdfplumber caches pages)
- **CPU**: Low (mostly I/O bound)
- **Run Frequency**: Once per logcode/version

### File 2 (Payload Parsing)
- **Time**: <10ms per payload
- **Memory**: ~5-10 MB (metadata loaded once)
- **CPU**: Low (simple bit operations)
- **Run Frequency**: Thousands of times per session

---

## Limitations and Assumptions

### extract_metadata_0xB823_196610.py
1. **Hardcoded for Single Logcode**: Only extracts 0xB823 v196610
2. **ToC Required**: PDF must have properly formatted Table of Contents
3. **Table Format Assumptions**: Expects standard 6-column format (Name, Type Name, Cnt, Off, Len, Description)
4. **Section 4.x Only**: Only processes "Log Items" section
5. **Caption Matching**: Assumes table captions appear in same order as extracted tables

### parse_payload_0xB823.py
1. **Version Must Match**: Rejects payloads with different versions
2. **Complete Metadata Required**: All referenced tables must be in metadata
3. **Fixed Byte Order**: Only supports little-endian
4. **No Dynamic Type Inference**: Types must be defined in metadata
5. **Hardcoded Payload**: Example payload is hardcoded in main()

---

## Extension Points

### To Support Multiple Logcodes
Modify extract_metadata script:
```python
# Replace hardcoded TARGET_LOGCODE
parser.add_argument('--logcode', required=True, help='Logcode to extract (e.g., 0xB823)')
parser.add_argument('--version', type=int, required=True, help='Version number')
```

### To Support Multiple Versions
Both scripts already support this through version_map:
```json
"version_map": {
  "196610": "11-55",
  "196611": "11-56",
  "196612": "11-57"
}
```

Parser automatically selects correct table based on payload version.

### To Parse from Command Line
Modify parse_payload script:
```python
parser.add_argument('payload', help='Hex payload string or file path')
parser.add_argument('--metadata', default='metadata.json', help='Metadata file')
```

### To Handle Variable-Length Arrays
Current limitation: Count = -1 not fully supported.

Enhancement:
```python
if field['count'] == -1:
    # Read count from previous field or header
    actual_count = determine_runtime_count(data, field)
    for i in range(actual_count):
        parse_array_element(data, field, i)
```

---

## Troubleshooting

### Metadata Extraction Issues

**Problem**: "Logcode not found in ToC"
- **Solution**: Check if PDF has ToC in first 50 pages
- **Verify**: Open PDF and search for pattern "4.X Name (0xB823) ... PageNum"

**Problem**: "No tables found"
- **Solution**: Check if pages contain tables
- **Debug**: Add print statements in extract_tables_from_section()

**Problem**: "Version table not found"
- **Solution**: Check table captions for "_Versions" or "Cond" column
- **Fallback**: Script uses last table in section

### Payload Parsing Issues

**Problem**: "Version mismatch"
- **Solution**: Extract metadata for correct version
- **Check**: Version in payload hex (first 4 bytes)

**Problem**: "Not enough data"
- **Solution**: Verify payload is complete
- **Check**: Calculate expected size from metadata field offsets

**Problem**: "Table X-Y not found"
- **Solution**: Re-extract metadata with all dependencies
- **Debug**: Check metadata JSON for missing tables

---

## Summary

### extract_metadata_0xB823_196610.py
**Purpose**: PDF → JSON metadata extraction

**Input**: ICD PDF document

**Output**: JSON with table definitions and field specifications

**Key Functions**:
- ToC parsing for fast logcode location
- pdfplumber for table extraction
- Version table detection and parsing
- Dependency resolution
- Optimized parsing (only required tables)

### parse_payload_0xB823.py
**Purpose**: Binary payload parsing using metadata

**Input**: Metadata JSON + Hex payload

**Output**: Structured JSON with parsed field values

**Key Functions**:
- Bit-level field extraction
- Little-endian byte order handling
- Recursive table parsing
- Enumeration value resolution
- Formatted JSON output

### Workflow Integration
```
PDF → [Extract Metadata] → JSON → [Parse Payload] → Parsed Output
```

Both scripts are designed to work together as a complete logcode parsing pipeline, with clear separation of concerns and minimal dependencies.
