"""
Main Application
CLI interface for the logcode parser system.
"""

import sys
import argparse
from pathlib import Path
from parser import LogcodeParser
from datastore import LogcodeDatastore
from query_engine import QueryEngine
from pdf_extractor import PDFExtractor


def parse_pdf_command(args):
    """Parse a PDF and store results in database"""
    pdf_path = args.pdf
    db_path = args.database

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1

    print(f"Parsing PDF: {pdf_path}")
    parser = LogcodeParser(pdf_path)

    print("Extracting logcode data...")
    logcodes = parser.parse_all_logcodes()
    print(f"Found {len(logcodes)} logcodes")

    # Extract revision history
    print("Extracting revision history...")
    extractor = PDFExtractor(pdf_path)
    revisions = extractor.extract_revision_history()
    print(f"Found {len(revisions)} revision entries")

    print(f"Storing in database: {db_path}")
    db = LogcodeDatastore(db_path)
    doc_id = db.add_document(pdf_path)

    # Store logcode data
    for logcode, data in parser.logcodes.items():
        db.store_logcode_data(data, doc_id)

    # Store revision history
    if revisions:
        db.store_revision_history(revisions, doc_id)
        print(f"Stored {len(revisions)} revision entries")

    if args.export_json:
        json_path = args.export_json
        print(f"Exporting to JSON: {json_path}")
        db.export_to_json(json_path)

    db.close()
    print("Done!")
    return 0


def query_command(args):
    """Query for a specific logcode and version"""
    db_path = args.database
    logcode = args.logcode
    version = args.version
    
    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        print("Run 'parse' command first to create the database.")
        return 1
    
    engine = QueryEngine(db_path)
    
    try:
        tables = engine.get_table(logcode, version)
        output = engine.format_output(tables)
        
        if args.output:
            # Write to file
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Output written to: {args.output}")
        else:
            # Print to console
            print(output)
        
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    finally:
        engine.close()
    
    return 0


def list_command(args):
    """List all available logcodes"""
    db_path = args.database
    
    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1
    
    engine = QueryEngine(db_path)
    logcodes = engine.list_all_logcodes()
    
    print(f"Found {len(logcodes)} logcodes:\n")
    print(f"{'Logcode':<12} {'Section':<10} {'Name'}")
    print("-" * 80)
    
    for lc in logcodes:
        print(f"{lc['logcode']:<12} {lc['section']:<10} {lc['name']}")
    
    engine.close()
    return 0


def search_command(args):
    """Search for logcodes"""
    db_path = args.database
    search_term = args.term
    
    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1
    
    engine = QueryEngine(db_path)
    results = engine.search_logcode(search_term)
    
    if not results:
        print(f"No logcodes found matching '{search_term}'")
    else:
        print(f"Found {len(results)} matching logcodes:\n")
        print(f"{'Logcode':<12} {'Section':<10} {'Name'}")
        print("-" * 80)
        
        for lc in results:
            print(f"{lc['logcode']:<12} {lc['section']:<10} {lc['name']}")
    
    engine.close()
    return 0


def versions_command(args):
    """List versions for a logcode"""
    db_path = args.database
    logcode = args.logcode

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    db = LogcodeDatastore(db_path)

    info = db.get_logcode_info(logcode)
    if not info:
        print(f"Error: Logcode {logcode} not found")
        return 1

    versions = db.get_versions(logcode)

    print(f"Logcode: {info['logcode']}")
    print(f"Name: {info['name']}")
    print(f"Section: {info['section']}")
    print(f"\nAvailable versions: {', '.join(versions)}")

    db.close()
    return 0


def revision_command(args):
    """Query revision by code (e.g., FK, FL)"""
    db_path = args.database
    revision_code = args.revision_code

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    db = LogcodeDatastore(db_path)

    result = db.get_revisions_by_code(revision_code)
    if not result:
        print(f"Error: Revision {revision_code} not found")
        db.close()
        return 1

    print(f"Revision: {result['revision']}")
    print(f"Date: {result['date']}")

    if result['updated_logcodes']:
        print(f"\nUpdated log codes ({len(result['updated_logcodes'])}):")
        for i, lc in enumerate(result['updated_logcodes'], 1):
            print(f"  {lc}", end='')
            if i % 5 == 0:  # New line every 5 codes
                print()
        if len(result['updated_logcodes']) % 5 != 0:
            print()  # Final newline if needed

    if result['new_logcodes']:
        print(f"\nNew log codes ({len(result['new_logcodes'])}):")
        for i, lc in enumerate(result['new_logcodes'], 1):
            print(f"  {lc}", end='')
            if i % 5 == 0:
                print()
        if len(result['new_logcodes']) % 5 != 0:
            print()

    db.close()
    return 0


