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
    
    print(f"Storing in database: {db_path}")
    db = LogcodeDatastore(db_path)
    db.import_from_parser(parser, pdf_path)
    
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
        """
    )
    
    # Global arguments
    parser.add_argument('--database', '-d', 
                       default='data/parsed_logcodes.db',
                       help='Path to SQLite database (default: data/parsed_logcodes.db)')
    
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
        'versions': versions_command
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
