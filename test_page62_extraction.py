import sys
sys.path.insert(0, 'src')
import pdfplumber

pdf_path = 'data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf'

with pdfplumber.open(pdf_path) as pdf:
    # Check pages 61-62 (indices 60-61)
    for page_idx in [60, 61]:
        print(f'\n{"="*60}')
        print(f'PAGE {page_idx + 1}')
        print("="*60)

        page = pdf.pages[page_idx]

        # Extract text to see captions
        text = page.extract_text()
        lines = text.split('\n') if text else []

        print('\n--- Text lines with "Table" ---')
        for i, line in enumerate(lines):
            if 'Table' in line and '4-16' in line:
                print(f'{i}: {line}')

        # Extract tables
        tables = page.extract_tables()
        print(f'\n--- pdfplumber found {len(tables)} tables ---')

        for i, table in enumerate(tables):
            if table and len(table) >= 2:
                print(f'\nTable {i+1}:')
                print(f'  Headers: {table[0][:6]}')  # First 6 columns
                print(f'  Rows: {len(table)-1}')
                print(f'  First data row: {table[1][:3] if len(table) > 1 else "N/A"}')
