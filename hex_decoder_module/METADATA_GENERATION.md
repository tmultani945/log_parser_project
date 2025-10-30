# ICD Metadata Generation

## Overview

The metadata generation feature creates comprehensive JSON files from ICD PDF documents. These JSON files contain all version information and dependent table structures for logcodes, enabling fast payload decoding without repeated PDF parsing.

## Why Use Metadata Generation?

**Benefits:**
- **Fast Decoding**: Pre-computed metadata eliminates PDF parsing overhead
- **Complete Information**: All versions and dependencies are fully expanded
- **Portable**: JSON metadata can be distributed without the PDF
- **Cached Results**: Generate once, use many times
- **Version Tracking**: See all available versions for a logcode at a glance

**Use Cases:**
- Real-time payload decoding in production systems
- Batch processing of log files
- Offline analysis without PDF access
- API services that decode log packets
- Documentation and reference generation

## Architecture

### How It Works

```
ICD PDF → MetadataGenerator → JSON Metadata File
                ↓
        ICDQueryEngine
                ↓
    ┌───────────────────────┐
    │ 1. Find logcode       │
    │ 2. Extract tables     │
    │ 3. Parse versions     │
    │ 4. Resolve deps       │
    │ 5. Expand fields      │
    └───────────────────────┘
```

### Key Components

1. **MetadataGenerator** (`export/metadata_generator.py`)
   - High-level API for metadata generation
   - Handles single and multiple logcodes
   - Manages caching and error handling

2. **ICDQueryEngine** (existing)
   - PDF scanning and table extraction
   - Version parsing and dependency resolution
   - Field expansion with offset adjustment

3. **CLI Interface** (`metadata_cli.py`)
   - Command-line tool for generation
   - Supports single and batch processing
   - Progress reporting and error handling

## Usage

### Command-Line Interface

#### Generate metadata for a single logcode

```bash
python -m hex_decoder_module.metadata_cli single \
    --logcode 0x1C07 \
    --pdf icd_document.pdf \
    -o metadata_1c07.json
```

#### Generate metadata for multiple logcodes (comma-separated)

```bash
python -m hex_decoder_module.metadata_cli multi \
    --logcodes "0x1C07,0x1C08,0x1C09" \
    --pdf icd_document.pdf \
    -o metadata.json
```

#### Generate metadata from file (one logcode per line)

```bash
# Create logcodes.txt:
# 0x1C07
# 0x1C08
# 0x1C09

python -m hex_decoder_module.metadata_cli multi \
    --logcodes logcodes.txt \
    --pdf icd_document.pdf \
    -o metadata.json \
    --verbose
```

#### CLI Options

- `--no-cache`: Disable caching (lower memory usage, slower)
- `--compact`: Generate compact JSON (no formatting)
- `--verbose`, `-v`: Show detailed progress information

### Python API

#### Generate metadata for a single logcode

```python
from hex_decoder_module.export import MetadataGenerator

# Initialize
generator = MetadataGenerator("icd_document.pdf", enable_cache=True)

# Generate metadata
metadata = generator.generate_logcode_metadata("0x1C07")

# Save to file
generator.save_to_file(metadata, "metadata_1c07.json", pretty=True)
```

#### Generate metadata for multiple logcodes

```python
from hex_decoder_module.export import MetadataGenerator

# Initialize
generator = MetadataGenerator("icd_document.pdf", enable_cache=True)

# List of logcodes
logcode_ids = ["0x1C07", "0x1C08", "0x1C09"]

# Generate metadata for all
metadata = generator.generate_multi_logcode_metadata(
    logcode_ids,
    show_progress=True
)

# Save to file
generator.save_to_file(metadata, "metadata_all.json", pretty=True)
```

#### Get cache statistics

```python
stats = generator.get_cache_stats()
print(f"Cache enabled: {stats['cache_enabled']}")
print(f"Cache size: {stats['cache_size']} entries")
```

