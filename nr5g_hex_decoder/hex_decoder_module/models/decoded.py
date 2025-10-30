"""
Data structures for decoded packet output.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Union, Optional
from .packet import Header


@dataclass
class DecodedField:
    """Single decoded field with raw + friendly value"""
    name: str
    type_name: str
    raw_value: Union[int, bool, str]
    friendly_value: Optional[str]  # Human-readable (for enums, bools)
    description: str


@dataclass
class DecodedPacket:
    """Complete decoded packet ready for export"""
    logcode_id_hex: str            # "0xB823"
    logcode_id_decimal: int        # 47139
    logcode_name: str
    version_raw: str               # "0x30002"
    version_resolved: str          # Table name or version identifier
    header: Header
    fields: List[DecodedField]
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info
