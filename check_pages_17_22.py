import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor
import re

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

print('=== TEXT CONTENT ON PAGES 17-22 (looking for section headers) ===\n')
for page_num in [16, 17, 18, 19, 20, 21]:  # 0-indexed
    if page_num < len(extractor.doc):
        page = extractor.doc[page_num]
        text = page.get_text()

        print(f'--- PAGE {page_num + 1} ---')
        # Look for section patterns
        pattern = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'
        lines = text.split('\n')
        found_section = False
        for i, line in enumerate(lines[:30]):  # First 30 lines
            match = re.match(pattern, line, re.IGNORECASE)
            if match or 'TxAGC' in line or 'RxAGC' in line or line.startswith('4.'):
                print(f'  Line {i}: {line.strip()}')
                if match:
                    found_section = True
        if not found_section:
            print(f'  No section header found')
        print()
