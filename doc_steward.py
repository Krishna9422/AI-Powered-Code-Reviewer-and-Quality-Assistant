import ast
import os
import json
import re
from typing import Dict, List, Any, Optional

class DocstringExtractor(ast.NodeVisitor):
    """AST-based extractor for functions, classes, and modules.
    
    Attributes:
        file_path (str): Path to the python file.
        entities (dict): Extracted entities and their docstring status.
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
        
        func_info = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "line": node.lineno,
            "end_line": getattr(node, 'end_lineno', node.lineno),
            "args": args
        }
        
        if self._current_class:
            self._current_class["methods"].append(func_info)
        else:
            self.entities["functions"].append(func_info)

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

def generate_google_docstring(name: str, args: List[str] = None, is_class: bool = False, indent: int = 4) -> str:
    """Generates a baseline Google-style docstring.
    
    Args:
        name (str): Name of the class or function.
        args (list): List of argument names.
        is_class (bool): Whether the entity is a class.
        indent (int): Indentation spaces.

    Returns:
        str: Formatted Google-style docstring.
    """
    prefix = " " * indent
    doc = f'{prefix}"""{name.replace("_", " ").capitalize()}.\n\n'
    if args:
        doc += f"{prefix}Args:\n"
        for arg in args:
            doc += f"{prefix}    {arg}: Description of {arg}.\n"
    
    if not is_class:
        doc += f"\n{prefix}Returns:\n"
        doc += f"{prefix}    Description of the return value.\n"
    
    doc += f'{prefix}"""'
    return doc

def analyze_file(file_path: str) -> Dict[str, Any]:
    """Analyzes a single file using AST."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
        tree = ast.parse(source)
    
    extractor = DocstringExtractor(file_path)
    extractor.visit(tree)
    return extractor.entities

def generate_coverage_report(files: List[str]) -> Dict[str, Any]:
    """Produces the docstring coverage report."""
    report = {
        "files_analyzed": len(files),
        "total_entities": 0,
        "documented_entities": 0,
        "details": {}
    }

    for file_path in files:
        if not os.path.exists(file_path): continue
        entities = analyze_file(file_path)
        file_stats = {"total": 0, "documented": 0}
        
        def check(item):
            file_stats["total"] += 1
            if item.get("docstring"):
                file_stats["documented"] += 1
        
        check(entities["module"])
        for cls in entities["classes"]:
            check(cls)
            for m in cls["methods"]:
                check(m)
        for f in entities["functions"]:
            check(f)
                
        report["total_entities"] += file_stats["total"]
        report["documented_entities"] += file_stats["documented"]
        
        coverage = (file_stats["documented"] / file_stats["total"] * 100) if file_stats["total"] > 0 else 0.0
        report["details"][file_path] = {
            "coverage": round(coverage, 2),
            "stats": file_stats
        }

    report["overall_coverage"] = round((report["documented_entities"] / report["total_entities"] * 100), 2) if report["total_entities"] > 0 else 0.0
    return report

def apply_missing_docstrings(file_path: str):
    """Adds missing Google-style docstrings to a file."""
    entities = analyze_file(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    to_add = []
    
    # Check functions
    for f in entities["functions"]:
        if not f["docstring"]:
            # Find indentation of the def line
            def_line = lines[f["line"]-1]
            indent = len(def_line) - len(def_line.lstrip())
            to_add.append((f["line"], generate_google_docstring(f["name"], f["args"], indent=indent+4)))
            
    # Check classes
    for cls in entities["classes"]:
        if not cls["docstring"]:
            def_line = lines[cls["line"]-1]
            indent = len(def_line) - len(def_line.lstrip())
            to_add.append((cls["line"], generate_google_docstring(cls["name"], is_class=True, indent=indent+4)))
        for m in cls["methods"]:
            if not m["docstring"]:
                def_line = lines[m["line"]-1]
                indent = len(def_line) - len(def_line.lstrip())
                to_add.append((m["line"], generate_google_docstring(m["name"], m["args"], indent=indent+4)))
                
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

def get_code_metrics(file_path: str) -> Dict[str, Any]:
    """Calculates code metrics using radon."""
    from radon.complexity import cc_visit
    from radon.raw import analyze
    
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    
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
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    raw = analyze(source)
    mi = mi_visit(source, raw.multi)
    return mi

def get_function_complexity(file_path: str) -> List[Dict]:
    from radon.complexity import cc_visit
    
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
        
    cc_blocks = cc_visit(source)
    complexity_map = {b.name: b.complexity for b in cc_blocks}
    
    entities = analyze_file(file_path)
    result = []
    
    for f in entities["functions"]:
        result.append({
            "name": f["name"],
            "complexity": complexity_map.get(f["name"], 1),
            "line": f["line"],
            "has_docstring": bool(f["docstring"])
        })
        
    for cls in entities["classes"]:
        for m in cls["methods"]:
            result.append({
                "name": m["name"],
                "complexity": complexity_map.get(m["name"], 1),
                "line": m["line"],
                "has_docstring": bool(m["docstring"])
            })
            
    result.sort(key=lambda x: x["line"])
    return result

if __name__ == "__main__":
    target_files = ["basics.py", "main_app.py", "sample_a.py", "sample_b.py"]
    existing_files = [f for f in target_files if os.path.exists(f)]
    
    if existing_files:
        print("--- Docstring Coverage Report (Before) ---")
        coverage_before = generate_coverage_report(existing_files)
        print(json.dumps(coverage_before, indent=2))
        
        # Save initial report
        os.makedirs("storage", exist_ok=True)
        with open("storage/review_logs.json", "w") as rf:
            json.dump(coverage_before, rf, indent=4)
        print("\nInitial report saved to storage/review_logs.json")
        
        # Apply docstrings
        for f in existing_files:
            apply_missing_docstrings(f)
            
        print("\n--- Docstring Coverage Report (After Application) ---")
        coverage_after = generate_coverage_report(existing_files)
        print(json.dumps(coverage_after, indent=2))
    else:
        print("No target files found to analyze.")
