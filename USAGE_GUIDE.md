# Payload Parser - Usage Guide

## Two-Step Process

### Step 1: Generate Metadata (One-time per logcode)
### Step 2: Parse Payloads (Use metadata repeatedly)

---

## STEP 1: Generate Metadata from PDF

**Command:**
```bash
python -m hex_decoder_module.metadata_cli single --logcode LOGCODE_ID --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_LOGCODE_ID.json -v
```

**Example:**
```bash
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v
```

**Output:**
- Creates `metadata_0xB888.json` file
- Contains all version layouts and table structures
- Only need to generate once per logcode

---

## STEP 2: Parse Payload with Metadata

### Create Hex Input File

Save your payload as `my_payload.hex`:

```
Length:     176
Header:     B0 00 88 B8 94 1A 8F DF 16 26 09 01
Payload:     01 00 03 00 73 5D 74 01 C0 26 03 60
      77 5D 78 5D 79 5D 7A 5D 00 00 01 00
      E1 8D 64 00 52 0A 02 00 16 08 02 00
      3C 02 00 00 83 0C 00 00 85 04 00 00
      2A 00 00 00 8B 33 B5 03 00 00 00 00
      A5 E3 58 00 00 00 00 00 30 17 0E 04
      00 00 00 00 A3 C8 49 00 00 00 00 00
      5E BD 5C 00 00 00 00 00 01 00 01 00
      B5 07 00 00 0B 00 00 00 07 00 00 00
      04 00 00 00 04 00 00 00 00 00 00 00
      00 00 00 00 4C 53 02 00 00 00 00 00
      38 C0 01 00 00 00 00 00 84 13 04 00
      00 00 00 00 C7 05 00 00 00 00 00 00
      38 C0 01 00 00 00 00 00
```

**Note:** Spacing/formatting is automatically handled!

### Parse the Payload

**Command:**
```bash
python parse_payload_from_file.py -i INPUT.hex -m METADATA.json -o OUTPUT.json -v
```

**Example:**
```bash
python parse_payload_from_file.py -i my_payload.hex -m metadata_0xB888.json -o parsed_output.json -v
```

---

## Complete Workflow

### For Logcode 0xB888

```bash
# Step 1: Generate metadata (one-time)
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v

# Step 2: Create hex input file
notepad my_payload.hex
# (paste your payload data and save)

# Step 3: Parse payload
python parse_payload_from_file.py -i my_payload.hex -m metadata_0xB888.json -o output.json -v

# Step 4: View results
type output.json
```

### For Multiple Payloads (Same Logcode)

```bash
# Step 1: Generate metadata once
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v

# Step 2: Parse multiple payloads (reuse metadata)
python parse_payload_from_file.py -i payload1.hex -m metadata_0xB888.json -o output1.json -v
python parse_payload_from_file.py -i payload2.hex -m metadata_0xB888.json -o output2.json -v
python parse_payload_from_file.py -i payload3.hex -m metadata_0xB888.json -o output3.json -v
```

---

## Command Reference

### Metadata Generation

```bash
python -m hex_decoder_module.metadata_cli single \
  --logcode LOGCODE_ID \
  --pdf PDF_PATH \
  -o OUTPUT_FILE.json \
  -v
```

**Options:**
- `--logcode` or `-l`: Logcode hex ID (e.g., 0xB888)
- `--pdf` or `-p`: Path to ICD PDF file
- `-o` or `--output`: Output metadata JSON file
- `-v` or `--verbose`: Show detailed progress
- `--no-cache`: Disable caching (slower)
- `--compact`: Generate compact JSON

### Payload Parsing

```bash
python parse_payload_from_file.py \
  -i INPUT.hex \
  -m METADATA.json \
  -o OUTPUT.json \
  -v
```

**Options:**
- `-i` or `--input`: Input hex file path
- `-m` or `--metadata`: Metadata JSON file path
- `-o` or `--output`: Output JSON file path
- `-v` or `--verbose`: Show detailed output

---

## Batch Processing

### Generate Metadata for Multiple Logcodes

```bash
# Option 1: One at a time
python -m hex_decoder_module.metadata_cli single -l 0xB888 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v
python -m hex_decoder_module.metadata_cli single -l 0x1C07 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0x1C07.json -v

# Option 2: Multiple logcodes in one file
python -m hex_decoder_module.metadata_cli multi --logcodes "0xB888,0x1C07,0x1C08" --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_multi.json -v
```

