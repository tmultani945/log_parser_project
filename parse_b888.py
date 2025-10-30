"""Parse 0xB888 payload"""
import sys
sys.path.insert(0, '.')

from hex_decoder_module.metadata_payload_parser import parse_payload_from_metadata

# Payload hex data (without spaces)
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
    metadata_file='metadata_0xB888.json',
    payload_hex=payload_hex,
    output_file='parsed_payload_0xB888.json',
    verbose=True
)

print("\n=== Parsing Complete ===")
print(f"Logcode: {result['logcode_id']}")
print(f"Name: {result['logcode_name']}")
print(f"Version: {result['version']['value']}")
print(f"Table: {result['version']['table']}")
print(f"Fields parsed: {result['metadata']['fields_parsed']}")
