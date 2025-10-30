# Quick Start Guide

Get started with NR5G Hex Decoder in 5 minutes.

## Prerequisites

```bash
# Install required Python packages
pip install pdfplumber PyMuPDF
```

**Required files:**
1. ICD PDF document (e.g., `80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf`)
2. Hex payload file (format shown below)

## Step-by-Step Workflow

### Step 1: Generate Metadata (One-time per logcode)

This extracts the logcode structure from your ICD PDF and saves it as a reusable metadata file.

```bash
python -m hex_decoder_module.metadata_cli single \
    --logcode 0xB888 \
    --pdf "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" \
    -o metadata_0xB888.json \
    -v
```

**What it does:**
- Scans the PDF for logcode 0xB888
- Extracts all versions and field layouts
- Resolves table dependencies
- Saves to `metadata_0xB888.json`

**Output:**
```
Generating metadata for logcode: 0xB888
Using ICD PDF: data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf

Summary:
  Logcode: 0xB888 (NR5G ML1 Serving Cell Measurement)
  Versions: 1
  Total tables: 2
```

**Time:** 3-6 seconds (first time), ~0.5 seconds (cached)

### Step 2: Parse Payload (Multiple times)

Now use the metadata to quickly decode hex payloads.

#### Create a hex payload file

Create `my_payload.hex`:
```
Length:     176
Header:     B0 00 88 B8 94 1A 8F DF 16 26 09 01
Payload:    01 00 03 00 73 5D 74 01 C0 26 03 60
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

#### Parse the payload

```bash
python scripts/parse_payload.py \
    -i my_payload.hex \
    -m metadata_0xB888.json \
    -o output.json \
    -v
```

**What it does:**
- Reads hex payload from file
- Loads metadata from Step 1
- Decodes all fields
- Saves to `output.json`

**Output:**
```
Reading hex input from: my_payload.hex
Payload size: 164 bytes
Using metadata: metadata_0xB888.json
Parsing payload...

============================================================
SUCCESS!
============================================================
Output saved to: output.json

Records decoded:
  Record 0: 14 fields
  Record 1: 14 fields
  Record 2: 14 fields
============================================================
```

**Time:** ~0.01-0.05 seconds

### Step 3: View the Results

Open `output.json` to see the decoded data:

```json
{
  "logcode": {
    "id_hex": "0xB888",
    "id_decimal": 47240,
    "name": "NR5G ML1 Serving Cell Measurement"
  },
  "version": {
    "raw": "0x00001",
    "resolved_layout": "4-4"
  },
  "header": {
    "length_bytes": 176,
    "sequence": 176,
    "timestamp_raw": 3752876180
  },
  "fields": {
    "Version": {
      "type": "Uint8",
      "raw": 1,
      "description": "Version number"
    },
    "Record Count": {
      "type": "Uint8",
      "raw": 3,
      "description": "Number of records"
    },
    "Record 0 Timestamp": {
      "type": "Uint32",
      "raw": 24346995,
      "description": "Measurement timestamp"
    }
  }
}
```

## Complete Example with Sample Data

Try the included example:

```bash
# Step 1: Generate metadata (if not already done)
python -m hex_decoder_module.metadata_cli single \
    --logcode 0xB888 \
    --pdf "data/input/YOUR_ICD.pdf" \
    -o data/metadata/metadata_0xB888.json

# Step 2: Parse the sample payload
python scripts/parse_payload.py \
    -i examples/sample_payload.hex \
    -m examples/metadata_0xB888.json \
    -o data/output/decoded_output.json \
    -v
```

## Directory Organization

Organize your files like this:

```
nr5g_hex_decoder/
├── data/
│   ├── input/
│   │   └── ICD_Document.pdf          # Your ICD PDF here
│   ├── metadata/
│   │   └── metadata_0xB888.json      # Generated metadata here
│   └── output/
│       └── decoded_output.json       # Decoded results here
```

## Common Options

### Metadata Generation Options

```bash
# Compact JSON (no formatting, smaller file)
python -m hex_decoder_module.metadata_cli single \
    --logcode 0xB888 \
    --pdf "data/input/ICD.pdf" \
    -o metadata.json \
    --compact

# Disable caching (lower memory usage)
python -m hex_decoder_module.metadata_cli single \
    --logcode 0xB888 \
    --pdf "data/input/ICD.pdf" \
    -o metadata.json \
    --no-cache

# Generate metadata for multiple logcodes
python -m hex_decoder_module.metadata_cli multi \
    --logcodes "0xB888,0xB889,0x1C07" \
    --pdf "data/input/ICD.pdf" \
    -o metadata_all.json \
    -v
```

### Payload Parsing Options

```bash
# Parse without verbose output
python scripts/parse_payload.py \
    -i my_payload.hex \
    -m metadata_0xB888.json \
    -o output.json

# Parse with verbose debugging
python scripts/parse_payload.py \
    -i my_payload.hex \
    -m metadata_0xB888.json \
    -o output.json \
    -v
```

## Next Steps

- **[USER_GUIDE.md](USER_GUIDE.md)** - Detailed documentation on all features
- **[examples/](examples/)** - More examples and sample data
- **[README.md](README.md)** - Complete module documentation

## Troubleshooting Quick Fixes

### Error: "Metadata file not found"
```bash
# Make sure you ran Step 1 first
ls metadata_0xB888.json
```

### Error: "Logcode not found in PDF"
```bash
# Check your logcode format (must include 0x prefix)
# Correct: 0xB888
# Wrong: B888
```

### Error: "Input file not found"
```bash
# Verify your hex file path
ls my_payload.hex
```

## Performance Tips

1. **Generate metadata once** - Reuse for all payloads with same logcode
2. **Use compact format** - Add `--compact` for smaller metadata files
3. **Batch processing** - Parse multiple payloads using the same metadata
4. **Cache enabled** - Keep caching on (default) for faster repeated runs

## Command Summary

```bash
# STEP 1: Generate metadata (one-time)
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "ICD.pdf" -o metadata.json -v

# STEP 2: Parse payload (multiple times)
python scripts/parse_payload.py -i payload.hex -m metadata.json -o output.json -v
```

That's it! You're now ready to decode NR5G hex packets.
