"""Legacy validator API package."""

from .validator import compute_complexity, validate_docstrings

__all__ = ["validate_docstrings", "compute_complexity"]
