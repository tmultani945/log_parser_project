"""
Parse raw hex input into structured packet data.
"""

import re
from typing import Tuple
from ..models.packet import ParsedPacket
from ..models.errors import MalformedHexError, LengthMismatchError
from ..utils.byte_ops import hex_string_to_bytes
from .validators import validate_hex_string, validate_packet_length, validate_hex_format


class HexInputParser:
    """Parser for hex input strings"""

    def parse(self, hex_input: str) -> ParsedPacket:
        """
        Parse hex input string into ParsedPacket.

        Expected input format:
            Length: 61
            Header: 3D 00 23 B8 CD 0F 67 95 F5 A6 06 01
            Payload:
            02 00 03 00 01 01 00 38 00 3A 00 7D
            F1 40 18 30 01 E0 E5 09 00 4A DE 09
            ...

        Args:
            hex_input: Raw hex input string

        Returns:
            ParsedPacket object

        Raises:
            MalformedHexError: If input format is invalid
            LengthMismatchError: If declared length doesn't match actual
        """
        # Validate format
        validate_hex_format(hex_input)

        # Extract sections
        length = self._extract_length(hex_input)
        header_hex = self._extract_section(hex_input, 'Header')
        payload_hex = self._extract_section(hex_input, 'Payload')

        # Validate hex strings
        validate_hex_string(header_hex)
        validate_hex_string(payload_hex)

        # Convert to bytes
        header_bytes = hex_string_to_bytes(header_hex)
        payload_bytes = hex_string_to_bytes(payload_hex)

        # Validate total length
        total_bytes = len(header_bytes) + len(payload_bytes)
        validate_packet_length(length, total_bytes)

        return ParsedPacket(
            length=length,
            header_bytes=header_bytes,
            payload_bytes=payload_bytes,
            raw_input=hex_input
        )

    def _extract_length(self, hex_input: str) -> int:
        """
        Extract packet length from input.

        Args:
            hex_input: Raw input string

        Returns:
            Length as integer

        Raises:
            MalformedHexError: If length cannot be parsed
        """
        match = re.search(r'Length:\s*(\d+)', hex_input, re.IGNORECASE)
        if not match:
            raise MalformedHexError("Could not parse 'Length' field")

        try:
            return int(match.group(1))
        except ValueError:
            raise MalformedHexError(f"Invalid length value: {match.group(1)}")

    def _extract_section(self, hex_input: str, section_name: str) -> str:
        """
        Extract a hex section (Header or Payload) from input.

        Args:
            hex_input: Raw input string
            section_name: Section name ('Header' or 'Payload')

        Returns:
            Hex string for the section

        Raises:
            MalformedHexError: If section cannot be found
        """
        # Pattern: "Section: <hex data until next section or end>"
        # Need to capture everything after "Section:" until the next section or end
        pattern = rf'{section_name}:\s*((?:[0-9A-Fa-f\s\r\n]+))'

        match = re.search(pattern, hex_input, re.IGNORECASE | re.MULTILINE)
        if not match:
            raise MalformedHexError(f"Could not find '{section_name}' section")

        hex_data = match.group(1).strip()

        # Stop at next section if present
        # Look for patterns like "Length:", "Header:", "Payload:" that might come after
        next_section_patterns = [r'\bLength:', r'\bHeader:', r'\bPayload:']

        for pattern in next_section_patterns:
            split_match = re.search(pattern, hex_data, re.IGNORECASE)
            if split_match:
                hex_data = hex_data[:split_match.start()].strip()
                break

        if not hex_data:
            raise MalformedHexError(f"'{section_name}' section is empty")

        return hex_data


def parse_hex_input(hex_input: str) -> ParsedPacket:
    """
    Convenience function to parse hex input.

    Args:
        hex_input: Raw hex input string

    Returns:
        ParsedPacket object
    """
    parser = HexInputParser()
    return parser.parse(hex_input)
