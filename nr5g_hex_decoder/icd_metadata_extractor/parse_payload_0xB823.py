#!/usr/bin/env python3
"""
Payload Parser for 0xB823

This script is a standalone parser for 0xB823 payloads with no external dependencies.
It reads metadata from JSON and parses binary payloads according to field definitions.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import struct


class PayloadParser:
    """
    Standalone payload parser that reads metadata and parses binary data.
    No dependency on external decoder modules.
    """

    def __init__(self, metadata_path: str):
        """
        Initialize parser with metadata file.

        Args:
            metadata_path: Path to metadata JSON file
        """
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Support both simple and full metadata formats
        if 'metadata' in data:
            self.metadata = data['metadata']
        else:
            self.metadata = data

        # Build table lookup
        self.tables = {}
        self._build_table_index()

    def _build_table_index(self):
        """Build index of all tables for quick lookup"""
        # Add pre-version tables (e.g., Table 11-43: MajorMinorVersion)
        for pre_table in self.metadata.get('pre_version_tables', []):
            self.tables[pre_table['table_number']] = pre_table

        # Add main table
        if 'main_table' in self.metadata:
            main = self.metadata['main_table']
            self.tables[main['table_number']] = main

        # Add dependent tables
        for dep_table in self.metadata.get('dependent_tables', []):
            self.tables[dep_table['table_number']] = dep_table

    def _hex_string_to_bytes(self, hex_string: str) -> bytes:
        """
        Convert hex string to bytes.

        Args:
            hex_string: Hex string with optional spaces/newlines

        Returns:
            Bytes object
        """
        # Remove whitespace and newlines
        clean_hex = ''.join(hex_string.split())
        # Convert to bytes
        return bytes.fromhex(clean_hex)

    def _read_bits(self, data: bytes, offset_bytes: int, offset_bits: int, length_bits: int) -> int:
        """
        Read bits from byte array (little-endian byte order).

        Args:
            data: Byte array
            offset_bytes: Byte offset
            offset_bits: Bit offset within byte
            length_bits: Number of bits to read

        Returns:
            Integer value
        """
        # For byte-aligned fields, use struct.unpack for proper little-endian handling
        if offset_bits == 0 and length_bits % 8 == 0:
            num_bytes = length_bits // 8
            end_byte = offset_bytes + num_bytes

            if end_byte > len(data):
                raise ValueError(f"Not enough data: need {end_byte} bytes, have {len(data)}")

            # Use struct to read little-endian integers
            byte_slice = data[offset_bytes:end_byte]

            if num_bytes == 1:
                return struct.unpack('<B', byte_slice)[0]
            elif num_bytes == 2:
                return struct.unpack('<H', byte_slice)[0]
            elif num_bytes == 4:
                return struct.unpack('<I', byte_slice)[0]
            elif num_bytes == 8:
                return struct.unpack('<Q', byte_slice)[0]
            else:
                # For other sizes, read as little-endian manually
                value = 0
                for i, byte in enumerate(byte_slice):
                    value |= byte << (i * 8)
                return value

        # For bit-level fields, use bit manipulation with little-endian byte order
        total_bit_offset = offset_bytes * 8 + offset_bits
        start_byte = total_bit_offset // 8
        end_byte = (total_bit_offset + length_bits + 7) // 8

        if end_byte > len(data):
            raise ValueError(f"Not enough data: need {end_byte} bytes, have {len(data)}")

        # Read bytes in little-endian order
        value = 0
        for i in range(start_byte, end_byte):
            byte_offset = i - start_byte
            value |= data[i] << (byte_offset * 8)

        # Calculate bit shift for bit-level offset
        bit_offset_in_byte = total_bit_offset % 8
        value >>= bit_offset_in_byte

        # Mask to get only the bits we need
        mask = (1 << length_bits) - 1
        value &= mask

        return value

    def _parse_field_value(self, data: bytes, field: Dict[str, Any]) -> Tuple[Any, str]:
        """
        Parse a single field value from binary data.

        Args:
            data: Binary payload data
            field: Field definition from metadata

        Returns:
            Tuple of (parsed_value, type_description)
        """
        type_name = field['type_name']
        offset_bytes = field['offset_bytes']
        offset_bits = field.get('offset_bits', 0)
        length_bits = field['length_bits']

        # Read raw bits
        raw_value = self._read_bits(data, offset_bytes, offset_bits, length_bits)

        # Parse based on type
        if type_name.startswith('Uint'):
            return raw_value, f"Uint{length_bits}"

        elif type_name == 'Bool':
            return bool(raw_value), "Bool"

        elif type_name == 'Enumeration':
            # Parse enum from description
            enum_str = self._parse_enum_from_description(field.get('description', ''), raw_value)
            return enum_str, "Enumeration"

        elif type_name.startswith('Table'):
            # Reference to another table - will be parsed recursively
            return raw_value, type_name

        else:
            # Unknown type, return raw value
            return raw_value, type_name

    def _parse_enum_from_description(self, description: str, value: int) -> str:
        """
        Parse enumeration value from field description.

        Args:
            description: Field description containing enum values
            value: Raw integer value

        Returns:
            Enum string name or str(value) if not found
        """
        if not description:
            return str(value)

        # Look for pattern: "• 1 – SINGLE STANDBY"
        lines = description.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-'):
                # Parse "• 1 – SINGLE STANDBY" or "- 1 – SINGLE STANDBY"
                parts = line.split('–', 1)
                if len(parts) == 2:
                    # Extract number from first part
                    num_part = parts[0].replace('•', '').replace('-', '').strip()
                    try:
                        enum_value = int(num_part)
                        if enum_value == value:
                            return parts[1].strip()
                    except ValueError:
                        continue

        return str(value)

    def _parse_table(self, data: bytes, table_number: str, record_index: int = 0) -> Dict[str, Any]:
        """
        Parse a table structure from binary data.

        Args:
            data: Binary payload data
            table_number: Table number to parse (e.g., "11-55")
            record_index: Record index for field naming

        Returns:
            Dictionary of parsed fields
        """
        if table_number not in self.tables:
            raise ValueError(f"Table {table_number} not found in metadata")

        table = self.tables[table_number]
        fields = table['fields']

        parsed_fields = {}

        for field in fields:
            field_name = field['name']
            type_name = field['type_name']

            # Check if this is a nested table reference
            if type_name.startswith('Table'):
                # Extract table number from "Table 11-55"
                ref_table_number = type_name.replace('Table', '').strip()

                # Parse the nested table
                nested_data = self._parse_table(data, ref_table_number, record_index)

                # Merge nested fields into parent
                for nested_field_name, nested_value in nested_data.items():
                    parsed_fields[nested_field_name] = nested_value
            else:
                # Parse simple field
                value, value_type = self._parse_field_value(data, field)

                # Store field with record index if needed
                if record_index > 0:
                    field_key = f"{field_name} (Record {record_index})"
                else:
                    field_key = field_name

                parsed_fields[field_key] = {
                    'value': value,
                    'type': value_type,
                    'offset_bytes': field['offset_bytes'],
                    'length_bits': field['length_bits']
                }

        return parsed_fields

    def parse_payload(self, payload_hex: str, version: int = None) -> Dict[str, Any]:
        """
        Parse complete payload using metadata.

        Args:
            payload_hex: Hex string of payload
            version: Optional version number (auto-detected if not provided)

        Returns:
            Parsed data dictionary
        """
        # Convert hex to bytes
        data = self._hex_string_to_bytes(payload_hex)

        # Parse version from payload (first 4 bytes) using Table 11-43: MajorMinorVersion
        if len(data) < 4:
            raise ValueError("Payload too short to contain version")

        # Use Table 11-43 to dynamically parse the version structure
        VERSION_TABLE = "11-43"  # MajorMinorVersion table

        if VERSION_TABLE not in self.tables:
            # Fallback to hardcoded parsing if Table 11-43 not available
            version_value = struct.unpack('<I', data[0:4])[0]
            major = (version_value >> 16) & 0xFFFF
            minor = version_value & 0xFFFF
        else:
            # Parse version using metadata-defined structure
            version_fields = self._parse_table(data[0:4], VERSION_TABLE)

            # Extract Major and Minor from parsed fields
            major = version_fields.get('Major', {}).get('value', 0)
            minor = version_fields.get('Minor', {}).get('value', 0)

            # Compute version value: (Major << 16) | Minor
            version_value = (major << 16) | minor

        # Find the table for this version
        target_version = self.metadata.get('target_version', {})
        if target_version.get('version') != version_value:
            raise ValueError(f"Version mismatch: expected {target_version.get('version')}, got {version_value}")

        table_number = target_version.get('table_number')

        # Parse main table (which will recursively parse dependent tables)
        parsed_fields = self._parse_table(data[4:], table_number)  # Skip version bytes

        # Build result
        result = {
            'logcode_id': self.metadata['logcode_id'],
            'logcode_name': self.metadata['logcode_name'],
            'version': {
                'value': version_value,
                'hex': f"0x{version_value:08X}",
                'major': major,
                'minor': minor
            },
            'fields': parsed_fields
        }

        return result


def format_output(parsed_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format parsed data to match the expected output structure.

    Args:
        parsed_data: Raw parsed data from parser
        metadata: Original metadata with field descriptions

    Returns:
        Formatted dictionary
    """
    version_info = parsed_data['version']

    result = {
        "Version": version_info['value'],
        "LogRecordDescription": parsed_data['logcode_name'],
        "MajorMinorVersion": [
            {"MajorMinorVersion": f"{version_info['major']}.{version_info['minor']}"}
        ],
        "Serving Cell Info": []
    }

    # Extract all fields into a single record
    record = {}

    for field_name, field_data in parsed_data['fields'].items():
        # Skip version field
        if 'version' in field_name.lower() and field_name == "Version":
            continue

        # Remove "(Record N)" suffix if present
        clean_name = field_name
        if '(Record' in field_name:
            clean_name = field_name.split('(Record')[0].strip()

        # Remove spaces from field name
        formatted_name = clean_name.replace(' ', '')

        # Get the value
        value = field_data['value']

        # Convert to string for JSON output
        if isinstance(value, bool):
            value = str(int(value))
        elif not isinstance(value, str):
            value = str(value)

        record[formatted_name] = value

    if record:
        result["Serving Cell Info"].append(record)

    return result


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent

    # Paths
    metadata_file = script_dir / "data" / "output" / "metadata_0xB823_v196610.json"

    # Payload from user
    payload_hex = """
        02 00 03 00 01 01 00 7B 00 1A 80 2E
		DE 40 18 30 01 E0 E5 09 00 4A DE 09
		00 64 00 64 00 1A 80 2E DE 00 00 00
		00 37 01 03 E0 01 00 08 01 16 00 4D
		00
    """

    print("="*80)
    print("0xB823 Payload Parser")
    print("="*80)

    if not metadata_file.exists():
        print(f"\nERROR: Metadata file not found: {metadata_file}")
        return 1

    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_json = json.load(f)

        # Create parser
        print(f"\nInitializing parser with metadata...")
        parser = PayloadParser(str(metadata_file))

        # Parse the payload
        print(f"Parsing payload ({len(payload_hex.replace(' ', '').replace(chr(10), '')) // 2} bytes)...")
        parsed_data = parser.parse_payload(payload_hex)

        # Format to match expected output
        formatted_output = format_output(parsed_data, metadata_json.get('metadata', {}))

        # Display
        print("\n" + "="*80)
        print("PARSED OUTPUT:")
        print("="*80)
        print(json.dumps(formatted_output, indent=2))

        # Save
        output_file = script_dir / "data" / "output" / "parsed_0xB823.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_output, f, indent=2, ensure_ascii=False)

        print("\n" + "="*80)
        print(f"Saved to: {output_file}")
        print("="*80)

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
