 System Architecture Overview

  Two-Step Workflow

  ┌─────────────────────────────────────────────────────────────┐
  │                     STEP 1: METADATA GENERATION              │
  │                          (Once per logcode)                  │
  ├─────────────────────────────────────────────────────────────┤
  │                                                              │
  │  ICD PDF File (e.g., "NR5G_ICD.pdf")                       │
  │         │                                                    │
  │         ├─► PDFScanner        → Find logcode section       │
  │         ├─► SectionExtractor  → Extract tables             │
  │         ├─► TableParser       → Parse field definitions    │
  │         ├─► VersionParser     → Map versions to tables     │
  │         ├─► DependencyResolver → Resolve table references  │
  │         └─► MetadataGenerator → Create JSON metadata       │
  │                                                              │
  │  OUTPUT: metadata_0xB888.json                               │
  │  {                                                           │
  │    "logcode_id": "0xB888",                                  │
  │    "versions": {...},                                        │
  │    "all_tables": {...}                                       │
  │  }                                                           │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │                     STEP 2: PAYLOAD PARSING                  │
  │                      (Multiple times, fast)                  │
  ├─────────────────────────────────────────────────────────────┤
  │                                                              │
  │  Hex Payload File (e.g., "payload.hex")                    │
  │         │                                                    │
  │  Metadata JSON (from Step 1)                                │
  │         │                                                    │
  │         ├─► HexInputParser    → Parse hex input            │
  │         ├─► HeaderDecoder     → Decode header              │
  │         ├─► VersionResolver   → Determine version          │
  │         ├─► FieldDecoder      → Decode all fields          │
  │         ├─► PostProcessor     → Calculate derived values   │
  │         └─► JSONBuilder       → Format output              │
  │                                                              │
  │  OUTPUT: output.json                                         │
  │  {                                                           │
  │    "logcode_id_hex": "0xB888",                              │
  │    "fields": [...]                                           │
  │  }                                                           │
  └─────────────────────────────────────────────────────────────┘

  ---
  Complete File-by-File Breakdown

  📦 Layer 0: Module Exports (hex_decoder_module/__init__.py)

  Purpose: Public API surface for external consumers

  Key Exports:
  from .ingest.hex_parser import parse_hex_input
  from .icd_parser.icd_query import ICDQueryEngine
  from .decoder.payload_decoder import PayloadDecoder
  from .export.json_builder import JSONBuilder
  from .export.file_writer import FileWriter

  Usage Example:
  from hex_decoder_module import ICDQueryEngine, PayloadDecoder

  # Create query engine
  icd = ICDQueryEngine("path/to/icd.pdf")

  # Create decoder
  decoder = PayloadDecoder(icd)

  ---
  🎯 Layer 1: Entry Points (CLI Files)

  1. metadata_cli.py - Metadata Generation CLI

  Role: Command-line interface for Step 1 (metadata generation)

  Key Functions:
  - generate_single_logcode(args) - Lines 17-54
    - Calls MetadataGenerator.generate_logcode_metadata()
    - Saves result to JSON file
    - Prints summary statistics

  Workflow:
  # User runs:
  # python -m hex_decoder_module.metadata_cli single --logcode 0xB888 --pdf icd.pdf -o metadata.json

  # What happens internally:
  generator = MetadataGenerator(pdf_path, enable_cache=True)  # Line 25
  metadata = generator.generate_logcode_metadata("0xB888")    # Line 28
  generator.save_to_file(metadata, "metadata.json")           # Line 31

  Output: JSON file with complete logcode structure

  ---
  2. cli.py - Single-Step Decode CLI

  Role: One-shot decode without saving metadata (internal API)

  When to Use: Quick decode where metadata reuse isn't needed

  ---
  3. scripts/parse_payload.py - Payload Parsing Script

  Role: Command-line interface for Step 2 (payload decoding)

  Usage:
  python scripts/parse_payload.py \
    -i payload.hex \
    -m metadata_0xB888.json \
    -o output.json

  ---
  📋 Layer 2: Data Models (hex_decoder_module/models/)

  These define the data structures used throughout the system.

  packet.py - Input Data Models

  Key Classes:
  - ParsedPacket - Raw parsed packet (header + payload bytes)
  - Header - Decoded header information

  Purpose: Represents the initial parsed form before decoding

  ---
  decoded.py - Output Data Models

  Key Classes:
  - DecodedPacket - Fully decoded packet with all fields
  - DecodedField - Individual decoded field with raw and friendly values

  Example:
  @dataclass
  class DecodedField:
      name: str               # e.g., "Num CA"
      raw_value: int          # e.g., 3
      friendly_value: str     # e.g., "3 carriers"
      offset_bytes: int
      length_bits: int
      type_name: str

  ---
  icd.py - ICD Metadata Structures

  Key Classes:
  - FieldDefinition - Defines how to decode a single field
  - LogcodeMetadata - Complete metadata for a logcode
  - RawTable - Raw extracted table from PDF

  Critical Structure:
  @dataclass
  class FieldDefinition:
      name: str               # "Num CA"
      type_name: str          # "Unsigned (8 bits)"
      count: int              # 1 (or -1 for repeating)
      offset_bytes: int       # 4
      offset_bits: int        # 0
      length_bits: int        # 8
      description: str

  ---
  errors.py - Exception Hierarchy

  Custom Exceptions:
  - HexDecoderError (base)
  - LogcodeNotFoundError
  - VersionNotFoundError
  - PayloadTooShortError
  - FieldDecodingError

  ---
  📥 Layer 3: Input Layer (hex_decoder_module/ingest/)

  hex_parser.py - Parse Hex Input

  Role: Parse hex strings and files into byte arrays

  Key Function:
  def parse_hex_input(input_data: str) -> ParsedPacket:
      # Handles:
      # - "B8 88 00 01 ..." (space-separated)
      # - "B888000100" (no spaces)
      # - File paths
      # Returns ParsedPacket with header_bytes and payload_bytes

  ---
  validators.py - Input Validation

  Role: Validate hex strings, file paths, logcode formats

  ---
  🔍 Layer 4: PDF Parsing (hex_decoder_module/icd_parser/)

  This is the heart of the system - extracts structure from PDF documents.

  pdf_scanner.py - Locate Logcode Sections

  Role: Scan PDF to find where a logcode is defined

  Algorithm:
  1. Search PDF text for pattern: 4.X <NAME> (0xB888)
  2. Extract section number and title
  3. Determine page range for section
  4. Return LogcodeSectionInfo

  Example:
  scanner = PDFScanner("icd.pdf")
  section = scanner.find_section("0xB888")
  # Returns: LogcodeSectionInfo(
  #   section_number="4.52",
  #   section_title="NR5G LL1 Serving Cell Measurement and Results",
  #   start_page=287,
  #   end_page=292
  # )

  ---
  section_extractor.py - Extract Tables from Section

  Role: Extract all tables from the logcode's section

  Process:
  1. Open PDF at section pages
  2. Use pdfplumber to extract tables
  3. Match tables with captions (e.g., "Table 7-2801")
  4. Return list of RawTable objects

  ---
  table_parser.py - Parse Tables to Field Definitions

  Role: Convert raw table data into structured FieldDefinition objects

  Expected Table Format:
  Name          | Type Name         | Cnt | Off | Len | Description
  ---------------------------------------------------------------------------
  Version       | Unsigned (8 bits) | 1   | 0   | 8   | Version field
  Num CA        | Unsigned (8 bits) | 1   | 4   | 8   | Number of carriers

  Parsing Logic:
  def parse_field_table(raw_table: RawTable) -> List[FieldDefinition]:
      fields = []
      for row in raw_table.rows[1:]:  # Skip header
          name = row[0]
          type_name = row[1]
          count = int(row[2]) if row[2] != '-1' else -1
          offset_bytes = int(row[3])
          length_bits = int(row[4])
          description = row[5]

          fields.append(FieldDefinition(
              name, type_name, count, offset_bytes, 0, length_bits, description
          ))
      return fields

  ---
  version_parser.py - Parse Version Mappings

  Role: Extract version-to-table mappings

  Example Table (logcode 0xB888_Versions):
  Version | Table
  ------------------
  2       | 7-2801
  3       | 7-2802

  Output:
  {2: "7-2801", 3: "7-2802"}

  ---
  dependency_resolver.py - Resolve Table References

  Role: Find tables referenced by other tables

  Example:
  - Table 7-2801 has field with Type Name = "Table 7-2803"
  - This creates a dependency: 7-2801 → 7-2803
  - The resolver tracks these relationships

  Why Important: Some field structures are defined in separate tables that must be fetched recursively.

  ---
  cache.py - LRU Cache

  Role: Cache parsed logcode metadata to avoid re-parsing

  Benefit: Second request for same logcode is instant (no PDF scanning)

  ---
  icd_query.py - Query API Engine (CRITICAL FILE)

  Role: Main orchestrator for PDF parsing - coordinates all ICD parser components

  Key Method: get_logcode_metadata() (Lines 37-125)

  This is the core workflow for Step 1:

  def get_logcode_metadata(self, logcode_id: str) -> LogcodeMetadata:
      # STEP 1: Scan PDF to find section
      section_info = self.scanner.find_section(logcode_id)  # Line 64

      # STEP 2: Extract all tables from section
      raw_tables = self.extractor.extract_tables(self.pdf_path, section_info)  # Line 67

      # STEP 3: Separate version table from field tables
      version_table = None
      field_tables = []
      for raw_table in raw_tables:
          if self.version_parser.is_version_table(raw_table.caption):
              version_table = raw_table
          else:
              field_tables.append(raw_table)

      # STEP 4: Parse version table
      version_map = self.version_parser.parse_version_table(version_table)  # Line 83

      # STEP 5: Parse field tables and build dependency graph
      table_definitions = {}
      dependencies = {}
      for raw_table in field_tables:
          table_name = extract_table_number(raw_table.caption)  # "7-2801"
          field_defs = self.table_parser.parse_field_table(raw_table)  # Line 95
          table_definitions[table_name] = field_defs

          deps = self.dep_resolver.find_dependencies(field_defs)  # Line 101
          dependencies[table_name] = list(deps)

      # STEP 6: Fetch dependent tables not in current section
      self._fetch_dependent_tables(dependencies, table_definitions, section_info)  # Line 106

      # STEP 7: Build metadata object
      return LogcodeMetadata(
          logcode_id=logcode_id,
          logcode_name=section_info.section_title,
          version_map=version_map,
          table_definitions=table_definitions,
          dependencies=dependencies
      )

  Key Insight: _fetch_dependent_tables() (Lines 252-361) searches nearby PDF pages for tables referenced but not in the main section - this handles cross-references.

  ---
  ⚙️ Layer 5: Decoding (hex_decoder_module/decoder/)

  This layer converts raw bytes into structured data using metadata.

  header_decoder.py - Decode Packet Header

  Role: Extract standard header fields (timestamp, logcode ID, etc.)

  ---
  version_resolver.py - Determine Version

  Role: Read version field from payload to determine which table layout to use

  Example:
  # Payload bytes: B8 88 00 02 ...
  #                       ^^ version = 2
  # Look up version 2 → Table 7-2801

  ---
  field_decoder.py - Decode Individual Fields (CRITICAL)

  Role: Extract field values from byte arrays based on field definitions

  Core Algorithm:
  def decode(self, payload: bytes, field_def: FieldDefinition) -> DecodedField:
      # Step 1: Extract raw bytes
      offset = field_def.offset_bytes
      length = field_def.length_bits

      # Step 2: Extract bits if needed
      raw_value = extract_bits(payload, offset, length)

      # Step 3: Convert to appropriate type based on type_name
      if "Unsigned" in field_def.type_name:
          value = int(raw_value)
      elif "Signed" in field_def.type_name:
          value = twos_complement(raw_value, length)
      elif "Enum" in field_def.type_name:
          value = map_enum(raw_value, field_def.type_name)

      return DecodedField(
          name=field_def.name,
          raw_value=value,
          friendly_value=format_friendly(value),
          ...
      )

  ---
  field_post_processor.py - Post-Processing

  Role: Calculate derived values (e.g., BLER from ACK/NACK counts)

  Example:
  # After decoding all fields:
  # - ACK Count = 95
  # - NACK Count = 5
  # Post-processor adds:
  # - BLER = 5 / (95 + 5) = 5%

  ---
  payload_decoder.py - Main Orchestrator (CRITICAL FILE)

  Role: Main orchestrator for Step 2 - coordinates all decoding components

  Key Method: decode() (Lines 32-131)

  This is the core workflow for Step 2:

  def decode(self, parsed_packet: ParsedPacket) -> DecodedPacket:
      # Step 1: Decode header to get logcode ID
      header = self.header_decoder.decode(parsed_packet.header_bytes)  # Line 49
      logcode_id_hex = "0x" + hex(header.logcode_id)[2:].upper()

      # Step 2: Fetch logcode metadata (from cache or PDF)
      metadata = self.icd.get_logcode_metadata(logcode_id_hex)  # Line 54

      # Step 3: Resolve version from payload
      version_info = self.version_resolver.resolve(
          parsed_packet.payload_bytes,
          metadata
      )  # Line 59

      # Step 4: Get field layout for this version
      table_name = metadata.version_map.get(version_info.version_value)  # Line 67
      raw_field_definitions = metadata.table_definitions.get(table_name)  # Line 73

      # Step 5: Decode all fields
      decoded_fields = []
      for field_def in raw_field_definitions:
          if field_def.count == -1:  # Repeating structure
              records = self._decode_repeating_structure(...)  # Line 100
              decoded_fields.extend(records)
          else:  # Regular field
              decoded_field = self.field_decoder.decode(payload, field_def)  # Line 109
              decoded_fields.append(decoded_field)

      # Step 5.5: Post-process (calculate BLER, etc.)
      decoded_fields = self.post_processor.process(decoded_fields, logcode_id_hex)  # Line 116

      # Step 6: Assemble final result
      return DecodedPacket(
          logcode_id_hex=logcode_id_hex,
          version_resolved=version_info.table_name,
          fields=decoded_fields
      )

  Critical Feature: Repeating Structures (Lines 133-209)

  Handles dynamic arrays (e.g., "Records" with count determined at runtime):

  def _decode_repeating_structure(self, payload, repeating_field_def, metadata_obj):
      # Step 1: Get referenced table (e.g., "Table 7-2803")
      ref_table_name = extract_table_ref(repeating_field_def.type_name)
      ref_table_fields = metadata_obj.table_definitions[ref_table_name]

      # Step 2: Calculate record size
      record_size_bytes = calculate_size(ref_table_fields)

      # Step 3: Determine count (from "Num CA" or "Num Records" field)
      actual_count = self._get_repetition_count(already_decoded_fields)  # Lines 211-241

      # Step 4: Decode each record
      for record_idx in range(actual_count):
          record_offset = base_offset + (record_idx * record_size_bytes)
          for ref_field in ref_table_fields:
              adjusted_field = adjust_offset(ref_field, record_offset)
              decoded_field = self.field_decoder.decode(payload, adjusted_field)
              decoded_records.append(decoded_field)

      return decoded_records

  Key Insight: _get_repetition_count() (Lines 211-241) looks for fields like "Num CA" or counts bits in "Cumulative Bitmask" to determine array size.

  ---
  📤 Layer 6: Export (hex_decoder_module/export/)

  metadata_generator.py - Generate Metadata JSON

  Role: Convert LogcodeMetadata objects into JSON format for Step 1 output

  ---
  json_builder.py - Build Structured JSON

  Role: Format DecodedPacket objects into pretty JSON for Step 2 output

  ---
  file_writer.py - Write to Disk

  Role: Handle file I/O with error handling

  ---
  🛠️ Layer 7: Utilities (hex_decoder_module/utils/)

  byte_ops.py - Byte Operations

  Key Functions:
  extract_bits(data, offset_bytes, offset_bits, length_bits) -> int
  uint_to_hex_string(value, prefix=True, width=4) -> str

  ---
  type_converters.py - Type-Specific Decoders

  Handles:
  - Unsigned integers
  - Signed integers (two's complement)
  - Floats
  - Enums
  - Booleans

  ---
  enum_mapper.py - Enum Mapping

  Role: Convert numeric values to human-readable enum names

  Example:
  # Type Name: "Enum(0=Idle, 1=Active, 2=Sleep)"
  # Raw value: 1
  # Friendly value: "Active"

  ---
  Complete Data Flow Example

  Let's trace a real decode operation:

  Step 1: Generate Metadata (Once)

  python -m hex_decoder_module.metadata_cli single \
    --logcode 0xB888 \
    --pdf NR5G_ICD.pdf \
    -o metadata_0xB888.json

  Internal Flow:
  1. metadata_cli.py:generate_single_logcode() called
  2. Creates MetadataGenerator which creates ICDQueryEngine
  3. ICDQueryEngine.get_logcode_metadata("0xB888"):
    - PDFScanner → finds section "4.52" on pages 287-292
    - SectionExtractor → extracts 3 tables
    - TableParser → parses Table 7-2801, 7-2802, 7-2803
    - VersionParser → version 2 → Table 7-2801
    - DependencyResolver → 7-2801 depends on 7-2803
    - _fetch_dependent_tables() → fetches Table 7-2803
  4. MetadataGenerator.save_to_file() → writes JSON

  Output (metadata_0xB888.json):
  {
    "logcode_id": "0xB888",
    "logcode_name": "NR5G LL1 Serving Cell Measurement",
    "versions": {
      "2": "7-2801",
      "3": "7-2802"
    },
    "all_tables": {
      "7-2801": [
        {
          "name": "Version",
          "type_name": "Unsigned (8 bits)",
          "offset_bytes": 0,
          "length_bits": 8
        },
        {
          "name": "Num CA",
          "type_name": "Unsigned (8 bits)",
          "offset_bytes": 4,
          "length_bits": 8
        },
        {
          "name": "Records",
          "type_name": "Table 7-2803",
          "count": -1,
          "offset_bytes": 8
        }
      ],
      "7-2803": [
        {
          "name": "Carrier Index",
          "offset_bytes": 0,
          "length_bits": 8
        },
        {
          "name": "RSRP",
          "offset_bytes": 1,
          "length_bits": 16
        }
      ]
    }
  }

  Step 2: Decode Payload (Many times)

  Input (payload.hex):
  B8 88 00 02 00 00 00 03 00 AA BB 01 CC DD 02 EE FF

  python scripts/parse_payload.py \
    -i payload.hex \
    -m metadata_0xB888.json \
    -o output.json

  Internal Flow:
  1. parse_payload.py loads metadata JSON
  2. HexInputParser.parse() → converts to bytes
  3. PayloadDecoder.decode():
    - HeaderDecoder → logcode = 0xB888
    - VersionResolver → version = 2 → Table 7-2801
    - FieldDecoder:
        - Decode "Version" @ offset 0 → 2
      - Decode "Num CA" @ offset 4 → 3
      - Decode "Records" (repeating):
            - Count = 3 (from "Num CA")
        - Record 0: Carrier Index=0, RSRP=-86 dBm
        - Record 1: Carrier Index=1, RSRP=-52 dBm
        - Record 2: Carrier Index=2, RSRP=-18 dBm
    - FieldPostProcessor → adds derived fields
  4. JSONBuilder → formats output

  Output (output.json):
  {
    "logcode_id_hex": "0xB888",
    "logcode_name": "NR5G LL1 Serving Cell Measurement",
    "version_resolved": "7-2801",
    "fields": [
      {
        "name": "Version",
        "raw_value": 2,
        "friendly_value": "2"
      },
      {
        "name": "Num CA",
        "raw_value": 3,
        "friendly_value": "3 carriers"
      },
      {
        "name": "Carrier Index (Record 0)",
        "raw_value": 0,
        "friendly_value": "0"
      },
      {
        "name": "RSRP (Record 0)",
        "raw_value": 170,
        "friendly_value": "-86 dBm"
      },
      {
        "name": "Carrier Index (Record 1)",
        "raw_value": 1,
        "friendly_value": "1"
      },
      {
        "name": "RSRP (Record 1)",
        "raw_value": 204,
        "friendly_value": "-52 dBm"
      },
      {
        "name": "Carrier Index (Record 2)",
        "raw_value": 2,
        "friendly_value": "2"
      },
      {
        "name": "RSRP (Record 2)",
        "raw_value": 238,
        "friendly_value": "-18 dBm"
      }
    ]
  }

  ---
  Key Design Decisions

  1. Two-Step Architecture

  Why: Separates slow PDF parsing (once) from fast decoding (many times). Metadata reuse improves performance 100x.

  2. On-Demand PDF Parsing

  Why: No preprocessing required. Users can decode any logcode without building a complete database first.

  3. Dependency Resolution

  Why: ICD tables reference each other. Automatic resolution handles complex nested structures.

  4. Repeating Structure Support

  Why: Real-world packets have variable-length arrays. System dynamically determines array sizes.

  5. Cache with LRU Eviction

  Why: Balances memory usage with performance. Most-used logcodes stay cached.

  ---
  Performance Characteristics

  | Operation                         | Time         | Notes                  |
  |-----------------------------------|--------------|------------------------|
  | First metadata generation         | 5-10 seconds | PDF scanning + parsing |
  | Cached metadata lookup            | <1ms         | In-memory cache hit    |
  | Payload decode (with metadata)    | 10-50ms      | Depends on field count |
  | Payload decode (without metadata) | 5-10 seconds | Triggers PDF scan      |

  ---
  Dependencies & Requirements

  pdfplumber>=0.10.3   # Table extraction from PDF
  PyMuPDF>=1.23.8      # PDF text/structure parsing (imported as fitz)

  Standard library: dataclasses, typing, argparse, pathlib, json, re, copy

  ---
  Common Extension Points

  Adding New Type Converters

  File: utils/type_converters.py

  Example: Add support for "Float32" type:
  def decode_float32(raw_bytes: bytes) -> float:
      return struct.unpack('!f', raw_bytes)[0]

  Adding New Post-Processors

  File: decoder/field_post_processor.py

  Example: Add SINR calculation:
  def _calculate_sinr(self, fields):
      rsrp = find_field(fields, "RSRP")
      rssi = find_field(fields, "RSSI")
      return rsrp - rssi

  Adding New Export Formats

  File: export/ directory

  Example: Add CSV export:
  class CSVExporter:
      def export(self, decoded_packet: DecodedPacket) -> str:
          # Generate CSV format
          pass

  ---
  This guide provides the complete picture of how nr5g_hex_decoder works. Use it to onboard new developers or extend the system with new features!