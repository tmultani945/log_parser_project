"""
Extracts all tables from a specific section of the PDF.
"""

import re
import pdfplumber
from typing import List
from ..models.icd import RawTable, LogcodeSectionInfo
from ..models.errors import PDFScanError


class SectionExtractor:
    """Extracts tables from a PDF section"""

    TABLE_CAPTION_PATTERN = re.compile(
        r'Table\s+(\d+-\d+(?:\s*\(cont\.\)?)?)',
        re.IGNORECASE
    )

    def extract_tables(self, pdf_path: str, section_info: LogcodeSectionInfo) -> List[RawTable]:
        """
        Extract all tables within the specified section.

        Args:
            pdf_path: Path to PDF file
            section_info: Section location info from PDFScanner

        Returns:
            List of RawTable objects (with continuations merged)

        Raises:
            PDFScanError: If PDF cannot be read
        """
        try:
            raw_tables = []

            with pdfplumber.open(pdf_path) as pdf:
                # Iterate through pages in the section
                for page_num in range(section_info.start_page, section_info.end_page + 1):
                    if page_num >= len(pdf.pages):
                        break

                    page = pdf.pages[page_num]

                    # Extract text to find table captions
                    text = page.extract_text() or ""

                    # Find all table captions on this page
                    captions = self._find_table_captions(text)

                    # Extract tables from this page
                    tables = page.extract_tables()

                    # Try to match tables with captions
                    for i, table_data in enumerate(tables):
                        if not table_data or len(table_data) == 0:
                            continue

                        # Use caption if available, otherwise generate generic name
                        caption = captions[i] if i < len(captions) else f"Table_{page_num}_{i}"

                        raw_tables.append(RawTable(
                            caption=caption,
                            rows=table_data,
                            page_num=page_num
                        ))

            # Merge continuations
            merged_tables = self._merge_continuations(raw_tables)

            return merged_tables

        except Exception as e:
            raise PDFScanError(f"Error extracting tables: {str(e)}")

    def _find_table_captions(self, text: str) -> List[str]:
        """
        Find all table captions in the text.

        Only matches captions at the START of a line to avoid matching
        table references inside table cells.

        Args:
            text: Page text

        Returns:
            List of table captions (e.g., ["Table 4-4", "Table 4-5"])
        """
        captions = []

        # Split into lines and check each line
        lines = text.split('\n')
        for line in lines:
            # Only match "Table X-Y" at the start of the line
            # This avoids matching references like "Serving Cell Info Table 11-55"
            if re.match(r'^Table\s+\d+-\d+', line, re.IGNORECASE):
                match = self.TABLE_CAPTION_PATTERN.search(line)
                if match:
                    caption = f"Table {match.group(1)}"
                    captions.append(caption)

        return captions

    def _merge_continuations(self, raw_tables: List[RawTable]) -> List[RawTable]:
        """
        Merge tables with "(cont.)" suffix into their parent tables.

        Example:
            "Table 4-4" on page 45
            "Table 4-4 (cont.)" on page 46
            → Merge into single "Table 4-4"

        Args:
            raw_tables: List of raw tables

        Returns:
            List of merged tables
        """
        # Group by base table number
        table_groups = {}

        for raw_table in raw_tables:
            # Extract base table number (remove "(cont.)")
            base_caption = re.sub(r'\s*\(cont\.\s*\)', '', raw_table.caption, flags=re.IGNORECASE).strip()

            if base_caption not in table_groups:
                table_groups[base_caption] = []

            table_groups[base_caption].append(raw_table)

        # Merge each group
        merged = []
        for base_caption, tables in table_groups.items():
            if len(tables) == 1:
                merged.append(tables[0])
            else:
                # Sort by page number
                tables.sort(key=lambda t: t.page_num)

                # Merge multiple parts
                merged_rows = tables[0].rows.copy()
                header = merged_rows[0] if merged_rows else []  # Save header

                for continuation in tables[1:]:
                    # Skip header rows in continuations
                    continuation_rows = continuation.rows

                    if continuation_rows:
                        # Check if first row matches header
                        if continuation_rows[0] == header:
                            continuation_rows = continuation_rows[1:]

                        merged_rows.extend(continuation_rows)

                merged.append(RawTable(
                    caption=base_caption,
                    rows=merged_rows,
                    page_num=tables[0].page_num
                ))

        return merged
