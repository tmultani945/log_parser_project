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
from .field_post_processor import FieldPostProcessor


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
        self.post_processor = FieldPostProcessor()

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

        # Step 4: Get field layout for this version (raw, before expansion)
        # We need the raw layout to detect repeating structures
        metadata_obj = self.icd.get_logcode_metadata(logcode_id_hex)
        table_name = metadata_obj.version_map.get(version_info.version_value)

        if not table_name:
            raise VersionNotFoundError(logcode_id_hex, version_info.version_value)

        # Get raw field definitions (before table reference expansion)
        raw_field_definitions = metadata_obj.table_definitions.get(table_name, [])

        if not raw_field_definitions:
            raise VersionNotFoundError(logcode_id_hex, version_info.version_value)

        # Step 5: Decode all fields (handling repeating structures)
        # Account for version offset (version field comes before payload fields)
        version_offset_bytes = (metadata_obj.version_offset +
                               (metadata_obj.version_length + 7) // 8)

        decoded_fields = []
        payload = parsed_packet.payload_bytes

        for field_def in raw_field_definitions:
            try:
                # Adjust field offset to account for version
                from copy import deepcopy
                adjusted_field = deepcopy(field_def)
                total_offset_bits = (adjusted_field.offset_bytes * 8 +
                                    adjusted_field.offset_bits +
                                    version_offset_bytes * 8)
                adjusted_field.offset_bytes = total_offset_bits // 8
                adjusted_field.offset_bits = total_offset_bits % 8

                # Check if this is a repeating structure (count=-1 and type is Table reference)
                if adjusted_field.count == -1 and 'Table' in adjusted_field.type_name:
                    # This is a repeating structure - decode multiple times
                    records = self._decode_repeating_structure(
                        payload,
                        adjusted_field,
                        metadata_obj,
                        decoded_fields
                    )
                    decoded_fields.extend(records)
                else:
                    # Regular field - decode once
                    decoded_field = self.field_decoder.decode(payload, adjusted_field)
                    decoded_fields.append(decoded_field)
            except Exception as e:
                # Log error but continue with other fields
                print(f"Warning: Failed to decode field '{field_def.name}': {e}")

        # Step 5.5: Post-process fields (calculate derived values like BLER)
        decoded_fields = self.post_processor.process(decoded_fields, logcode_id_hex)

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

    def _decode_repeating_structure(
        self,
        payload: bytes,
        repeating_field_def,
        metadata_obj,
        already_decoded_fields: list
    ) -> list:
        """
        Decode a repeating structure (e.g., Records array).

        Args:
            payload: Raw payload bytes
            repeating_field_def: Field definition for the repeating structure
            metadata_obj: Logcode metadata with table definitions
            already_decoded_fields: Already decoded fields (to find count values)

        Returns:
            List of decoded fields organized as repeating records
        """
        import re
        from copy import deepcopy

        # Step 1: Get the table reference (e.g., "Table 7-2803")
        table_ref_match = re.search(r'Table\s+(\d+-\d+)', repeating_field_def.type_name, re.IGNORECASE)
        if not table_ref_match:
            return []

        ref_table_name = table_ref_match.group(1)
        ref_table_fields = metadata_obj.table_definitions.get(ref_table_name, [])

        if not ref_table_fields:
            return []

        # Step 2: Calculate the size of one record in bytes
        record_size_bits = max(
            (f.offset_bytes * 8 + f.offset_bits + f.length_bits) for f in ref_table_fields
        )
        record_size_bytes = (record_size_bits + 7) // 8

        # Step 3: Determine the repetition count
        # First, get the logical count from count fields
        logical_count = self._get_repetition_count(already_decoded_fields)

        # Then, calculate how many records can actually fit in the payload
        base_offset_bytes = repeating_field_def.offset_bytes
        available_bytes = len(payload) - base_offset_bytes
        max_records_in_payload = available_bytes // record_size_bytes

        # Use the minimum of logical count and what fits in payload
        actual_count = min(logical_count, max_records_in_payload)

        if actual_count == 0:
            return []  # No records to decode

        # Step 4: Decode each record
        decoded_records = []

        for record_idx in range(actual_count):
            # Calculate offset for this record
            record_offset = base_offset_bytes + (record_idx * record_size_bytes)

            # Decode all fields in this record
            for ref_field in ref_table_fields:
                # Create adjusted field definition for this record
                adjusted_field = deepcopy(ref_field)
                adjusted_field.offset_bytes += record_offset

                # Add record index to field name for clarity
                adjusted_field.name = f"{adjusted_field.name} (Record {record_idx})"

                try:
                    decoded_field = self.field_decoder.decode(payload, adjusted_field)
                    decoded_records.append(decoded_field)
                except Exception as e:
                    print(f"Warning: Failed to decode {adjusted_field.name}: {e}")

        return decoded_records

    def _get_repetition_count(self, already_decoded_fields: list) -> int:
        """
        Determine repetition count from already decoded fields.

        Looks for fields like "Num CA", "Num Records", or "Cumulative Bitmask".

        Args:
            already_decoded_fields: List of already decoded fields

        Returns:
            Repetition count (integer)
        """
        # Create a lookup map
        field_map = {f.name: f for f in already_decoded_fields}

        # Try "Num CA" first (number of carriers)
        if "Num CA" in field_map:
            return field_map["Num CA"].raw_value

        # Try "Num Records"
        if "Num Records" in field_map:
            return field_map["Num Records"].raw_value

        # Try "Cumulative Bitmask" - count the number of set bits
        if "Cumulative Bitmask" in field_map:
            bitmask = field_map["Cumulative Bitmask"].raw_value
            # Count set bits
            return bin(bitmask).count('1')

        # Default: assume 1 record
        return 1
