# Parser Corrections Summary

## Issues Fixed

### 1. Metadata Generation (`hex_decoder_module/export/metadata_generator.py`)

**Problem**: The metadata generator was using `get_version_layout()` which expands all table dependencies inline. This destroyed the raw table structure and made it impossible to detect repeating structures (fields with `count=-1`).

**Solution**: Changed to use raw `table_definitions` from metadata instead of expanded layout:
```python
# OLD (incorrect):
field_layout = self.icd_engine.get_version_layout(logcode_id, version)

# NEW (correct):
raw_field_definitions = metadata.table_definitions.get(table_name, [])
```

**Result**: Metadata now preserves repeating structure fields like `"Records"` with `count=-1` and type `"Table 7-2805"`.

---

### 2. Metadata Payload Parser (`hex_decoder_module/metadata_payload_parser.py`)

**Problem 1**: Parser didn't handle repeating structures (Records arrays).

**Solution**: Completely rewrote parser to match `hex_decoder_module.cli` implementation:
- Added `_decode_repeating_structure()` method
- Added `_get_repetition_count()` to determine record count from "Num CA", "Num Records", or "Cumulative Bitmask"
- Added logic to decode multiple records based on available payload space

**Problem 2**: ICD metadata had invalid field offsets:
- BLER field had `offset=0` (should be at offset 72 after other fields)
- DummyField and Padding fields inflated record size from 72 to 73 bytes
- With 73-byte records, only 1 fit; with 72-byte records, 2 fit correctly

**Solution**: Added field filtering logic:
```python
# Skip fields with offset=0 that appear after other fields (calculated fields)
if field_offset == 0 and max_offset_seen > 0:
    continue

# Skip dummy/padding fields (not actual record data)
if 'dummy' in field_name or 'padding' in field_name:
    continue
```

---

## Verification Results

### Test Payload: 0xB888 Version 196609

**Expected vs Actual Values:**

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| **Header Fields** |
| Num Records | 1 | 1 | ✅ |
| Num Total Slots | 12908 | 12908 | ✅ |
| Num CA | 6 | 6 | ✅ |
| Cumulative Bitmask | 119 | 119 | ✅ |
| **Record 0** |
| Carrier ID | 0 | 0 | ✅ |
| Numerology | 30KHZ | 30KHZ | ✅ |
| NumSlotsElapsed | 6589921 | 6589921 | ✅ |
| NumPDSCHDecode | 133714 | 133714 | ✅ |
| NumCRCPassTB | 133142 | 133142 | ✅ |
| NumCRCFailTB | 572 | 572 | ✅ |
| NumReTx | 3203 | 3203 | ✅ |
| ACKAsNACK | 1157 | 1157 | ✅ |
| HARQFailure | 42 | 42 | ✅ |
| CRCPassTBBytes | 62206859 | 62206859 | ✅ |
| CRCFailTBBytes | 5825445 | 5825445 | ✅ |
| TBBytes | 68032304 | 68032304 | ✅ |
| ReTxBytes | 6077790 | 6077790 | ✅ |
| **Record 1** |
| Carrier ID | 1 | 1 | ✅ |
| Numerology | 30KHZ | 30KHZ | ✅ |
| NumSlotsElapsed | 1973 | 1973 | ✅ |
| NumPDSCHDecode | 11 | 11 | ✅ |
| NumCRCPassTB | 7 | 7 | ✅ |
| NumCRCFailTB | 4 | 4 | ✅ |
| NumReTx | 4 | 4 | ✅ |
| ACKAsNACK | 0 | 0 | ✅ |
| HARQFailure | 0 | 0 | ✅ |
| CRCPassTBBytes | 152396 | 152396 | ✅ |
| CRCFailTBBytes | 114744 | 114744 | ✅ |
| TBBytes | 267140 | 267140 | ✅ |
| ReTxBytes | 114744 | 114744 | ✅ |

**All values match perfectly! ✅**

---

## Updated Usage Commands

### 1. Generate Corrected Metadata
```bash
python -m hex_decoder_module.metadata_cli single \
  --logcode 0xB888 \
  --pdf "data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" \
  -o metadata_0xB888_corrected.json \
  -v
```

### 2. Parse Payload with Corrected Parser
```bash
python -m hex_decoder_module.metadata_payload_parser \
  metadata_0xB888_corrected.json \
  "01 00 03 00 73 5D 74 01 ..." \
  parsed_output.json
```

**Or using Python:**
```python
from hex_decoder_module.metadata_payload_parser import parse_payload_from_metadata

payload_hex = """
01 00 03 00 73 5D 74 01 C0 26 03 60
77 5D 78 5D 79 5D 7A 5D 00 00 01 00
...
"""

result = parse_payload_from_metadata(
    metadata_file='metadata_0xB888_corrected.json',
    payload_hex=payload_hex,
    output_file='parsed_output.json',
    verbose=True
)
```

---

## Key Improvements

1. **Repeating Structure Support**: Parser now correctly handles Records arrays with variable counts
2. **Dynamic Record Counting**: Uses "Num CA", "Num Records", or "Cumulative Bitmask" to determine record count
3. **Metadata Preservation**: Raw table structure with `count=-1` is preserved in metadata JSON
4. **Field Filtering**: Invalid fields (offset=0 calculated fields, dummy/padding fields) are excluded from record size calculation
5. **Correct Record Size**: 72 bytes instead of 73 bytes, allowing 2 complete records to fit in payload

---

## Files Modified

1. `hex_decoder_module/export/metadata_generator.py` - Line 92-98
2. `hex_decoder_module/metadata_payload_parser.py` - Complete rewrite (460 lines)

---

## Testing

Run the test script:
```bash
python test_corrected_parser.py
```

Expected output:
- Logcode: 0XB888 (NR5G MAC PDSCH Stats)
- Version: 196609 (0x00030001)
- Fields parsed: 33
- Record 0 fields: 13
- Record 1 fields: 13
- All values matching expected output
