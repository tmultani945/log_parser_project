"""
Hex Decoder Module - Decode log packets using ICD PDF on-demand.

This module provides functionality to decode hexadecimal log packets
by directly parsing the ICD PDF document on-demand.
"""

__version__ = '1.0.0'

from .ingest.hex_parser import parse_hex_input
from .icd_parser.icd_query import ICDQueryEngine
from .decoder.payload_decoder import PayloadDecoder
from .export.json_builder import JSONBuilder
from .export.file_writer import FileWriter

__all__ = [
    'parse_hex_input',
    'ICDQueryEngine',
    'PayloadDecoder',
    'JSONBuilder',
    'FileWriter',
]
