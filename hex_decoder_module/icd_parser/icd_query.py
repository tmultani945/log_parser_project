"""
High-level API for querying ICD data from PDF.
"""

import re
import pdfplumber
from typing import List, Dict, Optional
from ..models.icd import LogcodeMetadata, FieldDefinition
from ..models.errors import LogcodeNotFoundError, VersionNotFoundError
from .pdf_scanner import PDFScanner
from .section_extractor import SectionExtractor
from .table_parser import TableParser
from .version_parser import VersionParser
from .dependency_resolver import DependencyResolver
from .cache import ICDCache


class ICDQueryEngine:
    """Query engine for ICD PDF data"""

    def __init__(self, pdf_path: str, enable_cache: bool = True):
        """
        Initialize query engine.

        Args:
            pdf_path: Path to ICD PDF file
            enable_cache: Enable in-memory caching
        """
        self.pdf_path = pdf_path
        self.scanner = PDFScanner(pdf_path)
        self.extractor = SectionExtractor()
        self.table_parser = TableParser()
        self.version_parser = VersionParser()
        self.dep_resolver = DependencyResolver()
        self.cache = ICDCache() if enable_cache else None

    def get_logcode_metadata(self, logcode_id: str) -> LogcodeMetadata:
        """
        Get metadata for a logcode.

        This triggers PDF scanning and table extraction if not cached.

        Args:
            logcode_id: Logcode in hex format (e.g., "0xB823")

        Returns:
            LogcodeMetadata with all parsed tables

        Raises:
            LogcodeNotFoundError: If logcode not found
        """
        # Normalize logcode format
        if not logcode_id.startswith('0x'):
            logcode_id = f"0x{logcode_id}"
        logcode_id = logcode_id.upper()

        # Check cache first
        if self.cache:
            cached = self.cache.get(logcode_id)
            if cached:
                return cached

        # STEP 1: Scan PDF to find section
        section_info = self.scanner.find_section(logcode_id)

        # STEP 2: Extract all tables from section
        raw_tables = self.extractor.extract_tables(self.pdf_path, section_info)

        # STEP 3: Separate version table from field tables
        version_table = None
        field_tables = []

        for raw_table in raw_tables:
            # Pass table rows to check for Cond column
            if self.version_parser.is_version_table(raw_table.caption, raw_table.rows):
                version_table = raw_table
            else:
                field_tables.append(raw_table)

        # STEP 4: Parse version table
        version_map = {}
        if version_table:
            version_map = self.version_parser.parse_version_table(version_table)

        # STEP 5: Parse field tables and build dependency graph
        table_definitions = {}  # table_name → List[FieldDefinition]
        dependencies = {}  # table_name → [dependent_table_names]

        for raw_table in field_tables:
            # Extract table number from caption (e.g., "Table 4-4" → "4-4")
            import re
            match = re.search(r'(\d+-\d+)', raw_table.caption)
            if match:
                table_name = match.group(1)
                field_defs = self.table_parser.parse_field_table(raw_table)

                if field_defs:  # Only add if we got valid field definitions
                    table_definitions[table_name] = field_defs

                    # Detect dependencies
                    deps = self.dep_resolver.find_dependencies(field_defs)
                    if deps:
                        dependencies[table_name] = list(deps)

        # STEP 6: Fetch dependent tables that are not in current section
        self._fetch_dependent_tables(dependencies, table_definitions, section_info)

        # STEP 7: Build metadata object
        metadata = LogcodeMetadata(
            logcode_id=logcode_id,
            logcode_name=section_info.section_title,
            section=section_info.section_number,
            description='',
            version_offset=0,  # Assume version at offset 0
            version_length=32,  # Assume 32-bit version
            version_map=version_map,
            table_definitions=table_definitions,
            dependencies=dependencies
        )

        # Cache for future use
        if self.cache:
            self.cache.set(logcode_id, metadata)

        return metadata

    def get_version_layout(self, logcode_id: str, version: int) -> List[FieldDefinition]:
        """
        Get field layout for a specific version, including all dependent tables.

        Args:
            logcode_id: Logcode hex ID
            version: Version number

        Returns:
            List of FieldDefinition objects (main table + dependencies)

        Raises:
            LogcodeNotFoundError: If logcode not found
            VersionNotFoundError: If version not found
        """
        metadata = self.get_logcode_metadata(logcode_id)

        # Look up table name for this version
        table_name = metadata.version_map.get(version)

        if not table_name:
            # Try to find a default table if no version mapping exists
            if len(metadata.table_definitions) == 1:
                # Only one table - use it
                table_name = list(metadata.table_definitions.keys())[0]
            else:
                raise VersionNotFoundError(logcode_id, version)

        # Get main table fields
        field_defs = metadata.table_definitions.get(table_name, [])

        if not field_defs:
            raise VersionNotFoundError(logcode_id, version)

        # Expand wrapper fields that reference other tables
        expanded_fields = self._expand_table_references(
            field_defs,
            metadata,
            version_offset=metadata.version_offset + (metadata.version_length + 7) // 8
        )

        return expanded_fields

    def _expand_table_references(
        self,
        fields: List[FieldDefinition],
        metadata,
        version_offset: int = 0
    ) -> List[FieldDefinition]:
        """
        Expand fields that reference other tables (Type Name = 'Table X-Y').

        When a field has type 'Table X-Y', it's a container for the fields in that table.
        We replace it with the actual fields from that table, adjusting their offsets.
        """
        import re
        from copy import deepcopy

        expanded = []

        for field in fields:
            # Check if this field references a table
            table_ref_match = re.search(r'Table\s+(\d+-\d+)', field.type_name, re.IGNORECASE)

            if table_ref_match:
                # This is a wrapper field - replace with referenced table's fields
                ref_table_name = table_ref_match.group(1)

                if ref_table_name in metadata.table_definitions:
                    # Get fields from referenced table
                    ref_fields = metadata.table_definitions[ref_table_name]

                    # Adjust offsets: field.offset_bytes + version_offset
                    base_offset_bits = field.offset_bytes * 8 + field.offset_bits + version_offset * 8

                    for ref_field in ref_fields:
                        # Create adjusted copy
                        adjusted_field = deepcopy(ref_field)

                        # Adjust offset
                        ref_field_offset_bits = ref_field.offset_bytes * 8 + ref_field.offset_bits
                        total_offset_bits = base_offset_bits + ref_field_offset_bits

                        adjusted_field.offset_bytes = total_offset_bits // 8
                        adjusted_field.offset_bits = total_offset_bits % 8

                        expanded.append(adjusted_field)
                else:
                    # Referenced table not found - keep wrapper field as-is
                    expanded.append(field)
            else:
                # Regular field - keep as-is, but adjust for version offset
                adjusted_field = deepcopy(field)
                total_offset_bits = (field.offset_bytes * 8 + field.offset_bits + version_offset * 8)
                adjusted_field.offset_bytes = total_offset_bits // 8
                adjusted_field.offset_bits = total_offset_bits % 8
                expanded.append(adjusted_field)

        return expanded

    def list_available_versions(self, logcode_id: str) -> List[int]:
        """
        List all versions defined for a logcode.

        Args:
            logcode_id: Logcode hex ID

        Returns:
            List of version numbers
        """
        metadata = self.get_logcode_metadata(logcode_id)
        return sorted(metadata.version_map.keys())

    def clear_cache(self) -> None:
        """Clear the cache"""
        if self.cache:
            self.cache.clear()

    def get_cache_size(self) -> int:
        """Get current cache size"""
        return self.cache.size() if self.cache else 0

    def _fetch_dependent_tables(
        self,
        dependencies: Dict[str, List[str]],
        table_definitions: Dict[str, List[FieldDefinition]],
        section_info
    ) -> None:
        """
        Fetch dependent tables that are not in the current section.

        Searches nearby pages for missing tables and extracts them.

        Args:
            dependencies: Dict of table_name → [dependent_tables]
            table_definitions: Dict to update with found tables
            section_info: Current section info
        """
        # Find all referenced tables
        all_refs = set()
        for deps in dependencies.values():
            all_refs.update(deps)

        # Find missing tables (referenced but not extracted)
        missing = all_refs - set(table_definitions.keys())

        if not missing:
            return

        print(f"Fetching {len(missing)} dependent tables: {missing}")

        # Search nearby pages (within 10 pages of section boundaries)
        search_start = max(0, section_info.start_page - 5)
        search_end = min(section_info.end_page + 10, section_info.end_page + 10)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in range(search_start, min(search_end + 1, len(pdf.pages))):
                if not missing:
                    break  # All found

                page = pdf.pages[page_num]
                text = page.extract_text()
                if not text:
                    continue

                # Check if any missing table is on this page
                for table_num in list(missing):
                    caption_pattern = f"Table {table_num}"

                    # Only check if caption is at start of line
                    lines = text.split('\n')
                    found_on_page = False
                    for line in lines:
                        if line.strip().startswith(caption_pattern):
                            found_on_page = True
                            break

                    if found_on_page:
                        print(f"  Found Table {table_num} on page {page_num}")

                        # Extract and parse this table
                        tables = page.extract_tables()
                        page_text_lines = text.split('\n')

                        # Find captions on this page
                        captions_on_page = []
                        for line in page_text_lines:
                            if re.match(r'^Table\s+\d+-\d+', line, re.IGNORECASE):
                                match = re.search(r'Table\s+(\d+-\d+)', line, re.IGNORECASE)
                                if match:
                                    captions_on_page.append(f"Table {match.group(1)}")

                        # Try to match the table with its caption
                        for i, table_data in enumerate(tables):
                            if not table_data or len(table_data) < 2:
                                continue

                            # Use caption if available
                            table_caption = captions_on_page[i] if i < len(captions_on_page) else ""

                            if table_num in table_caption:
                                # Parse this table
                                from ..models.icd import RawTable
                                raw_table = RawTable(
                                    caption=table_caption,
                                    rows=table_data,
                                    page_num=page_num
                                )

                                field_defs = self.table_parser.parse_field_table(raw_table)
                                if field_defs:
                                    table_definitions[table_num] = field_defs
                                    missing.remove(table_num)
                                    print(f"    Extracted {len(field_defs)} fields from Table {table_num}")
                                break

        if missing:
            print(f"Warning: Could not find {len(missing)} dependent tables: {missing}")
