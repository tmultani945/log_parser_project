"""
Enum value mapping utilities.
"""

from typing import Dict, Optional


def get_enum_string(
    raw_value: int,
    mappings: Dict[int, str],
    default: str = "UNKNOWN"
) -> str:
    """
    Map enum value to human-readable string.

    Args:
        raw_value: Raw integer value
        mappings: Dict mapping int values to string names
        default: Default string if value not found

    Returns:
        Human-readable string
    """
    return mappings.get(raw_value, f"{default}({raw_value})")


def parse_enum_from_description(description: str) -> Optional[Dict[int, str]]:
    """
    Parse enum mappings from field description text.

    Some ICD descriptions include enum values like:
    "0 = IDLE, 1 = CONNECTED, 2 = SUSPENDED"

    Args:
        description: Field description text

    Returns:
        Dict of enum mappings, or None if no mapping found
    """
    import re

    # Pattern: "0 = VALUE1, 1 = VALUE2, ..."
    pattern = r'(\d+)\s*=\s*([A-Z_]+)'

    matches = re.findall(pattern, description)

    if matches:
        return {int(num): name for num, name in matches}

    return None


def create_boolean_mapping() -> Dict[int, str]:
    """
    Create standard boolean enum mapping.

    Returns:
        Dict mapping 0/1 to false/true
    """
    return {
        0: "false",
        1: "true"
    }
