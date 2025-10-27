"""
Query Interface Layer
Provides user-facing query functions with formatted table output.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from datastore import LogcodeDatastore


@dataclass
class TableDisplay:
    """Formatted table for display"""
    table_number: str
    title: str
    logcode: str
    logcode_name: str
    section: str
    headers: List[str]
    rows: List[Dict[str, str]]


class QueryEngine:
    """Query interface for logcode data"""
    
    STANDARD_HEADERS = ["Name", "Type Name", "Cnt", "Off", "Len", "Description"]
    
    def __init__(self, db_path: str = "data/parsed_logcodes.db"):
        self.db = LogcodeDatastore(db_path)
    
    def get_table(self, logcode: str, version: str) -> List[TableDisplay]:
        """
        Get formatted table(s) for a logcode and version.
        Includes main table and all dependencies.
        
        Args:
            logcode: e.g., "0x1C07"
            version: e.g., "2"
        
        Returns:
            List of TableDisplay objects in order (main table first, then dependencies)
        """
        # Normalize logcode format
        if not logcode.upper().startswith('0X'):
            logcode = '0X' + logcode.upper()
        else:
            logcode = logcode.upper()
        
        # Get logcode info
        info = self.db.get_logcode_info(logcode)
        if not info:
            raise ValueError(f"Logcode {logcode} not found")
        
        # Check version exists
        versions = self.db.get_versions(logcode)
        if version not in versions:
            available = ', '.join(versions)
            raise ValueError(f"Version {version} not found for {logcode}. Available versions: {available}")
        
        # Get main table
        main_table_num = self.db.get_table_for_version(logcode, version)
        if not main_table_num:
            raise ValueError(f"No table found for version {version}")
        
        # Get all tables (main + dependencies)
        table_numbers = [main_table_num]
        table_numbers.extend(self._get_all_dependencies(logcode, main_table_num))

        # Sort table numbers numerically (format: "X-Y")
        def table_sort_key(table_num):
            parts = table_num.split('-')
            return (int(parts[0]), int(parts[1]))
        table_numbers.sort(key=table_sort_key)

        # Format tables for display
        result = []
        for table_num in table_numbers:
            display = self._format_table(logcode, table_num, info)
            if display:
                result.append(display)
        
        return result
    
    def _get_all_dependencies(self, logcode: str, table_number: str) -> List[str]:
        """Recursively get all dependencies"""
        all_deps = []
        visited = set()
        queue = [table_number]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            deps = self.db.get_table_dependencies(logcode, current)
            for dep in deps:
                if dep not in visited:
                    all_deps.append(dep)
                    queue.append(dep)
        
        return all_deps
    
    def _format_table(self, logcode: str, table_number: str, logcode_info: Dict) -> Optional[TableDisplay]:
        """Format a single table for display"""
        rows = self.db.get_table_rows(logcode, table_number)
        if not rows:
            return None
        
        # Get table metadata
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT title FROM tables WHERE logcode = ? AND table_number = ?
        ''', (logcode.upper(), table_number))
        table_row = cursor.fetchone()
        title = table_row['title'] if table_row else table_number
        
        return TableDisplay(
            table_number=table_number,
            title=title,
            logcode=logcode,
            logcode_name=logcode_info['name'],
            section=logcode_info['section'],
            headers=self.STANDARD_HEADERS,
            rows=rows
        )
    
    def format_output(self, tables: List[TableDisplay]) -> str:
        """
        Format tables as readable text output.
        
        Returns:
            Formatted string with tables
        """
        output_lines = []
        
        for i, table in enumerate(tables):
            # Header
            output_lines.append("=" * 80)
            output_lines.append(f"Table {table.table_number}: {table.title}")
            output_lines.append(f"Logcode: {table.logcode} - {table.logcode_name}")
            output_lines.append(f"Section: {table.section}")
            output_lines.append("=" * 80)
            output_lines.append("")
            
            # Column headers
            col_widths = self._calculate_column_widths(table)
            header_row = " | ".join(
                header.ljust(col_widths[i]) 
                for i, header in enumerate(table.headers)
            )
            output_lines.append(header_row)
            output_lines.append("-" * len(header_row))
            
            # Data rows
            for row in table.rows:
                # Clean description: remove newlines and extra whitespace
                description = row.get('description', '')
                if description:
                    # Replace newlines with spaces
                    description = description.replace('\n', ' ').replace('\r', ' ')
                    # Replace multiple spaces with single space
                    description = ' '.join(description.split())
                    # Truncate if too long
                    if len(description) > 50:
                        description = description[:47] + '...'

                row_values = [
                    row.get('name', ''),
                    row.get('type_name', ''),
                    row.get('cnt', ''),
                    row.get('off', ''),
                    row.get('len', ''),
                    description
                ]

                row_str = " | ".join(
                    str(val).ljust(col_widths[i])
                    for i, val in enumerate(row_values)
                )
                output_lines.append(row_str)
            
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    def _calculate_column_widths(self, table: TableDisplay) -> List[int]:
        """Calculate optimal column widths"""
        widths = [len(h) for h in table.headers]

        for row in table.rows:
            # Clean description for width calculation
            description = row.get('description', '')
            if description:
                description = description.replace('\n', ' ').replace('\r', ' ')
                description = ' '.join(description.split())
                if len(description) > 50:
                    description = description[:47] + '...'

            values = [
                row.get('name', ''),
                row.get('type_name', ''),
                row.get('cnt', ''),
                row.get('off', ''),
                row.get('len', ''),
                description
            ]

            for i, val in enumerate(values):
                widths[i] = max(widths[i], len(str(val)))

        # Cap description width
        widths[5] = min(widths[5], 50)

        return widths
    
    def list_all_logcodes(self) -> List[Dict[str, str]]:
        """List all available logcodes with their names"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT logcode, name, section FROM logcodes
            ORDER BY
                CAST(SUBSTR(section, 1, INSTR(section, '.') - 1) AS INTEGER),
                CAST(SUBSTR(section, INSTR(section, '.') + 1) AS INTEGER)
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def search_logcode(self, search_term: str) -> List[Dict[str, str]]:
        """
        Search for logcodes by code or name.

        Args:
            search_term: Partial logcode or name to search for

        Returns:
            List of matching logcodes
        """
        cursor = self.db.conn.cursor()
        search_upper = search_term.upper()
        cursor.execute('''
            SELECT logcode, name, section
            FROM logcodes
            WHERE logcode LIKE ? OR UPPER(name) LIKE ?
            ORDER BY logcode
        ''', (f'%{search_upper}%', f'%{search_upper}%'))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        self.db.close()


def test_query_engine():
    """Test the query engine"""
    engine = QueryEngine("/home/claude/log_parser_project/data/parsed_logcodes.db")
    
    # List all logcodes
    print("=== All Logcodes ===")
    logcodes = engine.list_all_logcodes()
    for lc in logcodes[:5]:  # Show first 5
        print(f"{lc['logcode']}: {lc['name']} (Section {lc['section']})")
    
    print(f"\n(Total: {len(logcodes)} logcodes)\n")
    
    # Query specific logcode and version
    print("=== Querying 0x1C07, Version 2 ===\n")
    try:
        tables = engine.get_table("0x1C07", "2")
        output = engine.format_output(tables)
        # Print first 1000 chars
        print(output[:1000])
        print("\n... (truncated)")
        print(f"\nTotal tables returned: {len(tables)}")
    except ValueError as e:
        print(f"Error: {e}")
    
    # Search
    print("\n=== Search for 'TxAGC' ===")
    results = engine.search_logcode("TxAGC")
    for result in results:
        print(f"{result['logcode']}: {result['name']}")
    
    engine.close()


if __name__ == "__main__":
    test_query_engine()
