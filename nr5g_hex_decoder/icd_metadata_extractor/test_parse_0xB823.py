#!/usr/bin/env python3
"""
Test script for parsing 0xB823 payload

This script demonstrates parsing a specific 0xB823 log code payload
using the metadata and payload parser.
"""

import json
from pathlib import Path
from parse_payload import PayloadParser


def main():
    """Test payload parsing for 0xB823."""

    # Define paths
    script_dir = Path(__file__).parent
    metadata_file = script_dir / "data" / "output" / "metadata_0xB823_v196610.json"

    # The payload data from your log
    # Length: 61 bytes total
    # Header: 3D 00 23 B8 83 3E E3 04 62 DB 03 01 (12 bytes)
    # Payload: (49 bytes)
    header_hex = "3D 00 23 B8 83 3E E3 04 62 DB 03 01"
    payload_hex = """
        02 00 03 00 01 01 00 5B 00 2A 00 B9
        DD 40 18 30 01 E0 E5 09 00 4A DE 09
        00 64 00 64 00 2A 00 B9 DD 00 00 00
        00 37 01 03 E0 01 00 08 01 16 00 4D
        00
    """

    print("=" * 80)
    print("0xB823 Payload Parser Test")
    print("=" * 80)
    print(f"\nMetadata file: {metadata_file}")
    print(f"Metadata exists: {metadata_file.exists()}")

    if not metadata_file.exists():
        print(f"\nERROR: Metadata file not found!")
        print(f"Expected location: {metadata_file.absolute()}")
        return

    print(f"\nHeader ({len(header_hex.split())} bytes):")
    print(f"  {header_hex}")

    print(f"\nPayload ({len(payload_hex.split())} bytes):")
    print(f"  {payload_hex.strip()}")

    # Parse the payload
    try:
        parser = PayloadParser(str(metadata_file))
        parsed_data = parser.parse(payload_hex)

        # Display results
        print("\n")
        print(parser.format_output(parsed_data))

        # Save to JSON file
        output_file = script_dir / "data" / "output" / "parsed_payload_0xB823.json"
        parser.save_json(parsed_data, str(output_file))

        # Display some key fields
        print("\n" + "=" * 80)
        print("Key Field Summary:")
        print("=" * 80)

        fields = parsed_data['fields']

        key_fields = [
            'Physical Cell ID',
            'DL Frequency',
            'UL Frequency',
            'DL Bandwidth',
            'UL Bandwidth',
            'Selected PLMN MCC',
            'Selected PLMN MNC',
            'Freq Band Indicator'
        ]

        for field_name in key_fields:
            if field_name in fields:
                print(f"  {field_name}: {fields[field_name]['formatted']}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
