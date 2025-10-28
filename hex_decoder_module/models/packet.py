"""
Data structures for parsed packets and headers.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedPacket:
    """Raw packet after hex parsing"""
    length: int                    # Declared length
    header_bytes: bytes            # Raw header (first 12 bytes typically)
    payload_bytes: bytes           # Everything after header
    raw_input: str                 # Original hex input for debugging


@dataclass
class Header:
    """Decoded header fields"""
    length_bytes: int              # Total packet length
    logcode_id: int                # Extracted logcode (e.g., 0xB823)
    sequence: Optional[int]        # Sequence number if present
    timestamp_raw: Optional[int]   # Raw timestamp if present
