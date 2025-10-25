"""
Data Storage Layer
Persists parsed logcode data to SQLite database with proper indexing.
"""

import sqlite3
import json
from typing import Dict, List, Optional
from pathlib import Path
from parser import LogcodeData, LogcodeParser
from pdf_extractor import ExtractedTable


class LogcodeDatastore:
    """SQLite datastore for logcode information"""
    
    def __init__(self, db_path: str = "data/parsed_logcodes.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        self._create_schema()
    
    def _create_schema(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Logcodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logcodes (
                logcode TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                section TEXT NOT NULL,
                doc_id INTEGER,
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
            )
        ''')
        
        # Versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logcode TEXT NOT NULL,
                version TEXT NOT NULL,
                table_number TEXT NOT NULL,
                FOREIGN KEY (logcode) REFERENCES logcodes(logcode),
                UNIQUE(logcode, version)
            )
        ''')
        
        # Tables table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logcode TEXT NOT NULL,
                table_number TEXT NOT NULL,
                title TEXT NOT NULL,
                page_start INTEGER,
                page_end INTEGER,
                is_continuation BOOLEAN,
                parent_table_number TEXT,
                raw_caption TEXT,
                FOREIGN KEY (logcode) REFERENCES logcodes(logcode),
                UNIQUE(logcode, table_number)
            )
        ''')
        
        # Table rows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logcode TEXT NOT NULL,
                table_number TEXT NOT NULL,
                row_index INTEGER NOT NULL,
                name TEXT,
                type_name TEXT,
                cnt TEXT,
                off TEXT,
                len TEXT,
                description TEXT,
                FOREIGN KEY (logcode) REFERENCES logcodes(logcode)
            )
        ''')
        
        # Table dependencies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_deps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logcode TEXT NOT NULL,
                table_number TEXT NOT NULL,
                dep_table_number TEXT NOT NULL,
                FOREIGN KEY (logcode) REFERENCES logcodes(logcode),
                UNIQUE(logcode, table_number, dep_table_number)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logcode ON logcodes(logcode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_version ON versions(logcode, version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_table ON tables(logcode, table_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rows ON table_rows(logcode, table_number)')
        
        self.conn.commit()
    
    def add_document(self, source_path: str) -> int:
        """Add a document and return its ID"""
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO documents (source_path) VALUES (?)', (source_path,))
        self.conn.commit()
        return cursor.lastrowid
    
    def store_logcode_data(self, logcode_data: LogcodeData, doc_id: int):
        """Store complete logcode data"""
        cursor = self.conn.cursor()
        
        # Store logcode
        cursor.execute('''
            INSERT OR REPLACE INTO logcodes (logcode, name, section, doc_id)
            VALUES (?, ?, ?, ?)
        ''', (logcode_data.logcode, logcode_data.name, logcode_data.section, doc_id))
        
        # Store versions
        for version, table_num in logcode_data.version_to_table.items():
            cursor.execute('''
                INSERT OR REPLACE INTO versions (logcode, version, table_number)
                VALUES (?, ?, ?)
            ''', (logcode_data.logcode, version, table_num))
        
        # Store tables
        for table_num, table in logcode_data.tables.items():
            cursor.execute('''
                INSERT OR REPLACE INTO tables 
                (logcode, table_number, title, page_start, page_end, 
                 is_continuation, parent_table_number, raw_caption)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                logcode_data.logcode,
                table_num,
                table.metadata.title,
                table.metadata.page_start,
                table.metadata.page_end,
                table.metadata.is_continuation,
                table.metadata.parent_table,
                table.raw_caption
            ))
            
            # Store table rows
            for row_idx, row in enumerate(table.rows):
                # Map row columns to standard fields
                name = row[0] if len(row) > 0 else None
                type_name = row[1] if len(row) > 1 else None
                cnt = row[2] if len(row) > 2 else None
                off = row[3] if len(row) > 3 else None
                len_val = row[4] if len(row) > 4 else None
                description = row[5] if len(row) > 5 else None
                
                cursor.execute('''
                    INSERT INTO table_rows 
                    (logcode, table_number, row_index, name, type_name, cnt, off, len, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    logcode_data.logcode,
                    table_num,
                    row_idx,
                    name, type_name, cnt, off, len_val, description
                ))
        
        # Store dependencies
        for table_num, deps in logcode_data.dependencies.items():
            for dep in deps:
                cursor.execute('''
                    INSERT OR IGNORE INTO table_deps (logcode, table_number, dep_table_number)
                    VALUES (?, ?, ?)
                ''', (logcode_data.logcode, table_num, dep))
        
        self.conn.commit()
    
    def import_from_parser(self, parser: LogcodeParser, source_path: str):
        """Import all logcode data from a parser"""
        doc_id = self.add_document(source_path)
        
        for logcode, data in parser.logcodes.items():
            self.store_logcode_data(data, doc_id)
        
        print(f"Imported {len(parser.logcodes)} logcodes from {source_path}")
    
    def get_logcode_info(self, logcode: str) -> Optional[Dict]:
        """Get basic info about a logcode"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT logcode, name, section FROM logcodes WHERE logcode = ?
        ''', (logcode,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_versions(self, logcode: str) -> List[str]:
        """Get all versions for a logcode"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT version FROM versions WHERE logcode = ? ORDER BY CAST(version AS INTEGER)
        ''', (logcode,))
        return [row['version'] for row in cursor.fetchall()]
    
    def get_table_for_version(self, logcode: str, version: str) -> Optional[str]:
        """Get main table number for a version"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT table_number FROM versions WHERE logcode = ? AND version = ?
        ''', (logcode, version))
        row = cursor.fetchone()
        return row['table_number'] if row else None
    
    def get_table_dependencies(self, logcode: str, table_number: str) -> List[str]:
        """Get all dependencies for a table"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT dep_table_number FROM table_deps 
            WHERE logcode = ? AND table_number = ?
        ''', (logcode, table_number))
        return [row['dep_table_number'] for row in cursor.fetchall()]
    
    def get_table_rows(self, logcode: str, table_number: str) -> List[Dict]:
        """Get all rows for a table in their original PDF extraction order"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT name, type_name, cnt, off, len, description
            FROM table_rows
            WHERE logcode = ? AND table_number = ?
            ORDER BY row_index
        ''', (logcode, table_number))
        return [dict(row) for row in cursor.fetchall()]
    
    def export_to_json(self, output_path: str):
        """Export entire database to JSON"""
        cursor = self.conn.cursor()
        
        # Get all logcodes
        cursor.execute('SELECT logcode FROM logcodes')
        logcodes = [row['logcode'] for row in cursor.fetchall()]
        
        export_data = {}
        
        for logcode in logcodes:
            info = self.get_logcode_info(logcode)
            versions = self.get_versions(logcode)
            
            logcode_data = {
                'name': info['name'],
                'section': info['section'],
                'versions': versions,
                'version_to_table': {},
                'tables': {}
            }
            
            # Get version mappings
            for version in versions:
                table_num = self.get_table_for_version(logcode, version)
                if table_num:
                    logcode_data['version_to_table'][version] = table_num
            
            # Get all tables
            cursor.execute('''
                SELECT DISTINCT table_number, title, page_start, page_end
                FROM tables WHERE logcode = ?
            ''', (logcode,))
            
            for table_row in cursor.fetchall():
                table_num = table_row['table_number']
                rows = self.get_table_rows(logcode, table_num)
                deps = self.get_table_dependencies(logcode, table_num)
                
                logcode_data['tables'][table_num] = {
                    'title': table_row['title'],
                    'page_span': [table_row['page_start'], table_row['page_end']],
                    'rows': rows,
                    'dep_tables': deps
                }
            
            export_data[logcode] = logcode_data
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Exported to {output_path}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def test_datastore():
    """Test the datastore"""
    from parser import LogcodeParser
    
    pdf_path = "/mnt/user-data/uploads/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
    
    # Parse PDF
    print("Parsing PDF...")
    parser = LogcodeParser(pdf_path)
    parser.parse_all_logcodes()
    
    # Store in database
    print("Storing in database...")
    db = LogcodeDatastore("/home/claude/log_parser_project/data/parsed_logcodes.db")
    db.import_from_parser(parser, pdf_path)
    
    # Test queries
    print("\nTesting queries...")
    info = db.get_logcode_info("0x1C07")
    print(f"Logcode info: {info}")
    
    versions = db.get_versions("0x1C07")
    print(f"Versions: {versions}")
    
    if '2' in versions:
        table = db.get_table_for_version("0x1C07", "2")
        print(f"Table for version 2: {table}")
        
        if table:
            rows = db.get_table_rows("0x1C07", table)
            print(f"Number of rows: {len(rows)}")
            if rows:
                print(f"First row: {rows[0]}")
    
    # Export to JSON
    print("\nExporting to JSON...")
    db.export_to_json("/home/claude/log_parser_project/data/parsed_logcodes.json")
    
    db.close()


if __name__ == "__main__":
    test_datastore()
