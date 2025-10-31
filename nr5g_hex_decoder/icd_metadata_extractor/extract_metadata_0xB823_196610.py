#!/usr/bin/env python3
"""
ICD Metadata Extractor - Single Script Version (Corrected)
Extracts metadata for logcode 0xB823 version 196610 from ICD PDF

Uses proper ToC-based scanning and version table detection like nr5g_hex_decoder

Usage:
    python extract_metadata.py [pdf_path] [-o output.json]
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import pdfplumber


# ============================================================================
# CONFIGURATION - Hardcoded for logcode 0xB823 version 196610
# ============================================================================

TARGET_LOGCODE = "0xB823"
TARGET_VERSION = 196610  # 0x00030002 = version 3.2

# Default paths
DEFAULT_PDF = "data/input/ICD.pdf"
DEFAULT_OUTPUT = "data/output/metadata_0xB823_v196610.json"


# ============================================================================
# STEP 1: FIND LOGCODE IN TABLE OF CONTENTS
# ============================================================================

def find_logcode_in_toc(pdf_path: str, target_logcode: str) -> Optional[Dict]:
    """
    Find logcode using Table of Contents (like nr5g_hex_decoder does)

    Returns:
        Dictionary with: logcode_id, section_number, section_title, start_page, end_page
    """
    print(f"\n[1/5] Scanning Table of Contents for {target_logcode}...")

    target_logcode = target_logcode.upper()

    with pdfplumber.open(pdf_path) as pdf:
        # Parse ToC to build mapping
        toc_map = parse_toc(pdf)

        if target_logcode not in toc_map:
            print(f"  [X] Logcode {target_logcode} not found in ToC")
            print(f"      Found {len(toc_map)} logcodes")
            return None

        page_num, section_num, title = toc_map[target_logcode]

        # Find end page (next logcode's start page - 1)
        all_logcodes = sorted(toc_map.items(), key=lambda x: x[1][0])

        end_page = len(pdf.pages) - 1
        for idx, (lc, _) in enumerate(all_logcodes):
            if lc == target_logcode:
                if idx + 1 < len(all_logcodes):
                    end_page = all_logcodes[idx + 1][1][0] - 1
                break

        print(f"  [OK] Found {target_logcode} in ToC")
        print(f"       Section: {section_num} - {title}")
        print(f"       Pages: {page_num + 1} to {end_page + 1}")

        return {
            'logcode_id': target_logcode,
            'section_number': section_num,
            'section_title': title,
            'start_page': page_num,
            'end_page': end_page
        }


def parse_toc(pdf) -> Dict[str, Tuple[int, str, str]]:
    """
    Parse Table of Contents to find all logcodes

    Returns:
        Dict mapping logcode_id → (page_num, section_num, title)
    """
    # Pattern: "4.1 Name (0xB823) ......... 45"
    toc_pattern = re.compile(
        r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)[\s.]*(\d+)',
        re.MULTILINE
    )

    toc_map = {}

    # Scan first 50 pages for ToC
    for page_idx in range(min(50, len(pdf.pages))):
        page = pdf.pages[page_idx]
        text = page.extract_text()

        if not text:
            continue

        # Look for ToC entries
        for match in toc_pattern.finditer(text):
            section_num = match.group(1)
            title = match.group(2).strip()
            logcode = match.group(3).upper()
            page_num = int(match.group(4))

            # PDF page numbers are 1-indexed, convert to 0-indexed
            toc_map[logcode] = (page_num - 1, section_num, title)

    return toc_map


# ============================================================================
# STEP 2: EXTRACT ALL TABLES FROM SECTION
# ============================================================================

def extract_tables_from_section(pdf_path: str, section: Dict) -> List[Dict]:
    """
    Extract all tables from the logcode section

    Returns:
        List of dictionaries with: caption, headers, rows, page_number, table_number
    """
    print(f"\n[2/5] Extracting tables from pages {section['start_page'] + 1} to {section['end_page'] + 1}...")

    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(section['start_page'], section['end_page'] + 1):
            if page_num >= len(pdf.pages):
                break

            page = pdf.pages[page_num]
            tables = page.extract_tables()

            if tables:
                page_text = page.extract_text()

                # Find ALL table captions on this page
                all_captions = find_all_table_captions(page_text, page_num)

                for idx, table_data in enumerate(tables):
                    if not table_data or len(table_data) < 1:
                        continue

                    # Extract headers and rows
                    headers = [str(cell).strip() if cell else "" for cell in table_data[0]]
                    rows = []
                    for row in table_data[1:]:
                        cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                        if any(cleaned_row):
                            rows.append(cleaned_row)

                    if rows:
                        # Match caption by index (assumes captions appear in same order as tables)
                        caption = all_captions[idx] if idx < len(all_captions) else f"Table on page {page_num + 1}"
                        table_number = extract_table_number(caption)

                        all_tables.append({
                            'caption': caption,
                            'headers': headers,
                            'rows': rows,
                            'page_number': page_num,
                            'table_number': table_number
                        })

    print(f"  [OK] Extracted {len(all_tables)} tables")
    return all_tables


def find_all_table_captions(page_text: str, page_num: int) -> List[str]:
    """Find ALL table captions from page text in order"""
    table_pattern = r"Table\s+(\d+-\d+)[:\s]*(.+?)(?:\n|$)"
    matches = re.findall(table_pattern, page_text, re.IGNORECASE)

    # Group matches by table number to handle duplicates
    table_captions = {}

    for table_num, table_name in matches:
        table_name_clean = table_name.strip()

        # Skip empty captions
        if not table_name_clean:
            continue

        # Skip captions that are just numbers (like "Table 11-55: 0 360")
        if re.match(r'^\d+\s+\d+$', table_name_clean):
            continue

        # Skip captions that start with numbers followed by more data (likely table rows)
        # Pattern: starts with 1-3 digits separated by spaces (like "1 0 32 ...")
        if re.match(r'^\d+\s+\d+\s+\d+', table_name_clean):
            continue

        # For each table number, prefer captions that:
        # 1. Start with a letter (not a number)
        # 2. Don't contain "Shown only when" (that's a condition, not a name)
        # 3. Are shorter and cleaner (real captions are usually concise)

        if table_num not in table_captions:
            table_captions[table_num] = table_name_clean
        else:
            # Compare quality of captions - prefer the one that looks more like a title
            current = table_captions[table_num]

            # Score the captions (higher is better)
            def caption_quality(name):
                score = 0
                # Starts with letter (likely a name)
                if re.match(r'^[A-Za-z]', name):
                    score += 10
                # Doesn't contain "shown only when" or similar conditional text
                if not re.search(r'(shown|only|when|<=|>=)', name, re.IGNORECASE):
                    score += 5
                # Shorter is usually better for table names
                if len(name) < 50:
                    score += 3
                # No digits at start
                if not re.match(r'^\d', name):
                    score += 2
                return score

            if caption_quality(table_name_clean) > caption_quality(current):
                table_captions[table_num] = table_name_clean

    # Return in order of appearance
    captions = [f"Table {num}: {name}" for num, name in sorted(table_captions.items())]
    return captions if captions else [f"Table on page {page_num + 1}"]


def extract_table_number(caption: str) -> str:
    """Extract table number from caption"""
    match = re.search(r"Table\s+(\d+-\d+)", caption, re.IGNORECASE)
    return match.group(1) if match else ""


# ============================================================================
# STEP 3: IDENTIFY AND PARSE VERSION TABLE
# ============================================================================

def find_version_table(tables: List[Dict]) -> Optional[Dict]:
    """
    Find the version table (prioritizes "Cond" column format over caption-based detection)

    Returns:
        Version table dictionary or None
    """
    print(f"\n[3/5] Looking for version table...")

    # Priority 1: Check for "Cond" column format (most reliable)
    for table in tables:
        headers = table['headers']
        if any('cond' in str(h).lower() for h in headers):
            # Also check if Name column has "Version" entries
            for row in table['rows']:
                if row and len(row) > 0 and row[0]:
                    if 'version' in str(row[0]).lower():
                        print(f"  [OK] Found version table with Cond column: {table['caption']}")
                        return table

    # Priority 2: Check caption for "_Versions" keyword (more specific than just "version")
    for table in tables:
        if '_version' in table['caption'].lower():
            print(f"  [OK] Found version table by caption: {table['caption']}")
            return table

    print(f"  [!] No version table found (will use fallback)")
    return None


def parse_version_table(version_table: Dict) -> Dict[int, str]:
    """
    Parse version table to get version → table_number mapping

    Supports two formats:
    1. Traditional: Version | Details (Defined in 4-4)
    2. Cond format: Name=Version X | Type Name=Table 4-4 | Cond=version_number

    Returns:
        Dict mapping version number to table number
    """
    version_map = {}

    if not version_table:
        return version_map

    headers = version_table['headers']
    rows = version_table['rows']

    # Check if this has "Cond" column
    cond_idx = None
    for idx, header in enumerate(headers):
        if header and 'cond' in str(header).lower():
            cond_idx = idx
            break

    if cond_idx is not None:
        # Format 2: Cond column table
        print(f"       Parsing Cond-format version table...")
        for row in rows:
            if len(row) <= cond_idx or len(row) < 2:
                continue

            # Get Cond value (version in decimal)
            cond_str = str(row[cond_idx]).strip()
            if not cond_str:
                continue

            # Get table reference from Type Name column
            type_name = str(row[1]).strip() if len(row) > 1 else ''
            if not type_name:
                continue

            # Extract table number
            table_match = re.search(r'(\d+-\d+)', type_name)
            if not table_match:
                continue

            table_name = table_match.group(1)

            # Parse version number
            try:
                version_num = int(cond_str)
                version_map[version_num] = table_name
                print(f"       Version {version_num} -> Table {table_name}")
            except ValueError:
                continue
    else:
        # Format 1: Traditional _Versions table
        print(f"       Parsing traditional version table...")
        for row in rows:
            if len(row) < 2:
                continue

            version_str = str(row[0]).strip()
            details = str(row[1]).strip() if len(row) > 1 else ''

            if not version_str or not details:
                continue

            # Extract table number
            table_match = re.search(r'(\d+-\d+)', details)
            if not table_match:
                continue

            table_name = table_match.group(1)

            # Parse version
            try:
                if version_str.startswith('0x') or version_str.startswith('0X'):
                    version_num = int(version_str, 16)
                else:
                    version_num = int(version_str)

                version_map[version_num] = table_name
                print(f"       Version {version_num} -> Table {table_name}")
            except ValueError:
                continue

    return version_map


def parse_tables_before_version(all_tables: List[Dict], version_table: Optional[Dict]) -> List[Dict]:
    """
    Parse all tables that appear before the version table.
    These are typically structure definition tables (like 11-42, 11-43, etc.)

    Args:
        all_tables: All extracted tables from the section
        version_table: The version table (to determine cutoff point)

    Returns:
        List of parsed table dictionaries with table_number, table_name, and fields
    """
    if not version_table:
        print(f"\n[3.5/5] No version table found, skipping pre-version tables...")
        return []

    print(f"\n[3.5/5] Parsing tables before version table...")

    pre_version_tables = []
    version_table_index = None

    # Find the index of the version table in all_tables
    for idx, table in enumerate(all_tables):
        if table == version_table:
            version_table_index = idx
            break

    if version_table_index is None:
        print(f"  [!] Could not locate version table in extracted tables")
        return []

    # Parse all tables before the version table
    for idx in range(version_table_index):
        table = all_tables[idx]
        table_number = table.get('table_number')

        if not table_number:
            continue

        # Parse the table
        fields = parse_table_to_fields(table)
        if fields:
            parsed_table = {
                'table_number': table_number,
                'table_name': table['caption'],
                'page_number': table['page_number'] + 1,  # Convert to 1-indexed for display
                'fields': fields
            }
            pre_version_tables.append(parsed_table)
            print(f"       Parsed Table {table_number} (page {table['page_number'] + 1}) - {len(fields)} fields")

    print(f"  [OK] Found {len(pre_version_tables)} tables before version table")
    return pre_version_tables


# ============================================================================
# STEP 4: PARSE ONLY REQUIRED TABLES FOR TARGET VERSION
# ============================================================================

def parse_specific_table(tables: List[Dict], version_table: Optional[Dict], table_number: str) -> Optional[Dict]:
    """
    Parse a specific table by table number from extracted tables.
    If multiple tables with same number exist, keeps the largest one.

    Returns:
        Table definition dict or None if not found
    """
    matching_tables = []
    for table in tables:
        if version_table and table == version_table:
            continue
        if table.get('table_number') == table_number:
            matching_tables.append(table)

    if not matching_tables:
        return None

    # If multiple tables with same number, use the one with most rows
    best_table = max(matching_tables, key=lambda t: len(t.get('rows', [])))

    fields = parse_table_to_fields(best_table)
    if not fields:
        return None

    return {
        'table_number': table_number,
        'table_name': best_table['caption'],
        'fields': fields
    }


def parse_tables_for_version(
    all_tables: List[Dict],
    version_table: Optional[Dict],
    version_map: Dict[int, str],
    target_version: int,
    pdf_path: str,
    section: Dict
) -> Tuple[Dict, List[Dict]]:
    """
    Parse only the tables needed for target version (main table + dependencies).
    This is more efficient than parsing all tables in the section.

    Returns:
        Tuple of (main_table, dependent_tables)
    """
    print(f"\n[4/5] Parsing tables for version {target_version}...")

    # Look up main table number for target version
    main_table_num = version_map.get(target_version)

    if not main_table_num:
        print(f"  [!] Version {target_version} not in version map, using fallback")
        # Fallback: find last table in extracted tables
        table_numbers = [t['table_number'] for t in all_tables if t.get('table_number') and t != version_table]
        if table_numbers:
            main_table_num = sorted(table_numbers)[-1]
            print(f"      Using last table: {main_table_num}")
        else:
            raise Exception("No tables found")

    # Parse main table
    print(f"  [OK] Version {target_version} -> Table {main_table_num}")
    main_table = parse_specific_table(all_tables, version_table, main_table_num)

    if not main_table:
        raise Exception(f"Main table {main_table_num} not found in extracted tables")

    print(f"       Main table: {len(main_table['fields'])} fields")

    # Find dependencies from main table fields
    main_deps = find_dependencies(main_table['fields'])
    print(f"       Dependencies: {list(main_deps) if main_deps else 'none'}")

    # Parse dependent tables
    dependent_tables = []
    for dep_table_num in main_deps:
        # Try to find in extracted tables first
        dep_table = parse_specific_table(all_tables, version_table, dep_table_num)

        if dep_table:
            print(f"       Parsed dependency: {dep_table_num} ({len(dep_table['fields'])} fields)")
            dependent_tables.append(dep_table)
        else:
            # Fetch from PDF if not in extracted tables
            print(f"       Fetching dependency from PDF: {dep_table_num}")
            dep_table = fetch_table_from_pdf(
                pdf_path,
                dep_table_num,
                section_start=section['start_page'],
                section_end=section['end_page']
            )
            if dep_table:
                print(f"       Found dependency: {dep_table_num} ({len(dep_table['fields'])} fields)")
                dependent_tables.append(dep_table)

    return main_table, dependent_tables


def parse_table_to_fields(table: Dict) -> List[Dict]:
    """Parse table rows into field definitions"""
    fields = []

    for row in table['rows']:
        field = parse_row_to_field(row, table['headers'])
        if field:
            fields.append(field)

    return fields


def parse_row_to_field(row: List[str], headers: List[str]) -> Optional[Dict]:
    """Parse a single table row into field definition"""
    row_dict = {}
    for i, header in enumerate(headers):
        row_dict[header] = row[i] if i < len(row) else ""

    name = row_dict.get("Name", "")
    type_name = row_dict.get("Type Name", "")

    if not name and not type_name:
        return None

    count = parse_count(row_dict.get("Cnt", "1"))
    offset_bits = parse_number(row_dict.get("Off", "0"))
    length_bits = parse_number(row_dict.get("Len", "0"))
    description = row_dict.get("Description", "")

    offset_bytes = offset_bits // 8
    offset_bits_remainder = offset_bits % 8

    return {
        "name": name,
        "type_name": type_name,
        "count": count,
        "offset_bytes": offset_bytes,
        "offset_bits": offset_bits_remainder,
        "length_bits": length_bits,
        "description": description
    }


def parse_count(cnt_str: str) -> int:
    """Parse count field, returns -1 for variable/unknown counts"""
    if not cnt_str or cnt_str in ["-", "N/A", "Variable", "Var", "*"]:
        return -1

    try:
        return int(cnt_str)
    except ValueError:
        return -1


def parse_number(num_str: str) -> int:
    """Parse numeric field, returns 0 if not parseable"""
    if not num_str:
        return 0

    try:
        return int(num_str)
    except ValueError:
        return 0


def find_dependencies(fields: List[Dict]) -> set:
    """Find table dependencies from field Type Names"""
    dependencies = set()
    table_pattern = re.compile(r"Table\s+(\d+-\d+)", re.IGNORECASE)

    for field in fields:
        match = table_pattern.search(field['type_name'])
        if match:
            dependencies.add(match.group(1))

        if field['description']:
            match = table_pattern.search(field['description'])
            if match:
                dependencies.add(match.group(1))

    return dependencies


def fetch_table_from_pdf(pdf_path: str, table_number: str, section_start: int = 0, section_end: int = None) -> Optional[Dict]:
    """
    Fetch a specific table from the PDF (searches near section first, then expands)

    Args:
        pdf_path: Path to PDF
        table_number: Table number to find (e.g., "11-43")
        section_start: Start page of current section (search near here first)
        section_end: End page of current section
    """
    pattern = re.compile(rf"Table\s+{re.escape(table_number)}[:\s]", re.IGNORECASE)

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        # If section_end not provided, search entire document
        if section_end is None:
            section_end = total_pages - 1

        # Strategy 1: Search within the section first (most likely location)
        print(f"         Searching for Table {table_number} in section pages {section_start + 1} to {section_end + 1}...")
        for page_num in range(section_start, min(section_end + 1, total_pages)):
            result = _extract_table_from_page(pdf.pages[page_num], page_num, table_number, pattern)
            if result:
                return result

        # Strategy 2: Expand search to nearby pages (±50 pages from section)
        print(f"         Expanding search to nearby pages...")
        search_start = max(0, section_start - 50)
        search_end = min(total_pages, section_end + 50)

        for page_num in range(search_start, search_end):
            if section_start <= page_num <= section_end:
                continue  # Already searched
            result = _extract_table_from_page(pdf.pages[page_num], page_num, table_number, pattern)
            if result:
                return result

        # Strategy 3: Last resort - search entire document
        print(f"         Searching entire document ({total_pages} pages)...")
        for page_num in range(total_pages):
            if search_start <= page_num <= search_end:
                continue  # Already searched
            result = _extract_table_from_page(pdf.pages[page_num], page_num, table_number, pattern)
            if result:
                return result

    print(f"         [!] Table {table_number} not found in document")
    return None


def _extract_table_from_page(page, page_num: int, table_number: str, pattern) -> Optional[Dict]:
    """Helper to extract table from a specific page"""
    text = page.extract_text()
    if not text or not pattern.search(text):
        return None

    print(f"         Found Table {table_number} at page {page_num + 1}")
    tables = page.extract_tables()
    if not tables:
        return None

    table_data = tables[0]
    headers = [str(cell).strip() if cell else "" for cell in table_data[0]]
    rows = [[str(cell).strip() if cell else "" for cell in row] for row in table_data[1:]]
    rows = [r for r in rows if any(r)]

    if not rows:
        return None

    # Get table caption
    caption_match = re.search(rf"Table\s+{re.escape(table_number)}[:\s]*(.+?)(?:\n|$)", text, re.IGNORECASE)
    caption = f"Table {table_number}: {caption_match.group(1).strip()}" if caption_match else f"Table {table_number}"

    fields = parse_table_to_fields({'headers': headers, 'rows': rows})
    return {
        'table_number': table_number,
        'table_name': caption,
        'fields': fields
    }


# ============================================================================
# STEP 5: EXPORT TO JSON
# ============================================================================

def export_to_json(
    section: Dict,
    main_table: Dict,
    dependent_tables: List[Dict],
    pre_version_tables: List[Dict],
    version_map: Dict,
    output_path: str
):
    """Export metadata to JSON file"""
    print(f"\n[5/5] Exporting to JSON...")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "logcode_id": section['logcode_id'],
        "logcode_name": section['section_title'],
        "section_number": section['section_number'],
        "target_version": {
            "version": TARGET_VERSION,
            "version_hex": f"0x{TARGET_VERSION:08X}",
            "table_number": main_table['table_number']
        },
        "version_map": {str(TARGET_VERSION): version_map[TARGET_VERSION]} if TARGET_VERSION in version_map else {},
        "pre_version_tables": pre_version_tables,
        "main_table": main_table,
        "dependent_tables": dependent_tables
    }

    output_data = {
        "metadata": metadata,
        "export_info": {
            "generated_at": datetime.now().isoformat(),
            "generator": "ICD Metadata Extractor (Corrected)",
            "hardcoded_for": f"{TARGET_LOGCODE} version {TARGET_VERSION}"
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    file_size = output_file.stat().st_size

    print(f"  [OK] JSON exported successfully!")
    print(f"       File: {output_file.absolute()}")
    print(f"       Size: {file_size:,} bytes")
    print(f"       Pre-version tables: {len(pre_version_tables)}")
    print(f"       Main table: {main_table['table_number']} with {len(main_table['fields'])} fields")
    print(f"       Dependent tables: {len(dependent_tables)}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description=f"Extract metadata for {TARGET_LOGCODE} version {TARGET_VERSION}"
    )

    parser.add_argument('pdf_path', nargs='?', default=DEFAULT_PDF,
                       help=f'Path to ICD PDF (default: {DEFAULT_PDF})')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT,
                       help=f'Output JSON (default: {DEFAULT_OUTPUT})')

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        print(f"\n[ERROR] PDF not found: {pdf_path}")
        return 1

    print("="*70)
    print(f"ICD Metadata Extractor (Corrected)")
    print("="*70)
    print(f"Target: {TARGET_LOGCODE} version {TARGET_VERSION}")
    print(f"Input:  {pdf_path.absolute()}")
    print(f"Output: {args.output}")
    print("="*70)

    try:
        # Step 1: Find logcode in ToC
        section = find_logcode_in_toc(str(pdf_path), TARGET_LOGCODE)
        if not section:
            return 1

        # Step 2: Extract all tables
        all_tables = extract_tables_from_section(str(pdf_path), section)
        if not all_tables:
            print("[ERROR] No tables found")
            return 1

        # Step 3: Find and parse version table
        version_table = find_version_table(all_tables)
        version_map = parse_version_table(version_table) if version_table else {}

        # Step 3.5: Parse tables that appear before version table
        pre_version_tables = parse_tables_before_version(all_tables, version_table)

        # Step 4-5: Parse only tables needed for target version (combined and optimized)
        main_table, dependent_tables = parse_tables_for_version(
            all_tables, version_table, version_map, TARGET_VERSION, str(pdf_path), section
        )

        # Step 5: Export JSON
        export_to_json(section, main_table, dependent_tables, pre_version_tables, version_map, args.output)

        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"Metadata extracted for {TARGET_LOGCODE} version {TARGET_VERSION}")
        print(f"Output: {Path(args.output).absolute()}")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
