"""
Input validation utilities.
"""

import re
from ..models.errors import MalformedHexError, LengthMismatchError


def validate_hex_string(hex_str: str) -> None:
    """
    Validate that a string contains only valid hex characters.

    Args:
        hex_str: String to validate

    Raises:
        MalformedHexError: If string contains invalid characters
    """
    # Remove common separators
    cleaned = hex_str.replace(' ', '').replace('-', '').replace(':', '').replace('\n', '').replace('\r', '')

    # Check for valid hex characters
    if not re.match(r'^[0-9A-Fa-f]*$', cleaned):
        raise MalformedHexError(f"Invalid hex characters in: {hex_str[:50]}...")


def validate_packet_length(declared_length: int, actual_length: int) -> None:
    """
    Validate that declared length matches actual byte count.

    Args:
        declared_length: Length declared in packet header
        actual_length: Actual number of bytes

    Raises:
        LengthMismatchError: If lengths don't match
    """
    if declared_length != actual_length:
        raise LengthMismatchError(declared_length, actual_length)


def validate_hex_format(hex_input: str) -> None:
    """
    Validate the overall hex input format.

    Expected format:
        Length: <number>
        Header: <hex bytes>
        Payload: <hex bytes>

    Args:
        hex_input: Raw hex input string

    Raises:
        MalformedHexError: If format is invalid
    """
    # Check for required sections
    if 'Length:' not in hex_input:
        raise MalformedHexError("Missing 'Length:' section")

    if 'Header:' not in hex_input:
        raise MalformedHexError("Missing 'Header:' section")

    if 'Payload:' not in hex_input:
        raise MalformedHexError("Missing 'Payload:' section")
