import pdfplumber

pdf_path = r"data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"
page_num = 61  # 1-indexed in pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages in document: {len(pdf.pages)}")
    if page_num <= len(pdf.pages):
        page = pdf.pages[page_num - 1]
        text = page.extract_text()
        print(f"\n=== Page {page_num} ===")
        print(text)

        # Also extract tables
        tables = page.extract_tables()
        if tables:
            print(f"\n=== Tables on page {page_num} ===")
            for i, table in enumerate(tables):
                print(f"\nTable {i+1}:")
                for row in table:
                    print(row)
    else:
        print(f"Page {page_num} not found.")
