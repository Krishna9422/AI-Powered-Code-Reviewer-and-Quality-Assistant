"""Docstring page section renderer."""

import difflib
import os

import streamlit as st

from core import doc_steward
from core.doc_steward import apply_docstring_fix_at_line

def run_docstring_section(view, file_list, docstring_style, show_empty_state, collect_callable_nodes, get_docstring_issue):
    if view == "Docstring":
        if file_list:
            st.markdown(
                """
                <style>
                    div[data-testid="stRadio"] {
                        position: sticky;
                        top: 0.75rem;
                        z-index: 20;
                        padding: 0.9rem 1rem;
                        margin-bottom: 0.5rem;
                        border-radius: 14px;
                        border: 1px solid rgba(129, 140, 248, 0.35);
                        background: rgba(15, 23, 42, 0.75);
                        backdrop-filter: blur(12px);
                    }

                    div[data-testid="stRadio"] div[role="radiogroup"] {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        gap: 0.65rem;
                        flex-wrap: wrap;
                    }

                    div[data-testid="stRadio"] div[role="radiogroup"] > label {
                        margin: 0;
                        min-width: 120px;
                        justify-content: center;
                        text-align: center;
                        border-radius: 999px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        background: rgba(30, 41, 59, 0.75);
                        padding: 0.45rem 0.95rem;
                        transition: all 0.25s ease;
                    }

                    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
                        transform: translateY(-1px);
                        border-color: rgba(129, 140, 248, 0.8);
                        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.22);
                    }

                    div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
                        display: none;
                    }

                    div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
                        border-color: rgba(192, 132, 252, 0.95);
                        background: linear-gradient(135deg, rgba(99, 102, 241, 0.65) 0%, rgba(168, 85, 247, 0.65) 100%);
                        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.34);
                    }

                    div[data-testid="stRadio"] div[role="radiogroup"] > label span {
                        color: #f8fafc !important;
                        font-weight: 700 !important;
                        letter-spacing: 0.03em;
                    }
                </style>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div class='ui-section-title'>🧩 Docstring Style</div>", unsafe_allow_html=True)
            docstring_style = st.radio(
                "Choose style",
                options=["google", "numpy", "rest"],
                format_func=lambda value: value.upper(),
                horizontal=True,
                key="docstring_style"
            )
            st.caption("Selected style is used for preview, auto-fix, and apply actions on this page.")

            docstring_apply_result = st.session_state.pop("docstring_apply_result", None)
            if docstring_apply_result:
                if docstring_apply_result.get("type") == "success":
                    st.success(docstring_apply_result.get("message", "Docstring updated."))
                else:
                    st.warning(docstring_apply_result.get("message", "Could not apply docstring."))

            col_left, col_right = st.columns([1, 2.5])
            with col_left:
                st.markdown("<div style='display: flex; align-items: center; gap: 10px;'><h2 style='margin: 0;'>📂 Files</h2></div>", unsafe_allow_html=True)
                st.caption(f"Total files: {len(file_list)} | Style: {docstring_style.upper()}")

                if "ds_ok_overrides" not in st.session_state:
                    st.session_state.ds_ok_overrides = set()
                
                if "docstring_selected_file" not in st.session_state:
                    st.session_state.docstring_selected_file = file_list[0] if file_list else None
                if "docstring_selected_func" not in st.session_state:
                    st.session_state.docstring_selected_func = None
                
                for file_path in file_list:
                    file_name = os.path.basename(file_path)
                    try:
                        analysis = doc_steward.analyze_file(file_path)
                        funcs = collect_callable_nodes(analysis)
                        has_fix_needed = False
                        for f in funcs:
                            override_key = f"{file_path}|{int(f.get('line', -1))}|{docstring_style}"
                            issue = get_docstring_issue(f, docstring_style)
                            if issue:
                                # If the source changed or style switched, do not keep stale OK overrides.
                                st.session_state.ds_ok_overrides.discard(override_key)
                                has_fix_needed = True
                                break
                    except SyntaxError:
                        has_fix_needed = False
                        
                    status_icon = "🔧 Fix" if has_fix_needed else "✅ OK"
                    
                    if st.button(f"{file_name} {status_icon}", key=f"ds_file_{file_path}", use_container_width=True):
                        st.session_state.docstring_selected_file = file_path
                        st.session_state.docstring_selected_func = None
                
                if st.session_state.docstring_selected_file and os.path.exists(st.session_state.docstring_selected_file):
                    st.markdown("---")
                    file_name_display = os.path.basename(st.session_state.docstring_selected_file)
                    st.markdown(f"**Functions in {file_name_display}**")
                    try:
                        analysis = doc_steward.analyze_file(st.session_state.docstring_selected_file)
                        funcs = collect_callable_nodes(analysis)
                        st.caption("Legend: 🔧 Fix | ✅ OK")
                            
                        # Resync selected function to capture newly written docstrings into the session
                        if st.session_state.docstring_selected_func:
                            old_f = st.session_state.docstring_selected_func
                            refreshed_match = None
                            old_line = int(old_f.get("line", -1)) if old_f.get("line") is not None else -1
                            old_name = old_f.get("name")
                            old_args = old_f.get("args")

                            for f in funcs:
                                if int(f.get("line", -2)) == old_line and f.get("name") == old_name:
                                    refreshed_match = f
                                    break

                            if refreshed_match is None:
                                for f in funcs:
                                    if f.get("name") == old_name and f.get("args") == old_args:
                                        refreshed_match = f
                                        break

                            if refreshed_match is not None:
                                st.session_state.docstring_selected_func = refreshed_match
                            
                        for f in funcs:
                            fn_name = f["name"]
                            btn_label = fn_name
                            override_key = f"{st.session_state.docstring_selected_file}|{int(f.get('line', -1))}|{docstring_style}"
                            issue = get_docstring_issue(f, docstring_style)
                            if issue:
                                # Keep status truthful to current style/content.
                                st.session_state.ds_ok_overrides.discard(override_key)
                                btn_label += " 🔧 Fix"
                            else:
                                btn_label += " ✅ OK"
                                
                            if st.button(btn_label, key=f"ds_func_{fn_name}_{f['line']}", use_container_width=True):
                                st.session_state.docstring_selected_func = f
                                
                        st.markdown("<hr style='margin: 10px 0; opacity: 0.2;'>", unsafe_allow_html=True)
                        fix_candidates = []
                        for f in funcs:
                            override_key = f"{st.session_state.docstring_selected_file}|{int(f.get('line', -1))}|{docstring_style}"
                            issue = get_docstring_issue(f, docstring_style)
                            if issue:
                                st.session_state.ds_ok_overrides.discard(override_key)
                                fix_candidates.append(f)
                        if fix_candidates:
                            if st.button(f"✨ Auto-Fix All ({len(fix_candidates)})", use_container_width=True, key="ds_fix_all"):
                                progress_text = "Generating docstrings. Please wait."
                                my_bar = st.progress(0, text=progress_text)
                                
                                for i, f in enumerate(fix_candidates):
                                    percentage = int((i / len(fix_candidates)) * 100)
                                    my_bar.progress(percentage, text=f"Processing {f['name']} ({i+1}/{len(fix_candidates)})")
                                    
                                    try:
                                        file_content = doc_steward._read_file_with_encoding(st.session_state.docstring_selected_file)
                                        lines = file_content.splitlines()
                                        start_idx = f["line"] - 1
                                        end_idx = f.get("end_line", start_idx + 1)
                                        func_code = "\n".join(lines[start_idx:end_idx])
                                    except Exception:
                                        continue
                                        
                                    if func_code:
                                        indent = f.get("col_offset", 0) + 4
                                        gen_doc = doc_steward.generate_docstring_llm(
                                            func_code=func_code,
                                            style=docstring_style,
                                            indent=indent
                                        )
                                        applied = apply_docstring_fix_at_line(
                                            st.session_state.docstring_selected_file, 
                                            f['line'], 
                                            style=docstring_style, 
                                            doc_text_override=gen_doc
                                        )
                                        if applied:
                                            override_key = f"{st.session_state.docstring_selected_file}|{int(f.get('line', -1))}|{docstring_style}"
                                            st.session_state.ds_ok_overrides.add(override_key)
                                        func_key = f"{st.session_state.docstring_selected_file}_{f['name']}_{f['line']}_{docstring_style}"
                                        if "ds_generated_docs" in st.session_state and func_key in st.session_state.ds_generated_docs:
                                            del st.session_state.ds_generated_docs[func_key]
                                            
                                my_bar.progress(100, text="Done!")
                                st.rerun()

                    except Exception as e:
                        st.error(f"Error reading file: {e}")

            with col_right:
                if not st.session_state.docstring_selected_file:
                    st.info("Select a file from the left to begin.")
                elif not st.session_state.docstring_selected_func:
                    st.info("Select a function to view and edit its docstring.")
                else:
                    func = st.session_state.docstring_selected_func
                    st.markdown(f"### Function: <code style='color: #10b981; background: rgba(16, 185, 129, 0.1); padding: 2px 6px; border-radius: 4px;'>{func['name']}</code>", unsafe_allow_html=True)
                    
                    col_b, col_a = st.columns(2)
                    
                    indent = func.get("col_offset", 0) + 4
                    prefix = " " * indent
                    
                    before_doc = func.get("docstring")
                    if not before_doc:
                        before_text_display = "❌ No existing docstring"
                        before_text_diff = "No existing docstring\n"
                    else:
                        b_lines = before_doc.splitlines()
                        indented_b_lines = [prefix + '"""']
                        for line in b_lines:
                            if line.strip() == "":
                                indented_b_lines.append("")
                            else:
                                indented_b_lines.append(prefix + line)
                        indented_b_lines.append(prefix + '"""')
                        before_text_display = "\n".join(indented_b_lines)
                        before_text_diff = before_text_display + "\n"
                        
                    func_key = f"{st.session_state.docstring_selected_file}_{func['name']}_{func['line']}_{docstring_style}"
                    if "ds_generated_docs" not in st.session_state:
                        st.session_state.ds_generated_docs = {}
                        
                    if func_key not in st.session_state.ds_generated_docs:
                        func_code = ""
                        try:
                            file_content = doc_steward._read_file_with_encoding(st.session_state.docstring_selected_file)
                            lines = file_content.splitlines()
                            start_idx = func["line"] - 1
                            end_idx = func["end_line"]
                            func_code = "\n".join(lines[start_idx:end_idx])
                        except Exception:
                            pass
                            
                        with st.spinner("🧠 Generating docstring with AI..."):
                            gen_doc = doc_steward.generate_docstring_llm(
                                func_code=func_code,
                                style=docstring_style,
                                indent=indent
                            )
                        st.session_state.ds_generated_docs[func_key] = gen_doc
                    
                    new_doc = st.session_state.ds_generated_docs[func_key]

                    before_norm = "\n".join(line.rstrip() for line in before_text_display.strip().splitlines())
                    after_norm = "\n".join(line.rstrip() for line in new_doc.strip().splitlines())
                    preview_matches = before_norm == after_norm
                    current_override_key = f"{st.session_state.docstring_selected_file}|{int(func.get('line', -1))}|{docstring_style}"
                    if preview_matches:
                        st.session_state.ds_ok_overrides.add(current_override_key)
                    
                    # Do not do ANY manual HTML replacing if using a simple code block or letting markdown handle it natively.
                    safe_before = before_text_display.replace("<", "&lt;").replace(">", "&gt;")
                    safe_after = new_doc.replace("<", "&lt;").replace(">", "&gt;")
                    
                    with col_b:
                        st.caption("Before")
                        st.markdown(f'''<div style="background: rgba(30, 41, 59, 0.4); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); min-height: 250px; overflow-x: auto;">
```python
{before_text_display}
```
</div>''', unsafe_allow_html=True)
                        
                    with col_a:
                        st.caption("After (Preview)")
                        st.markdown(f'''<div style="background: rgba(16, 185, 129, 0.05); padding: 1rem; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2); min-height: 250px; position: relative; overflow-x: auto;">
```python
{new_doc}
```
</div>''', unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                        if preview_matches:
                            st.success("✅ OK: Before and After match for this function.")
                        accept_button_text = "✅ OK" if preview_matches else "✅ Accept"
                        accept_key = f"ds_accept_{func['name']}_{func['line']}_{docstring_style}"
                        reject_key = f"ds_reject_{func['name']}_{func['line']}_{docstring_style}"
                        with btn_col1:
                            if st.button(accept_button_text, use_container_width=True, key=accept_key):
                                try:
                                    applied = apply_docstring_fix_at_line(
                                        st.session_state.docstring_selected_file,
                                        int(func['line']),
                                        style=docstring_style,
                                        doc_text_override=new_doc,
                                    )
                                except Exception:
                                    applied = False

                                if applied:
                                    st.session_state.ds_ok_overrides.add(current_override_key)
                                    if func_key in st.session_state.ds_generated_docs:
                                        del st.session_state.ds_generated_docs[func_key]

                                    refreshed_func = None
                                    try:
                                        refreshed_analysis = doc_steward.analyze_file(st.session_state.docstring_selected_file)
                                        refreshed_funcs = refreshed_analysis.get("functions", [])
                                        for cls in refreshed_analysis.get("classes", []):
                                            refreshed_funcs.extend(cls.get("methods", []))

                                        for rf in refreshed_funcs:
                                            if rf.get("name") == func.get("name") and int(rf.get("line", -2)) == int(func.get("line", -1)):
                                                refreshed_func = rf
                                                break

                                        if refreshed_func is None:
                                            for rf in refreshed_funcs:
                                                if rf.get("name") == func.get("name") and rf.get("args") == func.get("args"):
                                                    refreshed_func = rf
                                                    break
                                    except Exception:
                                        refreshed_func = None

                                    if refreshed_func is not None:
                                        st.session_state.docstring_selected_func = refreshed_func
                                    else:
                                        fallback_doc = new_doc.strip()
                                        if fallback_doc.startswith('"""') and fallback_doc.endswith('"""'):
                                            fallback_doc = fallback_doc[3:-3].strip("\n")
                                        elif fallback_doc.startswith("'''") and fallback_doc.endswith("'''"):
                                            fallback_doc = fallback_doc[3:-3].strip("\n")
                                        st.session_state.docstring_selected_func = {
                                            **func,
                                            "docstring": fallback_doc,
                                        }

                                    st.session_state["docstring_apply_result"] = {
                                        "type": "success",
                                        "message": f"✅ Applied docstring for {func['name']} (line {func['line']})."
                                    }
                                else:
                                    st.session_state["docstring_apply_result"] = {
                                        "type": "warning",
                                        "message": f"⚠️ Could not apply docstring for {func['name']} at line {func['line']}."
                                    }
                                st.rerun()
                        with btn_col2:
                            if st.button("❌ Reject", use_container_width=True, key=reject_key):
                                st.session_state.docstring_selected_func = None
                                st.rerun()
                                
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("Diff")
                    import difflib
                    
                    before_lines = before_text_diff.splitlines(keepends=True) if before_text_diff else []
                    new_doc_lines = (new_doc + "\\n").splitlines(keepends=True)
                    
                    diff = list(difflib.ndiff(before_lines, new_doc_lines))
                    
                    if not diff or all(l.startswith('  ') for l in diff):
                        diff_display = "<span style='color: #94a3b8;'>No changes.</span>"
                    else:
                        formatted_diff = []
                        for line in diff:
                            raw_line = line
                            line_safe = line.replace("<", "&lt;").replace(">", "&gt;")
                            if raw_line.startswith("+ "):
                                formatted_diff.append(f"<span style='color: #10b981; background: rgba(16, 185, 129, 0.1);'>{line_safe}</span>")
                            elif raw_line.startswith("- "):
                                formatted_diff.append(f"<span style='color: #ef4444; background: rgba(239, 68, 68, 0.1);'>{line_safe}</span>")
                            elif raw_line.startswith("? "):
                                formatted_diff.append(f"<span style='color: #fbbf24; opacity: 0.8;'>{line_safe}</span>")
                            else:
                                formatted_diff.append(f"<span style='color: #94a3b8;'>{line_safe}</span>")
                        diff_display = "".join(formatted_diff)
                        
                    st.markdown(f'''<div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); font-size: 0.9em;">
<pre style="margin: 0; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace !important;">{diff_display}</pre>
</div>''', unsafe_allow_html=True)
        else:
            show_empty_state()


