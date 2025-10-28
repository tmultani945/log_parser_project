"""
Custom exception classes for hex decoder module.
"""


class HexDecoderError(Exception):
    """Base exception for all decoder errors"""
    pass


class MalformedHexError(HexDecoderError):
    """Invalid hex input format"""
    pass


class LengthMismatchError(HexDecoderError):
    """Declared length doesn't match actual bytes"""
    def __init__(self, declared: int, actual: int):
        self.declared = declared
        self.actual = actual
        super().__init__(
            f"Length mismatch: declared {declared} bytes, got {actual} bytes"
        )


class LogcodeNotFoundError(HexDecoderError):
    """Logcode not in ICD database"""
    def __init__(self, logcode_id: str):
        self.logcode_id = logcode_id
        super().__init__(f"Logcode {logcode_id} not found in ICD")


class VersionNotFoundError(HexDecoderError):
    """Version not defined for this logcode"""
    def __init__(self, logcode_id: str, version: int):
        self.logcode_id = logcode_id
        self.version = version
        super().__init__(
            f"Version {version} not found for logcode {logcode_id}"
        )


class PayloadTooShortError(HexDecoderError):
    """Payload is shorter than required by field definitions"""
    def __init__(self, required_bytes: int, actual_bytes: int, field_name: str = None):
        self.required = required_bytes
        self.actual = actual_bytes
        self.field_name = field_name
        msg = f"Payload too short: need {required_bytes} bytes, got {actual_bytes}"
        if field_name:
            msg += f" (field: {field_name})"
        super().__init__(msg)


class FieldDecodingError(HexDecoderError):
    """Error decoding a specific field"""
    def __init__(self, field_name: str, reason: str):
        self.field_name = field_name
        self.reason = reason
        super().__init__(f"Failed to decode field '{field_name}': {reason}")


class SectionNotFoundError(HexDecoderError):
    """Logcode section not found in PDF"""
    pass


class PDFScanError(HexDecoderError):
    """Error scanning PDF"""
    pass


class TableParsingError(HexDecoderError):
    """Error parsing table from PDF"""
    pass
