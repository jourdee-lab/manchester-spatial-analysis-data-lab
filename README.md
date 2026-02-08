# Manchester Spatial Analysis FYP (Work In Progress)

**Status:** Phase 6 Complete | ED-Level Indicators Computed  
**Last Updated:** 2026-01-14  

A reproducible geospatial data engineering pipeline for analyzing the spatial evolution and economic integration of Chinese immigrant communities in Manchester across three census periods (1981, 1991, 2001).

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Quick Start](#quick-start)
4. [Data Pipeline](#data-pipeline)
5. [Key Files & Documentation](#key-files--documentation)
6. [Phase Status](#phase-status)
7. [Geography & Codes](#geography--codes)
8. [Data Dictionary](#data-dictionary)
9. [Usage Examples](#usage-examples)
10. [Development](#development)
11. [References](#references)

---

## Overview

### Research Questions

1. How did the spatial distribution of Chinese immigrants in Manchester change from 1981 to 2001?
2. What were the trends in housing quality, tenure, and economic indicators across census periods?
3. Did areas with higher Chinese-born populations show distinct integration trajectories?

### Data Sources

- **UK Census Small Area Statistics (SAS)** — 1981, 1991, 2001
  - SAS02 (demographics), SAS04 (country of birth), SAS07 (employment), SAS10 (housing)
- **Digital Boundary Data** — Enumeration Districts (1981), Output Areas (2001)
- **UK Data Service / EDINA**

### Key Features

**Configuration-driven pipeline** (YAML-based, no hardcoding)  
**ED-level analysis** (1,053 Manchester Enumeration Districts)  
**25 computed indicators** (ethnicity, housing, employment, tenure)  
**QGIS integration** (join validation, mapping templates)  
**Reproducible workflows** (documented procedures, validation scripts)

---

## Repository Structure

```
FYP_Data_Pipeline/
├── .github/
│   └── instructions/               # Project phase specifications (PRDs)
│       ├── fyp_phase_5.instructions.md
│       ├── fyp_phase_6.instructions.md
│       └── Repository clean.instructions.md
│
├── configs/
│   ├── indicators.yml              # 29 indicator definitions (1981/1991/2001)
│   └── sas_raw_file_mapping.yml    # Raw SAS file structure documentation
│
├── data/
│   ├── raw/                        # Raw census CSVs (.gitignored)
│   │   └── census_1981/            # 20 SAS CSV files (5 parts × 4 tables)
│   │       ├── 81sas02ews/SAS02_1981_part{1-5}.csv
│   │       ├── 81sas04ews/SAS04_1981_part{1-5}.csv
│   │       ├── 81sas07ews/SAS07_1981_part{1-5}.csv
│   │       └── 81sas10ews/SAS10_1981_part{1-5}.csv
│   │
│   ├── processed/
│   │   ├── raw_ed_level/           # ED-level census data (Phase 6 input)
│   │   │   └── census_1981/
│   │   │       ├── sas02_1981_ed_level.csv    # 1,053 EDs × demographics
│   │   │       ├── sas04_1981_ed_level.csv    # 1,053 EDs × country of birth
│   │   │       ├── sas07_1981_ed_level.csv    # 1,053 EDs × employment
│   │   │       └── sas10_1981_ed_level.csv    # 1,053 EDs × housing
│   │   │
│   │   ├── indicators/             # Computed indicators (Phase 6 output)
│   │   │   └── 1981/
│   │   │       └── manchester_eds_1981_indicators.csv  # 1,053 EDs × 25 indicators
│   │   │
│   │   └── outputs/spatial/        # Spatial data products
│   │       └── 1981/
│   │           └── manchester_eds_1981_joined_attributes.csv
│   │
│   └── lookups/                    # Reference/lookup tables
│       ├── 1981_geography_lookup.csv          # ED code → geography mapping
│       ├── 1981_variable_lookup.csv           # SAS code → variable label
│       ├── 1981_table_code_name_lookup.csv    # Table definitions
│       └── 1991_table_code_name_lookup.csv
│
├── docs/
│   ├── archived/                   # Session logs and historical docs
│   │   └── SESSION_SUMMARY_2026_01_14.md
│   │
│   ├── phase6_indicator_documentation/
│   │   ├── PHASE_6_IMPLEMENTATION_REPORT.md
│   │   ├── PHASE_6_README.md
│   │   ├── indicators_1981_metadata.json
│   │   |── indicators_1981_summary.json
│   │   └── master_guide.md
│   │
│   ├── ingest_raw_sas_ed_level.md
│   ├── join_log_1981_ed_qgis.md
│   ├── join_validation_statistics.json
│   └── join_validation_summary.md
│
├── figures/
│   └── phase6_choropleth_maps/     # QGIS-generated maps (placeholder)
│
├── gis_boundaries/                 # Boundary shapefiles
│   └── 1981_ed_manchester/
│       ├── ED_1981_EW.shp          # 1,017 Manchester EDs (national dataset)
│       └── manchester_ed_level_sas_template.csv  # Phase 5 join template
│
├── notebooks/
│   ├── build_pipeline.ipynb        # Pipeline development/testing
│   └── merging.ipynb               # Data merging experiments
│
├── qgis/
│   ├── phase5_join_validation_1981_eds.qgz      # Phase 5 QGIS project
│   └── phase6_indicator_mapping_1981.qgz        # Phase 6 mapping template
│
├── scripts/
│   ├── ingest_raw_sas_ed_level_1981.py          # Data ingestion (5-part CSVs → ED-level)
│   ├── phase6_compute_indicators_1981_ed_level.py  # Indicator computation (main)
│   ├── phase6_compute_indicators_1981.py        # Original version (reference)
│   ├── phase6_compute_indicators_simple.py      # Simplified version (testing)
│   ├── prepare_ed_level_census.py               # Phase 5: ED extraction script
│   ├── validate_join_manual.py                  # Phase 5: Join validation
│   └── create_qgis_join_project.py              # Phase 5: QGIS project setup
│
├── master_guide.md                 # Project master guide
├── initial_prd.md                  # Initial project requirements
└── README.md                       # This file

```

---

## Quick Start

### Prerequisites

```bash
# Python 3.9+ required
python3 --version

# Install dependencies
pip install pandas pyyaml geopandas
```

### 1. Clone Repository

```bash
git clone https://github.com/jourdee-lab/FYP_Data_Pipeline.git
cd FYP_Data_Pipeline
```

### 2. Set Up Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # (if available)
```

### 3. Run Phase 6 Pipeline (1981 Indicators)

```bash
# Step 1: Ingest raw SAS data (creates ED-level CSVs)
python scripts/ingest_raw_sas_ed_level_1981.py

# Step 2: Compute indicators
python scripts/phase6_compute_indicators_1981_ed_level.py

# Output: data/processed/indicators/1981/manchester_eds_1981_indicators.csv
```

### 4. View Results

```bash
# Check indicator output
head -5 data/processed/indicators/1981/manchester_eds_1981_indicators.csv

# View summary statistics
cat data/processed/indicators/1981/indicators_summary.txt
```

---

## Data Pipeline

### Phase 1–4: Data Preparation (Complete ✓)

- Aggregate city-level SAS tables (SAS02, SAS04, SAS07, SAS10)
- Create Manchester filter logic (`zoneid.startswith("03BN")`)
- Define indicator formulas and denominators

### Phase 5: QGIS Join Validation (Complete ✓)

- **Goal:** Validate join between ED boundaries and census data
- **Result:** 100% match rate (1,017 EDs)
- **Outputs:** 
  - `qgis/phase5_join_validation_1981_eds.qgz`
  - `docs/join_log_1981_ed_qgis.md`

### Phase 6: Indicator Construction (Complete ✓)

- **Goal:** Compute ED-level indicators for mapping
- **Process:**
  1. Ingest 20 raw SAS CSV files → 4 ED-level CSVs (1,053 EDs)
  2. Compute 25 indicators (demographics, ethnicity, housing, employment)
  3. Export indicator table for QGIS mapping
- **Outputs:**
  - `data/processed/indicators/1981/manchester_eds_1981_indicators.csv`
  - `docs/phase6_indicator_documentation/` (metadata, summaries)

### Phase 7: Mapping & Analysis (In Progress)

- Create QGIS choropleths
- Statistical analysis (correlation, clustering)
- Longitudinal comparison (1981 vs 1991 vs 2001)

---

## Key Files & Documentation

### Configuration

| File | Purpose |
|------|---------|
| `configs/indicators.yml` | 29 indicator definitions with SAS code mappings |
| `configs/sas_raw_file_mapping.yml` | Raw file structure documentation |

### Scripts (Production)

| Script | Purpose | Status |
|--------|---------|--------|
| `ingest_raw_sas_ed_level_1981.py` | Ingest 20 raw CSVs → ED-level data | ✓ Active |
| `phase6_compute_indicators_1981_ed_level.py` | Compute 25 indicators from ED data | ✓ Active |
| `validate_join_manual.py` | Phase 5 join validation | ✓ Active |
| `prepare_ed_level_census.py` | Phase 5 ED extraction | ✓ Active |
| `create_qgis_join_project.py` | Phase 5 QGIS setup | ✓ Active |

### Documentation (Key)

| Document | Purpose |
|----------|---------|
| `PHASE_6_MASTER.md` | Complete Phase 6 guide (consolidated) |
| `PHASES_5_MASTER.md` | Complete Phase 5 guide (join validation) |
| `docs/join_log_1981_ed_qgis.md` | Phase 5 audit trail |
| `docs/phase6_indicator_documentation/PHASE_6_IMPLEMENTATION_REPORT.md` | Phase 6 technical report |

---

## Phase Status

| Phase | Description | Status | Output |
|-------|-------------|--------|--------|
| **1–4** | Aggregate data + configuration | ✓ Complete | City-level profiles |
| **5** | QGIS join validation | ✓ Complete | 100% match rate, QGIS project |
| **6** | ED-level indicator computation | ✓ Complete | 1,053 EDs × 25 indicators |
| **7** | Mapping & visualization | In Progress | QGIS choropleths |
| **8** | Longitudinal analysis (1991/2001) | Planned | Trend analysis |

---

## Geography & Codes

### Manchester LAD Code

- **1981 Census:** `03BN` (Greater Manchester - Manchester district)
- **Geography Type:** Enumeration Districts (EDs)
- **Total Manchester EDs:** 1,053 (includes aggregate rows with prefix `03BN`)

### ED Code Format

- Example: `03BNFA01`, `03BNFA02`, ..., `03BNZZ99`
- Structure: `03BN` (LAD) + `FA` (ward/area) + `01` (ED number)

---

## Data Dictionary

### 25 Computed Indicators (1981)

#### Demographics (SAS02)
- `TOTAL_RES_1981` — Total residents (count)
- `PCT_MALE_1981` — % male residents
- `PCT_FEMALE_1981` — % female residents

#### Ethnicity/Birthplace (SAS04)
- `CHINESE_BORN_1981` — Far East-born residents (count)
- `PCT_CHINESE_BORN_1981` — % Far East-born of total residents

#### Housing Quality (SAS10)
- `TOTAL_HH_1981` — Total households (denominator)
- `NO_CAR_HH_1981` — Households with no car (count)
- `PCT_NO_CAR_1981` — % households with no car
- `OVERCROWD_GT1P5_1981` — Overcrowded households >1.5 pp/room (count)
- `PCT_OVERCROWD_GT1P5_1981` — % overcrowded households
- `NO_BATH_OR_WC_HH_1981` — Households lacking bath or WC (count)
- `PCT_NO_BATH_OR_WC_1981` — % lacking bath/WC
- `NO_INSIDE_BATH_OR_WC_1981` — Households with no inside bath/WC (count)
- `PCT_NO_INSIDE_BATH_WC_1981` — % no inside bath/WC

#### Tenure (SAS10)
- `OWNER_OCC_HH_1981` — Owner-occupied households (count)
- `PCT_OWNER_OCC_1981` — % owner-occupied
- `SOCIAL_RENT_HH_1981` — Social rented households (count)
- `PCT_SOCIAL_RENT_1981` — % social rented

#### Employment (SAS07)
- `RES_16PLUS_1981` — Residents aged 16+ (count)
- `EMPLOYED_1981` — Employed residents (count)
- `UNEMPLOYED_1981` — Unemployed residents (count)
- `EMP_RATE_1981` — Employment rate (%)
- `UNEMP_RATE_1981` — Unemployment rate (%)

### Key SAS Codes (1981)

| Indicator | SAS Code | Description |
|-----------|----------|-------------|
| Total Residents | `81sas020050` | All ages, total persons |
| Far East Born | `81sas040359` | Persons born in Far East |
| Total Households | `81sas100929` | Households with residents (tenure base) |
| No Car | `81sas100958` | Households with no car |
| Overcrowding | `81sas100945` | Households >1.5 persons/room |
| No Bath/WC | `81sas100932` | Households lacking bath or WC |
| Owner-Occupied | `81sas100967` | Owner-occupied households |

*Full SAS code mappings in `configs/indicators.yml`*

---

## Usage Examples

### Load Indicator Data

```python
import pandas as pd

# Load computed indicators
indicators = pd.read_csv('data/processed/indicators/1981/manchester_eds_1981_indicators.csv')

# View summary
print(indicators.describe())

# Filter high Chinese-born concentration EDs
high_chinese = indicators[indicators['PCT_CHINESE_BORN_1981'] > 5.0]
print(high_chinese[['zoneid', 'PCT_CHINESE_BORN_1981', 'PCT_OWNER_OCC_1981']])
```

### Join to Boundaries in Python

```python
import geopandas as gpd

# Load boundaries
boundaries = gpd.read_file('gis_boundaries/1981_ed_manchester/ED_1981_EW.shp')
boundaries = boundaries[boundaries['ED81CD'].str.startswith('03BN')]

# Load indicators
indicators = pd.read_csv('data/processed/indicators/1981/manchester_eds_1981_indicators.csv')

# Join
joined = boundaries.merge(indicators, left_on='ED81CD', right_on='zoneid', how='left')

# Export to GeoPackage
joined.to_file('outputs/manchester_1981_indicators.gpkg', driver='GPKG')
```

### Reproduce Phase 6 Pipeline

```bash
# Full Phase 6 workflow
source .venv/bin/activate

# Step 1: Ingest (5 minutes)
python scripts/ingest_raw_sas_ed_level_1981.py

# Step 2: Compute indicators (2 minutes)
python scripts/phase6_compute_indicators_1981_ed_level.py

# Step 3: Validate output
python -c "import pandas as pd; df = pd.read_csv('data/processed/indicators/1981/manchester_eds_1981_indicators.csv'); print(f'Shape: {df.shape}'); print(df.head())"
```

---

## Development

### Repository Cleanup (Staging Branch)

This `staging` branch includes repository cleanup following the "Repository Janitor" protocol:

**Deleted Files:**
- Redundant Python scripts (superseded versions)
- Obsolete aggregate CSVs (city-level summaries)
- Duplicate documentation files
- Python cache directories

**Consolidated Documentation:**
- Phase 5: `PHASES_5_MASTER.md` (merged from 2 files)
- Phase 6: Content integrated into `PHASE_6_MASTER.md`

### Testing

```bash
# Run unit tests (if available)
pytest tests/

# Validate join
python scripts/validate_join_manual.py
```

### Adding 1991/2001 Data

1. Update `configs/indicators.yml` with 1991/2001 SAS codes
2. Copy `ingest_raw_sas_ed_level_1981.py` → `ingest_raw_sas_ed_level_1991.py`
3. Update paths and year parameters
4. Run ingestion + indicator computation
5. Perform areal interpolation for boundary changes (Phase 8)

---

## References

- **UK Data Service Census Support:** [https://census.ukdataservice.ac.uk/](https://census.ukdataservice.ac.uk/)
- **Casweb:** Online census data extraction
- **SAS Documentation:** UK Data Service variable lookups
- **QGIS:** [https://qgis.org/](https://qgis.org/)

---

## Contributors

- **Author:** Jourdan Tan
- **Institution** (NUI) University College Cork
- **Supervisor:** Dr.Shawn Day

---

## License

Academic research project. Census data sourced from UK Data Service under End User License. Original data is Crown Copyright.

---

## Questions?

For issues or questions:
- Open a GitHub issue
- Consult `docs/phase6_indicator_documentation/masterguide.md` for detailed workflow
- Check `docs/phase6_indicator_documentation/` for troubleshooting

---
**Status:** Phase 6 Complete, Phase 7 In Progress  
**Last Updated:** 2026-01-14
