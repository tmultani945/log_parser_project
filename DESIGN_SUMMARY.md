# NR5G Log Parser - Design Summary & Implementation Guide

## 📋 Executive Summary

This project implements a **modular, production-ready Python system** for parsing technical PDF documents containing ~100 log codes with multiple versions and complex table structures. The system handles real-world PDF challenges like table continuations, header repetitions, and cross-references.

## 🎯 Key Design Decisions

### 1. **Layered Architecture**
**Decision**: Use 5 distinct layers instead of monolithic approach

**Rationale**:
- **Maintainability**: Each layer has single responsibility
- **Testability**: Layers can be tested independently
- **Flexibility**: Easy to swap implementations (e.g., PostgreSQL instead of SQLite)

**Layers**:
1. PDF Extraction → Raw table data
2. Parsing → Structured logcode objects
3. Data Storage → Persistence
4. Query Engine → User interface
5. Application → CLI

### 2. **Dual Storage: SQLite + JSON**
**Decision**: Primary storage in SQLite, with JSON export option

**Rationale**:
- **SQLite**: Fast queries, indexing, relationships, < transactional integrity
- **JSON**: Easy sharing, human-readable, portable
- **Both**: SQLite for development/production, JSON for data exchange

### 3. **Table Continuation Merging Strategy**
**Decision**: Detect "(cont.)" in captions and merge at extraction layer

**Rationale**:
- Handle early before higher layers see fragmented data
- De-duplicate headers automatically
- Preserve correct row order across pages

**Implementation**:
```python
def merge_continuations(tables):
    # Group by table number
    # Check is_continuation flag
    # Remove duplicate header rows
    # Maintain page span metadata
```

### 4. **Version Mapping via "_Versions" Tables**
**Decision**: Explicitly parse tables ending with `_Versions`

**Rationale**:
- **Explicit is better than implicit**: Clear signal for version tables
- **Robust**: Works even if version table appears out of order
- **Extensible**: Easy to add version-specific metadata later

**Schema**:
```sql
CREATE TABLE versions (
    logcode TEXT,
    version TEXT,
    table_number TEXT,  -- Maps version → table
    UNIQUE(logcode, version)
)
```

### 5. **Dependency Graph Construction**
**Decision**: Parse "Type Name" column for table references, store as graph

**Rationale**:
- **Completeness**: Query returns all required data in one call
- **Performance**: Pre-computed during parsing, not at query time
- **Flexibility**: Supports arbitrary dependency depth

**Algorithm**:
```python
def get_all_dependencies(table):
    visited = set()
    queue = [table]
    while queue:
        current = queue.pop()
        for dep in dependencies[current]:
            if dep not in visited:
                yield dep
                queue.append(dep)
```

### 6. **Header Normalization**
**Decision**: Normalize to canonical headers at extraction time

**Rationale**:
- **Consistency**: All tables use same column names
- **Simplifies Queries**: No need to handle variations
- **Error Detection**: Spot tables that don't match expected format

**Standard Headers**:
```
Name | Type Name | Cnt | Off | Len | Description
```

### 7. **Tool Selection: PyMuPDF + pdfplumber**
**Decision**: Hybrid approach using multiple libraries

**Rationale**:
- **PyMuPDF**: Fast, good for structure, metadata, text extraction
- **pdfplumber**: Better for table detection and cell extraction
- **Fallback**: Can add Camelot/Tabula for difficult tables

**Trade-offs**:
- More dependencies, but better robustness
- Slower than single tool, but higher accuracy

### 8. **CLI as Primary Interface**
**Decision**: Build comprehensive CLI, expose programmatic API

**Rationale**:
- **User-friendly**: Most users prefer command-line
- **Scriptable**: Easy to integrate into pipelines
- **API available**: Advanced users can import modules

**Commands**:
- `parse`: Create database from PDF
- `query`: Get table for version
- `list`: Show all logcodes
- `search`: Find logcodes
- `versions`: Show versions

## 🏗️ Component Details

### PDF Extractor (`pdf_extractor.py`)

