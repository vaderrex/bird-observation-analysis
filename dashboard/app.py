"""
Bird Species Observation Analysis — Streamlit Dashboard
Phase 4: Interactive Visualization
Run: streamlit run app.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import duckdb
from plotly.subplots import make_subplots
import os
from pathlib import Path

# ── Directory Setup ────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent

# ── Data Loading Function ──────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """Load and cache bird observation data."""
    
    # Try multiple possible locations for the CSV
    csv_candidates = [
        REPO_ROOT / "bird_observations_clean.csv",
        SCRIPT_DIR / "bird_observations_clean.csv",
        Path("bird_observations_clean.csv"),
        REPO_ROOT / "data" / "bird_observations_clean.csv",
    ]
    
    csv_path = None
    for candidate in csv_candidates:
        if candidate.exists():
            csv_path = candidate
            break
    
    if csv_path and csv_path.exists():
        try:
            df = pd.read_csv(csv_path, parse_dates=["Observation_Date"])
            
            # Add temporal features if not present
            if "Date" not in df.columns and "Observation_Date" in df.columns:
                df["Date"] = df["Observation_Date"]
            if "Month" not in df.columns and "Observation_Date" in df.columns:
                df["Month"] = df["Observation_Date"].dt.month
            if "Month_Name" not in df.columns and "Observation_Date" in df.columns:
                df["Month_Name"] = df["Observation_Date"].dt.strftime("%b")
            if "Season" not in df.columns and "Month" in df.columns:
                df["Season"] = df["Month"].map(
                    {12:"Winter",1:"Winter",2:"Winter",
                     3:"Spring",4:"Spring",5:"Spring",
                     6:"Summer",7:"Summer",8:"Summer",
                     9:"Autumn",10:"Autumn",11:"Autumn"}
                )
            
            if "Start_Time" in df.columns and "Start_Hour" not in df.columns:
                df["Start_Hour"] = pd.to_datetime(
                    df["Start_Time"].astype(str), format="%H:%M:%S", errors="coerce"
                ).dt.hour
            
            if "Sky" in df.columns and "Sky_Clean" not in df.columns:
                SKY_MAP = {"Clear or Few Clouds":"Clear","Partly Cloudy":"Partly Cloudy",
                           "Cloudy/Overcast":"Overcast","Mist/Drizzle":"Mist/Drizzle",
                           "Fog":"Fog","Rain":"Rain"}
                df["Sky_Clean"] = df["Sky"].str.strip().map(SKY_MAP).fillna("Other")
            
            if "At_Risk" not in df.columns:
                df["At_Risk"] = (
                    (df.get("PIF_Watchlist_Status", False) == True) |
                    (df.get("Regional_Stewardship_Status", False) == True)
                )
            
            df["Year"] = df["Year"].astype("Int64")
            return df
        except Exception as e:
            st.warning(f"Failed to load CSV: {e}")
    
    # Fallback: build from Excel files
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Try multiple locations for Excel files
    excel_candidates = [
        (REPO_ROOT / "Bird_Monitoring_Data_FOREST.XLSX", REPO_ROOT / "Bird_Monitoring_Data_GRASSLAND.XLSX"),
        (SCRIPT_DIR / "Bird_Monitoring_Data_FOREST.XLSX", SCRIPT_DIR / "Bird_Monitoring_Data_GRASSLAND.XLSX"),
        (REPO_ROOT / "data" / "Bird_Monitoring_Data_FOREST.XLSX", REPO_ROOT / "data" / "Bird_Monitoring_Data_GRASSLAND.XLSX"),
        (Path("Bird_Monitoring_Data_FOREST.XLSX"), Path("Bird_Monitoring_Data_GRASSLAND.XLSX")),
    ]
    
    forest_path = None
    grassland_path = None
    
    for forest_candidate, grassland_candidate in excel_candidates:
        if forest_candidate.exists() and grassland_candidate.exists():
            forest_path = forest_candidate
            grassland_path = grassland_candidate
            break
    
    if not forest_path or not grassland_path:
        # Show available files for debugging
        st.error("❌ Data files not found!")
        st.write("**Looking in these locations:**")
        st.write(f"- Script directory: `{SCRIPT_DIR}`")
        st.write(f"- Repository root: `{REPO_ROOT}`")
        st.write("\n**Files in repository root:**")
        if REPO_ROOT.exists():
            files = list(REPO_ROOT.glob("*"))
            st.write([f.name for f in files if f.is_file()])
        st.write("\n**Files in dashboard directory:**")
        if SCRIPT_DIR.exists():
            files = list(SCRIPT_DIR.glob("*"))
            st.write([f.name for f in files if f.is_file()])
        st.stop()
    
    def ingest(path, label):
        sheets = pd.read_excel(path, sheet_name=None)
        frames = [df.assign(Source_Sheet=k, Habitat_Source=label)
                  for k, df in sheets.items() if not df.empty]
        return pd.concat(frames, ignore_index=True)
    
    df_f = ingest(forest_path, "Forest")
    df_g = ingest(grassland_path, "Grassland")
    
    if "NPSTaxonCode" in df_f.columns:
        df_f.rename(columns={"NPSTaxonCode": "TaxonCode"}, inplace=True)
    if "NPSTaxonCode" in df_g.columns:
        df_g.rename(columns={"NPSTaxonCode": "TaxonCode"}, inplace=True)
    
    df = pd.concat([df_f, df_g], ignore_index=True)
    
    # Handle date column naming variations
    if "Date" in df.columns and "Observation_Date" not in df.columns:
        df.rename(columns={"Date": "Observation_Date"}, inplace=True)
    
    if "Observation_Date" in df.columns:
        df["Observation_Date"] = pd.to_datetime(
            df["Observation_Date"], errors="coerce"
        )
        # Add temporal features
        df["Date"] = df["Observation_Date"]  # Alias for compatibility
        df["Month"] = df["Observation_Date"].dt.month
        df["Month_Name"] = df["Observation_Date"].dt.strftime("%b")
        df["Season"] = df["Month"].map(
            {12:"Winter",1:"Winter",2:"Winter",
             3:"Spring",4:"Spring",5:"Spring",
             6:"Summer",7:"Summer",8:"Summer",
             9:"Autumn",10:"Autumn",11:"Autumn"}
        )
    
    # Additional processing
    if "Start_Time" in df.columns:
        df["Start_Hour"] = pd.to_datetime(
            df["Start_Time"].astype(str), format="%H:%M:%S", errors="coerce"
        ).dt.hour
    
    df["Temperature"] = pd.to_numeric(df.get("Temperature"), errors="coerce")
    df["Humidity"] = pd.to_numeric(df.get("Humidity"), errors="coerce")
    
    if "Sex" in df.columns:
        df["Sex"] = df["Sex"].fillna("Undetermined").str.strip()
    
    if "Sky" in df.columns:
        SKY_MAP = {"Clear or Few Clouds":"Clear","Partly Cloudy":"Partly Cloudy",
                   "Cloudy/Overcast":"Overcast","Mist/Drizzle":"Mist/Drizzle",
                   "Fog":"Fog","Rain":"Rain"}
        df["Sky_Clean"] = df["Sky"].str.strip().map(SKY_MAP).fillna("Other")
    
    df["At_Risk"] = (
        (df.get("PIF_Watchlist_Status", pd.Series([False]*len(df))) == True) |
        (df.get("Regional_Stewardship_Status", pd.Series([False]*len(df))) == True)
    )
    
    df["Year"] = df["Year"].astype("Int64")
    return df

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bird Species Observation Analysis",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global dark theme */
    .main { background-color: #0e1117; }
    .block-container { padding: 1.5rem 2rem; }

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #1c2333 0%, #1e2a3a 100%);
        border: 1px solid #2d3a4f;
        border-radius: 12px;
        padding: 18px 22px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .kpi-value {
        font-size: 2.4rem;
        font-weight: 700;
        color: #4fc3f7;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.82rem;
        color: #8ca0c0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }
    .kpi-sub {
        font-size: 0.72rem;
        color: #56c978;
        margin-top: 2px;
    }

    /* Section headers */
    .section-header {
        color: #4fc3f7;
        font-size: 1.1rem;
        font-weight: 600;
        border-bottom: 1px solid #2d3a4f;
        padding-bottom: 6px;
        margin: 12px 0 14px 0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #141923;
        border-right: 1px solid #2d3a4f;
    }
    
    /* SQL Workspace Styling */
    .sql-container {
        background: #111827;
        border: 1px solid #2d3a4f;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .sql-title {
        font-size: 1rem;
        color: #4fc3f7;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .sql-editor textarea {
        background-color: #0e1117 !important;
        color: #e6edf3 !important;
        font-family: 'Courier New', monospace;
        border-radius: 8px;
    }

    .result-box {
        background: #111827;
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #2d3a4f;
    }

    .metric-box {
        background: #1c2333;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────────────────────
df_full = load_data()

# ── Sidebar Filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🦅 Bird Observatory")
    st.markdown("---")

    all_units = sorted(df_full["Admin_Unit_Code"].dropna().unique())
    sel_units = st.multiselect("Admin Unit", all_units, default=all_units,
                               help="Filter by administrative park unit")

    all_habitats = sorted(df_full["Habitat_Source"].dropna().unique())
    sel_habitats = st.multiselect("Habitat", all_habitats, default=all_habitats)

    all_years = sorted(df_full["Year"].dropna().unique())
    sel_years = st.multiselect("Year", all_years, default=list(all_years))

    all_species = sorted(df_full["Common_Name"].dropna().unique())
    sel_species = st.multiselect("Species (Common Name)",
                                 all_species, default=[],
                                 placeholder="All species")

    atrisk_only = st.toggle("At-Risk Species Only", value=False)
    st.markdown("---")
    st.caption("Data: NPS Bird Monitoring Programme")

# ── Apply Filters ──────────────────────────────────────────────────────────
mask = (
    df_full["Admin_Unit_Code"].isin(sel_units) &
    df_full["Habitat_Source"].isin(sel_habitats) &
    df_full["Year"].isin(sel_years)
)
if sel_species:
    mask &= df_full["Common_Name"].isin(sel_species)
if atrisk_only:
    mask &= df_full["At_Risk"] == True

df = df_full[mask].copy()

# ── DuckDB Connection ───────────────────────────────────────────
con = duckdb.connect()
con.register("bird_data", df)

if df.empty:
    st.warning("No data matches the current filters. Please adjust sidebar selections.")
    st.stop()

# ── Page Header ────────────────────────────────────────────────────────────
st.markdown("# 🦅 Bird Species Observation Analysis")
st.markdown("*Environmental Studies · Biodiversity Conservation · National Park Service*")
st.markdown("---")

# ── KPI Cards ──────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

total_obs     = len(df)
unique_sp     = df["Scientific_Name"].nunique()
atrisk_sp     = df[df["At_Risk"] == True]["Common_Name"].nunique()
admin_count   = df["Admin_Unit_Code"].nunique()
watchlist_sp  = df[df.get("PIF_Watchlist_Status", False) == True]["Common_Name"].nunique()

for col, value, label, sub in [
    (k1, f"{total_obs:,}", "Total Observations", f"{df['Date'].min().date() if pd.notna(df['Date'].min()) else '—'} → {df['Date'].max().date() if pd.notna(df['Date'].max()) else '—'}"),
    (k2, unique_sp, "Unique Species", "Scientific Name"),
    (k3, atrisk_sp, "At-Risk Species", "PIF + Regional Priority"),
    (k4, watchlist_sp, "PIF Watchlist", "Partners in Flight"),
    (k5, admin_count, "Admin Units", "Parks Surveyed"),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-value">{value}</div>'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Tab Navigation ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📅 Temporal",
    "🗺️ Spatial",
    "🦅 Species",
    "🌤️ Environment",
    "🔴 Conservation",
    "🌍 Global Map",
    "🛢️ SQL Explorer"
])


# ── TAB 1: TEMPORAL ────────────────────────────────────────────────────────
with tab1:
    st.markdown('<p class="section-header">Temporal Observation Patterns</p>', unsafe_allow_html=True)

    # Heatmap: Month × Year
    heat = df.groupby(["Year","Month_Name"]).size().reset_index(name="Observations")
    month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    heat["Month_Name"] = pd.Categorical(heat["Month_Name"], categories=month_order, ordered=True)
    heat_pivot = heat.pivot_table(index="Year", columns="Month_Name", values="Observations", fill_value=0)
    heat_pivot = heat_pivot.reindex(columns=[m for m in month_order if m in heat_pivot.columns])

    fig_heat = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        colorscale="YlOrRd",
        hovertemplate="Year: %{y}<br>Month: %{x}<br>Observations: %{z}<extra></extra>",
        colorbar=dict(title="Obs")
    ))
    fig_heat.update_layout(
        title="Seasonal Observation Heatmap (Month × Year)",
        xaxis_title="Month", yaxis_title="Year",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="white", height=350
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        # Season distribution
        season_ord = ["Spring","Summer","Autumn","Winter"]
        season_data = df.groupby(["Season","Habitat_Source"]).size().reset_index(name="Count")
        fig_season = px.bar(
            season_data[season_data["Season"].isin(season_ord)],
            x="Season", y="Count", color="Habitat_Source",
            barmode="group", title="Observations by Season & Habitat",
            color_discrete_map={"Forest":"#4fc3f7","Grassland":"#ffb74d"},
            category_orders={"Season": season_ord}
        )
        fig_season.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117",
            font_color="white", legend_title="Habitat"
        )
        st.plotly_chart(fig_season, use_container_width=True)

    with col_b:
        # Hourly activity
        hour_data = df["Start_Hour"].dropna().astype(int).value_counts().sort_index().reset_index()
        hour_data.columns = ["Hour","Count"]
        fig_hour = px.bar(
            hour_data, x="Hour", y="Count",
            title="Peak Activity by Hour of Day",
            color="Count", color_continuous_scale="Teal"
        )
        fig_hour.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117",
            font_color="white", showlegend=False,
            xaxis=dict(tickmode="linear", dtick=1)
        )
        st.plotly_chart(fig_hour, use_container_width=True)

    # Year-over-year trend
    yearly = df.groupby(["Year","Habitat_Source"]).agg(
        Observations=("Common_Name","count"),
        Unique_Species=("Scientific_Name","nunique")
    ).reset_index()

    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    for hab, color in [("Forest","#4fc3f7"),("Grassland","#ffb74d")]:
        sub = yearly[yearly["Habitat_Source"] == hab]
        fig_trend.add_trace(go.Bar(x=sub["Year"], y=sub["Observations"],
                                   name=f"{hab} Obs", marker_color=color, opacity=0.75))
        fig_trend.add_trace(go.Scatter(x=sub["Year"], y=sub["Unique_Species"],
                                       name=f"{hab} Species", mode="lines+markers",
                                       line=dict(color=color, dash="dot"), marker_size=7),
                            secondary_y=True)

    fig_trend.update_layout(
        title="Year-over-Year: Observations & Species Richness",
        plot_bgcolor="#141923", paper_bgcolor="#0e1117", font_color="white",
        barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    fig_trend.update_yaxes(title_text="Observations", secondary_y=False)
    fig_trend.update_yaxes(title_text="Unique Species", secondary_y=True)
    st.plotly_chart(fig_trend, use_container_width=True)


# ── TAB 2: SPATIAL ─────────────────────────────────────────────────────────
with tab2:
    st.markdown('<p class="section-header">Spatial Distribution & Biodiversity Hotspots</p>', unsafe_allow_html=True)

    # Admin unit diversity table
    unit_div = df.groupby(["Admin_Unit_Code","Habitat_Source"]).agg(
        Observations=("Common_Name","count"),
        Unique_Species=("Scientific_Name","nunique"),
        AtRisk_Species=("Common_Name", lambda x: df.loc[x.index][df.loc[x.index,"At_Risk"]==True]["Common_Name"].nunique()),
        Avg_Temp=("Temperature","mean"),
        Avg_Humidity=("Humidity","mean")
    ).reset_index()

    col_x, col_y = st.columns([3, 2])

    with col_x:
        fig_bubble = px.scatter(
            unit_div,
            x="Observations", y="Unique_Species",
            size="AtRisk_Species", color="Habitat_Source",
            hover_name="Admin_Unit_Code",
            text="Admin_Unit_Code",
            title="Biodiversity Hotspot Map (Bubble = At-Risk Count)",
            color_discrete_map={"Forest":"#4fc3f7","Grassland":"#ffb74d"},
            size_max=50
        )
        fig_bubble.update_traces(textposition="top center", textfont_size=10)
        fig_bubble.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117",
            font_color="white", legend_title="Habitat"
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

    with col_y:
        fig_treemap = px.treemap(
            unit_div,
            path=["Habitat_Source","Admin_Unit_Code"],
            values="Unique_Species",
            color="Unique_Species",
            color_continuous_scale="Blues",
            title="Species Richness Treemap"
        )
        fig_treemap.update_layout(
            paper_bgcolor="#0e1117", font_color="white"
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

    # Top plots
    top_plots = (df.groupby(["Plot_Name","Admin_Unit_Code","Habitat_Source"])
                  ["Scientific_Name"].nunique()
                  .reset_index(name="Unique_Species")
                  .sort_values("Unique_Species", ascending=False)
                  .head(20))

    fig_plots = px.bar(
        top_plots, x="Unique_Species", y="Plot_Name",
        color="Habitat_Source", orientation="h",
        hover_data=["Admin_Unit_Code"],
        title="Top 20 Plots by Species Richness",
        color_discrete_map={"Forest":"#4fc3f7","Grassland":"#ffb74d"}
    )
    fig_plots.update_layout(
        plot_bgcolor="#141923", paper_bgcolor="#0e1117",
        font_color="white", yaxis=dict(autorange="reversed"),
        height=520
    )
    st.plotly_chart(fig_plots, use_container_width=True)

    # Admin unit comparison table
    st.subheader("Admin Unit Summary Table")
    display_div = unit_div.copy()
    display_div["Avg_Temp"] = display_div["Avg_Temp"].round(1)
    display_div["Avg_Humidity"] = display_div["Avg_Humidity"].round(1)
    display_div = display_div.rename(columns={
        "Admin_Unit_Code":"Unit","Habitat_Source":"Habitat",
        "AtRisk_Species":"At-Risk Sp","Avg_Temp":"Avg Temp °C",
        "Avg_Humidity":"Avg Humidity %"
    })
    st.dataframe(display_div.sort_values("Unique_Species", ascending=False)
                             .reset_index(drop=True), use_container_width=True)


# ── TAB 3: SPECIES ─────────────────────────────────────────────────────────
with tab3:
    st.markdown('<p class="section-header">Species Distribution & Activity Patterns</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Top 25 species
        top_sp = df["Common_Name"].value_counts().head(25).reset_index()
        top_sp.columns = ["Common_Name", "Observations"]
        top_sp["At_Risk"] = top_sp["Common_Name"].isin(
            df[df["At_Risk"]==True]["Common_Name"].unique()
        )
        fig_sp = px.bar(
            top_sp, x="Observations", y="Common_Name",
            color="At_Risk", orientation="h",
            color_discrete_map={True:"#ef5350", False:"#4fc3f7"},
            title="Top 25 Species by Observation Count",
            labels={"At_Risk":"At Risk"}
        )
        fig_sp.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117",
            font_color="white", yaxis=dict(autorange="reversed"),
            height=560, legend_title="At Risk"
        )
        st.plotly_chart(fig_sp, use_container_width=True)

    with col2:
        # Habitat preference by species (top 15)
        top15 = df["Common_Name"].value_counts().head(15).index
        hab_pref = (df[df["Common_Name"].isin(top15)]
                    .groupby(["Common_Name","Habitat_Source"])
                    .size().reset_index(name="Count"))
        fig_hab = px.bar(
            hab_pref, x="Count", y="Common_Name",
            color="Habitat_Source", orientation="h",
            barmode="stack", title="Habitat Preference — Top 15 Species",
            color_discrete_map={"Forest":"#4fc3f7","Grassland":"#ffb74d"}
        )
        fig_hab.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117",
            font_color="white", yaxis=dict(autorange="reversed"),
            height=560
        )
        st.plotly_chart(fig_hab, use_container_width=True)

    # Sex ratio
    st.markdown('<p class="section-header">Sex Ratio — Top Species</p>', unsafe_allow_html=True)
    sex_top = df["Common_Name"].value_counts().head(12).index
    sex_df = (df[df["Common_Name"].isin(sex_top) & df["Sex"].isin(["Male","Female","Undetermined"])]
              .groupby(["Common_Name","Sex"]).size().reset_index(name="Count"))

    fig_sex = px.bar(
        sex_df, x="Common_Name", y="Count", color="Sex",
        barmode="stack", title="Sex Distribution — Top Species",
        color_discrete_map={"Male":"#42a5f5","Female":"#ec407a","Undetermined":"#78909c"}
    )
    fig_sex.update_layout(
        plot_bgcolor="#141923", paper_bgcolor="#0e1117",
        font_color="white", xaxis_tickangle=-35
    )
    st.plotly_chart(fig_sex, use_container_width=True)

    # ID Method & Interval
    col3, col4 = st.columns(2)
    with col3:
        method_df = df["ID_Method"].value_counts().reset_index()
        method_df.columns = ["Method","Count"]
        fig_method = px.pie(method_df, names="Method", values="Count",
                            title="Detection Method Distribution",
                            color_discrete_sequence=px.colors.qualitative.Pastel,
                            hole=0.4)
        fig_method.update_layout(paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig_method, use_container_width=True)

    with col4:
        interval_df = df["Interval_Length"].value_counts().reset_index()
        interval_df.columns = ["Interval","Count"]
        fig_int = px.pie(interval_df, names="Interval", values="Count",
                         title="Observation Interval Distribution",
                         color_discrete_sequence=px.colors.qualitative.Safe,
                         hole=0.4)
        fig_int.update_layout(paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig_int, use_container_width=True)

    # Distance distribution
    dist_df = df["Distance"].value_counts().reset_index()
    dist_df.columns = ["Distance Band","Count"]
    fig_dist = px.bar(dist_df, x="Distance Band", y="Count",
                      title="Observations by Distance Band",
                      color="Count", color_continuous_scale="Teal")
    fig_dist.update_layout(
        plot_bgcolor="#141923", paper_bgcolor="#0e1117",
        font_color="white", showlegend=False
    )
    st.plotly_chart(fig_dist, use_container_width=True)


# ── TAB 4: ENVIRONMENT ─────────────────────────────────────────────────────
with tab4:
    st.markdown('<p class="section-header">Environmental Conditions & Bird Activity</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Temperature vs unique species per unit
        env_agg = df.groupby("Admin_Unit_Code").agg(
            Avg_Temp=("Temperature","mean"),
            Unique_Species=("Scientific_Name","nunique"),
            Observations=("Common_Name","count")
        ).reset_index()
        fig_temp = px.scatter(
            env_agg, x="Avg_Temp", y="Unique_Species",
            size="Observations", hover_name="Admin_Unit_Code",
            color="Unique_Species", color_continuous_scale="Viridis",
            title="Avg Temperature vs Species Richness (per Unit)",
            text="Admin_Unit_Code"
        )
        fig_temp.update_traces(textposition="top center", textfont_size=9)
        fig_temp.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117", font_color="white"
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with col2:
        # Sky condition vs observations
        sky_df = df.groupby("Sky_Clean").agg(
            Observations=("Common_Name","count"),
            Unique_Species=("Scientific_Name","nunique")
        ).reset_index()
        fig_sky = px.bar(
            sky_df.sort_values("Observations", ascending=False),
            x="Sky_Clean", y="Observations", color="Unique_Species",
            title="Sky Condition vs Observation Count",
            color_continuous_scale="Blues",
            labels={"Sky_Clean":"Sky Condition","Unique_Species":"Species Count"}
        )
        fig_sky.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117", font_color="white"
        )
        st.plotly_chart(fig_sky, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Wind category vs observations
        if "Wind_Category" in df.columns:
            wind_df = df.groupby(["Wind_Category","Habitat_Source"]).size().reset_index(name="Count")
            fig_wind = px.bar(
                wind_df, x="Wind_Category", y="Count", color="Habitat_Source",
                barmode="group", title="Wind Category vs Observations",
                color_discrete_map={"Forest":"#4fc3f7","Grassland":"#ffb74d"}
            )
            fig_wind.update_layout(
                plot_bgcolor="#141923", paper_bgcolor="#0e1117", font_color="white"
            )
            st.plotly_chart(fig_wind, use_container_width=True)
        else:
            st.info("Wind Category data not available")

    with col4:
        # Disturbance effect on species richness
        if "Disturbance_Level" in df.columns:
            dist_df = df.groupby("Disturbance_Level").agg(
                Observations=("Common_Name","count"),
                Unique_Species=("Scientific_Name","nunique")
            ).reset_index()
            fig_dist = px.bar(
                dist_df.sort_values("Unique_Species", ascending=False),
                x="Disturbance_Level", y="Unique_Species",
                title="Disturbance Level vs Species Richness",
                color="Unique_Species", color_continuous_scale="RdYlGn"
            )
            fig_dist.update_layout(
                plot_bgcolor="#141923", paper_bgcolor="#0e1117",
                font_color="white", showlegend=False
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Disturbance Level data not available")

    # Temperature × Humidity density
    valid_env = df[["Temperature","Humidity","Habitat_Source"]].dropna()
    if not valid_env.empty:
        fig_density = px.density_heatmap(
            valid_env, x="Temperature", y="Humidity",
            facet_col="Habitat_Source", nbinsx=25, nbinsy=25,
            color_continuous_scale="Hot",
            title="Temperature × Humidity Density by Habitat"
        )
        fig_density.update_layout(paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig_density, use_container_width=True)

    # Flyover rate
    if "Flyover_Observed" in df.columns:
        flyover = df.groupby(["Admin_Unit_Code","Habitat_Source"]).apply(
            lambda x: pd.Series({
                "Flyover_Rate_%": round((x["Flyover_Observed"]==True).sum() / len(x) * 100, 1)
            })
        ).reset_index()
        fig_fly = px.bar(
            flyover.sort_values("Flyover_Rate_%", ascending=False),
            x="Admin_Unit_Code", y="Flyover_Rate_%", color="Habitat_Source",
            barmode="group", title="Flyover Rate by Admin Unit & Habitat (%)",
            color_discrete_map={"Forest":"#4fc3f7","Grassland":"#ffb74d"}
        )
        fig_fly.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117", font_color="white"
        )
        st.plotly_chart(fig_fly, use_container_width=True)


# ── TAB 5: CONSERVATION ────────────────────────────────────────────────────
with tab5:
    st.markdown('<p class="section-header">Conservation Priority & At-Risk Species</p>', unsafe_allow_html=True)

    # Stacked bar: at-risk vs not per unit
    cons_unit = df.groupby(["Admin_Unit_Code","Habitat_Source"]).apply(
        lambda x: pd.Series({
            "At_Risk_Obs": int((x["At_Risk"]==True).sum()),
            "Safe_Obs": int((x["At_Risk"]==False).sum()),
            "AtRisk_Species": x[x["At_Risk"]==True]["Common_Name"].nunique()
        })
    ).reset_index()

    fig_cons = px.bar(
        cons_unit.melt(id_vars=["Admin_Unit_Code","Habitat_Source"],
                       value_vars=["At_Risk_Obs","Safe_Obs"],
                       var_name="Status", value_name="Observations"),
        x="Admin_Unit_Code", y="Observations", color="Status",
        facet_col="Habitat_Source", barmode="stack",
        title="At-Risk vs Safe Observations per Admin Unit",
        color_discrete_map={"At_Risk_Obs":"#ef5350","Safe_Obs":"#66bb6a"}
    )
    fig_cons.update_layout(paper_bgcolor="#0e1117", font_color="white")
    st.plotly_chart(fig_cons, use_container_width=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        # At-risk species detail table
        atrisk_detail = (df[df["At_Risk"]==True]
                         .groupby(["Common_Name","Scientific_Name","Habitat_Source"])
                         .agg(
                             Observations=("Common_Name","count"),
                             Admin_Units=("Admin_Unit_Code","nunique"),
                             PIF_Watchlist=("PIF_Watchlist_Status",
                                            lambda x: any(x==True) if "PIF_Watchlist_Status" in df.columns else False),
                             Regional_Priority=("Regional_Stewardship_Status",
                                                lambda x: any(x==True) if "Regional_Stewardship_Status" in df.columns else False)
                         )
                         .reset_index()
                         .sort_values("Observations", ascending=False))

        st.subheader(f"At-Risk Species Registry ({len(atrisk_detail)} species)")
        st.dataframe(atrisk_detail.reset_index(drop=True),
                     use_container_width=True, height=420)

    with col2:
        # Donut: watchlist status
        wl = df[["Common_Name"]].copy()
        if "PIF_Watchlist_Status" in df.columns:
            wl["PIF_Watchlist_Status"] = df["PIF_Watchlist_Status"]
        else:
            wl["PIF_Watchlist_Status"] = False
        if "Regional_Stewardship_Status" in df.columns:
            wl["Regional_Stewardship_Status"] = df["Regional_Stewardship_Status"]
        else:
            wl["Regional_Stewardship_Status"] = False
        
        wl = wl.drop_duplicates()
        wl["Status"] = "Not At-Risk"
        wl.loc[wl["PIF_Watchlist_Status"]==True, "Status"] = "PIF Watchlist"
        wl.loc[wl["Regional_Stewardship_Status"]==True, "Status"] = "Regional Priority"
        wl.loc[(wl["PIF_Watchlist_Status"]==True) &
               (wl["Regional_Stewardship_Status"]==True), "Status"] = "Both Watchlists"
        status_counts = wl["Status"].value_counts().reset_index()
        status_counts.columns = ["Status","Count"]

        fig_donut = px.pie(
            status_counts, names="Status", values="Count",
            title="Species Conservation Status Distribution",
            color_discrete_map={
                "PIF Watchlist":"#ef5350",
                "Regional Priority":"#ffa726",
                "Both Watchlists":"#ab47bc",
                "Not At-Risk":"#66bb6a"
            },
            hole=0.5
        )
        fig_donut.update_layout(paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig_donut, use_container_width=True)

        # AOU code distribution for at-risk
        if "AOU_Code" in df.columns:
            top_aou = (df[df["At_Risk"]==True]["AOU_Code"]
                       .value_counts().head(10).reset_index())
            top_aou.columns = ["AOU_Code","Observations"]
            fig_aou = px.bar(
                top_aou, x="Observations", y="AOU_Code", orientation="h",
                title="Top 10 At-Risk AOU Codes",
                color="Observations", color_continuous_scale="OrRd"
            )
            fig_aou.update_layout(
                plot_bgcolor="#141923", paper_bgcolor="#0e1117",
                font_color="white", yaxis=dict(autorange="reversed"),
                showlegend=False
            )
            st.plotly_chart(fig_aou, use_container_width=True)

    # Observer breakdown for at-risk sightings
    if "Observer" in df.columns:
        obs_atrisk = (df[df["At_Risk"]==True]
                      .groupby("Observer")["Common_Name"]
                      .nunique().sort_values(ascending=False).reset_index())
        obs_atrisk.columns = ["Observer","At_Risk_Species"]
        fig_obs = px.bar(
            obs_atrisk, x="Observer", y="At_Risk_Species",
            title="At-Risk Species Recorded per Observer",
            color="At_Risk_Species", color_continuous_scale="Inferno"
        )
        fig_obs.update_layout(
            plot_bgcolor="#141923", paper_bgcolor="#0e1117",
            font_color="white", showlegend=False, xaxis_tickangle=-30
        )
        st.plotly_chart(fig_obs, use_container_width=True)

# ── TAB 6: GLOBAL MAP ──────────────────────────────────────────────────────
with tab6:
    st.markdown('<p class="section-header">Geographic Distribution — NPS National Capital Region</p>', unsafe_allow_html=True)

    # ── Admin Unit Coordinates (NPS National Capital Region) ───────────────
    UNIT_GEO = {
        "ANTI": {"lat": 39.4765, "lon": -77.7430, "name": "Antietam National Battlefield",            "state": "MD"},
        "CATO": {"lat": 39.6376, "lon": -77.4638, "name": "Catoctin Mountain Park",                   "state": "MD"},
        "CHOH": {"lat": 39.1020, "lon": -77.2300, "name": "C&O Canal National Historic Park",         "state": "MD"},
        "GWMP": {"lat": 38.9180, "lon": -77.0850, "name": "George Washington Memorial Pkwy",          "state": "VA"},
        "HAFE": {"lat": 39.3239, "lon": -77.7447, "name": "Harpers Ferry National Historical Park",   "state": "WV"},
        "MANA": {"lat": 38.8149, "lon": -77.5253, "name": "Manassas National Battlefield Park",       "state": "VA"},
        "MONO": {"lat": 39.3829, "lon": -77.3672, "name": "Monocacy National Battlefield",            "state": "MD"},
        "NACE": {"lat": 38.8050, "lon": -76.9100, "name": "National Capital Parks-East",              "state": "MD"},
        "PRWI": {"lat": 38.5671, "lon": -77.3867, "name": "Prince William Forest Park",              "state": "VA"},
        "ROCR": {"lat": 38.9601, "lon": -77.0511, "name": "Rock Creek Park",                         "state": "DC"},
        "WOTR": {"lat": 38.9387, "lon": -77.2684, "name": "Wolf Trap National Park",                 "state": "VA"},
    }

    # ── Aggregate stats per unit from filtered data ────────────────────────
    unit_agg = df.groupby("Admin_Unit_Code").agg(
        Observations        = ("Common_Name",   "count"),
        Unique_Species      = ("Scientific_Name","nunique"),
        AtRisk_Species      = ("Common_Name",   lambda x: df.loc[x.index, "At_Risk"].eq(True).sum()),
        Avg_Temp            = ("Temperature",   "mean"),
        Avg_Humidity        = ("Humidity",      "mean"),
        Top_Species         = ("Common_Name",   lambda x: x.value_counts().idxmax() if len(x) > 0 else "—"),
    ).reset_index()

    # Attach coordinates
    unit_agg["lat"]        = unit_agg["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("lat"))
    unit_agg["lon"]        = unit_agg["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("lon"))
    unit_agg["Park_Name"]  = unit_agg["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("name", c))
    unit_agg["State"]      = unit_agg["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("state", ""))
    unit_agg["Avg_Temp"]   = unit_agg["Avg_Temp"].round(1)
    unit_agg["Avg_Humidity"] = unit_agg["Avg_Humidity"].round(1)
    unit_agg["AtRisk_Pct"] = (unit_agg["AtRisk_Species"] / unit_agg["Observations"] * 100).round(1)

    geo = unit_agg.dropna(subset=["lat", "lon"])

    # ── Map Controls ────────────────────────────────────────────────────────
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 2])
    with col_ctrl1:
        map_metric = st.selectbox(
            "Bubble size / colour metric",
            ["Unique_Species", "Observations", "AtRisk_Species", "Avg_Temp", "Avg_Humidity"],
            format_func=lambda x: {
                "Unique_Species": "Species Richness",
                "Observations":   "Total Observations",
                "AtRisk_Species": "At-Risk Species",
                "Avg_Temp":       "Avg Temperature (°C)",
                "Avg_Humidity":   "Avg Humidity (%)",
            }[x]
        )
    with col_ctrl2:
        map_style = st.selectbox(
            "Map style",
            ["carto-darkmatter", "carto-positron", "open-street-map", "stamen-terrain"],
            index=0
        )
    with col_ctrl3:
        show_labels = st.toggle("Show park labels", value=True)

    # ── Primary Bubble Map ─────────────────────────────────────────────────
    color_scales = {
        "Unique_Species": "Viridis",
        "Observations":   "Plasma",
        "AtRisk_Species": "Reds",
        "Avg_Temp":       "RdYlBu_r",
        "Avg_Humidity":   "Blues",
    }
    metric_labels = {
        "Unique_Species": "Species Richness",
        "Observations":   "Observations",
        "AtRisk_Species": "At-Risk Species",
        "Avg_Temp":       "Avg Temp °C",
        "Avg_Humidity":   "Avg Humidity %",
    }

    fig_map = go.Figure()

    # Base bubble layer
    fig_map.add_trace(go.Scattermapbox(
        lat=geo["lat"],
        lon=geo["lon"],
        mode="markers+text" if show_labels else "markers",
        text=geo["Admin_Unit_Code"] if show_labels else None,
        textposition="top right",
        textfont=dict(color="white", size=11, family="Arial Black"),
        marker=go.scattermapbox.Marker(
            size=geo[map_metric] / geo[map_metric].max() * 55 + 14,
            color=geo[map_metric],
            colorscale=color_scales[map_metric],
            showscale=True,
            colorbar=dict(
                title=dict(
                    text=metric_labels[map_metric],
                    font=dict(color="white")
                ),
                tickfont=dict(color="white"),
                bgcolor="rgba(20,25,35,0.8)",
                bordercolor="#2d3a4f",
                thickness=14,
                len=0.55,
                x=1.01
            ),
            opacity=0.88,
        ),
        customdata=geo[["Park_Name","State","Observations","Unique_Species",
                         "AtRisk_Species","Avg_Temp","Avg_Humidity","Top_Species"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            "Observations: <b>%{customdata[2]:,}</b><br>"
            "Unique Species: <b>%{customdata[3]}</b><br>"
            "At-Risk Species: <b>%{customdata[4]}</b><br>"
            "Avg Temp: %{customdata[5]} °C | Humidity: %{customdata[6]}%<br>"
            "Top Species: <i>%{customdata[7]}</i>"
            "<extra></extra>"
        ),
        name="Admin Units"
    ))

    # At-risk hotspot ring overlay (highlight units where at-risk > threshold)
    atrisk_threshold = geo["AtRisk_Species"].quantile(0.6)
    hotspots = geo[geo["AtRisk_Species"] >= atrisk_threshold]
    if not hotspots.empty:
        fig_map.add_trace(go.Scattermapbox(
            lat=hotspots["lat"],
            lon=hotspots["lon"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=hotspots[map_metric] / geo[map_metric].max() * 55 + 28,
                color="rgba(239,83,80,0)",
                opacity=1,
                symbol="circle",
            ),
            line=dict(width=2, color="#ef5350"),
            hoverinfo="skip",
            name="Conservation Hotspot"
        ))

    center_lat = geo["lat"].mean()
    center_lon = geo["lon"].mean()

    fig_map.update_layout(
        mapbox=dict(
            style=map_style,
            center=dict(lat=center_lat, lon=center_lon),
            zoom=7.5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0e1117",
        font_color="white",
        height=560,
        legend=dict(
            bgcolor="rgba(20,25,35,0.85)",
            bordercolor="#2d3a4f",
            borderwidth=1,
            font=dict(color="white", size=11),
            x=0.01, y=0.99
        ),
        showlegend=True,
    )

    st.plotly_chart(fig_map, use_container_width=True)

    st.caption(
        "🔴 Red rings = Conservation Hotspots (above 60th percentile in at-risk species). "
        "Bubble size and colour both encode the selected metric. "
        "Coordinates represent park centroids for the NPS National Capital Region network."
    )

    # ── Secondary: Species Range Map ───────────────────────────────────────
    st.markdown('<p class="section-header">Species Range Across Parks</p>', unsafe_allow_html=True)

    col_sp1, col_sp2 = st.columns([2, 3])

    with col_sp1:
        # Pick a species to trace across the map
        available_species = sorted(df["Common_Name"].dropna().unique())
        selected_sp = st.selectbox(
            "Select species to map its range",
            available_species,
            index=available_species.index("American Robin")
            if "American Robin" in available_species else 0
        )
        sp_habitat_filter = st.radio(
            "Habitat filter", ["All", "Forest", "Grassland"], horizontal=True
        )

    with col_sp2:
        sp_df = df[df["Common_Name"] == selected_sp].copy()
        if sp_habitat_filter != "All":
            sp_df = sp_df[sp_df["Habitat_Source"] == sp_habitat_filter]

        sp_agg = sp_df.groupby("Admin_Unit_Code").agg(
            Count=("Common_Name","count"),
            Habitats=("Habitat_Source", lambda x: " + ".join(sorted(x.unique())))
        ).reset_index()
        sp_agg["lat"]  = sp_agg["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("lat"))
        sp_agg["lon"]  = sp_agg["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("lon"))
        sp_agg["name"] = sp_agg["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("name", c))
        sp_geo = sp_agg.dropna(subset=["lat", "lon"])

        # Background: all units greyed out
        fig_range = go.Figure()
        fig_range.add_trace(go.Scattermapbox(
            lat=geo["lat"], lon=geo["lon"],
            mode="markers",
            marker=dict(size=12, color="#2d3a4f", opacity=0.6),
            text=geo["Admin_Unit_Code"],
            hovertemplate="%{text} — not recorded<extra></extra>",
            name="Not Recorded"
        ))

        if not sp_geo.empty:
            fig_range.add_trace(go.Scattermapbox(
                lat=sp_geo["lat"], lon=sp_geo["lon"],
                mode="markers+text",
                text=sp_geo["Admin_Unit_Code"],
                textposition="top right",
                textfont=dict(color="white", size=10),
                marker=dict(
                    size=sp_geo["Count"] / sp_geo["Count"].max() * 40 + 14,
                    color="#56c978",
                    opacity=0.9,
                ),
                customdata=sp_geo[["name","Count","Habitats"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Observations of <i>" + selected_sp + "</i>: <b>%{customdata[1]}</b><br>"
                    "Habitat: %{customdata[2]}"
                    "<extra></extra>"
                ),
                name=selected_sp
            ))
        else:
            st.info(f"No observations of **{selected_sp}** in {sp_habitat_filter} habitat for current filters.")

        fig_range.update_layout(
            mapbox=dict(
                style=map_style,
                center=dict(lat=center_lat, lon=center_lon),
                zoom=7.4
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#0e1117",
            font_color="white",
            height=380,
            legend=dict(
                bgcolor="rgba(20,25,35,0.85)",
                bordercolor="#2d3a4f",
                font=dict(color="white")
            )
        )
        st.plotly_chart(fig_range, use_container_width=True)

    # ── Tertiary: Habitat Footprint Comparison ─────────────────────────────
    st.markdown('<p class="section-header">Habitat Observation Density — Park Comparison</p>', unsafe_allow_html=True)

    hab_unit = df.groupby(["Admin_Unit_Code","Habitat_Source"]).agg(
        Observations=("Common_Name","count"),
        Unique_Species=("Scientific_Name","nunique"),
        AtRisk=("At_Risk", lambda x: (x==True).sum())
    ).reset_index()

    hab_unit["lat"]  = hab_unit["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("lat"))
    hab_unit["lon"]  = hab_unit["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("lon"))
    hab_unit["name"] = hab_unit["Admin_Unit_Code"].map(lambda c: UNIT_GEO.get(c, {}).get("name", c))
    hab_unit = hab_unit.dropna(subset=["lat","lon"])

    # Offset Forest/Grassland markers slightly so they don't overlap
    offset = 0.018
    hab_unit["plot_lat"] = hab_unit.apply(
        lambda r: r["lat"] + (offset if r["Habitat_Source"] == "Forest" else -offset), axis=1
    )
    hab_unit["plot_lon"] = hab_unit.apply(
        lambda r: r["lon"] + (offset if r["Habitat_Source"] == "Forest" else -offset), axis=1
    )

    fig_hab_map = go.Figure()
    hab_colors = {"Forest": "#4fc3f7", "Grassland": "#ffb74d"}

    for hab in ["Forest", "Grassland"]:
        sub = hab_unit[hab_unit["Habitat_Source"] == hab]
        if sub.empty:
            continue
        fig_hab_map.add_trace(go.Scattermapbox(
            lat=sub["plot_lat"], lon=sub["plot_lon"],
            mode="markers",
            marker=dict(
                size=sub["Unique_Species"] / hab_unit["Unique_Species"].max() * 42 + 10,
                color=hab_colors[hab],
                opacity=0.85,
            ),
            customdata=sub[["name","Habitat_Source","Observations","Unique_Species","AtRisk"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Habitat: <b>%{customdata[1]}</b><br>"
                "Observations: %{customdata[2]:,}<br>"
                "Unique Species: %{customdata[3]}<br>"
                "At-Risk Obs: %{customdata[4]}"
                "<extra></extra>"
            ),
            name=hab
        ))

    fig_hab_map.update_layout(
        mapbox=dict(
            style=map_style,
            center=dict(lat=center_lat, lon=center_lon),
            zoom=7.4
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0e1117",
        font_color="white",
        height=440,
        legend=dict(
            title="Habitat",
            bgcolor="rgba(20,25,35,0.85)",
            bordercolor="#2d3a4f",
            font=dict(color="white"),
            x=0.01, y=0.99
        )
    )
    st.plotly_chart(fig_hab_map, use_container_width=True)
    st.caption(
        "Bubble size encodes species richness. Forest (blue) and Grassland (amber) markers are offset "
        "slightly from the park centroid so both are visible simultaneously."
    )

    # ── Data table beneath map ─────────────────────────────────────────────
    with st.expander("📋 Park-level geodata table"):
        display_geo = geo[["Admin_Unit_Code","Park_Name","State","Observations",
                            "Unique_Species","AtRisk_Species","AtRisk_Pct",
                            "Avg_Temp","Avg_Humidity","Top_Species","lat","lon"]].copy()
        display_geo.columns = ["Code","Park","State","Obs","Species","At-Risk Sp",
                                "At-Risk %","Avg Temp °C","Avg Humidity %","Most Seen","Lat","Lon"]
        st.dataframe(display_geo.sort_values("Species", ascending=False).reset_index(drop=True),
                     use_container_width=True)

# ── TAB 7: SQL WORKSPACE ────────────────────────────────────────────

with tab7:
    st.markdown('<p class="section-header">🧠 SQL Workspace</p>', unsafe_allow_html=True)

    # Layout split
    left, right = st.columns([1.2, 1])

    # ── LEFT: SQL EDITOR ─────────────────────────────
    with left:
        st.markdown('<div class="sql-container">', unsafe_allow_html=True)
        st.markdown('<div class="sql-title">SQL Editor</div>', unsafe_allow_html=True)

        query = st.text_area(
            "",
            value=st.session_state.get("sql_input", "SELECT * FROM bird_data LIMIT 50"),
            height=250,
            key="sql_input"
        )

        col1, col2, col3 = st.columns([1,1,1])

        run_query = col1.button("▶ Run", use_container_width=True)
        clear = col2.button("🧹 Clear", use_container_width=True)
        sample = col3.button("⚡ Sample", use_container_width=True)

        if clear:
            st.session_state.sql_input = ""
            st.rerun()

        if sample:
            st.session_state.sql_input = """SELECT Common_Name, COUNT(*) as obs
