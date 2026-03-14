import ast
import os
import json
import re
import subprocess
from typing import Dict, List, Any, Optional

from .ast_extractor import analyze_file

def run_pydocstyle_checks(files: List[str]) -> Dict[str, Any]:
    """Runs pydocstyle checks for provided files."""
    result = {
        "available": True,
        "total_violations": 0,
        "files_with_violations": 0,
        "details": {}
    }

    for file_path in files:
        if not os.path.exists(file_path):
            continue

        try:
            completed = subprocess.run(
                ["pydocstyle", file_path],
                capture_output=True,
                text=True,
                check=False
            )
        except FileNotFoundError:
            return {
                "available": False,
                "total_violations": 0,
                "files_with_violations": 0,
                "details": {},
                "message": "pydocstyle is not installed or not available in PATH"
            }

        output = (completed.stdout or "") + (completed.stderr or "")
        violations = []
        detailed_violations = []
        current_file = file_path
        current_line = None

        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            location_match = re.match(r"^(.*?\.py):(\d+)(?:\b|:|\s)", line)
            if location_match:
                current_file = location_match.group(1)
                current_line = int(location_match.group(2))

            code_match = re.search(r"\b(D\d{3})\b\s*:?\s*(.*)", line)
            if code_match:
                rule_code = code_match.group(1)
                message = code_match.group(2).strip()

                if current_line is not None:
                    summary = f"{current_file}:{current_line}: {rule_code}: {message}"
                else:
                    summary = f"{current_file}: {rule_code}: {message}"

                violations.append(summary)
                detailed_violations.append({
                    "file_path": current_file,
                    "line": current_line,
                    "code": rule_code,
                    "message": message,
                })

        result["details"][file_path] = {
            "violations_count": len(violations),
            "violations": violations,
            "violations_detailed": detailed_violations,
        }
        result["total_violations"] += len(violations)
        if violations:
            result["files_with_violations"] += 1

    return result

def generate_coverage_report(files: List[str], include_pydocstyle: bool = True) -> Dict[str, Any]:
    """Produces the docstring coverage report."""
    report = {
        "files_analyzed": len(files),
        "total_entities": 0,
        "documented_entities": 0,
        "details": {}
    }

    valid_files_count = 0

    for file_path in files:
        if not os.path.exists(file_path):
            continue

        try:
            entities = analyze_file(file_path)
        except SyntaxError as exc:
            report["details"][file_path] = {
                "coverage": 0.0,
                "stats": {"total": 0, "documented": 0},
                "parse_error": str(exc),
            }
            continue

        valid_files_count += 1
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

    report["files_analyzed"] = valid_files_count
    report["overall_coverage"] = round((report["documented_entities"] / report["total_entities"] * 100), 2) if report["total_entities"] > 0 else 0.0

    if include_pydocstyle:
        report["pydocstyle"] = run_pydocstyle_checks(files)

    return report