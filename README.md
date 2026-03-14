# 🧠 AI-Powered Code Reviewer & Quality Assistant

> An intelligent Streamlit-based application that analyzes Python codebases for quality issues, generates AI-powered docstrings, validates documentation coverage, and delivers rich visual analytics — all in one unified dashboard.

---

## ✨ Features

- 🔍 **AST-Based Code Analysis** — Extracts functions, classes, methods, arguments, return types, and control-flow signals (raises, yields, returns) using Python's abstract syntax tree.
- 📝 **AI Docstring Generation** — Generates context-aware docstrings via Groq LLM (LangChain integration) in **Google**, **NumPy**, or **reST** styles, including `Args`, `Returns`, `Raises`, and `Yields` sections.
- ✅ **Docstring Validation** — Validates existing docstrings against the selected style guide and flags missing or incomplete documentation.
- 📊 **Coverage Reporting** — Computes per-file and aggregate docstring coverage with interactive pie charts and bar graphs.
- 🛠️ **Auto-Fix Engine** — Applies suggested docstrings directly back to the source file at the correct line position.
- 🔬 **pydocstyle Integration** — Runs `pydocstyle` checks on uploaded files and surfaces violations in the UI.
- 📈 **Analytics Dashboard** — Visualizes metrics across all analyzed files using Plotly-powered charts (complexity, coverage, issue trends).
- 🔢 **Code Metrics** — Calculates cyclomatic complexity, maintainability index, and other Radon-based metrics.
- 🧾 **JSON Report Export** — Persists review results to a structured JSON log for downstream tooling or CI use.
- 🧪 **Test Suite** — Comprehensive pytest coverage for the parser, generator, validator, coverage reporter, dashboard, and LLM modules.

---

## 🖥️ Pages & Navigation

| Page | Description |
|------|-------------|
| 🏠 **Home** | File upload, tool shortcuts, and project overview |
| 📊 **Dashboard** | Aggregate analytics and visual metrics across all files |
| 📝 **Docstring** | Per-function docstring generation, preview, and one-click apply |
| 🔍 **Function Details** | Deep-dive into individual functions, arguments, and metadata |
| ✅ **Validation** | Docstring coverage table, style validation, and pydocstyle results |
| 🧾 **JSON Output** | Raw structured review output viewer |

---

## 🗂️ Project Architecture

```
📦 AI-Powered-Code-Reviewer
│
├── main_app.py                  # Streamlit entry point
├── requirements.txt             # Python dependencies
├── .env                         # API keys (not committed)
│
├── core/                        # Core analysis engine
│   ├── ast_extractor.py         # AST-based code parser
│   ├── auto_fixer.py            # Applies docstring patches to source files
│   ├── doc_steward.py           # Orchestrates analysis pipeline
│   ├── metrics_calculator.py    # Complexity & maintainability metrics (Radon)
│   ├── pydocstyle_runner.py     # Runs pydocstyle and parses violations
│   ├── _test_compat.py          # Test compatibility helpers
│   │
│   ├── docstring_engine/        # LLM-powered docstring generation
│   │   ├── generator.py         # Prompt builder and section composer
│   │   └── llm_integration.py   # Groq LLM client (LangChain)
│   │
│   ├── parser/                  # Python source file parser
│   │   └── python_parser.py
│   │
│   ├── reporter/                # Coverage reporting
│   │   └── coverage_reporter.py
│   │
│   └── validator/               # Docstring style validator
│       └── validator.py
│
├── ui/                          # Streamlit UI components
│   ├── enhanced_ui.py           # Global theme and CSS injection
│   ├── ui.py                    # Shared UI primitives (empty state, styling)
│   ├── dashboard.py             # Analytics dashboard page
│   ├── dashboard_metrics.py     # Aggregate metric calculations
│   ├── section_home.py          # Home page section
│   ├── section_docstring.py     # Docstring generation & apply UI
│   ├── section_validation.py    # Validation results UI
│   └── section_reports.py      # JSON output & report UI
│
├── generator/                   # Standalone generator module
│   └── docstring_generator.py
│
├── dashboard_ui/                # Legacy dashboard module
│   └── dashboard.py
│
├── tests/                       # Pytest test suite
│   ├── test_parser.py
│   ├── test_generator.py
│   ├── test_validation.py
│   ├── test_coverage_reporter.py
│   ├── test_dashboard.py
│   └── test_llm_integration.py
│
├── storage/                     # Auto-generated output directory
│   └── review_logs.json         # Persisted analysis results
│
└── sample_a.py / sample_b.py   # Sample Python files for demo
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Krishna9422/AI-Powered-Code-Reviewer-and-Quality-Assistant.git
cd AI-Powered-Code-Reviewer-and-Quality-Assistant
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> 🔑 Get your free Groq API key at [console.groq.com](https://console.groq.com)

---

## 🚀 Running the App

```bash
streamlit run main_app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# With JSON report output
pytest --json-report --json-report-file=storage/reports/pytest_results.json

# Verbose mode
pytest -v
```

---

## 📋 Supported Docstring Styles

| Style | Description | Example Section |
|-------|-------------|-----------------|
| **Google** | Google-style with indented sections | `Args:`, `Returns:`, `Raises:` |
| **NumPy** | NumPy-style with underline separators | `Parameters\n----------` |
| **reST** | reStructuredText (Sphinx) style | `:param x:`, `:returns:`, `:raises:` |

---

## 🧠 How It Works

```
Upload Python Files
       │
       ▼
AST Extraction (core/ast_extractor.py)
       │  Parses functions, classes, args, returns, raises, yields
       ▼
Docstring Validation (core/validator/validator.py)
       │  Checks against selected style: Google / NumPy / reST
       ▼
AI Docstring Generation (core/docstring_engine/)
       │  Sends function signatures to Groq LLM via LangChain
       ▼
Coverage Reporting (core/reporter/coverage_reporter.py)
       │  Computes % coverage per file and in aggregate
       ▼
Metrics & Complexity (core/metrics_calculator.py)
       │  Cyclomatic complexity, maintainability index via Radon
       ▼
Auto-Fix Application (core/auto_fixer.py)
       │  Writes accepted docstrings back to original source files
       ▼
Streamlit UI Dashboard
       │  Visual charts, tables, and controls via Plotly + Streamlit
       ▼
JSON Output (storage/review_logs.json)
```

---

## 📦 Key Dependencies

| Library | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `langchain` + `langchain-groq` | LLM orchestration and Groq integration |
| `groq` | Groq API client |
| `pydocstyle` | Docstring style linting |
| `radon` | Code complexity metrics |
| `plotly` | Interactive charts and visualizations |
| `pandas` | Data manipulation for reports |
| `pytest` | Testing framework |
| `python-dotenv` | Environment variable management |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ using <strong>Streamlit</strong>, <strong>LangChain</strong>, and <strong>Groq</strong>
</p>
