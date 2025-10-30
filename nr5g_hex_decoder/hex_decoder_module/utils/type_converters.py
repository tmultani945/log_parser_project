"""
Type-specific decoders for different field types.
"""

import struct
from typing import Dict, Tuple
from .byte_ops import bytes_to_uint_le, slice_bits


def decode_uint(payload: bytes, offset_bytes: int, length_bits: int, offset_bits: int = 0) -> int:
    """
    Decode unsigned integer of arbitrary bit length.

    Args:
        payload: Raw payload bytes
        offset_bytes: Byte offset
        length_bits: Bit length (8, 16, 32, 64, or custom)
        offset_bits: Additional bit offset within the byte (0-7)

    Returns:
        Unsigned integer value
    """
    # Calculate total bit offset
    total_offset_bits = offset_bytes * 8 + offset_bits

    # Calculate required bytes
    length_bytes = (length_bits + 7) // 8

    if length_bytes <= 0:
        return 0

    # Handle standard byte-aligned sizes efficiently
    if offset_bits == 0 and length_bits in [8, 16, 32, 64] and length_bits % 8 == 0:
        return bytes_to_uint_le(payload, offset_bytes, length_bytes)

    # Handle non-standard or non-aligned bit fields
    return slice_bits(payload, total_offset_bits, length_bits)


def decode_bool(payload: bytes, offset_bytes: int, bit_offset: int = 0) -> bool:
    """
    Decode single bit as boolean.

    Args:
        payload: Raw payload bytes
        offset_bytes: Byte offset
        bit_offset: Bit offset within the byte (0-7)

    Returns:
        Boolean value
    """
    if offset_bytes >= len(payload):
        return False

    byte_val = payload[offset_bytes]
    bit_val = (byte_val >> bit_offset) & 0x01

    return bool(bit_val)


def decode_enum(
    payload: bytes,
    offset_bytes: int,
    length_bits: int,
    mappings: Dict[int, str],
    offset_bits: int = 0
) -> Tuple[int, str]:
    """
    Decode enum: return (raw_value, friendly_string).

    Args:
        payload: Raw payload bytes
        offset_bytes: Byte offset
        length_bits: Bit length
        mappings: Dict mapping int values to string names
        offset_bits: Additional bit offset within the byte (0-7)

    Returns:
        Tuple of (raw_value, friendly_value)
    """
    raw_value = decode_uint(payload, offset_bytes, length_bits, offset_bits)

    friendly_value = mappings.get(raw_value, f"UNKNOWN({raw_value})")

    return raw_value, friendly_value


def decode_signed_int(payload: bytes, offset_bytes: int, length_bits: int, offset_bits: int = 0) -> int:
    """
    Decode signed integer (two's complement).

    Args:
        payload: Raw payload bytes
        offset_bytes: Byte offset
        length_bits: Bit length
        offset_bits: Additional bit offset within the byte (0-7)

    Returns:
        Signed integer value
    """
    # First decode as unsigned
    unsigned_value = decode_uint(payload, offset_bytes, length_bits, offset_bits)

    # Check sign bit
    sign_bit = 1 << (length_bits - 1)

    if unsigned_value & sign_bit:
        # Negative number - apply two's complement
        return unsigned_value - (1 << length_bits)
    else:
        return unsigned_value


def decode_string(payload: bytes, offset_bytes: int, length_bytes: int, encoding: str = 'utf-8') -> str:
    """
    Decode null-terminated or fixed-length string.

    Args:
        payload: Raw payload bytes
        offset_bytes: Byte offset
        length_bytes: Maximum length in bytes
        encoding: Character encoding

    Returns:
        Decoded string
    """
    if offset_bytes + length_bytes > len(payload):
        length_bytes = len(payload) - offset_bytes

    raw_bytes = payload[offset_bytes:offset_bytes + length_bytes]

    # Find null terminator
    null_idx = raw_bytes.find(b'\x00')
    if null_idx != -1:
        raw_bytes = raw_bytes[:null_idx]

    try:
        return raw_bytes.decode(encoding)
    except UnicodeDecodeError:
        # Fallback to raw hex
        return raw_bytes.hex()


def decode_float(payload: bytes, offset_bytes: int, length_bits: int, offset_bits: int = 0) -> float:
    """
    Decode IEEE 754 floating-point number (Float32 or Float64).

    Args:
        payload: Raw payload bytes
        offset_bytes: Byte offset
        length_bits: Bit length (32 for float, 64 for double)
        offset_bits: Additional bit offset (must be 0 for floats)

    Returns:
        Floating-point value

    Raises:
        ValueError: If offset_bits is non-zero or length_bits is invalid
    """
    if offset_bits != 0:
        raise ValueError("Float decoding does not support bit-level offsets")

    if length_bits not in [32, 64]:
        raise ValueError(f"Float must be 32 or 64 bits, got {length_bits}")

    length_bytes = length_bits // 8

    if offset_bytes + length_bytes > len(payload):
        raise ValueError(
            f"Cannot read {length_bytes} bytes at offset {offset_bytes} "
            f"from {len(payload)}-byte buffer"
        )

    # Extract bytes
    raw_bytes = payload[offset_bytes:offset_bytes + length_bytes]

    # Decode using struct (little-endian)
    if length_bits == 32:
        # Float32 - single precision
        return struct.unpack('<f', raw_bytes)[0]
    else:  # length_bits == 64
        # Float64 - double precision
        return struct.unpack('<d', raw_bytes)[0]
