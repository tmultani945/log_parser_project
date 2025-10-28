# How to Get Version Information from JSON File

This guide shows all the ways to query version information from decoded JSON files and the ICD PDF.

---

## Method 1: Quick One-Liner (Fastest)

```bash
python -c "
import json
data = json.load(open('hex_decoder_module/decoded_output.json'))
print(f\"Logcode: {data['logcode']['id_hex']}\")
print(f\"Version: {data['version']['raw']} (decimal {int(data['version']['raw'], 16)})\")
print(f\"Table:   {data['version']['resolved_layout']}\")
"
```

**Output:**
```
Logcode: 0xB823
Version: 0x00030003 (decimal 196611)
Table:   11-56
```

---

## Method 2: Using get_version.py Script

### Get Version from Decoded JSON

```bash
python hex_decoder_module/get_version.py --json hex_decoder_module/decoded_output.json
```

**Output:**
```
=== VERSION FROM DECODED JSON ===

Logcode ID:          0xB823 (47139)
Logcode Name:        NR5G RRC Serving Cell Info

Version (Hex):       0x00030003
Version (Decimal):   196611
Resolved Table:      11-56
```

### List All Available Versions from PDF

```bash
python hex_decoder_module/get_version.py \
  --logcode 0xB823 \
  --pdf "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"
```

**Output:**
```
=== AVAILABLE VERSIONS FROM PDF ===

Logcode: 0xB823
Total Versions: 8

Version Mappings:
  Version 1            (decimal          1) -> Table 11-46
  Version 2            (decimal          2) -> Table 11-47
  Version 3            (decimal          3) -> Table 11-48
  Version 4            (decimal          4) -> Table 11-49
  Version 0x00030000   (decimal     196608) -> Table 11-50
  Version 0x00030001   (decimal     196609) -> Table 11-52
  Version 0x00030002   (decimal     196610) -> Table 11-54
  Version 0x00030003   (decimal     196611) -> Table 11-56
```

### Combined: Current Version + All Available Versions

```bash
python hex_decoder_module/get_version.py \
  --json hex_decoder_module/decoded_output.json \
  --logcode 0xB823 \
  --pdf "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"
```

**Output:**
```
=== VERSION FROM DECODED JSON ===

Logcode ID:          0xB823 (47139)
Logcode Name:        NR5G RRC Serving Cell Info

Version (Hex):       0x00030003
Version (Decimal):   196611
Resolved Table:      11-56


=== AVAILABLE VERSIONS FROM PDF ===

Logcode: 0xB823
Total Versions: 8

Version Mappings:
  Version 1            (decimal          1) -> Table 11-46
  Version 2            (decimal          2) -> Table 11-47
  Version 3            (decimal          3) -> Table 11-48
  Version 4            (decimal          4) -> Table 11-49
  Version 0x00030000   (decimal     196608) -> Table 11-50
  Version 0x00030001   (decimal     196609) -> Table 11-52
  Version 0x00030002   (decimal     196610) -> Table 11-54
  Version 0x00030003   (decimal     196611) -> Table 11-56
```

---

## Method 3: Manual JSON Inspection

### View Complete JSON

```bash
cat hex_decoder_module/decoded_output.json
```

### Extract Specific Fields with jq (if available)

```bash
# Get version information
jq '.version' hex_decoder_module/decoded_output.json

# Get logcode information
jq '.logcode' hex_decoder_module/decoded_output.json

# Get both
jq '{logcode: .logcode, version: .version}' hex_decoder_module/decoded_output.json
```

### Using Python's json.tool

```bash
python -m json.tool hex_decoder_module/decoded_output.json | grep -A 5 '"version"'
```

---

## Method 4: Python Script for Batch Processing

Create a script to process multiple JSON files:

```python
import json
import glob

def get_version_info(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    return {
        'file': json_file,
        'logcode': data['logcode']['id_hex'],
        'version_hex': data['version']['raw'],
        'version_decimal': int(data['version']['raw'], 16),
        'table': data['version']['resolved_layout']
    }

# Process all JSON files in a directory
for json_file in glob.glob('*.json'):
    info = get_version_info(json_file)
    print(f"{info['file']:30s} | {info['logcode']:10s} | {info['version_hex']:12s} | Table {info['table']}")
```

