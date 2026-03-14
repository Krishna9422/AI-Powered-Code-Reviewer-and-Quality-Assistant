"""Shared compatibility helpers for legacy test-facing APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.ast_extractor import analyze_file

ROOT = Path(__file__).resolve().parents[1]
_IGNORED_DIRS = {".venv", "venv", ".git", "__pycache__", "tests", ".pytest_cache"}


def resolve_input_path(path: str) -> Path:
    """Resolve relative test paths against the project root."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if candidate.exists():
        return candidate

    # Legacy tests used "examples" as a fixture directory.
    if str(path).strip().lower() == "examples":
        return ROOT

    return candidate


def collect_python_files(path: Path) -> list[Path]:
    """Collect Python files under a path while skipping env/cache/test folders."""
    if path.is_file() and path.suffix == ".py":
        return [path]
    if not path.is_dir():
        return []

    files: list[Path] = []
    for py_file in path.rglob("*.py"):
        if any(part in _IGNORED_DIRS or part.startswith(".") for part in py_file.parts):
            continue
        files.append(py_file)
    return sorted(files, key=lambda p: str(p).lower())


def normalize_functions(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize AST extractor output into the legacy parser schema."""
    functions: list[dict[str, Any]] = []

    for fn in analysis.get("functions", []):
        functions.append(
            {
                "name": fn.get("name", ""),
                "args": [{"name": arg} for arg in fn.get("args", [])],
                "has_docstring": bool(fn.get("docstring")),
            }
        )

    for cls in analysis.get("classes", []):
        for method in cls.get("methods", []):
            functions.append(
                {
                    "name": method.get("name", ""),
                    "args": [{"name": arg} for arg in method.get("args", [])],
                    "has_docstring": bool(method.get("docstring")),
                }
            )

    return functions


def parse_file_record(file_path: str) -> dict[str, Any]:
    """Parse one file into the legacy parser record format."""
    resolved = resolve_input_path(file_path)
    analysis = analyze_file(str(resolved))
    return {
        "file_path": str(resolved),
        "functions": normalize_functions(analysis),
    }
