import sys
sys.path.insert(0, 'src')
from pdf_extractor import PDFExtractor

pdf_path = "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf"
extractor = PDFExtractor(pdf_path)

print('=== FULL TEXT OF PAGE 20 ===\n')
page = extractor.doc[19]  # 0-indexed, so page 20 is index 19
text = page.get_text()
lines = text.split('\n')

print('Looking for table captions...\n')
for i, line in enumerate(lines):
    if 'Table' in line and ('4-4' in line or '4-5' in line or '4-6' in line):
        print(f'Line {i}: {line}')
        # Print surrounding lines for context
        if i > 0:
            print(f'  Before: {lines[i-1]}')
        if i < len(lines) - 1:
            print(f'  After: {lines[i+1]}')
        print()
