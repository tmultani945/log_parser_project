import pdfplumber
import re

pdf_path = r"data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"

# Pattern to detect logcode sections
pattern = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'

sections_found = {}

print("Scanning PDF for all logcode sections...")

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        lines = text.split('\n')
        for line in lines:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                section = match.group(1)
                name = match.group(2).strip()
                logcode = match.group(3).upper()

                # Get major section number (e.g., "4" from "4.1")
                major_section = section.split('.')[0]

                if major_section not in sections_found:
                    sections_found[major_section] = []

                sections_found[major_section].append({
                    'section': section,
                    'name': name,
                    'logcode': logcode,
                    'page': i
                })

        # Progress indicator every 500 pages
        if i % 500 == 0:
            print(f"  Processed {i} pages...")

print(f"\n{'='*80}")
print("SUMMARY OF SECTIONS WITH LOGCODES")
print(f"{'='*80}\n")

for major_section in sorted(sections_found.keys(), key=int):
    logcodes_list = sections_found[major_section]
    print(f"Section {major_section}: {len(logcodes_list)} logcodes found")
    print(f"  First: {logcodes_list[0]['section']} - {logcodes_list[0]['name']} ({logcodes_list[0]['logcode']}) - Page {logcodes_list[0]['page']}")
    print(f"  Last:  {logcodes_list[-1]['section']} - {logcodes_list[-1]['name']} ({logcodes_list[-1]['logcode']}) - Page {logcodes_list[-1]['page']}")
    print()

print(f"\n{'='*80}")
print("DETAILED LIST")
print(f"{'='*80}\n")

for major_section in sorted(sections_found.keys(), key=int):
    print(f"\n=== SECTION {major_section} ===\n")
    for item in sections_found[major_section]:
        print(f"  {item['section']:8} {item['logcode']:8} {item['name']:50} Page {item['page']}")

print(f"\n\nTotal sections with logcodes: {len(sections_found)}")
print(f"Total logcodes found: {sum(len(v) for v in sections_found.values())}")
