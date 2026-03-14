import streamlit as st

def apply_global_ui_style():
    """Apply consistent UI styling across all pages."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
            
            /* Apply custom font */
            html, body, [class*="css"] {
                font-family: 'Outfit', sans-serif !important;
            }
            
            /* Overall Background */
            .stApp {
                background: #0f172a !important;
                background-image: 
                    radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                    radial-gradient(at 50% 0%, hsla(225,39%,30%,0.1) 0, transparent 50%), 
                    radial-gradient(at 100% 0%, hsla(339,49%,30%,0.1) 0, transparent 50%);
            }
            
            /* Adjust main container spacing */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1300px;
            }
            
            /* Sidebar Styling */
            [data-testid="stSidebar"] {
                background-color: rgba(15, 23, 42, 0.8) !important;
                backdrop-filter: blur(12px);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }
            [data-testid="stSidebar"] * {
                color: #e2e8f0;
            }
            
            /* Title and Headings */
            h1, h2, h3 {
                color: #f8fafc !important;
                font-weight: 700 !important;
                letter-spacing: -0.02em;
            }
            
            /* Gradient for main markdown headers that act as titles */
            .stMarkdown h3 {
                background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: inline-block;
                margin-top: -0.5rem;
            }
            
            /* Premium Button Styles */
            .stButton > button {
                border-radius: 10px;
                font-weight: 600;
                background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
                color: white !important;
                border: none;
                padding: 0.6rem 1.2rem;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25);
                font-family: 'Outfit', sans-serif;
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
                background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
            }
            .stButton > button:active {
                transform: translateY(0);
            }
            
            /* Download Button Variation */
            [data-testid="stDownloadButton"] > button {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25);
            }
            [data-testid="stDownloadButton"] > button:hover {
                box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
                background: linear-gradient(135deg, #059669 0%, #047857 100%);
            }
            
            /* Metric Cards (Glassmorphism) */
            div[data-testid="stMetric"] {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 1.2rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                transition: transform 0.3s ease, border-color 0.3s ease;
            }
            div[data-testid="stMetric"]:hover {
                transform: translateY(-4px);
                border-color: rgba(129, 140, 248, 0.5);
            }
            
            div[data-testid="stMetricLabel"] * {
                color: #94a3b8 !important;
                font-weight: 500;
                font-size: 0.95rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            div[data-testid="stMetricValue"] * {
                color: #f8fafc !important;
                font-weight: 700;
                font-size: 2.2rem;
                background: linear-gradient(to right, #ffffff, #cbd5e1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            /* Alerts and Info Boxes */
            [data-testid="stAlert"] {
                border-radius: 14px !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                padding: 1.2rem !important;
                background: rgba(30, 41, 59, 0.5) !important;
                backdrop-filter: blur(10px);
                color: #f8fafc !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
            }
            
            /* Custom Section Titles */
            .ui-section-title {
                font-family: 'Outfit', sans-serif !important;
                font-weight: 600;
                font-size: 1.3rem;
                margin: 2rem 0 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                color: #f8fafc;
                display: flex;
                align-items: center;
                gap: 0.6rem;
            }
            
            /* Dataframes / Tables Styling */
            [data-testid="stDataFrame"] {
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
            }
            
            /* Selectboxes and Inputs */
            .stSelectbox > div > div {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: #f8fafc;
                transition: border-color 0.2s;
            }
            .stSelectbox > div > div:hover, .stSelectbox > div > div:focus-within {
                border-color: rgba(129, 140, 248, 0.6);
            }
            
            .stTextInput > div > div > input {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: #f8fafc;
                transition: border-color 0.2s;
            }
            .stTextInput > div > div > input:focus {
                border-color: rgba(129, 140, 248, 0.6);
                box-shadow: 0 0 0 1px rgba(129, 140, 248, 0.6);
            }
            
            /* Radio buttons / Checkboxes inside Sidebar & Modals */
            .stRadio > div {
                background-color: rgba(30, 41, 59, 0.4);
                border-radius: 12px;
                padding: 0.8rem;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
            
            /* Expander Styling */
            [data-testid="stExpander"] {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                overflow: hidden;
            }
            
            /* Streamlit Tabs */
            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                background-color: rgba(30, 41, 59, 0.3);
                border-radius: 12px;
                padding: 0.3rem;
                gap: 0.3rem;
            }
            [data-testid="stTabs"] [data-baseweb="tab"] {
                border-radius: 8px;
                padding: 0.5rem 1rem;
                color: #94a3b8;
            }
            [data-testid="stTabs"] [aria-selected="true"] {
                background-color: rgba(255, 255, 255, 0.1);
                color: #f8fafc !important;
            }
            
            /* Custom Scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            ::-webkit-scrollbar-track {
                background: #0f172a;
            }
            ::-webkit-scrollbar-thumb {
                background: #334155;
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #475569;
            }
            
            /* File Uploader Custom Styling (Pink Theme) */
            [data-testid="stFileUploaderDropzone"] {
                background: linear-gradient(135deg, rgba(236, 72, 153, 0.05) 0%, rgba(219, 39, 119, 0.1) 100%) !important;
                border: 2px dashed rgba(236, 72, 153, 0.4) !important;
                border-radius: 16px !important;
                padding: 2rem !important;
                transition: all 0.3s ease !important;
            }
            [data-testid="stFileUploaderDropzone"]:hover {
                background: linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(219, 39, 119, 0.2) 100%) !important;
                border-color: rgba(236, 72, 153, 0.8) !important;
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(236, 72, 153, 0.15);
            }
            /* File Uploader 'Browse Files' Button */
            [data-testid="stFileUploaderDropzone"] button {
                background: linear-gradient(135deg, #ec4899 0%, #db2777 100%) !important;
                border: none !important;
                color: white !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                padding: 0.5rem 1rem !important;
                box-shadow: 0 4px 15px rgba(236, 72, 153, 0.3) !important;
                transition: all 0.3s ease !important;
            }
            [data-testid="stFileUploaderDropzone"] button:hover {
                background: linear-gradient(135deg, #f472b6 0%, #be185d 100%) !important;
                box-shadow: 0 6px 20px rgba(236, 72, 153, 0.4) !important;
                transform: translateY(-1px);
            }
            
            /* File Uploader Uploaded Files List Item Icon */
            [data-testid="stFileUploaderDropzone"] svg {
                fill: #ec4899 !important;
                color: #ec4899 !important;
            }
            
            /* File Uploader Status Text */
            [data-testid="stFileUploaderDropzone"] small {
                color: #fbcfe8 !important;
                font-weight: 500 !important;
            }
            
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_empty_state():
    """Display a beautifully styled empty state instead of a notification bar."""
    st.markdown(
        """
        <div style='text-align: center; padding: 6rem 2rem; border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 24px; margin: 3rem 0; background: linear-gradient(180deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.4) 100%); backdrop-filter: blur(12px); box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2); transition: all 0.4s ease;'>
            <div style='font-size: 5rem; margin-bottom: 1.5rem; animation: float 3s ease-in-out infinite; text-shadow: 0 10px 20px rgba(0,0,0,0.2);'>📄</div>
            <h3 style='color: #f8fafc; margin-bottom: 1rem; font-weight: 700; font-size: 1.8rem; font-family: "Outfit", sans-serif;'>No Python Files Selected</h3>
            <p style='color: #94a3b8; font-size: 1.15rem; max-width: 450px; margin: 0 auto; line-height: 1.6;'>Browse your directory or upload files from the sidebar to dive into intelligent code reviews.</p>
        </div>
        <style>
            @keyframes float {
                0% { transform: translateY(0px); }
                50% { transform: translateY(-12px); }
                100% { transform: translateY(0px); }
            }
        </style>
        """,
        unsafe_allow_html=True
    )
