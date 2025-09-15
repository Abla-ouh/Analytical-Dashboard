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
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


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
    Enhanced data validation and cleaning function with improved error handling,
    data type validation, and comprehensive quality scoring.
    """
    cleaning_report = {
        'original_rows': len(data),
        'issues_found': [],
        'fixes_applied': [],
        'warnings': [],
        'final_rows': 0,
        'data_quality_score': 0,
        'column_scores': {}
    }
    
    # Define expected data types and validation rules
    column_rules = {
        "Project name": {
            'type': str,
            'required': True,
            'min_length': 3,
            'max_length': 200,
            'weight': 1.0  # Importance weight for quality score
        },
        "Team size": {
            'type': float,
            'required': True,
            'min_value': 1,
            'max_value': 50,
            'weight': 0.8
        },
        "Project last update": {
            'type': 'datetime',
            'required': True,
            'max_value': pd.Timestamp.now(),
            'min_value': pd.Timestamp.now() - pd.DateOffset(years=5),
            'weight': 0.9
        },
        "Current step name": {
            'type': str,
            'required': True,
            'allowed_values': None,  # Will be populated from data
            'weight': 0.8
        },
        "Thématique": {
            'type': str,
            'required': True,
            'weight': 0.7
        },
        "Type de situation": {
            'type': str,
            'required': True,
            'weight': 0.7
        }
    }
    
    # 1. Validate column presence and data types
    missing_columns = [col for col in column_rules.keys() if col not in data.columns]
    if missing_columns:
        for col in missing_columns:
            cleaning_report['issues_found'].append(f"Critical column missing: {col}")
        raise ValueError(f"Missing critical columns: {', '.join(missing_columns)}")
    
    # Create a deep copy to track changes
    data = data.copy()
    
    # 2. Enhanced validation and cleaning for each column
    for col, rules in column_rules.items():
        col_report = {
            'missing_count': 0,
            'invalid_count': 0,
            'fixed_count': 0,
            'quality_score': 0
        }
        
        # Handle missing values
        missing_mask = data[col].isna()
        col_report['missing_count'] = missing_mask.sum()
        
        if col_report['missing_count'] > 0:
            cleaning_report['issues_found'].append(
                f"{col}: {col_report['missing_count']} missing values"
            )
            
            # Apply column-specific missing value handling
            if col == "Team size":
                median_size = data.loc[~missing_mask, col].median()
                data.loc[missing_mask, col] = median_size
                cleaning_report['fixes_applied'].append(
                    f"{col}: Filled {col_report['missing_count']} missing values with median ({median_size:.1f})"
                )
            elif col == "Current step name":
                data.loc[missing_mask, col] = "Unknown Step"
                cleaning_report['fixes_applied'].append(
                    f"{col}: Filled {col_report['missing_count']} missing values with 'Unknown Step'"
                )
            elif rules['required']:
                cleaning_report['warnings'].append(
                    f"Required column {col} contains missing values that couldn't be automatically fixed"
                )
        
        # Type-specific validation and cleaning
        if rules['type'] == float:
            # Convert to numeric and handle errors
            numeric_data = pd.to_numeric(data[col], errors='coerce')
            invalid_mask = numeric_data.isna() & ~missing_mask
            col_report['invalid_count'] += invalid_mask.sum()
            
            if col_report['invalid_count'] > 0:
                cleaning_report['issues_found'].append(
                    f"{col}: {col_report['invalid_count']} non-numeric values found"
                )
            
            # Apply value range validation
            if 'min_value' in rules:
                below_min = (numeric_data < rules['min_value']) & ~numeric_data.isna()
                if below_min.any():
                    data.loc[below_min, col] = rules['min_value']
                    cleaning_report['fixes_applied'].append(
                        f"{col}: Set {below_min.sum()} values below minimum to {rules['min_value']}"
                    )
            
            if 'max_value' in rules:
                above_max = (numeric_data > rules['max_value']) & ~numeric_data.isna()
                if above_max.any():
                    data.loc[above_max, col] = rules['max_value']
                    cleaning_report['fixes_applied'].append(
                        f"{col}: Set {above_max.sum()} values above maximum to {rules['max_value']}"
                    )
            
            data[col] = numeric_data
            
        elif rules['type'] == 'datetime':
            # Convert to datetime and handle errors
            datetime_data = pd.to_datetime(data[col], errors='coerce')
            invalid_mask = datetime_data.isna() & ~missing_mask
            col_report['invalid_count'] += invalid_mask.sum()
            
            if col_report['invalid_count'] > 0:
                cleaning_report['issues_found'].append(
                    f"{col}: {col_report['invalid_count']} invalid date values found"
                )
            
            # Handle future dates
            future_dates = datetime_data > rules['max_value']
            if future_dates.any():
                data.loc[future_dates, col] = rules['max_value']
                cleaning_report['fixes_applied'].append(
                    f"{col}: Set {future_dates.sum()} future dates to current timestamp"
                )
            
            # Handle dates too far in the past
            old_dates = datetime_data < rules['min_value']
            if old_dates.any():
                cleaning_report['warnings'].append(
                    f"{col}: {old_dates.sum()} dates are more than 5 years old"
                )
            
            data[col] = datetime_data
            
        elif rules['type'] == str:
            # String validation and cleaning
            if 'min_length' in rules:
                too_short = data[col].str.len() < rules['min_length']
                if too_short.any():
                    cleaning_report['warnings'].append(
                        f"{col}: {too_short.sum()} values shorter than minimum length"
                    )
            
            if 'max_length' in rules:
                too_long = data[col].str.len() > rules['max_length']
                if too_long.any():
                    data.loc[too_long, col] = data.loc[too_long, col].str[:rules['max_length']]
                    cleaning_report['fixes_applied'].append(
                        f"{col}: Truncated {too_long.sum()} values to maximum length"
                    )
            
            # Standardize string values
            data[col] = data[col].astype(str).str.strip()
            standardized = data[col].replace(['nan', 'None', 'null', 'NaN'], None)
            changes = (standardized != data[col]).sum()
            if changes > 0:
                cleaning_report['fixes_applied'].append(f"{col}: Standardized {changes} text values")
            data[col] = standardized
        
        # Calculate column quality score
        valid_count = len(data) - col_report['missing_count'] - col_report['invalid_count']
        col_report['quality_score'] = (valid_count / len(data)) * 100
        cleaning_report['column_scores'][col] = col_report
    
    # 3. Calculate overall data quality score with weighted dimensions
    total_weight = sum(rules['weight'] for rules in column_rules.values())
    weighted_scores = []
    
    for col, rules in column_rules.items():
        col_score = cleaning_report['column_scores'][col]['quality_score']
        weighted_scores.append(col_score * rules['weight'])
    
    cleaning_report['data_quality_score'] = round(sum(weighted_scores) / total_weight, 1)
    cleaning_report['final_rows'] = len(data)
    
    # Add severity levels to issues and warnings
    for i, issue in enumerate(cleaning_report['issues_found']):
        severity = 'HIGH' if 'Critical' in issue or 'missing' in issue else 'MEDIUM'
        cleaning_report['issues_found'][i] = f"[{severity}] {issue}"
    
    for i, warning in enumerate(cleaning_report['warnings']):
        cleaning_report['warnings'][i] = f"[LOW] {warning}"
    
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

    .kpi-metric-box {{
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        border: 1px solid #e5e7eb;
        font-size: 20px;
        transition: transform 0.2s;
        margin-bottom: 1.5rem;
    }}

    .kpi-metric-box:hover {{
        transform: scale(1.02);
    }}

    .kpi-metric-title {{
        font-size: 16px;
        font-weight: 500;
        color: {COLORS['lapis_lazuli']};
        margin-bottom: 0.25rem;
    }}

    .kpi-metric-value {{
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
        font-size: 24px;
        font-weight: 700;
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
st.markdown("""
    <style>
    /* Use very specific class names to avoid conflicts */
    .main-dashboard-tabs .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        position: relative;
        background: linear-gradient(to right, #f8f9fa, #ffffff);
        border-radius: 12px 12px 0 0;
        padding: 8px 16px 0 16px;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.03);
        border: 1px solid #f1f5f9;
        border-bottom: none;
    }
    
    /* Custom tab styling */
    .main-dashboard-tabs .stTabs [data-baseweb="tab"] {
        height: 54px;
        font-size: 17px;
        font-weight: 800;
        padding: 5px 32px;
        border-radius: 12px 12px 0 0;
        background: transparent;
        min-width: 170px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        z-index: 1;
        overflow: hidden;
        border: none;
    }
    
    /* Active tab styling with fancy bottom indicator */
    .main-dashboard-tabs .stTabs [aria-selected="true"] {
        font-weight: 900;
        background: white;
        color: #1e3a8a;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* Fancy animated bottom indicator */
    .main-dashboard-tabs .stTabs [aria-selected="true"]::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 10%;
        width: 80%;
        height: 4px;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        border-radius: 4px 4px 0 0;
        animation: slideIn 0.3s forwards cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    /* Hover effect for inactive tabs */
    .main-dashboard-tabs .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background: rgba(255, 255, 255, 0.7);
        transform: translateY(-2px);
    }
    
    /* Tab content area styling */
    .main-dashboard-tabs .stTabs [data-baseweb="tab-panel"] {
        background: white;
        border-radius: 0 0 12px 12px;
        padding: 20px;
        border: 1px solid #f1f5f9;
        border-top: none;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    }
    
    /* Animation for the sliding indicator */
    @keyframes slideIn {
        0% { width: 0; left: 50%; }
        100% { width: 80%; left: 10%; }
    }
    
    /* Tab icons styling */
    .main-dashboard-tabs .stTabs [data-baseweb="tab"] span {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Pulse animation for the active tab */
    .main-dashboard-tabs .stTabs [aria-selected="true"] {
        animation: pulse 2s infinite;
        animation-delay: 0.5s;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }
        50% { box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15); }
        100% { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }
    }
    </style>

    <!-- Add the specific class to the tabs container -->
    <div class="main-dashboard-tabs">
