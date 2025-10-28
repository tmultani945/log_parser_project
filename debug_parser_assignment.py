import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor
from parser import LogcodeParser

pdf_path = 'data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf'

# First, verify extraction
print('='*60)
print('STEP 1: Verify PDF Extraction')
print('='*60)

extractor = PDFExtractor(pdf_path)
all_tables = extractor.extract_all_tables()

tables_164_167 = [t for t in all_tables if t.metadata.table_number in ['4-164', '4-165', '4-166', '4-167']]
print(f'\nTables 4-164 to 4-167 in extraction: {len(tables_164_167)}/4')
for t in tables_164_167:
    print(f'  - Table {t.metadata.table_number}: {t.metadata.title} (page {t.metadata.page_start+1})')

# Now check parser
print('\n' + '='*60)
print('STEP 2: Check Parser Logcode Detection')
print('='*60)

parser = LogcodeParser(pdf_path)

# Check if 0x1C2C section is detected
print('\nSearching for 0x1C2C section header...')
for page_num in range(60, 63):  # Pages 61-63
    page = parser.extractor.doc[page_num]
    text = page.get_text()
    sections = parser.detect_logcode_sections(text)
    if sections:
        for section in sections:
            if section['logcode'] == '0X1C2C':
                print(f'  Found on page {page_num+1}: Section {section["section"]} - {section["name"]} ({section["logcode"]})')

# Check if parser assigns tables correctly
print('\n' + '='*60)
print('STEP 3: Trace Table Assignment Logic')
print('='*60)

print('\nParsing all logcodes...')
logcodes = parser.parse_all_logcodes()

# Check 0X1C1A (previous logcode)
if '0X1C1A' in logcodes:
    lc_data = logcodes['0X1C1A']
    table_nums = sorted(lc_data.tables.keys(), key=lambda x: (int(x.split('-')[0]), int(x.split('-')[1])))
    print(f'\n0X1C1A (Section {lc_data.section}):')
    print(f'  Tables assigned: {table_nums[:3]}...{table_nums[-3:]} (total: {len(table_nums)})')

# Check 0X1C2C
if '0X1C2C' in logcodes:
    lc_data = logcodes['0X1C2C']
    table_nums = sorted(lc_data.tables.keys())
    print(f'\n0X1C2C (Section {lc_data.section}):')
    print(f'  Tables assigned: {table_nums if table_nums else "NONE"}')
    print(f'  Versions: {lc_data.versions}')
else:
    print('\n0X1C2C: NOT FOUND in parsed logcodes!')

# Check what happened during section detection and table assignment
print('\n' + '='*60)
print('STEP 4: Detailed Section Analysis')
print('='*60)

# Re-run first pass of parse_all_logcodes to see section detection
logcode_sections = []
for page_num in range(len(parser.extractor.doc)):
    page = parser.extractor.doc[page_num]
    text = page.get_text()
    sections_on_page = parser.detect_logcode_sections(text)
    for section_info in sections_on_page:
        if section_info['section'].startswith('4.'):
            section_num = int(section_info['section'].split('.')[1])
            if 9 <= section_num <= 11:  # Sections 4.9, 4.10, 4.11
                logcode_sections.append({
                    'logcode': section_info['logcode'],
                    'name': section_info['name'],
                    'section': section_info['section'],
                    'page': page_num
                })

print(f'\nSections 4.9 to 4.11 detected:')
for sec in logcode_sections:
    print(f'  {sec["logcode"]} - Section {sec["section"]} (page {sec["page"]+1}): {sec["name"]}')
