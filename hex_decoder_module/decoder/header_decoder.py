"""
Decode packet header to extract logcode and other metadata.
"""

from ..models.packet import Header
from ..models.errors import PayloadTooShortError
from ..utils.byte_ops import bytes_to_uint_le


class HeaderDecoder:
    """Decodes packet headers"""

    # Standard header structure (12 bytes):
    # [0:2]   Total length (Uint16 LE)
    # [2:4]   Logcode ID (Uint16 LE) ← KEY FIELD
    # [4:8]   Timestamp (Uint32 LE)
    # [8:12]  Sequence (Uint32 LE)

    HEADER_MIN_SIZE = 12

    def decode(self, header_bytes: bytes) -> Header:
        """
        Decode packet header.

        Args:
            header_bytes: Raw header bytes (at least 12 bytes)

        Returns:
            Header object

        Raises:
            PayloadTooShortError: If header is too short
        """
        if len(header_bytes) < self.HEADER_MIN_SIZE:
            raise PayloadTooShortError(
                self.HEADER_MIN_SIZE,
                len(header_bytes),
                "header"
            )

        # Extract fields
        length_bytes = bytes_to_uint_le(header_bytes, 0, 2)
        logcode_id = bytes_to_uint_le(header_bytes, 2, 2)

        # Optional fields
        timestamp_raw = None
        sequence = None

        if len(header_bytes) >= 8:
            timestamp_raw = bytes_to_uint_le(header_bytes, 4, 4)

        if len(header_bytes) >= 12:
            sequence = bytes_to_uint_le(header_bytes, 8, 4)

        return Header(
            length_bytes=length_bytes,
            logcode_id=logcode_id,
            sequence=sequence,
            timestamp_raw=timestamp_raw
        )
