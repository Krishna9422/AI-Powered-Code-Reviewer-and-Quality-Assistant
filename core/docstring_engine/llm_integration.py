"""Compatibility LLM integration module expected by tests."""

from __future__ import annotations

from typing import Any


def generate_docstring_content(fn: dict[str, Any]) -> dict[str, Any]:
    """Return a structured fallback payload for docstring content."""
    args = {}
    for arg in fn.get("args", []):
        if isinstance(arg, dict):
            arg_name = str(arg.get("name", "arg"))
        else:
            arg_name = str(arg)
        args[arg_name] = "Description"

    return {
        "summary": "Generated description",
        "args": args,
        "returns": "None" if fn.get("returns") is None else "Result description",
        "raises": {},
    }
