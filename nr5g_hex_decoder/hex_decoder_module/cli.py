"""
Command-line interface for hex decoder module.
"""

import argparse
import sys
import os
import time
from pathlib import Path

from .ingest.hex_parser import HexInputParser
from .icd_parser.icd_query import ICDQueryEngine
from .decoder.payload_decoder import PayloadDecoder
from .export.json_builder import JSONBuilder
from .export.file_writer import FileWriter
from .models.errors import HexDecoderError


def decode_hex_packet(hex_input: str, pdf_path: str, enable_cache: bool = True):
    """
    Main decode pipeline.

    Args:
        hex_input: Raw hex string (Length/Header/Payload format)
        pdf_path: Path to ICD PDF file
        enable_cache: Enable caching

    Returns:
        DecodedPacket ready for export

    Raises:
        HexDecoderError: On any decoding failure
    """
    start_time = time.time()

    # Step 1: Parse hex input
    hex_parser = HexInputParser()
    parsed_packet = hex_parser.parse(hex_input)

    # Step 2: Initialize ICD query engine
    icd_engine = ICDQueryEngine(pdf_path, enable_cache=enable_cache)

    # Step 3: Decode packet
    payload_decoder = PayloadDecoder(icd_engine)
    decoded_packet = payload_decoder.decode(parsed_packet)

    # Add timing metadata
    decode_time = (time.time() - start_time) * 1000  # Convert to ms
    decoded_packet.metadata['decode_time_ms'] = round(decode_time, 2)
    decoded_packet.metadata['cache_enabled'] = enable_cache
    decoded_packet.metadata['cache_size'] = icd_engine.get_cache_size()

    return decoded_packet


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Decode hex log packet using ICD PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Decode from hex string
  python -m hex_decoder_module.cli --input "Length: 61\\nHeader: 3D 00 23 B8..." --pdf icd.pdf -o output.json

  # Decode from file
  python -m hex_decoder_module.cli --input packet.hex --pdf icd.pdf -o output.json

  # Disable caching
  python -m hex_decoder_module.cli --input packet.hex --pdf icd.pdf -o output.json --no-cache

  # Compact output
  python -m hex_decoder_module.cli --input packet.hex --pdf icd.pdf -o output.json --compact
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to hex input file or hex string'
    )

    parser.add_argument(
        '--pdf', '-p',
        required=True,
        help='Path to ICD PDF file'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file path'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (slower but uses less memory)'
    )

    parser.add_argument(
        '--compact',
        action='store_true',
        help='Generate compact JSON output'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    try:
        # Read input
        if os.path.isfile(args.input):
            with open(args.input, 'r', encoding='utf-8') as f:
                hex_input = f.read()
            if args.verbose:
                print(f"Reading hex input from: {args.input}")
        else:
            hex_input = args.input
            if args.verbose:
                print("Using hex input from command line")

        # Validate PDF exists
        if not os.path.isfile(args.pdf):
            print(f"ERROR: PDF file not found: {args.pdf}", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"Using ICD PDF: {args.pdf}")
            print(f"Cache enabled: {not args.no_cache}")
            print("\nDecoding packet...")

        # Decode packet
        result = decode_hex_packet(
            hex_input,
            args.pdf,
            enable_cache=not args.no_cache
        )

        if args.verbose:
            print(f"Successfully decoded logcode {result.logcode_id_hex} ({result.logcode_name})")
            print(f"Version: {result.version_raw} -> Table {result.version_resolved}")
            print(f"Decoded {len(result.fields)} fields")
            print(f"Decode time: {result.metadata.get('decode_time_ms', 0):.2f} ms")

        # Build JSON
        json_builder = JSONBuilder()
        if args.compact:
            json_data = json_builder.build_compact(result)
        else:
            json_data = json_builder.build(result)

        # Write output
        file_writer = FileWriter()
        file_writer.write_pretty(json_data, args.output)

        print(f"\nOutput written to: {args.output}")

        if args.verbose:
            print(f"Cache size: {result.metadata.get('cache_size', 0)} entries")

    except HexDecoderError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
