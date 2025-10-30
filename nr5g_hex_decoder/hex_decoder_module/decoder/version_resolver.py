"""
Resolve version field from payload.
"""

from ..models.icd import VersionInfo, LogcodeMetadata
from ..models.errors import PayloadTooShortError
from ..utils.byte_ops import bytes_to_uint_le, uint_to_hex_string


class VersionResolver:
    """Resolves version information from payload"""

    def resolve(self, payload_bytes: bytes, metadata: LogcodeMetadata) -> VersionInfo:
        """
        Extract and resolve version from payload.

        Args:
            payload_bytes: Raw payload bytes
            metadata: Logcode metadata with version info

        Returns:
            VersionInfo with resolved version

        Raises:
            PayloadTooShortError: If payload is too short for version field
        """
        offset = metadata.version_offset
        length_bits = metadata.version_length
        length_bytes = (length_bits + 7) // 8

        # Check payload length
        if len(payload_bytes) < offset + length_bytes:
            raise PayloadTooShortError(
                offset + length_bytes,
                len(payload_bytes),
                "version field"
            )

        # Extract version value
        version_value = bytes_to_uint_le(payload_bytes, offset, length_bytes)

        # Format as hex
        version_hex = uint_to_hex_string(version_value, prefix=True, width=length_bytes * 2)

        # Look up table name
        table_name = metadata.version_map.get(version_value, "unknown")

        # If no mapping found, try to use first available table
        if table_name == "unknown" and metadata.table_definitions:
            table_name = list(metadata.table_definitions.keys())[0]

        return VersionInfo(
            version_value=version_value,
            version_hex=version_hex,
            table_name=table_name
        )
