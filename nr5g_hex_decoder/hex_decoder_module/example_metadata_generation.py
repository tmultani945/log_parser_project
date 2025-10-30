"""
Example script demonstrating metadata generation from ICD PDF.

This script shows how to:
1. Generate metadata for a single logcode
2. Generate metadata for multiple logcodes
3. Use the generated metadata for fast payload decoding
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hex_decoder_module.export.metadata_generator import MetadataGenerator


def example_single_logcode():
    """Example: Generate metadata for a single logcode"""
    print("=" * 80)
    print("EXAMPLE 1: Generate metadata for a single logcode")
    print("=" * 80)

    # Path to ICD PDF (adjust to your PDF location)
    pdf_path = "../data/icd_document.pdf"  # Update this path

    if not os.path.exists(pdf_path):
        print(f"[WARNING] PDF not found at: {pdf_path}")
        print("Please update pdf_path in this script to point to your ICD PDF file")
        return

    # Initialize generator
    print(f"\n1. Initializing metadata generator...")
    generator = MetadataGenerator(pdf_path, enable_cache=True)

    # Generate metadata for a specific logcode
    logcode_id = "0x1C07"  # Example logcode
    print(f"\n2. Generating metadata for {logcode_id}...")

    try:
        metadata = generator.generate_logcode_metadata(logcode_id)

        # Display results
        print(f"\n3. Metadata generated successfully!")
        print(f"   Logcode: {metadata['logcode_id']} ({metadata['logcode_name']})")
        print(f"   Section: {metadata['section']}")
        print(f"   Available versions: {metadata['available_versions']}")
        print(f"   Total tables: {len(metadata['all_tables'])}")

        # Show version details
        print(f"\n4. Version details:")
        for version, version_data in metadata['versions'].items():
            print(f"   Version {version}:")
            print(f"     - Table: {version_data['table_name']}")
            print(f"     - Fields: {version_data['total_fields']}")
            print(f"     - Dependencies: {version_data['direct_dependencies']}")

        # Save to file
        output_path = f"metadata_{logcode_id.replace('0x', '').lower()}.json"
        print(f"\n5. Saving to {output_path}...")
        generator.save_to_file(metadata, output_path, pretty=True)

        print(f"\n[SUCCESS] Metadata saved to: {output_path}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


def example_multiple_logcodes():
    """Example: Generate metadata for multiple logcodes"""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 2: Generate metadata for multiple logcodes")
    print("=" * 80)

    # Path to ICD PDF (adjust to your PDF location)
    pdf_path = "../data/icd_document.pdf"  # Update this path

    if not os.path.exists(pdf_path):
        print(f"[WARNING] PDF not found at: {pdf_path}")
        print("Please update pdf_path in this script to point to your ICD PDF file")
        return

    # List of logcodes to process
    logcode_ids = [
        "0x1C07",
        "0x1C08",
        "0x1C09",
        # Add more logcodes as needed
    ]

    print(f"\n1. Initializing metadata generator...")
    generator = MetadataGenerator(pdf_path, enable_cache=True)

    print(f"\n2. Generating metadata for {len(logcode_ids)} logcodes...")
    print(f"   {', '.join(logcode_ids)}")

    try:
        metadata = generator.generate_multi_logcode_metadata(
            logcode_ids,
            show_progress=True
        )

        # Display results
        print(f"\n3. Metadata generation complete!")
        print(f"   Total logcodes: {metadata['total_logcodes']}")
        print(f"   Failed: {metadata['failed_logcodes']}")

        if metadata.get('errors'):
            print(f"\n   Failed logcodes:")
            for error_info in metadata['errors']:
                print(f"     - {error_info['logcode_id']}: {error_info['error']}")

        # Save to file
        output_path = "metadata_multiple_logcodes.json"
        print(f"\n4. Saving to {output_path}...")
        generator.save_to_file(metadata, output_path, pretty=True)

        print(f"\n[SUCCESS] Metadata saved to: {output_path}")

        # Show cache stats
        stats = generator.get_cache_stats()
        print(f"\nCache stats:")
        print(f"  - Enabled: {stats['cache_enabled']}")
        print(f"  - Entries: {stats['cache_size']}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


def example_metadata_structure():
    """Example: Show the structure of generated metadata"""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 3: Understanding the metadata structure")
    print("=" * 80)

    print("""
The generated metadata JSON has the following structure:

Single Logcode:
{
  "logcode_id": "0x1C07",
  "logcode_name": "Nr5g_RrcServingCellInfo",
  "section": "4.1",
  "description": "",
  "version_offset": 0,
  "version_length": 32,
  "version_map": {
    "2": "4-4",
    "3": "4-5"
  },
  "available_versions": ["2", "3"],
  "versions": {
    "2": {
      "version_value": 2,
      "table_name": "4-4",
      "direct_dependencies": ["4-5", "4-6"],
      "fields": [
        {
          "name": "Physical Cell ID",
          "type_name": "Uint16",
          "offset_bytes": 0,
          "offset_bits": 0,
          "length_bits": 16,
          "description": "..."
        },
        ...
      ],
      "total_fields": 25
    }
  },
  "all_tables": {
    "4-4": {
      "fields": [...],
      "field_count": 10,
      "dependencies": ["4-5"]
    }
  }
}

Multiple Logcodes:
{
  "metadata_version": "1.0",
  "generated_timestamp": "2025-10-29T...",
  "total_logcodes": 3,
  "failed_logcodes": 0,
  "logcodes": {
    "0x1C07": { ... },
    "0x1C08": { ... },
    "0x1C09": { ... }
  }
}

Key Features:
- All versions are pre-computed with complete field layouts
- Dependencies are fully expanded and included
- Offsets are adjusted for nested tables
- Enum mappings are included where available
- Ready for fast payload decoding without PDF access
    """)


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print(" ICD METADATA GENERATOR - EXAMPLES")
    print("=" * 80)

    # Show structure first
    example_metadata_structure()

    # Ask user if they want to run generation examples
    print("\n" + "-" * 80)
    response = input("\nDo you want to run the generation examples? (y/n): ")

    if response.lower() == 'y':
        example_single_logcode()
        example_multiple_logcodes()
    else:
        print("\nSkipped generation examples. Update the PDF path in this script and run again.")

    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
