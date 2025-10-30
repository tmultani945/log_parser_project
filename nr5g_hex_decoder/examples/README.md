# Examples

This directory contains working examples and sample data for the NR5G Hex Decoder.

## Files in This Directory

### Input Samples

- **`sample_payload.hex`** - Example hex payload file for logcode 0xB888
  - 176 bytes total (12 byte header + 164 byte payload)
  - Contains 3 measurement records
  - Ready to use with Step 2 (payload parsing)

### Output Samples

- **`metadata_0xB888.json`** - Example metadata file for logcode 0xB888
  - Generated from ICD PDF using Step 1
  - Contains version 1 field layout
  - Includes dependency table 4-5

### Scripts

- **`end_to_end_example.sh`** (or `.bat` for Windows) - Complete workflow demonstration
  - Runs both Step 1 and Step 2
  - Generates metadata and parses payload
  - Displays results

## Example Workflows

### Example 1: Basic Workflow

```bash
# Step 1: Generate metadata (if you have the ICD PDF)
python -m hex_decoder_module.metadata_cli single \
    --logcode 0xB888 \
    --pdf "../data/input/YOUR_ICD.pdf" \
    -o metadata_0xB888.json \
    -v

# Step 2: Parse the sample payload
python ../scripts/parse_payload.py \
    -i sample_payload.hex \
    -m metadata_0xB888.json \
    -o decoded_output.json \
    -v
```

### Example 2: Using Provided Metadata

If you don't have the ICD PDF, you can use the provided sample metadata:

```bash
# Parse using the provided metadata file
python ../scripts/parse_payload.py \
    -i sample_payload.hex \
    -m metadata_0xB888.json \
    -o decoded_output.json \
    -v
```

### Example 3: Batch Processing

Process multiple payload files:

```bash
# Assume you have: payload_1.hex, payload_2.hex, payload_3.hex
for file in payload_*.hex; do
    output="${file%.hex}_decoded.json"
    python ../scripts/parse_payload.py \
        -i "$file" \
        -m metadata_0xB888.json \
        -o "$output"
    echo "Processed: $file -> $output"
done
```

### Example 4: Multiple Logcodes

Generate metadata for multiple logcodes:

```bash
# Create a file with logcode list
cat > logcodes.txt << EOF
0xB888
0xB889
0x1C07
EOF

# Generate metadata for all
python -m hex_decoder_module.metadata_cli multi \
    --logcodes logcodes.txt \
    --pdf "../data/input/YOUR_ICD.pdf" \
    -o metadata_all.json \
    -v
```

## Sample Data Details

### sample_payload.hex

**Logcode:** 0xB888 (NR5G ML1 Serving Cell Measurement)

**Structure:**
- Header (12 bytes):
  - Length: 176 bytes (0xB0)
  - Logcode: 0xB888
  - Sequence: 6804
  - Timestamp: 3752876180

- Payload (164 bytes):
  - Version: 1
  - Record Count: 3
  - Record 0: 14 fields
  - Record 1: 14 fields
  - Record 2: 14 fields

**Fields per record:**
- Timestamp
- SSB Index
- Physical Cell ID
- SS-RSRP (multiple measurements)
- SS-RSRQ
- SS-SINR
- And more...

### metadata_0xB888.json

**Contents:**
- Logcode ID: 0xB888
- Logcode Name: NR5G ML1 Serving Cell Measurement
- Section: 4.4
- Versions: 1 (maps to Table 4-4)
- Total tables: 2 (main table 4-4 + dependency table 4-5)
- Total fields: 16 (2 header fields + 14 record fields)

## Expected Output

When you parse `sample_payload.hex` with `metadata_0xB888.json`, you should see:

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
    "Version": {"type": "Uint8", "raw": 1},
    "Record Count": {"type": "Uint8", "raw": 3},
    "Record 0 Timestamp": {"type": "Uint32", "raw": 24346995},
    "Record 0 SSB Index": {"type": "Uint16", "raw": 23668},
    ...
  },
  "metadata": {
    "section": "4.4",
    "total_fields": 44,
    "decode_time_ms": 12.34
  }
}
```

## Creating Your Own Payload Files

### Format Template

```
Length:     <total_bytes>
Header:     <12_hex_bytes_space_separated>
Payload:    <hex_bytes_space_separated>
            <continuation_of_hex_bytes>
            <more_hex_bytes>
```

### Example

```
Length:     61
Header:     3D 00 07 1C CD 0F 67 95 F5 A6 06 01
Payload:    02 00 03 00 01 01 00 38 00 3A 00 7D
            F1 40 18 30 01 E0 E5 09 00 4A DE 09
            00 64 00 64 00 3A 00 7D F1 00 00 00
            00 37 01 03 E0 01 00 07 01 18 00 4D
            00
```

**Tips:**
- Each hex byte is 2 characters (0-9, A-F)
- Separate bytes with spaces
- Multi-line payloads are supported
- Indentation doesn't matter (will be stripped)
- Case-insensitive (FF or ff both work)

## Verifying Examples

### Check File Integrity

```bash
# Verify hex file format
head -5 sample_payload.hex

# Verify metadata JSON validity
python -m json.tool metadata_0xB888.json > /dev/null && echo "Valid JSON"

# Check file sizes
ls -lh sample_payload.hex metadata_0xB888.json
```

### Run Complete Test

```bash
# Run the end-to-end example script
bash end_to_end_example.sh  # Linux/Mac
# or
end_to_end_example.bat      # Windows
```

## Troubleshooting Examples

### Issue: "Metadata file not found"

```bash
# Make sure you're in the examples directory
pwd
ls metadata_0xB888.json

# Or use absolute path
python ../scripts/parse_payload.py \
    -i sample_payload.hex \
    -m "$(pwd)/metadata_0xB888.json" \
    -o output.json
```

### Issue: "Input file not found"

```bash
# Check file exists
ls sample_payload.hex

# Use absolute path if needed
python ../scripts/parse_payload.py \
    -i "$(pwd)/sample_payload.hex" \
    -m metadata_0xB888.json \
    -o output.json
```

### Issue: "Permission denied"

```bash
# Check permissions
ls -l sample_payload.hex

# Fix if needed
chmod 644 sample_payload.hex
```

## Next Steps

After running the examples:

1. **Explore the output** - Open `decoded_output.json` to see the decoded data
2. **Try your own payload** - Create a hex file with your own data
3. **Generate your own metadata** - Use your ICD PDF to generate metadata for other logcodes
4. **Read the guides** - Check out [QUICKSTART.md](../QUICKSTART.md) and [USER_GUIDE.md](../USER_GUIDE.md)

## Additional Resources

- [Main README](../README.md) - Overview and features
- [QUICKSTART](../QUICKSTART.md) - Get started in 5 minutes
- [USER_GUIDE](../USER_GUIDE.md) - Comprehensive documentation
- [Scripts Directory](../scripts/) - Helper scripts

## Support

If you encounter issues with the examples:
1. Verify you've installed dependencies: `pip install pdfplumber PyMuPDF`
2. Check file paths are correct (use absolute paths if needed)
3. Run with verbose flag `-v` to see detailed output
4. Review error messages and check troubleshooting sections
