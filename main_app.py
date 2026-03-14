"""Main_app.py module."""

import streamlit as st
import os
import re
import importlib

# Import enhanced UI modules
from ui import enhanced_ui, dashboard
from ui.dashboard_metrics import calculate_aggregate_metrics as _calculate_aggregate_metrics
from ui.section_docstring import run_docstring_section
from ui.section_home import run_home_section
from ui.section_reports import run_report_section
from ui.section_validation import run_validation_section
from ui.ui import apply_global_ui_style as _apply_global_ui_style
from ui.ui import show_empty_state as _show_empty_state

from core import doc_steward
importlib.reload(doc_steward)

st.set_page_config(
    page_title="AI Code Reviewer - Advanced Analytics",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


def apply_global_ui_style():
    """Compatibility wrapper for shared UI styling."""
    _apply_global_ui_style()

def show_empty_state():
    """Compatibility wrapper for shared empty-state component."""
    _show_empty_state()


@st.cache_data(show_spinner=False)
def _list_workspace_python_files(root_dir: str):
    """Return absolute paths for Python files in the workspace."""
    py_files = []
    ignored_dirs = {".git", "__pycache__", ".venv", "venv"}

    for dir_path, dir_names, file_names in os.walk(root_dir):
        dir_names[:] = [d for d in dir_names if d not in ignored_dirs and not d.startswith(".")]
        for file_name in file_names:
            if file_name.endswith(".py"):
                py_files.append(os.path.abspath(os.path.join(dir_path, file_name)))

    return sorted(py_files, key=lambda p: p.lower())

# Initialize session state for tracking uploaded files
if "uploaded_file_paths" not in st.session_state:
    st.session_state.uploaded_file_paths = []
if "fixes_applied" not in st.session_state:
    st.session_state.fixes_applied = False

def calculate_aggregate_metrics(file_list):
    """Compatibility wrapper for shared aggregate metrics helper."""
    return _calculate_aggregate_metrics(file_list)


def _collect_callable_nodes(analysis: dict) -> list:
    """Return flat list of functions and methods from analyze_file output."""
    callables = list(analysis.get("functions", []))
    for cls in analysis.get("classes", []):
        callables.extend(cls.get("methods", []))
    return callables


def _get_docstring_issue(func_info: dict, style: str) -> str | None:
    """Return issue code for a callable docstring: missing/style/None."""
    doc = func_info.get("docstring")
    if not doc or not str(doc).strip():
        return "missing"

    normalized = str(doc)
    style_key = (style or "google").strip().lower()

    needs_args = bool(func_info.get("args"))
    needs_yields = bool(func_info.get("has_yield"))
    needs_returns = bool(func_info.get("has_return")) and not needs_yields
    needs_raises = bool(func_info.get("has_raises"))

    # Summary-only docstrings can be style-agnostic when no section is needed.
    if not any([needs_args, needs_yields, needs_returns, needs_raises]):
        return None

    def has_google_section(name: str) -> bool:
        return re.search(rf"(?m)^\s*{re.escape(name)}:\s*$", normalized) is not None

    def has_numpy_section(name: str) -> bool:
        return re.search(rf"(?ms)^\s*{re.escape(name)}\s*$\n\s*-{{3,}}\s*$", normalized) is not None

    if style_key == "google":
        if needs_args and not has_google_section("Args"):
            return "style"
        if needs_yields and not has_google_section("Yields"):
            return "style"
        if needs_returns and not has_google_section("Returns"):
            return "style"
        if needs_raises and not has_google_section("Raises"):
            return "style"
        return None

    if style_key == "numpy":
        if needs_args and not has_numpy_section("Parameters"):
            return "style"
        if needs_yields and not has_numpy_section("Yields"):
            return "style"
        if needs_returns and not has_numpy_section("Returns"):
            return "style"
        if needs_raises and not has_numpy_section("Raises"):
            return "style"
        return None

    # reST checks
    if needs_args and re.search(r"(?m):param\s+\w+\s*:", normalized) is None:
        return "style"
    if needs_yields and re.search(r"(?m):yields?\s*:", normalized) is None:
        return "style"
    if needs_returns and re.search(r"(?m):returns?\s*:", normalized) is None:
        return "style"
    if needs_raises and re.search(r"(?m):raises\s+", normalized) is None:
        return "style"
    return None

def main():
    """Main function for AI Code Reviewer."""
    # Apply enhanced UI theme
    enhanced_ui.apply_enhanced_theme()

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"
    elif st.session_state.current_page == "Coverage Report":
        # Migrate removed standalone page to Home.
        st.session_state.current_page = "Home"
    elif st.session_state.current_page == "Docstring Coverage":
        # Migrate removed standalone page to Validation.
        st.session_state.current_page = "Validation"
    elif st.session_state.current_page == "Analytics":
        # Migrate renamed page key.
        st.session_state.current_page = "Dashboard"
    elif st.session_state.current_page == "📊 Analytics":
        # Migrate old decorated label to renamed page key.
        st.session_state.current_page = "Dashboard"
    elif st.session_state.current_page == "Source Code":
        # Migrate removed page key to Function Details.
        st.session_state.current_page = "Function Details"

    st.sidebar.title("🧠 AI Code Reviewer")
    st.sidebar.caption("Smart code analysis with advanced analytics")

    page_icons = {
        "Home": "🏠",
        "Dashboard": "📊",
        "Docstring": "📝",
        "Function Details": "🔍",
        "JSON Output": "🧾",
        "Validation": "✅",
    }

    other_pages = [
        "Dashboard",
        "Docstring",
        "Function Details",
        "JSON Output",
        "Validation",
    ]
    pages = ["Home"] + sorted(other_pages, key=lambda page_name: page_name.lower())
    if st.session_state.current_page not in pages:
        st.session_state.current_page = "Home"

    view = st.sidebar.selectbox(
        "Page",
        pages,
        format_func=lambda value: f"{page_icons.get(value, '📌')} {value}",
        key="current_page"
    )

    if "docstring_style" not in st.session_state:
        st.session_state.docstring_style = "google"
    
    output_json = st.sidebar.text_input("Output JSON path", value="storage/review_logs.json")
    if view == "Docstring":
        docstring_style = st.session_state.docstring_style
        st.sidebar.caption("Docstring style can be changed on the Docstring page.")
    else:
        docstring_style = st.sidebar.selectbox(
            "Docstring Style",
            ["google", "numpy", "rest"],
            format_func=lambda value: value.upper(),
            key="docstring_style"
        )
    
    if view == "Home":
        st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>🚀 Home</h1>", unsafe_allow_html=True)
        st.markdown("<div class='ui-section-title'>📂 1. Select Files or Folder</div>", unsafe_allow_html=True)
        
        # Bigger styled container for file selection on Home
        file_container = st.container()
        
        st.markdown("<div class='ui-section-title'>🛠️ 2. Choose an Analysis Tool</div>", unsafe_allow_html=True)
        btn_container = st.container()
    else:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📂 File Selection")
        file_container = st.sidebar
        btn_container = None

    file_selection_method = "Workspace Files (real paths)"

    uploaded_file_paths = []
    use_uploaded_files = False
    
    uploaded_files = file_container.file_uploader(
        "Drag and drop Python files OR entire folders here",
        type=["py"],
        accept_multiple_files=True,
        key="uploaded_files_widget",
    )

    if uploaded_files:
        workspace_root = os.path.abspath(os.getcwd())
        workspace_files = _list_workspace_python_files(workspace_root)

        rel_lookup = {}
        base_lookup = {}
        for abs_path in workspace_files:
            rel_path = os.path.relpath(abs_path, workspace_root).replace("\\", "/").lower()
            rel_lookup[rel_path] = abs_path

            base_name = os.path.basename(abs_path).lower()
            base_lookup.setdefault(base_name, []).append(abs_path)

        unresolved_names = []
        ambiguous_names = []

        for uploaded_file in uploaded_files:
            raw_name = (uploaded_file.name or "").strip()
            if not raw_name:
                continue

            normalized_name = raw_name.replace("\\", "/").lstrip("./").lower()
            resolved_path = rel_lookup.get(normalized_name)

            if resolved_path is None:
                base_name = os.path.basename(normalized_name)
                matches = base_lookup.get(base_name, [])
                if len(matches) == 1:
                    resolved_path = matches[0]
                elif len(matches) > 1:
                    root_matches = [m for m in matches if os.path.dirname(m).lower() == workspace_root.lower()]
                    if len(root_matches) == 1:
                        resolved_path = root_matches[0]
                    else:
                        ambiguous_names.append(raw_name)
                        resolved_path = None

            if resolved_path and os.path.exists(resolved_path):
                uploaded_file_paths.append(os.path.abspath(resolved_path))
            else:
                unresolved_names.append(raw_name)

        uploaded_file_paths = list(dict.fromkeys(uploaded_file_paths))
        st.session_state.uploaded_file_paths = uploaded_file_paths

        if uploaded_file_paths:
            file_container.info(f"📂 {len(uploaded_file_paths)} workspace file(s) selected (no temp copy)")
        if unresolved_names:
            file_container.warning(
                "Could not map these uploaded names to files in current workspace: "
                + ", ".join(unresolved_names)
            )
        if ambiguous_names:
            file_container.warning(
                "Multiple files share these names in workspace. Select by unique path: "
                + ", ".join(ambiguous_names)
            )
    else:
        # Keep existing selection when no new upload is made, so navigation
        # between pages does not force users to select files again.
        uploaded_file_paths = list(st.session_state.get("uploaded_file_paths", []))

    if uploaded_file_paths:
        file_container.caption(f"Current selection: {len(uploaded_file_paths)} file(s)")
        if file_container.button("Clear selected files", key="clear_selected_files", use_container_width=True):
            uploaded_file_paths = []
            st.session_state.uploaded_file_paths = []
            st.rerun()

    # Get file to scan
    if uploaded_file_paths:
        file_list = uploaded_file_paths
        display_name = f"{len(uploaded_file_paths)} workspace file(s)"
    else:
        file_list = []
        display_name = None

    if view == "Dashboard":
        dashboard.show_analytics_dashboard()
        return

    files_to_display = file_list
    show_all_files = True

    run_home_section(view, btn_container, file_list, docstring_style, show_empty_state)
    if view == "Home":
        return

    if len(file_list) > 1:
        file_options = {"All selected files": None}
        for i, file_path in enumerate(file_list, start=1):
            file_options[f"{i}. {os.path.basename(file_path)}"] = file_path

        selected_scope = st.selectbox(
            "Select file report at top",
            options=list(file_options.keys()),
            index=1,
            key="selected_file_scope"
        )

        if file_options[selected_scope] is None:
            files_to_display = file_list
            show_all_files = True
        else:
            files_to_display = [file_options[selected_scope]]
            show_all_files = False

    st.markdown(f"### {'✅ Validation' if view == 'Validation' else '📊 ' + view}")
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("Selected Files", len(file_list))
    summary_col2.metric("View Scope", "All" if show_all_files else "Single")
    summary_col3.metric("Docstring Style", docstring_style.upper())
    summary_col4.metric("Selection Mode", file_selection_method)
    if display_name:
        st.caption(f"Working on: {display_name}")

    run_validation_section(
        view,
        file_list,
        files_to_display,
        show_all_files,
        docstring_style,
        output_json,
        use_uploaded_files,
        show_empty_state,
    )
    run_docstring_section(
        view,
        file_list,
        docstring_style,
        show_empty_state,
        _collect_callable_nodes,
        _get_docstring_issue,
    )
    run_report_section(
        view,
        file_list,
        files_to_display,
        show_all_files,
        output_json,
        show_empty_state,
    )

if __name__ == "__main__":
    main()
