"""Main_app.py module."""

import streamlit as st
import json
import os
import glob
from doc_steward import analyze_file, get_entity_list, get_maintainability_index, get_function_complexity

st.set_page_config(page_title="AI Code Reviewer", page_icon="🧠", layout="wide")

def main():
    """Main function for AI Code Reviewer."""
    st.sidebar.title("🧠 AI Code Reviewer")
    view = st.sidebar.selectbox("Select View", ["Docstring Coverage", "Metrics"])
    
    output_json = st.sidebar.text_input("Output JSON path", value="storage/review_logs.json")
    
    py_files_opts = [f for f in os.listdir(".") if f.endswith('.py')]
        
    if "sample_a.py" not in py_files_opts and os.path.exists("sample_a.py"):
        py_files_opts.append("sample_a.py")
        
    selected_file = st.sidebar.selectbox("Select File", options=sorted(list(set(py_files_opts))))
    
    if selected_file:
        file_to_scan = selected_file
    else:
        file_to_scan = None

    if view == "Docstring Coverage":
        st.header("📘 Docstring Coverage")
        
        if st.button("Generate Coverage Report"):
            from doc_steward import generate_coverage_report
            if py_files_opts:
                with st.spinner("Generating..."):
                    report = generate_coverage_report([f for f in py_files_opts if os.path.exists(f)])
                    os.makedirs(os.path.dirname(output_json), exist_ok=True)
                    with open(output_json, "w") as f:
                        json.dump(report, f, indent=4)
                    st.success("Report Generated!")
            else:
                st.error("No files found.")
            
        if file_to_scan and os.path.exists(file_to_scan):
            try:
                entities = get_entity_list(file_to_scan)
            except SyntaxError:
                st.error("Syntax Error in the file! Cannot calculate coverage.")
                entities = []
            
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
            
            st.markdown("### Function-wise Docstring Status")
            
            formatted_entities = []
            for i, e in enumerate(func_entities):
                formatted_entities.append({
                    "Function Name": e["Function Name"],
                    "Type": e["Type"],
                    "Start Line": e["Start Line"],
                    "End Line": e["End Line"],
                    "Has Docstring": "true" if e["Has Docstring"] else "false"
                })
                
            st.dataframe(formatted_entities, use_container_width=True)
            
            if total_funcs > documented:
                if st.button(f"Apply Missing Docstrings"):
                    from doc_steward import apply_missing_docstrings
                    apply_missing_docstrings(file_to_scan)
                    st.success("Applied! Reloading...")

    elif view == "Metrics":
        if file_to_scan and os.path.exists(file_to_scan):
            mi = get_maintainability_index(file_to_scan)
            
            st.markdown("<p style='font-size: 14px; color: gray; margin-bottom: 0;'>Maintainability Index</p>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='margin-top: 0;'>{round(mi, 2)}</h1>", unsafe_allow_html=True)
            
            st.subheader("Function Complexity")
            
            complexity_list = get_function_complexity(file_to_scan)
            st.json(complexity_list)
            
            # Save complexity report to JSON as well
            os.makedirs(os.path.dirname(output_json), exist_ok=True)
            with open(output_json, "w") as f:
                json.dump({"Maintainability Index": round(mi, 2), "Function Complexity": complexity_list}, f, indent=4)
        else:
            st.error("No file to scan.")

if __name__ == "__main__":
    main()