""", unsafe_allow_html=True)

# Create the tabs with enhanced styling and icons
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 **Overview Dashboard**", 
    "📈 **Stages Analysis**", 
    "🧹 **Data Quality**",
    "🤖 **ML Insights**"
])

# Close the specific div container
st.markdown("</div>", unsafe_allow_html=True)

with tab1:
    # ────────────────────── KPI SECTION ────────────────────── #
    st.markdown("###  Key Performance Indicators")
    
    # Add data quality indicators
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(f"""
            <div class="kpi-metric-box">
                <div class="kpi-metric-title">Total Projects</div>
                <div class="kpi-metric-value">{filtered_df.shape[0]}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        last_update = filtered_df["Project last update"].max()
        st.markdown(f"""
            <div class="kpi-metric-box">
                <div class="kpi-metric-title">Last Update</div>
                <div class="kpi-metric-value">{pd.to_datetime(last_update).date()}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        inactive_cutoff = pd.Timestamp.now() - pd.Timedelta(days=60)
        inactive_projects = filtered_df[filtered_df["Project last update"] < inactive_cutoff]
        st.markdown(f"""
            <div class="kpi-metric-box">
                <div class="kpi-metric-title">Inactive Projects (60+ days)</div>
                <div class="kpi-metric-value">⏳ {inactive_projects.shape[0]}</div>
            </div>
        """, unsafe_allow_html=True)

    # Optional preview
    with st.expander("🔍 View Raw Data"):
        st.dataframe(filtered_df)

    st.markdown("---")

    # ────────────────────── DYNAMIC CHARTS BASED ON SIDEBAR SELECTION ────────────────────── #
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


    if "Projects by Step" in selected_charts:
        # Section 1: Projects by Step (Radial Chart Style)
        st.markdown('<div class="chart-title">Projects Distribution By Current Step</div>', unsafe_allow_html=True)

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
            paper_bgcolor='white',
            plot_bgcolor='white',
        )

        st.plotly_chart(fig, use_container_width=True)
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

    # ────────────────────── TEAM SIZE DISTRIBUTION ────────────────────── #
    if "Team Size Distribution" in selected_charts:
        # Team Size Distribution
        st.markdown('<div class="chart-title">Team Size Distribution</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-subtitle">Distribution of team sizes across projects</div>', unsafe_allow_html=True)

        # Prepare data
        team_size_clean = pd.to_numeric(filtered_df["Team size"], errors="coerce").dropna()
        if not team_size_clean.empty:
            avg_size = team_size_clean.mean()
            median_size = team_size_clean.median()
            resource_allocation = team_size_clean.sum()
            outliers = team_size_clean[(team_size_clean > 20) | (team_size_clean < 1)]
            has_outliers = len(outliers) > 0

            # --- KPI Cards ---
            insight_col1, insight_col2, insight_col3 = st.columns(3)

            # Card styling (only needs to be declared once in your app)
            st.markdown("""
                <style>
                .metric-card {
                    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                    border-radius: 16px;
                    padding: 20px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(226, 232, 240, 0.8);
                    height: 100%;
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }
                .metric-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                }
                .metric-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }
                .metric-card:hover::before { opacity: 1; }
                .metric-label { font-size: 14px; font-weight: 500; color: #64748b; margin-bottom: 8px; }
                .metric-value {
                    font-size: 32px; font-weight: 700;
                    background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 4px;
                }
                .metric-subtitle { font-size: 13px; color: #94a3b8; }
                </style>
            """, unsafe_allow_html=True)

            with insight_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Average Team Size</div>
                    <div class="metric-value">{avg_size:.1f}</div>
                    <div class="metric-subtitle">members per project</div>
                </div>
                """, unsafe_allow_html=True)

            with insight_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total Resource Allocation</div>
                    <div class="metric-value">{resource_allocation:.0f}</div>
                    <div class="metric-subtitle">team members across portfolio</div>
                </div>
                """, unsafe_allow_html=True)

            with insight_col3:
                status = "Normal Distribution" if not has_outliers else f"{len(outliers)} Potential Outliers"
                color_grad = "90deg, #15803d 0%, #16a34a 100%" if not has_outliers else "90deg, #b91c1c 0%, #dc2626 100%"

                st.markdown(f"""
                <style>
                .metric-card-status .metric-value {{
                    background: linear-gradient({color_grad});
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .metric-card-status::before {{
                    background: linear-gradient({color_grad});
                }}
                </style>
                <div class="metric-card metric-card-status">
                    <div class="metric-label">Distribution Quality</div>
                    <div class="metric-value">{status}</div>
                    <div class="metric-subtitle">{len(team_size_clean)} projects analyzed</div>
                </div>
                """, unsafe_allow_html=True)

            # --- Enhanced Bar Chart ---
            team_size_counts = team_size_clean.astype(int).value_counts().sort_index()

            fig = go.Figure(data=[go.Bar(
                x=team_size_counts.index,
                y=team_size_counts.values,
                marker=dict(
                    color=COLORS['bondi_blue'],
                    line=dict(color='white', width=1)
                ),
                text=team_size_counts.values,  # Add value labels
                textposition='outside',
                textfont=dict(color=COLORS['indigo_dye'], size=12),
                hovertemplate='<b>Team Size: %{x}</b><br>Count: %{y} projects<extra></extra>'
            )])

            # Add mean and median lines
            fig.add_vline(
                x=avg_size, 
                line_dash="dash", 
                line_color="#f97316",
                annotation=dict(
                    text=f"Mean: {avg_size:.1f}",
                    font=dict(color="#f97316", size=12),
                    bgcolor="rgba(255,255,255,0.8)",
                    borderpad=4
                )
            )
            
            fig.add_vline(
                x=median_size, 
                line_dash="dash", 
                line_color="#0ea5e9",
                annotation=dict(
                    text=f"Median: {median_size:.0f}",
                    font=dict(color="#0ea5e9", size=12),
                    bgcolor="rgba(255,255,255,0.8)",
                    borderpad=4
                )
            )

            fig.update_layout(
                title={
                    'text': "Project Team Size Distribution",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 16, 'color': COLORS['indigo_dye']}
                },
                xaxis_title="Team Size (number of members)",
                yaxis_title="Number of Projects",
                height=400,
                margin=dict(l=50, r=30, t=50, b=50),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color=COLORS['indigo_dye']),
                bargap=0.15,
                xaxis=dict(
                    range=[-0.5, max(team_size_counts.index) + 0.5],  # Ensure bars are centered
                    dtick=1,
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)',
                    zeroline=True,
                    zerolinecolor='rgba(0,0,0,0.2)',
                    zerolinewidth=2,
                    tickfont=dict(size=11)
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)',
                    zeroline=True,
                    zerolinecolor='rgba(0,0,0,0.2)',
                    zerolinewidth=2,
                    rangemode='nonnegative',  # Ensure y-axis starts at 0
                    tickfont=dict(size=11)
                ),
                shapes=[
                    # Add vertical line at x=0
                    dict(
                        type='line',
                        x0=0,
                        y0=0,
                        x1=0,
                        y1=1,
                        yref='paper',
                        line=dict(
                            color='rgba(0,0,0,0.2)',
                            width=2
                        )
                    )
                ]
            )

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

        else:
            st.info("📋 Team size information not available in the dataset.")

    # ────────────────────── MENTORSHIP DISTRIBUTION ────────────────────── #
    
    st.markdown('---')
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
            st.markdown('''
                <div class="chart-title">
                    Mentorship Distribution
                </div>
            ''', unsafe_allow_html=True)
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
        st.markdown('''
            <div class="chart-title">
                Type de Situation Distribution (%)
            </div>
        ''', unsafe_allow_html=True)
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
        "Operating Model": "operating model", 
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
        "Operating Model": [
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

    # ── 7) Project Health Command Center ──
    st.markdown("### Project Portfolio Health Analysis")
    
    # Explanation of the analysis
    with st.expander("ℹ️ Understanding Risk Assessment Methodology", expanded=False):
        st.markdown("#### How Project Risk is Assessed")
        st.markdown("Risk is determined by the number of days since a project's last update. This helps identify projects that are stalled or require attention.")

        # Define risk levels with colors and descriptions
        risk_levels = {
            "Active": {
                "icon": "🟢", "color": "#10B981", "timeframe": "< 30 days",
                "meaning": "Project is on track and progressing as expected."
            },
            "Watch": {
                "icon": "🟡", "color": "#F59E0B", "timeframe": "31-60 days",
                "meaning": "Early warning signs of stalling. Requires monitoring."
            },
            "Action Required": {
                "icon": "🟠", "color": "#F97316", "timeframe": "61-90 days",
                "meaning": "Significant inactivity. Intervention is needed to prevent failure."
            },
            "Critical": {
                "icon": "🔴", "color": "#DC2626", "timeframe": "> 90 days",
                "meaning": "Severe stagnation. Immediate escalation and action are required."
            }
        }

        # Display risk levels in a visually appealing way
        cols = st.columns(4)
        for i, (status, details) in enumerate(risk_levels.items()):
            with cols[i]:
                st.markdown(f"""
                <div style="border: 1px solid {details['color']}; border-left: 5px solid {details['color']}; 
                             border-radius: 5px; padding: 15px; height: 180px; background-color: {details['color']}10;">
                    <h5 style="margin:0; color:{details['color']};">{details['icon']} {status}</h5>
                    <p style="font-size:0.9rem; margin-top:5px;"><strong>Timeframe:</strong> {details['timeframe']}</p>
                    <p style="font-size:0.85rem; color:#4A5568;">{details['meaning']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### How the Portfolio Health Score is Calculated")
        
        col1, col2 = st.columns([2, 1.5])
        
        with col1:
            st.markdown("""
            The score provides a single metric for the overall health of the project portfolio, calculated on a 100-point scale.
            
            **Formula:**
            `Score = 100 - (Total Weighted Deductions / Number of Projects)`
            
            A higher score indicates a healthier portfolio with fewer at-risk projects.
            """)
        with col2:
            st.markdown("""
            **Risk Weightings:**
            - Active: 0 points
            - Watch: 10 points
            - Action Required: 20 points
            - Critical: 40 points
            
            The score is adjusted based on the number of projects in each risk category.
            """)

    
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
    
    if not duration_df.empty:
        st.markdown("### Key Insights & Actions")
        
        # Calculate insights
        high_risk_stages = [
            stage for stage, metrics in stage_risk_metrics.items()
            if metrics['risk_level'] in ['High', 'Critical']
        ]
        bottleneck_stages = [
            stage for stage, metrics in stage_risk_metrics.items()
            if metrics['avg_duration'] > 60  # Stages taking more than 60 days
        ]
        
        # Determine overall health color and message
        if total_risk_score >= 85:
            health_color = "#10B981"  # Green
            health_message = "Portfolio is performing efficiently"
        elif total_risk_score >= 70:
            health_color = "#F59E0B"  # Yellow
            health_message = "Some stages require attention"
        else:
            health_color = "#DC2626"  # Red
            health_message = "Critical bottlenecks detected"

        # Display modern insight cards
        st.markdown(f"""
        <div style='
            background-color: {health_color}08;
            border: 1px solid {health_color}40;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;'>
            <h3 style='color: {health_color}; margin:0;'>
                Portfolio Health Score: {total_risk_score:.0f}/100
            </h3>
            <p style='margin: 10px 0;'>{health_message}</p>
        </div>
        """, unsafe_allow_html=True)

        # Action items based on analysis
        if high_risk_stages or bottleneck_stages:
            col1, col2 = st.columns(2)
            
            with col1:
                if high_risk_stages:
                    st.error("**High Risk Stages Identified**  \n" + 
                            "\n".join([f"• {stage}" for stage in high_risk_stages]))
            
            with col2:
                if bottleneck_stages:
                    st.warning(" **Process Bottlenecks**  \n" + 
                             "\n".join([f"• {stage}" for stage in bottleneck_stages]))

    # Only show the export option if we have data
    if not duration_df.empty:
        # Export functionality with enhanced Excel formatting
        st.markdown("### 📥 Export Analysis")
        
        def create_risk_report():
            # Create summary dataframe
            risk_summary = []
            project_details_list = []  # For detailed project listing
            
            # Include the project type (Business, OM, Ecosystem) in summary
            current_project_type = chosen  # This is the selected project type
            
            for stage, metrics in stage_risk_metrics.items():
                stage_data = duration_df[duration_df['Step'] == stage]
                
                # Create summary stats
                stage_stats = {
                    'Project Type': current_project_type,
                    'Stage': stage,
                    'Average Duration (days)': metrics['avg_duration'],
                    'Risk Level': metrics['risk_level'],
                    'Projects Count': len(stage_data),
                    'High Risk Projects': len(stage_data[stage_data['Duration (days)'] > 60])
                }
                risk_summary.append(stage_stats)

                # Gather detailed project information
                # First ensure stage_data has a Project ID column to use for merging
                # We need to get the Project ID from the original DataFrame 
                # by matching row indices from stage_data to original indices
                
                # Get project data directly using df_stage
                # This is a more direct approach that doesn't rely on index merging
                projects_in_stage = []
                for idx, row in stage_data.iterrows():
                    # Find matching projects in this stage
                    project_matches = df_stage[df_stage.index == idx]
                    if not project_matches.empty:
                        for _, project in project_matches.iterrows():
                            projects_in_stage.append({
                                'Duration (days)': row['Duration (days)'],
                                'Project name': project['Project name'],
                                'Project last update': project['Project last update']
                            })
                
                # Convert to DataFrame
                merged_data = pd.DataFrame(projects_in_stage) if projects_in_stage else pd.DataFrame(
                    columns=['Duration (days)', 'Project name', 'Project last update']
                )
                
                for idx, row in merged_data.iterrows():
                    project_name = row['Project name']
                    duration = row['Duration (days)']
                    risk_level = "Critical" if duration > 90 else "High" if duration > 60 else "Moderate" if duration > 30 else "Low"
                    last_update = row['Project last update'] if pd.notnull(row['Project last update']) else pd.Timestamp.now()
                    now = pd.Timestamp.now()
                    days_inactive = (now - pd.to_datetime(last_update)).days if pd.notnull(last_update) else 0
                    
                    project_details_list.append({
                        'Project Name': project_name,
                        'Project Type': current_project_type,
                        'Current Stage': stage,
                        'Days in Stage': duration,
                        'Days Since Last Update': days_inactive,
                        'Last Updated': last_update.strftime('%Y-%m-%d') if pd.notnull(last_update) else 'Unknown',
                        'Risk Level': risk_level,
                        'Status': 'Needs Immediate Action' if risk_level in ['Critical', 'High'] else 'Monitor' if risk_level == 'Moderate' else 'On Track'
                    })

            return pd.DataFrame(risk_summary), pd.DataFrame(project_details_list)

        # Create and format Excel report
        summary_df, details_df = create_risk_report()
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Get workbook and create formats
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#1a237e',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
            
            wrap_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1
            })
            
            # Risk level formats
            risk_colors = {
                'Critical': workbook.add_format({
                    'bg_color': '#ffcdd2', 
                    'bold': True, 
                    'border': 1,
                    'align': 'center'
                }),
                'High': workbook.add_format({
                    'bg_color': '#fff9c4', 
                    'bold': True, 
                    'border': 1,
                    'align': 'center'
                }),
                'Moderate': workbook.add_format({
                    'bg_color': '#c8e6c9', 
                    'border': 1,
                    'align': 'center'
                }),
                'Low': workbook.add_format({
                    'bg_color': '#e8f5e9', 
                    'border': 1,
                    'align': 'center'
                })
            }
            
            # === SUMMARY SHEET ===
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            summary_sheet = writer.sheets['Summary']
            
            # Format Summary sheet
            for col_num, value in enumerate(summary_df.columns.values):
                summary_sheet.write(0, col_num, value, header_format)
            
            # Set column widths for Summary
            summary_sheet.set_column('A:A', 15)  # Project Type
            summary_sheet.set_column('B:B', 25)  # Stage
            summary_sheet.set_column('C:C', 20)  # Average Duration
            summary_sheet.set_column('D:D', 15)  # Risk Level
            summary_sheet.set_column('E:E', 15)  # Count
            summary_sheet.set_column('F:F', 15)  # High Risk Projects
            
            # Apply risk level formatting to Summary
            for risk_level, format_props in risk_colors.items():
                summary_sheet.conditional_format(1, 3, len(summary_df), 3, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': risk_level,
                    'format': format_props
                })
            
            # === DETAILS SHEET ===
            details_df.to_excel(writer, sheet_name='Project Details', index=False)
            details_sheet = writer.sheets['Project Details']
            
            # Format Details sheet
            for col_num, value in enumerate(details_df.columns.values):
                details_sheet.write(0, col_num, value, header_format)
            
            # Set column widths for Details
            details_sheet.set_column('A:A', 35)  # Project Name
            details_sheet.set_column('B:B', 15)  # Project Type
            details_sheet.set_column('C:C', 25)  # Current Stage
            details_sheet.set_column('D:D', 15)  # Days in Stage
            details_sheet.set_column('E:E', 20)  # Days Since Last Update
            details_sheet.set_column('F:F', 15)  # Last Updated
            details_sheet.set_column('G:G', 15)  # Risk Level
            details_sheet.set_column('H:H', 20)  # Status
            
            # Apply risk level formatting to Details
            for risk_level, format_props in risk_colors.items():
                details_sheet.conditional_format(1, 6, len(details_df), 6, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': risk_level,
                    'format': format_props
                })
            
            # Add conditional formatting for Days Since Last Update
            details_sheet.conditional_format(1, 4, len(details_df), 4, {
                'type': 'cell',
                'criteria': '>',
                'value': 90,
                'format': workbook.add_format({'bg_color': '#ffcdd2', 'bold': True})  # Red
            })
            details_sheet.conditional_format(1, 4, len(details_df), 4, {
                'type': 'cell',
                'criteria': 'between',
                'minimum': 61,
                'maximum': 90,
                'format': workbook.add_format({'bg_color': '#fff9c4'})  # Yellow
            })
            
            # Add borders to all cells
            border_format = workbook.add_format({'border': 1})
            for sheet in [summary_sheet, details_sheet]:
                sheet.conditional_format(1, 0, sheet.dim_rowmax, sheet.dim_colmax, {
                    'type': 'no_blanks',
                    'format': border_format
                })
            
            # Freeze panes and add filters
            summary_sheet.freeze_panes(1, 0)
            details_sheet.freeze_panes(1, 0)
            summary_sheet.autofilter(0, 0, len(summary_df), len(summary_df.columns) - 1)
            details_sheet.autofilter(0, 0, len(details_df), len(details_df.columns) - 1)
            
            # Center text in both sheets except project names
            center_format = workbook.add_format({'align': 'center'})
            for sheet in [summary_sheet, details_sheet]:
                # Get data from the DataFrame
                df = summary_df if sheet.name == 'Summary' else details_df
                for row in range(len(df)):
                    for col in range(len(df.columns)):
                        value = df.iloc[row, col]
                        # Skip project name column and project type column in details
                        if (col != 0 and col != 1) or sheet.name == 'Summary':  
                            # Handle NaN/INF values
                            if isinstance(value, (int, float)):
                                if pd.isna(value) or np.isinf(value):
                                    value = 'N/A'
                            sheet.write(row + 1, col, value, center_format)
            
            # Apply risk level formatting to both sheets
            risk_format_props = {
                'Critical': {'bg_color': '#ffcdd2', 'bold': True, 'border': 1, 'align': 'center'},
                'High': {'bg_color': '#fff9c4', 'bold': True, 'border': 1, 'align': 'center'},
                'Moderate': {'bg_color': '#c8e6c9', 'border': 1, 'align': 'center'},
                'Low': {'bg_color': '#e8f5e9', 'border': 1, 'align': 'center'}
            }
            
            for risk_level, props in risk_format_props.items():
                format = workbook.add_format(props)
                # For Summary sheet
                summary_sheet.conditional_format(1, 3, len(summary_df), 3, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': risk_level,
                    'format': format
                })
                # For Details sheet
                details_sheet.conditional_format(1, 6, len(details_df), 6, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': risk_level,
                    'format': format
                })
            
        # Create download button
        st.download_button(
            label="💾 Download Detailed Risk Analysis Report",
            data=buffer.getvalue(),
            file_name=f"Stage_Duration_Analysis_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download a detailed Excel report with stage duration analysis and project details"
        )
