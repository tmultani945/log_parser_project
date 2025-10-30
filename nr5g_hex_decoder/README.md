# NR5G Hex Decoder

A comprehensive Python toolkit for decoding NR5G hexadecimal log packets using ICD (Interface Control Document) PDF files.

## Overview

This module provides a complete two-step workflow for decoding NR5G log packets:

**Step 1: Generate Metadata** (One-time per logcode)
- Extracts logcode structure from ICD PDF
- Generates reusable metadata JSON file
- Supports all versions and dependencies

**Step 2: Parse Payload** (Multiple times with same metadata)
- Decodes hex payloads using pre-generated metadata
- Fast, efficient parsing without PDF overhead
- Exports to structured JSON

## Key Features

- **Two-Step Workflow**: Separate metadata generation from payload decoding for efficiency
- **On-Demand PDF Parsing**: No preprocessing required - directly parse ICD sections as needed
- **Smart Caching**: In-memory LRU cache for parsed logcode data
- **Automatic Version Resolution**: Detects and uses correct version-specific field layouts
- **Dependency Resolution**: Automatically extracts referenced tables
- **Robust Error Handling**: Structured exceptions with detailed error information
- **Clean JSON Export**: Both raw and human-readable field values

## Quick Start

### Installation

```bash
# Install required dependencies
pip install pdfplumber PyMuPDF

# Or use requirements.txt (if provided)
pip install -r requirements.txt
```

### Basic Usage

#### Step 1: Generate Metadata (One-time)

```bash
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" -o metadata_0xB888.json -v

```

#### Step 2: Parse Payload (Multiple times)

```bash
python scripts/parse_payload.py -i my_payload.hex -m metadata_0xB888.json -o output.json -v

```

## File Identification

### Files Used in the Workflow

#### Command 1: Metadata Generation
```bash
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "data/input/ICD.pdf" -o metadata_0xB888.json -v
```

**Files involved:**
1. `hex_decoder_module/metadata_cli.py` - CLI script for metadata generation
2. `hex_decoder_module/export/metadata_generator.py` - Core metadata generation logic
3. `hex_decoder_module/icd_parser/` - PDF parsing modules
4. `data/input/ICD.pdf` - Input ICD PDF document (user-provided)
5. `metadata_0xB888.json` - Output metadata file (generated)

#### Command 2: Payload Parsing
```bash
python scripts/parse_payload.py -i my_payload.hex -m metadata_0xB888.json -o output.json -v
```

**Files involved:**
1. `scripts/parse_payload.py` - CLI script for payload parsing
2. `hex_decoder_module/metadata_payload_parser.py` - Metadata-based payload parser
3. `hex_decoder_module/decoder/` - Field decoding modules
4. `my_payload.hex` - Input hex payload file (user-provided)
5. `metadata_0xB888.json` - Metadata file from Step 1
6. `output.json` - Decoded output file (generated)

### Core Module Files

```
hex_decoder_module/
├── metadata_cli.py              # Step 1 entry point
├── metadata_payload_parser.py   # Step 2 parsing logic
├── cli.py                       # Alternative single-step CLI
├── models/                      # Data structures
│   ├── packet.py                # ParsedPacket, Header
│   ├── icd.py                   # ICD metadata structures
│   ├── decoded.py               # DecodedPacket, DecodedField
│   └── errors.py                # Exception classes
├── utils/                       # Helper functions
│   ├── byte_ops.py              # Byte manipulation
│   ├── type_converters.py       # Type-specific decoders
│   └── enum_mapper.py           # Enum mapping utilities
├── ingest/                      # Input parsing
│   ├── hex_parser.py            # Hex string parser
│   └── validators.py            # Input validation
├── icd_parser/                  # PDF parsing
│   ├── pdf_scanner.py           # Find logcode in PDF
│   ├── section_extractor.py     # Extract tables
│   ├── table_parser.py          # Parse table to FieldDefinitions
│   ├── version_parser.py        # Parse version mappings
│   ├── dependency_resolver.py   # Resolve table references
│   ├── cache.py                 # LRU cache
│   └── icd_query.py             # Query API
├── decoder/                     # Field decoding
│   ├── header_decoder.py        # Decode header
│   ├── version_resolver.py      # Resolve version
│   ├── field_decoder.py         # Decode individual fields
│   ├── field_post_processor.py  # Post-process decoded values
│   └── payload_decoder.py       # Main orchestrator
└── export/                      # JSON output
    ├── metadata_generator.py    # Generate metadata JSON
    ├── json_builder.py          # Build JSON structure
    └── file_writer.py           # Write to disk
```

## Project Structure

