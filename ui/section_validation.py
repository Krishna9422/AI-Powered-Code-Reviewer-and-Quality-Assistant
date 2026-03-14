"""Validation section renderer."""

import os
import re

import streamlit as st

from core import doc_steward
from core.doc_steward import (
    apply_docstring_fix_at_line,
    apply_docstring_fixes_from_pydocstyle,
    apply_missing_docstrings,
    generate_coverage_report,
    get_entity_list,
)
from ui.dashboard_metrics import calculate_aggregate_metrics

def run_validation_section(view, file_list, files_to_display, show_all_files, docstring_style, output_json, use_uploaded_files, show_empty_state):
    if view != "Validation":
        return

    # Always render the page body; show result toast only when a message exists.
    last_fix_result = st.session_state.pop("validation_last_fix_result", {})
    if last_fix_result is not None:
        status_type = last_fix_result.get("type", "success")
        message = last_fix_result.get("message", "")
        if message:
            if status_type == "warning":
                st.warning(message)
            else:
                st.success(message)
        
        if file_list:
            missing_doc_items = []
            for file_to_scan in files_to_display:
                if not os.path.exists(file_to_scan):
                    continue
                try:
                    entities = get_entity_list(file_to_scan)
                except SyntaxError:
                    continue

                for entity in entities:
                    if not entity.get("Has Docstring"):
                        missing_doc_items.append({
                            "file_path": file_to_scan,
                            "file_name": os.path.basename(file_to_scan),
                            "name": entity.get("Function Name"),
                            "type": entity.get("Type"),
                            "line": entity.get("Start Line"),
                        })

            if view == "Validation":
                col_title, col_btn = st.columns([4, 1])
                with col_title:
                    st.markdown("<div class='ui-section-title'>🧩 Missing Docstrings</div>", unsafe_allow_html=True)
                with col_btn:
                    if missing_doc_items:
                        if st.button("✨ Fix All Missing", key="bulk_fix_missing", use_container_width=True):
                            files_to_fix = sorted({item["file_path"] for item in missing_doc_items})
                            fixed_count = 0
                            for target in files_to_fix:
                                if os.path.exists(target):
                                    apply_missing_docstrings(target, style=docstring_style)
                                    fixed_count += 1
                            st.session_state["validation_last_fix_result"] = {
                                "type": "success",
                                "message": f"✅ Auto-fixed missing docstrings in {fixed_count} file(s)."
                            }
                            st.cache_data.clear()
                            st.rerun()
                if missing_doc_items:
                    grouped_missing = {}
                    for item in missing_doc_items:
                        grouped_missing.setdefault(item["file_name"], []).append(item)
                    for fname, items in grouped_missing.items():
                        with st.expander(f"📄 {fname} ({len(items)} missing)", expanded=True):
                            for idx, it in enumerate(items):
                                card_col, btn_col = st.columns([6, 1])
                                with card_col:
                                    st.markdown(f'''
                                    <div style="background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 12px; margin-bottom: 8px; border-radius: 4px;">
                                        <span style="color: #ef4444; font-weight: bold; background: rgba(239, 68, 68, 0.2); padding: 2px 6px; border-radius: 4px; margin-right: 8px;">Missing</span>
                                        <strong style="color: #f8fafc; font-size: 1.1em;">{it['name']}</strong> 
                                        <span style="color: #94a3b8; font-size: 0.9em; float: right;">Type: {it['type']} | Line: {it['line']}</span>
                                    </div>
                                    ''', unsafe_allow_html=True)
                                with btn_col:
                                    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
                                    if st.button("🛠️ Fix", key=f"fix_m_{fname}_{it['line']}_{idx}", use_container_width=True):
                                        apply_missing_docstrings(it["file_path"], style=docstring_style)
                                        st.session_state["validation_last_fix_result"] = {
                                            "type": "success",
                                            "message": f"✅ Fixed missing docstring in {fname} at line {it['line']}."
                                        }
                                        st.cache_data.clear()
                                        st.rerun()
                else:
                    st.success("✅ All functions and methods have docstrings in current scope.")

            detailed_violations = []
            pydoc_report = generate_coverage_report(files_to_display, include_pydocstyle=True).get("pydocstyle", {})
            st.markdown("<div class='ui-section-title'>🧪 pydocstyle Checks</div>", unsafe_allow_html=True)
            if pydoc_report.get("available", False):
                col1, col2 = st.columns(2)
                col1.metric("Files with Violations", pydoc_report.get("files_with_violations", 0))
                col2.metric("Total Violations", pydoc_report.get("total_violations", 0))

                violation_rows = []
                for path, details in pydoc_report.get("details", {}).items():
                    count = details.get("violations_count", 0)
                    if count > 0:
                        violation_rows.append({
                            "File": os.path.basename(path),
                            "Violations": count,
                        })

                if violation_rows:
                    st.dataframe(violation_rows, use_container_width=True)

                    if view == "Validation":
                        for path, details in pydoc_report.get("details", {}).items():
                            violation_items = details.get("violations_detailed", [])

                            if violation_items:
                                for violation in violation_items:
                                    message = violation.get("message", "")
                                    function_match = re.search(r"`([^`]+)`", message)
                                    symbol_name = function_match.group(1) if function_match else "-"

                                    detailed_violations.append({
                                        "file_path": violation.get("file_path", path),
                                        "File": os.path.basename(violation.get("file_path", path)),
                                        "Function / Symbol": symbol_name,
                                        "Line": violation.get("line"),
                                        "Rule": violation.get("code", "-"),
                                        "Message": message,
                                    })
                            else:
                                for violation in details.get("violations", []):
                                    code_match = re.search(r"\b(D\d{3})\b", violation)
                                    code = code_match.group(1) if code_match else "-"
                                    line_match = re.search(r":(\d+)\b", violation)
                                    line_no = int(line_match.group(1)) if line_match else None

                                    message = violation
                                    if code_match:
                                        message = violation[code_match.end():].strip(" :.-")

                                    function_match = re.search(r"`([^`]+)`", violation)
                                    symbol_name = function_match.group(1) if function_match else "-"

                                    detailed_violations.append({
                                        "file_path": path,
                                        "File": os.path.basename(path),
                                        "Function / Symbol": symbol_name,
                                        "Line": line_no,
                                        "Rule": code,
                                        "Message": message,
                                    })

                        col_title, col_btn = st.columns([4, 1])
                        with col_title:
                            st.markdown("<div class='ui-section-title'>🔍 Detailed Docstring Mistakes</div>", unsafe_allow_html=True)
                        with col_btn:
                            if detailed_violations:
                                if st.button("✨ Fix All Mistakes", key="bulk_fix_mistakes", use_container_width=True):
                                    files_to_fix = sorted({item["file_path"] for item in detailed_violations})
                                    fixed_count = 0
                                    for target in files_to_fix:
                                        if os.path.exists(target):
                                            fixed_count += apply_docstring_fixes_from_pydocstyle(target, style=docstring_style)
                                    st.session_state["validation_last_fix_result"] = {
                                        "type": "success",
                                        "message": f"✅ Auto-fixed {fixed_count} detailed docstring mistake(s)."
                                    }
                                    st.cache_data.clear()
                                    st.rerun()
                        if detailed_violations:
                            grouped_violations = {}
                            for v in detailed_violations:
                                grouped_violations.setdefault(v["File"], []).append(v)
                            for fname, violations in grouped_violations.items():
                                with st.expander(f"📄 {fname} ({len(violations)} issues)", expanded=True):
                                    for idx, v in enumerate(violations):
                                        card_col, btn_col = st.columns([6, 1])
                                        with card_col:
                                            st.markdown(f'''
                                            <div style="background-color: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 12px; margin-bottom: 8px; border-radius: 4px;">
                                                <span style="color: #f59e0b; font-weight: bold; background: rgba(245, 158, 11, 0.2); padding: 2px 6px; border-radius: 4px; margin-right: 8px;">{v['Rule']}</span>
                                                <strong style="color: #f8fafc; font-size: 1.1em;">{v['Function / Symbol']}</strong> 
                                                <span style="color: #94a3b8; font-size: 0.9em; float: right;">Line: {v['Line']}</span>
                                                <div style="margin-top: 8px; color: #cbd5e1; font-size: 0.95em;">{v['Message']}</div>
                                            </div>
                                            ''', unsafe_allow_html=True)
                                        with btn_col:
                                            st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
                                            if st.button("🛠️ Fix", key=f"fix_d_{fname}_{v['Line']}_{idx}", use_container_width=True):
                                                if v.get("Line") is not None:
                                                    fixed = apply_docstring_fix_at_line(v["file_path"], int(v["Line"]), style=docstring_style)
                                                else:
                                                    fixed = apply_docstring_fixes_from_pydocstyle(v["file_path"], style=docstring_style) > 0
                                                
                                                if fixed:
                                                    st.session_state["validation_last_fix_result"] = {
                                                        "type": "success",
                                                        "message": f"✅ Fixed {v['Rule']} in {fname} at line {v['Line']}."
                                                    }
                                                else:
                                                    st.session_state["validation_last_fix_result"] = {
                                                        "type": "warning",
                                                        "message": f"⚠️ Could not fix {v['Rule']} in {fname}."
                                                    }
                                                st.cache_data.clear()
                                                st.rerun()
                        else:
                            st.success("✅ No detailed docstring mistakes found.")
                else:
                    st.success("✅ No pydocstyle violations found for current scope.")
            else:
                st.warning(pydoc_report.get("message", "pydocstyle checks unavailable."))

            if view == "Validation":
                if missing_doc_items or detailed_violations:
                    st.markdown("<div class='ui-section-title'>🛠️ Auto Fix All Validation Errors</div>", unsafe_allow_html=True)
                    
                    col_title, col_fix_all = st.columns([4, 1])
                    with col_fix_all:
                        fix_all_clicked = st.button("✨ Fix Everything", key="auto_fix_all_validation_bottom", use_container_width=True)

                    if fix_all_clicked:
                        files_for_missing = sorted({item["file_path"] for item in missing_doc_items})
                        files_for_pydocstyle = sorted({item["file_path"] for item in detailed_violations})

                        fixed_missing_files = 0
                        for target_file in files_for_missing:
                            if os.path.exists(target_file):
                                apply_missing_docstrings(target_file, style=docstring_style)
                                fixed_missing_files += 1

                        fixed_pydoc_entities = 0
                        for target_file in files_for_pydocstyle:
                            fixed_pydoc_entities += apply_docstring_fixes_from_pydocstyle(
                                target_file,
                                style=docstring_style,
                            )

                        st.success(
                            "✅ Auto-fix all complete: "
                            f"{fixed_missing_files} file(s) for missing docstrings, "
                            f"{fixed_pydoc_entities} pydocstyle issue target(s) updated."
                        )
                        
                        # Provide download links for all fixed files
                        all_fixed_files = sorted(set(files_for_missing) | set(files_for_pydocstyle))
                        if all_fixed_files and use_uploaded_files:
                            st.markdown("#### 📥 Download Fixed Files")
                            for target_file in all_fixed_files:
                                if os.path.exists(target_file):
                                    file_content = doc_steward._read_file_with_encoding(target_file)
                                    file_name = os.path.basename(target_file)
                                    st.download_button(
                                        label=f"⬇️ Download {file_name}",
                                        data=file_content,
                                        file_name=file_name,
                                        mime="text/plain",
                                        key=f"download_allfix_{file_name}_{target_file}"
                                    )
                        
                        st.session_state["validation_last_fix_result"] = {
                            "type": "success",
                            "message": (
                                "✅ Auto-fix all complete: "
                                f"{fixed_missing_files} file(s) for missing docstrings, "
                                f"{fixed_pydoc_entities} pydocstyle issue target(s) updated."
                            ),
                        }
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.success("✅ No validation errors available for auto-fix.")

                if use_uploaded_files and file_list:
                    st.markdown("<br><hr><br><h2 style='text-align: center;'>📥 Download Modified Files</h2>", unsafe_allow_html=True)
                    st.markdown(
                        """
                        <style>
                        /* Target the persistent download buttons specifically via their key substrings */
                        button[data-testid="stBaseButton-secondary"] {
                            height: 70px !important;
                            font-size: 1.3rem !important;
                            width: 100% !important;
                            border-radius: 12px !important;
                            font-weight: 700 !important;
                            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2) !important;
                        }
                        </style>
                        """, unsafe_allow_html=True
                    )
                    cols = st.columns(min(len(file_list), 3))
                    for i, target_file in enumerate(file_list):
                        if os.path.exists(target_file):
                            file_content = doc_steward._read_file_with_encoding(target_file)
                            file_name = os.path.basename(target_file)
                            with cols[i % 3]:
                                st.download_button(
                                    label=f"⬇️ Download {file_name}",
                                    data=file_content,
                                    file_name=file_name,
                                    mime="text/plain",
                                    key=f"persistent_dl_bottom_{file_name}_{i}"
                                )
                    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
            
            # Display aggregate coverage report only on demand.
            if len(file_list) > 1 and show_all_files:
                if "validation_show_aggregate_report" not in st.session_state:
                    st.session_state.validation_show_aggregate_report = False

                col_title, col_btn = st.columns([4, 1])
                with col_title:
                    st.markdown("<div class='ui-section-title'>📊 Aggregate Coverage Report</div>", unsafe_allow_html=True)
                with col_btn:
                    button_label = "Hide Report" if st.session_state.validation_show_aggregate_report else "Show Report"
                    if st.button(button_label, key="toggle_validation_aggregate_report", use_container_width=True):
                        st.session_state.validation_show_aggregate_report = not st.session_state.validation_show_aggregate_report

                if st.session_state.validation_show_aggregate_report:
                    agg_metrics = calculate_aggregate_metrics(file_list)

                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("📁 Files", agg_metrics["file_count"])
                    col2.metric("Total Functions", agg_metrics["total_functions"])
                    col3.metric("Documented", agg_metrics["total_documented"])
                    col4.metric("Undocumented", agg_metrics["total_undocumented"])
                    col5.metric("Avg Coverage (%)", f"{round(agg_metrics['avg_coverage'], 1)}%")

                    st.markdown("<div class='ui-section-title'>File-wise Breakdown</div>", unsafe_allow_html=True)
                    file_breakdown = []
                    for detail in agg_metrics["file_details"]:
                        file_breakdown.append({
                            "File": detail["file"],
                            "Functions": detail["functions"],
                            "Documented": detail["documented"],
                            "Coverage (%)": f"{round(detail['coverage'], 1)}%",
                            "MI": f"{round(detail['mi'], 2)}"
                        })
                    st.dataframe(file_breakdown, use_container_width=True)
                    st.divider()
            
            # Display individual file analysis
            if len(file_list) > 1 and show_all_files:
                st.markdown("<div class='ui-section-title'>📄 Individual File Analysis</div>", unsafe_allow_html=True)
            
            for file_to_scan in files_to_display:
                if os.path.exists(file_to_scan):
                    file_name = os.path.basename(file_to_scan)
                    st.caption(f"📄 Analyzing: {file_name}")
                    try:
                        entities = get_entity_list(file_to_scan)
                    except SyntaxError:
                        st.error(f"❌ Syntax Error in {file_name}! Cannot calculate coverage.")
                        continue
                    
                    # Filter ONLY Functions and Methods for the UI
                    func_entities = [e for e in entities if e.get("Type") in ("Function", "Method")]
                    
                    total_funcs = len(func_entities)
                    documented = sum(1 for e in func_entities if e.get("Has Docstring"))
                    undocumented = total_funcs - documented
                    coverage = (documented / total_funcs * 100) if total_funcs > 0 else 0.0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Functions", total_funcs)
                    col2.metric("Documented", documented)
                    col3.metric("Undocumented", undocumented)
                    col4.metric("Coverage (%)", f"{round(coverage, 1)}")
                    
                    table_toggle_key = f"validation_show_function_table_{file_name}_{file_to_scan}"
                    if table_toggle_key not in st.session_state:
                        st.session_state[table_toggle_key] = False

                    toggle_label = "Hide Function Table" if st.session_state[table_toggle_key] else "Show Function Table"
                    if st.button(toggle_label, key=f"toggle_{table_toggle_key}", use_container_width=False):
                        st.session_state[table_toggle_key] = not st.session_state[table_toggle_key]

                    if st.session_state[table_toggle_key]:
                        st.markdown("<div class='ui-section-title'>Function-wise Docstring Status</div>", unsafe_allow_html=True)

                        formatted_entities = []
                        for i, e in enumerate(func_entities):
                            formatted_entities.append({
                                "Function Name": e["Function Name"],
                                "Type": e["Type"],
                                "Start Line": e["Start Line"],
                                "End Line": e["End Line"],
                                "Has Docstring": "✓" if e["Has Docstring"] else "✗"
                            })

                        st.dataframe(formatted_entities, use_container_width=True)
                    
                    if total_funcs > documented:
                        if st.button(f"Apply Missing Docstrings for {file_name}", key=file_to_scan):
                            apply_missing_docstrings(file_to_scan, style=docstring_style)
                            st.success(f"✅ Applied using {docstring_style.upper()} style! Reloading...")
                            st.rerun()
                    st.divider()
        else:
            show_empty_state()


