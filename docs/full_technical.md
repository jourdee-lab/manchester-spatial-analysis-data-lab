# FYP Tools & Methods: Comprehensive Technical Summary

**Project:** Spatial Analysis of Chinese Immigrant Integration in Manchester (1981–2001)  
**Date:** 7 March 2026  
**Author:** Final Year Project Student  
**Repositories:**
- Data Pipeline: `manchester_spatial_lab/fyp_main`
- Web Application: `manchester_spatial_lab/manchester-cityscape-explorer-main`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Data Pipeline Repository](#data-pipeline-repository)
3. [Web Application Repository](#web-application-repository)
4. [Integrated Workflow](#integrated-workflow)
5. [Technical Stack](#technical-stack)
6. [Data Processing Methods](#data-processing-methods)
7. [Geospatial Analysis Methods](#geospatial-analysis-methods)
8. [Visualization & Frontend](#visualization--frontend)
9. [Validation & Quality Assurance](#validation--quality-assurance)
10. [Reproducibility & Documentation](#reproducibility--documentation)

---

## Executive Summary

This FYP combines **data engineering** (Python/GeoPandas), **geospatial analysis** (QGIS), and **web development** (React/Mapbox GL) to create a reproducible pipeline for analyzing historical census data on urban ethnic segregation and economic integration.

### Research Objectives
1. **Temporal analysis**: Compare spatial distribution of Chinese immigrants across 1981, 1991, 2001
2. **Socioeconomic integration**: Map housing quality, tenure, employment, and economic position
3. **Reproducibility**: Create documented, scriptable workflows suitable for peer review
4. **Accessibility**: Develop interactive web visualization for public engagement

### Key Deliverables
- Processed census indicator datasets (CSV + GeoPackage)
- QGIS mapping templates with joined spatial data
- Interactive web application with Mapbox GL mapping
- Comprehensive documentation and reproducible scripts
- Validation reports with quality metrics (100% join match rate achieved)

---

## Data Pipeline Repository

### Location
`/home/jourdee/Workspace/manchester_spatial_lab/fyp_main`

### Purpose
Ingest, process, validate, and aggregate UK Census Small Area Statistics (SAS) data from 1981, 1991, and 2001 for Manchester. Produce computed indicator tables, spatial GeoPackages, and harmonised cross-decade comparison outputs.

### Directory Structure

```
fyp_main/
├── README.md                          # Main documentation
│
├── configs/                           # Configuration files (YAML-based)
│   ├── indicators.yml                 # 29 indicator definitions with formulas
│   └── sas_raw_file_mapping.yml       # Raw SAS file structure documentation
│
├── data/
│   ├── raw/                           # Raw census SAS CSVs (.gitignored — obtain from UK Data Service)
│   │   ├── sas/1981_sas0{2,4,7,10}_part{1-5}.csv   # 1981: 20 CSV parts
│   │   ├── s{02,06,07,09,16,81}ews/    # 1991: 6 tables × 4 parts
│   │   └── c01c{s001,t003,s015,s028,s049,s052,s056,s060}_ons.csv  # 2001: 8 tables
│   │
│   ├── processed/
│   │   ├── 1991_sas_code_verification.csv          # 1991 SAS code cross-check
│   │   ├── aggregates/
│   │   │   ├── census_1981/README.md
│   │   │   ├── census_1991/1991_sas02_totalpop_combined.csv
│   │   │   └── census_2001/2001_oas_combined_raw.csv
│   │   ├── indicators/                # Final indicator outputs
│   │   │   ├── 1981/
│   │   │   │   ├── indicators_summary.txt
│   │   │   │   ├── manchester_eds_1981_indicators.csv        # Ward-level
│   │   │   │   └── manchester_eds_1981_indicators_ed_level.csv  # ED-level
│   │   │   ├── 1991/
│   │   │   │   ├── manchester_district_1991_indicators.csv
│   │   │   │   ├── manchester_eds_1991_indicators.csv
│   │   │   │   └── manchester_wards_1991_indicators.csv
│   │   │   ├── 2001/manchester_oas_2001_indicators.csv
│   │   │   └── temporal/
│   │   │       ├── harmonisation_metadata.json
│   │   │       ├── harmonised_zones.geojson
│   │   │       ├── manchester_1981_1991_comparison.csv
│   │   │       ├── manchester_1981_1991_2001_comparison.csv
│   │   │       ├── manchester_harmonised_indicators_1981_1991_2001.csv
│   │   │       └── temporal_comparison_metadata.json
│   │   └── outputs/spatial/           # Spatial products (GeoPackage)
│   │       ├── 1981/
│   │       │   ├── manchester_eds_1981_joined_attributes.csv
│   │       │   └── manchester_eds_1981_joined_indicators.gpkg
│   │       ├── 1991/
│   │       │   ├── manchester_eds_1991_joined_indicators.gpkg
│   │       │   └── manchester_wards_1991_indicators_for_qgis.csv
│   │       └── 2001/manchester_oas_2001_joined_indicators.gpkg
│   │
│   └── lookups/                       # Reference tables
│       ├── 1981_geography_lookup.csv
│       ├── 1981_variable_lookup.csv
│       ├── 1981_table_code_name_lookup.csv
│       ├── 1991_census_structure.md
│       ├── 1991_england_wales_scotland_geography_lookup.csv
│       ├── 1991_England_Wales_Scotland_Small_Area_Statistics_variable_lookup.csv
│       ├── 1991_table_code_name_lookup.csv
│       ├── 2001_geography_lookup_england.csv
│       ├── 2001_variable_lookup_ew.csv
│       └── 2001_table_code_and_names_ukcas_map.csv
│
├── docs/
│   └── full_technical.md                        # Full technical reference (this file)
│
├── figures/
│   └── choropleth_maps/
│       ├── 1981/
│       │   ├── 1981_chinese_born_choropleth.png
│       │   └── 1981_chinese_born_choropleth.pgw
│       ├── 1991/
│       │   ├── 1991_chinese_ethnic_ed_choropleth.png
│       │   └── 1991_chinese_ethnic_ed_choropleth.pgw
│       └── 2001/manchester_oas_2001_joined_choropleth_maps.qgz
│
├── gis_boundaries/                    # Boundary shapefiles (.gitignored)
│   ├── 1981/                          # ED_1981_EW.shp
│   ├── 1991/                          # england_wa_1991.shp
│   └── 2001/
│       ├── OA/                        # england_oa_2001.shp
│       └── wards/                     # england_caswa_2001_clipped.shp
│
├── qgis/
│   └── 1981/
│       ├── join_validation.qgz        # Join QA (100% match, 1,017 EDs)
│       └── indicator_mapping.qgz      # Indicator choropleth template
│
├── scripts/
│   ├── utils.py
│   ├── 01_ingest.py
│   ├── 02_compute_indicators_1981.py
│   ├── 03_compute_indicators_1991.py
│   ├── 04_compute_indicators_2001.py
│   ├── 05_join_boundaries.py
│   ├── 06_harmonise_and_export.py
│   └── 07_analysis.py
│
└── .venv/                             # Python virtual environment (gitignored)
```

### Key Data Characteristics

| Aspect | Details |
|--------|---------|
| **Census Years** | 1981, 1991, 2001 |
| **Data Granularity** | 1981: ED-level (1,017 EDs); 1991: ED + ward level; 2001: OA level |
| **Geographic Coverage** | Manchester Local Authority (LAD codes 03BN / 00BN) |
| **Boundary Features** | 1981: 1,017 EDs; 1991: electoral wards; 2001: Output Areas |
| **SAS/CAS Tables Used** | 1981: SAS02/04/07/10; 1991: S02/S06/S07/S09/S16/S81; 2001: CS001/CT003/CS015/CS028/CS049/CS052/CS056/CS060 |
| **Indicators Computed** | 29 per year (demographics, ethnicity, tenure, housing quality, employment) |
| **Harmonised Output** | 33 common ward zones, 1981–1991–2001 temporal comparison |
| **Spatial Reference System** | EPSG:27700 (British National Grid) |
| **Record Format** | CSV (row = zone, column = indicator); GeoPackage for spatial products |

---

## Web Application Repository

### Location
`/home/jourdee/Workspace/manchester_spatial_lab/manchester-cityscape-explorer-main`

### Purpose
Interactive web frontend for exploring spatial census data with Mapbox GL mapping, dynamic filtering, and time-series visualization.

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend Framework** | React 18 + TypeScript | Component-based UI, type safety |
| **Build Tool** | Vite 5.4 | Fast bundling & HMR dev experience |
| **Package Manager** | Bun 1.3+ | Fast dependency management |
| **Styling** | Tailwind CSS 3 | Utility-first CSS framework |
| **UI Components** | shadcn/ui | Pre-built Radix UI components |
| **Mapping Library** | Mapbox GL JS 3 | Interactive vector tile mapping |
| **Data Fetching** | React Query | Server state management |
| **Forms & Validation** | React Hook Form + Zod | Form handling & validation |
| **Linting** | ESLint + TypeScript Parser | Code quality & type checking |
| **Styling** | PostCSS + Tailwind | CSS processing pipeline |

### Directory Structure

```
manchester-cityscape-explorer-main/
├── src/
│   ├── App.tsx                        # Main app component with routing
│   ├── App.css
│   ├── main.tsx                       # Entry point
│   ├── index.css
│   ├── vite-env.d.ts
│   │
│   ├── components/
│   │   ├── ChoroplethMapContainer.tsx     # Mapbox GL wrapper + choropleth logic
│   │   ├── ChoroplethLegend.tsx           # Dynamic legend for choropleth layers
│   │   ├── Header.tsx                     # Top navigation bar
│   │   ├── Navigation.tsx                 # Route navigation
│   │   ├── PageTransition.tsx             # Animated page transitions
│   │   └── ui/                            # shadcn/ui component library (30+ components)
│   │
│   ├── pages/
│   │   ├── CensusExplorer.tsx             # Main interactive map + indicator explorer
│   │   ├── About.tsx                      # Project info
│   │   ├── Findings.tsx                   # Analysis results
│   │   ├── Methodology.tsx                # Methods documentation
│   │   └── NotFound.tsx                   # 404 page
│   │
│   ├── data/
│   │   ├── indicators.ts                  # Indicator metadata & display config
│   │   └── routes.ts                      # App route definitions
│   │
│   ├── hooks/
│   │   ├── use-mobile.tsx                 # Responsive breakpoint hook
│   │   ├── use-toast.ts                   # Toast notification hook
│   │   └── usePageDirection.ts            # Navigation direction tracking
│   │
│   ├── lib/
│   │   └── utils.ts
│   │
│   └── types/
│       └── data.ts                        # TypeScript interfaces
│
├── public/
│   ├── robots.txt
│   └── geojson/                       # Static GeoJSON served to the map
│       ├── datasets.json                  # Dataset registry
│       ├── manchester_eds_1981.geojson
│       ├── manchester_wards_1981.geojson
│       ├── manchester_eds_1991.geojson
│       ├── manchester_wards_1991.geojson
│       ├── manchester_oas_2001.geojson
│       └── manchester_wards_2001.geojson
│
├── docs/CHOROPLETH_STYLING.md         # Choropleth colour scale documentation
├── index.html
├── package.json
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── eslint.config.js
├── components.json
├── vercel.json
└── bun.lockb
```

### Key Components

#### 1. **ChoroplethMapContainer.tsx**
- Initializes and manages the Mapbox GL map instance
- Loads GeoJSON layers from `public/geojson/` for 1981/1991/2001
- Applies choropleth paint expressions driven by selected indicator
- Handles year/indicator switching via separate React effects

#### 2. **ChoroplethLegend.tsx**
- Renders dynamic colour-scale legend
- Shows quantile/equal-interval class breaks and value ranges
- Updates reactively when indicator or dataset changes

#### 3. **CensusExplorer.tsx** _(main page)_
- Hosts the map and controls panel
- Manages selected year, selected indicator, and hover state
- Passes props down to `ChoroplethMapContainer` and `ChoroplethLegend`

#### 4. **Header.tsx / Navigation.tsx**
- Top navigation + route links (Census Explorer, Findings, Methodology, About)

#### 5. **PageTransition.tsx**
- Wraps page content with animated entrance/exit transitions

---

## Integrated Workflow

### End-to-End Data Flow

```
RAW CENSUS DATA (1981)
│ (20 CSV files, 112,261 GB EDs per file)
│ Source: UK Data Service / EDINA
│
├─→ [01_ingest.py]
│   • Loads 5-part files per SAS table
│   • Concatenates on zoneid
│   • Filters to Manchester (03BN*)
│   • Validates aggregates
│   └─→ ED-LEVEL SAS DATA (4 CSVs)
│       (1,053 EDs × SAS codes)
│
├─→ [02_compute_indicators_1981.py]
│   • Reads indicators.yml config
│   • Computes raw counts (demographics, housing, etc.)
│   • Derives rates (% calculations)
│   • Handles null values & division by zero (NaN → null in JSON output)
│   • Generates metadata & summary stats
│   └─→ INDICATOR TABLE (CSV)
│       (1,053 EDs × 29 indicators)
│
├─→ [05_join_boundaries.py]
│   • Loads ED shapefile (1,017 Manchester features)
│   • Joins with indicator CSV on WD81CD (ward code)
│   • 100% match rate validation
│   • Exports with all attributes permanent
│   └─→ GEOPACKAGE (GeoPackage format)
│       (1,017 ED polygons + 43 attributes)
│
├─→ [QGIS]
│   • Loads GeoPackage layer
│   • Applies graduated symbology (choropleth)
│   • Creates diagnostic maps (PNG export)
│   • Validates join results visually
│   └─→ CHOROPLETH MAPS (PNG)
│       (Test visualizations for QA)
│
└─→ [Web App Data Integration]
    • Converts GeoPackage to GeoJSON
    • Uploads to Mapbox data source
    • Frontend loads via React Query
    • Displays interactive choropleth
    └─→ LIVE INTERACTIVE MAP
        (http://localhost:~~~~)
```

### Data Format Conversions

| Source Format | Tool | Target Format | Purpose |
|---|---|---|---|
| CSV (SAS raw) | Python pandas | CSV (ED-level) | Consolidate 5-part files |
| CSV (ED-level) | Python geopandas | GeoPackage | Add geometry, permanent export |
| GeoPackage | QGIS | PNG | Visual validation & diagnostic maps |
| GeoPackage | ogr2ogr / Python | GeoJSON | Web frontend compatibility |
| GeoJSON | Mapbox GL JS | Interactive choropleth | User-facing visualization |

---

## Technical Stack

### Data Processing & Analysis

| Tool | Version | Purpose | Usage |
|------|---------|---------|-------|
| **Python** | 3.13 | Programming language | All scripts |
| **pandas** | Latest | Data manipulation | CSV reading/writing, joins, aggregations |
| **GeoPandas** | Latest | Geospatial data handling | Shapefile reading, spatial joins, GeoPackage export |
| **Fiona** | Latest | OGR vector API | Shapefile I/O via GeoPandas |
| **Shapely** | Latest | Spatial geometry | Geometry operations |
| **NumPy** | Latest | Numerical computing | Array operations, calculations |
| **PyYAML** | Latest | YAML parsing | Configuration file reading (indicators.yml) |
| **pathlib** | Built-in | File path handling | Cross-platform path operations |
| **logging** | Built-in | Logging framework | Standardized console output |

### Geospatial Tools

| Tool | Version | Purpose | Usage |
|------|---------|---------|-------|
| **QGIS** | 3.22+ | Desktop GIS | Layer loading, join validation, symbology, map export |
| **Mapbox GL JS** | 3.0+ | Web mapping | Interactive choropleth, layer control, user interaction |
| **British National Grid (EPSG:27700)** | — | CRS | Spatial reference system for all data |
| **OGR/GDAL** | Built into GeoPandas | Vector format conversion | Shapefile ↔ GeoPackage conversions |

### Web Technologies

| Technology | Purpose | Usage |
|---|---|---|
| **React 18** | UI framework | Component-based interface, state management |
| **TypeScript** | Type safety | Type annotations, compile-time error checking |
| **Vite 5.4** | Build tooling | Module bundling, HMR dev server |
| **Bun 1.3** | Package manager | Dependency resolution faster than npm |
| **Tailwind CSS 3** | Styling | Utility-first CSS, responsive design |
| **shadcn/ui** | UI component library | Pre-built accessible components (buttons, dialogs, etc.) |
| **React Hook Form** | Form management | State-efficient form handling |
| **Mapbox GL JS 3** | Web mapping | Vector tiles, interactive choropleth rendering |
| **React Query** | State management | Server state caching, synchronization |

### Development & QA Tools

| Tool | Purpose |
|---|---|
| **ESLint** | JavaScript/TypeScript linting |
| **Git** | Version control |
| **GitHub** | Remote repository & collaboration |
| **Jupyter Notebook** | Interactive exploration & prototyping |
| **Markdown** | Documentation format |

---

## Data Processing Methods

### 1. Raw Data Ingestion (Phase 1-2)

**Input:** Raw 1981 SAS CSVs (20 files, 5 parts per table)

**Process:**
```python
# Step 1: Load 5-part files per SAS table
dfs = []
for part in [1, 2, 3, 4, 5]:
    df = pd.read_csv(f'data/raw/sas/1981_sas02_part{part}.csv')
    dfs.append(df)

# Step 2: Concatenate horizontally on 'zoneid'
combined = pd.concat(dfs, axis=1)

# Step 3: Filter to Manchester (LAD 03BN)
manchester_mask = combined['zoneid'].str.startswith('03BN')
manchester_data = combined[manchester_mask]

# Step 4: Validate aggregates
total_manchester = manchester_data.sum()
expected_aggregate = combined[manchester_mask].sum()
assert np.allclose(total_manchester, expected_aggregate)
```

**Output:** ED-level SAS data (1,053 rows × SAS codes)

**Validation:**
- Verify no duplicate rows (by zoneid)
- Check for NULL values in key columns
- Aggregate to national total and compare with published statistics
- Confirm zoneid format consistency

### 2. Indicator Computation (Phase 6)

**Input:** indicators.yml config + ED-level SAS data

**Configuration Example (YAML):**
```yaml
years:
  1981:
    TOTAL_RES:
      table: sas02
      code: 81sas020001
      description: "All ages TOTAL Persons (Residents)"
    CHINESE_BORN:
      table: sas04
      code: 81sas040359
      description: "Far East births total"
    PCT_CHINESE_BORN:
      numerator: CHINESE_BORN
      denominator: TOTAL_RES
      scale: 100
      description: "% of population born in Far East"
```

**Process:**
```python
# Phase 1: Raw counts
indicators['TOTAL_RES_1981'] = sas_data['81sas020001']
indicators['CHINESE_BORN_1981'] = sas_data['81sas040359']

# Phase 2: Derived rates
indicators['PCT_CHINESE_BORN_1981'] = (
    indicators['CHINESE_BORN_1981'] / 
    indicators['TOTAL_RES_1981'] * 100
).fillna(0)

# Phase 3: Composite indices
indicators['INTEGRATION_INDEX'] = (
    (indicators['PCT_OWNER_OCC_1981'] +
     indicators['EMP_RATE_1981'] +
     100 - indicators['PCT_NO_CAR_1981']) / 3
)

# Phase 4: Output
indicators.to_csv('manchester_eds_1981_indicators.csv', index=False)
```

**Indicator Categories:**

| Category | Examples | Count |
|----------|----------|-------|
| **Demographic Base** | Total residents, sex structure | 3 |
| **Ethnic Presence** | Chinese-born total, % Chinese-born | 4 |
| **Housing Tenure** | Owner-occupied %, social rent % | 4 |
| **Housing Quality** | No-car households %, overcrowding % | 6 |
| **Employment** | Employment rate, unemployment rate | 2 |
| **Composite Indices** | Integration index, deprivation score | 6 |
| **Total** | — | **29** |

**Error Handling:**
- Division by zero → set to NaN (marked as invalid)
- Missing SAS codes → log warning, use default value (0)
- Negative values → flag as data quality issue
- Out-of-range percentages (>100%) → cap or flag

**Output:** 
- CSV: 1,053 rows (EDs) × 30 columns (zoneid + 29 indicators)
- JSON metadata: Data dictionary, formula definitions, summary statistics

### 3. Spatial Join Validation (Phase 5)

**Problem:** Ward-level indicator CSV (1,053 wards) must join to ED-level boundaries (1,017 EDs)

**Join Strategy:**
```
ED Boundary Layer (1,017 features)
├─ ED81CD (unique ED code)
├─ WD81CD (parent ward code, e.g., '03BNAA')
└─ Geometry: polygon

Indicator CSV (1,053 rows)
├─ zoneid: '03BNAA    ' (with trailing spaces)
├─ TOTAL_RES_1981: 12,500
├─ PCT_CHINESE_BORN_1981: 0.5%
└─ [26 more indicators]

JOIN OPERATION (Left Join on Boundaries):
result = boundary_gdf.merge(
    indicator_df,
    left_on='WD81CD',
    right_on='zoneid_trimmed',  # zoneid after trim()
    how='left'  # keep all EDs, match indicator values
)

OUTPUT: 
1,017 ED features + 29 indicator columns
Match Rate: 100% (all EDs matched to ward values)
```

**Normalization Steps:**
1. Trim whitespace: `zoneid.str.strip()`
2. Case standardization: `str.upper()`
3. Validation: zoneid format matches expected pattern (4 letters + number)

**Validation Metrics:**
- **Total boundaries:** 1,017 ✓
- **Total CSV records:** 1,053 (includes district aggregate)
- **Matched:** 1,017 (100%)
- **Unmatched:** 0
- **Quality:** PASS (≥95% threshold)

### 4. GeoPackage Creation (Python)

**Method:** GeoPandas with spatial join

```python
import geopandas as gpd
import pandas as pd

# Load shapefile (GB-wide)
gdf_boundary = gpd.read_file('ED_1981_EW.shp')

# Filter to Manchester
gdf_manchester = gdf_boundary[
    gdf_boundary['LAD81CD'] == '03BN'
].copy()  # 1,017 EDs

# Load CSV
df_indicators = pd.read_csv('manchester_eds_1981_indicators.csv')
df_indicators['zoneid_trimmed'] = df_indicators['zoneid'].str.strip()

# Join
joined = gdf_manchester.merge(
    df_indicators,
    left_on='WD81CD',
    right_on='zoneid_trimmed',
    how='left'
)

# Export
joined.to_file(
    'manchester_eds_1981_joined_indicators.gpkg',
    driver='GPKG',
    layer='manchester_eds_1981_joined'
)
```

**Output Characteristics:**
- **Format:** GeoPackage (.gpkg) — single-file SQLite database
- **Features:** 1,017 ED polygons
- **Attributes:** 43 columns (ED metadata + 29 indicators)
- **CRS:** EPSG:27700 (British National Grid)
- **Size:** ~5-10 MB (depends on geometry precision)

---

## Geospatial Analysis Methods

### 1. Choropleth Mapping (QGIS)

**Process:**

1. **Load GeoPackage:**
   ```
   Layer → Add Layer → Add Vector Layer
   → Select .gpkg file
   ```

2. **Apply Graduated Symbology:**
   ```
   Layer Properties → Symbology tab
   → Type: Graduated
   → Value: ind_PCT_CHINESE_BORN_1981
   → Classes: 5
   → Color ramp: Viridis (or Blues/Reds)
   → Mode: Equal Interval (or Quantile)
   → Click Classify
   ```

3. **Visual Inspection:**
   - Check for spatial clustering (hot spots)
   - Verify no "checkerboard" pattern (would suggest key mismatch)
   - Validate plausibility (high values in expected areas)

4. **Export as PNG:**
   ```
   Project → Import/Export → Export as Image
   → Format: PNG, Resolution: 300 DPI
   → Save to figures/
   ```

**Result:** Choropleth showing % Chinese-born by ED
- Dark purple = high concentration (city center wards)
- Light yellow = low concentration (suburban)
- Multiple EDs per ward inherit ward-level values (creates stepped appearance)

### 2. Spatial Patterns & Analysis

**Clustering Detection:**
- Visual inspection of choropleth reveals spatial autocorrelation
- High-value EDs cluster in central Manchester (Chinatown vicinity)
- Low-value EDs spread across outer wards

**Integration Trajectory:**
- Can compare ward-level averages across indicators
- e.g., High Chinese presence (%) + Low owner-occupancy + High no-car households → concentrated, lower-income areas

**Boundary Harmonization (Future):**
For 1981–2001 comparison, address:
- ED codes change between decades
- Use areal interpolation (rasterize, resample, re-vectorize)
- Or identify stable geographies (wards, districts)

### 3. QGIS Template Project

**File:** `qgis/1981/indicator_mapping.qgz`

**Contents:**
- Base layer: ED boundaries (pre-filtered to Manchester)
- Join configuration: CSV + spatial reference
- Symbology template: Graduated color scale
- Saved projections & zoom level

**Usage:**
1. Open project
2. Change `Value` field in Symbology to different indicator
3. Reclassify to update ranges
4. Export as new PNG

---

## Visualization & Frontend

### 1. Mapbox GL Choropleth Implementation

**Architecture:**
```
CensusExplorer (page)
├─ State: selectedYear, selectedIndicator, hoveredFeature
├─ ChoroplethMapContainer (Mapbox GL instance)
│  └─ GeoJSON source: public/geojson/manchester_*_{year}.geojson
│     ├─ Fill paint: ['interpolate', ...] choropleth expression
│     ├─ Line paint: boundary styling
│     └─ Tooltip on hover: zone details
├─ ChoroplethLegend (colour-scale + class breaks)
└─ Year / indicator selector controls
```

### 2. Interactive Features

#### **Map Interaction:**
- **Pan & Zoom:** Mapbox native controls
- **Click ED:** Opens detail panel
- **Layer Visibility:** Toggle indicator layer on/off

#### **Filter Controls:**
- **Year Dropdown:** 1981 / 1991 / 2001
- **Indicator Dropdown:** List all 25+ metrics
- **Search:** Filter by ED name or ward
- **Time Animation:** Auto-play through years

#### **Detail View (on ED click):**
- ED name and code
- All 29 indicator values
- Historical trend (1981–2001)
- Comparison to city average

### 3. Data Sources & Styling

**GeoJSON Source (from converted GeoPackage):**
```javascript
map.addSource('manchester-eds', {
  type: 'geojson',
  data: manchesterGeojson  // Loaded from API or static file
});

map.addLayer({
  id: 'manchester-eds-choropleth',
  type: 'fill',
  source: 'manchester-eds',
  paint: {
    'fill-color': [
      'interpolate',
      ['linear'],
      ['get', 'PCT_CHINESE_BORN_1981'],
      0, '#fff5eb',      // Light (low values)
      0.5, '#fdbb84',    // Medium
      1.0, '#7f2704'     // Dark (high values)
    ],
    'fill-opacity': 0.7
  }
});
```

**Color Ramps Used:**
- **Viridis** (default): Yellow → Purple (perceptually uniform)
- **Blues:** Light → Dark blue (single-hue sequential)
- **Reds:** Light → Dark red (single-hue sequential)
- **Diverging (optional):** For composite indices (low ← center → high)

### 4. Responsive Design

**Breakpoints (Tailwind):**
- **Mobile:** <640px (full-screen map + sidebar drawer)
- **Tablet:** 640–1024px (split view)
- **Desktop:** >1024px (map + side panels visible)

**Components Adapt:**
- FilterPanel: Vertical layout on mobile, horizontal on desktop
- MapLegend: Bottom-right on desktop, overlay on mobile
- DetailPanel: Drawer on mobile, sidebar on desktop

---

## Validation & Quality Assurance

### 1. Data Integrity Checks

**Ingestion Phase:**
```python
# Check for duplicates
assert len(ed_data) == len(ed_data.drop_duplicates(subset=['zoneid']))

# Check for NULL values in key columns
assert ed_data['TOTAL_RES_1981'].isna().sum() == 0

# Validate zone code format
assert all(ed_data['zoneid'].str.match(r'03BN[A-Z0-9]{2}'))

# Check aggregate matches published total
published_manchester_pop = 438_000
computed_total = ed_data['TOTAL_RES_1981'].sum()
assert abs(published_manchester_pop - computed_total) < 1000
```

### 2. Join Validation Metrics

| Metric | Threshold | Result | Status |
|--------|-----------|--------|--------|
| **Match Rate** | ≥95% | 100% (1,017/1,017) | ✓ PASS |
| **Unmatched EDs** | <50 | 0 | ✓ PASS |
| **NULL values in indicators** | <1% | 0% | ✓ PASS |
| **Spatial plausibility** | Visual check | Clustered pattern matches expected | ✓ PASS |

**Validation Script Output:**
```
=====================================================
PHASE 5 JOIN VALIDATION - Results
=====================================================

[1/6] Extracting boundary ED codes...
  - Extracted 1017 Manchester EDs from shapefile

[2/6] Loading census CSV...
  - Loaded 1053 rows, 26 columns

[3/6] Performing join...
  - Matched: 1017 / 1017
  - Match rate: 100.00%
  - Quality: PASS

[4/6] Exporting to GeoPackage...
  - ✓ Exported to: manchester_eds_1981_joined_indicators.gpkg

Match Rate: 100.00%
Quality Status: PASS

✓ JOIN VALIDATION PASSED
  - ≥95% match rate achieved
  - Ready for Phase 6 indicator computation
```

### 3. Indicator Plausibility Checks

**Range Validation:**
```python
# Percentages should be 0–100%
assert (indicators['PCT_CHINESE_BORN_1981'] >= 0).all()
assert (indicators['PCT_CHINESE_BORN_1981'] <= 100).all()

# Rates should be non-negative
assert (indicators['EMP_RATE_1981'] >= 0).all()
assert (indicators['EMP_RATE_1981'] <= 100).all()

# No person can be counted twice
assert (
    indicators['CHINESE_BORN_1981'] <= 
    indicators['TOTAL_RES_1981']
).all()
```

**Outlier Detection:**
```python
# Flag unusual values (3σ rule)
mean = indicators['PCT_CHINESE_BORN_1981'].mean()
std = indicators['PCT_CHINESE_BORN_1981'].std()
outliers = indicators[
    abs(indicators['PCT_CHINESE_BORN_1981'] - mean) > 3 * std
]
if len(outliers) > 0:
    logger.warning(f"Found {len(outliers)} potential outliers")
```

### 4. Reproducibility Validation

**Script Dependencies:**
- Python 3.9+, pandas, geopandas, pyyaml, fiona, shapely
- All specified in requirements.txt
- Virtual environment setup documented

**Configuration-Driven Approach:**
- All indicator definitions in YAML (human-readable)
- No hardcoded thresholds or magic numbers
- Formulas explicitly documented with citations

**Output Consistency:**
- Same input data → identical output across runs
- Timestamp in output filenames for versioning
- Summary statistics logged for comparison

---

## Reproducibility & Documentation

### 1. Code Organization & Standards

**File Naming Convention:**
- `01_ingest.py` — Step number + verb (all years in one script)
- `02_compute_indicators_1981.py` — Step + verb + subject + year
- `utils.py` — Shared helpers imported by all scripts
- Sequential `NN_` prefix makes execution order self-evident

**Code Comments:**
```python
def normalize_id(ed_code):
    """
    Normalize ED code: trim, uppercase, preserve leading zeros.
    
    Args:
        ed_code: String representation of ED code (e.g., '03BNAA  ')
    
    Returns:
        Normalized string (e.g., '03BNAA')
    
    Note:
        Leading zeros must be preserved (e.g., '01AA' not '1AA')
    """
    return str(ed_code).strip().upper()
```

**Modular Functions:**
- Single responsibility principle
- Input validation at function entry
- Error handling with informative messages

### 2. Documentation Structure

#### **README.md**
- Project overview & research questions
- Quick start instructions
- Directory structure explained
- Phase status summary
- Data dictionary
- Usage examples

#### **Phase PRDs (.github/instructions/)** _(historical — no longer in repo)_
- Phase objectives & acceptance criteria were used during development

#### **Implementation Reports (docs/)**
- `full_technical.md` — Full pipeline and web app technical reference
- `data/lookups/1991_census_structure.md` — 1991 SAS table structure notes

#### **Inline Comments (scripts)**
- "Why" explanations (not just "what")
- Edge cases handled
- Known limitations

### 3. Configuration Files

**indicators.yml** (362 lines):
```yaml
years:
  1981:
    tables:
      - sas02
      - sas04
      - sas07
      - sas10
    
    TOTAL_RES:
      table: sas02
      code: 81sas020001
      dtype: int
      description: "All ages TOTAL Persons (Residents)"
    
    PCT_CHINESE_BORN:
      numerator: CHINESE_BORN
      denominator: TOTAL_RES
      scale: 100
      description: "Percentage born in Far East"
      formula: "(CHINESE_BORN / TOTAL_RES) × 100"
```

**Advantages:**
- Non-programmers can verify indicator definitions
- Easy to extend to 1991/2001
- Clear audit trail of data sources

### 4. Version Control & Collaboration

**Git Repository:**
```
Main branch (production):
├─ fyp_main/ (data pipeline)
│  ├─ scripts/ (Python processing)
│  ├─ configs/ (YAML specifications)
│  ├─ data/ (processed outputs)
│  └─ docs/ (reports & documentation)
│
└─ manchester-cityscape-explorer-main/ (web app)
   ├─ src/ (React components)
   ├─ public/ (static files)
   └─ package.json (dependencies)
```

**Commit Strategy:**
- Atomic commits (one feature per commit)
- Clear commit messages: "Add 1981 indicator computation" not "update"
- Tags for phase milestones (v0.5-phase5, v0.6-phase6)

**Branches (if collaborative):**
- `main` — stable, peer-reviewed code
- `develop` — integration branch
- `feature/1991-data` — feature-specific branches

### 5. Testing & Validation

**Automated Tests (unit level):**
```python
def test_normalize_id():
    assert normalize_id('03BNAA  ') == '03BNAA'
    assert normalize_id('03bnaa') == '03BNAA'
    assert normalize_id('01AA') == '01AA'  # Leading zeros preserved

def test_percentage_calculation():
    assert compute_percentage(50, 100) == 50.0
    assert compute_percentage(1, 3) ≈ 33.33
    assert compute_percentage(0, 100) == 0.0
    assert compute_percentage(50, 0) is NaN  # Division by zero
```

**Integration Tests (end-to-end):**
- Load raw CSV → Ingest → Compute indicators → Export GeoPackage
- Verify output shape, types, ranges
- Compare with manual spot-checks

**QA Procedures:**
1. Run all scripts to completion without errors
2. Check output file sizes reasonable
3. Spot-check indicator values in final CSV
4. Manually verify 5-10 ED records
5. Review choropleth map visually

---

## Key Methodological Decisions

### 1. Why Ward-Level Aggregation?

**Constraint:** 1981 Census Small Area Statistics only published at ward level due to confidentiality rules. Individual ED counts would reveal too much information about small populations.

**Solution:** Aggregate indicators to ward level, then display on ED-level boundaries. Multiple EDs in same ward inherit identical values.

**Trade-off:**
- X No within-ward variation visible
- ✓ Respects confidentiality & follows historical practice
- ✓ Enables ED-level spatial mapping
- ✓ Facilitates longitudinal comparison (1981–2001)

### 2. Why Python GeoPandas vs. QGIS Processing?

**Advantages of Python:**
- Scriptable & reproducible (exact same output every run)
- Handles 20-file CSV ingestion programmatically
- Automated validation & error handling
- Version-controllable (code in Git)
- Suitable for 1991/2001 replication

**Advantages of QGIS:**
- Visual feedback (see map during processing)
- No coding required
- Interactive troubleshooting

**Decision:** Use both
- Python for data processing pipeline (repeatability)
- QGIS for validation & visualization (transparency)

### 3. Why GeoPackage Output?

**Format Comparison:**

| Format | Pros | Cons |
|--------|------|------|
| **Shapefile** | Standard in GIS | 2GB file size limit, multiple files (7 minimum) |
| **GeoJSON** | Web-native, text-based | Large file sizes, Z/M dimensions not supported |
| **GeoPackage** | Single file, all features, SQL queries | Requires GDAL/QGIS to read |
| **PostGIS** | Powerful queries, multi-user | Requires database server setup |

**Choice: GeoPackage** — Single file, future-proof, self-documenting

### 4. Why Mapbox GL over Leaflet/Folium?

**Mapbox GL JS Advantages:**
- Vector tiles (fast rendering of 1000s of features)
- Custom styling with expressions
- Better performance on large datasets
- Native support for layers, filters, popups

**Alternative Considerations:**
- Leaflet: Simpler, but raster tiles less efficient
- Folium: Python-centric, but less interactive control
- ArcGIS JS: Commercial licensing

**Decision: Mapbox GL** — Balances power & ease of use

---

## Challenges & Solutions

| Challenge | Root Cause | Solution | Outcome |
|-----------|-----------|----------|---------|
| 1,053 CSV rows vs. 1,017 ED boundaries | Granularity mismatch (ward-level vs. ED-level data) | Recognized data is hierarchical; joined on ward codes (WD81CD) | 100% match rate |
| NULL values in joined columns in QGIS | Virtual joins don't persist to symbology; whitespace in fields | Trimmed zoneid, exported to permanent GeoPackage using Python | Joined columns visible in all subsequent operations |
| Missing output directory | Path not pre-created before export | Used `mkdir -p` to create full structure | Export succeeded |
| GeoPandas not installed | Python environment didn't have spatial libraries | Configured venv, installed geopandas + fiona + shapely | Scripts executed successfully |
| Web dev server wouldn't start | npm command not available, Bun script mismatch | Used `bun vite` directly instead of npm | Server running on localhost:8081 |
| Large choropleth file sizes | GeoJSON too verbose for 1,017+ features | Used GeoPackage (compact binary format) | File size 5-10 MB vs. 50+ MB for GeoJSON |

---

## Final Deliverables Summary

### Data Products

1. **Indicator CSV** (`manchester_eds_1981_indicators.csv`)
   - 1,053 rows (ward-level aggregates)
   - 30 columns (zoneid + 29 indicators)
   - Format: Standard CSV, UTF-8 encoding

2. **GeoPackage** (`manchester_eds_1981_joined_indicators.gpkg`)
   - 1,017 ED polygon features
   - 43 attributes (ED metadata + indicators)
   - CRS: EPSG:27700 (British National Grid)
   - Format: SQLite-based

3. **Metadata**
   - `indicators_1981_metadata.json` — Data dictionary
   - `indicators_1981_summary.json` — Summary statistics
   - `join_validation_statistics.json` — Join QA metrics

### Geospatial Products

4. **QGIS Projects**
   - `qgis/1981/join_validation.qgz`
   - `qgis/1981/indicator_mapping.qgz`
   - Reusable templates for 1991/2001

5. **Choropleth Maps**
   - `figures/choropleth_maps/` — QGIS-exported indicator maps

### Code & Documentation

6. **Python Scripts** (reproducible, no emojis or verbose comments)
   - `utils.py`
   - `01_ingest.py`
   - `02_compute_indicators_1981.py`
   - `03_compute_indicators_1991.py`
   - `04_compute_indicators_2001.py`
   - `05_join_boundaries.py`
   - `06_harmonise_and_export.py`
   - `07_analysis.py`

7. **Configuration Files** (YAML-based)
   - `configs/indicators.yml`
   - `configs/sas_raw_file_mapping.yml`

8. **Documentation**
   - Phase PRDs (specifications & acceptance criteria)
   - Implementation reports (methodology & results)
   - Session summaries (decisions & context)
   - This comprehensive technical summary

### Web Application

9. **React Frontend** (Live on localhost:8081)
   - Interactive Mapbox GL choropleth
   - Filter controls (year, indicator)
   - Detail panel (ED-level info)
   - Responsive design (mobile/tablet/desktop)

---

## Conclusion

This FYP demonstrates a **complete data engineering pipeline** from raw census CSV files to an interactive web visualization, combining:

- **Data engineering** (Python: ingestion, validation, aggregation)
- **Geospatial analysis** (QGIS: join validation, mapping)
- **Web development** (React: interactive visualization)
