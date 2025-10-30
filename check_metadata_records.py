import json

m = json.load(open('metadata_0xB888.json'))
v = m['versions']['196609']

print("=== Checking repeating structure ===")
print(f"Table: {v['table_name']}")
print(f"Total fields: {len(v['fields'])}")
print()

# Find fields with Table references (repeating structures)
for i, f in enumerate(v['fields']):
    if 'Table' in f.get('type_name', ''):
        print(f"Field {i}: {f['name']}")
        print(f"  Type: {f['type_name']}")
        print(f"  Count: {f.get('count', 'N/A')}")
        print(f"  Offset bytes: {f['offset_bytes']}")
        print(f"  Offset bits: {f['offset_bits']}")
        print(f"  Length bits: {f['length_bits']}")
        print()

# Check all_tables to see the actual table structure
print("=== Checking all_tables ===")
table_name = v['table_name']
if table_name in m['all_tables']:
    table_info = m['all_tables'][table_name]
    print(f"Table {table_name}:")
    print(f"  Field count: {table_info['field_count']}")
    print(f"  Dependencies: {table_info['dependencies']}")
    print()

    # Look for the repeating field
    for f in table_info['fields']:
        if 'Table' in f.get('type_name', '') and f.get('count') == -1:
            print(f"FOUND REPEATING STRUCTURE:")
            print(f"  Name: {f['name']}")
            print(f"  Type: {f['type_name']}")
            print(f"  Count: {f.get('count')}")
            print()

            # Get the referenced table
            import re
            match = re.search(r'Table\s+(\d+-\d+)', f['type_name'])
            if match:
                ref_table = match.group(1)
                print(f"  References table: {ref_table}")
                if ref_table in m['all_tables']:
                    ref_info = m['all_tables'][ref_table]
                    print(f"  Referenced table has {ref_info['field_count']} fields")
                    print(f"  Referenced table fields:")
                    for rf in ref_info['fields'][:5]:  # Show first 5
                        print(f"    - {rf['name']} ({rf['type_name']})")
