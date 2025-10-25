import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

print('=== LOGCODE SECTIONS IN PDF ===\n')
for page_num in range(len(extractor.doc)):
    page = extractor.doc[page_num]
    text = page.get_text()

    # Check for logcode section headers
    import re
    pattern = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'
    for line in text.split('\n'):
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            print(f'Page {page_num + 1}: Section {match.group(1)} - {match.group(2)} ({match.group(3)})')
            break

print('\n=== TABLES BY PAGE ===\n')
all_tables = extractor.extract_all_tables()
for table in all_tables:
    print(f'Table {table.metadata.table_number}: {table.metadata.title} (Pages {table.metadata.page_start + 1}-{table.metadata.page_end + 1})')
