"""
Utility script to extract version information from decoded JSON files.
"""

import json
import sys
import argparse


def get_version_from_json(json_file):
    """Extract version information from decoded JSON file."""
    with open(json_file, 'r') as f:
        data = json.load(f)

    logcode_id_hex = data['logcode']['id_hex']
    logcode_id_decimal = data['logcode']['id_decimal']
    logcode_name = data['logcode']['name']

    version_hex = data['version']['raw']
    version_decimal = int(version_hex, 16)
    resolved_layout = data['version']['resolved_layout']

    return {
        'logcode_id_hex': logcode_id_hex,
        'logcode_id_decimal': logcode_id_decimal,
        'logcode_name': logcode_name,
        'version_hex': version_hex,
        'version_decimal': version_decimal,
        'resolved_layout': resolved_layout
    }


def list_available_versions(logcode_id, pdf_path):
    """List all available versions for a logcode from the PDF."""
    import sys
    import os

    # Add parent directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    from hex_decoder_module.icd_parser.icd_query import ICDQueryEngine

    engine = ICDQueryEngine(pdf_path, enable_cache=True)
    versions = engine.list_available_versions(logcode_id)

    # Get metadata to show version->table mapping
    metadata = engine.get_logcode_metadata(logcode_id)

    return versions, metadata.version_map


def main():
    parser = argparse.ArgumentParser(
        description='Extract version information from decoded JSON or query available versions from PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get version from decoded JSON file
  python get_version.py --json decoded_output.json

  # List all available versions for a logcode
  python get_version.py --logcode 0xB823 --pdf path/to/icd.pdf

  # Both: show current version and list all available
  python get_version.py --json decoded_output.json --pdf path/to/icd.pdf
        """
    )

    parser.add_argument('--json', '-j', help='Path to decoded JSON file')
    parser.add_argument('--logcode', '-l', help='Logcode ID (e.g., 0xB823)')
    parser.add_argument('--pdf', '-p', help='Path to ICD PDF file')

    args = parser.parse_args()

    if not args.json and not (args.logcode and args.pdf):
        parser.error("Either --json or both --logcode and --pdf must be provided")

    # Extract version from JSON
    if args.json:
        print("=== VERSION FROM DECODED JSON ===")
        print()

        info = get_version_from_json(args.json)

        print(f"Logcode ID:          {info['logcode_id_hex']} ({info['logcode_id_decimal']})")
        print(f"Logcode Name:        {info['logcode_name']}")
        print()
        print(f"Version (Hex):       {info['version_hex']}")
        print(f"Version (Decimal):   {info['version_decimal']}")
        print(f"Resolved Table:      {info['resolved_layout']}")
        print()

    # List available versions from PDF
    if args.logcode and args.pdf:
        # Normalize logcode format - remove any existing 0x/0X prefix first
        logcode_id = args.logcode.upper().replace('0X', '')
        logcode_id = f'0x{logcode_id}'

        if args.json:
            print()

        print("=== AVAILABLE VERSIONS FROM PDF ===")
        print()

        versions, version_map = list_available_versions(logcode_id, args.pdf)

        print(f"Logcode: {logcode_id}")
        print(f"Total Versions: {len(versions)}")
        print()

        print("Version Mappings:")
        for version in sorted(versions):
            table = version_map.get(version, 'Unknown')
            version_hex = f"0x{version:08X}" if version >= 65536 else str(version)
            print(f"  Version {version_hex:12s} (decimal {version:10d}) -> Table {table}")


if __name__ == '__main__':
    main()