---

## JSON Structure Reference

The decoded JSON file has the following structure:

```json
{
  "logcode": {
    "id_hex": "0xB823",           // Logcode ID in hex
    "id_decimal": 47139,          // Logcode ID in decimal
    "name": "NR5G RRC Serving Cell Info"  // Logcode name
  },
  "version": {
    "raw": "0x00030003",          // Version in hex format
    "resolved_layout": "11-56"    // Table number for this version
  },
  "header": {
    "length_bytes": 61,
    "sequence": 17288308,
    "timestamp_raw": 4220039016
  },
  "fields": {
    // All decoded fields...
  },
  "metadata": {
    "section": "11.3",
    "total_fields": 16,
    "decode_time_ms": 21589.57,
    "cache_enabled": true,
    "cache_size": 1
  }
}
```

---

## Version Interpretation

### Version Format

The version field can be in two formats:

1. **Simple Version** (e.g., 1, 2, 3, 4)
   - Small decimal numbers
   - Typically for older/simpler packet versions

2. **Extended Version** (e.g., 0x00030003 = 196611)
   - Large hex numbers (>= 0x00030000)
   - Format: `0x000MMMNN` where:
     - `MMM` = Major version (3 in this case)
     - `NN` = Minor version (3 in this case)
   - Example: 0x00030003 = Version 3.3

### Version to Table Mapping

Each version maps to a specific table in the ICD PDF:

| Version | Decimal | Table | Field Count |
|---------|---------|-------|-------------|
| 1 | 1 | 11-46 | 10 fields |
| 2 | 2 | 11-47 | 11 fields |
| 3 | 3 | 11-48 | 12 fields |
| 4 | 4 | 11-49 | 12 fields |
| 0x00030000 | 196608 | 11-50 | via 11-51 (13 fields) |
| 0x00030001 | 196609 | 11-52 | via 11-53 (16 fields) |
| 0x00030002 | 196610 | 11-54 | via 11-55 (16 fields) |
| **0x00030003** | **196611** | **11-56** | **via 11-57 (16 fields)** |

The table number determines which field layout is used for decoding the payload.

---

## Common Use Cases

### 1. Check if packet uses latest version

```bash
# Get current version
current=$(python -c "import json; print(int(json.load(open('hex_decoder_module/decoded_output.json'))['version']['raw'], 16))")

# Compare with expected latest (196611)
if [ "$current" -eq 196611 ]; then
    echo "Using latest version"
else
    echo "Using older version: $current"
fi
```

### 2. Batch process multiple packets

```python
import json
import glob

version_counts = {}

for json_file in glob.glob('decoded_*.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)

    version = data['version']['raw']
    version_counts[version] = version_counts.get(version, 0) + 1

print("Version Distribution:")
for version, count in sorted(version_counts.items()):
    print(f"  {version:12s}: {count:5d} packets")
```

### 3. Filter by version

```bash
# Find all JSON files with version 0x00030003
for file in *.json; do
    version=$(python -c "import json; print(json.load(open('$file'))['version']['raw'])")
    if [ "$version" = "0x00030003" ]; then
        echo $file
    fi
done
```

---

## Quick Reference Commands

```bash
# Navigate to project
cd C:/Users/proca/ICD_code_for_version_ch/log_parser_project

# Get version from JSON (one-liner)
python -c "import json; d=json.load(open('hex_decoder_module/decoded_output.json')); print(f\"Version: {d['version']['raw']}\")"

# Get version using utility script
python hex_decoder_module/get_version.py --json hex_decoder_module/decoded_output.json

# List all versions for a logcode
python hex_decoder_module/get_version.py --logcode 0xB823 --pdf "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"

# Get both current and available versions
python hex_decoder_module/get_version.py --json hex_decoder_module/decoded_output.json --logcode 0xB823 --pdf "data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"
```
