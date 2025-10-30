"""
Build JSON output from decoded packet data.
"""

from typing import Dict, Any
from ..models.decoded import DecodedPacket


class JSONBuilder:
    """Builds JSON structure from decoded packet"""

    def build(self, decoded_packet: DecodedPacket) -> Dict[str, Any]:
        """
        Convert DecodedPacket to JSON-serializable dict.

        Args:
            decoded_packet: Decoded packet data

        Returns:
            JSON-serializable dictionary
        """
        return {
            "logcode": {
                "id_hex": decoded_packet.logcode_id_hex,
                "id_decimal": decoded_packet.logcode_id_decimal,
                "name": decoded_packet.logcode_name
            },
            "version": {
                "raw": decoded_packet.version_raw,
                "resolved_layout": decoded_packet.version_resolved
            },
            "header": {
                "length_bytes": decoded_packet.header.length_bytes,
                "sequence": decoded_packet.header.sequence,
                "timestamp_raw": decoded_packet.header.timestamp_raw
            },
            "fields": self._build_fields(decoded_packet.fields),
            "metadata": decoded_packet.metadata
        }

    def _build_fields(self, fields) -> Dict[str, Any]:
        """
        Build fields section of JSON.

        Args:
            fields: List of DecodedField objects

        Returns:
            Dictionary of field data
        """
        fields_dict = {}

        for field in fields:
            field_data = {
                "type": field.type_name,
                "raw": field.raw_value,
                "description": field.description
            }

            # Add decoded/friendly value if available
            if field.friendly_value is not None:
                field_data["decoded"] = field.friendly_value

            fields_dict[field.name] = field_data

        return fields_dict

    def build_compact(self, decoded_packet: DecodedPacket) -> Dict[str, Any]:
        """
        Build compact JSON (only essential fields).

        Args:
            decoded_packet: Decoded packet data

        Returns:
            Compact JSON dictionary
        """
        fields_simple = {}
        for field in decoded_packet.fields:
            # Use friendly value if available, otherwise raw
            value = field.friendly_value if field.friendly_value is not None else field.raw_value
            fields_simple[field.name] = value

        return {
            "logcode": decoded_packet.logcode_id_hex,
            "name": decoded_packet.logcode_name,
            "version": decoded_packet.version_raw,
            "fields": fields_simple
        }
