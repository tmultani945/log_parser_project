"""
Decode individual fields from payload.
"""

from ..models.icd import FieldDefinition
from ..models.decoded import DecodedField
from ..models.errors import PayloadTooShortError, FieldDecodingError
from ..utils.type_converters import decode_uint, decode_bool, decode_enum, decode_signed_int


class FieldDecoder:
    """Decodes individual fields from payload bytes"""

    def decode(self, payload: bytes, field_def: FieldDefinition) -> DecodedField:
        """
        Decode a single field from payload.

        Args:
            payload: Raw payload bytes
            field_def: Field definition from ICD

        Returns:
            DecodedField with raw and friendly values

        Raises:
            PayloadTooShortError: If field extends beyond payload
            FieldDecodingError: If field decoding fails
        """
        # Calculate required payload length
        required_bytes = field_def.offset_bytes + ((field_def.length_bits + 7) // 8)

        if len(payload) < required_bytes:
            raise PayloadTooShortError(required_bytes, len(payload), field_def.name)

        try:
            # Decode based on type
            type_name = field_def.type_name.lower()

            if 'uint' in type_name or 'unsigned' in type_name:
                raw_value = decode_uint(
                    payload,
                    field_def.offset_bytes,
                    field_def.length_bits,
                    field_def.offset_bits
                )
                friendly_value = None

            elif 'int' in type_name and 'uint' not in type_name:
                # Signed integer
                raw_value = decode_signed_int(
                    payload,
                    field_def.offset_bytes,
                    field_def.length_bits,
                    field_def.offset_bits
                )
                friendly_value = None

            elif 'bool' in type_name:
                raw_value = decode_bool(
                    payload,
                    field_def.offset_bytes,
                    field_def.offset_bits
                )
                friendly_value = str(raw_value).lower()

            elif 'enum' in type_name:
                if field_def.enum_mappings:
                    raw_value, friendly_value = decode_enum(
                        payload,
                        field_def.offset_bytes,
                        field_def.length_bits,
                        field_def.enum_mappings,
                        field_def.offset_bits
                    )
                else:
                    # No mappings - treat as uint
                    raw_value = decode_uint(
                        payload,
                        field_def.offset_bytes,
                        field_def.length_bits,
                        field_def.offset_bits
                    )
                    friendly_value = None

            else:
                # Unknown type - treat as raw bytes
                raw_value = decode_uint(
                    payload,
                    field_def.offset_bytes,
                    field_def.length_bits,
                    field_def.offset_bits
                )
                friendly_value = None

            return DecodedField(
                name=field_def.name,
                type_name=field_def.type_name,
                raw_value=raw_value,
                friendly_value=friendly_value,
                description=field_def.description
            )

        except Exception as e:
            raise FieldDecodingError(field_def.name, str(e))
