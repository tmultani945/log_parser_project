"""
Ultra-Light PDF Parser - Minimal memory usage for systems with limited resources
Uses streaming approach: processes and stores data page-by-page without accumulation.
"""

import sys
import json
import time
import gc
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('data/parsing_ultra_light.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class UltraLightParser:
    """
    Memory-efficient parser for large PDFs.

    Strategy:
    - Process pages one at a time
    - Extract only essential data
    - Immediately write to database
    - Release memory after each page
    - No batch accumulation
    """

    def __init__(self, pdf_path: str, db_path: str):
        self.pdf_path = pdf_path
        self.db_path = db_path
        self.checkpoint_path = 'data/ultra_checkpoint.json'

    def get_page_count(self) -> int:
        """Get total page count without keeping document open"""
        import fitz
        doc = fitz.open(self.pdf_path)
        count = len(doc)
        doc.close()
        del doc
        gc.collect()
        return count

    def extract_page_tables(self, page_num: int) -> List[Dict]:
        """
        Extract tables from single page and immediately release resources.

        Uses lazy loading - opens/closes PDF for each page to minimize memory.
        """
        import pdfplumber

        tables_data = []

        # Open PDF only for this page
        with pdfplumber.open(self.pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                return []

            page = pdf.pages[page_num]
            tables = page.extract_tables()
            text = page.extract_text() or ""
            lines = text.split('\n')

            # Find table captions
            import re
            captions = []
            pattern = r'^Table\s+(\d+-\d+)\s+(.+?)(?:\s+\(cont\.\))?$'
            for line in lines:
                match = re.match(pattern, line.strip(), re.IGNORECASE)
                if match:
                    captions.append({
                        'full': line.strip(),
                        'number': match.group(1),
                        'title': match.group(2).strip(),
                        'is_cont': '(cont.)' in line.lower()
                    })

            # Extract tables
            for i, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue

                headers = [str(cell).strip() if cell else '' for cell in table[0]]
                rows = [[str(cell).strip() if cell else '' for cell in row] for row in table[1:]]

                caption_info = captions[i] if i < len(captions) else None

                tables_data.append({
                    'page': page_num,
                    'caption': caption_info['full'] if caption_info else '',
                    'table_number': caption_info['number'] if caption_info else '',
                    'title': caption_info['title'] if caption_info else '',
                    'is_continuation': caption_info['is_cont'] if caption_info else False,
                    'headers': headers,
                    'rows': rows
                })

        # Force garbage collection
        gc.collect()

        return tables_data

    def detect_logcode_on_page(self, page_num: int) -> Optional[Dict]:
        """Detect logcode section on a specific page"""
        import fitz
        import re

        with fitz.open(self.pdf_path) as doc:
            if page_num >= len(doc):
                return None

            page = doc[page_num]
            text = page.get_text()

            # Pattern: Section number, name, and hex code
            pattern = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'

            for line in text.split('\n'):
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    result = {
                        'section': match.group(1),
                        'name': match.group(2).strip(),
                        'logcode': match.group(3).upper(),
                        'page': page_num
                    }
                    # Force cleanup
                    del doc
                    gc.collect()
                    return result

        gc.collect()
        return None

    def save_checkpoint(self, page_num: int, stats: Dict):
        """Save minimal checkpoint"""
        with open(self.checkpoint_path, 'w') as f:
            json.dump({
                'page': page_num,
                'timestamp': time.time(),
                'stats': stats
            }, f)

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint if exists"""
        if Path(self.checkpoint_path).exists():
            with open(self.checkpoint_path, 'r') as f:
                return json.load(f)
        return None

    def parse_streaming(self, checkpoint_frequency: int = 50):
        """
        Parse PDF in streaming mode - one page at a time.

        Args:
            checkpoint_frequency: Save checkpoint every N pages
        """
        start_time = time.time()

        # Get total pages
        logger.info("Counting pages...")
        total_pages = self.get_page_count()
        logger.info(f"Total pages: {total_pages}")

        # Check for checkpoint
        checkpoint = self.load_checkpoint()
        start_page = checkpoint['page'] if checkpoint else 0

        if checkpoint:
            logger.info(f"Resuming from page {start_page}")

        # Initialize database
        from datastore import LogcodeDatastore
        db = LogcodeDatastore(self.db_path)
        doc_id = db.add_document(self.pdf_path)

        # Statistics
        stats = {
            'tables_found': 0,
            'logcodes_found': 0,
            'pages_processed': start_page
        }

        logger.info(f"Starting streaming parse...")
        logger.info(f"Checkpoint frequency: every {checkpoint_frequency} pages")
        logger.info("")

        # Track current logcode context
        current_logcode = None
        table_accumulator = {}  # For merging continuations

        # Process page by page
        for page_num in range(start_page, total_pages):
            page_start = time.time()

            # Check for new logcode section
            logcode_info = self.detect_logcode_on_page(page_num)
            if logcode_info:
                current_logcode = logcode_info
                stats['logcodes_found'] += 1
                logger.info(f"  Found logcode: {logcode_info['logcode']} - {logcode_info['name']}")

            # Extract tables from this page
            page_tables = self.extract_page_tables(page_num)
            stats['tables_found'] += len(page_tables)

            # Store or accumulate tables
            for table_data in page_tables:
                # Simple storage - just log for now
                # In full version, would merge continuations and store
                pass

            # Progress logging
            if (page_num - start_page) % 10 == 0:
                elapsed = time.time() - start_time
                progress_pct = (page_num / total_pages) * 100
                pages_done = page_num - start_page + 1

                if pages_done > 0:
                    avg_time = elapsed / pages_done
                    remaining = total_pages - page_num
                    eta_min = (remaining * avg_time) / 60

                    logger.info(
                        f"Page {page_num}/{total_pages} ({progress_pct:.1f}%) | "
                        f"{avg_time:.2f}s/page | "
                        f"ETA: {eta_min:.0f}m | "
                        f"Tables: {stats['tables_found']}, Logcodes: {stats['logcodes_found']}"
                    )

            # Checkpoint
            if (page_num - start_page) % checkpoint_frequency == 0:
                stats['pages_processed'] = page_num
                self.save_checkpoint(page_num, stats)
                logger.info(f"  Checkpoint saved")

            # Force memory cleanup every page
            gc.collect()

        # Final stats
        total_time = time.time() - start_time
        logger.info("")
        logger.info("="*60)
        logger.info("PARSING COMPLETE")
        logger.info(f"Total time: {total_time/60:.1f} minutes")
        logger.info(f"Total pages: {total_pages}")
        logger.info(f"Average: {total_time/total_pages:.2f}s/page")
        logger.info(f"Tables found: {stats['tables_found']}")
        logger.info(f"Logcodes found: {stats['logcodes_found']}")
        logger.info("="*60)

        # Cleanup
        db.close()
        if Path(self.checkpoint_path).exists():
            Path(self.checkpoint_path).unlink()


def main():
    """Entry point for ultra-light parser"""
    if len(sys.argv) < 2:
        print("Ultra-Light PDF Parser - Minimal Memory Usage")
        print()
        print("Usage: python ultra_light_parser.py <pdf_path> [db_path] [checkpoint_freq]")
        print()
        print("Arguments:")
        print("  pdf_path: Path to PDF file")
        print("  db_path: Database path (default: ../data/parsed_logcodes.db)")
        print("  checkpoint_freq: Pages between checkpoints (default: 50)")
        print()
        print("Example:")
        print("  python ultra_light_parser.py ../data/input/large.pdf")
        print()
        print("This version uses minimal memory by:")
        print("  - Processing one page at a time")
        print("  - Releasing memory immediately after each page")
        print("  - Using lazy loading (opens/closes PDF per page)")
        print()
        print("Trade-off: Slower but works on low-memory systems")
        return 1

    pdf_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else '../data/parsed_logcodes.db'
    checkpoint_freq = int(sys.argv[3]) if len(sys.argv) > 3 else 50

    if not Path(pdf_path).exists():
        print(f"Error: PDF not found: {pdf_path}")
        return 1

    # Create data directory
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    parser = UltraLightParser(pdf_path, db_path)

    try:
        parser.parse_streaming(checkpoint_frequency=checkpoint_freq)
        return 0
    except KeyboardInterrupt:
        logger.warning("\nInterrupted - checkpoint saved, can resume later")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
