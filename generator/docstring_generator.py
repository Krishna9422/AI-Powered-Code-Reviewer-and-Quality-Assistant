import ast
import os
import json
import re
import subprocess
import requests
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

def _format_summary(name: str) -> str:
    """Format name into an imperative summary."""
    summary = name.replace("_", " ")
    words = summary.split()
    if not words:
        return "Docstring."
    
    first_word = words[0].lower()
    mapping = {
        "generator": "generate",
        "raises": "raise",
        "calculates": "calculate",
        "adds": "add",
        "gets": "get",
        "sets": "set",
        "checks": "check",
        "processes": "process",
        "returns": "return",
        "creates": "create",
        "updates": "update",
        "deletes": "delete",
    }
    if first_word in mapping:
        words[0] = mapping[first_word]
    elif first_word.endswith("s") and not first_word.endswith("ss") and not first_word.endswith("us") and not first_word.endswith("is") and len(first_word) > 3:
        if first_word.endswith("ies"):
            words[0] = first_word[:-3] + "y"
        elif first_word.endswith("oes"):
            words[0] = first_word[:-2]
        else:
            words[0] = first_word[:-1]
    
    summary = " ".join(words)
    return summary[0].upper() + summary[1:] + "."

def generate_google_docstring(
    name: str,
    args: List[str] = None,
    is_class: bool = False,
    indent: int = 4,
    has_return: bool = True,
    has_yield: bool = False,
    has_raises: bool = False,
    attributes: Optional[List[str]] = None
) -> str:
    """Generates a Google-style docstring."""
    prefix = " " * indent
    summary = _format_summary(name)
    
    needs_multi = bool((is_class and attributes) or args or (has_yield and not is_class) or (has_return and not is_class) or has_raises)
    
    if not needs_multi:
        return f'{prefix}"""{summary}"""'

    sections = []
    
    if is_class and attributes:
        sec = f"{prefix}Attributes:\n"
        sec += "\n".join(f"{prefix}    {attr}: Description of {attr}." for attr in attributes)
        sections.append(sec)

    if args:
        sec = f"{prefix}Args:\n"
        sec += "\n".join(f"{prefix}    {arg}: Description of {arg}." for arg in args)
        sections.append(sec)

    if has_yield and not is_class:
        sections.append(f"{prefix}Yields:\n{prefix}    Description of yielded values.")
    elif has_return and not is_class:
        sections.append(f"{prefix}Returns:\n{prefix}    Description of the return value.")

    if has_raises:
        sections.append(f"{prefix}Raises:\n{prefix}    Exception: Description of when this exception is raised.")
    
    doc = f'{prefix}"""{summary}\n\n'
    doc += "\n\n".join(sections)
    doc += f'\n{prefix}"""'
    return doc

def generate_numpy_docstring(
    name: str,
    args: List[str] = None,
    is_class: bool = False,
    indent: int = 4,
    has_return: bool = True,
    has_yield: bool = False,
    has_raises: bool = False,
    attributes: Optional[List[str]] = None
) -> str:
    """Generates a NumPy-style docstring."""
    prefix = " " * indent
    summary = _format_summary(name)
    
    needs_multi = bool((is_class and attributes) or args or (has_yield and not is_class) or (has_return and not is_class) or has_raises)
    if not needs_multi:
        return f'{prefix}"""{summary}"""'

    sections = []
    
    if args:
        sec = f"{prefix}Parameters\n{prefix}----------\n"
        sec += "\n".join(f"{prefix}{arg} : Any\n{prefix}    Description of {arg}." for arg in args)
        sections.append(sec)

    if is_class and attributes:
        sec = f"{prefix}Attributes\n{prefix}----------\n"
        sec += "\n".join(f"{prefix}{attr} : Any\n{prefix}    Description of {attr}." for attr in attributes)
        sections.append(sec)

    if has_yield and not is_class:
        sections.append(f"{prefix}Yields\n{prefix}------\n{prefix}Any\n{prefix}    Description of yielded values.")
    elif has_return and not is_class:
        sections.append(f"{prefix}Returns\n{prefix}-------\n{prefix}Any\n{prefix}    Description of the return value.")

    if has_raises:
        sections.append(f"{prefix}Raises\n{prefix}------\n{prefix}Exception\n{prefix}    Description of when this exception is raised.")

    doc = f'{prefix}"""{summary}\n\n'
    doc += "\n\n".join(sections)
    doc += f'\n{prefix}"""'
    return doc

