# Quick Usage Guide

## Run the Script

```bash
python extract_metadata.py
```

That's it! The script will:
1. Read `data/input/ICD.pdf`
2. Find logcode 0xB823
3. Extract all field definitions
4. Save to `data/output/metadata_0xB823_v196610.json`

## What You Get

A JSON file with complete metadata:
- **21 field definitions** with exact offsets and types
- **Ready for payload parsing**
- **Human-readable** structure

## Example Output

```json
{
  "metadata": {
    "logcode_id": "0xB823",
    "target_version": {
      "version": 196610,
      "table_number": "4-6"
    },
    "main_table": {
      "fields": [
        {
          "name": "Tx Chain Mask",
          "type_name": "Uint32",
          "offset_bytes": 9,
          "offset_bits": 1,
          "length_bits": 2
        }
        // ...20 more fields
      ]
    }
  }
}
```

## Customize

Want to change logcode or version?

**Edit line 28-29** in `extract_metadata.py`:
```python
TARGET_LOGCODE = "0xB823"
TARGET_VERSION = 196610
```

## Custom Paths

```bash
# Custom PDF
python extract_metadata.py /path/to/ICD.pdf

# Custom output
python extract_metadata.py -o output.json
```

## Understanding the Code

The script has **5 clear sections**:

1. **Configuration** (lines 25-40) - Hardcoded values
2. **Find Section** (lines 47-97) - Scan PDF for logcode
3. **Extract Tables** (lines 104-176) - Pull tables from PDF
4. **Parse Fields** (lines 183-284) - Convert to field definitions
5. **Export JSON** (lines 341-380) - Save to file

**Total: ~350 lines, all in one file!**

Just read the script top-to-bottom to understand how it works.

## Need Help?

See full documentation in `README.md`