## JSON Structure

### Single Logcode Metadata

```json
{
  "logcode_id": "0x1C07",
  "logcode_name": "Nr5g_RrcServingCellInfo",
  "section": "4.1",
  "description": "",
  "version_offset": 0,
  "version_length": 32,
  "version_map": {
    "2": "4-4",
    "3": "4-5"
  },
  "available_versions": ["2", "3"],
  "versions": {
    "2": {
      "version_value": 2,
      "table_name": "4-4",
      "direct_dependencies": ["4-5", "4-6"],
      "fields": [
        {
          "name": "Physical Cell ID",
          "type_name": "Uint16",
          "offset_bytes": 0,
          "offset_bits": 0,
          "length_bits": 16,
          "description": "Physical cell identifier",
          "count": null
        },
        ...
      ],
      "total_fields": 25
    }
  },
  "all_tables": {
    "4-4": {
      "fields": [...],
      "field_count": 10,
      "dependencies": ["4-5"]
    }
  }
}
```

### Multiple Logcodes Metadata

```json
{
  "metadata_version": "1.0",
  "generated_timestamp": "2025-10-29T12:34:56.789",
  "total_logcodes": 3,
  "failed_logcodes": 0,
  "logcodes": {
    "0x1C07": {
      "logcode_id": "0x1C07",
      "logcode_name": "...",
      "versions": {...}
    },
    "0x1C08": {...},
    "0x1C09": {...}
  }
}
```

### Field Structure

Each field in the metadata contains:

- `name`: Field name (e.g., "Physical Cell ID")
- `type_name`: Data type (e.g., "Uint16", "Bool", "Table 4-5")
- `offset_bytes`: Byte offset from payload start
- `offset_bits`: Additional bit offset (for bit fields)
- `length_bits`: Field length in bits
- `description`: Field description from ICD
- `count`: Repetition count (optional, for arrays)
- `enum_mappings`: Enum value mappings (optional, for enum types)

## Understanding Dependencies

### Main Tables vs. Dependent Tables

In the ICD, a logcode version may reference other tables:

```
Version 2 → Table 4-4
Table 4-4 fields:
  - Field1: Uint8
  - Field2: Table 4-5  ← References another table
  - Field3: Uint16

Table 4-5 (dependent):
  - SubField1: Uint8
  - SubField2: Uint16
```

### How Dependencies Are Resolved

The metadata generator:

1. **Identifies references**: Scans `type_name` for "Table X-Y" patterns
2. **Fetches dependent tables**: Retrieves referenced tables from PDF
3. **Expands fields**: Replaces wrapper fields with actual fields
4. **Adjusts offsets**: Calculates correct byte/bit offsets
5. **Includes all fields**: Returns complete field layout

### Example: Version Expansion

**Before expansion (main table only):**
```json
{
  "fields": [
    {"name": "Field1", "type_name": "Uint8", "offset_bytes": 0},
    {"name": "Field2", "type_name": "Table 4-5", "offset_bytes": 1},
    {"name": "Field3", "type_name": "Uint16", "offset_bytes": 5}
  ]
}
```

**After expansion (with dependencies):**
```json
{
  "fields": [
    {"name": "Field1", "type_name": "Uint8", "offset_bytes": 0},
    {"name": "SubField1", "type_name": "Uint8", "offset_bytes": 1},
    {"name": "SubField2", "type_name": "Uint16", "offset_bytes": 2},
    {"name": "Field3", "type_name": "Uint16", "offset_bytes": 5}
  ]
}
```

