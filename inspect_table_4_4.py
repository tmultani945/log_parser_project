import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

# Extract all tables
all_tables = extractor.extract_all_tables()

print("=== ALL TABLES WITH NUMBER 4-4 OR STARTING WITH Nr5g_Sub6TxAgc_V2 ===\n")
for table in all_tables:
    if table.metadata.table_number == '4-4' or 'Nr5g_Sub6TxAgc_V2' in table.metadata.title:
        print(f"Table: {table.metadata.table_number}")
        print(f"Title: {table.metadata.title}")
        print(f"Caption: {table.raw_caption}")
        print(f"Pages: {table.metadata.page_start} - {table.metadata.page_end}")
        print(f"Is continuation: {table.metadata.is_continuation}")
        print(f"Number of rows: {len(table.rows)}")
        print(f"First 5 rows:")
        for i, row in enumerate(table.rows[:5]):
            print(f"  Row {i}: {row[0] if len(row) > 0 else ''} | {row[1] if len(row) > 1 else ''} | Off={row[3] if len(row) > 3 else ''}")
        print()

print("\n=== CHECKING PAGES 17-19 FOR ALL TABLES ===\n")
for table in all_tables:
    if 17 <= table.metadata.page_start <= 19 or 17 <= table.metadata.page_end <= 19:
        print(f"Table {table.metadata.table_number}: {table.metadata.title} (Pages {table.metadata.page_start}-{table.metadata.page_end})")
