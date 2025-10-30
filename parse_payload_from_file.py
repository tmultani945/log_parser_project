"""
Parse Payload from Hex File

Simple script to parse payload using pre-generated metadata.
Reads hex input file in the same format as hex_decoder_module.cli
"""

import sys
import re
import argparse
import os

sys.path.insert(0, '.')
from hex_decoder_module.metadata_payload_parser import parse_payload_from_metadata


def read_hex_file(hex_file):
    """
    Read hex input file in format:

    Length:     176
    Header:     B0 00 88 B8 94 1A 8F DF 16 26 09 01
    Payload:     01 00 03 00 73 5D 74 01 C0 26 03 60
          77 5D 78 5D 79 5D 7A 5D 00 00 01 00
          ...

    Returns just the payload hex string (cleaned)
    """
    with open(hex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find Payload section
    payload_match = re.search(r'Payload:\s*([0-9A-Fa-f\s\n]+?)(?:\n\n|\Z)',
                             content, re.IGNORECASE | re.DOTALL)

    if not payload_match:
        raise ValueError("Could not find 'Payload:' section in input file")

    # Clean up hex string (remove all whitespace)
    payload_hex = re.sub(r'\s+', '', payload_match.group(1))

    return payload_hex


def main():
    parser = argparse.ArgumentParser(
        description="Parse payload from hex file using metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parse_payload_from_file.py -i payload.hex -m metadata_0xB888.json -o output.json
  python parse_payload_from_file.py -i payload.hex -m metadata_0xB888.json -o output.json -v

Input file format (payload.hex):
  Length:     176
  Header:     B0 00 88 B8 94 1A 8F DF 16 26 09 01
  Payload:     01 00 03 00 73 5D 74 01 C0 26 03 60
        77 5D 78 5D 79 5D 7A 5D 00 00 01 00
        E1 8D 64 00 52 0A 02 00 16 08 02 00
        ...

Note: Spacing in payload is automatically handled.
        """
    )

    parser.add_argument('-i', '--input', required=True,
                       help='Input hex file path')
    parser.add_argument('-m', '--metadata', required=True,
                       help='Metadata JSON file path')
    parser.add_argument('-o', '--output', required=True,
                       help='Output JSON file path')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Check files exist
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    if not os.path.exists(args.metadata):
        print(f"ERROR: Metadata file not found: {args.metadata}")
        sys.exit(1)

    # Read hex file
    if args.verbose:
        print(f"Reading hex input from: {args.input}")

    try:
        payload_hex = read_hex_file(args.input)
        if args.verbose:
            print(f"Payload size: {len(payload_hex) // 2} bytes")
    except Exception as e:
        print(f"ERROR: Failed to read hex file: {e}")
        sys.exit(1)

    # Parse payload
    if args.verbose:
        print(f"Using metadata: {args.metadata}")
        print(f"Parsing payload...")
        print()

    try:
        result = parse_payload_from_metadata(
            metadata_file=args.metadata,
            payload_hex=payload_hex,
            output_file=args.output,
            verbose=args.verbose
        )

        print()
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Output saved to: {args.output}")

        # Show record summary
        records = {}
        for field_name in result['fields'].keys():
            match = re.search(r'Record (\d+)', field_name)
            if match:
                rec_num = match.group(1)
                records[rec_num] = records.get(rec_num, 0) + 1

        if records:
            print(f"\nRecords decoded:")
            for rec_num in sorted(records.keys(), key=int):
                print(f"  Record {rec_num}: {records[rec_num]} fields")

        print("=" * 60)

    except Exception as e:
        print(f"ERROR: Failed to parse payload: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
