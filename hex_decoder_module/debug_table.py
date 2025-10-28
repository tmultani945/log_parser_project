"""
Debug script to see what Table 11-57 looks like.
"""

from hex_decoder_module.icd_parser.icd_query import ICDQueryEngine
import json

# Initialize query engine
pdf_path = r"C:\Users\proca\ICD_code_for_version_ch\log_parser_project\data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"
engine = ICDQueryEngine(pdf_path, enable_cache=True)

# Get metadata for 0xB823
logcode_id = "0xB823"
metadata = engine.get_logcode_metadata(logcode_id)

print(f"\n=== Logcode {logcode_id} ===")
print(f"Name: {metadata.logcode_name}")
print(f"Section: {metadata.section}")
print(f"\nVersion Map:")
for version, table in sorted(metadata.version_map.items()):
    print(f"  Version {version} -> Table {table}")

print(f"\nTables:")
for table_name, fields in metadata.table_definitions.items():
    print(f"\n  Table {table_name} ({len(fields)} fields):")
    for field in fields:
        print(f"    - {field.name:30s} | Type: {field.type_name:20s} | Offset: {field.offset_bytes:3d} | Len: {field.length_bits:3d} bits")

print(f"\nDependencies:")
for table, deps in metadata.dependencies.items():
    print(f"  Table {table} -> {deps}")

# Now get the version layout
print(f"\n\n=== Version 196611 Field Layout ===")
fields = engine.get_version_layout(logcode_id, 196611)
print(f"Total fields (including dependencies): {len(fields)}\n")
for i, field in enumerate(fields, 1):
    print(f"{i:2d}. {field.name:40s} | Type: {field.type_name:20s} | Offset: {field.offset_bytes:3d} | Len: {field.length_bits:3d} bits")
    if field.description:
        desc_lines = field.description.split('\n')[:2]  # First 2 lines
        for line in desc_lines:
            if line.strip():
                print(f"    Desc: {line.strip()[:80]}")
