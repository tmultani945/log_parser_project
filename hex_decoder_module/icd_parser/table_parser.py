"""
Parses raw table data into structured FieldDefinition objects.
"""

from typing import List, Dict, Optional
from ..models.icd import FieldDefinition, RawTable
from ..models.errors import TableParsingError


class TableParser:
    """Parses tables into field definitions"""

    STANDARD_HEADERS = ['Name', 'Type Name', 'Cnt', 'Off', 'Len', 'Description']

    def parse_field_table(self, raw_table: RawTable) -> List[FieldDefinition]:
        """
        Parse a field definition table.

        Args:
            raw_table: Raw table extracted from PDF

        Returns:
            List of FieldDefinition objects

        Raises:
            TableParsingError: If table cannot be parsed
        """
        rows = raw_table.rows

        if not rows or len(rows) < 2:
            # Need at least header + one data row
            return []

        try:
            # First row is header
            header = rows[0]
            data_rows = rows[1:]

            # Normalize header to standard format
            header_map = self._normalize_headers(header)

            # Verify we have minimum required columns
            if 'Name' not in header_map or 'Type Name' not in header_map:
                # This might not be a field definition table
                return []

            # Parse each data row
            field_defs = []
            for row_idx, row in enumerate(data_rows):
                if not row or all(cell is None or (isinstance(cell, str) and cell.strip() == '') for cell in row):
                    continue  # Skip empty rows

                field_def = self._parse_field_row(row, header_map, raw_table.caption, row_idx)
                if field_def:
                    field_defs.append(field_def)

            return field_defs

        except Exception as e:
            raise TableParsingError(f"Error parsing table {raw_table.caption}: {str(e)}")

    def _normalize_headers(self, header: List[str]) -> Dict[str, int]:
        """
        Map standard header names to column indices.

        Args:
            header: Header row from table

        Returns:
            Dict like {'Name': 0, 'Type Name': 1, ...}
        """
        header_map = {}

        for idx, cell in enumerate(header):
            if cell is None:
                continue

            cell_clean = cell.strip().lower() if isinstance(cell, str) else ''

            # Match to standard headers
            if 'name' in cell_clean and 'type' not in cell_clean:
                header_map['Name'] = idx
            elif 'type' in cell_clean:
                header_map['Type Name'] = idx
            elif cell_clean in ['cnt', 'count']:
                header_map['Cnt'] = idx
            elif cell_clean in ['off', 'offset']:
                header_map['Off'] = idx
            elif cell_clean in ['len', 'length']:
                header_map['Len'] = idx
            elif 'desc' in cell_clean:
                header_map['Description'] = idx

        return header_map

    def _parse_field_row(
        self,
        row: List[str],
        header_map: Dict[str, int],
        table_caption: str,
        row_idx: int
    ) -> Optional[FieldDefinition]:
        """
        Parse a single row into a FieldDefinition.

        Args:
            row: Data row
            header_map: Column name to index mapping
            table_caption: Table caption for error messages
            row_idx: Row index for error messages

        Returns:
            FieldDefinition or None if row cannot be parsed
        """
        try:
            # Extract required fields
            name_idx = header_map.get('Name')
            type_idx = header_map.get('Type Name')

            if name_idx is None or type_idx is None:
                return None

            if name_idx >= len(row) or type_idx >= len(row):
                return None

            name = row[name_idx]
            type_name = row[type_idx]

            if not name or not type_name:
                return None

            name = name.strip() if isinstance(name, str) else str(name)
            type_name = type_name.strip() if isinstance(type_name, str) else str(type_name)

            # Extract optional fields
            offset_str = ''
            length_str = ''
            description = ''

            if 'Off' in header_map and header_map['Off'] < len(row):
                offset_str = row[header_map['Off']]
                offset_str = offset_str.strip() if isinstance(offset_str, str) else ''

            if 'Len' in header_map and header_map['Len'] < len(row):
                length_str = row[header_map['Len']]
                length_str = length_str.strip() if isinstance(length_str, str) else ''

            if 'Description' in header_map and header_map['Description'] < len(row):
                description = row[header_map['Description']]
                description = description.strip() if isinstance(description, str) else ''

            # Parse offset (in BITS from PDF, convert to bytes + bit offset)
            offset_bits_total = 0
            if offset_str and offset_str.isdigit():
                offset_bits_total = int(offset_str)

            # Convert total bit offset to bytes + remaining bits
            offset_bytes = offset_bits_total // 8
            offset_bits = offset_bits_total % 8

            # Parse length (bits)
            length_bits = 0
            if length_str and length_str.isdigit():
                length_bits = int(length_str)

            # Try to infer length from type name if not specified
            if length_bits == 0 and type_name:
                length_bits = self._infer_length_from_type(type_name)

            # Parse enum mappings from description if type is Enumeration
            enum_mappings = None
            if 'enum' in type_name.lower() and description:
                enum_mappings = self._parse_enum_mappings(description)

            return FieldDefinition(
                name=name,
                type_name=type_name,
                offset_bytes=offset_bytes,
                offset_bits=offset_bits,
                length_bits=length_bits,
                description=description,
                enum_mappings=enum_mappings
            )

        except (KeyError, ValueError, IndexError, AttributeError) as e:
            # Skip malformed rows
            return None

    def _infer_length_from_type(self, type_name: str) -> int:
        """
        Infer bit length from type name.

        Args:
            type_name: Type name (e.g., "Uint16", "Bool")

        Returns:
            Bit length
        """
        type_lower = type_name.lower()

        if 'uint8' in type_lower or 'int8' in type_lower:
            return 8
        elif 'uint16' in type_lower or 'int16' in type_lower:
            return 16
        elif 'uint32' in type_lower or 'int32' in type_lower:
            return 32
        elif 'uint64' in type_lower or 'int64' in type_lower:
            return 64
        elif 'bool' in type_lower:
            return 1
        else:
            # Check for numeric suffix (e.g., "Uint<24>")
            import re
            match = re.search(r'(\d+)', type_name)
            if match:
                return int(match.group(1))

        return 0  # Unknown

    def _parse_enum_mappings(self, description: str) -> Dict[int, str]:
        """
        Parse enum mappings from description text.

        Example input:
            "Values:\\n• 0 – NONE\\n• 1 – SINGLE STANDBY\\n• 2 – DUAL STANDBY"

        Returns:
            Dict mapping int values to string names {0: "NONE", 1: "SINGLE STANDBY", ...}
        """
        import re

        mappings = {}

        # Pattern to match: "• 0 – NONE" or "0 – NONE" or "0: NONE"
        # Handle bullet points (•, -, *) and separators (–, -, :)
        pattern = r'[•\-\*]?\s*(\d+)\s*[–\-:]\s*(.+?)(?=\n|$)'

        for match in re.finditer(pattern, description, re.MULTILINE):
            try:
                value = int(match.group(1))
                name = match.group(2).strip()
                mappings[value] = name
            except (ValueError, IndexError):
                continue

        return mappings if mappings else None
