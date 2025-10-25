"""
Parsing & Structuring Layer
Converts extracted tables into structured logcode data with version mappings.
"""

import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from pdf_extractor import ExtractedTable, PDFExtractor


@dataclass
class LogcodeVersion:
    """Represents a single version of a logcode"""
    version: str  # e.g., "2"
    main_table: str  # e.g., "4-4"
    dep_tables: List[str] = field(default_factory=list)  # e.g., ["4-5"]


@dataclass
class LogcodeData:
    """Complete data for a single logcode"""
    logcode: str  # e.g., "0x1C07"
    name: str  # e.g., "NR5G Sub6 TxAGC"
    section: str  # e.g., "4.1"
    versions: List[str]  # e.g., ["1", "2", "3"]
    version_to_table: Dict[str, str]  # version -> table_number mapping
    tables: Dict[str, ExtractedTable]  # table_number -> table data
    dependencies: Dict[str, List[str]]  # table_number -> [dep_table_numbers]


class LogcodeParser:
    """Parses extracted tables into structured logcode information"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.extractor = PDFExtractor(pdf_path)
        self.logcodes: Dict[str, LogcodeData] = {}
    
    def detect_logcode_section(self, page_text: str) -> Optional[Dict[str, str]]:
        """
        Detect logcode section headers like:
        "4.1 NR5G Sub6 TxAGC (0x1C07)"
        or with newline:
        "4.1
        NR5G Sub6 TxAGC (0x1C07)"

        IMPORTANT: Only detects logcodes from Section 4 ("Log Items" section).
        Other sections like MAC, ML1, RRC, etc. are NOT considered valid logcodes.

        Returns:
            Dict with 'section', 'name', 'logcode' (only if section starts with "4.")
        """
        # Pattern 1: Section, name, and code all on one line
        pattern1 = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'
        # Pattern 2: Section on one line, name and code on next line
        pattern2 = r'^\s*(\d+\.\d+)\s*$'

        lines = page_text.split('\n')
        for i, line in enumerate(lines):
            # Try pattern 1 first (all on one line)
            match = re.match(pattern1, line, re.IGNORECASE)
            if match:
                section = match.group(1)
                # Only accept logcodes from Section 4 (Log Items)
                if section.startswith('4.'):
                    return {
                        'section': section,
                        'name': match.group(2).strip(),
                        'logcode': match.group(3).upper()
                    }

            # Try pattern 2 (section on one line, rest on next)
            match = re.match(pattern2, line)
            if match and i + 1 < len(lines):
                section = match.group(1)
                if section.startswith('4.'):
                    # Check next line for name and code
                    next_line = lines[i + 1]
                    name_code_match = re.search(r'^(.+?)\s+\((0x[0-9A-F]+)\)', next_line, re.IGNORECASE)
                    if name_code_match:
                        return {
                            'section': section,
                            'name': name_code_match.group(1).strip(),
                            'logcode': name_code_match.group(2).upper()
                        }
        return None
    
    def parse_versions_from_table_rows(self, table: ExtractedTable, tables_dict: Dict[str, ExtractedTable]) -> Dict[str, str]:
        """
        Parse version mappings from table rows.

        Version information can be:
        1. Directly in the table: "Version 2 | Table 4-4"
        2. Referenced in another table: "Versions | Table 4-2" (then read Table 4-2 for mappings)

        Returns:
            Dict mapping version number to table number (e.g., {"2": "4-4", "3": "4-6"})
        """
        version_map = {}

        for row in table.rows:
            if len(row) < 2:
                continue

            name_col = row[0].strip()
            type_col = row[1].strip()

            # Pattern 1: "Version X" → "Table Y-Z"
            version_match = re.search(r'^Version\s+(\d+)$', name_col, re.IGNORECASE)
            if version_match:
                version_num = version_match.group(1)
                table_match = re.search(r'Table\s+(\d+-\d+)', type_col, re.IGNORECASE)
                if table_match:
                    table_num = table_match.group(1)
                    version_map[version_num] = table_num

            # Pattern 2: "Versions" → "Table X-Y" (reference to versions table)
            if name_col.lower() == 'versions':
                table_match = re.search(r'Table\s+(\d+-\d+)', type_col, re.IGNORECASE)
                if table_match:
                    versions_table_num = table_match.group(1)
                    # Recursively read the referenced versions table
                    if versions_table_num in tables_dict:
                        versions_table = tables_dict[versions_table_num]
                        # Parse version mappings from the referenced table
                        for vrow in versions_table.rows:
                            if len(vrow) < 2:
                                continue
                            vname = vrow[0].strip()
                            vtype = vrow[1].strip()
                            vmatch = re.search(r'^Version\s+(\d+)$', vname, re.IGNORECASE)
                            if vmatch:
                                vnum = vmatch.group(1)
                                vtable_match = re.search(r'Table\s+(\d+-\d+)', vtype, re.IGNORECASE)
                                if vtable_match:
                                    version_map[vnum] = vtable_match.group(1)

        return version_map
    
    def detect_table_dependencies(self, table: ExtractedTable) -> List[str]:
        """
        Detect references to other tables in the "Type Name" column.
        
        For example, if a row has:
        Name: "Systime"
        Type Name: "Table 4-5"
        
        This means the current table depends on Table 4-5.
        
        Returns:
            List of table numbers this table depends on
        """
        dependencies = set()
        
        # Find Type Name column index
        type_name_idx = None
        for i, header in enumerate(table.headers):
            if header.lower().strip() == "type name":
                type_name_idx = i
                break
        
        if type_name_idx is None:
            return []
        
        # Scan rows for table references
        for row in table.rows:
            if len(row) > type_name_idx:
                type_val = row[type_name_idx].strip()
                match = re.search(r'Table\s+(\d+-\d+)', type_val, re.IGNORECASE)
                if match:
                    dependencies.add(match.group(1))
        
        return sorted(list(dependencies))
    
    def group_tables_by_section(self, all_tables: List[ExtractedTable]) -> Dict[str, List[ExtractedTable]]:
        """
        Group tables by their parent logcode section.
        Uses section numbers (e.g., "4.1") to group related tables.
        """
        section_tables = {}
        
        for table in all_tables:
            # Extract section from table number (e.g., "4-4" -> "4")
            match = re.match(r'(\d+)-\d+', table.metadata.table_number)
            if match:
                section_major = match.group(1)
                
                if section_major not in section_tables:
                    section_tables[section_major] = []
                section_tables[section_major].append(table)
        
        return section_tables
    
    def parse_all_logcodes(self) -> Dict[str, LogcodeData]:
        """
        Parse the entire PDF and extract all logcode data.

        Scans page-by-page to track which logcode is active and assigns tables accordingly.

        Returns:
            Dict mapping logcode (e.g., "0x1C07") to LogcodeData
        """
        # Extract all tables
        all_tables = self.extractor.extract_all_tables()

        # Build table lookup by page range
        table_by_page = {}
        for table in all_tables:
            for page_num in range(table.metadata.page_start, table.metadata.page_end + 1):
                if page_num not in table_by_page:
                    table_by_page[page_num] = []
                table_by_page[page_num].append(table)

        # First pass: detect all logcode sections and their starting table numbers
        logcode_sections = []
        for page_num in range(len(self.extractor.doc)):
            page = self.extractor.doc[page_num]
            text = page.get_text()
            section_info = self.detect_logcode_section(text)
            if section_info:
                logcode_sections.append({
                    'logcode': section_info['logcode'],
                    'name': section_info['name'],
                    'section': section_info['section'],
                    'page': page_num
                })

        # Find the first table for each logcode section by looking for tables on/after the section page
        for i, section in enumerate(logcode_sections):
            section['first_table'] = None
            # Look for first table with matching name pattern
            for table in all_tables:
                # Check if table is on or after this section's page
                if table.metadata.page_start >= section['page']:
                    # Check if table title contains the section name keywords
                    # For example: "Nr5g_Sub6TxAgc" for section 4.1, "Nr5g_MmwTxAgc" for section 4.2
                    section_keywords = section['name'].replace(' ', '').replace('5G', '5g')
                    table_keywords = table.metadata.title.replace('_', '')
                    if section_keywords[:15].lower() in table_keywords.lower():
                        section['first_table'] = table.metadata.table_number
                        break

        # Assign tables to logcodes based on table number ranges
        logcodes = {}
        for i, section in enumerate(logcode_sections):
            logcode = section['logcode']
            logcodes[logcode] = {
                'name': section['name'],
                'section': section['section'],
                'tables': []
            }

            # Determine table number range for this section
            if section['first_table']:
                start_major, start_minor = map(int, section['first_table'].split('-'))
                # Find the end range (before next section's first table)
                if i + 1 < len(logcode_sections) and logcode_sections[i + 1]['first_table']:
                    end_major, end_minor = map(int, logcode_sections[i + 1]['first_table'].split('-'))
                    end_minor -= 1  # Exclude the next section's first table
                else:
                    end_major, end_minor = 999, 999  # Last section gets all remaining tables

                # Assign tables in this range
                for table in all_tables:
                    table_major, table_minor = map(int, table.metadata.table_number.split('-'))
                    if (table_major == start_major and start_minor <= table_minor <= end_minor):
                        logcodes[logcode]['tables'].append(table)

        # Now process each logcode's tables to extract version mappings and dependencies
        result = {}
        for logcode, data in logcodes.items():
            tables_list = data['tables']

            # Sort tables by table number
            sorted_tables = sorted(tables_list, key=lambda t: (
                int(t.metadata.table_number.split('-')[0]),
                int(t.metadata.table_number.split('-')[1])
            ))

            # Build tables dict first (needed for version parsing)
            tables_dict = {}
            dependencies = {}

            for tbl in sorted_tables:
                tbl_num = tbl.metadata.table_number
                tables_dict[tbl_num] = tbl

                # Detect dependencies
                deps = self.detect_table_dependencies(tbl)
                if deps:
                    dependencies[tbl_num] = deps

            # Parse version mappings from the first table's rows
            version_map = {}
            versions = []
            if sorted_tables:
                first_table = sorted_tables[0]
                version_map = self.parse_versions_from_table_rows(first_table, tables_dict)

                # Add version 1 as default (first table is version 1)
                if first_table.metadata.table_number not in version_map.values():
                    version_map['1'] = first_table.metadata.table_number

                versions = sorted(version_map.keys(), key=lambda x: int(x))

            # Create LogcodeData
            logcode_data = LogcodeData(
                logcode=logcode,
                name=data['name'],
                section=data['section'],
                versions=versions,
                version_to_table=version_map,
                tables=tables_dict,
                dependencies=dependencies
            )

            result[logcode] = logcode_data

        self.logcodes = result
        return result
    
    def get_tables_for_version(self, logcode: str, version: str) -> List[ExtractedTable]:
        """
        Get all tables for a specific logcode version, including dependencies.
        
        Args:
            logcode: e.g., "0x1C07"
            version: e.g., "2"
        
        Returns:
            List of tables in order: [main_table, dep1, dep2, ...]
        """
        if logcode not in self.logcodes:
            return []
        
        logcode_data = self.logcodes[logcode]
        
        # Get main table for version
        if version not in logcode_data.version_to_table:
            return []
        
        main_table_num = logcode_data.version_to_table[version]
        
        if main_table_num not in logcode_data.tables:
            return []
        
        result = [logcode_data.tables[main_table_num]]
        
        # Add dependencies recursively
        visited = {main_table_num}
        queue = [main_table_num]
        
        while queue:
            current = queue.pop(0)
            if current in logcode_data.dependencies:
                for dep in logcode_data.dependencies[current]:
                    if dep not in visited and dep in logcode_data.tables:
                        result.append(logcode_data.tables[dep])
                        visited.add(dep)
                        queue.append(dep)
        
        return result


def test_parser():
    """Test the parser on the uploaded PDF"""
    pdf_path = "/mnt/user-data/uploads/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
    
    parser = LogcodeParser(pdf_path)
    logcodes = parser.parse_all_logcodes()
    
    print(f"Found {len(logcodes)} logcodes\n")
    
    # Show example logcode
    for logcode, data in list(logcodes.items())[:2]:
        print(f"=== {logcode}: {data.name} ===")
        print(f"Section: {data.section}")
        print(f"Versions: {data.versions}")
        print(f"Version mappings: {data.version_to_table}")
        print(f"Tables: {list(data.tables.keys())}")
        print(f"Dependencies: {data.dependencies}")
        print()
        
        # Test getting tables for version 2
        if '2' in data.versions:
            tables = parser.get_tables_for_version(logcode, '2')
            print(f"Tables for version 2: {[t.metadata.table_number for t in tables]}")
        print()


if __name__ == "__main__":
    test_parser()
