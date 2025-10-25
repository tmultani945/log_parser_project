import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

print("=== RAW TABLES FROM PAGE 17 ===\n")
page_17_tables = extractor.extract_tables_from_page(17)
for i, table in enumerate(page_17_tables):
    print(f"Table {i+1} on page 17:")
    print(f"Caption: {table['caption']}")
    print(f"Rows: {len(table['rows'])}")
    print(f"Last 5 rows:")
    for row in table['rows'][-5:]:
        print(f"  {row[0] if len(row) > 0 else ''} | {row[1] if len(row) > 1 else ''} | Off={row[3] if len(row) > 3 else ''}")
    print()

print("\n=== RAW TABLES FROM PAGE 18 ===\n")
page_18_tables = extractor.extract_tables_from_page(18)
for i, table in enumerate(page_18_tables):
    print(f"Table {i+1} on page 18:")
    print(f"Caption: {table['caption']}")
    print(f"Rows: {len(table['rows'])}")
    print(f"First 5 rows:")
    for row in table['rows'][:5]:
        print(f"  {row[0] if len(row) > 0 else ''} | {row[1] if len(row) > 1 else ''} | Off={row[3] if len(row) > 3 else ''}")
    print()
