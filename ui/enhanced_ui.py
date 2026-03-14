"""Enhanced UI module with advanced visualizations and dashboard components."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def apply_enhanced_theme():
    """Apply modern enhanced UI theme with glassmorphism."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
            
            /* Global Font */
            html, body, [class*="css"] {
                font-family: 'Outfit', sans-serif !important;
            }
            
            /* Premium Dark Background */
            .stApp {
                background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 50%, #0f172a 100%);
                background-attachment: fixed;
                background-image: 
                    radial-gradient(at 20% 50%, hsla(250,16%,7%,1) 0, transparent 50%), 
                    radial-gradient(at 80% 80%, hsla(280,39%,30%,0.1) 0, transparent 50%), 
                    radial-gradient(at 50% 50%, hsla(210,35%,25%,0.1) 0, transparent 60%);
            }
            
            /* Main Container */
            .main .block-container {
                padding-top: 2.5rem;
                padding-bottom: 3rem;
                max-width: 1400px;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(20, 30, 50, 0.8) 100%) !important;
                backdrop-filter: blur(20px);
                border-right: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 2px 0 20px rgba(0, 0, 0, 0.3);
            }
            [data-testid="stSidebar"] * {
                color: #e2e8f0;
            }
            
            /* Headers and Titles */
            h1, h2, h3, h4, h5 {
                color: #f8fafc !important;
                font-weight: 700 !important;
                letter-spacing: -0.01em !important;
            }
            
            h1 {
                font-size: 2.8rem !important;
                background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #ec4899 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 2rem !important;
            }
            
            h2 {
                font-size: 2rem !important;
                margin-top: 2.5rem !important;
                margin-bottom: 1.5rem !important;
                border-bottom: 2px solid rgba(129, 140, 248, 0.3);
                padding-bottom: 0.8rem;
            }
            
            h3 {
                font-size: 1.4rem !important;
                color: #e2e8f0 !important;
                margin-top: 1.5rem !important;
                margin-bottom: 1rem !important;
            }
            
            /* Premium Button Styles */
            .stButton > button {
                border-radius: 12px;
                font-weight: 600;
                font-size: 0.95rem;
                background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
                color: white !important;
                border: 1px solid rgba(168, 85, 247, 0.5);
                padding: 0.75rem 1.5rem;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
                font-family: 'Outfit', sans-serif;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .stButton > button:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.3);
                background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
            }
            .stButton > button:active {
                transform: translateY(-1px);
            }
            
            /* Download Button */
            [data-testid="stDownloadButton"] > button {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                border: 1px solid rgba(16, 185, 129, 0.5);
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            }
            [data-testid="stDownloadButton"] > button:hover {
                box-shadow: 0 8px 30px rgba(16, 185, 129, 0.5);
                background: linear-gradient(135deg, #059669 0%, #047857 100%);
            }
            
            /* Metric Cards with Glassmorphism */
            div[data-testid="stMetric"] {
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            }
            div[data-testid="stMetric"]:hover {
                transform: translateY(-6px);
                border-color: rgba(129, 140, 248, 0.6);
                box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15);
                background: rgba(30, 41, 59, 0.7);
            }
            
            div[data-testid="stMetricLabel"] * {
                color: #94a3b8 !important;
                font-weight: 600;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }
            
            div[data-testid="stMetricValue"] * {
                color: #f8fafc !important;
                font-weight: 800;
                font-size: 2.4rem;
                background: linear-gradient(135deg, #fbbf24 0%, #f97316 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-family: 'Space Mono', monospace;
            }
            
            /* Cards/Containers */
            .dashboard-card {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                backdrop-filter: blur(12px);
                transition: all 0.3s ease;
            }
            .dashboard-card:hover {
                border-color: rgba(129, 140, 248, 0.4);
                box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
                transform: translateY(-2px);
            }
            
            /* Alerts */
            [data-testid="stAlert"] {
                border-radius: 14px !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                padding: 1.5rem !important;
                background: rgba(30, 41, 59, 0.6) !important;
                backdrop-filter: blur(12px);
                color: #f8fafc !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
            }
            
            /* Tabs */
            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                background-color: rgba(30, 41, 59, 0.4);
                border-radius: 14px;
                padding: 0.4rem;
                gap: 0.4rem;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            [data-testid="stTabs"] [data-baseweb="tab"] {
                border-radius: 10px;
                padding: 0.7rem 1.3rem;
                color: #94a3b8;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            [data-testid="stTabs"] [aria-selected="true"] {
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(168, 85, 247, 0.2) 100%);
                color: #f8fafc !important;
                border: 1px solid rgba(129, 140, 248, 0.4);
            }
            
            /* Expandable Sections */
            [data-testid="stExpander"] {
                background-color: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                overflow: hidden;
            }
            
            /* Tables/Dataframes */
            [data-testid="stDataFrame"] {
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
            }
            
            /* Input Elements */
            .stSelectbox > div > div, .stTextInput > div > div > input {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: #f8fafc;
                transition: all 0.2s;
            }
            .stSelectbox > div > div:hover, .stTextInput > div > div > input:hover {
                border-color: rgba(129, 140, 248, 0.4);
            }
            .stSelectbox > div > div:focus-within, .stTextInput > div > div > input:focus {
                border-color: rgba(129, 140, 248, 0.8);
                box-shadow: 0 0 0 2px rgba(129, 140, 248, 0.2);
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            ::-webkit-scrollbar-track {
                background: #0f172a;
            }
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(180deg, #6366f1 0%, #a855f7 100%);
                border-radius: 5px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #a855f7;
            }
            
            /* File Uploader */
            [data-testid="stFileUploaderDropzone"] {
                background: linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(168, 85, 247, 0.05) 100%) !important;
                border: 2px dashed rgba(236, 72, 153, 0.5) !important;
                border-radius: 16px !important;
                padding: 2.5rem !important;
                transition: all 0.3s ease !important;
            }
            [data-testid="stFileUploaderDropzone"]:hover {
                background: linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(168, 85, 247, 0.1) 100%) !important;
                border-color: rgba(236, 72, 153, 0.8) !important;
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(236, 72, 153, 0.15);
            }
            [data-testid="stFileUploaderDropzone"] button {
                background: linear-gradient(135deg, #ec4899 0%, #db2777 100%) !important;
                border: none !important;
                color: white !important;
                border-radius: 8px !important;
                font-weight: 700 !important;
                padding: 0.6rem 1.2rem !important;
                box-shadow: 0 4px 15px rgba(236, 72, 153, 0.3) !important;
                transition: all 0.3s ease !important;
            }
            [data-testid="stFileUploaderDropzone"] button:hover {
                background: linear-gradient(135deg, #f472b6 0%, #be185d 100%) !important;
                box-shadow: 0 6px 20px rgba(236, 72, 153, 0.4) !important;
                transform: translateY(-1px);
            }
            
            /* Plotly Charts */
            .plotly-graph-div {
                border-radius: 14px;
                overflow: hidden;
            }
            
            /* Custom Animations */
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .stMetric {
                animation: slideIn 0.5s ease-out;
            }
            
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_metric_cards(metrics_dict):
    """Create beautiful metric cards with icons and values."""
    cols = st.columns(len(metrics_dict))
    for col, (key, value) in zip(cols, metrics_dict.items()):
        with col:
            emoji = value.get("emoji", "📊")
            label = value.get("label", key)
            val = value.get("value", 0)
            delta = value.get("delta", None)
            
            st.metric(f"{emoji} {label}", val, delta=delta)


def create_line_chart(data, x_col, y_col, title, color="Viridis"):
    """Create an interactive line chart."""
    fig = px.line(
        data,
        x=x_col,
        y=y_col,
        title=title,
        markers=True,
        color_discrete_sequence=px.colors.sequential.Viridis
        if color == "Viridis"
        else px.colors.sequential.RdPu,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0.02)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        hovermode="x unified",
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
    )
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
    )
    st.plotly_chart(fig, use_container_width=True)


