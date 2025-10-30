"""
Simple CLI for parsing hex payloads using pre-generated metadata JSON files.
This avoids PDF parsing issues and uses corrected metadata.
"""

import argparse
import json
import sys
from pathlib import Path
from .metadata_payload_parser import MetadataPayloadParser


def calc_bler(crc_fail, crc_pass):
    """Calculate BLER percentage"""
    total = crc_pass + crc_fail
    return f'{(crc_fail / total) * 100:.2f}' if total > 0 else '0.00'


def calc_residual_bler(harq_fail, pdsch_decode):
    """Calculate Residual BLER percentage"""
    return f'{(harq_fail / pdsch_decode) * 100:.2f}' if pdsch_decode > 0 else '0.00'


def format_output(result):
    """Format parsed result to match expected structure"""
    output = {
        'LogRecordDescription': result['logcode_name'],
        'MAC Version': [{'MajorMinorVersion': '3.1'}],
        'Version': result['version']['value'],
        'NumRecords': str(result['fields']['Num Records']['raw']),
        'FlushGapCount': str(result['fields']['flush_gap_cnt']['raw']),
        'NumTotalSlots': str(result['fields']['Num Total Slots']['raw']),
        'NumCA': str(result['fields']['Num CA']['raw']),
        'CumulativeBitmask': str(result['fields']['Cumulative Bitmask']['raw']),
        'Records': []
    }

    # Determine number of records from parsed fields
    record_indices = set()
    for field_name in result['fields'].keys():
        if '(Record ' in field_name:
            # Extract record index
            idx = int(field_name.split('(Record ')[1].split(')')[0])
            record_indices.add(idx)

    # Extract each record
    for rec_idx in sorted(record_indices):
        rec = {
            'CarrierID': str(result['fields'][f'Carrier ID (Record {rec_idx})']['raw']),
            'Numerology': result['fields'][f'Numerology (Record {rec_idx})']['decoded'],
            'NumSlotsElapsed': str(result['fields'][f'Num Slots Elapsed (Record {rec_idx})']['raw']),
            'NumPDSCHDecode': str(result['fields'][f'Num PDSCH Decode (Record {rec_idx})']['raw']),
            'NumCRCPassTB': str(result['fields'][f'Num CRC Pass TB (Record {rec_idx})']['raw']),
            'NumCRCFailTB': str(result['fields'][f'Num CRC Fail TB (Record {rec_idx})']['raw']),
            'NumReTx': str(result['fields'][f'Num ReTx (Record {rec_idx})']['raw']),
            'ACKAsNACK': str(result['fields'][f'ACK As NACK (Record {rec_idx})']['raw']),
            'HARQFailure': str(result['fields'][f'HARQ Failure (Record {rec_idx})']['raw']),
            'CRCPassTBBytes': str(result['fields'][f'CRC Pass TB Bytes (Record {rec_idx})']['raw']),
            'CRCFailTBBytes': str(result['fields'][f'CRC Fail TB Bytes (Record {rec_idx})']['raw']),
            'TBBytes': str(result['fields'][f'TB Bytes (Record {rec_idx})']['raw']),
            'ReTxBytes': str(result['fields'][f'ReTx Bytes (Record {rec_idx})']['raw']),
            'BLER': calc_bler(
                result['fields'][f'Num CRC Fail TB (Record {rec_idx})']['raw'],
                result['fields'][f'Num CRC Pass TB (Record {rec_idx})']['raw']
            ),
            'ResidualBLER': calc_residual_bler(
                result['fields'][f'HARQ Failure (Record {rec_idx})']['raw'],
                result['fields'][f'Num PDSCH Decode (Record {rec_idx})']['raw']
            )
        }
        output['Records'].append(rec)

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Parse hex payload using metadata JSON file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse payload using corrected metadata
  python -m hex_decoder_module.parse_with_metadata \\
    --input hex_decoder_module/hex_input.txt \\
    --metadata metadata_0xB888_corrected.json \\
    --output hex_decoder_module/decoded_output.json

  # With verbose output
  python -m hex_decoder_module.parse_with_metadata \\
    --input hex_decoder_module/hex_input.txt \\
    --metadata metadata_0xB888_corrected.json \\
    --output hex_decoder_module/decoded_output.json \\
    --verbose
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to hex input file'
    )

    parser.add_argument(
        '--metadata', '-m',
        required=True,
        help='Path to metadata JSON file (e.g., metadata_0xB888_corrected.json)'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file path'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    try:
        # Validate input file exists
        if not Path(args.input).is_file():
            print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)

        # Validate metadata file exists
        if not Path(args.metadata).is_file():
            print(f"ERROR: Metadata file not found: {args.metadata}", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"Reading hex input from: {args.input}")
            print(f"Using metadata file: {args.metadata}")

        # Read hex input
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.strip().split('\n')
            payload_hex = ''
            for line in lines:
                if 'Payload:' in line:
                    payload_hex = line.split('Payload:')[1].strip()
                elif 'Header:' not in line and 'Length:' not in line and payload_hex:
                    payload_hex += ' ' + line.strip()

        if args.verbose:
            print(f"\nParsing payload...")

        # Parse using metadata
        parser_obj = MetadataPayloadParser(args.metadata)
        result = parser_obj.parse_payload(payload_hex)

        if args.verbose:
            print(f"Successfully parsed logcode {result['logcode_id']} ({result['logcode_name']})")
            print(f"Version: {result['version']['value_hex']} -> Table {result['version']['table']}")
            print(f"Total fields parsed: {result['metadata']['fields_parsed']}")

        # Format output
        formatted_output = format_output(result)

        if args.verbose:
            print(f"Records found: {len(formatted_output['Records'])}")

        # Save output
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(formatted_output, f, indent=2)

        print(f"\nOutput written to: {args.output}")

        if args.verbose:
            print(f"\nSummary:")
            for idx, rec in enumerate(formatted_output['Records']):
                print(f"  Record {idx} - Carrier {rec['CarrierID']}: BLER={rec['BLER']}%, ResidualBLER={rec['ResidualBLER']}%")

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
