# Quick Start Guide - NR5G Log Parser

## 🚀 Get Running in 5 Minutes

### Step 1: Install Dependencies (1 minute)

```bash
cd log_parser_project
pip install PyMuPDF==1.23.8 pdfplumber==0.10.3 pandas==2.1.4
```

**Note**: The other dependencies in requirements.txt are optional. These 3 are enough to get started.

### Step 2: Parse Your PDF (2 minutes)

```bash
cd src
python app.py parse /path/to/your/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document-1-31.pdf
```

**Expected Output**:
```
Parsing PDF: /path/to/document.pdf
Extracting logcode data...
Found 10 logcodes
Storing in database: data/parsed_logcodes.db
Imported 10 logcodes from /path/to/document.pdf
Done!
```

### Step 3: Query a Logcode (30 seconds)

```bash
python app.py query 0x1C07 2
```

**Expected Output**:
```
================================================================================
Table 4-4: Nr5g_Sub6TxAgc_V2
Logcode: 0x1C07 - NR5G Sub6 TxAGC
Section: 4.1
================================================================================

Name           | Type Name | Cnt | Off | Len | Description
----------------------------------------------------------------
Version        | Uint32    | 1   | 0   | 32  |
Systime        | Table 4-5 | 1   | 32  | 32  | systime
Sym Index      | Uint32    | 1   | 64  | 4   | Symbol number having Tx activity
...

================================================================================
Table 4-5: Nr5g_SystemTime
...
```

### Step 4: Explore (1 minute)

```bash
# List all logcodes
python app.py list

# Search for specific logcode
python app.py search TxAGC

# Show versions for a logcode
python app.py versions 0x1C07
```

## 💡 What Just Happened?

1. **Parsing**: Extracted all ~100 logcodes from the PDF with their:
   - Names (e.g., "NR5G Sub6 TxAGC")
   - Versions (e.g., "1", "2", "3")
   - Tables with full data
   - Dependencies between tables

2. **Storage**: Saved everything in `data/parsed_logcodes.db` (SQLite)

3. **Query**: Retrieved Table 4-4 (version 2) and Table 4-5 (dependency)

## 🎯 Common Use Cases

### Use Case 1: Check What Versions Exist

```bash
python app.py versions 0x1C07
# Output: Version 1, 2, 3, 5, 6, 7, 8
```

### Use Case 2: Save Results to File

```bash
python app.py query 0x1C07 2 --output table_v2.txt
```

### Use Case 3: Find All TxAGC Logcodes

```bash
python app.py search TxAGC
# Output: 0x1C07, 0x1C08, etc.
```

### Use Case 4: Export Everything to JSON

```bash
python app.py parse document.pdf --export-json output.json
```

## 📁 Files Created

```
log_parser_project/
├── data/
│   └── parsed_logcodes.db  ← Your parsed data (SQLite)
├── src/
│   └── *.py                 ← Python modules
└── README.md
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'fitz'"

**Solution**: Install PyMuPDF
```bash
pip install PyMuPDF
```

### "No such file or directory: data/parsed_logcodes.db"

**Solution**: Run `parse` command first
```bash
python app.py parse your_document.pdf
```

### "Logcode 0x1C07 not found"

**Solution**: Check what's available
```bash
python app.py list
```

### "Version 99 not found"

**Solution**: Check available versions
```bash
python app.py versions 0x1C07
```

## 🔍 Understanding the Output

### Query Output Structure

```
================================================================================
Table 4-4: Nr5g_Sub6TxAgc_V2        ← Table number and title
Logcode: 0x1C07 - NR5G Sub6 TxAGC   ← Logcode and full name
Section: 4.1                        ← PDF section
================================================================================

Name      | Type Name | Cnt | Off | Len | Description
--------------------------------------------------------
Field1    | Uint32    | 1   | 0   | 32  | ...
Field2    | Table 4-5 | 1   | 32  | 32  | → References another table
```

**Key Points**:
- Each query returns the **main table** plus all **dependencies**
- "Type Name" column shows data types or table references
- Tables are shown in logical order (main → dependencies)

## 📚 Next Steps

### Learn More
1. Read [README.md](README.md) for detailed usage
2. Check [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) for architecture details
3. Browse [src/](src/) for code documentation

### Advanced Usage
1. Use programmatic API (Python imports)
2. Integrate into CI/CD pipelines
3. Export to custom formats
4. Add custom post-processing

### Customize
1. Modify `query_engine.py` for custom output formats
2. Add new commands to `app.py`
3. Extend schema in `datastore.py`

## ✨ Features You'll Love

1. **Smart Dependency Resolution**: Query one table, get all related tables automatically
2. **Version Management**: Easy access to any version of any logcode
3. **Fast Queries**: SQLite indexes make lookups instant
4. **Robust Parsing**: Handles table continuations, header repeats, and layout variations
5. **Dual Storage**: SQLite for queries, JSON for sharing

## 🎉 That's It!

You now have a fully functional log parser. Start exploring your data!

**Common Commands**:
```bash
python app.py list              # Browse available logcodes
python app.py search <term>     # Find specific logcodes
python app.py query <code> <v>  # Get table data
python app.py versions <code>   # Check versions
```

---

**Need Help?** Check the full [README.md](README.md) or review [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md).
