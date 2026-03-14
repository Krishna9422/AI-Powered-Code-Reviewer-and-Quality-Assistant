import ast
import os
import json
import re
import subprocess
from typing import Dict, List, Any, Optional

class DocstringExtractor(ast.NodeVisitor):
    """DocstringExtractor.

    Attributes:
        _current_class: Description of _current_class.
        entities: Description of entities.
        file_path: Description of file_path.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.entities = {
            "module": {"docstring": None, "line": 1, "name": "Module"},
            "classes": [],
            "functions": []
        }
        self._current_class = None

    def visit_Module(self, node: ast.Module):
        self.entities["module"]["docstring"] = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_info = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "line": node.lineno,
            "end_line": getattr(node, 'end_lineno', node.lineno),
            "col_offset": getattr(node, 'col_offset', 0),
            "attributes": self._extract_class_attributes(node),
            "methods": []
        }
        self.entities["classes"].append(class_info)
        
        old_class = self._current_class
        self._current_class = class_info
        self.generic_visit(node)
        self._current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_callable(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_callable(node)

    def _visit_callable(self, node: Any):
        # Extract arguments and handle self/cls
        args = [arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')]
        has_yield = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node))
        has_return = any(
            isinstance(n, ast.Return) and n.value is not None
            for n in ast.walk(node)
        )
        has_raises = any(isinstance(n, ast.Raise) for n in ast.walk(node))
        
        func_info = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "line": node.lineno,
            "end_line": getattr(node, 'end_lineno', node.lineno),
            "col_offset": getattr(node, 'col_offset', 0),
            "args": args,
            "has_return": has_return,
            "has_yield": has_yield,
            "has_raises": has_raises
        }
        
        if self._current_class:
            self._current_class["methods"].append(func_info)
        else:
            self.entities["functions"].append(func_info)

    def _extract_class_attributes(self, node: ast.ClassDef) -> List[str]:
        attrs = set()
        for child in node.body:
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

def _read_file_with_encoding(file_path: str) -> str:
    """Read file content with automatic encoding detection."""
    encodings = ['utf-8', 'utf-16', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Last resort: read with errors='replace'
    with open(file_path, "r", encoding='utf-8', errors='replace') as f:
        return f.read()

def get_entity_list(file_path: str) -> List[Dict[str, Any]]:
    """Returns a flat list of entities for display."""
    entities = analyze_file(file_path)
    entity_list = []
    
    # Functions
    for f in entities["functions"]:
        entity_list.append({
            "Function Name": f["name"],
            "Type": "Function",
            "Start Line": f["line"],
            "End Line": f["end_line"],
            "Has Docstring": bool(f["docstring"])
        })
    
    # Classes and Methods
    for cls in entities["classes"]:
        entity_list.append({
            "Function Name": cls["name"],
            "Type": "Class",
            "Start Line": cls["line"],
            "End Line": cls["end_line"],
            "Has Docstring": bool(cls["docstring"])
        })
        for m in cls["methods"]:
            entity_list.append({
                "Function Name": m["name"],
                "Type": "Method",
                "Start Line": m["line"],
                "End Line": m["end_line"],
                "Has Docstring": bool(m["docstring"])
            })
            
    return entity_list

def analyze_file(file_path: str) -> Dict[str, Any]:
    """Analyzes a single file using AST."""
    # Try multiple encodings to handle different file formats
    encodings = ['utf-8', 'utf-16', 'utf-8-sig', 'latin-1', 'cp1252']
    source = None
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                source = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if source is None:
        # Last resort: read with errors='replace' to ignore bad characters
        with open(file_path, "r", encoding='utf-8', errors='replace') as f:
            source = f.read()
    
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        escaped_newline_markers = ("\\n" in source) or ("\\r\\n" in source)
        has_minimal_real_newlines = source.count("\n") <= 1

        if escaped_newline_markers and has_minimal_real_newlines:
            normalized_source = (
                source.replace("\\r\\n", "\n")
                .replace("\\n", "\n")
                .replace("\\t", "\t")
            )
            tree = ast.parse(normalized_source)
        else:
            raise SyntaxError(f"{file_path}: {exc}") from exc

    extractor = DocstringExtractor(file_path)
    extractor.visit(tree)
    return extractor.entities