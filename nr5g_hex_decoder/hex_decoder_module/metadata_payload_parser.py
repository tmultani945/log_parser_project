"""
Payload Parser using Metadata JSON (CORRECTED VERSION)

This module parses binary payloads using pre-generated metadata JSON files,
handling repeating structures correctly like hex_decoder_module.cli does.
"""

import json
import struct
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from copy import deepcopy


class MetadataPayloadParser:
    """Parse payloads using metadata JSON files with support for repeating structures"""

    def __init__(self, metadata_file: str):
        """
        Initialize parser with metadata JSON file.

        Args:
            metadata_file: Path to metadata JSON file
        """
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from JSON file"""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_payload(
        self,
        payload_hex: str,
        logcode_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse a hex payload using metadata.

        Args:
            payload_hex: Hex string of payload (e.g., "01020304...")
            logcode_id: Logcode ID (optional, inferred from metadata if single logcode)

        Returns:
            Dictionary with parsed fields organized by records
        """
        # Convert hex to bytes
        payload_bytes = bytes.fromhex(payload_hex.replace(' ', '').replace('\n', ''))

        # Get logcode metadata
        if 'logcodes' in self.metadata:
            # Multi-logcode metadata
            if not logcode_id:
                raise ValueError("logcode_id required for multi-logcode metadata files")
            logcode_metadata = self.metadata['logcodes'].get(logcode_id)
            if not logcode_metadata:
                raise ValueError(f"Logcode {logcode_id} not found in metadata")
        else:
            # Single logcode metadata
            logcode_metadata = self.metadata
            logcode_id = logcode_metadata['logcode_id']

        # Extract version from payload
        version_offset = logcode_metadata['version_offset']
        version_length = logcode_metadata['version_length']
        version_bytes = (version_length + 7) // 8

        if len(payload_bytes) < version_offset + version_bytes:
            raise ValueError(f"Payload too short: {len(payload_bytes)} bytes, need at least {version_offset + version_bytes}")

        # Read version value (assuming little-endian)
        version_value = int.from_bytes(
            payload_bytes[version_offset:version_offset + version_bytes],
            byteorder='little'
        )

        # Get version metadata
        version_str = str(version_value)
        if version_str not in logcode_metadata['versions']:
            available = ', '.join(logcode_metadata['available_versions'])
            raise ValueError(f"Version {version_value} not found. Available: {available}")

        version_metadata = logcode_metadata['versions'][version_str]

        # Parse fields (handling repeating structures)
        version_offset_bytes = version_bytes
        parsed_fields = {}
        already_decoded = []

        for field in version_metadata['fields']:
            # Check if this is a table reference (repeating structure)
            # Handle both dynamic count (-1) and fixed count (e.g., 8)
            if 'Table' in field.get('type_name', '') and field.get('count'):
                # This is a repeating structure - decode multiple records
                records = self._decode_repeating_structure(
                    payload_bytes,
                    field,
                    logcode_metadata,
                    version_offset_bytes,
                    already_decoded
                )
                # Add all record fields to parsed_fields
                for rec_field in records:
                    parsed_fields[rec_field['name']] = rec_field
            else:
                # Regular field - decode once
                try:
                    field_value = self._parse_field(payload_bytes, field, version_offset_bytes)
                    parsed_fields[field['name']] = field_value

                    # Keep track for record count detection
                    already_decoded.append({
                        'name': field['name'],
                        'raw_value': field_value.get('raw'),
                        'value': field_value.get('value')
                    })
                except Exception as e:
                    # Include error info but continue parsing
                    parsed_fields[field['name']] = {
                        'error': str(e),
                        'raw': None
                    }

        # Build result
        result = {
            'logcode_id': logcode_id,
            'logcode_name': logcode_metadata['logcode_name'],
            'version': {
                'value': version_value,
                'value_hex': f"0x{version_value:08X}",
                'table': version_metadata['table_name']
            },
            'fields': parsed_fields,
            'metadata': {
                'payload_size_bytes': len(payload_bytes),
                'fields_parsed': len(parsed_fields)
            }
        }

        return result

    def _decode_repeating_structure(
        self,
        payload: bytes,
        repeating_field_def: Dict[str, Any],
        logcode_metadata: Dict[str, Any],
        version_offset_bytes: int,
        already_decoded_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Decode a repeating structure (e.g., Records array).

        Args:
            payload: Raw payload bytes
            repeating_field_def: Field definition for the repeating structure
            logcode_metadata: Full logcode metadata
            version_offset_bytes: Version field size in bytes
            already_decoded_fields: Already decoded fields (to find count values)

        Returns:
            List of decoded fields organized as repeating records
        """
        # Step 1: Get the table reference (e.g., "Table 7-2805")
        table_ref_match = re.search(r'Table\s+(\d+-\d+)', repeating_field_def['type_name'], re.IGNORECASE)
        if not table_ref_match:
            return []

        ref_table_name = table_ref_match.group(1)

        # Get the referenced table from all_tables
        if ref_table_name not in logcode_metadata.get('all_tables', {}):
            return []

        ref_table_info = logcode_metadata['all_tables'][ref_table_name]
        ref_table_fields = ref_table_info['fields']

        if not ref_table_fields:
            return []

        # Step 2: Calculate the size of one record in bytes
        # Filter out fields with invalid offset (e.g., calculated fields like BLER with offset=0)
        # that appear after other fields
        valid_fields = []
        max_offset_seen = 0
        for f in ref_table_fields:
            field_offset = f['offset_bytes'] * 8 + f['offset_bits']
            field_name = f['name'].lower()

            # Skip fields that have offset 0 when we've already seen larger offsets
            # (these are likely calculated fields incorrectly included)
            if field_offset == 0 and max_offset_seen > 0:
                continue

            # Skip dummy/padding fields (they're not actual record data)
            if 'dummy' in field_name or 'padding' in field_name:
                continue

            valid_fields.append(f)
            max_offset_seen = max(max_offset_seen, field_offset)

        if not valid_fields:
            return []

        record_size_bits = max(
            (f['offset_bytes'] * 8 + f['offset_bits'] + f['length_bits'])
            for f in valid_fields
        )
        record_size_bytes = (record_size_bits + 7) // 8

        # Step 3: Determine the repetition count
        # First check if count is fixed in field definition (e.g., count: 8)
        # If count == -1, then determine dynamically from already decoded fields
        if repeating_field_def.get('count') and repeating_field_def['count'] != -1:
            logical_count = repeating_field_def['count']
        else:
            logical_count = self._get_repetition_count(already_decoded_fields)

        # Then, calculate how many records can actually fit in the payload
        base_offset_bytes = repeating_field_def['offset_bytes'] + version_offset_bytes
        available_bytes = len(payload) - base_offset_bytes
        max_records_in_payload = available_bytes // record_size_bytes

        # Use the minimum of logical count and what fits in payload
        actual_count = min(logical_count, max_records_in_payload)

        if actual_count == 0:
            return []  # No records to decode

        # Step 4: Decode each record
        decoded_records = []

        for record_idx in range(actual_count):
            # Calculate offset for this record
            record_offset = base_offset_bytes + (record_idx * record_size_bytes)

            # Decode all VALID fields in this record (skip fields with invalid offsets)
            for ref_field in valid_fields:
                # Create adjusted field definition for this record
                adjusted_field = deepcopy(ref_field)
                adjusted_field['offset_bytes'] += record_offset

                # Add record index to field name for clarity
                field_name_with_record = f"{adjusted_field['name']} (Record {record_idx})"

                try:
                    decoded_field = self._parse_field(payload, adjusted_field, offset_adjustment=0)
                    decoded_field['name'] = field_name_with_record
                    decoded_records.append(decoded_field)
                except Exception as e:
                    print(f"Warning: Failed to decode {field_name_with_record}: {e}")

        return decoded_records

    def _get_repetition_count(self, already_decoded_fields: List[Dict[str, Any]]) -> int:
        """
        Determine repetition count from already decoded fields.

        Looks for fields like "Num CA", "Num Records", or "Cumulative Bitmask".

        Args:
            already_decoded_fields: List of already decoded fields

        Returns:
            Repetition count (integer)
        """
        # Create a lookup map
        field_map = {f['name']: f for f in already_decoded_fields}

        # Try "Num CA" first (number of carriers)
        if "Num CA" in field_map:
            return field_map["Num CA"]['raw_value']

        # Try "Num Records"
        if "Num Records" in field_map:
            return field_map["Num Records"]['raw_value']

        # Try "Cumulative Bitmask" - count the number of set bits
        if "Cumulative Bitmask" in field_map:
            bitmask = field_map["Cumulative Bitmask"]['raw_value']
            # Count set bits
            return bin(bitmask).count('1')

        # Default: assume 1 record
        return 1

    def _parse_field(self, payload_bytes: bytes, field: Dict[str, Any], offset_adjustment: int = 0) -> Dict[str, Any]:
        """
        Parse a single field from payload.

        Args:
            payload_bytes: Raw payload bytes
            field: Field metadata
            offset_adjustment: Additional offset to add (e.g., for version field)

        Returns:
            Dictionary with parsed field data
        """
        offset_bytes = field['offset_bytes'] + offset_adjustment
        offset_bits = field['offset_bits']
        length_bits = field['length_bits']
        field_type = field['type_name']

        # Calculate total offset in bits
        total_offset_bits = offset_bytes * 8 + offset_bits

        # Extract raw value
        raw_value = self._extract_bits(payload_bytes, total_offset_bits, length_bits)

        # Convert based on type
        converted_value = self._convert_value(raw_value, field_type, length_bits)

        # Handle enumerations
        friendly_value = None
        if field.get('enum_mappings') and str(raw_value) in field['enum_mappings']:
            friendly_value = field['enum_mappings'][str(raw_value)]

        # Build field result
        field_result = {
            'name': field['name'],
            'raw': raw_value,
            'type': field_type,
            'value': converted_value
        }

        if friendly_value:
            field_result['decoded'] = friendly_value

        if field.get('description'):
            field_result['description'] = field['description']

        return field_result

    def _extract_bits(self, data: bytes, offset_bits: int, length_bits: int) -> int:
        """
        Extract bits from byte array.

        Args:
            data: Byte array
            offset_bits: Starting bit offset
            length_bits: Number of bits to extract

        Returns:
            Extracted value as integer
        """
        # Calculate byte positions
        start_byte = offset_bits // 8
        end_byte = (offset_bits + length_bits + 7) // 8

        if end_byte > len(data):
            raise ValueError(f"Field extends beyond payload: need {end_byte} bytes, have {len(data)}")

        # Extract bytes
        byte_slice = data[start_byte:end_byte]

        # Convert to integer (little-endian)
        value = int.from_bytes(byte_slice, byteorder='little')

        # Shift to align
        bit_offset_in_byte = offset_bits % 8
        value >>= bit_offset_in_byte

        # Mask to get only desired bits
        mask = (1 << length_bits) - 1
        value &= mask

        return value

    def _convert_value(self, raw_value: int, field_type: str, length_bits: int) -> Any:
        """
        Convert raw integer value to proper type.

        Args:
            raw_value: Raw integer value
            field_type: Field type string
            length_bits: Bit length

        Returns:
            Converted value
        """
        # Handle signed integers
        if field_type.startswith('Int'):
            # Check if sign bit is set
            if raw_value & (1 << (length_bits - 1)):
                # Convert to negative (two's complement)
                raw_value = raw_value - (1 << length_bits)
            return raw_value

        # Handle floats
        if field_type == 'Float32' and length_bits == 32:
            # Convert raw bits to float
            try:
                return struct.unpack('f', struct.pack('I', raw_value))[0]
            except:
                return float(raw_value)

        if field_type == 'Float64' and length_bits == 64:
            # Convert raw bits to double
            try:
                return struct.unpack('d', struct.pack('Q', raw_value))[0]
            except:
                return float(raw_value)

        # Handle unsigned integers and enumerations
        return raw_value

    def save_parsed_output(self, parsed_data: Dict[str, Any], output_file: str, pretty: bool = True):
        """
        Save parsed data to JSON file.

        Args:
            parsed_data: Parsed payload data
            output_file: Output file path
            pretty: Use pretty formatting (default: True)
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(parsed_data, f, ensure_ascii=False)

        print(f"Parsed output saved to: {output_file}")


def parse_payload_from_metadata(
    metadata_file: str,
    payload_hex: str,
    output_file: str,
    logcode_id: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to parse payload and save to file.

    Args:
        metadata_file: Path to metadata JSON file
        payload_hex: Hex string payload
        output_file: Output JSON file path
        logcode_id: Logcode ID (required for multi-logcode metadata)
        verbose: Print verbose output

    Returns:
        Parsed data dictionary
    """
    if verbose:
        print(f"Loading metadata from: {metadata_file}")

    parser = MetadataPayloadParser(metadata_file)

    if verbose:
        print(f"Parsing payload ({len(payload_hex.replace(' ', '').replace(chr(10), '')) // 2} bytes)...")

    parsed_data = parser.parse_payload(payload_hex, logcode_id)

    if verbose:
        print(f"Logcode: {parsed_data['logcode_id']} ({parsed_data['logcode_name']})")
        print(f"Version: {parsed_data['version']['value']} ({parsed_data['version']['value_hex']}) -> Table {parsed_data['version']['table']}")
        print(f"Fields parsed: {parsed_data['metadata']['fields_parsed']}")

    parser.save_parsed_output(parsed_data, output_file)

    return parsed_data


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print("Usage: python metadata_payload_parser.py <metadata.json> <payload_hex> <output.json> [logcode_id]")
        print("\nExample:")
        print("  python metadata_payload_parser.py metadata_0x1C07.json \"02000000...\" parsed_output.json")
        sys.exit(1)

    metadata_file = sys.argv[1]
    payload_hex = sys.argv[2]
    output_file = sys.argv[3]
    logcode_id = sys.argv[4] if len(sys.argv) > 4 else None

    result = parse_payload_from_metadata(
        metadata_file,
        payload_hex,
        output_file,
        logcode_id,
        verbose=True
    )

    print("\nParsing complete!")
