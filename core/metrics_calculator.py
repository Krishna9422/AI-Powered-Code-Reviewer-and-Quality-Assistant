import ast
import os
import json
import re
import subprocess
from typing import Dict, List, Any, Optional

from .ast_extractor import get_entity_list, _read_file_with_encoding, analyze_file
import radon
from radon.complexity import cc_visit
from radon.metrics import mi_visit

def get_code_metrics(file_path: str) -> Dict[str, Any]:
    """Get code metrics.

    Args:
        file_path: Description of file_path.

    Returns:
        Description of the return value.
    """
    from radon.complexity import cc_visit
    from radon.raw import analyze
    
    source = _read_file_with_encoding(file_path)
    
    # Complexity
    cc_blocks = cc_visit(source)
    # Raw metrics
    raw = analyze(source)
    
    return {
        "loc": raw.loc,
        "lloc": raw.lloc,
        "sloc": raw.sloc,
        "comments": raw.comments,
        "multi": raw.multi,
        "blank": raw.blank,
        "complexity": [
            {"type": b.type, "name": b.name, "complexity": b.complexity, "rank": b.rank}
            for f in [cc_blocks] for b in f
        ]
    }

def get_maintainability_index(file_path: str) -> float:
    from radon.metrics import mi_visit
    from radon.raw import analyze
    source = _read_file_with_encoding(file_path)
    raw = analyze(source)
    mi = mi_visit(source, raw.multi)
    return mi

def get_function_complexity(file_path: str) -> Dict[str, Any]:
    from radon.complexity import cc_visit
    
    source = _read_file_with_encoding(file_path)
        
    cc_blocks = cc_visit(source)
    complexity_map = {b.name: b.complexity for b in cc_blocks}
    
    entities = analyze_file(file_path)
    functions_list = []
    
    # Process standalone functions
    for f in entities["functions"]:
        functions_list.append({
            "name": f["name"],
            "type": "Function",
            "start_line": f["line"],
            "end_line": f["end_line"],
            "has_docstring": bool(f["docstring"]),
            "complexity": complexity_map.get(f["name"], 1)
        })
        
    # Process methods within classes
    for cls in entities["classes"]:
        for m in cls["methods"]:
            functions_list.append({
                "name": m["name"],
                "type": "Method",
                "start_line": m["line"],
                "end_line": m["end_line"],
                "has_docstring": bool(m["docstring"]),
                "complexity": complexity_map.get(m["name"], 1)
            })
            
    functions_list.sort(key=lambda x: x["start_line"])
    
    total_funcs = len(functions_list)
    documented = sum(1 for f in functions_list if f["has_docstring"])
    undocumented = total_funcs - documented
    coverage = (documented / total_funcs * 100) if total_funcs > 0 else 0.0
    
    return {
        "total_functions": total_funcs,
        "documented": documented,
        "undocumented": undocumented,
        "coverage_percent": round(coverage, 2),
        "functions": functions_list
    }