"""
Parallel PDF Parser - Uses multiprocessing for efficient large PDF parsing (5000+ pages)
Includes progress tracking, checkpointing, timeout handling, and memory management.
"""

import sys
import json
import time
import gc
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from multiprocessing import Pool, cpu_count, Manager
from functools import partial
import logging
from parser import LogcodeParser, LogcodeData
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


def extract_tables_from_page_range(args: Tuple[str, int, int, int]) -> Dict:
    """
    Worker function to extract tables from a range of pages.
    Must be a top-level function for pickling by multiprocessing.

    Args:
        args: Tuple of (pdf_path, start_page, end_page, worker_id)

    Returns:
        Dict with 'tables' and 'metadata'
    """
    pdf_path, start_page, end_page, worker_id = args

    try:
        extractor = PDFExtractor(pdf_path)
        tables = []

        for page_num in range(start_page, end_page):
            try:
                page_tables = extractor.extract_tables_from_page(page_num)
                tables.extend(page_tables)
            except Exception as e:
                logger.error(f"Worker {worker_id}: Error on page {page_num}: {e}")
                continue

        # Close PDF to free memory
        extractor.close()

        return {
            'tables': tables,
            'start_page': start_page,
            'end_page': end_page,
            'worker_id': worker_id,
            'table_count': len(tables)
        }
    except Exception as e:
        logger.error(f"Worker {worker_id}: Fatal error in range {start_page}-{end_page}: {e}")
        return {
            'tables': [],
            'start_page': start_page,
            'end_page': end_page,
            'worker_id': worker_id,
            'table_count': 0,
            'error': str(e)
        }


def scan_pages_for_logcodes(args: Tuple[str, int, int, int]) -> List[Dict]:
    """
    Worker function to scan pages for logcode section headers.

    Args:
        args: Tuple of (pdf_path, start_page, end_page, worker_id)

    Returns:
        List of logcode section dictionaries
    """
    pdf_path, start_page, end_page, worker_id = args

    try:
        extractor = PDFExtractor(pdf_path)
        parser = LogcodeParser(pdf_path)
        parser.extractor = extractor

        sections = []
        for page_num in range(start_page, end_page):
            try:
                # Skip table of contents pages (first 20 pages) to avoid duplicate detection
                # Sections appear in both TOC and on actual content pages
                if page_num < 20:
                    continue

                page = extractor.doc[page_num]
                text = page.get_text()
                sections_on_page = parser.detect_logcode_sections(text)

                for section_info in sections_on_page:
                    sections.append({
                        'logcode': section_info['logcode'],
                        'name': section_info['name'],
                        'section': section_info['section'],
                        'page': page_num
                    })
            except Exception as e:
                logger.error(f"Worker {worker_id}: Error scanning page {page_num}: {e}")
                continue

        extractor.close()
        return sections

    except Exception as e:
        logger.error(f"Worker {worker_id}: Fatal error scanning {start_page}-{end_page}: {e}")
        return []


