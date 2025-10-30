# Complete Guide: Parsing Payloads Using Metadata JSON

This guide shows you how to use pre-generated metadata JSON files to parse binary payloads for any logcode and version.

## Overview

**The Two-Step Workflow:**

```
┌─────────────────────────────────────┐
│ STEP 1: Generate Metadata (Once)   │
│ ----------------------------------- │
│ ICD PDF → Metadata Generator        │
│         → metadata_<logcode>.json   │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ STEP 2: Parse Payloads (Repeated)  │
│ ----------------------------------- │
│ Hex Payload + Metadata JSON         │
│         → Payload Parser            │
│         → parsed_output.json        │
└─────────────────────────────────────┘
```

## STEP 1: Generate Metadata JSON (One-Time Setup)

### Option A: Single Logcode

```bash
python -m hex_decoder_module.metadata_cli single \
    --logcode 0x1C07 \
    --pdf data/input/icd_document.pdf \
    -o metadata_0x1C07.json \
    --verbose
```

**Output:** `metadata_0x1C07.json` containing:
- All available versions (2, 3, 5, 6, 7, 8)
- Complete field layouts for each version
- Field offsets (byte:bit precision)
- Data types (Uint, Int, Float, Enum)
- Enum value mappings
- Field descriptions

### Option B: Multiple Logcodes

```bash
python -m hex_decoder_module.metadata_cli multi \
    --logcodes "0x1C07,0x1C08,0x1C09" \
    --pdf data/input/icd_document.pdf \
    -o metadata_all_logcodes.json \
    --verbose
```

## STEP 2: Parse Payloads Using Metadata

### Method 1: Python API

```python
from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser

# 1. Initialize parser with metadata file
parser = MetadataPayloadParser('metadata_0x1C07.json')

# 2. Your hex payload (from logs, packets, etc.)
payload_hex = """
02000000   # Version = 2 (32 bits)
64001001   # Sys FN, Sub FN, Slot, SCS
01050000   # Sym Index, Channel Type, ...
00000000   # More fields...
...
"""

# 3. Parse payload
parsed_data = parser.parse_payload(payload_hex)

# 4. Access parsed fields
print(f"Logcode: {parsed_data['logcode_id']}")
print(f"Version: {parsed_data['version']['value']}")

for field_name, field_data in parsed_data['fields'].items():
    print(f"{field_name}: {field_data['raw']}")
    if 'enum' in field_data:
        print(f"  → {field_data['enum']}")

# 5. Save to JSON file
parser.save_parsed_output(parsed_data, 'parsed_output.json')
```

### Method 2: Convenience Function

```python
from hex_decoder_module.metadata_payload_parser import parse_payload_from_metadata

# One-line parsing + saving
result = parse_payload_from_metadata(
    metadata_file='metadata_0x1C07.json',
    payload_hex='02000000640010010105...',
    output_file='parsed_output.json',
    verbose=True
)
```

### Method 3: Command Line

```bash
python hex_decoder_module/metadata_payload_parser.py \
    metadata_0x1C07.json \
    "02000000640010010105..." \
    parsed_output.json
```

### Method 4: Parse from Hex File

```bash
# Save hex payload to file
echo "02000000640010010105..." > payload.hex

# Parse from file
python -c "
from hex_decoder_module.metadata_payload_parser import parse_payload_from_metadata
with open('payload.hex') as f:
    payload = f.read().strip()
parse_payload_from_metadata('metadata_0x1C07.json', payload, 'output.json', verbose=True)
"
```

## Parsed Output Format

The parser generates a JSON file with this structure:

```json
{
  "logcode_id": "0X1C07",
  "logcode_name": "NR5G Sub6 TxAGC",
  "version": {
    "value": 2,
    "table": "4-4"
  },
  "fields": {
    "Version": {
      "raw": 2,
      "type": "Uint32",
      "value": 2
    },
    "Sys FN": {
      "raw": 100,
      "type": "Uint16",
      "value": 100,
      "description": "Sysframe Number, range [0 to 1023]"
    },
    "SCS": {
      "raw": 1,
      "type": "Enumeration",
      "value": 1,
      "enum": "30",
      "description": "Numerology or SCS..."
    },
    "Channel Type": {
      "raw": 0,
      "type": "Enumeration",
      "value": 0,
      "enum": "PUCCH",
      "description": "..."
    }
  },
  "metadata": {
    "payload_size_bytes": 49,
    "fields_parsed": 26
  }
}
```

### Field Structure

Each field contains:
- **`raw`**: Raw integer value extracted from payload
- **`type`**: Data type (Uint32, Int16, Float32, Enumeration, etc.)
- **`value`**: Converted value (handles signed integers, floats)
- **`enum`**: Friendly enum name (if field is an enumeration)
- **`description`**: Field description from ICD (if available)

## Complete Example

### Step-by-Step Walkthrough

```python
# ============================================
# STEP 1: Generate Metadata (Run Once)
# ============================================
import subprocess

subprocess.run([
    'python', '-m', 'hex_decoder_module.metadata_cli',
    'single',
    '--logcode', '0x1C07',
    '--pdf', 'data/input/icd.pdf',
    '-o', 'metadata_0x1C07.json'
])

# ============================================
# STEP 2: Parse Payloads (Run Many Times)
# ============================================
from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser

# Initialize parser
parser = MetadataPayloadParser('metadata_0x1C07.json')

# Example: Parse multiple payloads from log file
payloads = [
    "02000000640010010105...",  # Payload 1
    "02000000660010010205...",  # Payload 2
    "03000000680010010305...",  # Payload 3 (different version)
]

for i, payload_hex in enumerate(payloads, 1):
    print(f"\nParsing payload {i}...")

    # Parse
    parsed = parser.parse_payload(payload_hex)

    # Display key info
    print(f"  Version: {parsed['version']['value']}")
    print(f"  Sys FN: {parsed['fields']['Sys FN']['raw']}")
    print(f"  Channel Type: {parsed['fields']['Channel Type']['enum']}")

    # Save to file
    parser.save_parsed_output(parsed, f'parsed_payload_{i}.json')
```

