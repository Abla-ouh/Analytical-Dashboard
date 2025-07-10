import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Color palette in rgba format
COLORS = {
    "mindaro": "rgba(217, 237, 146, 1)",
    "light_green": "rgba(181, 228, 140, 1)",
    "light_green_2": "rgba(153, 217, 140, 1)",
    "emerald": "rgba(118, 200, 147, 1)",
    "keppel": "rgba(82, 182, 154, 1)",
    "verdigris": "rgba(52, 160, 164, 1)",
    "bondi_blue": "rgba(22, 138, 173, 1)",
    "cerulean": "rgba(26, 117, 159, 1)",
    "lapis_lazuli": "rgba(30, 96, 145, 1)",
    "indigo_dye": "rgba(24, 78, 119, 1)"
}

# Page setup - enable sidebar
st.set_page_config(
    page_title="🚀 Le Mouvement Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"  # Changed to expanded
)
# ────────────────────── DATA LOADING (CACHED) ────────────────────── #
@st.cache_data
def load_data():
    return pd.read_excel("data/GoMvmt.xlsx")

df = load_data()

# ────────────────────── SIDEBAR ────────────────────── #
with st.sidebar:
    st.title("Dashboard Navigation")
    
    # Create a multiselect for charts to display
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
            "Top TOD Advisors",
            "Team Size Distribution",
            "Mentorship Distribution",
            "Type de Situation"
        ]
    )
    
    # Optional filters could be added here
    st.markdown("---")
    st.markdown("**Filters**")
    min_team_size = st.slider(
        "Minimum Team Size",
        min_value=1,
        max_value=20,
        value=1
    )
    
    # Filter data based on sidebar selections
    filtered_df = df[df["Team size"] >= min_team_size]

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
        font-size: 24px;
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
        
    
    </style>
""", unsafe_allow_html=True)

# ────────────────────── HEADER ────────────────────── #
st.markdown('<div class="title-header"> Le Mouvement Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">A real-time visual overview of intrapreneurial projects led within OCP\'s innovation ecosystem.</div>', unsafe_allow_html=True)

# ────────────────────── KPI SECTION ────────────────────── #
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Total Projects</div>
            <div class="metric-value"> {filtered_df.shape[0]}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    last_update = filtered_df["Project last update"].max()
    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Last Update</div>
            <div class="metric-value"> {pd.to_datetime(last_update).date()}</div>
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

# Optional preview
with st.expander("🔍 View Raw Data"):
    st.dataframe(filtered_df)

st.markdown("---")

# ────────────────────── DYNAMIC CHARTS BASED ON SIDEBAR SELECTION ────────────────────── #

if "Projects by Step" in selected_charts:
    # Section 1: Projects by Step (Radial Chart Style)
    st.markdown('<div class="chart-title">Projects Distribution by Step (%)</div>', unsafe_allow_html=True)

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

    # Build Plotly chart
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
        ],
        custom_data=["Project name", "Project last update", "Team size"]
    )

    fig.update_traces(
        texttemplate='%%{text}%%',
        textposition='outside',
        marker_line_color='white',
        marker_line_width=1,
        hovertemplate="""
            <b>%%{y}</b><br>
            Projects: %%{x}<br>
            Last Update: %%{customdata[1]}<br>
            Avg Team Size: %%{customdata[2]}<br><br>
            <b>Sample Projects:</b><br>%%{customdata[0]}<extra></extra>
        """
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

    st.markdown('<div class="chart-title">Projects by Thematic Area (%)</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

if "Top TOD Advisors" in selected_charts:
    # Top TOD Advisors
    advisor_data = filtered_df["TOD Advisor"].dropna()
    top_advisors = advisor_data.value_counts().nlargest(5).reset_index()
    top_advisors.columns = ["Advisor", "Project Count"]

    with st.container():
        st.markdown('<div class="chart-title">Top TOD Advisors</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-subtitle">By number of supported projects (Top 5)</div>', unsafe_allow_html=True)

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
            height=350,
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

