"""Compatibility generator function expected by tests."""

from __future__ import annotations

from typing import Any

from generator.docstring_generator import generate_docstring as _generate_docstring

_VALID_STYLES = {"google", "numpy", "rest"}


def generate_docstring(fn: dict[str, Any], style: str = "google") -> str:
    """Generate a style-specific docstring from legacy function metadata."""
    style_key = (style or "google").strip().lower()
    if style_key not in _VALID_STYLES:
        raise ValueError(f"Unknown style: {style}")

    args = []
    for arg in fn.get("args", []):
        if isinstance(arg, dict):
            arg_name = str(arg.get("name", "arg"))
            arg_annotation = arg.get("annotation")
            if arg_annotation:
                args.append(f"{arg_name} ({arg_annotation})")
            else:
                args.append(arg_name)
        else:
            args.append(str(arg))

    has_return = fn.get("returns") is not None
    return _generate_docstring(
        name=str(fn.get("name", "function")),
        args=args,
        style=style_key,
        has_return=has_return,
    )
