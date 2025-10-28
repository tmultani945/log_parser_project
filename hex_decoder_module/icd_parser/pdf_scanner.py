"""
Scans PDF to find the section containing a specific logcode using Table of Contents.
"""

import re
import pdfplumber
from typing import Optional, Dict, Tuple
from ..models.icd import LogcodeSectionInfo
from ..models.errors import SectionNotFoundError, PDFScanError


class PDFScanner:
    """Scans PDF to locate specific logcode sections using ToC"""

    # Pattern for ToC entries: "4.3 Name (0xB823) ......... 45"
    TOC_PATTERN = re.compile(
        r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)[\s.]*(\d+)',
        re.MULTILINE
    )

    # Pattern for section headers in content
    SECTION_PATTERN = re.compile(
        r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)',
        re.MULTILINE
    )

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._toc_cache: Optional[Dict[str, Tuple[int, str, str]]] = None

    def find_section(self, logcode_id: str) -> LogcodeSectionInfo:
        """
        Find the section containing the specified logcode using ToC.

        Args:
            logcode_id: Logcode in hex format (e.g., "0xB823")

        Returns:
            LogcodeSectionInfo with section location

        Raises:
            SectionNotFoundError: If logcode not found in PDF
            PDFScanError: If PDF cannot be read
        """
        logcode_upper = logcode_id.upper()

        try:
            # Build or retrieve ToC mapping
            toc_map = self._get_toc_mapping()

            # Look up logcode in ToC
            if logcode_upper not in toc_map:
                raise SectionNotFoundError(
                    f"Logcode {logcode_id} not found in PDF Table of Contents. "
                    f"Found {len(toc_map)} logcodes in Section 4."
                )

            page_num, section_num, title = toc_map[logcode_upper]

            # Determine section boundaries
            with pdfplumber.open(self.pdf_path) as pdf:
                # Find next section to determine end page
                all_logcodes = sorted(toc_map.items(), key=lambda x: x[1][0])

                # Find index of current logcode
                current_idx = None
                for idx, (lc, _) in enumerate(all_logcodes):
                    if lc == logcode_upper:
                        current_idx = idx
                        break

                # End page is page before next section, or last page
                if current_idx is not None and current_idx + 1 < len(all_logcodes):
                    end_page = all_logcodes[current_idx + 1][1][0] - 1
                else:
                    end_page = len(pdf.pages) - 1

                return LogcodeSectionInfo(
                    logcode_id=logcode_upper,
                    section_number=section_num,
                    section_title=title,
                    start_page=page_num,
                    end_page=end_page
                )

        except FileNotFoundError:
            raise PDFScanError(f"PDF file not found: {self.pdf_path}")
        except Exception as e:
            if isinstance(e, SectionNotFoundError):
                raise
            raise PDFScanError(f"Error scanning PDF: {str(e)}")

    def _get_toc_mapping(self) -> Dict[str, Tuple[int, str, str]]:
        """
        Get or build Table of Contents mapping.

        Returns:
            Dict mapping logcode_id → (page_num, section_num, title)

        Raises:
            PDFScanError: If ToC cannot be parsed
        """
        if self._toc_cache is not None:
            return self._toc_cache

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                toc_map = {}

                # Strategy 1: Parse ToC from first ~20 pages
                toc_map = self._parse_toc_section(pdf)

                # Strategy 2: If ToC parsing failed, fall back to full scan
                if not toc_map:
                    print("Warning: ToC not found or empty, falling back to full PDF scan...")
                    toc_map = self._full_pdf_scan(pdf)

                self._toc_cache = toc_map
                return toc_map

        except Exception as e:
            raise PDFScanError(f"Error building ToC mapping: {str(e)}")

    def _parse_toc_section(self, pdf) -> Dict[str, Tuple[int, str, str]]:
        """
        Parse Table of Contents section from PDF.

        Expected format:
            4.1 LogcodeName (0x1C07) ..................... 45
            4.2 AnotherLogcode (0xB823) .................. 67

        Returns:
            Dict mapping logcode_id → (page_num, section_num, title)
        """
        toc_map = {}

        # Find the Contents section and scan ALL pages in it
        toc_start = None
        toc_end = None

        # First, find where "Contents" section starts and ends
        for page_idx in range(min(50, len(pdf.pages))):
            page = pdf.pages[page_idx]
            text = page.extract_text()

            if not text:
                continue

            text_lower = text.lower()

            # Look for "Contents" or "Table of Contents" heading
            if toc_start is None:
                if 'contents' in text_lower or 'table of contents' in text_lower:
                    toc_start = page_idx
                    continue

            # If we found start, look for end (next major section like "Introduction", "Chapter 1", etc)
            if toc_start is not None and toc_end is None:
                # Contents typically ends when we see actual content (not ToC entries)
                # Look for major section headers like "1 Introduction", "2 Overview", etc.
                if page_idx > toc_start + 2:  # Give at least 3 pages for ToC
                    # Check for chapter/section headers that indicate content has started
                    if re.search(r'^\s*\d+\s+[A-Z][a-z]+', text, re.MULTILINE):
                        # Make sure it's not just a ToC entry by checking if there's substantial text
                        if len(text) > 1000 and not re.search(r'\.{3,}', text):  # No dots means not ToC
                            toc_end = page_idx
                            break

        # If we didn't find explicit end, scan up to page 100 or end of PDF
        if toc_start is None:
            toc_start = 0
        if toc_end is None:
            toc_end = min(100, len(pdf.pages))

        print(f"Scanning Contents section from page {toc_start} to {toc_end}...")

        # Now scan all pages in the Contents section
        for page_idx in range(toc_start, toc_end):
            if page_idx >= len(pdf.pages):
                break

            page = pdf.pages[page_idx]
            text = page.extract_text()

            if not text:
                continue

            # Look for ToC entries
            for match in self.TOC_PATTERN.finditer(text):
                section_num = match.group(1)
                title = match.group(2).strip()
                logcode = match.group(3).upper()
                page_num = int(match.group(4))

                # Store all logcodes (not just Section 4)
                # PDF page numbers in ToC are 1-indexed, convert to 0-indexed
                toc_map[logcode] = (page_num - 1, section_num, title)

        return toc_map

    def _full_pdf_scan(self, pdf) -> Dict[str, Tuple[int, str, str]]:
        """
        Fallback: Full PDF scan to find all logcode sections.

        This is slower but works if ToC parsing fails.

        Returns:
            Dict mapping logcode_id → (page_num, section_num, title)
        """
        toc_map = {}

        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            # Find section headers
            for match in self.SECTION_PATTERN.finditer(text):
                section_num = match.group(1)
                title = match.group(2).strip()
                logcode = match.group(3).upper()

                # Store all logcodes (all sections)
                # Only store first occurrence (section start)
                if logcode not in toc_map:
                    toc_map[logcode] = (page_num, section_num, title)

        return toc_map

    def list_all_logcodes(self) -> list:
        """
        List all logcodes found in Section 4 of the PDF.

        Returns:
            List of tuples: (logcode_id, section_num, title, page_num)

        Raises:
            PDFScanError: If PDF cannot be read
        """
        try:
            toc_map = self._get_toc_mapping()

            # Convert to list format
            logcodes = [
                (logcode, section_num, title, page_num)
                for logcode, (page_num, section_num, title) in toc_map.items()
            ]

            # Sort by page number
            logcodes.sort(key=lambda x: x[3])

            return logcodes

        except Exception as e:
            raise PDFScanError(f"Error listing logcodes: {str(e)}")

    def clear_cache(self):
        """Clear the ToC cache"""
        self._toc_cache = None