## Batch Processing Example

```python
from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser
import json

# Load parser
parser = MetadataPayloadParser('metadata_0x1C07.json')

# Read payloads from log file
with open('logfile.hex', 'r') as f:
    payloads = [line.strip() for line in f if line.strip()]

# Parse all payloads
results = []
for i, payload in enumerate(payloads, 1):
    try:
        parsed = parser.parse_payload(payload)
        results.append({
            'id': i,
            'version': parsed['version']['value'],
            'sys_fn': parsed['fields']['Sys FN']['raw'],
            'status': 'success'
        })
    except Exception as e:
        results.append({
            'id': i,
            'error': str(e),
            'status': 'failed'
        })

# Save summary
with open('batch_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Processed {len(payloads)} payloads")
print(f"Success: {sum(1 for r in results if r['status'] == 'success')}")
print(f"Failed: {sum(1 for r in results if r['status'] == 'failed')}")
```

## Supported Data Types

The parser handles all ICD data types:

| Type | Description | Example |
|------|-------------|---------|
| **Uint8/16/32** | Unsigned integers | 0, 255, 65535 |
| **Int16** | Signed integers | -32768 to 32767 |
| **Float32** | IEEE 754 floats | 3.14159 |
| **Enumeration** | Enum with mappings | 1 → "30 KHz" |
| **Bool** | Boolean (0/1) | True/False |

### Special Handling

- **Bit-level offsets**: Fields can start at any bit (e.g., byte 5, bit 2)
- **Signed integers**: Automatic two's complement conversion
- **Float32**: IEEE 754 bit pattern to float conversion
- **Enumerations**: Raw value + friendly name

## Performance

- **Metadata Generation**: ~5 seconds per logcode (one-time)
- **Payload Parsing**: <1ms per payload (using metadata)

**Benefits of metadata-based parsing:**
- No PDF access during parsing
- 1000x faster than parsing PDF each time
- Portable metadata files
- Easy integration with other tools

## Multi-Logcode Metadata

If you generated metadata for multiple logcodes:

```python
parser = MetadataPayloadParser('metadata_all_logcodes.json')

# Must specify logcode_id for multi-logcode metadata
parsed = parser.parse_payload(
    payload_hex="02000000...",
    logcode_id="0x1C07"
)
```

## Error Handling

```python
from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser

parser = MetadataPayloadParser('metadata_0x1C07.json')

try:
    parsed = parser.parse_payload(payload_hex)

    # Check for field-level errors
    for field_name, field_data in parsed['fields'].items():
        if 'error' in field_data:
            print(f"Warning: {field_name} failed to parse: {field_data['error']}")

except ValueError as e:
    print(f"Payload parsing failed: {e}")
```

## Examples Directory

Run the examples:

```bash
# Show workflow and run examples
python hex_decoder_module/example_payload_parsing.py

# Or run individual examples
cd hex_decoder_module
python example_payload_parsing.py
```

## Integration with Existing Tools

### Use with pandas

```python
import pandas as pd
from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser

parser = MetadataPayloadParser('metadata_0x1C07.json')

# Parse multiple payloads
records = []
for payload in payloads:
    parsed = parser.parse_payload(payload)
    record = {
        'version': parsed['version']['value'],
        'sys_fn': parsed['fields']['Sys FN']['raw'],
        'channel_type': parsed['fields']['Channel Type']['enum']
    }
    records.append(record)

# Create DataFrame
df = pd.DataFrame(records)
print(df.describe())
```

### Use with streaming data

```python
from hex_decoder_module.metadata_payload_parser import MetadataPayloadParser
import queue

parser = MetadataPayloadParser('metadata_0x1C07.json')
payload_queue = queue.Queue()

while True:
    payload = payload_queue.get()
    parsed = parser.parse_payload(payload)
    # Process parsed data...
```

## Troubleshooting

### "Version X not found"
- Check which versions are available in metadata
- Generate metadata with the correct ICD version

### "Payload too short"
- Ensure complete payload (not truncated)
- Check minimum size for the logcode/version

### "Field extends beyond payload"
- Payload is shorter than expected
- May indicate truncated or corrupted data

## Files Reference

| File | Purpose |
|------|---------|
| `metadata_cli.py` | CLI for generating metadata |
| `metadata_generator.py` | Core metadata generation logic |
| `metadata_payload_parser.py` | Payload parser using metadata |
| `example_payload_parsing.py` | Usage examples |
| `METADATA_GENERATION.md` | Metadata generation guide |
| `PAYLOAD_PARSING_GUIDE.md` | This guide |

## Summary

1. **Generate metadata once** from ICD PDF
2. **Use metadata repeatedly** to parse payloads
3. **No PDF access needed** during parsing
4. **Fast, portable, easy to integrate**

For more details:
- Metadata generation: See `METADATA_GENERATION.md`
- Examples: Run `example_payload_parsing.py`
- API reference: See docstrings in `metadata_payload_parser.py`
