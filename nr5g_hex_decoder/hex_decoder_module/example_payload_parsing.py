"""
Example: Parsing Payloads Using Metadata JSON

This script demonstrates how to use pre-generated metadata JSON files
to parse binary payloads without accessing the ICD PDF.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser, parse_payload_from_metadata


def example_1_parse_single_payload():
    """Example 1: Parse a single payload using metadata"""
    print("=" * 100)
    print("EXAMPLE 1: Parse Single Payload Using Metadata")
    print("=" * 100)

    # Sample payload for logcode 0x1C07, version 2
    # This is a synthetic example - replace with real payload data
    sample_payload = (
        "02000000"  # Version = 2 (32 bits / 4 bytes)
        "64001001"  # Sys FN (10 bits), Sub FN (6 bits), Slot (8 bits), SCS (8 bits)
        "01050000"  # Sym Index (4 bits), Channel Type (4 bits), Reserved, Tx Chain Mask, etc.
        "0000"      # More fields...
        "0000"
        "0000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
    )

    print(f"\n1. Sample Payload:")
    print(f"   Hex: {sample_payload}")
    print(f"   Length: {len(sample_payload) // 2} bytes")

    print(f"\n2. Loading metadata from: metadata_0x1C07.json")

    # Check if metadata file exists
    metadata_file = "metadata_0x1C07.json"
    if not Path(metadata_file).exists():
        print(f"\n   [WARNING] Metadata file not found: {metadata_file}")
        print(f"   Please generate it first using:")
        print(f"   python -m hex_decoder_module.metadata_cli single --logcode 0x1C07 --pdf <pdf_path> -o metadata_0x1C07.json")
        return

    try:
        # Parse payload
        print(f"\n3. Parsing payload...")
        parser = MetadataPayloadParser(metadata_file)
        parsed_data = parser.parse_payload(sample_payload)

        # Display results
        print(f"\n4. Parse Results:")
        print(f"   Logcode: {parsed_data['logcode_id']} ({parsed_data['logcode_name']})")
        print(f"   Version: {parsed_data['version']['value']} (Table {parsed_data['version']['table']})")
        print(f"   Fields Parsed: {parsed_data['metadata']['fields_parsed']}")

        print(f"\n5. Sample Field Values:")
        sample_fields = ['Version', 'Sys FN', 'Sub FN', 'Slot', 'SCS', 'Channel Type']
        for field_name in sample_fields:
            if field_name in parsed_data['fields']:
                field_data = parsed_data['fields'][field_name]
                enum_str = f" ({field_data['enum']})" if 'enum' in field_data else ''
                print(f"   {field_name:20s}: {field_data['raw']:8d} (0x{field_data['raw']:04X}){enum_str}")

        # Save to file
        output_file = "parsed_payload_example.json"
        parser.save_parsed_output(parsed_data, output_file)
        print(f"\n6. Full parsed data saved to: {output_file}")

        print(f"\n[SUCCESS] Payload parsed successfully!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


def example_2_parse_from_file():
    """Example 2: Parse payload from hex file"""
    print("\n\n")
    print("=" * 100)
    print("EXAMPLE 2: Parse Payload from Hex File")
    print("=" * 100)

    # Create a sample hex file
    sample_hex_file = "sample_payload.hex"
    sample_payload = (
        "02000000"
        "64001001"
        "01050000"
        "0000"
        "0000"
        "0000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
        "00000000"
    )

    print(f"\n1. Creating sample hex file: {sample_hex_file}")
    with open(sample_hex_file, 'w') as f:
        f.write(sample_payload)

    print(f"\n2. Reading payload from file...")
    with open(sample_hex_file, 'r') as f:
        payload_hex = f.read().strip()

    metadata_file = "metadata_0x1C07.json"
    if not Path(metadata_file).exists():
        print(f"\n   [WARNING] Metadata file not found: {metadata_file}")
        return

    print(f"\n3. Parsing...")
    try:
        result = parse_payload_from_metadata(
            metadata_file,
            payload_hex,
            "parsed_from_file.json",
            verbose=True
        )
        print(f"\n[SUCCESS] Parsed and saved to: parsed_from_file.json")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def example_3_parse_multiple_payloads():
    """Example 3: Parse multiple payloads in batch"""
    print("\n\n")
    print("=" * 100)
    print("EXAMPLE 3: Parse Multiple Payloads in Batch")
    print("=" * 100)

    # Sample payloads with different versions
    payloads = [
        ("Payload 1 (Version 2)", "02000000" + "64001001" * 10),
        ("Payload 2 (Version 3)", "03000000" + "64001001" * 10),
        ("Payload 3 (Version 5)", "05000000" + "64001001" * 10),
    ]

    metadata_file = "metadata_0x1C07.json"
    if not Path(metadata_file).exists():
        print(f"\n[WARNING] Metadata file not found: {metadata_file}")
        return

    print(f"\n1. Loading parser...")
    parser = MetadataPayloadParser(metadata_file)

    print(f"\n2. Processing {len(payloads)} payloads...")
    results = []

    for name, payload_hex in payloads:
        try:
            print(f"\n   Processing: {name}")
            parsed = parser.parse_payload(payload_hex)
            results.append({
                'name': name,
                'logcode': parsed['logcode_id'],
                'version': parsed['version']['value'],
                'fields_count': parsed['metadata']['fields_parsed'],
                'status': 'SUCCESS'
            })
            print(f"     Version: {parsed['version']['value']}, Fields: {parsed['metadata']['fields_parsed']}")
        except Exception as e:
            results.append({
                'name': name,
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"     [FAILED] {e}")

    print(f"\n3. Summary:")
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    print(f"   Total: {len(results)}, Success: {success_count}, Failed: {len(results) - success_count}")


def show_workflow():
    """Show the complete workflow"""
    print("=" * 100)
    print("METADATA-BASED PAYLOAD PARSING WORKFLOW")
    print("=" * 100)
    print("""
