"""
Large PDF Parser - Optimized for parsing very large PDFs (5000+ pages)
Includes progress tracking, checkpointing, and batch processing.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging
from parser import LogcodeParser
from datastore import LogcodeDatastore
from pdf_extractor import PDFExtractor, ExtractedTable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/parsing_progress.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LargePDFParser:
    """Parser optimized for large PDFs with progress tracking and checkpointing"""

    def __init__(self, pdf_path: str, db_path: str, checkpoint_path: str = 'data/parse_checkpoint.json'):
        self.pdf_path = pdf_path
        self.db_path = db_path
        self.checkpoint_path = checkpoint_path
        self.extractor = PDFExtractor(pdf_path)
        self.total_pages = len(self.extractor.doc)

    def save_checkpoint(self, checkpoint_data: Dict):
        """Save checkpoint to disk for resume capability"""
        with open(self.checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"Checkpoint saved at page {checkpoint_data.get('last_page_processed', 0)}")

    def load_checkpoint(self) -> Optional[Dict]:
        """Load existing checkpoint if available"""
        checkpoint_file = Path(self.checkpoint_path)
        if checkpoint_file.exists():
            with open(self.checkpoint_path, 'r') as f:
                return json.load(f)
        return None

    def extract_tables_batch(self, start_page: int, end_page: int) -> List[Dict]:
        """
        Extract tables from a batch of pages.

        Args:
            start_page: Starting page number (inclusive)
            end_page: Ending page number (exclusive)

        Returns:
            List of table dictionaries
        """
        batch_tables = []
        batch_size = end_page - start_page

        logger.info(f"Processing batch: pages {start_page}-{end_page-1} ({batch_size} pages)")
        batch_start_time = time.time()

        for page_num in range(start_page, end_page):
            try:
                # Progress update every 10 pages within batch
                if (page_num - start_page) % 10 == 0:
                    progress_pct = (page_num / self.total_pages) * 100
                    elapsed = time.time() - batch_start_time
                    pages_done = page_num - start_page + 1
                    if pages_done > 0:
                        avg_time_per_page = elapsed / pages_done
                        remaining_pages = self.total_pages - page_num
                        eta_seconds = remaining_pages * avg_time_per_page
                        eta_minutes = eta_seconds / 60
                        logger.info(
                            f"Page {page_num}/{self.total_pages} ({progress_pct:.1f}%) | "
                            f"Avg: {avg_time_per_page:.2f}s/page | "
                            f"ETA: {eta_minutes:.1f} min"
                        )

                page_tables = self.extractor.extract_tables_from_page(page_num)
                batch_tables.extend(page_tables)

            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
                continue

        batch_time = time.time() - batch_start_time
        logger.info(
            f"Batch complete: {batch_size} pages in {batch_time:.1f}s "
            f"({batch_time/batch_size:.2f}s/page), {len(batch_tables)} tables found"
        )

        return batch_tables

    def parse_with_progress(self, batch_size: int = 100, resume: bool = True):
        """
        Parse PDF with progress tracking and checkpointing.

        Args:
            batch_size: Number of pages to process before saving checkpoint
            resume: Whether to resume from last checkpoint
        """
        overall_start_time = time.time()

        # Check for existing checkpoint
        checkpoint = None
        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                logger.info(f"Found checkpoint - resuming from page {checkpoint['last_page_processed']}")

        # Initialize database
        db = LogcodeDatastore(self.db_path)
        doc_id = db.add_document(self.pdf_path)

        # Determine starting page
        start_page = checkpoint['last_page_processed'] if checkpoint else 0
        all_tables_dict = {}

        logger.info(f"Starting parse of {self.total_pages} pages (batch size: {batch_size})")
        logger.info(f"PDF: {self.pdf_path}")
        logger.info(f"Database: {self.db_path}")

        # Step 1: Extract all tables in batches
        logger.info("\n=== PHASE 1: Table Extraction ===")
        current_page = start_page

        while current_page < self.total_pages:
            end_page = min(current_page + batch_size, self.total_pages)

            # Extract batch of tables
            batch_tables = self.extract_tables_batch(current_page, end_page)

            # Store tables temporarily
            for table_dict in batch_tables:
                page_num = table_dict['page']
                if page_num not in all_tables_dict:
                    all_tables_dict[page_num] = []
                all_tables_dict[page_num].append(table_dict)

            # Save checkpoint
            checkpoint_data = {
                'last_page_processed': end_page,
                'tables_extracted': sum(len(v) for v in all_tables_dict.values()),
                'timestamp': time.time()
            }
            self.save_checkpoint(checkpoint_data)

            current_page = end_page

        logger.info(f"Table extraction complete: {sum(len(v) for v in all_tables_dict.values())} tables found")

        # Step 2: Merge continuations
        logger.info("\n=== PHASE 2: Merging Table Continuations ===")
        all_tables_list = []
        for page_num in sorted(all_tables_dict.keys()):
            all_tables_list.extend(all_tables_dict[page_num])

        merged_tables = self.extractor.merge_continuations(all_tables_list)
        logger.info(f"Merged into {len(merged_tables)} logical tables")

        # Step 3: Parse logcode sections
        logger.info("\n=== PHASE 3: Parsing Logcode Sections ===")
        parser = LogcodeParser(self.pdf_path)
        parser.extractor = self.extractor  # Reuse already opened extractor

        # Detect all logcode sections
        logcode_sections = []
        for page_num in range(self.total_pages):
            if page_num % 100 == 0:
                logger.info(f"Scanning for logcode sections: page {page_num}/{self.total_pages}")
            page = self.extractor.doc[page_num]
            text = page.get_text()
            sections_on_page = parser.detect_logcode_sections(text)
            for section_info in sections_on_page:
                logcode_sections.append({
                    'logcode': section_info['logcode'],
                    'name': section_info['name'],
                    'section': section_info['section'],
                    'page': page_num
                })

        logger.info(f"Found {len(logcode_sections)} logcode sections")

        # Step 4: Group tables by logcode and store
        logger.info("\n=== PHASE 4: Grouping Tables and Storing ===")

        # Build table lookup
        tables_dict = {table.metadata.table_number: table for table in merged_tables}

        # Group tables by logcode (reuse parser logic)
        parser.logcodes = {}

        # Track which tables have been used by previous sections
        used_tables = set()

        # Assign first table to each logcode section
        for i, section in enumerate(logcode_sections):
            section['first_table'] = None
            section_major = section['section'].split('.')[0]

            # Try multiple matching strategies
            candidates = []

            for table in merged_tables:
                # Skip tables already used by previous sections
                if table.metadata.table_number in used_tables:
                    continue

                if table.metadata.page_start >= section['page']:
                    table_major = table.metadata.table_number.split('-')[0]

                    if table_major != section_major:
                        continue

                    # Collect candidate tables on same page OR next page with matching major section
                    # (Check next page to handle cases where logcode header is at bottom of page)
                    if table.metadata.page_start in [section['page'], section['page'] + 1]:
                        candidates.append(table)

            # Strategy 1: Try to match by name keywords (first 15 chars)
            for table in candidates:
                section_keywords = section['name'].replace(' ', '').replace('5G', '5g')
                table_keywords = table.metadata.title.replace('_', '')
                if section_keywords[:15].lower() in table_keywords.lower():
                    section['first_table'] = table.metadata.table_number
                    break

            # Strategy 2: If no match, try first 10 chars (more lenient)
            if not section['first_table']:
                for table in candidates:
                    section_keywords = section['name'].replace(' ', '').replace('5G', '5g')
                    table_keywords = table.metadata.title.replace('_', '')
                    if section_keywords[:10].lower() in table_keywords.lower():
                        section['first_table'] = table.metadata.table_number
                        break

            # Strategy 3: If still no match, take first candidate table on same page
            if not section['first_table'] and candidates:
                section['first_table'] = candidates[0].metadata.table_number

            # Mark all candidate tables as used to prevent them from being candidates for next section
            for table in candidates:
                used_tables.add(table.metadata.table_number)

        # Assign table ranges to logcodes
        logcodes = {}
        for i, section in enumerate(logcode_sections):
            logcode = section['logcode']
            logcodes[logcode] = {
                'name': section['name'],
                'section': section['section'],
                'tables': []
            }

            if section['first_table']:
                start_major, start_minor = map(int, section['first_table'].split('-'))
                if i + 1 < len(logcode_sections) and logcode_sections[i + 1]['first_table']:
                    end_major, end_minor = map(int, logcode_sections[i + 1]['first_table'].split('-'))
                    end_minor -= 1
                else:
                    end_major, end_minor = 999, 999

                for table in merged_tables:
                    table_major, table_minor = map(int, table.metadata.table_number.split('-'))
                    if table_major == start_major and start_minor <= table_minor <= end_minor:
                        logcodes[logcode]['tables'].append(table)

        logger.info(f"Storing {len(logcodes)} logcodes to database...")

        # Store each logcode
        for idx, (logcode, data) in enumerate(logcodes.items(), 1):
            if idx % 10 == 0:
                logger.info(f"Storing logcode {idx}/{len(logcodes)}: {logcode}")

            # Parse versions and dependencies
            tables_list = data['tables']
            sorted_tables = sorted(tables_list, key=lambda t: (
                int(t.metadata.table_number.split('-')[0]),
                int(t.metadata.table_number.split('-')[1])
            ))

            tables_dict_local = {}
            dependencies = {}
            for tbl in sorted_tables:
                tbl_num = tbl.metadata.table_number
                tables_dict_local[tbl_num] = tbl
                deps = parser.detect_table_dependencies(tbl)
                if deps:
                    dependencies[tbl_num] = deps

            version_map = {}
            versions = []
            if sorted_tables:
                # Scan all tables to find version tables (tables with 'Cond' column header)
                for tbl in sorted_tables:
                    if parser.is_version_table(tbl):
                        # Parse version information from this version table
                        tbl_versions = parser.parse_versions_from_table_rows(tbl, tables_dict_local)
                        version_map.update(tbl_versions)

                # Add version 'All' as default if no versions found or first table not mapped
                first_table = sorted_tables[0]
                if not version_map or first_table.metadata.table_number not in version_map.values():
                    version_map['All'] = first_table.metadata.table_number

                def version_sort_key(v):
                    try:
                        return (0, int(v), v)
                    except ValueError:
                        pass
                    if v.lower().startswith('0x'):
                        try:
                            return (1, int(v, 16), v)
                        except ValueError:
                            pass
                    return (2, 0, v)

                versions = sorted(version_map.keys(), key=version_sort_key)

            # Create LogcodeData
            from parser import LogcodeData
            logcode_data = LogcodeData(
                logcode=logcode,
                name=data['name'],
                section=data['section'],
                versions=versions,
                version_to_table=version_map,
                tables=tables_dict_local,
                dependencies=dependencies
            )

            # Store to database
            db.store_logcode_data(logcode_data, doc_id)

        # Step 5: Extract and store revision history
        logger.info("\n=== PHASE 5: Extracting Revision History ===")
        revisions = self.extractor.extract_revision_history()
        logger.info(f"Found {len(revisions)} revision entries")

        if revisions:
            db.store_revision_history(revisions, doc_id)
            logger.info(f"Stored {len(revisions)} revision entries")

        # Cleanup
        db.close()

        # Remove checkpoint file on success
        if Path(self.checkpoint_path).exists():
            Path(self.checkpoint_path).unlink()
            logger.info("Checkpoint file removed (parsing complete)")

        # Final summary
        total_time = time.time() - overall_start_time
        logger.info("\n" + "="*60)
        logger.info("PARSING COMPLETE")
        logger.info(f"Total time: {total_time/60:.1f} minutes ({total_time:.1f} seconds)")
        logger.info(f"Total pages: {self.total_pages}")
        logger.info(f"Total logcodes: {len(logcodes)}")
        logger.info(f"Total tables: {len(merged_tables)}")
        logger.info(f"Average time per page: {total_time/self.total_pages:.2f}s")
        logger.info("="*60)


def main():
    """Main entry point for large PDF parsing"""
    if len(sys.argv) < 2:
        print("Usage: python large_pdf_parser.py <pdf_path> [db_path] [batch_size]")
        print("Example: python large_pdf_parser.py ../data/input/large.pdf ../data/parsed.db 100")
        print()
        print("Options:")
        print("  pdf_path: Path to PDF file to parse")
        print("  db_path: Path to output database (default: ../data/parsed_logcodes.db)")
        print("  batch_size: Pages per batch (default: 100)")
        return 1

    pdf_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else '../data/parsed_logcodes.db'
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1

    # Create data directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    parser = LargePDFParser(pdf_path, db_path)

    try:
        parser.parse_with_progress(batch_size=batch_size, resume=True)
        return 0
    except KeyboardInterrupt:
        logger.warning("\nParsing interrupted by user - checkpoint saved, you can resume later")
        return 1
    except Exception as e:
        logger.error(f"Error during parsing: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
