"""
Data structures for ICD metadata and field definitions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LogcodeSectionInfo:
    """Information about where a logcode section is located in PDF"""
    logcode_id: str
    section_number: str            # e.g., "4.3"
    section_title: str             # e.g., "Nr5g_RrcServingCellInfo"
    start_page: int                # PDF page number (0-indexed)
    end_page: int                  # Where this section ends


@dataclass
class RawTable:
    """Raw table extracted from PDF before parsing"""
    caption: str                   # e.g., "Table 4-4"
    rows: List[List[str]]          # List of row data (each row is a list of cell values)
    page_num: int


@dataclass
class FieldDefinition:
    """Single field definition from ICD table"""
    name: str                      # e.g., "Physical Cell ID"
    type_name: str                 # "Uint16", "Bool", "Enum", etc.
    offset_bytes: int              # Byte offset from start of struct
    offset_bits: int               # Additional bit offset (for bit fields)
    length_bits: int               # Length in bits
    description: str
    enum_mappings: Optional[Dict[int, str]] = None  # For enum types
    count: Optional[int] = None    # Repetition count (from Cnt column)


@dataclass
class LogcodeMetadata:
    """Metadata about a logcode from ICD"""
    logcode_id: str                # e.g., "0x1C07"
    logcode_name: str              # e.g., "Nr5g_RrcServingCellInfo"
    section: str                   # e.g., "4.1"
    description: str
    version_offset: int            # Byte offset of version field in payload
    version_length: int            # Bit length of version field
    version_map: Dict[int, str] = field(default_factory=dict)  # version → table_name
    table_definitions: Dict[str, List[FieldDefinition]] = field(default_factory=dict)  # table_name → fields
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # table_name → [dependent_tables]


@dataclass
class VersionInfo:
    """Information about the resolved version"""
    version_value: int             # Raw version number
    version_hex: str               # Hex representation (e.g., "0x30002")
    table_name: str                # Associated table name (e.g., "4-4")
