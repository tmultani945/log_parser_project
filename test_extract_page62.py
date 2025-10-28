import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = 'data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf'

extractor = PDFExtractor(pdf_path)

print('=== Extracting all tables ===')
all_tables = extractor.extract_all_tables()

print(f'\nTotal tables extracted: {len(all_tables)}')

# Check for tables on pages 61-62 (indices 60-61)
print('\n=== Tables on pages 61-62 ===')
tables_on_pages = [t for t in all_tables if t.metadata.page_start in [60, 61] or t.metadata.page_end in [60, 61]]

for table in tables_on_pages:
    print(f'\nTable {table.metadata.table_number}: {table.metadata.title}')
    print(f'  Pages: {table.metadata.page_start+1} to {table.metadata.page_end+1}')
    print(f'  Headers: {table.headers}')
    print(f'  Rows: {len(table.rows)}')

# Check for tables in 4-160 to 4-170 range
print('\n=== Tables 4-160 to 4-170 ===')
for i in range(160, 171):
    tnum = f'4-{i}'
    found_tables = [t for t in all_tables if t.metadata.table_number == tnum]
    if found_tables:
        t = found_tables[0]
        print(f'Table {tnum}: Found - {t.metadata.title} (page {t.metadata.page_start+1})')
    else:
        print(f'Table {tnum}: NOT FOUND')
