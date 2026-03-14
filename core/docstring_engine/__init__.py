"""Legacy docstring engine API package."""

from .generator import generate_docstring
from . import llm_integration

__all__ = ["generate_docstring", "llm_integration"]
