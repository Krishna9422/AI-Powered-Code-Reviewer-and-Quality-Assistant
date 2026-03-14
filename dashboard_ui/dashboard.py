"""Compatibility dashboard helpers expected by tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]


def load_pytest_results() -> dict[str, Any] | None:
    """Load pytest JSON report if it exists."""
    report_path = _ROOT / "storage" / "reports" / "pytest_results.json"
    if not report_path.exists():
        return None
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def filter_functions(functions: list[dict[str, Any]], search: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    """Filter function records by name search and docstring status."""
    filtered = list(functions)

    if search:
        needle = search.lower()
        filtered = [fn for fn in filtered if needle in str(fn.get("name", "")).lower()]

    if status == "OK":
        filtered = [fn for fn in filtered if bool(fn.get("has_docstring"))]
    elif status == "Fix":
        filtered = [fn for fn in filtered if not bool(fn.get("has_docstring"))]

    return filtered
