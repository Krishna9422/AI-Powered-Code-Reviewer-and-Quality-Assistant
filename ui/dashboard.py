"""Dashboard module for visualizing code review analytics."""

import html
import json
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px


def _load_pytest_report() -> tuple[dict | None, Path | None]:
    """Load pytest JSON report from known workspace locations."""
    candidates = [
        Path("storage/reports/pytest_results.json"),
        Path("tests/storage/reports/pytest_results.json"),
    ]

    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            return json.loads(candidate.read_text(encoding="utf-8")), candidate
        except (OSError, json.JSONDecodeError):
            continue

    return None, None


def _build_test_dataframe(report: dict) -> pd.DataFrame:
    """Normalize pytest test records into a chart-friendly dataframe."""
    rows = []
    for idx, test_item in enumerate(report.get("tests", []), start=1):
        nodeid = str(test_item.get("nodeid", ""))
        if "::" in nodeid:
            module_name, test_name = nodeid.split("::", 1)
        else:
            module_name, test_name = nodeid, nodeid

        setup_duration = float((test_item.get("setup") or {}).get("duration", 0.0) or 0.0)
        call_duration = float((test_item.get("call") or {}).get("duration", 0.0) or 0.0)
        teardown_duration = float((test_item.get("teardown") or {}).get("duration", 0.0) or 0.0)
        total_duration = setup_duration + call_duration + teardown_duration

        rows.append(
            {
                "order": idx,
                "nodeid": nodeid,
                "module": module_name,
                "test": test_name,
                "outcome": str(test_item.get("outcome", "unknown")),
                "setup_duration": setup_duration,
                "call_duration": call_duration,
                "teardown_duration": teardown_duration,
                "total_duration": total_duration,
                "lineno": test_item.get("lineno"),
            }
        )

    return pd.DataFrame(rows)


def _outcome_color_map() -> dict[str, str]:
    return {
        "passed": "#10b981",
        "failed": "#ef4444",
        "error": "#f97316",
        "skipped": "#f59e0b",
        "xfailed": "#8b5cf6",
        "xpassed": "#06b6d4",
        "unknown": "#94a3b8",
    }


def _format_suite_name(module_name: str) -> str:
    """Format pytest module path into a dashboard-friendly suite title."""
    stem = Path(str(module_name)).stem
    if stem.startswith("test_"):
        stem = stem[5:]
    words = [word for word in stem.replace("-", "_").split("_") if word]
    if not words:
        return "General Tests"
    return f"{' '.join(word.capitalize() for word in words)} Tests"