STEP 1: Generate Metadata JSON (One-time setup)
------------------------------------------------
python -m hex_decoder_module.metadata_cli single \\
    --logcode 0x1C07 \\
    --pdf icd_document.pdf \\
    -o metadata_0x1C07.json

This creates a metadata JSON file containing:
  - All available versions
  - Complete field layouts for each version
  - Field offsets, types, lengths
  - Enum mappings


STEP 2: Parse Payloads Using Metadata (Fast, repeatable)
---------------------------------------------------------
from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser

# Initialize parser with metadata
parser = MetadataPayloadParser('metadata_0x1C07.json')

# Parse payload
payload_hex = "02000000640010010105000000000000..."
parsed_data = parser.parse_payload(payload_hex)

# Save results
parser.save_parsed_output(parsed_data, 'output.json')


BENEFITS:
---------
  - No PDF access needed after metadata generation
  - Fast parsing (no PDF scanning/table extraction)
  - Portable metadata files
  - Easy integration with other tools
  - Batch processing support


OUTPUT FORMAT:
--------------
{
  "logcode_id": "0X1C07",
  "logcode_name": "NR5G Sub6 TxAGC",
  "version": {
    "value": 2,
    "table": "4-4"
  },
  "fields": {
    "Version": {
      "raw": 2,
      "type": "Uint32",
      "value": 2
    },
    "SCS": {
      "raw": 1,
      "type": "Enumeration",
      "value": 1,
      "enum": "30"
    },
    ...
  }
}
    """)


def main():
    """Run all examples"""
    print("\n" + "=" * 100)
    print(" PAYLOAD PARSING EXAMPLES - Using Metadata JSON")
    print("=" * 100)

    # Show workflow
    show_workflow()

    # Ask user
    print("\n" + "-" * 100)
    response = input("\nDo you want to run the parsing examples? (y/n): ")

    if response.lower() == 'y':
        example_1_parse_single_payload()
        example_2_parse_from_file()
        example_3_parse_multiple_payloads()
    else:
        print("\nSkipped examples. You can run them anytime by executing this script.")

    print("\n" + "=" * 100)
    print("Examples complete!")
    print("=" * 100)


if __name__ == '__main__':
    main()