def revision_date_command(args):
    """Query revisions by date (month and year)"""
    db_path = args.database
    month = args.month
    year = args.year

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    db = LogcodeDatastore(db_path)

    results = db.get_revisions_by_date(month, year)
    if not results:
        print(f"No revisions found for {month} {year}")
        db.close()
        return 1

    print(f"Revisions for {month} {year}:\n")

    for result in results:
        print(f"Revision: {result['revision']}")

        if result['updated_logcodes']:
            print(f"  Updated ({len(result['updated_logcodes'])}): {', '.join(result['updated_logcodes'][:5])}", end='')
            if len(result['updated_logcodes']) > 5:
                print(f" ... (+{len(result['updated_logcodes']) - 5} more)")
            else:
                print()

        if result['new_logcodes']:
            print(f"  New ({len(result['new_logcodes'])}): {', '.join(result['new_logcodes'][:5])}", end='')
            if len(result['new_logcodes']) > 5:
                print(f" ... (+{len(result['new_logcodes']) - 5} more)")
            else:
                print()
        print()

    db.close()
    return 0


def revision_logcode_command(args):
    """Find all revisions for a specific logcode"""
    db_path = args.database
    logcode = args.logcode

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    db = LogcodeDatastore(db_path)

    results = db.search_revisions_by_logcode(logcode)
    if not results:
        print(f"No revisions found for logcode {logcode}")
        db.close()
        return 1

    print(f"Revision history for {logcode}:\n")
    print(f"{'Revision':<12} {'Date':<20} {'Status'}")
    print("-" * 50)

    for rev in results:
        print(f"{rev['revision']:<12} {rev['date']:<20} {rev['status']}")

    db.close()
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NR5G Log Packet Parser - Extract and query logcode tables from technical PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse a PDF and create database
  python app.py parse input.pdf

  # Parse and export to JSON
  python app.py parse input.pdf --export-json output.json

  # Query a specific logcode and version
  python app.py query 0x1C07 2

  # Save query output to file
  python app.py query 0x1C07 2 --output table.txt

  # List all logcodes
  python app.py list

  # Search for logcodes
  python app.py search TxAGC

  # Show versions for a logcode
  python app.py versions 0x1C07

  # Query revision by code
  python app.py revision FL

  # Query revisions by date
  python app.py revision-date February 2025

  # Find revisions for a logcode
  python app.py revision-logcode 0x1C07
        """
    )

    # Global arguments
    parser.add_argument('--database', '-d',
                       default='../data/parsed_logcodes.db',
                       help='Path to SQLite database (default: ../data/parsed_logcodes.db)')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse PDF and create database')
    parse_parser.add_argument('pdf', help='Path to PDF file')
    parse_parser.add_argument('--export-json', '-j', help='Export to JSON file')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query logcode and version')
    query_parser.add_argument('logcode', help='Logcode (e.g., 0x1C07)')
    query_parser.add_argument('version', help='Version number (e.g., 2)')
    query_parser.add_argument('--output', '-o', help='Output file (default: print to console)')

    # List command
    list_parser = subparsers.add_parser('list', help='List all logcodes')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search for logcodes')
    search_parser.add_argument('term', help='Search term (logcode or name)')

    # Versions command
    versions_parser = subparsers.add_parser('versions', help='Show versions for a logcode')
    versions_parser.add_argument('logcode', help='Logcode (e.g., 0x1C07)')

    # Revision command (by code)
    revision_parser = subparsers.add_parser('revision', help='Query revision by code (e.g., FK, FL)')
    revision_parser.add_argument('revision_code', help='Revision code (e.g., FL, FK)')

    # Revision date command
    revision_date_parser = subparsers.add_parser('revision-date', help='Query revisions by date')
    revision_date_parser.add_argument('month', help='Month name (e.g., February, March)')
    revision_date_parser.add_argument('year', help='Year (e.g., 2025, 2024)')

    # Revision logcode command
    revision_logcode_parser = subparsers.add_parser('revision-logcode', help='Find revisions for a logcode')
    revision_logcode_parser.add_argument('logcode', help='Logcode (e.g., 0x1C07)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to appropriate command
    commands = {
        'parse': parse_pdf_command,
        'query': query_command,
        'list': list_command,
        'search': search_command,
        'versions': versions_command,
        'revision': revision_command,
        'revision-date': revision_date_command,
        'revision-logcode': revision_logcode_command
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