class ParallelPDFParser:
    """Parser optimized for large PDFs using parallel processing"""

    def __init__(self, pdf_path: str, db_path: str, checkpoint_path: str = 'data/parse_checkpoint.json',
                 num_workers: Optional[int] = None):
        self.pdf_path = pdf_path
        self.db_path = db_path
        self.checkpoint_path = checkpoint_path

        # Use CPU count - 1 to leave one core for system, minimum 2
        self.num_workers = num_workers or max(2, cpu_count() - 1)

        # Open PDF to get page count, then close
        extractor = PDFExtractor(pdf_path)
        self.total_pages = len(extractor.doc)
        extractor.close()

        logger.info(f"Initialized parallel parser with {self.num_workers} workers for {self.total_pages} pages")

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

    def parse_with_progress(self, batch_size: int = 100, resume: bool = True, timeout: int = 300):
        """
        Parse PDF with parallel processing, progress tracking, and checkpointing.

        Args:
            batch_size: Number of pages per batch (will be divided among workers)
            resume: Whether to resume from last checkpoint
            timeout: Timeout in seconds for each worker task (default 5 minutes)
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

        logger.info(f"Starting parallel parse of {self.total_pages} pages")
        logger.info(f"PDF: {self.pdf_path}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Workers: {self.num_workers}, Batch size: {batch_size}, Timeout: {timeout}s")

        # Step 1: Extract all tables in parallel
        logger.info("\n=== PHASE 1: Parallel Table Extraction ===")
        all_tables_list = []
        current_page = start_page

        with Pool(processes=self.num_workers) as pool:
            while current_page < self.total_pages:
                end_page = min(current_page + batch_size, self.total_pages)
                pages_in_batch = end_page - current_page

                # Divide batch among workers
                pages_per_worker = max(1, pages_in_batch // self.num_workers)
                worker_tasks = []

                for worker_id in range(self.num_workers):
                    worker_start = current_page + (worker_id * pages_per_worker)
                    worker_end = min(worker_start + pages_per_worker, end_page)

                    # Last worker takes any remaining pages
                    if worker_id == self.num_workers - 1:
                        worker_end = end_page

                    if worker_start < worker_end:
                        worker_tasks.append((self.pdf_path, worker_start, worker_end, worker_id))

                logger.info(f"Processing batch: pages {current_page}-{end_page-1} with {len(worker_tasks)} workers")
                batch_start_time = time.time()

                try:
                    # Process tasks in parallel with timeout
                    results = pool.map_async(extract_tables_from_page_range, worker_tasks).get(timeout=timeout)

                    # Collect results
                    batch_tables = []
                    for result in results:
                        if 'error' in result:
                            logger.warning(f"Worker {result['worker_id']} had errors in range {result['start_page']}-{result['end_page']}")
                        batch_tables.extend(result['tables'])
                        logger.info(f"Worker {result['worker_id']}: Found {result['table_count']} tables in pages {result['start_page']}-{result['end_page']}")

                    all_tables_list.extend(batch_tables)

                    batch_time = time.time() - batch_start_time
                    progress_pct = (end_page / self.total_pages) * 100
                    remaining_pages = self.total_pages - end_page
                    eta_seconds = (remaining_pages / pages_in_batch) * batch_time if pages_in_batch > 0 else 0

                    logger.info(
                        f"Batch complete: {pages_in_batch} pages in {batch_time:.1f}s "
                        f"({batch_time/pages_in_batch:.2f}s/page) | "
                        f"Progress: {progress_pct:.1f}% | "
                        f"ETA: {eta_seconds/60:.1f} min | "
                        f"Total tables: {len(all_tables_list)}"
                    )

                    # Save checkpoint
                    checkpoint_data = {
                        'last_page_processed': end_page,
                        'tables_extracted': len(all_tables_list),
                        'timestamp': time.time()
                    }
                    self.save_checkpoint(checkpoint_data)

                    # Force garbage collection
                    gc.collect()

                except Exception as e:
                    logger.error(f"Error processing batch {current_page}-{end_page}: {e}")
                    # Continue with next batch even if this one failed

                current_page = end_page

        logger.info(f"Table extraction complete: {len(all_tables_list)} tables found")

        # Step 2: Merge continuations
        logger.info("\n=== PHASE 2: Merging Table Continuations ===")
        extractor = PDFExtractor(self.pdf_path)
        merged_tables = extractor.merge_continuations(all_tables_list)
        extractor.close()
        logger.info(f"Merged into {len(merged_tables)} logical tables")

        # Free memory
        del all_tables_list
        gc.collect()

        # Step 3: Parse logcode sections in parallel
        logger.info("\n=== PHASE 3: Parallel Logcode Section Detection ===")

        # Divide pages among workers for scanning
        scan_batch_size = max(100, self.total_pages // (self.num_workers * 4))
        scan_tasks = []
        worker_id = 0

        for scan_start in range(0, self.total_pages, scan_batch_size):
            scan_end = min(scan_start + scan_batch_size, self.total_pages)
            scan_tasks.append((self.pdf_path, scan_start, scan_end, worker_id))
            worker_id += 1

        logger.info(f"Scanning for logcode sections with {len(scan_tasks)} parallel tasks")

        with Pool(processes=self.num_workers) as pool:
            try:
                section_results = pool.map_async(scan_pages_for_logcodes, scan_tasks).get(timeout=timeout)

                # Flatten results
                logcode_sections = []
                for sections in section_results:
                    logcode_sections.extend(sections)

            except Exception as e:
                logger.error(f"Error during parallel section scanning: {e}")
                # Fallback to sequential scanning
                logger.info("Falling back to sequential scanning...")
                logcode_sections = []
                extractor = PDFExtractor(self.pdf_path)
                parser = LogcodeParser(self.pdf_path)
                parser.extractor = extractor

                for page_num in range(self.total_pages):
                    if page_num % 100 == 0:
                        logger.info(f"Sequential scan: page {page_num}/{self.total_pages}")
                    page = extractor.doc[page_num]
                    text = page.get_text()
                    sections_on_page = parser.detect_logcode_sections(text)
                    for section_info in sections_on_page:
                        logcode_sections.append({
                            'logcode': section_info['logcode'],
                            'name': section_info['name'],
                            'section': section_info['section'],
                            'page': page_num
                        })
                extractor.close()

        logger.info(f"Found {len(logcode_sections)} logcode sections")

        # Step 4: Group tables by logcode and store
        logger.info("\n=== PHASE 4: Grouping Tables and Storing ===")

        # Build table lookup
        tables_dict = {table.metadata.table_number: table for table in merged_tables}

        # Create parser for utility functions
        parser = LogcodeParser(self.pdf_path)
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

                    # Look for tables on the same page or next page as the section header
                    if table.metadata.page_start in [section['page'], section['page'] + 1]:
                        candidates.append(table)

            # Strategy 1: Try to match by name keywords (first 15 chars)
            for table in candidates:
                section_keywords = section['name'].replace(' ', '').replace('5G', '5g')
                table_keywords = table.metadata.title.replace('_', '')
                if section_keywords[:15].lower() in table_keywords.lower():
                    section['first_table'] = table.metadata.table_number
                    break

            # Strategy 2: Fuzzy word matching - extract significant words and check overlap
            if not section['first_table']:
                def extract_words(text):
                    """Extract significant words (2+ chars, not common words)"""
                    import re
                    # Split camelCase: insert space before capital letters
                    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
                    # Replace separators with spaces
                    words = text.upper().replace('_', ' ').replace('-', ' ').split()
                    # Filter out very common words
                    skip = {'NR5G', 'NR', '5G', 'LOG', 'PACKET', 'V1', 'V2', 'V3', 'THE', 'AND', 'OR'}
                    return set(w for w in words if len(w) >= 2 and w not in skip)

                section_words = extract_words(section['name'])

                for table in candidates:
                    table_words = extract_words(table.metadata.title)
                    # Check for at least 2 common significant words
                    common = section_words & table_words
                    if len(common) >= 2:
                        section['first_table'] = table.metadata.table_number
                        logger.info(f"  Fuzzy match: '{section['name']}' → '{table.metadata.title}' (common: {common})")
                        break

            # Strategy 3: If no match, try first 10 chars (more lenient)
            if not section['first_table']:
                for table in candidates:
                    section_keywords = section['name'].replace(' ', '').replace('5G', '5g')
                    table_keywords = table.metadata.title.replace('_', '')
                    if section_keywords[:10].lower() in table_keywords.lower():
                        section['first_table'] = table.metadata.table_number
                        break

            # Strategy 4: If still no match, take first candidate table on same page
            if not section['first_table'] and candidates:
                section['first_table'] = candidates[0].metadata.table_number

            # Mark all candidate tables as used
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

            # Special handling for event sections (16, 17, 18, 19): direct 1-to-1 mapping
            # Section X.Y should map to Table X-Y only
            section_parts = section['section'].split('.')
            if len(section_parts) == 2 and section_parts[0] in ['16', '17', '18', '19']:
                section_major = section_parts[0]
                section_minor = section_parts[1]
                expected_table_num = f"{section_major}-{section_minor}"
                logger.info(f"Event section {section_major} logcode {logcode} (section {section['section']}): looking for table {expected_table_num}")

                for table in merged_tables:
                    if table.metadata.table_number == expected_table_num:
                        logcodes[logcode]['tables'].append(table)
                        logger.info(f"  -> Assigned table {expected_table_num} to {logcode}")
                        break
            # Standard range-based assignment for all other sections
            elif section['first_table']:
                start_major, start_minor = map(int, section['first_table'].split('-'))
                if i + 1 < len(logcode_sections) and logcode_sections[i + 1]['first_table']:
                    end_major, end_minor = map(int, logcode_sections[i + 1]['first_table'].split('-'))
                    # If next logcode is in a different major section, include all tables
                    # in current section (up to 999). Otherwise, go up to (but not including)
                    # the next logcode's first table.
                    if end_major != start_major:
                        end_major, end_minor = start_major, 999
                    else:
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
                # Scan all tables to find version tables
                for tbl in sorted_tables:
                    if parser.is_version_table(tbl):
                        tbl_versions = parser.parse_versions_from_table_rows(tbl, tables_dict_local)
                        version_map.update(tbl_versions)

                # Add version 'All' as default
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
        extractor = PDFExtractor(self.pdf_path)
        revisions = extractor.extract_revision_history()
        extractor.close()
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
        logger.info(f"Workers used: {self.num_workers}")
        logger.info("="*60)


def main():
    """Main entry point for parallel PDF parsing"""
    if len(sys.argv) < 2:
        print("Usage: python parallel_pdf_parser.py <pdf_path> [db_path] [batch_size] [num_workers] [timeout]")
        print("Example: python parallel_pdf_parser.py ../data/input/large.pdf ../data/parsed.db 200 4 300")
        print()
        print("Options:")
        print("  pdf_path: Path to PDF file to parse")
        print("  db_path: Path to output database (default: ../data/parsed_logcodes.db)")
        print("  batch_size: Pages per batch (default: 200)")
        print("  num_workers: Number of parallel workers (default: CPU count - 1)")
        print("  timeout: Timeout per task in seconds (default: 300)")
        return 1

    pdf_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else '../data/parsed_logcodes.db'
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    num_workers = int(sys.argv[4]) if len(sys.argv) > 4 else None
    timeout = int(sys.argv[5]) if len(sys.argv) > 5 else 300

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1

    # Create data directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    parser = ParallelPDFParser(pdf_path, db_path, num_workers=num_workers)

    try:
        parser.parse_with_progress(batch_size=batch_size, resume=True, timeout=timeout)
        return 0
    except KeyboardInterrupt:
        logger.warning("\nParsing interrupted by user - checkpoint saved, you can resume later")
        return 1
    except Exception as e:
        logger.error(f"Error during parsing: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