**Core Responsibilities**:
- Extract text and tables from PDF pages
- Detect table captions: "Table X-Y Title"
- Handle continuations: "Table X-Y Title (cont.)"
- Merge multi-page tables
- De-duplicate repeated headers

**Key Classes**:
- `ExtractedTable`: Represents a complete table with metadata
- `TableMetadata`: Page spans, continuation flags
- `PDFExtractor`: Main extraction logic

**Challenges Addressed**:
- ✅ Tables spanning multiple pages
- ✅ Headers repeated on new pages
- ✅ Variable spacing in column alignment
- ✅ Caption detection with regex patterns

### Parser (`parser.py`)

**Core Responsibilities**:
- Detect logcode sections (e.g., "4.1 NR5G Sub6 TxAGC (0x1C07)")
- Parse "_Versions" tables to extract version mappings
- Build dependency graph from table references
- Group tables by logcode

**Key Classes**:
- `LogcodeData`: Complete data for one logcode
- `LogcodeParser`: Main parsing logic

**Detection Patterns**:
```python
SECTION_PATTERN = r'^\s*(\d+\.\d+)\s+(.+?)\s+\((0x[0-9A-F]+)\)'
VERSION_PATTERN = r'Version\s+(\d+)'
TABLE_REF_PATTERN = r'Table\s+(\d+-\d+)'
```

### Datastore (`datastore.py`)

**Core Responsibilities**:
- Create SQLite schema with proper indexes
- Store logcode data with referential integrity
- Export to JSON format
- Provide low-level query methods

**Schema Design**:
```sql
documents       -- Source PDFs
logcodes        -- Logcode metadata
versions        -- Version → table mappings
tables          -- Table metadata
table_rows      -- Actual table data
table_deps      -- Table dependencies
```

**Indexes**:
- `(logcode)` → Fast logcode lookup
- `(logcode, version)` → Fast version queries
- `(logcode, table_number)` → Fast table access

### Query Engine (`query_engine.py`)

**Core Responsibilities**:
- High-level query interface
- Dependency resolution
- Formatted output generation
- Search functionality

**Main Operations**:
```python
get_table(logcode, version)  → List[TableDisplay]
search_logcode(term)         → List[Dict]
list_all_logcodes()          → List[Dict]
format_output(tables)        → str
```

**Output Formatting**:
- Calculated column widths
- Aligned text
- Clear table boundaries
- Complete metadata (logcode, name, section)

### Application (`app.py`)

**Core Responsibilities**:
- CLI argument parsing
- Command routing
- Error handling
- User feedback

**Command Structure**:
```
app.py parse <pdf> [--export-json]
app.py query <logcode> <version> [--output]
app.py list
app.py search <term>
app.py versions <logcode>
```

## 🧪 Testing Strategy

### Unit Testing
Each layer can be tested independently:

```python
# Test extractor
extractor = PDFExtractor("test.pdf")
tables = extractor.extract_all_tables()
assert len(tables) > 0

# Test parser
parser = LogcodeParser("test.pdf")
logcodes = parser.parse_all_logcodes()
assert "0x1C07" in logcodes

# Test datastore
db = LogcodeDatastore(":memory:")  # In-memory for tests
db.store_logcode_data(test_data, 1)
result = db.get_logcode_info("0x1C07")
assert result is not None
```

### Integration Testing
Test end-to-end workflow:

```python
# Parse → Store → Query
parser = LogcodeParser("test.pdf")
parser.parse_all_logcodes()

db = LogcodeDatastore("test.db")
db.import_from_parser(parser, "test.pdf")

engine = QueryEngine("test.db")
tables = engine.get_table("0x1C07", "2")
assert len(tables) >= 1  # At least main table
```

## 🔧 Implementation Highlights

### 1. Robust Table Caption Detection
```python
pattern = r'Table\s+(\d+-\d+)\s+(.+?)(?:\s+\(cont\.\))?$'
match = re.search(pattern, text, re.IGNORECASE)
# Handles: "Table 4-4 Title", "Table 4-4 Title (cont.)"
```

### 2. Intelligent Header De-duplication
```python
def _is_header_row(row, headers):
    """Case-insensitive comparison"""
    return all(
        cell.lower().strip() == header.lower().strip()
        for cell, header in zip(row, headers)
    )
```

