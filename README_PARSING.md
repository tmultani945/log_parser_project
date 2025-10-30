# Corrected Payload Parser - README

## Overview

This system has **TWO SEPARATE STEPS**:

1. **Generate Metadata** from ICD PDF (one-time per logcode)
2. **Parse Payloads** using the metadata (reuse for many payloads)

---

## ✅ What Was Fixed

1. **Metadata Generation** - Now preserves raw table structure with repeating records
2. **Payload Parser** - Correctly handles multiple records (Records arrays)
3. **Hex Input** - Accepts files with flexible spacing (like hex_decoder_module.cli)

---

## 🚀 Quick Start

### Step 1: Generate Metadata

```bash
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v
```

### Step 2: Create Hex Input File (`my_payload.hex`)

```
Header:     B0 00 88 B8 94 1A 8F DF 16 26 09 01
Payload:     01 00 03 00 73 5D 74 01 C0 26 03 60
      77 5D 78 5D 79 5D 7A 5D 00 00 01 00
      E1 8D 64 00 52 0A 02 00 16 08 02 00
      (paste your hex data - spacing doesn't matter)
```

### Step 3: Parse Payload

```bash
python parse_payload_from_file.py -i my_payload.hex -m metadata_0xB888.json -o output.json -v
```

---

## 📋 Command Reference

### Generate Metadata (Step 1)

```bash
python -m hex_decoder_module.metadata_cli single \
  --logcode LOGCODE_ID \
  --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" \
  -o metadata_LOGCODE_ID.json \
  -v
```

### Parse Payload (Step 2)

```bash
python parse_payload_from_file.py \
  -i INPUT.hex \
  -m METADATA.json \
  -o OUTPUT.json \
  -v
```

---

## 📝 Examples

### Example 1: Single Payload

```bash
# Generate metadata
python -m hex_decoder_module.metadata_cli single -l 0xB888 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v

# Parse payload
python parse_payload_from_file.py -i payload.hex -m metadata_0xB888.json -o output.json -v
```

### Example 2: Multiple Payloads (Same Logcode)

```bash
# Generate metadata once
python -m hex_decoder_module.metadata_cli single -l 0xB888 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v

# Parse many payloads
python parse_payload_from_file.py -i payload1.hex -m metadata_0xB888.json -o output1.json -v
python parse_payload_from_file.py -i payload2.hex -m metadata_0xB888.json -o output2.json -v
python parse_payload_from_file.py -i payload3.hex -m metadata_0xB888.json -o output3.json -v
```

### Example 3: Batch Processing

```bash
# Generate metadata
python -m hex_decoder_module.metadata_cli single -l 0xB888 -p "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v

# Process all .hex files
for %f in (*.hex) do python parse_payload_from_file.py -i %f -m metadata_0xB888.json -o parsed_%f.json
```

---

## 📂 Files

| File | Description |
|------|-------------|
| `parse_payload_from_file.py` | Payload parser script |
| `example_payload_b888.hex` | Example hex input file |
| `COMMANDS.txt` | Quick command reference |
| `USAGE_GUIDE.md` | Detailed usage guide |
| `PARSER_CORRECTIONS_SUMMARY.md` | Technical details about fixes |

---

## ✨ Key Features

✅ **Two separate steps** - Generate metadata once, parse many times
✅ **Flexible hex input** - Any spacing/formatting in hex files works
✅ **Repeating structures** - Correctly decodes multiple records
✅ **Cached metadata** - Fast parsing after metadata generation
✅ **Clean output** - JSON with all fields properly decoded

---

## 🎯 Verification

Tested with 0xB888 payload:
- ✅ Version: 196609 (0x00030001)
- ✅ All header fields correct
- ✅ Record 0: 13 fields, all values correct
- ✅ Record 1: 13 fields, all values correct
- ✅ Total: 33 fields parsed successfully

---

## 📚 Documentation

- **COMMANDS.txt** - Copy-paste ready commands
- **USAGE_GUIDE.md** - Complete usage guide with examples
- **PARSER_CORRECTIONS_SUMMARY.md** - Technical details

---

## Summary

**Two simple commands:**

```bash
# 1. Generate metadata (once per logcode)
python -m hex_decoder_module.metadata_cli single -l LOGCODE -p PDF_PATH -o metadata.json -v

# 2. Parse payload (reuse metadata)
python parse_payload_from_file.py -i payload.hex -m metadata.json -o output.json -v
```

**That's it!**