# ────────────────────── DATA QUALITY TAB ──────────────────────
with tab3:
    # Header with executive-focused styling and business context
    st.markdown("""
    <div style='background-color: #f8fafc; padding: 20px; border-radius: 10px; margin-bottom: 20px; 
         border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);'>
        <h2 style='color: #1e3a8a; margin-top: 0;'> Portfolio Data Quality Dashboard</h2>
        <p style='font-size: 16px; color: #475569;'>
            <b>Business Impact:</b> High-quality project data directly impacts decision accuracy, resource allocation efficiency, 
            and portfolio performance monitoring. This dashboard enables data-driven governance and risk mitigation.
        </p>
        <div style='display: flex; margin-top: 10px;'>
            <div style='background-color: #e0f2fe; border-radius: 4px; padding: 5px 10px; margin-right: 10px;'>
                <span style='font-weight: 500; color: #0369a1;'>Updated Weekly</span>
            </div>
            <div style='background-color: #f0fdf4; border-radius: 4px; padding: 5px 10px; margin-right: 10px;'>
                <span style='font-weight: 500; color: #166534;'>Portfolio Oversight</span>
            </div>
            <div style='background-color: #fef3c7; border-radius: 4px; padding: 5px 10px;'>
                <span style='font-weight: 500; color: #92400e;'>Executive Summary</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    
    # Load the original complete dataframe for quality analysis
    original_df = load_data()
    
    # Calculate core metrics with business context using the complete dataset
    total_cells = len(original_df) * len(original_df.columns)
    non_null_cells = original_df.count().sum()
    completeness = (non_null_cells / total_cells) * 100
    
    # Use the original dataframe for all calculations to get accurate quality metrics
    df = original_df.copy()  # Use the original dataframe for calculations
    
    # Create KPI row with improved visuals and business context
    kpi1, kpi2, kpi3 = st.columns([1, 1, 1])

    # Intelligent column mapping with fallback strategies
    column_mapping = {}
    # Get all columns from the original DataFrame
    all_columns = original_df.columns.tolist()
    
    # Categorize columns based on their content and data types from the original dataset
    column_categories = {
        'identification': [],
        'dates': [],
        'numeric': [],
        'categorical': [],
        'text': []
    }
    
    for col in all_columns:
        # Identify date columns
        if 'date' in col.lower() or 'time' in col.lower() or pd.api.types.is_datetime64_any_dtype(original_df[col]):
            column_categories['dates'].append(col)
        # Identify numeric columns
        elif pd.api.types.is_numeric_dtype(original_df[col]):
            column_categories['numeric'].append(col)
        # Identify potential ID/key columns
        elif any(term in col.lower() for term in ['id', 'code', 'key', 'num']):
            column_categories['identification'].append(col)
        # Identify text columns with long content
        elif pd.api.types.is_string_dtype(original_df[col]) and original_df[col].str.len().mean() > 50:
            column_categories['text'].append(col)
        # Everything else is considered categorical
        else:
            column_categories['categorical'].append(col)
    
    # Use all columns for analysis
    critical_columns = all_columns
    expected_columns = critical_columns.copy()  # For backward compatibility
    
    # Multi-strategy column detection to handle various naming conventions
    for expected_col in critical_columns:
        # Strategy 1: Exact match (case-sensitive)
        if expected_col in df.columns:
            column_mapping[expected_col] = expected_col
            continue
            
        # Strategy 2: Case-insensitive match
        matches = [col for col in df.columns if col.lower() == expected_col.lower()]
        if matches:
            column_mapping[expected_col] = matches[0]
            continue
            
        # Strategy 3: Word-based matching (handles spacing/formatting differences)
        expected_words = set(expected_col.lower().split())
        best_match = None
        best_score = 0
        
        for col in df.columns:
            col_words = set(col.lower().split())
            common_words = expected_words.intersection(col_words)
            
            # Calculate match score based on word overlap
            if common_words:
                score = len(common_words) / max(len(expected_words), len(col_words))
                if score > 0.5 and score > best_score:  # Threshold for acceptable match
                    best_score = score
                    best_match = col
        
        if best_match:
            column_mapping[expected_col] = best_match
            
    # Special handling for critical project identifiers
    project_name_col = column_mapping.get('Project name')
    current_step_col = column_mapping.get('Current step name')  # Define current_step_col for consistency calculation
    if not project_name_col:
        # Look for columns with both "project" and "name" or columns with "ID" that might serve as identifiers
        project_cols = [col for col in df.columns if 
                      ('project' in col.lower() and 'name' in col.lower()) or 
                      ('project' in col.lower() and 'id' in col.lower())]
        if project_cols:
            project_name_col = project_cols[0]
            column_mapping['Project name'] = project_name_col
    
    # Find date columns for freshness calculation
    date_col = column_mapping.get('Project last update')
    project_update_col = date_col  # Define project_update_col variable for freshness calculation
    if not date_col:
        # Look for columns with date-related keywords
        date_cols = [col for col in df.columns if any(kw in col.lower() for kw in ['date', 'updated', 'last', 'modified'])]
        if date_cols:
            project_update_col = date_cols[0]  # Assign first matching date columndate_col = date_cols[0]
            column_mapping['Project last update'] = date_col
    
    # Define helper functions for business impact context
    def missing_count_text(score):
        if score >= 95:
            return "Excellent - Very few missing values"
        elif score >= 85:
            return "Good - Some non-critical gaps"
        elif score >= 75:
            return "Fair - Notable data gaps"
        else:
            return "Poor - Significant missing data"
            
    def completeness_impact(score):
        if score >= 95:
            return "High confidence in portfolio analysis"
        elif score >= 85:
            return "Minor impact on decision quality"
        elif score >= 75:
            return "May affect resource allocation decisions"
        else:
            return "High risk of incorrect portfolio analysis"
            
    def freshness_impact(days):
        if days <= 7:
            return "Real-time portfolio visibility"
        elif days <= 30:
            return "Acceptable for monthly reporting"
        elif days <= 60:
            return "May miss recent project changes"
        else:
            return "Strategic decisions based on outdated data"
            
    def duplicates_impact(count):
        if count == 0:
            return "Accurate project count and allocation"
        elif count < 3:
            return "Minor risk of double-counting"
        else:
            return "Significant risk of resource misallocation"
    
    # Calculate comprehensive data quality score based on multiple dimensions
    
    scores = {
        'completeness': 0,  # Missing data
        'validity': 0,      # Data type conformance and valid values
        'freshness': 0,     # Timeliness of updates
        'consistency': 0,   # Format standardization
        'accuracy': 0       # Business rule compliance
    }
    
    # Calculate scores for each dimension
    for col in critical_columns:
        if col in df.columns:
            # Completeness check
            non_null_pct = (df[col].count() / len(df)) * 100
            scores['completeness'] += non_null_pct
            
            # Validity check
            if pd.api.types.is_numeric_dtype(df[col]):
                valid_pct = (df[col].apply(lambda x: isinstance(x, (int, float)) and not pd.isna(x)).sum() / len(df)) * 100
                scores['validity'] += valid_pct
            elif 'date' in col.lower():
                valid_pct = (pd.to_datetime(df[col], errors='coerce').notna().sum() / len(df)) * 100
                scores['validity'] += valid_pct
                
            # Consistency check (format standardization)
            unique_values_pct = (df[col].nunique() / len(df)) * 100
            scores['consistency'] += max(0, 100 - unique_values_pct)  # Lower unique % is better for categorical fields
    
    # Normalize scores
    for key in scores:
        scores[key] = scores[key] / len(critical_columns)
    
    # Freshness score based on latest update
    if project_update_col:
        latest_update = pd.to_datetime(df[project_update_col].max())
        now = pd.Timestamp.now()
        days_since = (now - latest_update).days
        scores['freshness'] = max(0, 100 - (days_since * 1.5))
    
    # Weights for different quality dimensions
    weights = {
        'completeness': 0.3,
        'validity': 0.25,
        'freshness': 0.2,
        'consistency': 0.15,
        'accuracy': 0.1
    }
    
    # Calculate weighted overall score from dimension scores
    overall_quality_score = sum(scores[key] * weights[key] for key in weights)
    
    # Calculate consistency score based on current step values
    if current_step_col and current_step_col in df.columns:
        # Get value counts for the current step column
        step_counts = df[current_step_col].value_counts()
        # Count values that appear only once (potential inconsistencies)
        outlier_values = sum(1 for count in step_counts if count == 1)
        consistency_score = 100 - min(100, (outlier_values / len(df)) * 100)
    else:
        # Default consistency score if no step column is available
        consistency_score = 50  # Neutral score when we can't calculate
        
    # Calculate final weighted score considering completeness, freshness, and consistency
    completeness_score = scores['completeness']
    freshness_score = scores['freshness']
    
    overall_quality_score = (
        (completeness_score * 0.5) + 
        (freshness_score * 0.3) + 
        (consistency_score * 0.2)
    )
    
    # Score to grade conversion for executive clarity
    grade = "A+" if overall_quality_score >= 95 else \
            "A" if overall_quality_score >= 90 else \
            "B+" if overall_quality_score >= 85 else \
            "B" if overall_quality_score >= 80 else \
            "C+" if overall_quality_score >= 75 else \
            "C" if overall_quality_score >= 70 else \
            "D" if overall_quality_score >= 60 else "F"
    
    # Color coding for visual impact
    score_color = "#15803d" if overall_quality_score >= 90 else \
                 "#0284c7" if overall_quality_score >= 80 else \
                 "#ea580c" if overall_quality_score >= 70 else \
                 "#b91c1c"
    
    with kpi1:
        completeness_color = "#15803d" if completeness_score >= 95 else \
                            "#0284c7" if completeness_score >= 85 else \
                            "#ea580c" if completeness_score >= 75 else "#b91c1c"
        
        st.markdown(f"""
        <div style='background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 4px rgba(0,0,0,0.1);
             height: 100%; border: 1px solid #e2e8f0;'>
            <div style='font-size: 14px; color: #64748b; margin-bottom: 5px;'>Data Completeness</div>
            <div style='font-size: 28px; font-weight: bold; color: {completeness_color};'>{completeness_score:.1f}%</div>
            <div style='margin-top: 10px; font-size: 13px; color: #64748b;'>
                <span style='display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: {completeness_color}; margin-right: 5px;'></span>
                {missing_count_text(completeness_score)}
            </div>
            <div style='margin-top: 10px; font-size: 12px; color: #64748b;'>
                <b>Business Impact:</b> {completeness_impact(completeness_score)}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        freshness_color = "#15803d" if freshness_score >= 95 else \
                         "#0284c7" if freshness_score >= 85 else \
                         "#ea580c" if freshness_score >= 75 else "#b91c1c"
                         
        if project_update_col:
            latest_update = pd.to_datetime(df[project_update_col].max())
            now = pd.Timestamp.now()
            days_since = (now - latest_update).days
            
            st.markdown(f"""
            <div style='background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0px 4px 4px rgba(0,0,0,0.1);
                 height: 100%; border: 1px solid #e2e8f0;'>
                <div style='font-size: 14px; color: #64748b; margin-bottom: 5px;'>Data Freshness</div>
                <div style='font-size: 28px; font-weight: bold; color: {freshness_color};'>{days_since} days</div>
                <div style='margin-top: 10px; font-size: 13px; color: #64748b;'>
                    <span style='display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: {freshness_color}; margin-right: 5px;'></span>
                    Since last portfolio update
                </div>
                <div style='margin-top: 10px; font-size: 12px; color: #64748b;'>
                    <b>Business Impact:</b> {freshness_impact(days_since)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0px 4px 4px rgba(0,0,0,0.1);
                 height: 100%; border: 1px solid #e2e8f0;'>
                <div style='font-size: 14px; color: #64748b; margin-bottom: 5px;'>Data Freshness</div>
                <div style='font-size: 28px; font-weight: bold; color: #94a3b8;'>N/A</div>
                <div style='margin-top: 10px; font-size: 13px; color: #64748b;'>
                    <span style='display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #94a3b8; margin-right: 5px;'></span>
                    Update date column not found
                </div>
                <div style='margin-top: 10px; font-size: 12px; color: #64748b;'>
                    <b>Action Required:</b> Add date tracking to improve portfolio oversight
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    
    with kpi3:
        if project_name_col:
            unique_projects = df[project_name_col].nunique()
            duplicates = df[project_name_col].duplicated().sum()
            duplication_rate = (duplicates / len(df)) * 100 if len(df) > 0 else 0
            
            uniqueness_color = "#15803d" if duplication_rate == 0 else \
                              "#0284c7" if duplication_rate < 2 else \
                              "#ea580c" if duplication_rate < 5 else "#b91c1c"
            
            st.markdown(f"""
            <div style='background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 4px rgba(0,0,0,0.1);
                 height: 100%; border: 1px solid #e2e8f0;'>
                <div style='font-size: 14px; color: #64748b; margin-bottom: 5px;'>Project Uniqueness</div>
                <div style='font-size: 28px; font-weight: bold; color: {uniqueness_color};'>{unique_projects}</div>
                <div style='margin-top: 10px; font-size: 13px; color: #64748b;'>
                    <span style='display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: {uniqueness_color}; margin-right: 5px;'></span>
                    Unique projects ({duplicates} duplicates)
                </div>
                <div style='margin-top: 10px; font-size: 12px; color: #64748b;'>
                    <b>Business Impact:</b> {duplicates_impact(duplicates)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                 height: 100%; border: 1px solid #e2e8f0;'>
                <div style='font-size: 14px; color: #64748b; margin-bottom: 5px;'>Project Uniqueness</div>
                <div style='font-size: 28px; font-weight: bold; color: #94a3b8;'>N/A</div>
                <div style='margin-top: 10px; font-size: 13px; color: #64748b;'>
                    <span style='display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #94a3b8; margin-right: 5px;'></span>
                    Project ID column not found
                </div>
                <div style='margin-top: 10px; font-size: 12px; color: #64748b;'>
                    <b>Action Required:</b> Implement project identifiers for proper tracking
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            
    st.markdown("----")
    
    # Enhanced Column Quality Analysis with business context
    st.markdown("""
    <div style='margin-bottom: 20px;'>
        <h3 style='font-weight: 600; margin-bottom: 8px;'> Column Quality Analysis</h3>
        <p style='color: #475569; font-size: 15px;'>
            Detailed assessment of critical fields that drive portfolio analysis and executive reporting.
            Fields with quality issues directly impact the reliability of portfolio metrics.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load the original complete dataframe for quality analysis
    original_df = load_data()
    
    # Calculate more sophisticated column quality metrics for all columns in the original DataFrame
    quality_data = []
    
    # Function to get column description based on common naming patterns
    def get_column_description(col_name):
        col_lower = col_name.lower()
        
        # Dictionary of common column patterns and their descriptions
        descriptions = {
            'id': 'Unique identifier for the record',
            'date': 'Date/time information',
            'name': 'Name or title field',
            'status': 'Current state or status',
            'type': 'Classification or category',
            'description': 'Detailed text description',
            'priority': 'Priority or importance level',
            'size': 'Size or magnitude measure',
            'count': 'Numeric count or quantity',
            'department': 'Organizational unit',
            'cost': 'Financial or cost information',
            'duration': 'Time duration or period',
            'location': 'Physical or virtual location',
            'owner': 'Responsible person or team',
            'target': 'Goal or target value',
            'actual': 'Actual or realized value',
            'comment': 'Additional notes or comments',
            'email': 'Email address',
            'phone': 'Phone number',
            'address': 'Physical address',
            'category': 'Classification category',
            'score': 'Numeric score or rating',
            'percentage': 'Percentage value',
            'flag': 'Boolean indicator',
            'version': 'Version number or identifier'
        }
        
        # Check for exact matches first
        for key, desc in descriptions.items():
            if key == col_lower:
                return desc
                
        # Then check for partial matches
        for key, desc in descriptions.items():
            if key in col_lower:
                return desc
                
        # Default description if no match found
        return 'Field containing project-related information'
    
    # Function to detect outliers with business-appropriate thresholds
    def detect_outliers(series):
        if pd.api.types.is_numeric_dtype(series):
            clean_series = series.dropna()
            if len(clean_series) == 0:
                return []
            
        q1 = clean_series.quantile(0.25)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        return clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)].index.tolist()
    
    for col in original_df.columns:
        # Get column statistics
        missing_count = original_df[col].isnull().sum()
        total_count = len(original_df)
        completeness = ((total_count - missing_count) / total_count) * 100
        
        # Initialize variables
        data_type = "Unknown"
        invalid_count = 0
        invalid_percentage = 0
        color = "#94A3B8"
        
        # Detect data type and validate accordingly
        if pd.api.types.is_numeric_dtype(original_df[col]):
            # Check for numeric validity
            invalid_count = original_df[col].apply(lambda x: not (isinstance(x, (int, float)) or pd.isna(x))).sum()
            outliers = detect_outliers(original_df[col])
            invalid_count += len(outliers)
            data_type = "Numeric"
            
        elif pd.api.types.is_datetime64_any_dtype(original_df[col]) or 'date' in col.lower():
            # Check for date validity
            data_type = "Date"
            datetime_col = pd.to_datetime(original_df[col], errors='coerce')
            invalid_count = datetime_col.isna().sum() - missing_count
            
            # Check for future dates if it's not a target/plan date
            if not any(term in col.lower() for term in ['target', 'plan', 'due']):
                now = pd.Timestamp.now()
                future_dates = original_df[datetime_col > now].shape[0]
                invalid_count += future_dates
                
        else:
            # For text/categorical, check for standardization
            value_counts = original_df[col].value_counts()
            unique_ratio = len(value_counts) / (total_count - missing_count) if total_count > missing_count else 0
            
            if unique_ratio > 0.8:  # If more than 80% values are unique, likely free text
                data_type = "Text"
                # Check for extremely short or long values
                if isinstance(original_df[col].dtype, pd.StringDtype):
                    lengths = original_df[col].str.len()
                    avg_len = lengths.mean()
                    invalid_count = original_df[col].apply(lambda x: len(str(x)) < 0.2 * avg_len or len(str(x)) > 5 * avg_len).sum()
            else:
                data_type = "Categorical"
                # Check for minor variations (case, spacing)
                cleaned_values = original_df[col].str.strip().str.lower() if isinstance(original_df[col].dtype, pd.StringDtype) else original_df[col]
                invalid_count = len(value_counts) - len(cleaned_values.value_counts())
        
        # Calculate quality metrics
        invalid_percentage = (invalid_count / total_count) * 100 if total_count > 0 else 0
        
        # Determine quality status
        if completeness >= 95 and invalid_percentage <= 5:
            quality_status = "🟢 Excellent"
            color = "#15803d"
        elif completeness >= 85 and invalid_percentage <= 10:
            quality_status = "🟡 Good"
            color = "#0284c7"
        elif completeness >= 75 and invalid_percentage <= 15:
            quality_status = "🟠 Fair"
            color = "#ea580c"
        else:
            quality_status = "🔴 Poor"
            color = "#b91c1c"
        
        # Determine business criticality based on content and usage
        criticality = "High" if any(term in col.lower() for term in 
                                  ['id', 'name', 'date', 'status', 'priority', 'type', 'department']) else \
                     "Medium" if any(term in col.lower() for term in 
                                   ['description', 'note', 'comment', 'size', 'count']) else "Low"
        
        quality_data.append({
            'Field Name': col,
            'System Field': col,
            'Data Type': data_type,
            'Missing Count': missing_count,
            'Completeness %': f"{completeness:.1f}",
            'Invalid %': f"{invalid_percentage:.1f}",
            'Quality Status': quality_status,
            'Business Criticality': criticality,
            'Color': color
        })
    
    
    quality_df = pd.DataFrame(quality_data)
    
    # Function to detect outliers with business-appropriate thresholds
    def detect_outliers(series):
        clean_series = series.dropna()
        if len(clean_series) == 0:
            return []
            
        q1 = clean_series.quantile(0.25)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        return clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)].index.tolist()
        
    # Create a more executive-friendly visualization
    col_details, col_viz = st.columns([3, 2])
    
    with col_details:
        # Display the dataframe with enhanced styling for executives
        st.dataframe(
            quality_df[['Field Name', 'System Field', 'Missing Count', 'Completeness %', 'Invalid %', 'Quality Status', 'Business Criticality']],
            use_container_width=True,
            height=320,
            column_config={
                "Field Name": st.column_config.TextColumn("Business Field", help="Standard field name used in business reporting"),
                "System Field": st.column_config.TextColumn("System Field", help="Actual field name in the data source"),
                "Missing Count": st.column_config.NumberColumn("Missing Values", help="Number of records with missing values"),
                "Completeness %": st.column_config.ProgressColumn("Completeness", help="Percentage of records with valid values", format="%s", min_value=0, max_value=100),
                "Invalid %": st.column_config.ProgressColumn("Invalid Data", help="Percentage of records with invalid or inconsistent values", format="%s", min_value=0, max_value=100),
                "Quality Status": st.column_config.TextColumn("Quality Rating", help="Overall quality assessment of the field"),
                "Business Criticality": st.column_config.SelectboxColumn("Business Impact", help="Importance of this field for business decisions", options=["High", "Medium", "Low"])
            },
            hide_index=True
        )
        
        # Add business context for critical fields
        st.markdown("""
        <div style='margin-top: 10px; font-size: 13px; color: #64748b; background-color: #f8fafc; padding: 10px; border-radius: 5px;'>
            <b>📝 Field Importance:</b> Fields with <span style='color: #ef4444; font-weight: 500;'>High</span> business criticality 
            directly impact portfolio analysis and executive reporting. Quality issues in these fields should be addressed as a priority.
        </div>
        """, unsafe_allow_html=True)
    
    with col_viz:
        # Create a more impactful completion percentage visual with business context
        # Sort by completeness for better visualization
        plot_df = quality_df.copy()
        plot_df['Completeness'] = plot_df['Completeness %'].str.rstrip('%').astype(float)
        plot_df = plot_df.sort_values('Completeness', ascending=False)
        
        # Create a horizontal bar chart with business context
        fig = go.Figure()
        
        for idx, row in plot_df.iterrows():
            completeness = float(row['Completeness %'].replace('%', ''))
            criticality = row['Business Criticality']
            
            # Adjust bar appearance based on business criticality
            marker_line_width = 2 if criticality == "High" else 1
            marker_line_color = "#000000" if criticality == "High" else "#ffffff"
            opacity = 1.0 if criticality == "High" else 0.8
            
            fig.add_trace(go.Bar(
                y=[row['Field Name']],
                x=[completeness],
                orientation='h',
                name=row['Field Name'],
                marker=dict(
                    color=row['Color'],
                    line=dict(color=marker_line_color, width=marker_line_width),
                    opacity=opacity
                ),
                hovertemplate=(
                    f"<b>{row['Field Name']}</b><br>" +
                    f"Completeness: {row['Completeness %']}<br>" +
                    f"Missing: {row['Missing Count']} records<br>" +
                    f"Invalid: {row['Invalid %']}<br>" +
                    f"Status: {row['Quality Status']}<br>" +
                    f"Criticality: {criticality}<extra></extra>"
                ),
                text=row['Completeness %'],
                textposition='auto'
            ))
        
        fig.update_layout(
            title={
                'text': "Data Field Quality Assessment",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 16, 'color': '#1e3a8a', 'family': 'Arial'}
            },
            xaxis=dict(
                title="Completeness %",
                range=[0, 100],
                ticksuffix="%",
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                zeroline=True,
                zerolinecolor='rgba(0,0,0,0.1)',
            ),
            yaxis=dict(
                title="",
                autorange="reversed",
                tickfont={'size': 12}
            ),
            plot_bgcolor='white',
            margin=dict(l=0, r=0, t=40, b=0),
            height=320,
            showlegend=False,
            barmode='group',
            bargap=0.15,
            annotations=[
                dict(
                    x=25,
                    y=-0.15,
                    xref="x",
                    yref="paper",
                    text="Poor Quality",
                    showarrow=False,
                    font=dict(size=10, color="#b91c1c"),
                    align="center",
                ),
                dict(
                    x=75,
                    y=-0.15,
                    xref="x",
                    yref="paper",
                    text="Good Quality",
                    showarrow=False,
                    font=dict(size=10, color="#15803d"),
                    align="center",
                )
            ]
        )
        
        # Add visual indicators for quality thresholds
        fig.add_shape(
            type="rect",
            x0=0, y0=0,
            x1=70, y1=1,
            yref="paper",
            fillcolor="rgba(239, 68, 68, 0.07)",
            layer="below",
            line_width=0,
        )
        
        fig.add_shape(
            type="rect",
            x0=70, y0=0,
            x1=90, y1=1,
            yref="paper",
            fillcolor="rgba(234, 179, 8, 0.07)",
            layer="below",
            line_width=0,
        )
        
        fig.add_shape(
            type="rect",
            x0=90, y0=0,
            x1=100, y1=1,
            yref="paper",
            fillcolor="rgba(21, 128, 61, 0.07)",
            layer="below",
            line_width=0,
        )
        
        st.plotly_chart(fig, use_container_width=True, key="data_field_quality_chart")

    st.markdown("----")
    
    # Export quality report with actionable insights
    st.markdown("### Quality Report Export")
    
    # Create tabs for different export options
    export_tab1, export_tab2, export_tab3 = st.tabs(["📊 Quality Report", "🔄 Cleaned Dataset", "📘 Data Dictionary"])
    
    with export_tab1:
        st.markdown("""
        The quality report provides a comprehensive assessment of your project data quality.
        It includes all metrics, findings, and recommendations for improving data reliability.
        """)
        
        if st.button("Generate Quality Report", key="generate_quality_report_btn_tab1"):
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
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "💾 Download as JSON",
                    data=report_json,
                    file_name=f"data_quality_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_json_report_tab1"
                )
            
            with col2:
                # Create a PDF-friendly format (simulated)
                st.download_button(
                    "📄 Download as PDF",
                    data=report_json,  # Would be replaced with actual PDF in production
                    file_name=f"data_quality_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="download_pdf_report_tab1"
                )
    
    with export_tab2:
        st.markdown("### 🔄 Export Complete Dataset")
        st.markdown("Download the complete dataset with all columns and rows.")
        
        # Load the original complete dataframe again to ensure we have all data
        original_df = load_data()
        
        # Show preview of the data with counts of rows and columns
        st.markdown(f"**Preview of export data ({len(original_df)} rows × {len(original_df.columns)} columns)**")
        st.dataframe(original_df.head(), use_container_width=True)
        
        # Information about what's being exported
        st.info(f"""
        📋 **Export Information**
        - All {len(original_df)} rows will be included
        - All {len(original_df.columns)} columns will be included
        - No filtering is applied to the data
        - Choose Excel format for best data type preservation
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Create Excel file in memory with the complete dataframe
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Export the complete dataframe with all columns and rows
                original_df.to_excel(writer, index=False, sheet_name="Complete Dataset")
            
            buffer.seek(0)
            
            st.download_button(
                label=" Download Complete Dataset (Excel)",
                data=buffer,
                file_name=f"complete_dashboard_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_complete"
            )
        
        with col2:
            # Create CSV in memory with the complete dataframe
            csv_buffer = df.to_csv(index=False)
            
            st.download_button(
                label="Download Complete Dataset (CSV)",
                data=csv_buffer,
                file_name=f"complete_dashboard_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_csv_complete"
            )
    
    with export_tab3:
        st.markdown("""
        The data dictionary provides comprehensive documentation of all data fields,
        including definitions, acceptable values, and business context for executives.
        """)
        
        # Load the original complete dataframe for the data dictionary
        original_df = load_data()
        
        # Display a data dictionary with all columns from the original dataset
        dict_data = []
        # Use all columns from the original DataFrame
        for col in original_df.columns:
            # Get data type and sample values
            data_type = str(original_df[col].dtype)
            # Convert sample values to strings to avoid type conversion issues
            sample_vals = [str(val) for val in original_df[col].dropna().head(3).tolist()]
            sample_str = ', '.join(sample_vals) if sample_vals else 'No samples available'

            dict_data.append({
                "Field Name": str(col),
                "System Field": str(col),  # Use the actual column name as is
                "Data Type": str(data_type),
                "Description": str(get_column_description(col)) if 'get_column_description' in globals() else 'Field for project data',
                "Required": "Yes" if any(term in col.lower() for term in ['id', 'name', 'date', 'status', 'priority', 'type']) else "No",
                "Example Values": sample_str
            })
        
        # Create DataFrame with explicit string dtypes
        dict_df = pd.DataFrame(dict_data).astype(str)
        st.dataframe(dict_df, use_container_width=True,
            column_config={
                "Field Name": st.column_config.TextColumn("Field Name", help="Business name of the field"),
                "System Field": st.column_config.TextColumn("System Field", help="Technical name in the dataset"),
                "Data Type": st.column_config.TextColumn("Data Type", help="Type of data stored in the field"),
                "Description": st.column_config.TextColumn("Description", help="Field description and purpose"),
                "Required": st.column_config.TextColumn("Required", help="Whether the field is mandatory"),
                "Example Values": st.column_config.TextColumn("Example Values", help="Sample values from the dataset")
            })
        
        # Add download button for the data dictionary
        if st.button("Download Data Dictionary", key="download_dict_btn_tab3"):
            dict_buffer = io.BytesIO()
            with pd.ExcelWriter(dict_buffer, engine='openpyxl') as writer:
                dict_df.to_excel(writer, index=False, sheet_name="Data_Dictionary")
            dict_buffer.seek(0)
            
            st.download_button(
                "💾 Download Data Dictionary",
                data=dict_buffer,
                file_name=f"project_data_dictionary_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_dict_file_tab3"
            )

    # Data Source Information with improved styling
    st.markdown("### 📁 Data Source Information")

    # Get data source information if not already present
    if not hasattr(st.session_state, 'file_info') and 'df' in locals():
        # If dataset is loaded but file_info not set, create it
        st.session_state.file_info = {
            'source': 'Loaded dataset',
            'format': 'DataFrame',
            'size_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'rows': len(df),
            'columns': len(df.columns)
        }

    # Refresh file information from the currently loaded dataset
    if hasattr(st.session_state, 'file_info'):
        # Update size and dimensions from current dataset
        st.session_state.file_info.update({
            'size_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'rows': len(df),
            'columns': len(df.columns)
        })
    if hasattr(st.session_state, 'file_info'):
        info = st.session_state.file_info

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"""
            <div style='background-color: #E0F2FE; padding: 15px; border-radius: 5px;'>
                <h4 style='margin:0; color: #0369A1;'>Current Data Source</h4>
                <p style='margin:5px 0;'><b>Format:</b> {info['format']}</p>
                <p style='margin:5px 0;'><b>File:</b> <code>{info['source']}</code></p>
                <p style='margin:5px 0;'><b>Size:</b> {info['size_mb']} MB</p>
                <p style='margin:5px 0;'><b>Dimensions:</b> {info['rows']:,} rows × {info['columns']} columns</p>
                <p style='margin:5px 0;'><b>Last Updated:</b> {pd.Timestamp.now().strftime('%Y-%m-%d')}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style='background-color: #DCFCE7; padding: 15px; border-radius: 5px;'>
                <h4 style='margin:0; color: #166534;'>Data Governance</h4>
                <p style='margin:5px 0;'><b>Owner:</b> TBD</p>
                <p style='margin:5px 0;'><b>Update Frequency:</b> TBD</p>
                <p style='margin:5px 0;'><b>Quality Rules:</b> Automated validation</p>
                <p style='margin:5px 0;'><b>Format Support:</b> Excel (.xlsx), CSV (.csv)</p>
                <p style='margin:5px 0;'><b>Storage:</b> Centralized data repository</p>
            </div>
            """, unsafe_allow_html=True)

        # Format recommendation
        if info['format'] == 'CSV':
            st.markdown("""
            <div style='background-color: #FEF3C7; padding: 15px; border-radius: 5px; margin-top: 20px;'>
                <h4 style='margin:0; color: #92400E;'>💡 Format Recommendation</h4>
                <p style='margin:5px 0;'>
                    For better data type preservation, consider converting your CSV to Excel using the download options in the Cleaned Dataset tab.
                </p>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("No data source loaded yet. Please upload a dataset to view this information.")

    
    st.markdown("---")
    
    # Footer with information
    st.markdown("""
    <div style='text-align: center; color: #64748B; padding: 10px; font-size: 12px;'>
        Dashboard automatically detects and loads the best available format (Excel preferred, CSV fallback).<br>
        Data quality rules and definitions follow industry standards for project portfolio management.
    </div>
    """, unsafe_allow_html=True)

# ────────────────────── ML INSIGHTS TAB ────────────────────── #
with tab4:
    st.markdown("## 🤖 Machine Learning Insights")
    st.markdown("""
        <div style='background-color: #f8fafc; padding: 20px; border-radius: 10px; margin-bottom: 20px; 
             border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);'>
            <h3 style='color: #1e3a8a; margin-top: 0;'>Predictive Analytics Dashboard</h3>
            <p style='color: #475569;'>
                Leverage machine learning to gain insights into project trends, predict outcomes, 
                and optimize resource allocation.
            </p>
        </div>
    """, unsafe_allow_html=True)

