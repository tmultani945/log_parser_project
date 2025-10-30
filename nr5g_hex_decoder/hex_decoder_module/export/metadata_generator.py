"""
Generate JSON metadata for logcodes from ICD PDF.

This module extracts all version information and dependent tables for logcodes,
creating a comprehensive metadata file that can be used for fast payload decoding.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict

from ..icd_parser.icd_query import ICDQueryEngine
from ..models.icd import LogcodeMetadata, FieldDefinition
from ..models.errors import LogcodeNotFoundError


class MetadataGenerator:
    """Generate comprehensive metadata JSON from ICD PDF"""

    def __init__(self, pdf_path: str, enable_cache: bool = True):
        """
        Initialize metadata generator.

        Args:
            pdf_path: Path to ICD PDF file
            enable_cache: Enable query caching for better performance
        """
        self.icd_engine = ICDQueryEngine(pdf_path, enable_cache=enable_cache)

    def generate_logcode_metadata(self, logcode_id: str) -> Dict[str, Any]:
        """
        Generate complete metadata for a single logcode.

        Extracts all versions and their complete field layouts (main + dependencies).

        Args:
            logcode_id: Logcode hex ID (e.g., "0x1C07")

        Returns:
            Dictionary with complete logcode metadata

        Raises:
            LogcodeNotFoundError: If logcode not found in PDF
        """
        # Get base metadata
        metadata = self.icd_engine.get_logcode_metadata(logcode_id)

        # Get all available versions
        versions = self.icd_engine.list_available_versions(logcode_id)

        # Build version-specific metadata
        versions_dict = {}
        for version in versions:
            version_data = self._generate_version_metadata(logcode_id, version, metadata)
            versions_dict[str(version)] = version_data

        # Build complete logcode metadata
        logcode_data = {
            "logcode_id": metadata.logcode_id,
            "logcode_name": metadata.logcode_name,
            "section": metadata.section,
            "description": metadata.description,
            "version_offset": metadata.version_offset,
            "version_length": metadata.version_length,
            "version_map": {str(k): v for k, v in metadata.version_map.items()},
            "available_versions": sorted([str(v) for v in versions]),
            "versions": versions_dict,
            "all_tables": self._extract_all_tables(metadata)
        }

        return logcode_data

    def _generate_version_metadata(
        self,
        logcode_id: str,
        version: int,
        metadata: LogcodeMetadata
    ) -> Dict[str, Any]:
        """
        Generate metadata for a specific version.

        Args:
            logcode_id: Logcode hex ID
            version: Version number
            metadata: Base logcode metadata

        Returns:
            Version-specific metadata with RAW table structure (preserves repeating structures)
        """
        # Get main table name for this version
        table_name = metadata.version_map.get(version, "unknown")

        # Get direct dependencies for the main table
        direct_deps = metadata.dependencies.get(table_name, [])

        # Get RAW field definitions (NOT expanded) to preserve repeating structures with count=-1
        raw_field_definitions = metadata.table_definitions.get(table_name, [])

        # Build field definitions
        fields_list = [self._field_to_dict(field) for field in raw_field_definitions]

        return {
            "version_value": version,
            "table_name": table_name,
            "direct_dependencies": direct_deps,
            "fields": fields_list,
            "total_fields": len(fields_list)
        }

    def _field_to_dict(self, field: FieldDefinition) -> Dict[str, Any]:
        """
        Convert FieldDefinition to dictionary.

        Args:
            field: Field definition

        Returns:
            Dictionary representation of field
        """
        field_dict = {
            "name": field.name,
            "type_name": field.type_name,
            "offset_bytes": field.offset_bytes,
            "offset_bits": field.offset_bits,
            "length_bits": field.length_bits,
            "description": field.description
        }

        if field.count is not None:
            field_dict["count"] = field.count

        if field.enum_mappings:
            field_dict["enum_mappings"] = {str(k): v for k, v in field.enum_mappings.items()}

        return field_dict

    def _extract_all_tables(self, metadata: LogcodeMetadata) -> Dict[str, Any]:
        """
        Extract all table definitions (without version expansion).

        This provides raw table data for reference.

        Args:
            metadata: Logcode metadata

        Returns:
            Dictionary of table_name → table info
        """
        all_tables = {}

        for table_name, field_defs in metadata.table_definitions.items():
            fields_list = [self._field_to_dict(field) for field in field_defs]
            deps = metadata.dependencies.get(table_name, [])

            all_tables[table_name] = {
                "fields": fields_list,
                "field_count": len(fields_list),
                "dependencies": deps
            }

        return all_tables

    def generate_multi_logcode_metadata(
        self,
        logcode_ids: List[str],
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Generate metadata for multiple logcodes.

        Args:
            logcode_ids: List of logcode hex IDs
            show_progress: Print progress information

        Returns:
            Dictionary with metadata for all logcodes
        """
        logcodes_dict = {}
        failed_logcodes = []

        for i, logcode_id in enumerate(logcode_ids, 1):
            if show_progress:
                print(f"Processing {i}/{len(logcode_ids)}: {logcode_id}...")

            try:
                logcode_data = self.generate_logcode_metadata(logcode_id)
                logcodes_dict[logcode_id] = logcode_data

                if show_progress:
                    version_count = len(logcode_data.get("versions", {}))
                    print(f"  [OK] Found {version_count} versions")

            except LogcodeNotFoundError as e:
                if show_progress:
                    print(f"  [FAIL] Not found: {e}")
                failed_logcodes.append({
                    "logcode_id": logcode_id,
                    "error": str(e)
                })

            except Exception as e:
                if show_progress:
                    print(f"  [FAIL] Error: {e}")
                failed_logcodes.append({
                    "logcode_id": logcode_id,
                    "error": str(e)
                })

        # Build complete metadata structure
        metadata_output = {
            "metadata_version": "1.0",
            "generated_timestamp": datetime.now().isoformat(),
            "total_logcodes": len(logcodes_dict),
            "failed_logcodes": len(failed_logcodes),
            "logcodes": logcodes_dict
        }

        if failed_logcodes:
            metadata_output["errors"] = failed_logcodes

        return metadata_output

    def save_to_file(
        self,
        metadata: Dict[str, Any],
        output_path: str,
        pretty: bool = True
    ) -> None:
        """
        Save metadata to JSON file.

        Args:
            metadata: Metadata dictionary
            output_path: Output file path
            pretty: Use pretty formatting (default: True)
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            else:
                json.dump(metadata, f, ensure_ascii=False)

        print(f"\nMetadata saved to: {output_path}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache info
        """
        return {
            "cache_enabled": self.icd_engine.cache is not None,
            "cache_size": self.icd_engine.get_cache_size()
        }
