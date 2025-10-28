"""
Low-level byte manipulation utilities.
"""


def bytes_to_uint_le(data: bytes, offset: int, length_bytes: int) -> int:
    """
    Extract unsigned integer from bytes (little-endian).

    Args:
        data: Byte array
        offset: Starting byte offset
        length_bytes: Number of bytes to read

    Returns:
        Unsigned integer value
    """
    if offset + length_bytes > len(data):
        raise ValueError(
            f"Cannot read {length_bytes} bytes at offset {offset} "
            f"from {len(data)}-byte buffer"
        )

    return int.from_bytes(
        data[offset:offset + length_bytes],
        byteorder='little',
        signed=False
    )


def slice_bits(data: bytes, offset_bits: int, length_bits: int) -> int:
    """
    Extract bit field from byte array.

    Args:
        data: Byte array
        offset_bits: Starting bit offset
        length_bits: Number of bits to extract

    Returns:
        Unsigned integer value of the bit field
    """
    # Calculate byte boundaries
    start_byte = offset_bits // 8
    end_byte = (offset_bits + length_bits + 7) // 8

    if end_byte > len(data):
        raise ValueError(
            f"Cannot read {length_bits} bits at offset {offset_bits} "
            f"from {len(data)}-byte buffer"
        )

    # Extract relevant bytes
    relevant_bytes = data[start_byte:end_byte]

    # Convert to integer
    value = int.from_bytes(relevant_bytes, byteorder='little', signed=False)

    # Calculate bit shift within the first byte
    bit_shift = offset_bits % 8

    # Shift and mask
    value >>= bit_shift
    mask = (1 << length_bits) - 1

    return value & mask


def uint_to_hex_string(value: int, prefix: bool = True, width: int = 4) -> str:
    """
    Convert integer to hex string.

    Args:
        value: Integer value
        prefix: Include "0x" prefix
        width: Minimum hex digit width (zero-padded)

    Returns:
        Hex string (e.g., "0xB823")
    """
    hex_str = f"{value:0{width}X}"
    return f"0x{hex_str}" if prefix else hex_str


def hex_string_to_bytes(hex_str: str) -> bytes:
    """
    Convert hex string to bytes.

    Args:
        hex_str: Hex string (with or without spaces)

    Returns:
        Byte array

    Example:
        "3D 00 23 B8" → b'\x3d\x00\x23\xb8'
    """
    # Remove spaces, newlines, and common separators
    cleaned = hex_str.replace(' ', '').replace('-', '').replace(':', '')
    cleaned = cleaned.replace('\n', '').replace('\r', '').replace('\t', '')

    # Remove 0x prefix if present
    if cleaned.startswith('0x') or cleaned.startswith('0X'):
        cleaned = cleaned[2:]

    # Validate hex characters
    if not all(c in '0123456789ABCDEFabcdef' for c in cleaned):
        raise ValueError(f"Invalid hex string: {hex_str}")

    # Ensure even length
    if len(cleaned) % 2 != 0:
        raise ValueError(f"Hex string must have even length: {hex_str}")

    return bytes.fromhex(cleaned)


def bytes_to_hex_string(data: bytes, separator: str = ' ') -> str:
    """
    Convert bytes to hex string.

    Args:
        data: Byte array
        separator: Separator between bytes

    Returns:
        Hex string (e.g., "3D 00 23 B8")
    """
    return separator.join(f"{b:02X}" for b in data)