FROM bird_data
GROUP BY Common_Name
ORDER BY obs DESC
LIMIT 10"""
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Schema
        with st.expander("📋 Schema"):
            st.dataframe(con.execute("DESCRIBE bird_data").fetchdf(), use_container_width=True)

    # ── RIGHT: RESULTS & CHART ───────────────────────
    with right:
        st.markdown('<div class="sql-container">', unsafe_allow_html=True)
        st.markdown('<div class="sql-title">Results & Visualization</div>', unsafe_allow_html=True)

        if run_query:
            try:
                result = con.execute(query).fetchdf()

                # Metrics
                c1, c2 = st.columns(2)
                c1.metric("Rows", len(result))
                c2.metric("Columns", len(result.columns))

                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.dataframe(result, use_container_width=True, height=250)
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Visualization ─────────────────
                st.markdown("### 📊 Chart")

                numeric_cols = result.select_dtypes(include=['number']).columns.tolist()

                if len(result.columns) >= 2 and numeric_cols:
                    x_col = st.selectbox("X-axis", result.columns, key="x")
                    y_col = st.selectbox("Y-axis", numeric_cols, key="y")

                    chart_type = st.radio(
                        "Type",
                        ["Bar", "Line", "Scatter"],
                        horizontal=True
                    )

                    if chart_type == "Bar":
                        fig = px.bar(result, x=x_col, y=y_col)
                    elif chart_type == "Line":
                        fig = px.line(result, x=x_col, y=y_col)
                    else:
                        fig = px.scatter(result, x=x_col, y=y_col)

                    fig.update_layout(
                        plot_bgcolor="#111827",
                        paper_bgcolor="#111827",
                        font_color="white",
                        margin=dict(l=10, r=10, t=30, b=10)
                    )

                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info("Run a query with numeric columns to visualize")

            except Exception as e:
                st.error(f"SQL Error: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Bird Species Observation Analysis Dashboard · NPS National Capital Region · Built with Streamlit & Plotly")
st.caption("Author: RICHARD JOY · Email: richardjoy9946@gmail.com · [linkedin.com/in/richard-joy](https://linkedin.com/in/richard-joy) | [github.com/vaderrex](https://github.com/vaderrex)")