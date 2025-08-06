#!/usr/bin/env python3
"""
Test script for file format detection
"""

import pandas as pd
import os
from datetime import datetime

def test_file_format_detection():
    """Test the file format detection logic"""
    print("🔍 Testing File Format Detection...")
    print("=" * 50)
    
    # Define possible file paths in order of preference
    file_paths = [
        "data/Clean_Dashboard_Data.xlsx",  # Primary: Excel format
        "data/Clean_Dashboard_Data.csv"    # Fallback: CSV format
    ]
    
    data = None
    used_file = None
    
    # Try each file format
    for file_path in file_paths:
        print(f"🔍 Trying to load: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"   ❌ File not found: {file_path}")
            continue
            
        try:
            file_size = os.path.getsize(file_path)
            print(f"   📏 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            if file_path.endswith('.xlsx'):
                data = pd.read_excel(file_path)
                used_file = file_path
                data_source = f"📊 Excel: {file_path}"
                print(f"   ✅ Successfully loaded Excel file")
                break
            elif file_path.endswith('.csv'):
                data = pd.read_csv(file_path)
                used_file = file_path
                data_source = f"📄 CSV: {file_path}"
                print(f"   ✅ Successfully loaded CSV file")
                break
                
        except FileNotFoundError:
            print(f"   ❌ File not found: {file_path}")
            continue
        except Exception as e:
            print(f"   ❌ Error loading {file_path}: {str(e)}")
            continue
    
    if data is None:
        print("\n❌ No valid data file found!")
        return False
    
    # Show results
    print(f"\n🎉 Successfully loaded data!")
    print(f"📁 Source: {data_source}")
    print(f"📊 Shape: {data.shape[0]:,} rows × {data.shape[1]} columns")
    print(f"💾 Memory usage: {data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    # Check required columns
    required_columns = [
        "Project name", "Team size", "Project last update",
        "Current step name", "Thématique", "Type de situation"
    ]
    
    print(f"\n🔍 Checking required columns...")
    missing_cols = [col for col in required_columns if col not in data.columns]
    
    if missing_cols:
        print(f"❌ Missing required columns: {', '.join(missing_cols)}")
        return False
    else:
        print(f"✅ All required columns present!")
    
    # Show data sample
    print(f"\n📋 Data sample:")
    print(data[required_columns].head(3))
    
    print("\n" + "=" * 50)
    print("🎉 File format detection test completed successfully!")
    
    return True

if __name__ == "__main__":
    test_file_format_detection()
    
    
    





//`# This script is designed to test the file format detection logic for loading data files.

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_plotly_events import plotly_events
import pandas as pd
import numpy as np
import time
import io
import importlib.util
import json


# Initialize session state for performance tracking
if 'load_time' not in st.session_state:
    st.session_state.load_time = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Performance tracking decorator
def track_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        st.session_state.load_time = round(end_time - start_time, 2)
        return result
    return wrapper


# Improved and safe color palette
COLORS = {
    "mindaro": "#D9ED92",
    "light_green": "#B5E48C",
    "light_green_2": "#99D98C",
    "emerald": "#76C893",
    "keppel": "#52B69A",
    "verdigris": "#34A0A4",
    "bondi_blue": "#168AAD",
    "cerulean": "#1A759F",
    "lapis_lazuli": "#1E6091",
    "indigo_dye": "#184E77",
    "gray": "#D1D5DB"
}

# Streamlit page configuration
st.set_page_config(
    page_title=" Le Mouvement Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data validation and cleaning functions
def validate_and_clean_data(data):
    """
    Comprehensive data validation and cleaning function
    """
    cleaning_report = {
        'original_rows': len(data),
        'issues_found': [],
        'fixes_applied': [],
        'final_rows': 0,
        'data_quality_score': 0
    }
    
    # 1. Handle missing values in critical columns
    critical_columns = ["Project name", "Team size", "Project last update", "Current step name"]
    
    for col in critical_columns:
        if col in data.columns:
            missing_count = data[col].isnull().sum()
            if missing_count > 0:
                cleaning_report['issues_found'].append(f"{col}: {missing_count} missing values")
                
                if col == "Team size":
                    # Fill with median team size
                    median_size = data[col].median()
                    data[col] = data[col].fillna(median_size)
                    cleaning_report['fixes_applied'].append(f"{col}: Filled {missing_count} missing values with median ({median_size})")
                
                elif col == "Current step name":
                    # Fill with "Unknown Step"
                    data[col] = data[col].fillna("Unknown Step")
                    cleaning_report['fixes_applied'].append(f"{col}: Filled {missing_count} missing values with 'Unknown Step'")
    
    # 2. Clean and validate Team size
    if "Team size" in data.columns:
        # Convert to numeric, handling errors
        original_team_size = data["Team size"].copy()
        data["Team size"] = pd.to_numeric(data["Team size"], errors='coerce')
        
        # Check for outliers (team size > 50 or < 1)
        outliers = data[(data["Team size"] > 50) | (data["Team size"] < 1)]["Team size"].count()
        if outliers > 0:
            cleaning_report['issues_found'].append(f"Team size: {outliers} outlier values (>50 or <1)")
            # Cap extreme values
            data.loc[data["Team size"] > 50, "Team size"] = 50
            data.loc[data["Team size"] < 1, "Team size"] = 1
            cleaning_report['fixes_applied'].append(f"Team size: Capped {outliers} outlier values")
    
    # 3. Standardize text columns
    text_columns = ["Current step name", "Thématique", "Type de situation"]
    for col in text_columns:
        if col in data.columns:
            # Remove extra whitespace and standardize
            original_values = data[col].copy()
            data[col] = data[col].astype(str).str.strip()
            data[col] = data[col].replace(['nan', 'None', 'null'], None)
            
            # Count how many were cleaned
            changes = (original_values.astype(str).str.strip() != data[col].astype(str)).sum()
            if changes > 0:
                cleaning_report['fixes_applied'].append(f"{col}: Cleaned {changes} text entries")
    
    # 4. Validate and clean date columns
    date_columns = ["Project last update"]
    for col in date_columns:
        if col in data.columns:
            # Check for future dates
            future_dates = data[data[col] > pd.Timestamp.now()][col].count()
            if future_dates > 0:
                cleaning_report['issues_found'].append(f"{col}: {future_dates} future dates found")
                # Set future dates to today
                data.loc[data[col] > pd.Timestamp.now(), col] = pd.Timestamp.now()
                cleaning_report['fixes_applied'].append(f"{col}: Fixed {future_dates} future dates")
    
    # 5. Calculate data quality score
    cleaning_report['final_rows'] = len(data)
    
    # Quality factors
    completeness = 1 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))
    consistency = 1 - (len(cleaning_report['issues_found']) / max(len(data), 1)) * 0.1
    validity = 1 - max(0, (cleaning_report['original_rows'] - cleaning_report['final_rows']) / cleaning_report['original_rows'])
    
    cleaning_report['data_quality_score'] = round((completeness * 0.4 + consistency * 0.3 + validity * 0.3) * 100, 1)
    
    return data, cleaning_report

# Enhanced data loading with flexible format support and comprehensive cleaning
@st.cache_data
@track_performance  
def load_data():
    """
    Load data with automatic format detection (Excel preferred, CSV fallback)
    """
    try:
        # Define possible file paths in order of preference
        file_paths = [
            "data/Clean_Dashboard_Data.xlsx",  # Primary: Excel format
            "data/Clean_Dashboard_Data.csv"    # Fallback: CSV format
        ]
        
        data = None
        used_file = None
        
        # Try each file format
        for file_path in file_paths:
            try:
                if file_path.endswith('.xlsx'):
                    data = pd.read_excel(file_path)
                    used_file = file_path
                    st.session_state.data_source = f"📊 Excel: {file_path}"
                    break
                elif file_path.endswith('.csv'):
                    data = pd.read_csv(file_path)
                    used_file = file_path
                    st.session_state.data_source = f"📄 CSV: {file_path}"
                    break
            except FileNotFoundError:
                continue
            except Exception as e:
                st.warning(f"Could not load {file_path}: {str(e)}")
                continue
        
        if data is None:
            st.error("❌ No valid data file found! Please ensure either 'Clean_Dashboard_Data.xlsx' or 'Clean_Dashboard_Data.csv' exists in the data/ folder.")
            st.stop()
        
        # Log successful loading
        st.session_state.file_info = {
            'source': used_file,
            'format': 'Excel' if used_file.endswith('.xlsx') else 'CSV',
            'size_mb': round(data.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'rows': len(data),
            'columns': len(data.columns)
        }
        
        # Verify required columns exist
        required_columns = [
            "Project name", "Team size", "Project last update",
            "Current step name", "Thématique", "Type de situation"
        ]
        missing_cols = [col for col in required_columns if col not in data.columns]
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            st.stop()
        
        # Basic datetime conversion
        data['Project last update'] = pd.to_datetime(data['Project last update'], errors='coerce')
        
        # Apply comprehensive cleaning
        cleaned_data, cleaning_report = validate_and_clean_data(data)
        
        # Store cleaning report in session state for display
        st.session_state.cleaning_report = cleaning_report
        
        # Check for parsing errors after cleaning
        if cleaned_data['Project last update'].isnull().any():
            remaining_nulls = cleaned_data['Project last update'].isnull().sum()
            st.warning(f"⚠️ {remaining_nulls} dates couldn't be parsed and will be excluded from time-based analysis.")
        
        return cleaned_data
    
    except Exception as e:
        st.error(f"❌ An unexpected error occurred while loading data: {e}")
        st.stop()

# Load the dataset
df = load_data()

# ────────────────────── ENHANCED SIDEBAR ────────────────────── #
with st.sidebar:
    st.title("📌 Dashboard Navigation")
    
    # Performance metrics section
    with st.expander("⚡ Performance Metrics"):
        if st.session_state.load_time:
            st.metric("Data Load Time", f"{st.session_state.load_time}s")
        st.metric("Last Refresh", st.session_state.last_refresh.strftime("%H:%M:%S"))
        st.metric("Total Records", f"{len(df):,}")
        
        # Show data source information
        if hasattr(st.session_state, 'file_info'):
            info = st.session_state.file_info
            st.write(f"**Data Source:** {info['format']}")
            st.write(f"**File Size:** {info['size_mb']} MB")
            st.write(f"**Dimensions:** {info['rows']:,} × {info['columns']}")
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    # Data Quality Report
    if hasattr(st.session_state, 'cleaning_report'):
        with st.expander("🧹 Data Quality Report"):
            report = st.session_state.cleaning_report
            
            # Quality score with color coding
            score = report['data_quality_score']
            if score >= 90:
                score_color = "🟢"
            elif score >= 70:
                score_color = "🟡"
            else:
                score_color = "🔴"
            
            st.metric("Data Quality Score", f"{score_color} {score}%")
            st.metric("Rows Processed", f"{report['original_rows']:,}")
            st.metric("Issues Found", len(report['issues_found']))
            st.metric("Fixes Applied", len(report['fixes_applied']))
            
            if report['issues_found']:
                st.write("**Issues Found:**")
                for issue in report['issues_found']:
                    st.write(f"• {issue}")
            
            if report['fixes_applied']:
                st.write("**Fixes Applied:**")
                for fix in report['fixes_applied']:
                    st.write(f"✅ {fix}")
    
    st.markdown("---")
    
    # Multiselect for charts to display
    selected_charts = st.multiselect(
        "Select charts to display:",
        options=[
            "Projects by Step",
            "Projects by Thematic Area",
            "Top TOD Advisors",
            "Team Size Distribution",
            "Mentorship Distribution",
            "Type de Situation"
        ],
        default=[
            "Projects by Step",
            "Projects by Thematic Area",
            "Top TOD Advisors"
        ]
    )

    st.markdown("---")
    st.subheader("Data Filters")

    # Team Size filter
    min_team_size, max_team_size = st.slider(
        "Team Size Range:",
        min_value=int(df["Team size"].min()),
        max_value=int(df["Team size"].max()),
        value=(int(df["Team size"].min()), int(df["Team size"].max()))
    )

    # Current Step filter
    step_options = df["Current step name"].dropna().unique().tolist()
    selected_steps = st.multiselect(
        "Current Step:",
        options=step_options,
        default=step_options  # All selected by default
    )

    # Date Range filter for Project Last Update
    min_date, max_date = st.date_input(
        "Project Last Update Range:",
        value=[
            df["Project last update"].min().date(),
            df["Project last update"].max().date()
        ],
        min_value=df["Project last update"].min().date(),
        max_value=df["Project last update"].max().date()
    )

    # Filter data based on sidebar selections
    filtered_df = df[
        (df["Team size"] >= min_team_size) &
        (df["Team size"] <= max_team_size) &
        # (df["Thématique"].isin(selected_thematic)) &
        (df["Current step name"].isin(selected_steps)) &
        (df["Project last update"].dt.date.between(min_date, max_date))
    ]

    st.markdown(f"**Filtered Projects:** {filtered_df.shape[0]} out of {df.shape[0]}")

    # Reset Filters Button (optional but useful UX feature)
    if st.button("Reset Filters"):
        st.rerun()
# ────────────────────── STYLE ────────────────────── #
st.markdown(f"""
    <style>
    html, body, .stApp {{
        background-color: #f5f7fa;
        color: #1f2937;
        font-family: 'Segoe UI', sans-serif;
    }}

    .stMultiSelect > div[data-baseweb="tag"]{{
        background-color: rgba(26, 117, 159, 1) !important;  /* cerulean */
        color: white !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
        font-weight: 500;
    }}

    /* Optional: Keep the X remove icon neutral */
    .stMultiSelect > div[data-baseweb="tag"] svg {{
        color: white !important;
        opacity: 0.8;
    }}
        
    /* Sidebar styling */
    .sidebar .sidebar-content {{
        background-color: {COLORS['indigo_dye']};
        color: white;
    }}
    
    .title-header {{
        font-size: 42px;
        font-weight: bold;
        color: {COLORS['indigo_dye']};
        margin-bottom: 0.25rem;
    }}

    .sub-header {{
        font-size: 18px;
        color: {COLORS['lapis_lazuli']};
        margin-top: -8px;
        margin-bottom: 2rem;
    }}

    .metric-box {{
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        border: 1px solid #e5e7eb;
        font-size: 20px;
        transition: transform 0.2s;
    }}

    .metric-box:hover {{
        transform: scale(1.02);
    }}

    .metric-title {{
        font-size: 16px;
        font-weight: 500;
        color: {COLORS['lapis_lazuli']};
        margin-bottom: 0.25rem;
    }}

    .metric-value {{
        font-size: 32px;
        font-weight: 700;
        color: {COLORS['indigo_dye']};
    }}
    
    .chart-card {{
        background-color: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }}
    .chart-title {{
        font-size: 20px;
        font-weight: bold;
        color: {COLORS['indigo_dye']};
    }}
    .chart-subtitle {{
        font-size: 14px;
        color: {COLORS['lapis_lazuli']};
        margin-bottom: 1rem;
    }}
    .chart-footer {{
        font-size: 13px;
        color: {COLORS['lapis_lazuli']};
        border-top: 1px solid #e5e7eb;
        margin-top: 1.5rem;
        padding-top: 1rem;
    }}
    .dashboard-navigation {{
    background-color: #2c3e50; /* Dark blue-gray */
    color: #ecf0f1; /* Light gray text */
    }}

    .dashboard-navigation a {{
        color: #3498db; /* Light blue links */
    }}

    .filters-section {{
    background-color: #34495e; /* Slightly lighter than nav */
    border-top: 1px solid #7f8c8d; /* Gray divider */
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 8px 20px;
        border-radius: 8px 8px 0 0;
        background-color: #e5e7eb;
        transition: all 0.2s;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: #d1d5db;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['indigo_dye']};
        color: white;
    }}
    
    </style>
""", unsafe_allow_html=True)

# ────────────────────── HEADER ────────────────────── #
st.markdown('<div class="title-header"> Le Mouvement Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">A real-time visual overview of intrapreneurial projects led within OCP\'s innovation ecosystem.</div>', unsafe_allow_html=True)

# ────────────────────── MAIN CONTENT TABS ────────────────────── #
tab1, tab2, tab3 = st.tabs(["📊 Overview Dashboard", "📈 Stages Analysis", "🧹 Data Quality"])

with tab1:
    # ────────────────────── KPI SECTION ────────────────────── #
    st.markdown("###  Key Performance Indicators")
    
    # Add data quality indicators
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Projects</div>
                <div class="metric-value">{filtered_df.shape[0]}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        last_update = filtered_df["Project last update"].max()
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Last Update</div>
                <div class="metric-value">{pd.to_datetime(last_update).date()}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        inactive_cutoff = pd.Timestamp.now() - pd.Timedelta(days=60)
        inactive_projects = filtered_df[filtered_df["Project last update"] < inactive_cutoff]
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Inactive Projects (60+ days)</div>
                <div class="metric-value">⏳ {inactive_projects.shape[0]}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col4:
        # Data completeness indicator
        step_completeness = filtered_df["Current step name"].notna().mean() * 100
        color = "🟢" if step_completeness > 90 else "🟡" if step_completeness > 70 else "🔴"
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Data Completeness</div>
                <div class="metric-value">{color} {step_completeness:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    # Optional preview
    with st.expander("🔍 View Raw Data"):
        st.dataframe(filtered_df)

    st.markdown("---")

    # ────────────────────── DYNAMIC CHARTS BASED ON SIDEBAR SELECTION ────────────────────── #

    if "Projects by Step" in selected_charts:
        # Section 1: Projects by Step (Radial Chart Style)
        st.markdown('<div class="chart-title">Projects Distribution By Their Current Step</div>', unsafe_allow_html=True)

        step_counts = filtered_df["Current step name"].value_counts().reset_index()
        step_counts.columns = ["Step", "Count"]

        # Use the color palette for the pie chart
        pie_colors = [
            COLORS['mindaro'], COLORS['light_green'], COLORS['light_green_2'], 
            COLORS['emerald'], COLORS['keppel'], COLORS['verdigris'],
            COLORS['bondi_blue'], COLORS['cerulean'], COLORS['lapis_lazuli'], 
            COLORS['indigo_dye']
        ]

        fig = go.Figure(data=[go.Pie(
            labels=step_counts["Step"],
            values=step_counts["Count"],
            hole=0.7,
            marker=dict(
                colors=pie_colors,
                line=dict(color='white', width=2)
            ),
            textinfo='label+percent',
            insidetextorientation='radial',
        )])

        fig.update_layout(
            showlegend=True,
            margin=dict(t=70, b=0, l=0, r=0),
            height=400,
            title={
                'text': "",
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20)
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
    if "Projects by Thematic Area" in selected_charts:
        # Group and enrich data
        theme_projects = filtered_df.groupby("Thématique").agg({
            "Project name": lambda x: "<br>".join(map(str, x.head(5))),  # Ensure string
            "Project last update": "max",
            "Team size": "mean"
        }).reset_index()

        # Compute value counts for themes
        theme_counts = filtered_df["Thématique"].value_counts().reset_index()
        theme_counts.columns = ["Theme", "Count"]
        theme_counts["Percent"] = (theme_counts["Count"] / theme_counts["Count"].sum() * 100).round(1)

        # Merge all relevant data
        theme_data = pd.merge(
            theme_counts,
            theme_projects,
            left_on="Theme",
            right_on="Thématique",
            how="left"
        )

        # Sanitize & format data
        theme_data["Project name"] = theme_data["Project name"].fillna("N/A")
        theme_data["Project last update"] = pd.to_datetime(theme_data["Project last update"]).dt.date.astype(str)
        theme_data["Team size"] = theme_data["Team size"].fillna(0).round(1)

        # Sort by count
        theme_data = theme_data.sort_values(by="Count", ascending=True)

        # Store thematic project lists in session state
        if 'thematic_projects' not in st.session_state:
            st.session_state.thematic_projects = {}
        
        # Group projects by thematic for the full list
        for thematic in filtered_df['Thématique'].unique():
            projects = filtered_df[filtered_df['Thématique'] == thematic][['Project name', 'Team size', 'Project last update', 'Current step name']]
            st.session_state.thematic_projects[thematic] = projects
        
        # Add click callback data to figure
        fig = px.bar(
            theme_data,
            x="Count",
            y="Theme",
            orientation="h",
            text="Percent",
            labels={"Count": "Number of Projects", "Theme": "Thematic Area"},
            color="Theme",
            color_discrete_sequence=[
                COLORS['mindaro'], COLORS['light_green'], COLORS['light_green_2'],
                COLORS['emerald'], COLORS['keppel'], COLORS['verdigris']
            ]
        )

        fig.update_traces(
            texttemplate='%%{text}%%',
            textposition='outside',
            marker_line_color='white',
            marker_line_width=1,
            hovertemplate="<b>%{y}</b><br>Projects: %{x}<extra></extra>",
            customdata=theme_data['Theme']  # Store theme names for click events
        )

        # Layout
        fig.update_layout(
            title="Project Distribution Across All Thematics",
            xaxis_title="Number of Projects",
            yaxis_title="",
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=30, r=30, t=50, b=30),
            showlegend=False
        )

        # Enhanced styling for interactive elements
        st.markdown("""
            <style>
            .thematic-section {
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                margin-bottom: 1rem;
            }
            .thematic-controls {
                display: flex;
                align-items: center;
                padding: 1rem;
                border-bottom: 1px solid #f0f0f0;
            }
            .thematic-content {
                padding: 1.5rem;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }
            .stats-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.85rem;
                margin-right: 8px;
                background-color: #f3f4f6;
                color: #374151;
            }
            .interaction-hint {
                color: #6B7280;
                font-size: 0.875rem;
                margin-bottom: 0.5rem;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="chart-title">Projects by Thematic Area</div>', unsafe_allow_html=True)
        st.markdown('<div class="interaction-hint">👇🏻 use the selector below to explore projects</div>', unsafe_allow_html=True)
        
        # Display the chart and get clicked data
        clicked = st.plotly_chart(fig, use_container_width=True)
        
        # Thematic selector with improved UX
        with st.container():
            st.markdown('<div class="thematic-section">', unsafe_allow_html=True)
            selected_thematic = st.selectbox(
                "Select a thematic area",
                options=[''] + list(st.session_state.thematic_projects.keys()),
                key='thematic_selector',
                format_func=lambda x: f"{x} ({len(st.session_state.thematic_projects[x]) if x else 0} projects)"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Show project details with premium presentation
        if selected_thematic:
            projects_df = st.session_state.thematic_projects[selected_thematic]
            
            # Enhanced styling for premium look
            st.markdown("""
                <style>
                .premium-container {
                    background: linear-gradient(to right, #ffffff, #f8f9fa);
                    border: 1px solid #e5e7eb;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                }
                .metric-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 0.5rem;
                    margin-bottom: 1rem;
                }
                .thematic-metric-card {
                    background: white;
                    padding: 0.75rem;
                    border-radius: 8px;
                    border: 1px solid #e5e7eb;
                    transition: all 0.2s ease;
                }
                .thematic-metric-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                }
                .thematic-metric-label {
                    font-size: 0.875rem;
                    color: #6B7280;
                    margin-bottom: 0.25rem;
                }
                .thematic-metric-value {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: """ + COLORS['indigo_dye'] + """;
                }
                .status-indicator {
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    margin-right: 6px;
                }
                .header-section {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding-left: 1rem;
                    border-bottom: 2px solid #f3f4f6;
                }
                .title-badge {
                    background-color: """ + COLORS['cerulean'] + """;
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 16px;
                    font-size: 0.875rem;
                    font-weight: 500;
                }
                </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="premium-container">', unsafe_allow_html=True)
                
                # Enhanced header with visual hierarchy
                st.markdown(f"""
                    <div class="header-section">
                        <div>
                            <h2 style="margin:0; color:{COLORS['indigo_dye']}; font-size:1.5rem;">
                                {selected_thematic} Projects Overview : 
                            </h2>
                            <span class="title-badge">Thematic Area Analysis</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Removed metrics grid to reduce redundancy and improve clarity
                
                # Add dynamic table styling
                st.markdown("""
                    <style>
                    [data-testid="stDataFrame"] {
                        min-height: 200px;
                        max-height: 600px;
                    }
                    [data-testid="stDataFrame"] > div {
                        transition: all 0.3s ease;
                    }
                    [data-testid="stDataFrame"] [data-testid="stTable"] {
                        height: auto !important;
                    }
                    .table-info {
                        color: #6B7280;
                        font-size: 0.875rem;
                        margin-bottom: 0.5rem;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    }
                    </style>
                """, unsafe_allow_html=True)

                # Calculate dynamic height based on number of rows
                min_height = 200
                max_height = 600
                rows_per_page = 10
                calculated_height = min(max(min_height, len(projects_df) * 35), max_height)

                # Show table info
                st.markdown(
                    f'<div class="table-info">📑 Showing {len(projects_df)} projects</div>',
                    unsafe_allow_html=True
                )

                # Enhanced interactive project table with dynamic height
                st.dataframe(
                    projects_df,
                    use_container_width=True,
                    column_config={
                        "Project name": st.column_config.TextColumn(
                            "Project Name",
                            help="Name of the project",
                            width="large",
                        ),
                        "Team size": st.column_config.NumberColumn(
                            "Team Size",
                            help="Number of team members",
                            format="%d 👥",
                            min_value=0,
                            max_value=50,
                        ),
                        "Project last update": st.column_config.DateColumn(
                            "Last Update",
                            help="Most recent update date",
                            format="MMM DD, YYYY",
                        ),
                        "Current step name": st.column_config.TextColumn(
                            "Current Step",
                            help="Current project stage",
                            width="medium",
                        )
                    },
                    height=calculated_height
                )
                
                # Enhanced export section with actions
                st.markdown("""
                    <div style="border-top: 1px solid #e5e7eb; margin-top: 1rem; padding-top: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="color: #6B7280; font-size: 0.875rem;">
                                Export options for detailed analysis
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 2, 2])
                with col2:
                    csv = projects_df.to_csv(index=False)
                    st.download_button(
                        "📥 Export to Excel Format",
                        csv,
                        f"{selected_thematic}_Projects_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key='download_csv',
                        use_container_width=True,
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")

    if "Top TOD Advisors" in selected_charts:
        # Top TOD Advisors
        advisor_data = filtered_df["TOD Advisor"].dropna()
        top_advisors = advisor_data.value_counts().nlargest(10).reset_index()
        top_advisors.columns = ["Advisor", "Project Count"]

        with st.container():
            st.markdown('<div class="chart-title">Top TOD Advisors</div>', unsafe_allow_html=True)
            st.markdown('<div class="chart-subtitle">By number of supported projects (Top 10)</div>', unsafe_allow_html=True)

            fig = go.Figure(go.Bar(
                x=top_advisors["Project Count"],
                y=top_advisors["Advisor"],
                orientation='h',
                text=top_advisors["Project Count"],
                textposition='outside',
                marker_color=COLORS['cerulean'],
                hovertemplate='%{y}: %{x} projects',
            ))

            fig.update_layout(
                height=500,  # Increased height to accommodate more entries
                margin=dict(l=50, r=30, t=20, b=50),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color=COLORS['indigo_dye']),
                xaxis=dict(
                    title="Number of Projects",
                    showgrid=True,
                    gridcolor="#f3f4f6",
                    zeroline=False,
                    title_font=dict(size=14, color=COLORS['lapis_lazuli']),
                ),
                yaxis=dict(
                    title="Advisor",
                    showgrid=False,
                    title_font=dict(size=14, color=COLORS['lapis_lazuli']),
                    automargin=True,
                )
            )

            st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

    if "Team Size Distribution" in selected_charts:
        # Team Size Distribution - Enhanced Version
        st.markdown('<div class="chart-title">Team Size Distribution</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-subtitle">Histogram with summary statistics</div>', unsafe_allow_html=True)

        # Clean and convert team size column
        filtered_df["Team Size"] = pd.to_numeric(filtered_df["Team size"], errors="coerce")
        team_size_clean = filtered_df["Team Size"].dropna()

        # Calculate statistics
        avg_size = team_size_clean.mean().round(1)
        median_size = team_size_clean.median()
        mode_size = team_size_clean.mode().values[0]
        min_size = team_size_clean.min()
        max_size = team_size_clean.max()

        # Create figure with dual axes
        fig = go.Figure()

        # Add histogram (primary axis)
        fig.add_trace(
            go.Histogram(
                x=team_size_clean,
                nbinsx=10,
                name="Distribution",
                marker_color=COLORS['verdigris'],
                opacity=0.7,
                hovertemplate="Team Size: %%{x}<br>Count: %%{y}<extra></extra>"
            )
        )

        # Add box plot (secondary axis, invisible but shows quartiles)
        fig.add_trace(
            go.Box(
                x=team_size_clean,
                name="Box Plot",
                line_color=COLORS['indigo_dye'],
                hoverinfo="none",
                showlegend=False
            )
        )

        # Add vertical lines for stats
        for stat, val, color in zip(
            ["Mean", "Median", "Mode"],
            [avg_size, median_size, mode_size],
            [COLORS['emerald'], COLORS['bondi_blue'], COLORS['mindaro']]
        ):
            fig.add_vline(
                x=val,
                line_dash="dot",
                line_color=color,
                annotation_text=f"{stat}: {val}",
                annotation_position="top",
                annotation_font_size=12,
                annotation_bgcolor="rgba(255,255,255,0.7)"
            )

        # Layout enhancements
        fig.update_layout(
            title="",
            xaxis_title="Team Size",
            yaxis_title="Number of Projects",
            bargap=0.15,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=40, r=30, t=20, b=60),
            hovermode="x unified",
            showlegend=False,
            annotations=[
                dict(
                    x=0.95,
                    y=0.7,
                    xref="paper",
                    yref="paper",
                    text=f"<b>Stats Summary</b><br>Min: {min_size}<br>Max: {max_size}",
                    showarrow=False,
                    align="right",
                    bgcolor="white",
                    bordercolor=COLORS['lapis_lazuli'],
                    borderwidth=1
                )
            ]
        )

        st.plotly_chart(fig, use_container_width=True)
    if "Mentorship Distribution" in selected_charts:
        # Mentorship Data Preparation
        mentor_series = filtered_df["Accompagnement"].fillna("Not Mentored").replace("0", "Not Mentored")
        mentor_list = mentor_series.str.split(",", expand=True).stack().reset_index(drop=True)
        mentor_df = pd.DataFrame(mentor_list, columns=["Mentor"])
        mentor_df["Mentor"] = mentor_df["Mentor"].str.strip()

        # Create complete mentorship data with project information
        mentor_df = mentor_df.join(
            filtered_df[["Project name", "Project last update", "Team size"]], 
            how="left"
        )

        # Aggregate data by mentor
        mentor_stats = mentor_df.groupby("Mentor").agg({
            "Project name": lambda x: "<br>• ".join([""] + list(x.dropna().astype(str).unique())),
            "Project last update": "max",
            "Team size": "mean"
        }).reset_index()

        # Get counts and percentages
        mentor_counts = mentor_df["Mentor"].value_counts().reset_index()
        mentor_counts.columns = ["Mentor", "Count"]
        mentor_counts["Percentage"] = (mentor_counts["Count"] / mentor_counts["Count"].sum() * 100).round(1)

        # Combine all data
        mentor_data = pd.merge(mentor_counts, mentor_stats, on="Mentor", how="left")

        # Clean and format data
        mentor_data["Project name"] = mentor_data["Project name"].fillna("No projects")
        mentor_data["Project last update"] = pd.to_datetime(
            mentor_data["Project last update"]
        ).dt.strftime("%Y-%m-%d").fillna("Unknown")
        mentor_data["Team size"] = mentor_data["Team size"].fillna(0).round(1)

        # Prepare colors
        mentorship_colors = [
            COLORS['mindaro'], COLORS['light_green'], COLORS['emerald'],
            COLORS['keppel'], COLORS['verdigris'], COLORS['bondi_blue']
        ]

        with st.container():
            st.markdown('<div class="chart-title">Mentorship Distribution</div>', unsafe_allow_html=True)
            st.markdown('<div class="chart-subtitle">As of {}</div>'.format(pd.Timestamp.now().date()), unsafe_allow_html=True)

            # Create pie chart with proper customdata
        fig = go.Figure(data=[go.Pie(
            labels=mentor_data["Mentor"],
            values=mentor_data["Count"],
            hole=0.5,
            textinfo="label+percent",
            marker=dict(
                colors=mentorship_colors,
                line=dict(color="#ffffff", width=2)
            ),
            customdata=mentor_data[["Project name", "Project last update"]],
            hovertemplate="""
                <b>%%{label}</b><br>
                Projects: %%{value}<br>
                <b>Projects:</b>%%{customdata[0]}
                <extra></extra>
            """
        )])

        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=True,
            height=450  # Slightly taller to accommodate tooltips
            )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
    if "Type de Situation" in selected_charts:
        # Clean column names to avoid hidden spaces or weird characters
        filtered_df.columns = filtered_df.columns.str.strip()
        
        # Chart: Type de Situation Distribution
        true_col_name = [col for col in filtered_df.columns if "Type de situation" in col][0]

        # Prepare data
        situation_counts = filtered_df[true_col_name].dropna().value_counts().reset_index()
        situation_counts.columns = ["Situation Type", "Count"]
        situation_counts["Percent"] = (situation_counts["Count"] / situation_counts["Count"].sum() * 100).round(1)

        # Custom Colors using the palette
        colors = [COLORS['emerald'], COLORS['bondi_blue'], COLORS['light_green_2']]

        # Build chart
        fig = go.Figure()

        for i, row in situation_counts.iterrows():
            fig.add_trace(go.Bar(
                y=[""],
                x=[row["Percent"]],
                name=row["Situation Type"],
                orientation='h',
                marker=dict(color=colors[i % len(colors)]),
                hovertemplate=f"<b>{row['Situation Type']}</b><br>Share: {row['Percent']}%%",
                width=0.3,
                text=f"{row['Percent']}%",
                textposition='inside',
                insidetextanchor='start',
                textfont=dict(color="white", size=12)
            ))

        # Layout polish
        fig.update_layout(
            barmode='stack',
            height=220,
            margin=dict(t=30, b=60, l=40, r=40),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=12, color=COLORS['lapis_lazuli'])
            ),
            title=dict(
                text="<b>Relative Share by Type de Situation</b>",
                x=0.01,
                xanchor='left',
                font=dict(size=16, color=COLORS['indigo_dye'])
            ),
            xaxis=dict(
                title="Percentage",
                ticksuffix="%",
                showgrid=False,
                showline=False,
                zeroline=False,
                title_font=dict(size=13, color=COLORS['lapis_lazuli']),
                tickfont=dict(size=12),
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                showline=False,
                zeroline=False,
            )
        )

        # Display
        st.markdown('<div class="chart-title"> Type de Situation Distribution (%)</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    # ────────────────────── STAGES ANALYSIS TAB ──────────────────────
with tab2:

    # palette for the three traces
    status_colors = {
        "Completed": COLORS["emerald"],
        "Blocked": COLORS["mindaro"],
        "NotStarted": COLORS["gray"]
    }

    st.markdown("### Stages Analysis")

    # ── 0) Mandatory category selection ──
    counts_raw = df["Type de situation"].str.lower().value_counts(dropna=False)
    label_map = {
        "Business": "business",
        "OM": "operating model", 
        "Ecosystem": "ecosystème"
    }

    chosen = st.selectbox(
        "Select project category:",
        options=list(label_map.keys()),
        format_func=lambda x: f"{x} ({counts_raw.get(label_map[x], 0)})"
    )

    # ── 1) Filter dataframe based on selection ──
    df_stage = filtered_df.copy()
    long_key = label_map[chosen]
    df_stage = df_stage[
        df_stage["Type de situation"]
        .str.lower()
        .str.startswith(long_key, na=False)
    ]
    
    if df_stage.empty:
        st.info("No projects in this category with current filters.")
        st.stop()

    # ── 2) Define canonical step sequences ──
    sequences = {
        "Business": [
            "Soumission", "Categorization", "Ideation", "Ideation | Demo Day", "Development",
            "Business | Incubation", "Business | Pre-Hacking Committee", "Business | Hacking Committee",
            "Business | Acceleration", "Business | Pre-Impact Committee", "Business | Impact Committee",
            "Business | Impact", "Business | Series B"
        ],
        "OM": [
            "Soumission", "Categorization", "Ideation", "Ideation | Demo Day", "Development",
            "OM | Incubation", "OM | Pre-Hacking Committee", "OM | Hacking Committee",
            "OM | Acceleration", "OM | Pre-Impact Committee", "OM | Impact Committee", "OM | Impact"
        ],
        "Ecosystem": [
            "Soumission", "Categorization", "Ideation", "Ideation | Demo Day", "Development",
            "Ecosystem | Pre-Hacking Committee", "Ecosystem | Hacking Committee",
            "Ecosystem | Acceleration", "Ecosystem | Pre-Impact Committee",
            "Ecosystem | Impact Committee", "Ecosystem | Impact"
        ]
    }
    
    current_sequence = sequences[chosen]

    # ── 3) Create step lookup dictionaries ──
    sid_list = sorted({c.split("(")[1].split(")")[0] for c in df_stage.columns if "Step Name" in c},
                     key=lambda s: int(s.split("_")[1]))
    
    sid_to_label = {}
    for sid in sid_list:
        lbls = df_stage[f"Step Name ({sid})"].dropna().astype(str)
        if not lbls.empty:
            sid_to_label[sid] = lbls.mode().iat[0].strip()
    label_to_sid = {lbl: sid for sid, lbl in sid_to_label.items()}

    # Filter labels to only include those in our current sequence
    iter_labels = [lbl for lbl in current_sequence if lbl in label_to_sid]

    # Helper function to gather project names
    def gather(mask):
        return df_stage.loc[mask, "Project name"].astype(str).tolist()

    # ── 4) Create step status dataframe ──
    recs = []
    for lbl in iter_labels:
        sid = label_to_sid[lbl]
        entry_col = f"Entry date ({sid})"
        submit_col = f"Submission date ({sid})"

        entered = df_stage.get(entry_col, pd.Series(index=df_stage.index)).notna()
        submitted = df_stage.get(submit_col, pd.Series(index=df_stage.index)).notna()

        recs.append(dict(
            FullStepName=lbl,
            Step=lbl.split("|")[-1].strip(),
            Completed=submitted.sum(),
            Blocked=(entered & ~submitted).sum(),
            NotStarted=(~entered).sum(),
            Completed_names=gather(submitted),
            Blocked_names=gather(entered & ~submitted),
            NotStarted_names=gather(~entered)
        ))

    step_df = pd.DataFrame(recs)
    step_df["Total"] = step_df[["Completed", "Blocked", "NotStarted"]].sum(axis=1)
    xmax = int(step_df["Total"].max())
    dtick = 1 if xmax <= 20 else None

    # ── 5) Create stacked-bar funnel chart ──
    clip = lambda lst, n=8: "<br>".join(lst[:n]) + ("<br>…" if len(lst) > n else "")
    fig = go.Figure()

    for col, label in [("Completed", "Completed"),
                      ("Blocked", "In progress"),
                      ("NotStarted", "Not started")]:
        fig.add_bar(
            y=step_df["Step"],
            x=step_df[col],
            name=label,
            orientation="h",
            marker_color=status_colors[col],
            customdata=step_df[f"{col}_names"].apply(clip),
            hovertemplate=f"%{{y}}<br>{label}: %{{x}} proj.<br><br>%{{customdata}}<extra></extra>"
        )

    fig.update_layout(
        barmode="stack",
        height=460,
        title=f"Stage funnel – {chosen}",
        xaxis=dict(title="Number of projects",
                  range=[0, xmax],
                  dtick=dtick),
        yaxis_title="",
        plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── 6) Drill-down widgets ──
    nice_status = {
        "Completed": "Completed",
        "Blocked": "In Progress",
        "NotStarted": "Not started"
    }

    step_chosen = st.selectbox(
        "Select a step to inspect", step_df["Step"], key="step_select"
    )
    status_chosen = st.radio(
        "Status within that step",
        ["Completed", "Blocked", "NotStarted"],
        format_func=lambda s: nice_status[s],
        horizontal=True,
        key="status_select"
    )

    # Get the full step name for the selected step
    full_step_name = step_df.loc[step_df["Step"] == step_chosen, "FullStepName"].iat[0]
    names_sorted = sorted(
        step_df.loc[step_df["Step"] == step_chosen,
                   f"{status_chosen}_names"].iat[0]
    )

    st.markdown(
        f"#### {nice_status[status_chosen]} – {step_chosen} "
        f"({len(names_sorted)} project{'s' if len(names_sorted)!=1 else ''})"
    )
    tbl = pd.DataFrame({"Project name": names_sorted})
    st.dataframe(tbl, use_container_width=True)

    # Download button
    import io, importlib
    engine = "xlsxwriter" if importlib.util.find_spec("xlsxwriter") else "openpyxl"
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine=engine) as writer:
        tbl.to_excel(writer, index=False, sheet_name="Projects")
    buffer.seek(0)

    st.download_button(
        "💾 Download This List",
        data=buffer,
        file_name=f"{step_chosen}_{status_chosen}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    with st.expander("ℹ What do these statuses mean?"):
        st.markdown("""
    * **Completed** – entry date **and** submission date present  
    * **In Progress** – entry date present, submission date missing  
    * **Not started** – entry date missing
    """)

    # ── 7) Stage Duration Analysis (Fixed to show ALL steps) ──
    st.markdown("### Stage Duration Analysis")
    
    # Get the complete step sequence for the selected category
    complete_steps = sequences[chosen]
    
    # Get display names (after "|") for all steps
    display_names = [step.split("|")[-1].strip() for step in complete_steps]
    
    # Prepare duration data
    duration_data = []
    for step in complete_steps:
        if step in label_to_sid:  # Only if step exists in data
            sid = label_to_sid[step]
            entry_col = f"Entry date ({sid})"
            submit_col = f"Submission date ({sid})"
            
            if all(col in df_stage.columns for col in [entry_col, submit_col]):
                # Safely handle datetime conversion
                try:
                    entries = df_stage[[entry_col, submit_col]].copy()
                    entries[entry_col] = pd.to_datetime(entries[entry_col], errors='coerce')
                    entries[submit_col] = pd.to_datetime(entries[submit_col], errors='coerce')
                    entries = entries.dropna()
                    
                    if not entries.empty:
                        durations = (entries[submit_col] - entries[entry_col]).dt.days
                        for days in durations:
                            duration_data.append({
                                'Step': step.split("|")[-1].strip(),
                                'Duration (days)': days
                            })
                        
                except Exception as e:
                    st.warning(f"Error processing dates for step {step}: {str(e)}")

    duration_df = pd.DataFrame(duration_data)
    
    # Create visualization
    fig = go.Figure()
    
    # Color palette from your COLORS dictionary
    color_sequence = [
        COLORS['mindaro'], COLORS['light_green'], COLORS['light_green_2'],
        COLORS['emerald'], COLORS['keppel'], COLORS['verdigris'],
        COLORS['bondi_blue'], COLORS['cerulean'], COLORS['lapis_lazuli']
    ]
    
    # Add traces for ALL steps in the predefined order with integrated risk assessment
    for i, step_name in enumerate(display_names):
        # Check if we have data for this step
        step_has_data = not duration_df.empty and (duration_df['Step'] == step_name).any()
        
        if step_has_data:
            step_data = duration_df[duration_df['Step'] == step_name]
            
            # Calculate risk metrics for this step
            avg_duration = step_data["Duration (days)"].mean()
            risk_level = "Low" if avg_duration <= 30 else "Moderate" if avg_duration <= 60 else "High" if avg_duration <= 90 else "Critical"
            risk_colors = {"Low": "#10B981", "Moderate": "#F59E0B", "High": "#F97316", "Critical": "#DC2626"}
            
            # Add box plot with real data and risk-based coloring
            fig.add_trace(go.Box(
                y=step_data["Duration (days)"],
                name=step_name,
                marker_color=risk_colors[risk_level],
                boxmean=False,
                line=dict(width=2),
                boxpoints='outliers',
                fillcolor=risk_colors[risk_level],
                opacity=0.7,
                width=0.4,
                hovertemplate=(
                    f"<b>{step_name}</b><br>" +
                    "Duration: %{y} days<br>" +
                    f"Average: {avg_duration:.1f} days<br>" +
                    f"Risk Level: {risk_level}<br>" +
                    "<extra></extra>"
                )
            ))
            
            # Add average marker
            avg_days = step_data["Duration (days)"].mean()
            fig.add_trace(go.Scatter(
                x=[step_name],
                y=[avg_days],
                mode="markers+text",
                marker=dict(
                    color='red',
                    size=12,
                    symbol='diamond'
                ),
                text=[f"Avg: {int(avg_days)}d"],
                textposition="top center",
                showlegend=False
            ))
        else:
            # Add invisible trace to maintain the step's position
            fig.add_trace(go.Box(
                y=[None],
                name=step_name,
                marker_color='rgba(0,0,0,0)',
                line=dict(width=0),
                fillcolor='rgba(0,0,0,0)',
                width=0.4
            ))

    # Calculate overall risk metrics
    stage_risk_metrics = {}
    for step_name in display_names:
        if step_name in duration_df['Step'].values:
            step_data = duration_df[duration_df['Step'] == step_name]
            avg_duration = step_data["Duration (days)"].mean()
            risk_level = "Low" if avg_duration <= 30 else "Moderate" if avg_duration <= 60 else "High" if avg_duration <= 90 else "Critical"
            stage_risk_metrics[step_name] = {
                'avg_duration': avg_duration,
                'risk_level': risk_level
            }
    
    # Calculate portfolio risk score
    risk_weights = {"Low": 0, "Moderate": 10, "High": 20, "Critical": 40}
    total_risk_score = 100
    if stage_risk_metrics:
        deductions = sum(risk_weights[metrics['risk_level']] for metrics in stage_risk_metrics.values())
        total_risk_score = max(0, 100 - (deductions / len(stage_risk_metrics)))
    
    # Update layout with integrated risk assessment
    fig.update_layout(
        title={
            'text': f"<b>Stage Duration & Risk Analysis - {chosen} Projects</b><br>" +
                   f"<span style='font-size:16px'>Portfolio Health Score: {total_risk_score:.0f}/100</span>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=22, color=COLORS['indigo_dye'])
        },
        xaxis=dict(
            title="Process Steps",
            categoryorder='array',
            categoryarray=display_names,
            tickangle=-45,
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title="Stage Duration (days)",
            gridcolor="#f3f4f6",
            title_font=dict(size=16)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=120, b=150, l=50, r=50),
        height=600,
        showlegend=False,
        annotations=[
            dict(
                x=1.0,
                y=1.05,
                xref='paper',
                yref='paper',
                text=f"Risk Levels: " +
                     "🟢 Low (≤30d) | " +
                     "🟡 Moderate (31-60d) | " +
                     "🟠 High (61-90d) | " +
                     "🔴 Critical (>90d)",
                showarrow=False,
                font=dict(size=12),
                align='right'
            )
        ]
    )

    # Add explanatory note if no data exists
    if duration_df.empty:
        fig.add_annotation(
            text="No duration data available for completed projects",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS['lapis_lazuli'])
        )

    st.plotly_chart(fig, use_container_width=True)
    
    # Display integrated insights
    if not duration_df.empty:
        # Identify bottlenecks and risks
        high_risk_stages = [
            stage for stage, metrics in stage_risk_metrics.items()
            if metrics['risk_level'] in ['High', 'Critical']    # Export functionality
    st.markdown("#### 📊 Executive Export")
    if st.button("Generate Risk Report", type="primary"):
        with st.spinner("Compiling executive report..."):
            # Create formatted Excel report
            report_df = risk_df[[
                "Project name", "Risk_Category", "Days_Since_Update", "Project last update"
            ]].rename(columns={
                "Project name": "Project",
                "Risk_Category": "Risk Level",
                "Days_Since_Update": "Days Inactive",
                "Project last update": "Last Update"
            }).sort_values(["Risk Level", "Days Inactive"], ascending=[True, False])
            
            # Apply conditional formatting
            def risk_color(val):
                colors = {
                    "Critical": "#FFC7CE",
                    "Action Required": "#FFEB9C",
                    "Watch": "#C6EFCE",
                    "Active": "#FFFFFF"
                }
                return f"background-color: {colors.get(val, '#FFFFFF')}"
            
            styled_report = report_df.style.applymap(risk_color, subset=["Risk Level"])
            
            # Export to Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                styled_report.to_excel(writer, index=False, sheet_name='Risk Report')
                workbook = writer.book
                worksheet = writer.sheets['Risk Report']
                
                # Add header formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#1F497D',
                    'font_color': 'white',
                    'border': 1
                })
                
                for col_num, value in enumerate(report_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
            
            buffer.seek(0)
            st.success("Report generated!")
            st.download_button(
                label="📥 Download Risk Report",
                data=buffer,
                file_name=f"Portfolio_Risk_Report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.ms-excel"
            )
        ]
        
        longest_stage = max(stage_risk_metrics.items(), key=lambda x: x[1]['avg_duration'])
        shortest_stage = min(stage_risk_metrics.items(), key=lambda x: x[1]['avg_duration'])
        
        # Create insight cards
        col1, col2 = st.columns(2)
        
        with col1:
            status_color = "#10B981" if total_risk_score >= 85 else "#F59E0B" if total_risk_score >= 70 else "#DC2626"
            st.markdown(f"""
            <div style='background-color: {status_color}15; border-left: 5px solid {status_color}; padding: 15px; border-radius: 5px;'>
                <h4 style='margin:0; color: {status_color}'>Process Health Summary</h4>
                <p style='margin:10px 0'>
                    <strong>Duration Insights:</strong><br>
                    • Longest stage: {longest_stage[0]} ({longest_stage[1]['avg_duration']:.1f} days)<br>
                    • Shortest stage: {shortest_stage[0]} ({shortest_stage[1]['avg_duration']:.1f} days)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            if high_risk_stages:
                st.markdown(f"""
                <div style='background-color: #DC262615; border-left: 5px solid #DC2626; padding: 15px; border-radius: 5px;'>
                    <h4 style='margin:0; color: #DC2626'>Risk Areas</h4>
                    <p style='margin:10px 0'>
                        <strong>High-Risk Stages:</strong><br>
                        {'<br>'.join(f"• {stage}" for stage in high_risk_stages)}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background-color: #10B98115; border-left: 5px solid #10B981; padding: 15px; border-radius: 5px;'>
                    <h4 style='margin:0; color: #10B981'>Risk Areas</h4>
                    <p style='margin:10px 0'>✅ No high-risk stages identified</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ── 8) Executive Risk Intelligence (BCG-Grade) ──
    # --- Executive consultant essentials ---
    # Only keep: Export risk report, actionable insights, and features not covered by stage analysis
    now = pd.Timestamp.now()
    if "Current step name" in df_stage.columns:
        risk_df = df_stage.copy()
        risk_df["StepNameShort"] = risk_df["Current step name"].str.split("|").str[-1].str.strip()
        current_display_names = [x.split("|")[-1].strip() for x in iter_labels]
        risk_df = risk_df[risk_df["StepNameShort"].isin(current_display_names)]
        risk_df["Days_Since_Update"] = (now - risk_df["Project last update"]).dt.days
        # Export risk report for projects stalled >60 days
        at_risk_export = risk_df[risk_df["Days_Since_Update"] >= 60][
            ["Project name", "StepNameShort", "Days_Since_Update"]
        ].copy()
        at_risk_export.columns = ["Project", "Current_Stage", "Days_Inactive"]
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            at_risk_export.to_excel(writer, index=False, sheet_name="At_Risk_Projects")
        buffer.seek(0)
        st.download_button(
            "📤 Export At-Risk Projects",
            data=buffer,
            file_name=f"risk_report_{chosen}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download a list of projects stalled >60 days for executive review"
        )
        # Actionable insight: highlight bottleneck stage if >40% of at-risk projects are in one stage
        if not at_risk_export.empty:
            bottleneck = at_risk_export["Current_Stage"].value_counts(normalize=True)
            if bottleneck.iloc[0] > 0.4:
                st.error(f"🚨 Bottleneck detected: {bottleneck.index[0]} ({bottleneck.iloc[0]*100:.0f}% of at-risk projects)")
            else:
                st.success("No critical bottleneck detected among at-risk projects.")
        else:
            st.info("No projects stalled >60 days. Portfolio is healthy.")

