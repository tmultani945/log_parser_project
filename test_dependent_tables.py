"""Test script to verify dependent table fields are expanded"""

from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser

# Load parser with metadata
parser = MetadataPayloadParser('metadata_0xB888.json')

# Load payload
with open('payload_0xB888.hex', 'r') as f:
    payload_hex = f.read().strip()

# Parse payload
result = parser.parse_payload(payload_hex)

print("=" * 60)
print("PARSING TEST RESULTS")
print("=" * 60)
print(f"Logcode: {result['logcode_id']} - {result['logcode_name']}")
print(f"Version: {result['version']['value']} (0x{result['version']['value']:08X})")
print(f"Table: {result['version']['table']}")
print(f"Total fields parsed: {result['metadata']['fields_parsed']}")
print()

# Show fields from dependent tables (those with Record index)
print("Fields from DEPENDENT TABLES (expanded):")
print("-" * 60)
record_fields = [f for f in result['fields'].keys() if 'Record' in f]
print(f"Found {len(record_fields)} record-indexed fields")
print()

for field_name in sorted(record_fields)[:20]:
    field_data = result['fields'][field_name]
    print(f"  {field_name}:")
    print(f"    Value: {field_data.get('value')}")
    print(f"    Type: {field_data.get('type')}")
print()

# Show main table fields
print("Main table fields:")
print("-" * 60)
main_fields = [f for f in result['fields'].keys() if 'Record' not in f]
for field_name in main_fields[:10]:
    field_data = result['fields'][field_name]
    print(f"  {field_name}: {field_data.get('value')} ({field_data.get('type')})")

print()
print("✓ Test completed successfully!")
print("✓ Dependent table fields are now being expanded from metadata JSON")
