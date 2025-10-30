"""
Parses "_Versions" tables to extract version→table mappings.
"""

import re
from typing import Dict
from ..models.icd import RawTable


class VersionParser:
    """Parses version mapping tables"""

    def parse_version_table(self, raw_table: RawTable) -> Dict[int, str]:
        """
        Parse a version mapping table.

        Supports two formats:

        Format 1 - "_Versions" table:
            | Version | Details         |
            |---------|-----------------|
            | 1       | Defined in 4-4  |
            | 2       | Defined in 4-4  |

        Format 2 - "Cond" column table:
            | Name           | Type Name  | Cnt | Off | Len | Cond   | Description |
            |----------------|------------|-----|-----|-----|--------|-------------|
            | Version 1      | Table 4-4  | 1   | 0   | 176 | 1      | ...         |
            | Version 0x3003 | Table 4-5  | 1   | 0   | 360 | 196611 | ...         |

        Args:
            raw_table: Raw table from PDF

        Returns:
            Dict mapping version number to table name
            Example: {1: "4-4", 2: "4-4", 196611: "11-56"}
        """
        version_map = {}

        rows = raw_table.rows
        if len(rows) < 2:
            return version_map

        header = rows[0]

        # Check if this table has a "Cond" column
        cond_idx = None
        for idx, cell in enumerate(header):
            if cell and 'cond' in str(cell).lower():
                cond_idx = idx
                break

        if cond_idx is not None:
            # Format 2: Table with Cond column
            return self._parse_cond_table(rows, cond_idx)
        else:
            # Format 1: Traditional _Versions table
            return self._parse_traditional_versions_table(rows)

    def _parse_cond_table(self, rows: list, cond_idx: int) -> Dict[int, str]:
        """
        Parse version table with Cond column.

        Expected format:
            Row: ['Version 0x3003', 'Table 11-56', '', '0', '360', '196611', '']
                  ^Name             ^Type Name                      ^Cond (version decimal)
        """
        version_map = {}

        for row in rows[1:]:  # Skip header
            if len(row) <= cond_idx or len(row) < 2:
                continue

            # Get Cond value (version in decimal)
            cond_cell = row[cond_idx]
            if not cond_cell:
                continue

            cond_str = str(cond_cell).strip()

            # Get table reference from Type Name column (usually column 1)
            type_name_cell = row[1] if len(row) > 1 else ''
            if not type_name_cell:
                continue

            type_name = str(type_name_cell).strip()

            # Extract table number
            table_match = re.search(r'(\d+-\d+)', type_name)
            if not table_match:
                continue

            table_name = table_match.group(1)

            # Parse version number from Cond
            try:
                version_num = int(cond_str)
                version_map[version_num] = table_name
            except ValueError:
                continue

        return version_map

    def _parse_traditional_versions_table(self, rows: list) -> Dict[int, str]:
        """Parse traditional _Versions table format."""
        version_map = {}

        for row in rows[1:]:  # Skip header
            if len(row) < 2:
                continue

            # Extract version number (first column)
            version_cell = row[0]
            if not version_cell:
                continue

            version_str = str(version_cell).strip()

            # Extract table reference from second column
            details_cell = row[1] if len(row) > 1 else ''
            if not details_cell:
                continue

            details = str(details_cell).strip()

            # Try to extract table number
            table_match = re.search(r'(\d+-\d+)', details)

            if table_match:
                table_name = table_match.group(1)

                # Try to parse version as integer
                try:
                    if version_str.startswith('0x') or version_str.startswith('0X'):
                        # Hex version
                        version_num = int(version_str, 16)
                    else:
                        # Decimal version
                        version_num = int(version_str)

                    version_map[version_num] = table_name

                except ValueError:
                    continue

        return version_map

    def is_version_table(self, table_caption: str, table_rows: list = None) -> bool:
        """
        Check if a table is a version mapping table.

        Args:
            table_caption: Table caption
            table_rows: Optional table rows to check for Cond column

        Returns:
            True if this is a version table
        """
        caption_lower = table_caption.lower()

        # Check caption for version keywords
        if '_version' in caption_lower or 'version' in caption_lower:
            return True

        # Check if table has "Cond" column (alternative version table format)
        if table_rows and len(table_rows) > 0:
            header = table_rows[0]
            if any(cell and 'cond' in str(cell).lower() for cell in header):
                # Also check if Name column has "Version" entries
                if len(table_rows) > 1:
                    for row in table_rows[1:]:
                        if row and len(row) > 0 and row[0]:
                            if 'version' in str(row[0]).lower():
                                return True

        return False