def _render_suite_status_cards(tests_df: pd.DataFrame) -> None:
    """Render top-level suite pass/fail summary cards."""
    suite_df = (
        tests_df.groupby("module", as_index=False)
        .agg(
            total=("nodeid", "count"),
            passed=("outcome", lambda outcomes: int((outcomes == "passed").sum())),
        )
        .sort_values("module")
    )

    if suite_df.empty:
        return

    st.markdown(
        """
        <style>
        .suite-status-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 10px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.6rem;
            border-left: 5px solid #10b981;
            background: rgba(16, 185, 129, 0.22);
        }
        .suite-status-card.warn {
            border-left-color: #f59e0b;
            background: rgba(245, 158, 11, 0.2);
        }
        .suite-status-left {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            font-weight: 700;
            color: #e5e7eb;
        }
        .suite-status-right {
            font-weight: 700;
            color: #e5e7eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    for _, suite_row in suite_df.iterrows():
        total = int(suite_row["total"])
        passed = int(suite_row["passed"])
        all_passed = total > 0 and passed == total
        card_class = "suite-status-card" if all_passed else "suite-status-card warn"
        icon = "✅" if all_passed else "⚠️"
        suite_title = html.escape(_format_suite_name(str(suite_row["module"])))

        st.markdown(
            f"""
            <div class=\"{card_class}\">
                <div class=\"suite-status-left\">{icon} {suite_title}</div>
                <div class=\"suite-status-right\">{passed}/{total} passed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _filter_to_selected_files(rows_df: pd.DataFrame) -> pd.DataFrame:
    """Return rows that match files selected in the main app session."""
    selected_paths = st.session_state.get("uploaded_file_paths", [])
    if not selected_paths:
        return rows_df

    cwd = Path.cwd()
    selected_rel = set()
    selected_base = set()
    selected_abs = set()

    for path_str in selected_paths:
        try:
            path_obj = Path(path_str).resolve()
        except OSError:
            path_obj = Path(path_str)

        selected_base.add(path_obj.name.lower())
        selected_abs.add(str(path_obj).replace("\\", "/").lower())

        try:
            rel = path_obj.relative_to(cwd)
            selected_rel.add(str(rel).replace("\\", "/").lower())
        except ValueError:
            # Selected file outside cwd; keep absolute match only.
            pass

    module_norm = rows_df["module"].fillna("").astype(str).str.replace("\\", "/", regex=False).str.lower()
    mask = pd.Series(False, index=rows_df.index)

    for name in selected_base:
        mask |= (module_norm == name) | module_norm.str.endswith(f"/{name}")
    for rel in selected_rel:
        mask |= (module_norm == rel) | module_norm.str.endswith(f"/{rel}")
    for absolute in selected_abs:
        mask |= module_norm == absolute

    return rows_df[mask].copy()


def _build_docstring_status_df(file_paths: list[str]) -> pd.DataFrame:
    """Create per-function docstring status rows for selected Python files."""
    if not file_paths:
        return pd.DataFrame(columns=["file", "function", "line", "documented"])

    from core import doc_steward as core_doc_steward

    rows: list[dict[str, object]] = []
    for file_path in file_paths:
        path_obj = Path(file_path)
        if not path_obj.exists() or path_obj.suffix.lower() != ".py":
            continue

        try:
            analysis = core_doc_steward.analyze_file(str(path_obj))
        except SyntaxError:
            continue

        for fn in analysis.get("functions", []):
            rows.append(
                {
                    "file": path_obj.name,
                    "function": str(fn.get("name", "")),
                    "line": int(fn.get("line") or 0),
                    "documented": bool(fn.get("docstring")),
                }
            )

        for cls in analysis.get("classes", []):
            cls_name = str(cls.get("name", ""))
            for method in cls.get("methods", []):
                method_name = str(method.get("name", ""))
                display_name = f"{cls_name}.{method_name}" if cls_name else method_name
                rows.append(
                    {
                        "file": path_obj.name,
                        "function": display_name,
                        "line": int(method.get("line") or 0),
                        "documented": bool(method.get("docstring")),
                    }
                )

    return pd.DataFrame(rows)


def show_analytics_dashboard():
    """Display modern analytics dashboard using pytest results."""
    st.markdown("## 📊 Test Results Dashboard")

    report, report_path = _load_pytest_report()
    if not report:
        st.warning(
            "No pytest report found. Run pytest with JSON output first, for example: "
            "`pytest --json-report --json-report-file=storage/reports/pytest_results.json`."
        )
        return

    tests_df = _build_test_dataframe(report)
    summary = report.get("summary", {})
    total_tests = int(summary.get("total", len(tests_df)))
    passed_tests = int(summary.get("passed", 0))
    failed_tests = int(summary.get("failed", 0))
    total_duration = float(report.get("duration", tests_df["total_duration"].sum() if not tests_df.empty else 0.0))
    pass_rate = (passed_tests / total_tests * 100) if total_tests else 0.0
    slowest_test = tests_df.sort_values("call_duration", ascending=False).head(1)
    slowest_label = slowest_test.iloc[0]["test"] if not slowest_test.empty else "N/A"
    slowest_value = float(slowest_test.iloc[0]["call_duration"]) if not slowest_test.empty else 0.0

    created_raw = report.get("created")
    created_label = "Unknown"
    if isinstance(created_raw, (int, float)):
        created_label = datetime.fromtimestamp(created_raw).strftime("%Y-%m-%d %H:%M:%S")

    st.caption(
        f"Source: `{report_path}` | Generated: {created_label} | Root: `{report.get('root', '')}`"
    )

    metric_cols = st.columns(5)
    metric_cols[0].metric("✅ Passed", passed_tests)
    metric_cols[1].metric("❌ Failed", failed_tests)
    metric_cols[2].metric("🧪 Total Tests", total_tests)
    metric_cols[3].metric("🎯 Pass Rate", f"{pass_rate:.1f}%")
    metric_cols[4].metric("⏱️ Suite Duration", f"{total_duration:.2f}s")
    st.caption(f"Slowest test: `{slowest_label}` ({slowest_value:.3f}s call time)")

    if tests_df.empty:
        st.info("Report loaded, but there are no individual test entries to visualize.")
        return

    _render_suite_status_cards(tests_df)
    st.divider()

    st.markdown(
        """
        <style>
        .main .stButton > button {
            min-height: 64px;
            font-size: 1.08rem;
            font-weight: 700;
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.14);
        }
        .main .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.2);
        }
        .main .stDownloadButton > button {
            min-height: 60px;
            font-size: 1.08rem;
            font-weight: 700;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(239, 68, 68, 0.24);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Quick Actions")
    action_keys = {
        "filters": "dashboard_show_advanced_filters",
        "search": "dashboard_show_search",
        "export": "dashboard_show_export_controls",
        "help": "dashboard_show_help_tips",
    }
    for state_key in action_keys.values():
        if state_key not in st.session_state:
            st.session_state[state_key] = False

    def _toggle_exclusive_panel(panel_key: str) -> None:
        """Toggle one quick-action panel while closing all other panels."""
        target_state_key = action_keys[panel_key]
        is_currently_open = bool(st.session_state.get(target_state_key, False))

        for state_key in action_keys.values():
            st.session_state[state_key] = False

        st.session_state[target_state_key] = not is_currently_open

    action_cols = st.columns(4)
    if action_cols[0].button("🔎 Advanced Filters", key="dashboard_toggle_filters", use_container_width=True):
        _toggle_exclusive_panel("filters")
    if action_cols[1].button("🧭 Search", key="dashboard_toggle_search", use_container_width=True):
        _toggle_exclusive_panel("search")
    if action_cols[2].button("📤 Export", key="dashboard_toggle_export", use_container_width=True):
        _toggle_exclusive_panel("export")
    if action_cols[3].button("ℹ️ Help & Tips", key="dashboard_toggle_help", use_container_width=True):
        _toggle_exclusive_panel("help")

    chart_df = tests_df.copy()

    if st.session_state[action_keys["filters"]]:
        selected_paths = st.session_state.get("uploaded_file_paths", [])
        if selected_paths:
            chart_df = _filter_to_selected_files(chart_df)
            selected_names = sorted({Path(path).name for path in selected_paths})
            st.caption("Showing only selected files: " + ", ".join(selected_names))
        else:
            st.caption("No selected files found in current session. Showing all files from report.")

        st.markdown(
            """
            <style>
            .adv-filter-banner {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                border-radius: 12px;
                padding: 1.2rem 1rem;
                margin: 0.5rem 0 1rem 0;
                color: #eef2ff;
            }
            .adv-filter-title {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 0.3rem;
            }
            .adv-filter-subtitle {
                font-size: 0.95rem;
                opacity: 0.9;
            }
            .adv-kpi {
                background: linear-gradient(135deg, #5f79e0 0%, #6d65d8 100%);
                border-radius: 10px;
                padding: 0.9rem;
                text-align: center;
                color: #eef2ff;
                margin-bottom: 0.8rem;
            }
            .adv-kpi .value {
                font-size: 2rem;
                font-weight: 700;
                line-height: 1;
            }
            .adv-kpi .label {
                font-size: 0.9rem;
                opacity: 0.9;
                margin-top: 0.25rem;
            }
            .adv-table {
                width: 100%;
                border-collapse: collapse;
                overflow: hidden;
                border-radius: 10px;
                margin-top: 0.2rem;
                background: rgba(51, 65, 85, 0.25);
            }
            .adv-table thead th {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: #eef2ff;
                text-align: left;
                padding: 0.75rem;
                font-size: 0.95rem;
                letter-spacing: 0.02em;
            }
            .adv-table tbody td {
                padding: 0.7rem 0.75rem;
                border-bottom: 1px solid rgba(148, 163, 184, 0.2);
                color: #e2e8f0;
            }
            .adv-badge {
                display: inline-block;
                padding: 0.22rem 0.65rem;
                border-radius: 999px;
                background: #10b981;
                color: #ecfdf5;
                font-weight: 700;
                font-size: 0.85rem;
            }
            .adv-badge-no {
                background: #ef4444;
                color: #fef2f2;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="adv-filter-banner">
                <div class="adv-filter-title">🔎 Advanced Filters</div>
                <div class="adv-filter-subtitle">Filter dynamically by file, function, and documentation status</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        doc_status = st.selectbox(
            "📊 Documentation status",
            ["All", "Yes", "No"],
            key="dashboard_doc_status_filter",
        )

        function_df = _build_docstring_status_df(selected_paths)
        filtered_function_df = function_df.copy()
        if doc_status == "Yes":
            filtered_function_df = filtered_function_df[filtered_function_df["documented"] == True]
        elif doc_status == "No":
            filtered_function_df = filtered_function_df[filtered_function_df["documented"] == False]

        kpi_col1, kpi_col2 = st.columns(2)
        with kpi_col1:
            st.markdown(
                f"""
                <div class="adv-kpi">
                    <div class="value">{len(filtered_function_df)}</div>
                    <div class="label">Showing</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with kpi_col2:
            st.markdown(
                f"""
                <div class="adv-kpi" style="background: linear-gradient(135deg, #6d65d8 0%, #7c3aed 100%);">
                    <div class="value">{len(function_df)}</div>
                    <div class="label">Total</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        preview_df = filtered_function_df[["file", "function", "documented"]].head(150)

        row_html = []
        for _, row in preview_df.iterrows():
            is_yes = bool(row["documented"])
            badge_class = "adv-badge" if is_yes else "adv-badge adv-badge-no"
            badge_text = "✅ Yes" if is_yes else "❌ No"
            row_html.append(
                "<tr>"
                f"<td>{html.escape(str(row['file']))}</td>"
                f"<td>{html.escape(str(row['function']))}</td>"
                f"<td><span class=\"{badge_class}\">{badge_text}</span></td>"
                "</tr>"
            )

        if row_html:
            st.markdown(
                "<table class=\"adv-table\">"
                "<thead><tr><th>📁 FILE</th><th>⚙️ FUNCTION</th><th>✅ DOCSTRING</th></tr></thead>"
                f"<tbody>{''.join(row_html)}</tbody></table>",
                unsafe_allow_html=True,
            )
        else:
            st.info("No rows available for the selected documentation status.")

    if st.session_state[action_keys["search"]]:
        st.markdown("#### Search")
        selected_paths = st.session_state.get("uploaded_file_paths", [])

        if not selected_paths:
            st.info("Select one or more files first, then use Search.")
        else:
            function_df = _build_docstring_status_df(selected_paths)
            if function_df.empty:
                st.warning("No Python functions were found in the selected files.")
            else:
                file_options = ["All selected files"] + sorted(function_df["file"].dropna().astype(str).unique().tolist())
                selected_file = st.selectbox(
                    "File scope",
                    file_options,
                    key="dashboard_function_finder_file_scope",
                )

                filtered_functions = function_df.copy()
                if selected_file != "All selected files":
                    filtered_functions = filtered_functions[filtered_functions["file"] == selected_file]

                function_options = sorted(
                    filtered_functions["function"].dropna().astype(str).unique().tolist()
                )
                selected_function = st.selectbox(
                    "Function name (type to search)",
                    ["All functions"] + function_options,
                    key="dashboard_function_finder_selected_function",
                    help="Start typing, for example: find_max",
                )

                if selected_function != "All functions":
                    filtered_functions = filtered_functions[
                        filtered_functions["function"] == selected_function
                    ]

                st.caption(f"Found {len(filtered_functions)} function(s) in selected files.")
                display_df = filtered_functions.copy()
                display_df["line"] = pd.to_numeric(display_df["line"], errors="coerce").fillna(0).astype(int)
                display_df["documented"] = display_df["documented"].map({True: "Yes", False: "No"})
                st.dataframe(
                    display_df[["file", "function", "line", "documented"]],
                    use_container_width=True,
                    hide_index=True,
                )

    if st.session_state[action_keys["help"]]:
        st.markdown("#### Help & Tips")
        st.markdown(
            """
            <style>
            .help-hero {
                background: linear-gradient(90deg, #3ddc84 0%, #35d7c4 100%);
                border-radius: 10px;
                padding: 1.2rem 1.3rem;
                margin: 0.35rem 0 0.9rem 0;
                color: #f8fafc;
            }
            .help-hero-title {
                font-size: 2rem;
                font-weight: 700;
                line-height: 1.15;
                margin-bottom: 0.35rem;
            }
            .help-hero-subtitle {
                font-size: 0.98rem;
                opacity: 0.95;
            }
            .help-card {
                border-radius: 10px;
                padding: 1rem 1.1rem;
                margin: 0.3rem 0 0.8rem 0;
                min-height: 180px;
            }
            .help-card-title {
                font-size: 1.9rem;
                font-weight: 700;
                margin-bottom: 0.45rem;
            }
            .help-line {
                margin: 0.14rem 0;
                font-size: 0.98rem;
                color: #334155;
            }
            .help-card.metrics {
                background: #d4e6db;
                border-left: 4px solid #4ade80;
            }
            .help-card.status {
                background: #f4e9d4;
                border-left: 4px solid #f59e0b;
            }
            .help-card.results {
                background: #d8e8f5;
                border-left: 4px solid #60a5fa;
            }
            .help-card.styles {
                background: #e6d8ef;
                border-left: 4px solid #a855f7;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="help-hero">
                <div class="help-hero-title">ℹ️ Interactive Help &amp; Tips</div>
                <div class="help-hero-subtitle">Contextual help and quick reference guide</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        help_col1, help_col2 = st.columns(2)
        with help_col1:
            st.markdown(
                """
                <div class="help-card metrics">
                    <div class="help-card-title">📊 Coverage Metrics</div>
                    <div class="help-line">• Coverage % = (Documented / Total) × 100</div>
                    <div class="help-line">• Green badge (🟢): &gt;=90% coverage</div>
                    <div class="help-line">• Yellow badge (🟡): 70-89% coverage</div>
                    <div class="help-line">• Red badge (🔴): &lt;70% coverage</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="help-card results">
                    <div class="help-card-title">🧪 Test Results</div>
                    <div class="help-line">• Real-time test execution monitoring</div>
                    <div class="help-line">• Pass/fail ratio visualization</div>
                    <div class="help-line">• Per-file test breakdown</div>
                    <div class="help-line">• Integration with pytest reports</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with help_col2:
            st.markdown(
                """
                <div class="help-card status">
                    <div class="help-card-title">✅ Function Status</div>
                    <div class="help-line">• ✅ Green: Complete docstring present</div>
                    <div class="help-line">• ❌ Red: Missing or incomplete docstring</div>
                    <div class="help-line">• Auto-detection of docstring styles</div>
                    <div class="help-line">• Style-specific validation</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="help-card styles">
                    <div class="help-card-title">📄 Docstring Styles</div>
                    <div class="help-line">• Google: Args, Returns, Raises</div>
                    <div class="help-line">• NumPy: Parameters/Returns with dashes</div>
                    <div class="help-line">• reST: :param, :type, :return directives</div>
                    <div class="help-line">• Auto-style detection &amp; validation</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("📘 Advanced Usage Guide", expanded=False):
            st.markdown(
                "### 🚀 Getting Started\n"
                "1. **Scan Your Project**: Enter the path and click `Scan` in the sidebar.\n"
                "2. **Review Coverage**: Open dashboard cards to inspect documented vs missing functions.\n"
                "3. **Search Functions**: Use `Search` to find function names with file and line details.\n"
                "4. **Validate Quality**: Use filters to focus on undocumented or high-priority items.\n"
                "5. **Export Reports**: Download JSON for automation and CSV for review sheets.\n\n"
                "### 💡 Pro Tips\n"
                "- Use `Advanced Filters` to focus only on missing docstrings.\n"
                "- Type partial function names in `Search` for fast suggestions.\n"
                "- Re-run scans after edits to verify coverage improvements.\n"
                "- Use CSV exports during code reviews and sprint reporting.\n\n"
                "### ⌨️ Keyboard Shortcuts\n"
                "- `Ctrl + F`: Browser find in long tables.\n"
                "- `Enter`: Confirm selected search item quickly.\n"
                "- `Esc`: Close active dropdown/search suggestions."
            )

    if st.session_state[action_keys["export"]]:
        selected_paths = st.session_state.get("uploaded_file_paths", [])
        export_function_df = _build_docstring_status_df(selected_paths)
        total_functions = int(len(export_function_df))
        documented_functions = int(export_function_df["documented"].sum()) if total_functions else 0
        missing_docstrings = total_functions - documented_functions

        st.markdown(
            """
            <style>
            .export-hero {
                background: linear-gradient(90deg, #2ea0ea 0%, #19d3da 100%);
                border-radius: 10px;
                padding: 1.2rem 1.4rem;
                margin: 0.35rem 0 0.8rem 0;
                color: #f8fafc;
            }
            .export-hero-title {
                font-size: 2rem;
                font-weight: 700;
                line-height: 1.1;
                margin-bottom: 0.35rem;
            }
            .export-hero-subtitle {
                font-size: 0.98rem;
                opacity: 0.95;
            }
            .export-summary {
                background: rgba(186, 209, 228, 0.55);
                border-left: 4px solid #38bdf8;
                border-radius: 10px;
                padding: 1rem 1.1rem;
                margin: 0.5rem 0 0.9rem 0;
                color: #1e293b;
            }
            .export-summary-title {
                font-size: 1.55rem;
                font-weight: 700;
                margin-bottom: 0.4rem;
                color: #0f172a;
            }
            .export-bullet {
                font-size: 1rem;
                margin: 0.2rem 0;
                color: #334155;
            }
            .stDownloadButton > button {
                background: #ff4f4f;
                color: #ffffff;
                border: none;
                border-radius: 9px;
                font-weight: 700;
            }
            .stDownloadButton > button:hover {
                background: #ef4444;
                color: #ffffff;
                border: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="export-hero">
                <div class="export-hero-title">📤 Export Data</div>
                <div class="export-hero-subtitle">Download analysis results in JSON or CSV format</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="export-summary">
                <div class="export-summary-title">📊 Export Summary</div>
                <div class="export-bullet">• Total Functions: {total_functions}</div>
                <div class="export-bullet">• Documented: {documented_functions}</div>
                <div class="export-bullet">• Missing Docstrings: {missing_docstrings}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        export_col1, export_col2 = st.columns(2)
        with export_col1:
            st.download_button(
                label="📥 Export as JSON",
                data=json.dumps(report, indent=2).encode("utf-8"),
                file_name="pytest_results.json",
                mime="application/json",
                use_container_width=True,
                key="dashboard_export_json",
            )
            st.caption("💡 JSON format for programmatic access")
        with export_col2:
            st.download_button(
                label="📥 Export as CSV",
                data=chart_df.to_csv(index=False).encode("utf-8"),
                file_name="test_dashboard_data.csv",
                mime="text/csv",
                use_container_width=True,
                key="dashboard_export_csv",
            )
            st.caption("💡 CSV format for Excel/spreadsheets")

    if chart_df.empty:
        st.warning(
            "No tests match the current filters. Test charts are hidden, but function search results above still work."
        )
        return

    st.divider()

    color_map = _outcome_color_map()
    tabs = st.tabs(["📈 Outcomes", "⚡ Performance", "🧩 Modules", "🕒 Timeline", "📋 Raw Data"])

    with tabs[0]:
        left, right = st.columns(2)

        with left:
            outcome_df = (
                chart_df.groupby("outcome", as_index=False)
                .size()
                .rename(columns={"size": "count"})
                .sort_values("count", ascending=False)
            )
            fig = px.pie(
                outcome_df,
                names="outcome",
                values="count",
                hole=0.58,
                title="Test Outcome Distribution",
                color="outcome",
                color_discrete_map=color_map,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Outfit, sans-serif", color="#e2e8f0"))
            st.plotly_chart(fig, use_container_width=True)

        with right:
            module_outcome_df = (
                chart_df.groupby(["module", "outcome"], as_index=False)
                .size()
                .rename(columns={"size": "count"})
            )
            fig = px.bar(
                module_outcome_df,
                x="module",
                y="count",
                color="outcome",
                barmode="stack",
                title="Outcome Split by Module",
                color_discrete_map=color_map,
            )
            fig.update_layout(
                xaxis_title=None,
                yaxis_title="Tests",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.03)",
                font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        left, right = st.columns(2)

        with left:
            top_n = chart_df.nlargest(12, "call_duration").sort_values("call_duration", ascending=True)
            fig = px.bar(
                top_n,
                x="call_duration",
                y="test",
                color="outcome",
                orientation="h",
                title="Top 12 Slowest Tests (Call Duration)",
                color_discrete_map=color_map,
            )
            fig.update_layout(
                xaxis_title="Seconds",
                yaxis_title=None,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.03)",
                font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            scatter_df = chart_df.copy()
            scatter_df["duration_ms"] = scatter_df["call_duration"] * 1000
            fig = px.scatter(
                scatter_df,
                x="setup_duration",
                y="call_duration",
                size="total_duration",
                color="outcome",
                hover_name="test",
                hover_data=["module", "teardown_duration"],
                title="Setup vs Call Time",
                color_discrete_map=color_map,
            )
            fig.update_layout(
                xaxis_title="Setup (s)",
                yaxis_title="Call (s)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.03)",
                font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        left, right = st.columns(2)
        module_df = (
            chart_df.groupby("module", as_index=False)
            .agg(
                tests=("nodeid", "count"),
                passed=("outcome", lambda s: int((s == "passed").sum())),
                failed=("outcome", lambda s: int((s == "failed").sum())),
                avg_call=("call_duration", "mean"),
                total_call=("call_duration", "sum"),
            )
            .sort_values("tests", ascending=False)
        )
        module_df["pass_rate"] = (module_df["passed"] / module_df["tests"] * 100).round(1)

        with left:
            fig = px.treemap(
                module_df,
                path=["module"],
                values="tests",
                color="pass_rate",
                color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
                title="Module Health Treemap (Size=Tests, Color=Pass Rate)",
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Outfit, sans-serif", color="#e2e8f0"))
            st.plotly_chart(fig, use_container_width=True)

        with right:
            fig = px.bar(
                module_df.sort_values("pass_rate", ascending=True),
                x="pass_rate",
                y="module",
                color="avg_call",
                orientation="h",
                title="Pass Rate by Module",
                color_continuous_scale="Tealgrn",
            )
            fig.update_layout(
                xaxis_title="Pass Rate (%)",
                yaxis_title=None,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.03)",
                font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        left, right = st.columns(2)

        with left:
            timeline_df = tests_df.sort_values("order").copy()
            timeline_df["cumulative_duration"] = timeline_df["total_duration"].cumsum()
            fig = px.area(
                timeline_df,
                x="order",
                y="cumulative_duration",
                title="Cumulative Suite Runtime",
            )
            fig.update_layout(
                xaxis_title="Execution Order",
                yaxis_title="Seconds",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.03)",
                font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            top_modules = chart_df["module"].value_counts().head(8).index.tolist()
            box_df = chart_df[chart_df["module"].isin(top_modules)]
            fig = px.box(
                box_df,
                x="module",
                y="call_duration",
                color="outcome",
                title="Duration Spread (Top Modules)",
                color_discrete_map=color_map,
            )
            fig.update_layout(
                xaxis_title=None,
                yaxis_title="Call Duration (s)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.03)",
                font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        display_df = chart_df[[
            "nodeid",
            "module",
            "test",
            "outcome",
            "setup_duration",
            "call_duration",
            "teardown_duration",
            "total_duration",
            "lineno",
        ]].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.download_button(
            label="⬇️ Download Processed Test Data (CSV)",
            data=display_df.to_csv(index=False).encode("utf-8"),
            file_name="test_dashboard_data.csv",
            mime="text/csv",
            use_container_width=True,
        )


def show_overview_tab(data):
    """Display overview metrics and statistics."""
    st.markdown("### Key Metrics Overview")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🔎 Total Files Analyzed",
            data["total_files"],
            f"+{data['files_today']} today",
            delta_color="off"
        )
    
    with col2:
        st.metric(
            "⚠️ Issues Found",
            data["total_issues"],
            f"-{data['issues_resolved']} resolved",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "📝 Avg Coverage",
            f"{data['avg_coverage']}%",
            f"+{data['coverage_gain']}%",
            delta_color="off"
        )
    
    with col4:
        st.metric(
            "⭐ Quality Score",
            f"{data['quality_score']}/100",
            f"+{data['score_change']} points",
            delta_color="off"
        )
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            data['issues_by_type'],
            x='type',
            y='count',
            title='Issues by Type',
            color_discrete_sequence=['#6366f1'],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0.02)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(
            data['severity_dist'],
            names='severity',
            values='count',
            title='Issues by Severity',
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)


def show_quality_tab(data):
    """Display code quality metrics."""
    st.markdown("### Code Quality Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🏆 Maintainability Index", "78/100", "+5 points")
    
    with col2:
        st.metric("🔄 Cyclomatic Complexity", "3.2", "-0.3")
    
    with col3:
        st.metric("📊 Code Coverage", "85%", "+8%")
    
    st.divider()
    
    # Quality trends
    col1, col2 = st.columns(2)
    
    with col1:
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'score': np.random.randint(70, 95, 30),
        })
        fig = px.line(df, x='date', y='score', title='Quality Score Trend')
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0.02)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        df = pd.DataFrame({
            'category': ['Complexity', 'Duplication', 'Comments', 'Coverage', 'Style'],
            'score': [85, 72, 90, 78, 88],
        })
        # Plotly Express has no `radar`; build a radar chart with Scatterpolar.
        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=df['score'],
                theta=df['category'],
                fill='toself',
                name='Quality',
                line=dict(color='#60a5fa', width=2),
            )
        )
        fig.update_layout(
            title='Quality Radar',
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.15)'),
                angularaxis=dict(gridcolor='rgba(255,255,255,0.15)'),
                bgcolor='rgba(0,0,0,0)',
            ),
        )
        st.plotly_chart(fig, use_container_width=True)


def show_file_analysis_tab(data):
    """Display file analysis visualizations."""
    st.markdown("### File Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            data['files_by_size'],
            x='name',
            y='lines',
            title='Files by Size',
            color='issues',
            color_continuous_scale='Reds',
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0.02)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(
            data['complexity_vs_coverage'],
            x='complexity',
            y='coverage',
            size='lines',
            color='issues',
            title='Complexity vs Coverage',
            color_continuous_scale='Viridis',
            hover_data=['filename'],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0.02)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)


def show_trends_tab(data):
    """Display trend analysis."""
    st.markdown("### Trend Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'issues': np.random.randint(5, 25, 30),
        })
        fig = px.area(df, x='date', y='issues', title='Issues Over Time')
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0.02)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'resolved': np.random.randint(2, 12, 30),
            'new': np.random.randint(3, 15, 30),
        })
        fig = go.Figure(
            data=[
                go.Scatter(x=df['date'], y=df['new'], name='New Issues'),
                go.Scatter(x=df['date'], y=df['resolved'], name='Resolved'),
            ]
        )
        fig.update_layout(
            title='New vs Resolved Issues',
            plot_bgcolor="rgba(0,0,0,0.02)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)


def show_performance_tab():
    """Display performance metrics."""
    st.markdown("### Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("⚡ Avg Analysis Time", "2.3s", "-0.5s")
    
    with col2:
        st.metric("🎯 Detection Rate", "94%", "+3%")
    
    with col3:
        st.metric("✅ False Positives", "2.1%", "-0.5%")
    
    st.divider()
    
    # Performance visualization
    categories = ['Speed', 'Accuracy', 'Coverage', 'Reliability', 'Scalability']
    values = [85, 92, 78, 88, 80]
    
    fig = go.Figure(
        data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Performance'
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="rgba(148, 163, 184, 0.1)",
            ),
            bgcolor="rgba(30, 41, 59, 0.1)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        title='Performance Spider Chart',
    )
    
    st.plotly_chart(fig, use_container_width=True)


def generate_overview_data():
    """Generate sample overview data."""
    return {
        'total_files': 156,
        'files_today': 12,
        'total_issues': 45,
        'issues_resolved': 8,
        'avg_coverage': 85,
        'coverage_gain': 5,
        'quality_score': 82,
        'score_change': 3,
        'issues_by_type': pd.DataFrame({
            'type': ['Style', 'Logic', 'Security', 'Performance', 'Documentation'],
            'count': [15, 12, 8, 6, 4],
        }),
        'severity_dist': pd.DataFrame({
            'severity': ['Critical', 'High', 'Medium', 'Low'],
            'count': [3, 8, 18, 16],
        }),
    }


def generate_file_data():
    """Generate sample file data."""
    files = ['main.py', 'utils.py', 'config.py', 'handler.py', 'models.py']
    return {
        'files_by_size': pd.DataFrame({
            'name': files,
            'lines': [450, 320, 180, 650, 420],
            'issues': [5, 3, 2, 8, 4],
        }),
        'complexity_vs_coverage': pd.DataFrame({
            'filename': files,
            'complexity': [3.2, 2.1, 1.5, 4.8, 2.9],
            'coverage': [85, 92, 78, 65, 88],
            'lines': [450, 320, 180, 650, 420],
            'issues': [5, 3, 2, 8, 4],
        }),
    }


def generate_trend_data():
    """Generate sample trend data."""
    return pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=30),
        'issues': np.random.randint(10, 30, 30),
        'resolved': np.random.randint(5, 15, 30),
    })


