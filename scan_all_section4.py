import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor
import re

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

print(f'=== SCANNING ALL {len(extractor.doc)} PAGES FOR SECTION 4 HEADERS ===\n')

# Pattern for section headers (split across lines)
pattern1 = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'
pattern2 = r'^\s*(\d+\.\d+)\s*$'

for page_num in range(len(extractor.doc)):
    page = extractor.doc[page_num]
    text = page.get_text()
    lines = text.split('\n')

    for i, line in enumerate(lines):
        # Check pattern 1 (all on one line)
        match = re.match(pattern1, line, re.IGNORECASE)
        if match and match.group(1).startswith('4.'):
            print(f'Page {page_num + 1}: {line.strip()}')

        # Check pattern 2 (section on one line, details on next)
        match = re.match(pattern2, line)
        if match and match.group(1).startswith('4.') and i + 1 < len(lines):
            next_line = lines[i + 1]
            name_code_match = re.search(r'^(.+?)\s+\((0x[0-9A-F]+)\)', next_line, re.IGNORECASE)
            if name_code_match:
                print(f'Page {page_num + 1}: {match.group(1)} {name_code_match.group(1)} ({name_code_match.group(2)})')
