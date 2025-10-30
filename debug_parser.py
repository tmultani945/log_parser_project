"""Debug the parser to see record count logic"""
import json

# Load corrected metadata
m = json.load(open('metadata_0xB888_corrected.json'))

# Check Table 7-2804 structure
table_7_2804 = m['versions']['196609']['fields']
print("=== Table 7-2804 Structure ===")
for i, f in enumerate(table_7_2804):
    count_info = f.get('count', 'N/A')
    if count_info == -1:
        print(f"{i}: {f['name']:30} count={count_info:5}  type={f['type_name']} <-- REPEATING")
    else:
        print(f"{i}: {f['name']:30} count={count_info:5}  type={f['type_name']}")

# Check Table 7-2805 (Records table)
print("\n=== Table 7-2805 (Records) Structure ===")
table_7_2805 = m['all_tables']['7-2805']
print(f"Total fields: {len(table_7_2805['fields'])}")
print(f"Dependencies: {table_7_2805['dependencies']}")

# Calculate record size
fields = table_7_2805['fields']
print("\nField offsets:")
for i, f in enumerate(fields[:8]):
    end_bit = f['offset_bytes'] * 8 + f['offset_bits'] + f['length_bits']
    end_byte = (end_bit + 7) // 8
    print(f"  {i}: {f['name']:25} offset={f['offset_bytes']:3} bits={f['offset_bits']:2} len={f['length_bits']:3}  end_byte={end_byte}")

max_end_bit = max((f['offset_bytes'] * 8 + f['offset_bits'] + f['length_bits']) for f in fields)
record_size_bytes = (max_end_bit + 7) // 8

print(f"\nCalculated record size: {record_size_bytes} bytes")
print(f"Max end bit: {max_end_bit}")

# Check "Records" field offset in Table 7-2804
records_field = [f for f in table_7_2804 if f.get('count') == -1 and 'Table' in f['type_name']][0]
print(f"\n=== Records Field in Table 7-2804 ===")
print(f"Name: {records_field['name']}")
print(f"Offset bytes: {records_field['offset_bytes']}")
print(f"Offset bits: {records_field['offset_bits']}")
print(f"Type: {records_field['type_name']}")

# Calculate where records start in payload
version_size = 4  # 32 bits = 4 bytes
records_start = records_field['offset_bytes'] + version_size
print(f"\nRecords start at payload offset: {records_start} bytes")

# Calculate max records
payload_size = 164
available = payload_size - records_start
max_records = available // record_size_bytes

print(f"\nPayload size: {payload_size} bytes")
print(f"Available for records: {available} bytes")
print(f"Max complete records: {max_records}")

# Check actual offsets
print(f"\nRecord 0 would be at: {records_start} to {records_start + record_size_bytes - 1}")
print(f"Record 1 would be at: {records_start + record_size_bytes} to {records_start + 2*record_size_bytes - 1}")
print(f"Payload ends at: {payload_size - 1}")

if records_start + 2 * record_size_bytes <= payload_size:
    print(f"\n✓ TWO records should FIT")
else:
    print(f"\n✗ Only ONE record fits")
    shortfall = (records_start + 2 * record_size_bytes) - payload_size
    print(f"  Short by {shortfall} bytes")
