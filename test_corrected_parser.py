"""Test the corrected metadata payload parser"""
import sys
sys.path.insert(0, '.')

from hex_decoder_module.metadata_payload_parser import parse_payload_from_metadata

# Payload hex data
payload_hex = """
01 00 03 00 73 5D 74 01 C0 26 03 60
77 5D 78 5D 79 5D 7A 5D 00 00 01 00
E1 8D 64 00 52 0A 02 00 16 08 02 00
3C 02 00 00 83 0C 00 00 85 04 00 00
2A 00 00 00 8B 33 B5 03 00 00 00 00
A5 E3 58 00 00 00 00 00 30 17 0E 04
00 00 00 00 A3 C8 49 00 00 00 00 00
5E BD 5C 00 00 00 00 00 01 00 01 00
B5 07 00 00 0B 00 00 00 07 00 00 00
04 00 00 00 04 00 00 00 00 00 00 00
00 00 00 00 4C 53 02 00 00 00 00 00
38 C0 01 00 00 00 00 00 84 13 04 00
00 00 00 00 C7 05 00 00 00 00 00 00
38 C0 01 00 00 00 00 00
"""

# Parse the payload
result = parse_payload_from_metadata(
    metadata_file='metadata_0xB888_corrected.json',
    payload_hex=payload_hex,
    output_file='parsed_payload_corrected.json',
    verbose=True
)

print("\n=== Parsing Complete ===")
print(f"Logcode: {result['logcode_id']}")
print(f"Name: {result['logcode_name']}")
print(f"Version: {result['version']['value']} ({result['version']['value_hex']})")
print(f"Table: {result['version']['table']}")
print(f"Fields parsed: {result['metadata']['fields_parsed']}")

# Show key fields
print("\n=== Key Header Fields ===")
for field_name in ['Num Records', 'Num Total Slots', 'Num CA', 'Cumulative Bitmask']:
    if field_name in result['fields']:
        field_data = result['fields'][field_name]
        print(f"{field_name}: {field_data.get('raw', field_data.get('value'))}")

# Count records
record_fields = [k for k in result['fields'].keys() if 'Record' in k]
records_0 = [k for k in record_fields if 'Record 0' in k]
records_1 = [k for k in record_fields if 'Record 1' in k]
records_2 = [k for k in record_fields if 'Record 2' in k]

print(f"\n=== Records Decoded ===")
print(f"Record 0 fields: {len(records_0)}")
print(f"Record 1 fields: {len(records_1)}")
print(f"Record 2 fields: {len(records_2)}")

# Show first few fields of each record
if records_0:
    print(f"\n=== Record 0 Sample ===")
    for field_name in ['Carrier ID (Record 0)', 'Numerology (Record 0)', 'Num Slots Elapsed (Record 0)']:
        if field_name in result['fields']:
            field_data = result['fields'][field_name]
            decoded = field_data.get('decoded', field_data.get('value'))
            print(f"{field_name}: {decoded}")

if records_1:
    print(f"\n=== Record 1 Sample ===")
    for field_name in ['Carrier ID (Record 1)', 'Numerology (Record 1)', 'Num Slots Elapsed (Record 1)']:
        if field_name in result['fields']:
            field_data = result['fields'][field_name]
            decoded = field_data.get('decoded', field_data.get('value'))
            print(f"{field_name}: {decoded}")
