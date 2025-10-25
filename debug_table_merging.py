import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

print('=== RAW TABLES FROM PAGES 18-22 (before merging) ===\n')
for page_num in range(18, 22):
    page_tables = extractor.extract_tables_from_page(page_num)
    print(f'--- PAGE {page_num + 1} ---')
    for i, table in enumerate(page_tables):
        print(f'  Table {i+1}: Caption = "{table["caption"]}"')
        print(f'  Rows: {len(table["rows"])}')
        if len(table['rows']) > 0:
            print(f'  First row: {table["rows"][0][0] if len(table["rows"][0]) > 0 else ""} | Off={table["rows"][0][3] if len(table["rows"][0]) > 3 else ""}')
            print(f'  Last row: {table["rows"][-1][0] if len(table["rows"][-1]) > 0 else ""} | Off={table["rows"][-1][3] if len(table["rows"][-1]) > 3 else ""}')
        print()

print('\n=== MERGED TABLES (after merging) ===\n')
all_tables = extractor.extract_all_tables()
for table in all_tables:
    if table.metadata.table_number in ['4-4', '4-6']:
        print(f'Table {table.metadata.table_number}: {table.metadata.title}')
        print(f'  Caption: {table.raw_caption}')
        print(f'  Pages: {table.metadata.page_start + 1} - {table.metadata.page_end + 1}')
        print(f'  Total rows: {len(table.rows)}')
        print(f'  First row: {table.rows[0][0]} | Off={table.rows[0][3] if len(table.rows[0]) > 3 else ""}')
        print(f'  Last row: {table.rows[-1][0]} | Off={table.rows[-1][3] if len(table.rows[-1]) > 3 else ""}')
        print()
