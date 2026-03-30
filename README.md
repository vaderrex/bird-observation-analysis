# Bird Species Observation Analysis
### NPS National Capital Region — Breeding Season 2018

**Domain:** Environmental Studies, Biodiversity Conservation, and Ecology

**Skills:** Data Cleaning and Preprocessing, Exploratory Data Analysis (EDA), Data Visualization, Geographic Analysis, Species Analysis, SQL, Streamlit / Power BI

---

## Problem Statement

This project analyzes the distribution and diversity of bird species across two distinct ecosystems: forests and grasslands. By examining bird species observations across these habitats, the goal is to understand how environmental factors — such as vegetation type, temperature, humidity, and wind conditions — influence bird populations and behavior.

The study works with observational data collected across 11 National Park Service (NPS) units in the National Capital Region, identifying patterns of habitat preference and assessing the impact of these habitats on bird diversity. The findings provide actionable insights for habitat conservation, biodiversity management, and understanding the effects of environmental changes on avian communities.

---

## Business Use Cases

1. **Wildlife Conservation** — Inform decisions on protecting critical bird habitats and enhancing biodiversity conservation efforts.
2. **Land Management** — Optimize land use and habitat restoration strategies by understanding species habitat preferences.
3. **Eco-Tourism** — Identify bird-rich areas to develop bird-watching tourism, attracting eco-tourists and supporting local economies.
4. **Sustainable Agriculture** — Support agricultural practices that minimize impact on bird populations in grasslands and forests.
5. **Policy Support** — Provide data-driven insights to help environmental agencies create effective conservation policies for vulnerable species.
6. **Biodiversity Monitoring** — Track the health and diversity of avian populations, aiding in the monitoring of ecosystem stability.

---

## Dataset

**Source:** NPS Inventory and Monitoring Program — National Capital Region Bird Monitoring Protocol. Dataset provided for academic analysis.

