# Hex Decoder Module

A Python module for decoding hexadecimal log packets using ICD (Interface Control Document) PDF files with on-demand parsing.

## Features

- **On-Demand PDF Parsing**: No preprocessing required - directly parse ICD sections as needed
- **Smart Caching**: In-memory LRU cache for parsed logcode data
- **Automatic Version Resolution**: Detects and uses correct version-specific field layouts
- **Dependency Resolution**: Automatically extracts referenced tables
- **Robust Error Handling**: Structured exceptions with detailed error information
- **JSON Export**: Clean, structured JSON output with both raw and friendly values

## Architecture

The module uses a 5-layer modular design:

1. **Ingest Layer** (`ingest/`) - Parse raw hex input
2. **ICD Parser Layer** (`icd_parser/`) - Extract logcode metadata from PDF
3. **Decoder Layer** (`decoder/`) - Decode packet fields
4. **Export Layer** (`export/`) - Generate JSON output
5. **Models Layer** (`models/`) - Data structures and errors

## Installation

### Requirements

```bash
pip install pdfplumber PyMuPDF
```

Or use the provided requirements file:

```bash
pip install -r requirements.txt
```

### Python Version

- Python 3.8+

## Quick Start

### Command Line Usage

```bash
# Decode a hex packet
python -m hex_decoder_module.cli \
    --input packet.hex \
    --pdf /path/to/ICD.pdf \
    --output decoded.json

# Decode from hex string directly
python -m hex_decoder_module.cli \
    --input "Length: 61\nHeader: 3D 00 23 B8...\nPayload: ..." \
    --pdf ICD.pdf \
    --output decoded.json

# Disable caching (uses less memory)
python -m hex_decoder_module.cli \
    --input packet.hex \
    --pdf ICD.pdf \
    --output decoded.json \
    --no-cache

# Generate compact JSON
python -m hex_decoder_module.cli \
    --input packet.hex \
    --pdf ICD.pdf \
    --output decoded.json \
    --compact
```

### Hex Input Format

The input file should follow this format:

```
Length: 61
Header: 3D 00 23 B8 CD 0F 67 95 F5 A6 06 01
Payload:
02 00 03 00 01 01 00 38 00 3A 00 7D
F1 40 18 30 01 E0 E5 09 00 4A DE 09
00 64 00 64 00 3A 00 7D F1 00 00 00
00 37 01 03 E0 01 00 07 01 18 00 4D
00
```

### Programmatic Usage

```python
from hex_decoder_module import (
    parse_hex_input,
    ICDQueryEngine,
    PayloadDecoder,
    JSONBuilder,
    FileWriter
)

# Parse hex input
hex_input = """
Length: 61
Header: 3D 00 23 B8 CD 0F 67 95 F5 A6 06 01
Payload:
02 00 03 00 01 01 00 38 00 3A 00 7D
...
"""

parsed_packet = parse_hex_input(hex_input)

# Initialize ICD query engine
icd_engine = ICDQueryEngine('/path/to/ICD.pdf', enable_cache=True)

# Decode packet
decoder = PayloadDecoder(icd_engine)
decoded_packet = decoder.decode(parsed_packet)

# Export to JSON
json_builder = JSONBuilder()
json_data = json_builder.build(decoded_packet)

file_writer = FileWriter()
file_writer.write_pretty(json_data, 'output.json')
```

## Output Format

### Full Format

```json
{
  "logcode": {
    "id_hex": "0xB823",
    "id_decimal": 47139,
    "name": "Nr5g_RrcServingCellInfo"
  },
  "version": {
    "raw": "0x30002",
    "resolved_layout": "4-4"
  },
  "header": {
    "length_bytes": 61,
    "sequence": 4045,
    "timestamp_raw": 2791119783
  },
  "fields": {
    "Standby Mode": {
      "type": "Enum",
      "raw": 1,
      "decoded": "SINGLE STANDBY",
      "description": "Device standby mode"
    },
    "Physical Cell ID": {
      "type": "Uint16",
      "raw": 56,
      "description": "Physical cell identifier"
    }
  },
  "metadata": {
    "section": "4.3",
    "total_fields": 15,
    "decode_time_ms": 3245.67,
    "cache_enabled": true,
    "cache_size": 1
  }
}
```

### Compact Format

```json
{
  "logcode": "0xB823",
  "name": "Nr5g_RrcServingCellInfo",
  "version": "0x30002",
  "fields": {
    "Standby Mode": "SINGLE STANDBY",
    "Physical Cell ID": 56,
    "DL Frequency": 648672
  }
}
```

## How It Works

### Data Flow

1. **Hex Input** → Parse hex string into binary bytes
2. **Header Decoding** → Extract logcode ID (e.g., 0xB823)
3. **PDF Scanning** → Search PDF for logcode section (cached if seen before)
4. **Table Extraction** → Extract all tables from the section
5. **Version Resolution** → Read version field from payload
6. **Field Decoding** → Decode each field using ICD definitions
7. **JSON Export** → Generate structured JSON output

