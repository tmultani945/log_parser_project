"""
PDF Extraction Layer
Extracts text, tables, and metadata from technical PDF documents.
Handles table continuations, header deduplication, and caption detection.
"""

import re
import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class TableMetadata:
    """Metadata for an extracted table"""
    table_number: str  # e.g., "4-4"
    title: str  # e.g., "Nr5g_Sub6TxAgc_V2"
    page_start: int
    page_end: int
    is_continuation: bool = False
    parent_table: Optional[str] = None  # If this is a sub-table


@dataclass
class ExtractedTable:
    """Represents a fully extracted table with all continuations merged"""
    metadata: TableMetadata
    headers: List[str]
    rows: List[List[str]]
    raw_caption: str


class PDFExtractor:
    """Extracts structured content from technical PDF documents"""
    
    # Standard headers for log packet tables
    STANDARD_HEADERS = ["Name", "Type Name", "Cnt", "Off", "Len", "Description"]
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.plumber_pdf = pdfplumber.open(pdf_path)
        
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'doc'):
            self.doc.close()
        if hasattr(self, 'plumber_pdf'):
            self.plumber_pdf.close()
    
    def extract_section_context(self, page_num: int) -> Optional[Dict[str, str]]:
        """
        Extract section number and logcode from page context.
        Looks for patterns like: "4.1 NR5G Sub6 TxAGC (0x1C07)"
        
        Returns:
            Dict with 'section', 'logcode', 'name' or None
        """
        page = self.doc[page_num]
        text = page.get_text()
        
        # Pattern: Section number, name, and hex code
        pattern = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'
        
        for line in text.split('\n'):
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return {
                    'section': match.group(1),
                    'name': match.group(2).strip(),
                    'logcode': match.group(3)
                }
        
        return None
    
    def detect_table_caption(self, text_block: str) -> Optional[Tuple[str, str, bool]]:
        """
        Detect table captions like "Table 4-4 Nr5g_Sub6TxAgc_V2" or "Table 4-4 ... (cont.)"
        
        Returns:
            Tuple of (table_number, title, is_continuation) or None
        """
        # Match "Table X-Y Title" or "Table X-Y Title (cont.)"
        pattern = r'Table\s+(\d+-\d+)\s+(.+?)(?:\s+\(cont\.\))?$'
        match = re.search(pattern, text_block, re.IGNORECASE)
        
        if match:
            table_num = match.group(1)
            title = match.group(2).strip()
            is_cont = '(cont.)' in text_block.lower()
            return (table_num, title, is_cont)
        
        return None
    
    def normalize_headers(self, headers: List[str]) -> List[str]:
        """
        Normalize table headers to standard format.
        Handles variations in spacing, case, etc.
        """
        normalized = []
        for header in headers:
            h = header.strip()
            # Match against standard headers (case-insensitive)
            for std_header in self.STANDARD_HEADERS:
                if h.lower() == std_header.lower():
                    normalized.append(std_header)
                    break
            else:
                # Keep original if no match
                normalized.append(h)
        return normalized
    
    def extract_tables_from_page(self, page_num: int) -> List[Dict]:
        """
        Extract all tables from a single page using pdfplumber.
        
        Returns:
            List of dicts with 'caption', 'headers', 'rows', 'bbox'
        """
        page = self.plumber_pdf.pages[page_num]
        tables = page.extract_tables()
        
        # Get text to find captions
        text = page.extract_text()
        lines = text.split('\n') if text else []
        
        extracted = []
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # First row is typically headers
            headers = [str(cell).strip() if cell else '' for cell in table[0]]
            rows = [[str(cell).strip() if cell else '' for cell in row] for row in table[1:]]
            
            # Try to find caption by looking at text above table
            caption = self._find_caption_for_table(lines, table)
            
            extracted.append({
                'caption': caption,
                'headers': self.normalize_headers(headers),
                'rows': rows,
                'page': page_num
            })
        
        return extracted
    
    def _find_caption_for_table(self, text_lines: List[str], table: List[List]) -> str:
        """Find the caption line that precedes a table"""
        # Look for "Table X-Y" pattern in recent lines
        for i, line in enumerate(text_lines):
            if self.detect_table_caption(line):
                return line.strip()
        return ""
    
    def merge_continuations(self, tables: List[Dict]) -> List[ExtractedTable]:
        """
        Merge table continuations into single logical tables.
        Removes duplicate headers from continuation pages.
        """
        merged = {}
        
        for table_dict in tables:
            caption = table_dict.get('caption', '')
            detection = self.detect_table_caption(caption)
            
            if not detection:
                continue
            
            table_num, title, is_cont = detection
            
            if table_num not in merged:
                # First occurrence - create new entry
                metadata = TableMetadata(
                    table_number=table_num,
                    title=title,
                    page_start=table_dict['page'],
                    page_end=table_dict['page'],
                    is_continuation=False
                )
                merged[table_num] = ExtractedTable(
                    metadata=metadata,
                    headers=table_dict['headers'],
                    rows=table_dict['rows'],
                    raw_caption=caption
                )
            else:
                # Continuation - merge rows
                existing = merged[table_num]
                existing.metadata.page_end = table_dict['page']
                
                # Check if first row is duplicate header
                first_row = table_dict['rows'][0] if table_dict['rows'] else []
                if self._is_header_row(first_row, existing.headers):
                    # Skip the duplicate header
                    existing.rows.extend(table_dict['rows'][1:])
                else:
                    existing.rows.extend(table_dict['rows'])
        
        return list(merged.values())
    
    def _is_header_row(self, row: List[str], headers: List[str]) -> bool:
        """Check if a row is actually a repeated header"""
        if len(row) != len(headers):
            return False
        
        # Case-insensitive comparison
        for cell, header in zip(row, headers):
            if cell.lower().strip() != header.lower().strip():
                return False
        return True
    
    def extract_all_tables(self) -> List[ExtractedTable]:
        """
        Extract all tables from the entire PDF, merging continuations.
        
        Returns:
            List of ExtractedTable objects
        """
        all_tables = []
        
        # Extract tables from each page
        for page_num in range(len(self.doc)):
            page_tables = self.extract_tables_from_page(page_num)
            all_tables.extend(page_tables)
        
        # Merge continuations
        merged_tables = self.merge_continuations(all_tables)
        
        return merged_tables
    
    def extract_versions_table(self, logcode: str, tables: List[ExtractedTable]) -> Optional[ExtractedTable]:
        """
        Find the versions table for a specific logcode.
        Versions tables end with "_Versions" (e.g., "Nr5g_Sub6TxAgc_Versions")
        """
        for table in tables:
            if table.metadata.title.endswith('_Versions'):
                # Check if this versions table belongs to the logcode section
                # This would require context from the parser layer
                return table
        return None


def test_extractor():
    """Test the PDF extractor on the uploaded file"""
    pdf_path = "/mnt/user-data/uploads/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
    
    extractor = PDFExtractor(pdf_path)
    
    # Extract all tables
    tables = extractor.extract_all_tables()
    
    print(f"Extracted {len(tables)} tables")
    
    # Show first few tables
    for i, table in enumerate(tables[:5]):
        print(f"\n--- Table {i+1}: {table.metadata.table_number} ---")
        print(f"Title: {table.metadata.title}")
        print(f"Pages: {table.metadata.page_start}-{table.metadata.page_end}")
        print(f"Headers: {table.headers}")
        print(f"Rows: {len(table.rows)}")
        if table.rows:
            print(f"First row: {table.rows[0]}")


if __name__ == "__main__":
    test_extractor()
