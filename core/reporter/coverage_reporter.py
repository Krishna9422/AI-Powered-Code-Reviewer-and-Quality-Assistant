"""Compatibility coverage reporter expected by tests."""

from __future__ import annotations

from typing import Any


def compute_coverage(parsed: list[dict[str, Any]], threshold: int = 80) -> dict[str, Any]:
    """Compute aggregate documentation coverage from parsed function metadata."""
    total_functions = 0
    documented = 0

    for file_data in parsed:
        functions = file_data.get("functions", [])
        total_functions += len(functions)
        documented += sum(1 for fn in functions if fn.get("has_docstring"))

    coverage_percent = (documented / total_functions * 100) if total_functions else 0
    return {
        "aggregate": {
            "coverage_percent": coverage_percent,
            "total_functions": total_functions,
            "documented": documented,
            "meets_threshold": coverage_percent >= threshold,
        }
    }
