import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

# Extract all tables
all_tables = extractor.extract_all_tables()

print(f"Total tables extracted: {len(all_tables)}\n")

# Show first 10 table titles and their first few rows
for i, table in enumerate(all_tables[:15]):
    print(f"=== Table {table.metadata.table_number}: {table.metadata.title} ===")
    print(f"Caption: {table.raw_caption}")
    print(f"Headers: {table.headers}")
    print(f"Number of rows: {len(table.rows)}")
    if len(table.rows) > 0:
        print(f"First 3 rows:")
        for row in table.rows[:3]:
            print(f"  {row[0] if len(row) > 0 else ''} | {row[1] if len(row) > 1 else ''}")
    print()
