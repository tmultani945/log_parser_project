"""
Write JSON output to files.
"""

import json
import os
from typing import Dict, Any
from pathlib import Path


class FileWriter:
    """Writes JSON data to files"""

    def write(
        self,
        json_data: Dict[str, Any],
        output_path: str,
        pretty: bool = True,
        create_dirs: bool = True
    ) -> None:
        """
        Write JSON data to file.

        Args:
            json_data: JSON-serializable dictionary
            output_path: Path to output file
            pretty: Use pretty-printing (indented)
            create_dirs: Create parent directories if they don't exist

        Raises:
            IOError: If file cannot be written
        """
        # Create parent directories if needed
        if create_dirs:
            parent_dir = Path(output_path).parent
            if parent_dir and not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(json_data, f, ensure_ascii=False)

    def write_pretty(self, json_data: Dict[str, Any], output_path: str) -> None:
        """
        Write pretty-printed JSON.

        Args:
            json_data: JSON-serializable dictionary
            output_path: Path to output file
        """
        self.write(json_data, output_path, pretty=True)

    def write_compact(self, json_data: Dict[str, Any], output_path: str) -> None:
        """
        Write compact JSON (no indentation).

        Args:
            json_data: JSON-serializable dictionary
            output_path: Path to output file
        """
        self.write(json_data, output_path, pretty=False)

    def append_to_jsonl(self, json_data: Dict[str, Any], output_path: str) -> None:
        """
        Append JSON as a line to a JSONL file (for batch processing).

        Args:
            json_data: JSON-serializable dictionary
            output_path: Path to JSONL file
        """
        with open(output_path, 'a', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False)
            f.write('\n')
