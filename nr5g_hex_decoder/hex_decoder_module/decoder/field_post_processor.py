"""
Post-processing for calculated/derived fields.

Some fields in the ICD are not raw payload data but calculated from other fields.
This module handles such post-processing after initial field decoding.
"""

from typing import List, Dict, Any, Optional
from ..models.decoded import DecodedField


class FieldPostProcessor:
    """Post-processes decoded fields to calculate derived values"""

    def __init__(self):
        """Initialize post-processor"""
        pass

    def process(self, fields: List[DecodedField], logcode_id: str) -> List[DecodedField]:
        """
        Post-process decoded fields to calculate derived values.

        Args:
            fields: List of decoded fields
            logcode_id: Logcode ID (e.g., "0xB888")

        Returns:
            Updated list of decoded fields with calculated values
        """
        # Create a field lookup dictionary for easy access
        field_map = {field.name: field for field in fields}

        # Apply logcode-specific calculations
        # Normalize logcode_id to uppercase for comparison
        logcode_id_upper = logcode_id.upper()
        if logcode_id_upper == "0XB888":  # NR5G MAC PDSCH Stats
            self._calculate_pdsch_stats(field_map)
            self._calculate_pdsch_stats_per_carrier(field_map)

        # Return the updated fields list
        return list(field_map.values())

    def _calculate_pdsch_stats(self, field_map: Dict[str, DecodedField]) -> None:
        """
        Calculate derived fields for NR5G MAC PDSCH Stats (0xB888).

        Calculates:
        - BLER: Block Error Rate = (CRC Fail / Total) × 100
        - Residual BLER: (HARQ Failures / Total) × 100 (if applicable)
        """
        # Calculate BLER if all required fields exist
        if self._has_fields(field_map, ["BLER", "Num CRC Pass TB", "Num CRC Fail TB"]):
            num_crc_pass = field_map["Num CRC Pass TB"].raw_value
            num_crc_fail = field_map["Num CRC Fail TB"].raw_value
            total = num_crc_pass + num_crc_fail

            if total > 0:
                bler_percent = (num_crc_fail / total) * 100

                # Update the BLER field with calculated value
                bler_field = field_map["BLER"]
                bler_field.raw_value = round(bler_percent, 2)
                bler_field.friendly_value = f"{bler_percent:.2f}%"
            else:
                # No transmissions - BLER is undefined/0
                bler_field = field_map["BLER"]
                bler_field.raw_value = 0.0
                bler_field.friendly_value = "0.00%"

        # Calculate Residual BLER if field exists
        if self._has_fields(field_map, ["Residual BLER", "HARQ Failure", "Num CRC Pass TB", "Num CRC Fail TB"]):
            harq_failures = field_map["HARQ Failure"].raw_value
            num_crc_pass = field_map["Num CRC Pass TB"].raw_value
            num_crc_fail = field_map["Num CRC Fail TB"].raw_value
            total = num_crc_pass + num_crc_fail

            if total > 0:
                residual_bler_percent = (harq_failures / total) * 100

                residual_bler_field = field_map["Residual BLER"]
                residual_bler_field.raw_value = round(residual_bler_percent, 2)
                residual_bler_field.friendly_value = f"{residual_bler_percent:.2f}%"
            else:
                residual_bler_field = field_map["Residual BLER"]
                residual_bler_field.raw_value = 0.0
                residual_bler_field.friendly_value = "0.00%"

    def _calculate_pdsch_stats_per_carrier(self, field_map: Dict[str, DecodedField]) -> None:
        """
        Calculate BLER and Residual BLER for each carrier record.

        For fields like "BLER (Record 0)", "BLER (Record 1)", etc.
        """
        import re

        # Find all carrier record indices
        carrier_indices = set()
        for field_name in field_map.keys():
            match = re.search(r'Record (\d+)', field_name)
            if match:
                carrier_indices.add(int(match.group(1)))

        # Calculate BLER for each carrier
        for record_idx in carrier_indices:
            bler_field_name = f"BLER (Record {record_idx})"
            crc_pass_field_name = f"Num CRC Pass TB (Record {record_idx})"
            crc_fail_field_name = f"Num CRC Fail TB (Record {record_idx})"

            if bler_field_name in field_map and crc_pass_field_name in field_map and crc_fail_field_name in field_map:
                num_crc_pass = field_map[crc_pass_field_name].raw_value
                num_crc_fail = field_map[crc_fail_field_name].raw_value
                total = num_crc_pass + num_crc_fail

                if total > 0:
                    bler_percent = (num_crc_fail / total) * 100

                    # Update the BLER field with calculated value
                    bler_field = field_map[bler_field_name]
                    bler_field.raw_value = round(bler_percent, 2)
                    bler_field.friendly_value = f"{bler_percent:.2f}%"
                else:
                    # No transmissions - BLER is undefined/0
                    bler_field = field_map[bler_field_name]
                    bler_field.raw_value = 0.0
                    bler_field.friendly_value = "0.00%"

            # Calculate Residual BLER if field exists
            residual_bler_field_name = f"Residual BLER (Record {record_idx})"
            harq_failure_field_name = f"HARQ Failure (Record {record_idx})"

            if (residual_bler_field_name in field_map and
                harq_failure_field_name in field_map and
                crc_pass_field_name in field_map and
                crc_fail_field_name in field_map):

                harq_failures = field_map[harq_failure_field_name].raw_value
                num_crc_pass = field_map[crc_pass_field_name].raw_value
                num_crc_fail = field_map[crc_fail_field_name].raw_value
                total = num_crc_pass + num_crc_fail

                if total > 0:
                    residual_bler_percent = (harq_failures / total) * 100

                    residual_bler_field = field_map[residual_bler_field_name]
                    residual_bler_field.raw_value = round(residual_bler_percent, 2)
                    residual_bler_field.friendly_value = f"{residual_bler_percent:.2f}%"
                else:
                    residual_bler_field = field_map[residual_bler_field_name]
                    residual_bler_field.raw_value = 0.0
                    residual_bler_field.friendly_value = "0.00%"

    def _has_fields(self, field_map: Dict[str, DecodedField], field_names: List[str]) -> bool:
        """
        Check if all required fields exist in the field map.

        Args:
            field_map: Dictionary of field name -> DecodedField
            field_names: List of required field names

        Returns:
            True if all fields exist, False otherwise
        """
        return all(name in field_map for name in field_names)
