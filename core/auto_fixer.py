import ast
import os
import json
import re
import subprocess
from typing import Dict, List, Any, Optional

from generator.docstring_generator import generate_docstring
from .ast_extractor import analyze_file, _read_file_with_encoding
from .pydocstyle_runner import run_pydocstyle_checks

def apply_missing_docstrings(file_path: str, style: str = "google"):
    """Adds missing style-aware docstrings to a file."""
    # Try multiple encodings to read file
    encodings = ['utf-8', 'utf-16', 'utf-8-sig', 'latin-1', 'cp1252']
    lines = None
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if lines is None:
        # Last resort: read with errors='replace'
        with open(file_path, "r", encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    
    entities = analyze_file(file_path)

    to_add = []
    
    # Check functions
    for f in entities["functions"]:
        if not f["docstring"]:
            # Find indentation of the def line
            def_line = lines[f["line"]-1]
            indent = len(def_line) - len(def_line.lstrip())
            to_add.append((
                f["line"],
                generate_docstring(
                    name=f["name"],
                    args=f["args"],
                    indent=indent+4,
                    style=style,
                    has_return=f.get("has_return", True),
                    has_yield=f.get("has_yield", False),
                    has_raises=f.get("has_raises", False)
                )
            ))
            
    # Check classes
    for cls in entities["classes"]:
        if not cls["docstring"]:
            def_line = lines[cls["line"]-1]
            indent = len(def_line) - len(def_line.lstrip())
            to_add.append((
                cls["line"],
                generate_docstring(
                    name=cls["name"],
                    is_class=True,
                    indent=indent+4,
                    style=style,
                    has_return=False,
                    has_yield=False,
                    has_raises=False,
                    attributes=cls.get("attributes", [])
                )
            ))
        for m in cls["methods"]:
            if not m["docstring"]:
                def_line = lines[m["line"]-1]
                indent = len(def_line) - len(def_line.lstrip())
                to_add.append((
                    m["line"],
                    generate_docstring(
                        name=m["name"],
                        args=m["args"],
                        indent=indent+4,
                        style=style,
                        has_return=m.get("has_return", True),
                        has_yield=m.get("has_yield", False),
                        has_raises=m.get("has_raises", False)
                    )
                ))
                
    # Check Module
    if not entities["module"]["docstring"]:
        to_add.append((0, f'"""{os.path.basename(file_path).capitalize()} module."""\n'))

    # Sort descending by line number to keep indices correct while inserting
    to_add.sort(key=lambda x: x[0], reverse=True)
    
    for line_idx, doc_str in to_add:
        if line_idx == 0:
            lines.insert(0, doc_str + "\n")
        else:
            # Need to find the end of the def/class line (it might wrap)
            # For simplicity, we assume one line or we find the first line ending with colon
            curr_idx = line_idx - 1
            while curr_idx < len(lines) and ":" not in lines[curr_idx]:
                curr_idx += 1
            
            lines.insert(curr_idx + 1, doc_str + "\n")
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        f.flush()
        os.fsync(f.fileno())

def _extract_method_attributes(class_node: ast.ClassDef) -> List[str]:
    """Extract class attributes assigned to self in __init__."""
    attrs = set()
    for child in class_node.body:
        if isinstance(child, ast.FunctionDef) and child.name == "__init__":
            for sub in ast.walk(child):
                if isinstance(sub, ast.Assign):
                    for target in sub.targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            attrs.add(target.attr)
    return sorted(attrs)

def _replace_or_insert_docstring(
    lines: List[str],
    node: Any,
    docstring_text: str,
    indent_spaces: int,
) -> List[str]:
    """Replace existing docstring for a node or insert a new one after signature."""
    doc_lines = [line + "\n" for line in docstring_text.splitlines()]

    first_stmt = node.body[0] if getattr(node, "body", None) else None
    has_existing = (
        first_stmt is not None
        and isinstance(first_stmt, ast.Expr)
        and isinstance(getattr(first_stmt, "value", None), ast.Constant)
        and isinstance(first_stmt.value.value, str)
    )

    if has_existing:
        start_idx = first_stmt.lineno - 1
        end_idx = getattr(first_stmt, "end_lineno", first_stmt.lineno) - 1
        
        is_func = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        is_class = isinstance(node, ast.ClassDef)
        if is_func:
            # Fix D202: no blank lines after function docstring
            while end_idx + 1 < len(lines) and lines[end_idx + 1].strip() == "":
                lines.pop(end_idx + 1)
            # Fix D201: no blank lines before function docstring
            signature_idx = node.lineno - 1
            while signature_idx < len(lines) and ":" not in lines[signature_idx]:
                signature_idx += 1
            while start_idx - 1 > signature_idx and lines[start_idx - 1].strip() == "":
                lines.pop(start_idx - 1)
                start_idx -= 1
                end_idx -= 1
        elif is_class:
            # Fix D204: 1 blank line required after class docstring
            if end_idx + 1 < len(lines) and lines[end_idx + 1].strip() != "":
                lines.insert(end_idx + 1, "\n")

        lines[start_idx:end_idx + 1] = doc_lines
        return lines

    signature_idx = node.lineno - 1
    while signature_idx < len(lines) and ":" not in lines[signature_idx]:
        signature_idx += 1

    insert_idx = min(signature_idx + 1, len(lines))
    lines[insert_idx:insert_idx] = doc_lines
    
    if isinstance(node, ast.ClassDef):
        idx_after_doc = insert_idx + len(doc_lines)
        if idx_after_doc < len(lines) and lines[idx_after_doc].strip() != "":
            lines.insert(idx_after_doc, "\n")
            
    return lines

def apply_docstring_fix_at_line(file_path: str, target_line: int, style: str = "google", doc_text_override: str = None) -> bool:
    """Auto-fix docstring for entity located at a specific line.

    Returns True if a fix was applied, False otherwise.
    """
    if not os.path.exists(file_path):
        return False

    # Try multiple encodings to read file
    encodings = ['utf-8', 'utf-16', 'utf-8-sig', 'latin-1', 'cp1252']
    lines = None
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if lines is None:
        # Last resort: read with errors='replace'
        with open(file_path, "r", encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    
    source = "".join(lines)
    tree = ast.parse(source)

    target_node = None
    target_kind = None
    min_size = float('inf')

    if target_line == 1:
        target_node = tree
        target_kind = "module"
    else:
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, 'end_lineno', node.lineno)
                if start <= target_line <= end:
                    size = end - start
                    if size < min_size:
                        min_size = size
                        target_node = node
                        target_kind = "class" if isinstance(node, ast.ClassDef) else "function"

    if target_node is None:
        return False

    if target_kind == "module":
        if doc_text_override is not None:
            module_doc = doc_text_override
        else:
            module_doc = generate_docstring(
                name=os.path.basename(file_path),
                args=[],
                is_class=False,
                indent=0,
                style=style,
                has_return=False,
                has_yield=False,
                has_raises=False,
            )

        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(getattr(tree.body[0], "value", None), ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            first_stmt = tree.body[0]
            start_idx = first_stmt.lineno - 1
            end_idx = getattr(first_stmt, "end_lineno", first_stmt.lineno) - 1
            lines[start_idx:end_idx + 1] = [line + "\n" for line in module_doc.splitlines()]
        else:
            lines.insert(0, module_doc + "\n")

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True

    if target_kind == "class":
        if doc_text_override is not None:
            doc_text = doc_text_override
        else:
            doc_text = generate_docstring(
                name=target_node.name,
                args=[],
                is_class=True,
                indent=target_node.col_offset + 4,
                style=style,
                has_return=False,
                has_yield=False,
                has_raises=False,
                attributes=_extract_method_attributes(target_node),
            )
        lines = _replace_or_insert_docstring(lines, target_node, doc_text, target_node.col_offset + 4)
    else:
        args = [arg.arg for arg in target_node.args.args if arg.arg not in ("self", "cls")]
        has_yield = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(target_node))
        has_return = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(target_node))
        has_raises = any(isinstance(n, ast.Raise) for n in ast.walk(target_node))

        if doc_text_override is not None:
            doc_text = doc_text_override
        else:
            doc_text = generate_docstring(
                name=target_node.name,
                args=args,
                is_class=False,
                indent=target_node.col_offset + 4,
                style=style,
                has_return=has_return,
                has_yield=has_yield,
                has_raises=has_raises,
            )
        lines = _replace_or_insert_docstring(lines, target_node, doc_text, target_node.col_offset + 4)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        f.flush()
        os.fsync(f.fileno())

    return True

def apply_docstring_fixes_from_pydocstyle(file_path: str, style: str = "google") -> int:
    """Apply auto-fixes for pydocstyle violations in a single file.

    Returns the number of entities updated.
    """
    if not os.path.exists(file_path):
        return 0

    report = run_pydocstyle_checks([file_path])
    details = report.get("details", {}).get(file_path, {})
    violation_list = details.get("violations_detailed", [])

    target_lines = set()
    for viol in violation_list:
        line_no = viol.get("line")
        if line_no is not None:
            target_lines.add(line_no)

    if not target_lines:
        violations = details.get("violations", [])
        for violation in violations:
            line_match = re.search(r":(\d+)\b", violation)
            if line_match:
                target_lines.add(int(line_match.group(1)))

    fixed = 0
    for line_no in sorted(target_lines):
        if apply_docstring_fix_at_line(file_path, line_no, style=style):
            fixed += 1

    return fixed