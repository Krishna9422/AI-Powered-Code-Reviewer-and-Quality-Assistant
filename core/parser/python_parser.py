"""Compatibility parser functions expected by tests."""

from __future__ import annotations

from typing import Any

from core._test_compat import collect_python_files, parse_file_record, resolve_input_path


def parse_file(file_path: str) -> dict[str, Any]:
    """Parse a single Python file and return metadata."""
    return parse_file_record(file_path)


def parse_path(path: str) -> list[dict[str, Any]]:
    """Parse a file or directory path and return metadata for each file."""
    resolved = resolve_input_path(path)
    files = collect_python_files(resolved)
    return [parse_file_record(str(file_path)) for file_path in files]