### 3. Recursive Dependency Resolution
```python
def get_all_dependencies(table):
    visited = {table}
    queue = [table]
    result = []
    
    while queue:
        current = queue.pop(0)
        for dep in dependencies[current]:
            if dep not in visited:
                result.append(dep)
                visited.add(dep)
                queue.append(dep)
    
    return result
```

### 4. Flexible Query Interface
```python
# Simple API
tables = engine.get_table("0x1C07", "2")

# Returns complete data:
# - Main table (4-4)
# - All dependencies (4-5, etc.)
# - Formatted for display
```

## 📊 Performance Considerations

### Parsing Performance
- **Caching**: Extract once, query many times
- **Incremental**: Can add support for partial updates
- **Parallel**: PDF pages can be processed in parallel

### Query Performance
- **Indexed**: All common queries use indexes
- **Pre-computed**: Dependencies calculated at parse time
- **Optimized**: SQLite query planner handles joins efficiently

### Memory Usage
- **Streaming**: Process one table at a time
- **Pagination**: Large result sets can be paginated
- **Cleanup**: Close connections properly

## 🚀 Future Enhancements

### Short-term (Easy)
1. **OCR Support**: For scanned PDFs
2. **Fuzzy Search**: Using Levenshtein distance
3. **Web UI**: Simple Flask/FastAPI interface
4. **Export Formats**: CSV, Excel output

### Medium-term (Moderate)
1. **Multiple PDFs**: Support indexing multiple documents
2. **Version Diff**: Compare versions side-by-side
3. **Cache Layer**: Redis for popular queries
4. **REST API**: Full REST interface

### Long-term (Complex)
1. **ML-based Extraction**: Train model on PDF structure
2. **Semantic Search**: Vector embeddings for descriptions
3. **Real-time Updates**: Watch folder for new PDFs
4. **Distributed**: Handle thousands of PDFs

## 📚 Usage Examples

### Example 1: Simple Query
```bash
# Parse PDF
python app.py parse document.pdf

# Query logcode 0x1C07, version 2
python app.py query 0x1C07 2

# Output: Table 4-4 + Table 4-5 (formatted)
```

### Example 2: Programmatic Use
```python
from query_engine import QueryEngine

engine = QueryEngine("data/parsed_logcodes.db")

# Get tables
tables = engine.get_table("0x1C07", "2")

# Custom processing
for table in tables:
    print(f"Processing {table.table_number}")
    for row in table.rows:
        # Your logic here
        pass

engine.close()
```

### Example 3: Batch Processing
```bash
# Parse multiple PDFs
for pdf in *.pdf; do
    python app.py parse "$pdf" -d "data/all_logs.db"
done

# Query consolidated database
python app.py list -d "data/all_logs.db"
```

## ✅ Requirements Checklist

All domain rules implemented:

- ✅ **Canonical sectioning**: Section + logcode detection
- ✅ **Logcode name**: Persisted with code
- ✅ **Table headers**: Normalized to standard 6 columns
- ✅ **Versions table**: Detects `_Versions` suffix
- ✅ **Version lookup**: Maps version → table number
- ✅ **Multi-page merge**: Handles "(cont.)" correctly
- ✅ **Robustness**: Handles layout variations
- ✅ **Cross-table refs**: Detects and includes dependencies
- ✅ **Uniform presentation**: Standard format for all tables

## 🎓 Key Takeaways

1. **Modularity Wins**: Layered architecture makes system maintainable
2. **Handle Reality**: Real PDFs are messy; robust parsing is critical
3. **Explicit is Better**: `_Versions` tables make intent clear
4. **Store Smart**: SQLite for queries, JSON for sharing
5. **Test Everything**: Each layer can be tested independently

---

## 📞 Support

For questions or issues:
- Check README.md for usage examples
- Review src/ modules for API details
- Run with `-h` flag for command help

## 🏁 Conclusion

This implementation provides a **production-ready, extensible system** for parsing and querying complex technical PDFs. The modular design allows easy testing, maintenance, and future enhancements while handling real-world PDF challenges robustly.
