"""Compatibility validator functions expected by tests."""

from __future__ import annotations

from radon.complexity import cc_visit

from core._test_compat import resolve_input_path
from core.pydocstyle_runner import run_pydocstyle_checks


def validate_docstrings(file_path: str) -> list[str]:
    """Validate docstrings for a file using pydocstyle checks."""
    resolved = resolve_input_path(file_path)
    checks = run_pydocstyle_checks([str(resolved)])
    details = checks.get("details", {}).get(str(resolved), {})
    return details.get("violations", [])


def compute_complexity(source: str) -> list[dict[str, int | str]]:
    """Return cyclomatic complexity for all functions in source code."""
    return [
        {"name": block.name, "complexity": int(block.complexity)}
        for block in cc_visit(source)
    ]