### Caching Strategy

- **First decode** (cache miss): ~3-6 seconds (PDF scan + table extraction)
- **Subsequent decodes** (cache hit): ~0.01 seconds (instant)
- **Default cache size**: 50 logcodes
- **Eviction policy**: LRU (Least Recently Used)

## Error Handling

The module provides structured error handling with specific exception types:

```python
from hex_decoder_module.models import (
    MalformedHexError,      # Invalid hex input
    LengthMismatchError,    # Length doesn't match
    LogcodeNotFoundError,   # Logcode not in PDF
    VersionNotFoundError,   # Version not defined
    PayloadTooShortError,   # Payload too short for fields
    FieldDecodingError,     # Field decoding failed
    SectionNotFoundError,   # Section not found in PDF
    PDFScanError           # PDF reading error
)
```

All exceptions include detailed error information and suggestions.

## Supported Field Types

- **Uint8, Uint16, Uint32, Uint64** - Unsigned integers (little-endian)
- **Int8, Int16, Int32, Int64** - Signed integers (two's complement)
- **Bool** - Boolean values (single bit)
- **Enum** - Enumerated values with human-readable mappings
- **String** - Fixed-length or null-terminated strings

## Performance

### Typical Performance

- **First decode** (new logcode): 3-6 seconds
- **Cached decode** (seen logcode): 0.01 seconds
- **Memory usage**: ~5-10 MB per cached logcode
- **PDF size**: Handles 100+ page PDFs efficiently

### Optimization Tips

1. **Enable caching** (default) for repeated decodes
2. **Use compact JSON** for smaller output files
3. **Pre-warm cache** by decoding common logcodes first
4. **Disable verbose mode** in production

## Project Structure

```
hex_decoder_module/
├── __init__.py           # Package exports
├── cli.py                # CLI entry point
├── models/               # Data structures
│   ├── packet.py         # ParsedPacket, Header
│   ├── icd.py            # ICD metadata structures
│   ├── decoded.py        # DecodedPacket, DecodedField
│   └── errors.py         # Exception classes
├── utils/                # Helper functions
│   ├── byte_ops.py       # Byte manipulation
│   ├── type_converters.py # Type-specific decoders
│   └── enum_mapper.py    # Enum mapping utilities
├── ingest/               # Input parsing
│   ├── hex_parser.py     # Hex string parser
│   └── validators.py     # Input validation
├── icd_parser/           # PDF parsing (core feature)
│   ├── pdf_scanner.py    # Find logcode in PDF
│   ├── section_extractor.py # Extract tables
│   ├── table_parser.py   # Parse table → FieldDefinitions
│   ├── version_parser.py # Parse version mappings
│   ├── dependency_resolver.py # Resolve table refs
│   ├── cache.py          # LRU cache
│   └── icd_query.py      # Query API
├── decoder/              # Field decoding
│   ├── header_decoder.py # Decode header
│   ├── version_resolver.py # Resolve version
│   ├── field_decoder.py  # Decode individual fields
│   └── payload_decoder.py # Main orchestrator
└── export/               # JSON output
    ├── json_builder.py   # Build JSON structure
    └── file_writer.py    # Write to disk
```

## Module Isolation

This module is designed to be **completely independent** from the main log parser project:

- **No imports** from `src/` directory
- **No database** required (works directly from PDF)
- **Self-contained** - Can be moved to a separate repository
- **Independent CLI** - Separate entry point

## Limitations

1. **Section 4 Only**: Only parses logcodes from Section 4 (Log Items)
2. **Byte-Aligned Fields**: Assumes fields are byte-aligned (no sub-byte offsets)
3. **Little-Endian**: All multi-byte values are little-endian
4. **Standard Header**: Assumes 12-byte header format
5. **No Cross-Section Dependencies**: Referenced tables must be in same section

## Troubleshooting

### "Logcode not found in PDF"

- Verify the PDF contains Section 4 (Log Items)
- Check that the logcode ID in the header is correct
- Use verbose mode: `--verbose` to see scan details

### "Version not found for logcode"

- Check if the logcode has a "_Versions" table
- Verify the version field offset/length is correct
- Try listing available versions in the PDF

### "Payload too short"

- Verify the payload length matches the declared length
- Check if hex input is complete
- Some fields may extend beyond actual payload

### Slow first decode

- This is normal - PDF scanning takes 3-6 seconds
- Enable caching (default) to speed up subsequent decodes
- Consider pre-warming cache for common logcodes

## Contributing

This module follows these design principles:

1. **Explicit over implicit** - No magic behavior
2. **Fail fast** - Validate at each stage
3. **Structured errors** - Never crash with raw exceptions
4. **Type safety** - Use dataclasses and type hints
5. **Testability** - Each component is independently testable

## License

[Your license here]

## Version

Version 1.0.0

## Contact

[Your contact information]