def generate_quality_data():
    """Generate sample quality data."""
    return pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=30),
        'score': np.random.randint(75, 95, 30),
        'complexity': np.random.randint(1, 8, 30),
    })


def show_comparison_charts():
    """Show comparison metrics."""
    st.markdown("### 📊 Detailed Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        df = pd.DataFrame({
            'Module': ['Auth', 'Database', 'API', 'Utils', 'Config'],
            'Complexity': [3.2, 2.8, 4.1, 1.9, 1.2],
            'Coverage': [85, 78, 92, 88, 95],
        })
        
        fig = go.Figure(
            data=[
                go.Bar(name='Complexity', x=df['Module'], y=df['Complexity']),
                go.Bar(name='Coverage', x=df['Module'], y=df['Coverage']),
            ]
        )
        fig.update_layout(
            barmode='group',
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0.02)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        df = pd.DataFrame({
            'Language': ['Python', 'JavaScript', 'TypeScript', 'Go'],
            'Files': [45, 32, 28, 15],
            'Issues': [8, 12, 5, 3],
        })
        
        fig = px.scatter(
            df,
            x='Files',
            y='Issues',
            size='Issues',
            hover_name='Language',
            title='Files vs Issues by Language',
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0.02)",
            font=dict(family="Outfit, sans-serif", color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