# ────────────────────── DATA QUALITY TAB ──────────────────────
with tab3:
    st.markdown("### 🧹 Data Quality Analysis")
    st.markdown("Comprehensive analysis of data completeness, consistency, and quality issues.")
    
    # Data Quality Overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Overall completeness
        total_cells = len(df) * len(df.columns)
        non_null_cells = df.count().sum()
        completeness = (non_null_cells / total_cells) * 100
        
        st.metric(
            "Overall Completeness",
            f"{completeness:.1f}%",
            help="Percentage of non-null values across all columns"
        )
    
    with col2:
        # Data freshness
        if 'Project last update' in df.columns:
            latest_update = df['Project last update'].max()
            days_since = (pd.Timestamp.now() - latest_update).days
            st.metric(
                "Data Freshness",
                f"{days_since} days",
                help="Days since the most recent project update"
            )
    
    with col3:
        # Duplicate projects
        duplicates = df['Project name'].duplicated().sum()
        st.metric(
            "Duplicate Projects",
            duplicates,
            help="Number of projects with duplicate names"
        )
    
    st.markdown("---")
    
    # Column-by-Column Analysis
    st.markdown("#### Column Quality Analysis")
    
    quality_data = []
    for col in df.columns:
        if col in ['Project name', 'Team size', 'Project last update', 'Current step name', 'Thématique', 'Type de situation']:
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / len(df)) * 100
            unique_values = df[col].nunique()
            
            # Determine quality status
            if missing_pct == 0:
                status = "🟢 Excellent"
            elif missing_pct < 5:
                status = "🟡 Good"
            elif missing_pct < 15:
                status = "🟠 Fair"
            else:
                status = "🔴 Poor"
            
            quality_data.append({
                'Column': col,
                'Missing Count': missing_count,
                'Missing %': f"{missing_pct:.1f}%",
                'Unique Values': unique_values,
                'Quality Status': status
            })
    
    quality_df = pd.DataFrame(quality_data)
    st.dataframe(quality_df, use_container_width=True)
    
    # Data Distribution Analysis
    st.markdown("#### Data Distribution Issues")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Team size distribution issues
        if 'Team size' in df.columns:
            team_size_clean = pd.to_numeric(df['Team size'], errors='coerce')
            outliers = team_size_clean[(team_size_clean > 20) | (team_size_clean < 1)]
            
            fig = px.histogram(
                team_size_clean.dropna(),
                title="Team Size Distribution",
                nbins=20,
                color_discrete_sequence=[COLORS['verdigris']]
            )
            fig.update_layout(
                xaxis_title="Team Size",
                yaxis_title="Count",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
            if len(outliers) > 0:
                st.warning(f"Found {len(outliers)} team size outliers (>20 or <1)")
    
    with col2:
        # Project age distribution
        if 'Project last update' in df.columns:
            df_with_dates = df.dropna(subset=['Project last update'])
            if not df_with_dates.empty:
                df_with_dates['Days Since Update'] = (pd.Timestamp.now() - df_with_dates['Project last update']).dt.days
                
                fig = px.histogram(
                    df_with_dates['Days Since Update'],
                    title="Project Age Distribution",
                    nbins=20,
                    color_discrete_sequence=[COLORS['bondi_blue']]
                )
                fig.update_layout(
                    xaxis_title="Days Since Last Update",
                    yaxis_title="Count",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                
                stale_projects = (df_with_dates['Days Since Update'] > 90).sum()
                if stale_projects > 0:
                    st.warning(f"Found {stale_projects} projects not updated in 90+ days")
    
    # Data Cleaning Recommendations
    st.markdown("#### 🛠️ Data Cleaning Recommendations")
    
    recommendations = []
    
    # Check for missing values
    missing_data = df.isnull().sum()
    for col, missing_count in missing_data.items():
        if missing_count > 0 and col in ['Project name', 'Team size', 'Current step name']:
            pct = (missing_count / len(df)) * 100
            recommendations.append(f"**{col}**: {missing_count} missing values ({pct:.1f}%) - Consider data collection improvement")
    
    # Check for inconsistent formatting
    if 'Current step name' in df.columns:
        step_variations = df['Current step name'].value_counts()
        if len(step_variations) > 20:  # Many unique steps might indicate inconsistency
            recommendations.append("**Current step name**: High number of unique values - Review for naming consistency")
    
    # Check for data freshness
    if 'Project last update' in df.columns:
        old_data = (pd.Timestamp.now() - df['Project last update']).dt.days.max()
        if old_data > 180:
            recommendations.append(f"**Data freshness**: Oldest data is {old_data} days old - Consider data refresh schedule")
    
    if recommendations:
        for rec in recommendations:
            st.write(f"• {rec}")
    else:
        st.success("✅ No major data quality issues detected!")
    
    # Export cleaned data option
    st.markdown("#### 📥 Export & Format Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Download Quality Report"):
            quality_report = {
                'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': st.session_state.get('file_info', {}).get('source', 'Unknown'),
                'total_records': len(df),
                'data_completeness': f"{completeness:.1f}%",
                'column_analysis': quality_df.to_dict('records'),
                'recommendations': recommendations
            }
            
            # Convert to JSON for download
            import json
            report_json = json.dumps(quality_report, indent=2)
            
            st.download_button(
                "💾 Download Quality Report (JSON)",
                data=report_json,
                file_name=f"data_quality_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📋 Download Cleaned Dataset (Excel)"):
            # Apply the same cleaning that was done during load
            cleaned_df, _ = validate_and_clean_data(df.copy())
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                cleaned_df.to_excel(writer, index=False, sheet_name="Cleaned_Data")
            buffer.seek(0)
            
            st.download_button(
                "💾 Download as Excel",
                data=buffer,
                file_name=f"cleaned_dashboard_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    with col3:
        if st.button("📄 Download Cleaned Dataset (CSV)"):
            # Apply the same cleaning that was done during load
            cleaned_df, _ = validate_and_clean_data(df.copy())
            
            csv_buffer = cleaned_df.to_csv(index=False)
            
            st.download_button(
                "💾 Download as CSV",
                data=csv_buffer,
                file_name=f"cleaned_dashboard_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Data Format Information
    st.markdown("#### 📁 Current Data Source")
    if hasattr(st.session_state, 'file_info'):
        info = st.session_state.file_info
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **Current Source:** {info['format']} format  
            **File:** `{info['source']}`  
            **Size:** {info['size_mb']} MB  
            **Dimensions:** {info['rows']:,} rows × {info['columns']} columns
            """)
        
        with col2:
            st.success("""
            **✅ Format Support:**
            - Excel (.xlsx) - Preferred format
            - CSV (.csv) - Fallback format
            - Automatic detection & loading
            - Cross-format compatibility
            """)
    
    # Format conversion recommendations
    if hasattr(st.session_state, 'file_info') and st.session_state.file_info['format'] == 'CSV':
        st.warning("""
        **💡 Recommendation:** Consider using Excel format for better data type preservation and faster loading.
        You can convert your CSV to Excel using the download options above.
        """)
    
    st.markdown("---")
    st.markdown("*Dashboard automatically detects and loads the best available format (Excel preferred, CSV fallback)*")
`
