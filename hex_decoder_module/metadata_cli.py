"""
Command-line interface for generating logcode metadata from ICD PDF.

This tool extracts comprehensive metadata for logcodes including all versions
and their field layouts (main tables + dependencies).
"""

import argparse
import sys
import os
from pathlib import Path

from .export.metadata_generator import MetadataGenerator
from .models.errors import HexDecoderError


def generate_single_logcode(args):
    """Generate metadata for a single logcode"""
    print(f"Generating metadata for logcode: {args.logcode}")
    print(f"Using ICD PDF: {args.pdf}")
    print()

    try:
        # Initialize generator
        generator = MetadataGenerator(args.pdf, enable_cache=not args.no_cache)

        # Generate metadata
        metadata = generator.generate_logcode_metadata(args.logcode)

        # Save to file
        generator.save_to_file(metadata, args.output, pretty=not args.compact)

        # Print summary
        print(f"\nSummary:")
        print(f"  Logcode: {metadata['logcode_id']} ({metadata['logcode_name']})")
        print(f"  Versions: {len(metadata['versions'])}")
        print(f"  Total tables: {len(metadata['all_tables'])}")

        # Show cache stats if verbose
        if args.verbose:
            stats = generator.get_cache_stats()
            print(f"\nCache stats:")
            print(f"  Enabled: {stats['cache_enabled']}")
            print(f"  Size: {stats['cache_size']} entries")

    except HexDecoderError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def generate_multiple_logcodes(args):
    """Generate metadata for multiple logcodes"""
    # Read logcode list
    if os.path.isfile(args.logcodes):
        print(f"Reading logcode list from: {args.logcodes}")
        with open(args.logcodes, 'r', encoding='utf-8') as f:
            logcode_ids = [line.strip() for line in f if line.strip()]
    else:
        # Treat as comma-separated list
        logcode_ids = [lc.strip() for lc in args.logcodes.split(',')]

    print(f"Processing {len(logcode_ids)} logcodes")
    print(f"Using ICD PDF: {args.pdf}")
    print()

    try:
        # Initialize generator
        generator = MetadataGenerator(args.pdf, enable_cache=not args.no_cache)

        # Generate metadata for all logcodes
        metadata = generator.generate_multi_logcode_metadata(
            logcode_ids,
            show_progress=args.verbose
        )

        # Save to file
        generator.save_to_file(metadata, args.output, pretty=not args.compact)

        # Print summary
        print(f"\nSummary:")
        print(f"  Total logcodes processed: {metadata['total_logcodes']}")
        print(f"  Failed: {metadata['failed_logcodes']}")

        if metadata.get('errors'):
            print(f"\nFailed logcodes:")
            for error_info in metadata['errors']:
                print(f"  - {error_info['logcode_id']}: {error_info['error']}")

        # Show cache stats if verbose
        if args.verbose:
            stats = generator.get_cache_stats()
            print(f"\nCache stats:")
            print(f"  Enabled: {stats['cache_enabled']}")
            print(f"  Size: {stats['cache_size']} entries")

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate logcode metadata from ICD PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate metadata for a single logcode
  python -m hex_decoder_module.metadata_cli single --logcode 0x1C07 --pdf icd.pdf -o metadata_1c07.json

  # Generate metadata for multiple logcodes (comma-separated)
  python -m hex_decoder_module.metadata_cli multi --logcodes "0x1C07,0x1C08,0x1C09" --pdf icd.pdf -o metadata.json

  # Generate metadata from file (one logcode per line)
  python -m hex_decoder_module.metadata_cli multi --logcodes logcodes.txt --pdf icd.pdf -o metadata.json

  # Compact output (no formatting)
  python -m hex_decoder_module.metadata_cli single --logcode 0x1C07 --pdf icd.pdf -o metadata.json --compact

  # Disable caching (lower memory usage)
  python -m hex_decoder_module.metadata_cli single --logcode 0x1C07 --pdf icd.pdf -o metadata.json --no-cache
        """
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    subparsers.required = True

    # Single logcode command
    single_parser = subparsers.add_parser('single', help='Generate metadata for a single logcode')
    single_parser.add_argument(
        '--logcode', '-l',
        required=True,
        help='Logcode hex ID (e.g., 0x1C07)'
    )
    single_parser.add_argument(
        '--pdf', '-p',
        required=True,
        help='Path to ICD PDF file'
    )
    single_parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file path'
    )
    single_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (lower memory, slower)'
    )
    single_parser.add_argument(
        '--compact',
        action='store_true',
        help='Generate compact JSON (no formatting)'
    )
    single_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    single_parser.set_defaults(func=generate_single_logcode)

    # Multiple logcodes command
    multi_parser = subparsers.add_parser('multi', help='Generate metadata for multiple logcodes')
    multi_parser.add_argument(
        '--logcodes', '-l',
        required=True,
        help='Comma-separated list of logcodes OR path to file (one per line)'
    )
    multi_parser.add_argument(
        '--pdf', '-p',
        required=True,
        help='Path to ICD PDF file'
    )
    multi_parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file path'
    )
    multi_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (lower memory, slower)'
    )
    multi_parser.add_argument(
        '--compact',
        action='store_true',
        help='Generate compact JSON (no formatting)'
    )
    multi_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    multi_parser.set_defaults(func=generate_multiple_logcodes)

    # Parse arguments
    args = parser.parse_args()

    # Validate PDF exists
    if not os.path.isfile(args.pdf):
        print(f"ERROR: PDF file not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
