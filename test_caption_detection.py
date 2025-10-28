import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor
import re

pdf_path = 'data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf'

extractor = PDFExtractor(pdf_path)

# Test caption detection on page 62 (index 61)
page_num = 61
page = extractor.plumber_pdf.pages[page_num]
text = page.extract_text()
lines = text.split('\n') if text else []

print(f'PAGE {page_num + 1} - Testing caption detection')
print('='*60)

# Test the detect_table_caption method on each line
captions_found = []
for i, line in enumerate(lines):
    if 'Table' in line and '4-16' in line:
        result = extractor.detect_table_caption(line)
        if result:
            table_num, title, is_cont = result
            captions_found.append(result)
            print(f'[MATCH] Line {i}: "{line}"')
            print(f'  -> Table: {table_num}, Title: {title}, Continuation: {is_cont}')
        else:
            print(f'[NO MATCH] Line {i}: "{line}"')

print(f'\n{"="*60}')
print(f'Total captions detected: {len(captions_found)}')
print(f'Expected: 4 (Tables 4-164, 4-165, 4-166, 4-167)')

# Now test the full extraction
print(f'\n{"="*60}')
print('Testing extract_tables_from_page()')
print('='*60)

extracted = extractor.extract_tables_from_page(page_num)
print(f'Tables extracted: {len(extracted)}')

for i, table_dict in enumerate(extracted):
    print(f'\nTable {i+1}:')
    print(f'  Caption: "{table_dict.get("caption", "")}"')
    print(f'  Headers: {table_dict.get("headers", [])}')
    print(f'  Rows: {len(table_dict.get("rows", []))}')