Note how:
- `Field2` (wrapper) is replaced by `SubField1` and `SubField2`
- Offsets are adjusted: `SubField1` starts at byte 1 (Field2's offset)
- `SubField2` starts at byte 2 (1 + 1 byte for SubField1)
- `Field3` keeps its original offset (5 bytes)

## Using Generated Metadata

### For Payload Decoding

```python
import json

# Load metadata
with open("metadata_1c07.json", "r") as f:
    metadata = json.load(f)

# Get version 2 field layout
version_layout = metadata["versions"]["2"]
fields = version_layout["fields"]

# Decode payload bytes using field definitions
for field in fields:
    offset_bytes = field["offset_bytes"]
    offset_bits = field["offset_bits"]
    length_bits = field["length_bits"]

    # Extract field value from payload
    # ... (your decoding logic)
```

### For Documentation Generation

```python
import json

# Load metadata
with open("metadata_all.json", "r") as f:
    metadata = json.load(f)

# Generate HTML/Markdown documentation
for logcode_id, logcode_data in metadata["logcodes"].items():
    print(f"## {logcode_id} - {logcode_data['logcode_name']}")
    print(f"Section: {logcode_data['section']}")
    print(f"Available versions: {', '.join(logcode_data['available_versions'])}")
    # ... more documentation
```

## Performance Considerations

### Memory Usage

- **With cache (default)**: Higher memory, faster generation
  - Each parsed logcode is cached in memory
  - Recommended for batch processing

- **Without cache (`--no-cache`)**: Lower memory, slower generation
  - No caching, re-parses PDF for each logcode
  - Recommended for single logcode or memory-constrained environments

### Processing Time

| Operation | Time (approx.) |
|-----------|----------------|
| Single logcode | 2-5 seconds |
| 10 logcodes | 10-30 seconds |
| 100 logcodes | 2-5 minutes |

*Times vary based on PDF size, table complexity, and hardware.*

### Recommendations

1. **Batch processing**: Use `multi` command with cache enabled
2. **Single logcode**: Use `single` command for quick results
3. **Large batches**: Consider splitting into smaller batches
4. **Production**: Generate metadata once, use repeatedly

## Troubleshooting

### Common Errors

**Error: "Logcode not found"**
- Check logcode ID format (should be "0xXXXX")
- Verify logcode exists in PDF Section 4
- Try with `--verbose` to see scan progress

**Error: "Version not found"**
- Logcode may not have a version table
- Check if PDF contains version mappings for this logcode

**Error: "Missing dependent tables"**
- Referenced table may be outside search range
- Check PDF manually for table location
- Dependencies are searched within ±5 pages of section

### Debug Tips

1. **Use verbose mode**: `--verbose` shows detailed progress
2. **Check cache stats**: See how many entries are cached
3. **Test with known logcode**: Start with a simple logcode
4. **Validate PDF**: Ensure PDF follows ICD structure

## Examples

See `example_metadata_generation.py` for complete working examples:

```bash
python hex_decoder_module/example_metadata_generation.py
```

This script demonstrates:
- Single logcode generation
- Multiple logcode generation
- Metadata structure explanation
- Error handling

## Integration with Existing System

The metadata generator integrates seamlessly with the existing hex_decoder_module:

```
hex_decoder_module/
├── export/
│   ├── metadata_generator.py   ← New
│   ├── json_builder.py          ← Existing
│   └── file_writer.py           ← Existing
├── icd_parser/
│   ├── icd_query.py            ← Used by generator
│   ├── dependency_resolver.py  ← Used by generator
│   └── ...
├── metadata_cli.py             ← New CLI
└── example_metadata_generation.py  ← New examples
```

The generator uses existing components:
- `ICDQueryEngine` for PDF parsing
- `DependencyResolver` for table references
- `FileWriter` for JSON output

## Future Enhancements

Potential improvements:
- [ ] Parallel processing for large batches
- [ ] Incremental updates (update only changed logcodes)
- [ ] Validation against existing metadata
- [ ] Binary format for faster loading
- [ ] Compression for large metadata files

## Support

For issues or questions:
1. Check this documentation
2. Review examples in `example_metadata_generation.py`
3. Run with `--verbose` for detailed output
4. Report issues with error messages and PDF details