def generate_rest_docstring(
    name: str,
    args: List[str] = None,
    is_class: bool = False,
    indent: int = 4,
    has_return: bool = True,
    has_yield: bool = False,
    has_raises: bool = False,
    attributes: Optional[List[str]] = None
) -> str:
    """Generates a reST-style docstring."""
    prefix = " " * indent
    summary = _format_summary(name)
    
    needs_multi = bool((is_class and attributes) or args or (has_yield and not is_class) or (has_return and not is_class) or has_raises)
    if not needs_multi:
        return f'{prefix}"""{summary}"""'

    sections = []

    if args:
        sec = "\n".join(f"{prefix}:param {arg}: Description of {arg}.\n{prefix}:type {arg}: Any" for arg in args)
        sections.append(sec)

    if is_class and attributes:
        sec = "\n".join(f"{prefix}:ivar {attr}: Description of {attr}." for attr in attributes)
        sections.append(sec)

    if has_yield and not is_class:
        sections.append(f"{prefix}:yields: Description of yielded values.\n{prefix}:rtype: Any")
    elif has_return and not is_class:
        sections.append(f"{prefix}:returns: Description of the return value.\n{prefix}:rtype: Any")

    if has_raises:
        sections.append(f"{prefix}:raises Exception: Description of when this exception is raised.")

    doc = f'{prefix}"""{summary}\n\n'
    doc += "\n\n".join(sections)
    doc += f'\n{prefix}"""'
    return doc

def generate_docstring(
    name: str,
    args: List[str] = None,
    is_class: bool = False,
    indent: int = 4,
    style: str = "google",
    has_return: bool = True,
    has_yield: bool = False,
    has_raises: bool = False,
    attributes: Optional[List[str]] = None
) -> str:
    """Generates a style-specific docstring."""
    style_key = (style or "google").strip().lower()
    builders = {
        "google": generate_google_docstring,
        "numpy": generate_numpy_docstring,
        "rest": generate_rest_docstring,
    }
    builder = builders.get(style_key, generate_google_docstring)
    return builder(
        name=name,
        args=args,
        is_class=is_class,
        indent=indent,
        has_return=has_return,
        has_yield=has_yield,
        has_raises=has_raises,
        attributes=attributes,
    )

def generate_docstring_llm(func_code: str, style: str = "google", indent: int = 4) -> str:
    """Generates a docstring using LangChain's ChatGroq API."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "\"\"\"\nError: GROQ_API_KEY is not set in .env file.\n\"\"\""

    style_lower = style.lower()
    style_hints = ""
    if style_lower == "numpy":
        style_hints = """
CRITICAL: You MUST use the exact NumPy format with dashed underlines for section headers and proper indentation.
Example format:
\"\"\"
Summary line.

Parameters
----------
arg_name : type
    Description of the argument on a new indented line.

Returns
-------
type
    Description of the return value on a new indented line.

Examples
--------
>>> function_call()
expected_output
\"\"\"
"""
    elif style_lower == "google":
        style_hints = """
CRITICAL: You MUST use the exact Google format with indented sections and proper spacing.
Example format:
\"\"\"
Summary line.

Args:
    arg_name (type): Description of the argument.

Returns:
    type: Description of the return value.
\"\"\"
"""
    elif style_lower == "rest":
        style_hints = """
CRITICAL: You MUST use the exact reStructuredText (reST) format.
Example format:
\"\"\"
Summary line.

:param arg_name: Description.
:type arg_name: type
:returns: Description.
:rtype: type
\"\"\"
"""

    prompt = f"""You are a professional Python developer. 
Generate a Python docstring for the following code using the {style.upper()} docstring style format.
{style_hints}
Do NOT include the Python code in your response. 
ONLY output the docstring itself, enclosed in triple double-quotes (\"\"\"). 
Preserve strict line breaks and proper indentation. Do not squash paragraphs into single lines.

Code:
{func_code}
"""

    try:
        llm = ChatGroq(
            model="openai/gpt-oss-120b", # openai/gpt-oss-120b, llama-3.1-8b-instant
            temperature=0.3,
            api_key=api_key
        )
        
        response = llm.invoke([HumanMessage(content=prompt)])
        docstring = response.content.strip()
        
        # Cleanup
        if docstring.startswith("```python"):
            docstring = docstring[9:]
        if docstring.startswith("```"):
            docstring = docstring[3:]
        if docstring.endswith("```"):
            docstring = docstring[:-3]
        docstring = docstring.strip()

        prefix = " " * indent
        
        # Apply prefix to all lines
        lines = docstring.splitlines()
        indented_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                indented_lines.append(prefix + line.lstrip())
            else:
                if line.strip() == "":
                    indented_lines.append("")
                else:
                    # Unconditionally add prefix to preserve LLM's relative inner indentation
                    indented_lines.append(prefix + line)
                        
        return "\n".join(indented_lines)
    except Exception as e:
        prefix = " " * indent
        return f'{prefix}"""\n{prefix}Error generating docstring via LLM: {str(e)}\n{prefix}"""'