### Parse Multiple Payloads

```bash
# Windows CMD
for %f in (*.hex) do python parse_payload_from_file.py -i %f -m metadata_0xB888.json -o parsed_%f.json

# PowerShell
Get-ChildItem *.hex | ForEach-Object { python parse_payload_from_file.py -i $_.Name -m metadata_0xB888.json -o "parsed_$($_.Name).json" }

# Git Bash
for file in *.hex; do python parse_payload_from_file.py -i "$file" -m metadata_0xB888.json -o "parsed_${file}"; done
```

---

## Input File Format

Your hex input file must have:

### Required Sections

**Header:**
```
Header:     B0 00 88 B8 94 1A 8F DF 16 26 09 01
```

**Payload:**
```
Payload:     01 00 03 00 73 5D 74 01 C0 26 03 60
      77 5D 78 5D 79 5D 7A 5D 00 00 01 00
```

### Optional Section

**Length:**
```
Length:     176
```

### Spacing Examples (All Valid!)

**Compact:**
```
Payload: 010003007 35D7401C0260360
```

**Spaced:**
```
Payload: 01 00 03 00 73 5D 74 01 C0 26 03 60
```

**Multi-line with indentation:**
```
Payload: 01 00 03 00 73 5D 74 01 C0 26 03 60
         77 5D 78 5D 79 5D 7A 5D 00 00 01 00
         E1 8D 64 00 52 0A 02 00 16 08 02 00
```

---

## Example Output

```
============================================================
SUCCESS!
============================================================
Output saved to: output.json

Records decoded:
  Record 0: 13 fields
  Record 1: 13 fields
============================================================
```

**JSON Output:**
```json
{
  "logcode_id": "0XB888",
  "logcode_name": "NR5G MAC PDSCH Stats",
  "version": {
    "value": 196609,
    "value_hex": "0x00030001",
    "table": "7-2804"
  },
  "fields": {
    "Num Records": {"raw": 1, "type": "Uint8", "value": 1},
    "Carrier ID (Record 0)": {"raw": 0, "type": "Uint32", "value": 0},
    "Numerology (Record 0)": {"raw": 1, "type": "Enumeration", "value": 1, "decoded": "30KHZ"},
    ...
  }
}
```

---

## Examples for Different Logcodes

### 0xB888 (MAC PDSCH Stats)

```bash
# Step 1: Generate metadata
python -m hex_decoder_module.metadata_cli single -l 0xB888 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v

# Step 2: Parse payload
python parse_payload_from_file.py -i payload_b888.hex -m metadata_0xB888.json -o output_b888.json -v
```

### 0x1C07 (RF TxAGC)

```bash
# Step 1: Generate metadata
python -m hex_decoder_module.metadata_cli single -l 0x1C07 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0x1C07.json -v

# Step 2: Parse payload
python parse_payload_from_file.py -i payload_1c07.hex -m metadata_0x1C07.json -o output_1c07.json -v
```

### 0x1C08 (RF RxAGC)

```bash
# Step 1: Generate metadata
python -m hex_decoder_module.metadata_cli single -l 0x1C08 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0x1C08.json -v

# Step 2: Parse payload
python parse_payload_from_file.py -i payload_1c08.hex -m metadata_0x1C08.json -o output_1c08.json -v
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Input file not found" | Check file path exists |
| "Metadata file not found" | Run Step 1 to generate metadata first |
| "Could not find Payload" | Add "Payload:" line to hex file |
| "Version not found" | Regenerate metadata with `--force` |
| Wrong values | Verify hex data in input file |

---

## File Organization

```
log_parser_project/
├── metadata_0xB888.json          # Generated metadata files
├── metadata_0x1C07.json
├── payload1.hex                  # Your hex input files
├── payload2.hex
├── output1.json                  # Parsed output files
├── output2.json
└── parse_payload_from_file.py    # Payload parser script
```

---

## Summary

**Two separate steps:**

1. **Generate metadata** (one-time per logcode)
   ```bash
   python -m hex_decoder_module.metadata_cli single -l LOGCODE -p PDF_PATH -o metadata.json -v
   ```

2. **Parse payloads** (use metadata repeatedly)
   ```bash
   python parse_payload_from_file.py -i payload.hex -m metadata.json -o output.json -v
   ```

**That's it!**