def create_bar_chart(data, x_col, y_col, title, orientation="v", color_scale=None):
    """Create an interactive bar chart."""
    if orientation == "v":
        fig = px.bar(
            data,
            x=x_col,
            y=y_col,
            title=title,
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
    else:
        fig = px.bar(
            data,
            y=x_col,
            x=y_col,
            title=title,
            orientation="h",
            color_discrete_sequence=px.colors.sequential.Plasma,
        )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0.02)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        hovermode="closest",
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>",
        marker=dict(
            line=dict(color="rgba(255, 255, 255, 0.2)", width=1),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_pie_chart(data, names_col, values_col, title):
    """Create an interactive pie chart."""
    fig = px.pie(
        data,
        names=names_col,
        values=values_col,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
        marker=dict(line=dict(color="#0f172a", width=2)),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_scatter_chart(data, x_col, y_col, title, size_col=None, color_col=None):
    """Create an interactive scatter plot."""
    fig = px.scatter(
        data,
        x=x_col,
        y=y_col,
        title=title,
        size=size_col,
        color=color_col,
        color_continuous_scale="Viridis",
        hover_data=[x_col, y_col],
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0.02)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        hovermode="closest",
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
    )
    fig.update_traces(
        marker=dict(size=10, line=dict(width=1, color="rgba(255, 255, 255, 0.3)"))
    )
    st.plotly_chart(fig, use_container_width=True)


def create_histogram(data, col, title, nbins=20):
    """Create an interactive histogram."""
    fig = px.histogram(
        data,
        x=col,
        nbins=nbins,
        title=title,
        color_discrete_sequence=px.colors.sequential.Purples,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0.02)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        hovermode="x",
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        marker=dict(line=dict(color="rgba(255, 255, 255, 0.2)", width=1)),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_box_plot(data, x_col, y_col, title):
    """Create an interactive box plot."""
    fig = px.box(
        data, x=x_col, y=y_col, title=title, color_discrete_sequence=["#6366f1"]
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0.02)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        hovermode="closest",
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_heatmap(data, title, color_scale="Viridis"):
    """Create an interactive heatmap."""
    fig = go.Figure(
        data=go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale=color_scale,
            hovertemplate="<b>%{x}</b><br>%{y}<br>Value: %{z:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_area_chart(data, x_col, y_col, title):
    """Create an interactive area chart."""
    fig = px.area(
        data,
        x=x_col,
        y=y_col,
        title=title,
        color_discrete_sequence=px.colors.sequential.Viridis,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0.02)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        hovermode="x unified",
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_sunburst_chart(data, ids_col, labels_col, parents_col, values_col, title):
    """Create an interactive sunburst chart for hierarchical data."""
    fig = px.sunburst(
        data,
        ids=ids_col,
        labels=labels_col,
        parents=parents_col,
        values=values_col,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_code_quality_dashboard(metrics_data):
    """Create a comprehensive code quality dashboard."""
    st.markdown("### 📊 Code Quality Dashboard")
    
    # Create metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Maintainability", metrics_data.get("maintainability", "N/A"))
    with col2:
        st.metric("🔍 Complexity", metrics_data.get("complexity", "N/A"))
    with col3:
        st.metric("📝 Coverage", f"{metrics_data.get('coverage', 0)}%")
    with col4:
        st.metric("⚠️ Issues", metrics_data.get("issues", 0))


def create_file_analysis_dashboard(data):
    """Create analysis dashboard for files."""
    st.markdown("### 📁 File Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not data.empty:
            create_bar_chart(data, "filename", "issues", "Issues per File")
    
    with col2:
        if not data.empty:
            create_pie_chart(data, "filename", "lines", "Lines of Code Distribution")


def create_time_series_dashboard(dates, values, title):
    """Create a time series analysis dashboard."""
    if len(dates) > 0 and len(values) > 0:
        df = pd.DataFrame({"date": dates, "value": values})
        st.markdown(f"### {title}")
        create_line_chart(df, "date", "value", title)


def create_comparison_dashboard(categories, values1, values2, label1, label2):
    """Create a comparison dashboard with multiple series."""
    df = pd.DataFrame(
        {
            "Category": categories,
            label1: values1,
            label2: values2,
        }
    )
    
    fig = go.Figure(
        data=[
            go.Bar(name=label1, x=df["Category"], y=df[label1]),
            go.Bar(name=label2, x=df["Category"], y=df[label2]),
        ]
    )
    
    fig.update_layout(
        barmode="group",
        title=f"Comparison: {label1} vs {label2}",
        plot_bgcolor="rgba(0,0,0,0.02)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        hovermode="x unified",
        margin=dict(l=50, r=50, t=70, b=50),
        title_font=dict(size=18, color="#f8fafc", family="Outfit"),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148, 163, 184, 0.1)",
            zeroline=False,
        ),
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_stats_grid(stats_dict):
    """Show statistics in a nice grid layout."""
    cols = st.columns(4)
    for idx, (key, value) in enumerate(stats_dict.items()):
        with cols[idx % 4]:
            st.metric(key, value)


def create_gauge_chart(value, max_value, title, color="Viridis"):
    """Create a gauge chart."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={"text": title},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, max_value]},
                "bar": {"color": "#6366f1"},
                "steps": [
                    {"range": [0, max_value * 0.33], "color": "#ef4444"},
                    {"range": [max_value * 0.33, max_value * 0.66], "color": "#f59e0b"},
                    {"range": [max_value * 0.66, max_value], "color": "#10b981"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": max_value,
                },
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", size=12, color="#e2e8f0"),
        margin=dict(l=50, r=50, t=70, b=50),
    )
    st.plotly_chart(fig, use_container_width=True)


def create_sample_data():
    """Create sample data for demonstrations."""
    # Sample code quality metrics over time
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    quality_scores = np.random.randint(60, 95, 30)
    complexity_scores = np.random.randint(1, 10, 30)
    
    df = pd.DataFrame({
        "date": dates,
        "quality": quality_scores,
        "complexity": complexity_scores,
        "issues": np.random.randint(0, 20, 30),
        "coverage": np.random.randint(40, 100, 30),
    })
    
    return df
