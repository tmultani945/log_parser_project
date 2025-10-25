import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

# Extract all tables
all_tables = extractor.extract_all_tables()

print('=== TABLES ON PAGES 24-28 ===\n')
for table in all_tables:
    if 23 <= table.metadata.page_start <= 27 or 23 <= table.metadata.page_end <= 27:
        print(f'Table {table.metadata.table_number}: {table.metadata.title}')
        print(f'  Pages: {table.metadata.page_start + 1} - {table.metadata.page_end + 1}')
        print()