```
nr5g_hex_decoder/
├── README.md                    # This file
├── QUICKSTART.md                # Quick start guide
├── USER_GUIDE.md                # Detailed user guide
├── requirements.txt             # Python dependencies
│
├── examples/                    # Example files
│   ├── README.md                # Examples documentation
│   ├── sample_payload.hex       # Sample hex input
│   ├── metadata_0xB888.json     # Sample metadata output
│   └── end_to_end_example.sh    # Complete workflow script
│
├── data/                        # Data directory
│   ├── input/                   # Place your ICD PDFs here
│   ├── metadata/                # Generated metadata files
│   └── output/                  # Decoded output files
│
├── hex_decoder_module/          # Core decoder module
│   ├── metadata_cli.py          # Step 1: Metadata generation CLI
│   ├── metadata_payload_parser.py  # Metadata-based parser
│   ├── cli.py                   # Alternative single-step CLI
│   ├── models/                  # Data structures
│   ├── utils/                   # Helper utilities
│   ├── ingest/                  # Input parsing
│   ├── icd_parser/              # PDF parsing
│   ├── decoder/                 # Field decoding
│   └── export/                  # JSON export
│
└── scripts/                     # Helper scripts
    └── parse_payload.py         # Step 2: Parse payload from file
```

## Input File Formats

### Hex Payload Format (my_payload.hex)

```
Length:     176
Header:     B0 00 88 B8 94 1A 8F DF 16 26 09 01
Payload:    01 00 03 00 73 5D 74 01 C0 26 03 60
            77 5D 78 5D 79 5D 7A 5D 00 00 01 00
            E1 8D 64 00 52 0A 02 00 16 08 02 00
            ...
```

**Format specifications:**
- `Length:` Total packet length in bytes
- `Header:` 12-byte header (space-separated hex bytes)
- `Payload:` Payload data (space-separated hex bytes, multi-line supported)
- Whitespace in payload is automatically handled

## Output Format

### Metadata File (metadata_0xB888.json)

Contains comprehensive logcode structure:
- Logcode ID and name
- All available versions
- Field layouts for each version
- Table dependencies
- Field types, offsets, and lengths

**Example structure:**
```json
{
  "logcode_id": "0xB888",
  "logcode_name": "NR5G ML1 Serving Cell Measurement",
  "versions": {
    "1": {
      "table_number": "4-4",
      "fields": [...]
    }
  },
  "all_tables": {...}
}
```

### Decoded Output (output.json)

Clean, structured representation of decoded packet:

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
  },
  "metadata": {
    "total_fields": 42,
    "decode_time_ms": 15.23
  }
}
```

## Common Logcodes

Here are some commonly used NR5G logcodes:

| Logcode | Name | Description |
|---------|------|-------------|
| 0xB888 | NR5G ML1 Serving Cell Measurement | Cell measurement data |
| 0xB889 | NR5G ML1 Neighbor Cell Measurement | Neighbor cell info |
| 0x1C07 | NR5G RRC Serving Cell Info | RRC serving cell data |

## Performance

### Step 1: Metadata Generation
- **First time**: 3-6 seconds (PDF scan + table extraction)
- **Cached**: ~0.5 seconds (if caching enabled)
- **Memory**: ~5-10 MB per logcode

### Step 2: Payload Parsing
- **With metadata**: ~0.01-0.05 seconds
- **Memory**: Minimal (no PDF loading)
- **Scalability**: Can process thousands of payloads quickly

## Advantages of Two-Step Workflow

1. **Efficiency**: Generate metadata once, use many times
2. **Speed**: Payload parsing is 100x faster without PDF overhead
3. **Portability**: Share metadata files without sharing PDFs
4. **Automation**: Easy to integrate into automated workflows
5. **Debugging**: Inspect metadata to understand field layouts

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[USER_GUIDE.md](USER_GUIDE.md)** - Detailed usage guide
- **[examples/](examples/)** - Working examples and sample data

## Requirements

- Python 3.8 or higher
- pdfplumber 0.10.3+
- PyMuPDF (fitz) 1.23.8+

## Troubleshooting

### "Logcode not found in PDF"
- Verify the PDF contains Section 4 (Log Items)
- Check that the logcode ID is correct (e.g., 0xB888, not B888)
- Use verbose mode `-v` to see scan details

### "Version not found for logcode"
- Check if the logcode has a "_Versions" table in the PDF
- Verify the version field offset/length is correct
- Some logcodes may only have a single version

### "Payload too short"
- Verify the payload length matches the declared length
- Check if hex input file is complete
- Some fields may extend beyond actual payload

### Slow metadata generation
- This is normal - PDF scanning takes 3-6 seconds
- Enable caching (default) to speed up subsequent runs
- Disable cache with `--no-cache` if memory is limited

## Examples

See the [examples/](examples/) directory for:
- Sample hex payload files
- Generated metadata examples
- Decoded output examples
- End-to-end workflow scripts

## Contributing

This module follows these design principles:

1. **Explicit over implicit** - No magic behavior
2. **Fail fast** - Validate at each stage
3. **Structured errors** - Never crash with raw exceptions
4. **Type safety** - Use dataclasses and type hints
5. **Testability** - Each component is independently testable

## License

[Specify your license here]

## Version

1.0.0

## Support

For issues, questions, or contributions, please contact:
[Your contact information]
