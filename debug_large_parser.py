import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = 'data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf'

extractor = PDFExtractor(pdf_path)

print('='*60)
print('DEBUG: Testing large_pdf_parser.py logic for 0x1C2C')
print('='*60)

# Step 1: Extract tables from pages 61-62
print('\nStep 1: Extract tables from pages 61-62')
all_tables_dict = {}
for page_num in [60, 61]:  # Pages 61-62 (0-indexed)
    page_tables = extractor.extract_tables_from_page(page_num)
    all_tables_dict[page_num] = page_tables
    print(f'  Page {page_num+1}: {len(page_tables)} tables')
    for t in page_tables:
        caption = t.get('caption', '')
        print(f'    - {caption}')

# Step 2: Merge continuations
print('\nStep 2: Merge continuations')
all_tables_list = []
for page_num in sorted(all_tables_dict.keys()):
    all_tables_list.extend(all_tables_dict[page_num])

merged_tables = extractor.merge_continuations(all_tables_list)
print(f'  Merged into {len(merged_tables)} logical tables')

tables_164_167 = [t for t in merged_tables if t.metadata.table_number in ['4-164', '4-165', '4-166', '4-167']]
print(f'  Tables 4-164 to 4-167: {len(tables_164_167)}/4 found')
for t in tables_164_167:
    print(f'    - Table {t.metadata.table_number}: {t.metadata.title} (page {t.metadata.page_start+1})')

# Step 3: Detect logcode section for 0x1C2C
print('\nStep 3: Detect logcode section for 0x1C2C')
from parser import LogcodeParser
parser = LogcodeParser(pdf_path)

section_0x1c2c = None
for page_num in [60, 61]:  # Check pages 61-62
    page = extractor.doc[page_num]
    text = page.get_text()
    sections = parser.detect_logcode_sections(text)
    for sec in sections:
        if sec['logcode'] == '0X1C2C':
            section_0x1c2c = {
                'logcode': sec['logcode'],
                'name': sec['name'],
                'section': sec['section'],
                'page': page_num
            }
            print(f'  Found on page {page_num+1}: Section {sec["section"]} - {sec["name"]} ({sec["logcode"]})')

# Step 4: Simulate large_pdf_parser.py candidate collection
print('\nStep 4: Simulate large_pdf_parser.py candidate collection')
if section_0x1c2c:
    section = section_0x1c2c
    section_major = section['section'].split('.')[0]
    candidates = []

    print(f'  Section major: {section_major}')
    print(f'  Section page: {section["page"]} (page {section["page"]+1})')
    print(f'  Looking for tables on pages {section["page"]} or {section["page"]+1}')

    for table in merged_tables:
        if table.metadata.page_start >= section['page']:
            table_major = table.metadata.table_number.split('-')[0]
            if table_major != section_major:
                continue

            if table.metadata.page_start in [section['page'], section['page'] + 1]:
                candidates.append(table)
                print(f'    Added candidate: Table {table.metadata.table_number} - {table.metadata.title} (page {table.metadata.page_start+1})')

    print(f'\n  Total candidates: {len(candidates)}')

    # Step 5: Try matching strategies
    print('\nStep 5: Try matching strategies')

    # Strategy 1: First 15 chars
    print('  Strategy 1: Match first 15 chars')
    section_keywords = section['name'].replace(' ', '').replace('5G', '5g')
    print(f'    Section keywords: "{section_keywords}" (first 15: "{section_keywords[:15]}")')

    matched_strategy1 = None
    for table in candidates:
        table_keywords = table.metadata.title.replace('_', '')
        print(f'    Table {table.metadata.table_number}: "{table_keywords}"')
        if section_keywords[:15].lower() in table_keywords.lower():
            matched_strategy1 = table
            print(f'      ✓ MATCH! "{section_keywords[:15].lower()}" in "{table_keywords.lower()}"')
            break
        else:
            print(f'      ✗ No match')

    if matched_strategy1:
        print(f'\n  Strategy 1 result: Table {matched_strategy1.metadata.table_number}')
    else:
        print('\n  Strategy 1 result: No match')

        # Strategy 2: First 10 chars
        print('\n  Strategy 2: Match first 10 chars')
        print(f'    Section keywords (first 10): "{section_keywords[:10]}"')

        matched_strategy2 = None
        for table in candidates:
            table_keywords = table.metadata.title.replace('_', '')
            if section_keywords[:10].lower() in table_keywords.lower():
                matched_strategy2 = table
                print(f'      ✓ MATCH! Table {table.metadata.table_number}: "{section_keywords[:10].lower()}" in "{table_keywords.lower()}"')
                break

        if matched_strategy2:
            print(f'\n  Strategy 2 result: Table {matched_strategy2.metadata.table_number}')
        else:
            print('\n  Strategy 2 result: No match')

            # Strategy 3: First candidate
            if candidates:
                print(f'\n  Strategy 3: Take first candidate: Table {candidates[0].metadata.table_number}')
            else:
                print('\n  Strategy 3: No candidates available')

else:
    print('  ERROR: Section 0x1C2C not detected!')
