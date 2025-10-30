# NR5G Hex Decoder - Module Structure

Complete file listing and organization of the NR5G Hex Decoder module.

## Directory Tree

```
nr5g_hex_decoder/
├── README.md                              # Main documentation
├── QUICKSTART.md                          # Quick start guide
├── USER_GUIDE.md                          # Comprehensive user guide
├── MODULE_STRUCTURE.md                    # This file
├── requirements.txt                       # Python dependencies
│
├── data/                                  # Data directory (user workspace)
│   ├── input/                             # Place ICD PDF files here
│   │   └── .gitkeep
│   ├── metadata/                          # Generated metadata files
│   │   └── .gitkeep
│   └── output/                            # Decoded output files
│       └── .gitkeep
│
├── examples/                              # Examples and sample data
│   ├── README.md                          # Examples documentation
│   ├── sample_payload.hex                 # Sample hex input file
│   ├── metadata_0xB888.json               # Sample metadata file
│   ├── end_to_end_example.sh              # Bash script for complete workflow
│   └── end_to_end_example.bat             # Windows batch script
│
├── scripts/                               # Helper scripts
│   └── parse_payload.py                   # Step 2: Parse payload from file
│
└── hex_decoder_module/                    # Core decoder module
    ├── __init__.py                        # Package initialization
    ├── cli.py                             # Alternative single-step CLI
    ├── metadata_cli.py                    # Step 1: Metadata generation CLI
    ├── metadata_payload_parser.py         # Metadata-based payload parser
    ├── get_version.py                     # Version extraction utility
    ├── parse_with_metadata.py             # Metadata parsing helper
    ├── debug_table.py                     # Debug utility
    ├── example_metadata_generation.py     # Example script
    ├── example_payload_parsing.py         # Example script
    │
    ├── models/                            # Data structures
    │   ├── __init__.py
    │   ├── packet.py                      # ParsedPacket, Header classes
    │   ├── icd.py                         # ICD metadata structures
    │   ├── decoded.py                     # DecodedPacket, DecodedField
    │   └── errors.py                      # Exception classes
    │
    ├── utils/                             # Utility functions
    │   ├── __init__.py
    │   ├── byte_ops.py                    # Byte manipulation functions
    │   ├── type_converters.py             # Type conversion utilities
    │   └── enum_mapper.py                 # Enum mapping utilities
    │
    ├── ingest/                            # Input parsing layer
    │   ├── __init__.py
    │   ├── hex_parser.py                  # Hex string parser
    │   └── validators.py                  # Input validation
    │
    ├── icd_parser/                        # PDF parsing layer
    │   ├── __init__.py
    │   ├── pdf_scanner.py                 # Scan PDF for logcode sections
    │   ├── section_extractor.py           # Extract section tables
    │   ├── table_parser.py                # Parse tables to field definitions
    │   ├── version_parser.py              # Parse version mappings
    │   ├── dependency_resolver.py         # Resolve table dependencies
    │   ├── cache.py                       # LRU cache implementation
    │   └── icd_query.py                   # Query API
    │
    ├── decoder/                           # Field decoding layer
    │   ├── __init__.py
    │   ├── header_decoder.py              # Decode packet header
    │   ├── version_resolver.py            # Resolve version from payload
    │   ├── field_decoder.py               # Decode individual fields
    │   ├── field_post_processor.py        # Post-process decoded values
    │   └── payload_decoder.py             # Main payload decoder orchestrator
    │
    └── export/                            # Export layer
        ├── __init__.py
        ├── metadata_generator.py          # Generate metadata JSON
        ├── json_builder.py                # Build JSON output structure
        └── file_writer.py                 # Write JSON to files
```

## File Categories

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main module documentation with overview and features |
| `QUICKSTART.md` | Quick start guide to get running in 5 minutes |
| `USER_GUIDE.md` | Comprehensive user guide with all features |
| `MODULE_STRUCTURE.md` | This file - complete module organization |
| `examples/README.md` | Examples documentation and usage |

### Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python package dependencies |
| `data/input/.gitkeep` | Git placeholder for input directory |
| `data/metadata/.gitkeep` | Git placeholder for metadata directory |
| `data/output/.gitkeep` | Git placeholder for output directory |

### Sample Data Files

| File | Purpose |
|------|---------|
| `examples/sample_payload.hex` | Sample hex payload for logcode 0xB888 |
| `examples/metadata_0xB888.json` | Sample metadata file for logcode 0xB888 |

### Scripts and Tools

| File | Purpose |
|------|---------|
| `scripts/parse_payload.py` | Step 2 CLI: Parse payload using metadata |
| `examples/end_to_end_example.sh` | Bash script for complete workflow |
| `examples/end_to_end_example.bat` | Windows batch script for complete workflow |
| `hex_decoder_module/metadata_cli.py` | Step 1 CLI: Generate metadata from PDF |
| `hex_decoder_module/cli.py` | Alternative single-step CLI interface |

### Core Module Files

#### Entry Points
- `hex_decoder_module/metadata_cli.py` - Metadata generation CLI (Step 1)
- `hex_decoder_module/metadata_payload_parser.py` - Metadata-based parser (Step 2)
- `hex_decoder_module/cli.py` - Alternative single-step CLI

#### Models (Data Structures)
- `models/packet.py` - Packet and header data structures
- `models/icd.py` - ICD metadata structures
- `models/decoded.py` - Decoded packet structures
- `models/errors.py` - Custom exception classes

#### Utilities
- `utils/byte_ops.py` - Byte manipulation and conversion
- `utils/type_converters.py` - Type-specific converters
- `utils/enum_mapper.py` - Enum value mapping

#### Ingest Layer
- `ingest/hex_parser.py` - Parse hex strings and files
- `ingest/validators.py` - Validate input data

#### ICD Parser Layer
- `icd_parser/pdf_scanner.py` - Scan PDF for logcode sections
- `icd_parser/section_extractor.py` - Extract tables from sections
- `icd_parser/table_parser.py` - Parse tables to field definitions
- `icd_parser/version_parser.py` - Parse version mappings
- `icd_parser/dependency_resolver.py` - Resolve table dependencies
- `icd_parser/cache.py` - LRU caching mechanism
- `icd_parser/icd_query.py` - High-level query interface

#### Decoder Layer
- `decoder/header_decoder.py` - Decode 12-byte packet header
- `decoder/version_resolver.py` - Resolve version from payload
- `decoder/field_decoder.py` - Decode individual fields by type
- `decoder/field_post_processor.py` - Post-process decoded values
- `decoder/payload_decoder.py` - Main decoder orchestrator

#### Export Layer
- `export/metadata_generator.py` - Generate metadata JSON files
- `export/json_builder.py` - Build structured JSON output
- `export/file_writer.py` - Write JSON to disk

## Command Files Mapping

### Files Used in Command 1 (Metadata Generation)

**Command:**
```bash
python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf "ICD.pdf" -o metadata.json -v
```

**Files involved:**
1. **Entry point:** `hex_decoder_module/metadata_cli.py`
2. **Core logic:** `hex_decoder_module/export/metadata_generator.py`
3. **PDF parsing:**
   - `hex_decoder_module/icd_parser/pdf_scanner.py`
   - `hex_decoder_module/icd_parser/section_extractor.py`
   - `hex_decoder_module/icd_parser/table_parser.py`
   - `hex_decoder_module/icd_parser/version_parser.py`
   - `hex_decoder_module/icd_parser/dependency_resolver.py`
4. **Models:**
   - `hex_decoder_module/models/icd.py`
   - `hex_decoder_module/models/errors.py`
5. **Output:**
   - `hex_decoder_module/export/file_writer.py`
   - `hex_decoder_module/export/json_builder.py`

