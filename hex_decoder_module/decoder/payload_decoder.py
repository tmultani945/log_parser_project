"""
Main orchestrator for decoding packets.
"""

from ..models.packet import ParsedPacket
from ..models.decoded import DecodedPacket
from ..models.errors import LogcodeNotFoundError, VersionNotFoundError
from ..icd_parser.icd_query import ICDQueryEngine
from ..utils.byte_ops import uint_to_hex_string
from .header_decoder import HeaderDecoder
from .version_resolver import VersionResolver
from .field_decoder import FieldDecoder


class PayloadDecoder:
    """Main orchestrator for decoding packets"""

    def __init__(self, icd_query_engine: ICDQueryEngine):
        """
        Initialize decoder.

        Args:
            icd_query_engine: ICD query engine for metadata lookup
        """
        self.icd = icd_query_engine
        self.header_decoder = HeaderDecoder()
        self.version_resolver = VersionResolver()
        self.field_decoder = FieldDecoder()

    def decode(self, parsed_packet: ParsedPacket) -> DecodedPacket:
        """
        Decode a parsed packet into structured data.

        Args:
            parsed_packet: Parsed packet with header and payload bytes

        Returns:
            DecodedPacket ready for export

        Raises:
            LogcodeNotFoundError: If logcode not in ICD
            VersionNotFoundError: If version not defined
            PayloadTooShortError: If payload is too short
            FieldDecodingError: If field decoding fails
        """
        # Step 1: Decode header to get logcode ID
        header = self.header_decoder.decode(parsed_packet.header_bytes)
        logcode_id_hex = uint_to_hex_string(header.logcode_id, prefix=True, width=4)

        # Step 2: Fetch logcode metadata from ICD (may trigger PDF scan)
        try:
            metadata = self.icd.get_logcode_metadata(logcode_id_hex)
        except Exception as e:
            raise LogcodeNotFoundError(logcode_id_hex)

        # Step 3: Resolve version from payload
        version_info = self.version_resolver.resolve(
            parsed_packet.payload_bytes,
            metadata
        )

        # Step 4: Get field layout for this version
        field_definitions = self.icd.get_version_layout(
            logcode_id_hex,
            version_info.version_value
        )

        if not field_definitions:
            raise VersionNotFoundError(
                logcode_id_hex,
                version_info.version_value
            )

        # Step 5: Decode all fields
        decoded_fields = []
        payload = parsed_packet.payload_bytes

        for field_def in field_definitions:
            try:
                decoded_field = self.field_decoder.decode(payload, field_def)
                decoded_fields.append(decoded_field)
            except Exception as e:
                # Log error but continue with other fields
                # In production, you might want to add a "warnings" field
                print(f"Warning: Failed to decode field '{field_def.name}': {e}")

        # Step 6: Assemble final result
        return DecodedPacket(
            logcode_id_hex=logcode_id_hex,
            logcode_id_decimal=header.logcode_id,
            logcode_name=metadata.logcode_name,
            version_raw=version_info.version_hex,
            version_resolved=version_info.table_name,
            header=header,
            fields=decoded_fields,
            metadata={
                'section': metadata.section,
                'total_fields': len(decoded_fields)
            }
        )