**Reference:** [Bird_Observation_DataSet (Google Drive)](https://drive.google.com/drive/folders/1Zry_64VTPuCR_NKdaWCt6MkQZ1m1xwqF?usp=drive_link)

**Collection methodology:** Trained observers conducted 10-minute point-count surveys at fixed plots. Each survey was split into four time intervals (0-2.5 min, 2.5-5 min, 5-7.5 min, 7.5-10 min). Every bird detected was recorded with species identity, detection method, distance band, sex, and whether it was observed during the first 3 minutes.

**Coverage:** May 2018 to July 2018 (peak breeding season)
**Total records:** ~17,077 observations across Forest and Grassland habitats
**Attributes per record:** 29 columns

**Park units covered:**

| Code | Full Name | Forest Records | Grassland Records |
|------|-----------|:--------------:|:-----------------:|
| ANTI | Antietam National Battlefield | 333 | 3,588 |
| CATO | Catoctin Mountain Park | 805 | 0 |
| CHOH | C&O Canal National Historical Park | 2,202 | 0 |
| GWMP | George Washington Memorial Parkway | 386 | 0 |
| HAFE | Harpers Ferry National Historical Park | 422 | 117 |
| MANA | Manassas National Battlefield Park | 465 | 1,811 |
| MONO | Monocacy National Battlefield | 370 | 3,015 |
| NACE | National Capital Parks-East | 684 | 0 |
| PRWI | Prince William Forest Park | 2,463 | 0 |
| ROCR | Rock Creek Park | 289 | 0 |
| WOTR | Wolf Trap National Park | 127 | 0 |

**Column reference:**

| Column | Description |
|--------|-------------|
| `Admin_Unit_Code` | Administrative unit code (e.g., ANTI) |
| `Sub_Unit_Code` | Sub-unit within the administrative unit |
| `Site_Name` | Specific observation site name |
| `Plot_Name` | Unique plot identifier for the survey point |
| `Location_Type` | Habitat type — Forest or Grassland |
| `Year`, `Date` | Observation year and exact date |
| `Start_Time`, `End_Time` | Survey session timestamps |
| `Observer` | Field observer name |
| `Visit` | Visit count to the same plot per season |
| `Interval_Length` | Time window within the 10-min survey |
| `ID_Method` | Detection method — Singing, Calling, Visualization |
| `Distance` | Distance band from observer — ≤50m or 50-100m |
| `Flyover_Observed` | Whether the bird was flying overhead (TRUE/FALSE) |
| `Sex` | Observed bird sex — Male, Female, Undetermined |
| `Common_Name` | Common species name (e.g., Eastern Towhee) |
| `Scientific_Name` | Scientific species name (e.g., Pipilo erythrophthalmus) |
| `AcceptedTSN` | Taxonomic Serial Number |
| `NPSTaxonCode` | NPS-assigned taxon code |
| `AOU_Code` | American Ornithological Union species code |
| `PIF_Watchlist_Status` | Partners in Flight conservation watchlist flag |
| `Regional_Stewardship_Status` | NPS regional conservation priority flag |
| `Temperature` | Temperature at time of observation (°C) |
| `Humidity` | Humidity percentage at observation time |
| `Sky` | Sky condition (e.g., Clear, Cloudy, Mist) |
| `Wind` | Wind condition (e.g., Calm, Light breeze) |
| `Disturbance` | Human disturbance level during survey |
| `Initial_Three_Min_Cnt` | Whether detected in the first 3 minutes (TRUE/FALSE) |

**Known data quality notes:**
- `Sub_Unit_Code` is null for the majority of Forest records — excluded from analysis
- `Sex` has high null rates (~60-70%) — treated as optional attribute
- 7 Grassland park sheets are empty (CATO, CHOH, GWMP, NACE, PRWI, ROCR, WOTR) — those parks have no grassland survey plots
- Minor nulls in `Distance` and `AcceptedTSN` — handled during preprocessing

---

## Methodology

The project follows a structured five-phase analytical pipeline.

**Phase 1 — Data Cleaning and Preprocessing**
Raw Excel files (Forest and Grassland) were loaded using `pandas` and `openpyxl`. Each park sheet was extracted, labelled with its source habitat type, and vertically concatenated into a unified DataFrame. Missing values, duplicates, and outliers were handled systematically. Relevant columns were filtered and standardised for downstream analysis.

**Phase 2 — Exploratory Data Analysis (EDA)**
Visual EDA was performed across six analytical lenses: temporal patterns, spatial patterns, species diversity, environmental conditions, distance and behavior, and conservation insights. A correlation heatmap was produced to identify relationships between environmental conditions and observation density.

**Phase 3 — SQL Storage and Querying**
Data was stored in a SQL Server star schema (Fact + Dimension tables) to enable structured multi-dimensional querying. All queries include inline comments explaining business logic and metric definitions. Window functions and indexes were applied for performance and advanced aggregation.

**Phase 4 — Visualization**
Interactive visualizations were built using Plotly in a Streamlit application, covering species distributions, temporal heatmaps, and environmental condition analysis. Power BI was used for an executive-level summary dashboard.

**Phase 5 — Insights and Documentation**
Key findings were synthesised into actionable conservation insights addressing each business use case. A concise report documents the approach, findings, and recommendations in stakeholder-friendly language.

**Tools used:**

| Phase | Tools |
|-------|-------|
| Ingestion | Python, pandas, openpyxl |
| Preprocessing | Python, pandas |
| EDA | Python, matplotlib, seaborn, plotly |
| SQL Analysis | SQL Server, T-SQL |
| Visualization | Streamlit, Plotly, Power BI |
| Schema Design | SQL Server (Star Schema — Fact + Dimension tables) |

---

## Analysis Dimensions

### Temporal Analysis
- Seasonal trends across the breeding season (May to July)
- Observation time windows — which hours produce the highest bird activity?

### Spatial Analysis
- Biodiversity hotspots by park unit and habitat type
- Plot-level comparison — which plots attract the most species?

### Species Analysis
- Unique species count and distribution across habitat types
- Activity patterns by detection method (Singing, Calling, Visualization)
- Sex ratio analysis across key species

### Environmental Conditions
- Correlation between Temperature, Humidity, Sky, and Wind with observation counts
- Disturbance level impact on bird sightings

### Distance and Behavior
- Species typically observed close vs. far from the observer
- Flyover frequency and behavioral trends

### Observer Trends
- Observer bias analysis — do certain observers report more observations or specific species?
- Impact of repeat visits on species count and diversity

### Conservation Insights
- PIF Watchlist and Regional Stewardship species trends by park
- AOU Code distribution linked to conservation priorities

---

## Project Structure

```
bird-species-observation-analysis/
│
├── data/
│   ├── Bird_Monitoring_Data_FOREST.XLSX
│   └── Bird_Monitoring_Data_GRASSLAND.XLSX
│
├── notebooks/
│   ├── 01_preprocessing.ipynb       # Data ingestion, cleaning, and export
│   ├── 02_eda.ipynb                 # Visual EDA, distributions, correlations
│   └── 03_analysis.ipynb            # Advanced analysis and ML modelling
│
├── sql/
│   ├── schema/
│   │   ├── create_dimensions.sql
│   │   └── create_fact.sql
│   └── analysis/
│       ├── species_richness.sql
│       ├── conservation_flags.sql
│       ├── habitat_comparison.sql
│       ├── environmental_analysis.sql
│       └── kpi_summary.sql
│
├── dashboard/
│   ├── app.py
│   └── tabs/
│
├── powerbi/
│   └── bird_monitoring.pbix
│
├── docs/
│   └── screenshots/
│
└── README.md
```

---

## Deliverables

- **Cleaned Dataset** — Final preprocessed dataset with documented cleaning steps
- **Source Code** — Well-commented Python scripts and SQL queries
- **Interactive Dashboard** — Streamlit application with Plotly visualizations and Power BI executive summary
- **Documentation** — Concise report covering approach, key findings, and actionable recommendations

---

## Conclusion

*(To be completed after full analysis — will cover top findings across species richness, conservation priority species, habitat differences, and environmental drivers, with specific recommendations for each business use case.)*

---

## Future Work

- Incorporate multi-year data to detect population trends over time
- Build a predictive model to classify conservation-priority observations based on environmental conditions
- Integrate weather API data to enrich environmental context beyond survey-time snapshots
- Develop park-level biodiversity scorecards for NPS management reporting

---

## Author

**Richard Joy Y**
Junior Data Analyst
[linkedin.com/in/richard-joy](https://linkedin.com/in/richard-joy) | richardjoy9946@gmail.com | [github.com/vaderrex](https://github.com/vaderrex)