**Input:** ICD PDF file
**Output:** Metadata JSON file

### Files Used in Command 2 (Payload Parsing)

**Command:**
```bash
python scripts/parse_payload.py -i payload.hex -m metadata.json -o output.json -v
```

**Files involved:**
1. **Entry point:** `scripts/parse_payload.py`
2. **Core logic:** `hex_decoder_module/metadata_payload_parser.py`
3. **Hex parsing:**
   - `hex_decoder_module/ingest/hex_parser.py`
   - `hex_decoder_module/ingest/validators.py`
4. **Decoding:**
   - `hex_decoder_module/decoder/header_decoder.py`
   - `hex_decoder_module/decoder/version_resolver.py`
   - `hex_decoder_module/decoder/field_decoder.py`
   - `hex_decoder_module/decoder/field_post_processor.py`
5. **Utilities:**
   - `hex_decoder_module/utils/byte_ops.py`
   - `hex_decoder_module/utils/type_converters.py`
   - `hex_decoder_module/utils/enum_mapper.py`
6. **Models:**
   - `hex_decoder_module/models/packet.py`
   - `hex_decoder_module/models/decoded.py`
   - `hex_decoder_module/models/errors.py`
7. **Output:**
   - `hex_decoder_module/export/json_builder.py`
   - `hex_decoder_module/export/file_writer.py`

**Inputs:** Hex payload file + Metadata JSON file
**Output:** Decoded JSON file

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        STEP 1                               │
│                   Metadata Generation                       │
│                   (One-time per logcode)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ICD PDF ──→ metadata_cli.py ──→ Metadata JSON             │
│                     │                                       │
│                     ├──→ pdf_scanner.py                     │
│                     ├──→ section_extractor.py               │
│                     ├──→ table_parser.py                    │
│                     ├──→ version_parser.py                  │
│                     ├──→ dependency_resolver.py             │
│                     └──→ metadata_generator.py              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Metadata JSON
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        STEP 2                               │
│                    Payload Parsing                          │
│               (Multiple times, fast)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Hex File ──→ parse_payload.py ──→ Decoded JSON            │
│  Metadata ──→        │                                      │
│                      ├──→ hex_parser.py                     │
│                      ├──→ header_decoder.py                 │
│                      ├──→ version_resolver.py               │
│                      ├──→ field_decoder.py                  │
│                      ├──→ field_post_processor.py           │
│                      └──→ json_builder.py                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Directory Purpose

### `/` (Root)
Main documentation and configuration files

### `/data/`
User workspace for organizing input PDFs, metadata, and outputs

### `/data/input/`
Place ICD PDF documents here

### `/data/metadata/`
Store generated metadata JSON files here

### `/data/output/`
Decoded output JSON files are saved here

### `/examples/`
Working examples with sample data and end-to-end scripts

### `/scripts/`
Helper scripts for common operations

### `/hex_decoder_module/`
Core Python module with all decoding functionality

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Place your ICD PDF in:**
   ```
   data/input/YOUR_ICD.pdf
   ```

3. **Run Step 1 (generate metadata):**
   ```bash
   python -m hex_decoder_module.metadata_cli single \
       --logcode 0xB888 \
       --pdf "data/input/YOUR_ICD.pdf" \
       -o data/metadata/metadata_0xB888.json \
       -v
   ```

4. **Run Step 2 (parse payload):**
   ```bash
   python scripts/parse_payload.py \
       -i examples/sample_payload.hex \
       -m data/metadata/metadata_0xB888.json \
       -o data/output/decoded_output.json \
       -v
   ```

## Next Steps

- Read [QUICKSTART.md](QUICKSTART.md) for a 5-minute tutorial
- Review [USER_GUIDE.md](USER_GUIDE.md) for comprehensive documentation
- Explore [examples/](examples/) for sample data and scripts
- Check [README.md](README.md) for module overview

## Support

For questions or issues, please refer to the documentation files or contact support.
