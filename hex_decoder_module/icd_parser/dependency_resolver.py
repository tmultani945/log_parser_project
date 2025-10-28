"""
Resolves table dependencies by extracting referenced tables.
"""

import re
from typing import List, Set
from ..models.icd import FieldDefinition


class DependencyResolver:
    """Finds and resolves table dependencies"""

    # Pattern: "Table X-Y" in Type Name column
    TABLE_REF_PATTERN = re.compile(r'Table\s+(\d+-\d+)', re.IGNORECASE)

    def find_dependencies(self, field_defs: List[FieldDefinition]) -> Set[str]:
        """
        Find all table references in field definitions.

        Args:
            field_defs: List of field definitions

        Returns:
            Set of table names referenced (e.g., {"4-5", "4-6"})
        """
        dependencies = set()

        for field_def in field_defs:
            # Check Type Name column for table references
            match = self.TABLE_REF_PATTERN.search(field_def.type_name)
            if match:
                table_name = match.group(1)
                dependencies.add(table_name)

            # Also check description field
            if field_def.description:
                match = self.TABLE_REF_PATTERN.search(field_def.description)
                if match:
                    table_name = match.group(1)
                    dependencies.add(table_name)

        return dependencies

    def has_dependencies(self, field_defs: List[FieldDefinition]) -> bool:
        """
        Check if field definitions have any table dependencies.

        Args:
            field_defs: List of field definitions

        Returns:
            True if dependencies found
        """
        return len(self.find_dependencies(field_defs)) > 0
