# Manchester Spatial Analysis: Final Year Project

**Last updated:** 28 February 2026

A geospatial data engineering pipeline for analysing the spatial evolution and economic integration of Chinese immigrant communities in Manchester across three census periods (1981, 1991, 2001).

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Installation and Reproduction](#installation-and-reproduction)
4. [Data Pipeline](#data-pipeline)
5. [Key Files & Documentation](#key-files--documentation)
6. [Geography & Codes](#geography--codes)
7. [Data Dictionary](#data-dictionary)
8. [Usage Examples](#usage-examples)
9. [Development](#development)
10. [References](#references)

---

## Overview

### Research Questions

1. How did the spatial distribution of Chinese-born residents in Manchester shift between 1981 and 2001?
2. What changes occurred in housing tenure, housing quality, and employment rates in wards with higher concentrations of Chinese-born residents?
3. Do the trajectories observed at ward and enumeration district level support or complicate existing accounts of suburban dispersal and socioeconomic integration among minority ethnic communities in post-industrial British cities?

### Key Findings

| Metric | Value |
|--------|-------|
| Population growth | ~2,400 Far East-born (1981) → 5,100+ self-identified Chinese (2001), 0.55% → 1.31% of city |
| Index of Dissimilarity | 0.43 (1981) → 0.28 (1991) → 0.32 (2001): moderate and declining segregation |
| Mean ward owner-occupation | +7.3 percentage points across the period |
| Mean ward severe overcrowding | −0.36 percentage points across the period |
| Integration trajectory | Asymmetric convergence: settled family households converged on citywide norms; growing student and transient population depressed aggregate indicators |
| Self-employment | Negatively correlated with Chinese concentration (r = −0.30), consistent with a geographically dispersed catering economy rather than an enclave |
| Peak concentration wards (2001) | Central (6.06%), Ardwick (5.84%), Hulme (3.58%) |

### Data Sources

- **UK Census Small Area Statistics (SAS)** — sourced via UK Data Service / EDINA
  - **1981:** SAS02 (demographics), SAS04 (country of birth), SAS07 (employment), SAS10 (housing) — 5-part split CSVs
  - **1991:** S02 (demographics), S06 (ethnic group), S07 (country of birth), S09 (economic position), S16/S20 (tenure/amenities), S81 (communal establishments) — 4-part split CSVs
  - **2001:** CS001EW (population), CT003EW (ethnicity), CS015EW (country of birth), CS028EW (economic activity), CS049EW (tenure), CS052EW (overcrowding), CS056EW (amenities), CS060EW (car ownership) — ONS dissemination CSVs
- **Digital Boundary Shapefiles** — UK Data Service / EDINA
  - 1981: Enumeration District boundaries (`ED_1981_EW.shp`)
  - 1991: Electoral ward boundaries (`england_wa_1991.shp`)
  - 2001: Output Area boundaries (`england_oa_2001.shp`) + ward boundaries (`england_caswa_2001_clipped.shp`)

### Technical Specification

The pipeline is configured via YAML files and operates at Enumeration District level across 1,053 Manchester EDs (1981), electoral wards (1991), and Output Areas (2001), harmonised to 33 common ward geographies. It computes 29 indicators spanning ethnicity, housing tenure and quality, employment, and economic position. QGIS is used for spatial join validation and choropleth mapping. All workflow steps are documented with accompanying validation scripts to support independent reproduction.

---

## Repository Structure

```
FYP_Data_Pipeline/
│
├── configs/
│   ├── indicators.yml              # 29 indicator definitions (1981/1991/2001)
│   └── sas_raw_file_mapping.yml    # Raw SAS file structure documentation
│
├── data/
│   ├── raw/                        # Raw census CSVs (.gitignored — obtain from UK Data Service)
│   │   ├── sas/                    # 1981: 20 CSV parts (5 parts × 4 tables)
│   │   │   ├── 1981_sas02_part{1-5}.csv   # Demographics
│   │   │   ├── 1981_sas04_part{1-5}.csv   # Country of birth
│   │   │   ├── 1981_sas07_part{1-5}.csv   # Employment
│   │   │   └── 1981_sas10_part{1-5}.csv   # Housing & tenure
│   │   ├── s02ews/                 # 1991: Demographics (4 parts)
│   │   │   └── s02ews{1-4}.csv
│   │   ├── s06ews/                 # 1991: Ethnic group (4 parts)
│   │   │   └── s06ews{1-4}.csv
│   │   ├── s07ews/                 # 1991: Country of birth (4 parts)
│   │   │   └── s07ews{1-4}.csv
│   │   ├── s09ews/                 # 1991: Economic position (4 parts)
│   │   │   └── s09ews{1-4}.csv
│   │   ├── s16ew+s/               # 1991: Tenure & amenities (4 parts)
│   │   │   └── s16ew{1-4}.csv
│   │   ├── s81ews/                 # 1991: Communal establishments (4 parts)
│   │   │   └── s81ews{1-4}.csv
│   │   ├── c01cs001_ons.csv        # 2001: CS001EW – Total population
│   │   ├── c01ct003_ons.csv        # 2001: CT003EW – Ethnic group (incl. Chinese)
│   │   ├── c01cs015_ons.csv        # 2001: CS015EW – Country of birth (Asia proxy)
│   │   ├── c01cs028_ons.csv        # 2001: CS028EW – Economic activity
│   │   ├── c01cs049_ons.csv        # 2001: CS049EW – Tenure
│   │   ├── c01cs052_ons.csv        # 2001: CS052EW – Persons per room
│   │   ├── c01cs056_ons.csv        # 2001: CS056EW – Amenities (bath/WC)
│   │   └── c01cs060_ons.csv        # 2001: CS060EW – Car ownership
│   │
│   ├── processed/
│   │   ├── raw_ed_level/           # Zone-level census data (pipeline input)
│   │   │   ├── 1981/
│   │   │   │   ├── sas02_1981_ed_level.csv    # 1,017 EDs × demographics
│   │   │   │   ├── sas04_1981_ed_level.csv    # 1,017 EDs × country of birth
│   │   │   │   ├── sas07_1981_ed_level.csv    # 1,017 EDs × employment
│   │   │   │   └── sas10_1981_ed_level.csv    # 1,017 EDs × housing
│   │   │   └── 1991/
│   │   │       ├── sas02_1991_ed_level.csv    # Demographics
│   │   │       ├── sas06_1991_ed_level.csv    # Ethnic group
│   │   │       ├── sas07_1991_ed_level.csv    # Country of birth
│   │   │       ├── sas09_1991_ed_level.csv    # Economic position
│   │   │       ├── sas20_1991_ed_level.csv    # Tenure/amenities
│   │   │       └── sas81_1991_ed_level.csv    # Communal establishments
│   │   ├── aggregates/             # Pre-combined reference totals (validation)
│   │   │   ├── census_1981/        # 1981 aggregate CSVs
│   │   │   ├── census_1991/        # 1991_sas02_totalpop_combined.csv
│   │   │   └── census_2001/        # 2001_oas_combined_raw.csv
│   │   ├── indicators/             # Computed indicators per decade
│   │   │   ├── 1981/manchester_eds_1981_indicators.csv
│   │   │   ├── 1991/
│   │   │   ├── 2001/manchester_oas_2001_indicators.csv
│   │   │   └── temporal/           # Cross-decade comparison CSVs
│   │   └── outputs/spatial/        # GeoPackage spatial products
│   │       ├── 1981/manchester_eds_1981_joined_indicators.gpkg
│   │       ├── 1991/manchester_wards_1991_joined_indicators.gpkg
│   │       └── 2001/manchester_oas_2001_joined_indicators.gpkg
│   │
│   └── lookups/                    # Reference/lookup tables
│       ├── 1981_geography_lookup.csv
│       ├── 1981_variable_lookup.csv
│       ├── 1981_table_code_name_lookup.csv
│       ├── 1991_england_wales_scotland_geography_lookup.csv
│       ├── 1991_England_Wales_Scotland_Small_Area_Statistics_variable_lookup.csv
│       ├── 1991_table_code_name_lookup.csv
│       ├── 2001_geography_lookup_england.csv   # OA → ward mapping
│       ├── 2001_variable_lookup_ew.csv
│       └── 2001_table_code_and_names_ukcas_map.csv
│
├── docs/
│   └── full_technical.md                   # Full technical reference
│
├── figures/
│   └── phase6_choropleth_maps/     # QGIS-generated maps (placeholder)
│
├── gis_boundaries/                 # Boundary shapefiles (.gitignored — obtain from UK Data Service)
│   ├── 1981/
│   │   └── ED_1981_EW.shp                     # National ED boundaries (England & Wales)
│   ├── 1991/
│   │   └── england_wa_1991.shp                # Electoral ward boundaries (England & Wales)
│   └── 2001/
│       ├── OA/england_oa_2001.shp             # Output Area boundaries (England)
│       └── wards/england_caswa_2001_clipped.shp  # Ward boundaries (harmonisation anchor)
│
├── gis_boundaries/                 # Boundary shapefiles (.gitignored — obtain from UK Data Service)
│   ├── 1981/                       # ED_1981_EW.shp — National ED boundaries (England & Wales)
│   ├── 1991/                       # england_wa_1991.shp — Electoral ward boundaries
│   └── 2001/
│       ├── OA/                     # england_oa_2001.shp — Output Area boundaries
│       └── wards/                  # england_caswa_2001_clipped.shp — Ward boundaries
│
├── qgis/
│   └── 1981/
│       ├── join_validation.qgz     # Join QA — 100% match rate (1,017 EDs)
│       └── indicator_mapping.qgz   # Indicator choropleth template
│
├── scripts/
│   ├── utils.py                    # Shared helpers (safe_rate, weighted_mean, dissimilarity_index)
│   ├── 01_ingest.py                # Step 1: Raw data ingestion (1981, 1991, 2001)
│   ├── 02_compute_indicators_1981.py  # Step 2a: Compute indicators (1981 EDs)
│   ├── 03_compute_indicators_1991.py  # Step 2b: Compute indicators (1991 EDs + wards)
│   ├── 04_compute_indicators_2001.py  # Step 2c: Compute indicators (2001 OAs)
│   ├── 05_join_boundaries.py          # Step 3: Spatial join (1981, 1991, 2001)
│   ├── 06_harmonise_and_export.py     # Step 4: Harmonise ward boundaries + export GeoJSON
│   └── 07_analysis.py                 # Step 5: Dissertation analysis (RQ1–RQ5)
│
└── .venv/                          # Python virtual environment (gitignored)

```

---

## Installation and Reproduction

### Prerequisites

```bash
# Python 3.9+ required
python3 --version

# Install dependencies
pip install pandas pyyaml geopandas
```

### 1. Clone the Repository

```bash
git clone https://github.com/jourdee-lab/FYP_Data_Pipeline.git
cd FYP_Data_Pipeline
```

### 2. Set Up the Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # (if available)
```

### 3. Run the Pipeline

```bash
# Step 1: Ingest all three census years
python scripts/01_ingest.py

# Step 2: Compute indicators
python scripts/02_compute_indicators_1981.py
python scripts/03_compute_indicators_1991.py
python scripts/04_compute_indicators_2001.py

# Step 3: Spatial joins
python scripts/05_join_boundaries.py

# Step 4: Harmonise ward boundaries and export web GeoJSON
python scripts/06_harmonise_and_export.py

# Step 5: Run dissertation analysis
python scripts/07_analysis.py
```

### 4. Inspect Outputs

```bash
# Check indicator output
head -5 data/processed/indicators/1981/manchester_eds_1981_indicators.csv

# View summary statistics
cat data/processed/indicators/1981/indicators_summary.txt
```

---

## Data Pipeline

### Phase 1–4: Data Preparation (Complete)

- Aggregate city-level SAS tables (SAS02, SAS04, SAS07, SAS10)
- Create Manchester filter logic (`zoneid.startswith("03BN")`)
- Define indicator formulas and denominators

### Phase 5: QGIS Join Validation (Complete)

- **Goal:** Validate join between ED boundaries and census data
- **Result:** 100% match rate (1,017 EDs)
- **Outputs:**
  - `qgis/1981/join_validation.qgz`

### Phase 6: Indicator Construction (Complete)

- **Goal:** Compute indicators at ED, ward, and OA level across all three census years
- **Process:**
  1. Ingest raw SAS CSV files into zone-level data frames
  2. Compute 29 indicators (demographics, ethnicity, housing, employment)
  3. Export per-decade indicator tables and an ED-level detail table
- **Outputs:**
  - `data/processed/indicators/1981/manchester_eds_1981_indicators.csv`
  - `data/processed/indicators/1981/manchester_eds_1981_indicators_ed_level.csv`
  - `data/processed/indicators/1991/manchester_wards_1991_indicators.csv`
  - `data/processed/indicators/2001/manchester_oas_2001_indicators.csv`
  - `data/processed/indicators/temporal/` (harmonised cross-decade comparison files)

### Phase 7: Mapping & Analysis (Complete)

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
| `01_ingest_1981_eds.py` | Ingest 1981 raw CSVs into ED-level data | Active |
| `02_ingest_1991_eds.py` | Ingest 1991 raw CSVs into ED-level data | Active |
| `03_ingest_2001_oas.py` | Ingest 2001 raw CSVs into OA-level data | Active |
| `04_compute_indicators_1981_eds.py` | Compute 25 indicators (1981 EDs) | Active |
| `05_compute_indicators_1991_eds.py` | Compute indicators (1991 EDs) | Active |
| `06_compute_indicators_1991_wards.py` | Compute indicators (1991 wards) | Active |
| `07_compute_indicators_2001_oas.py` | Compute indicators (2001 OAs) | Active |
| `08_join_boundaries_1981_eds.py` | Spatial join: 1981 EDs | Active |
| `09_join_boundaries_1991_wards.py` | Spatial join: 1991 wards | Active |
| `10_join_boundaries_2001_oas.py` | Spatial join: 2001 OAs | Active |
| `11_harmonise_ward_boundaries.py` | Harmonise ward boundaries across decades | Active |
| `12_aggregate_2001_oas_to_wards.py` | Aggregate 2001 OAs to ward level | Active |
| `13_export_web_geojson.py` | Export GeoJSON for the web application | Active |
| `utils_convert_gpkg_to_geojson.py` | Utility: GeoPackage to GeoJSON conversion | Active |

### Documentation (Key)

| Document | Purpose |
|----------|---------|
| `PHASE_6_MASTER.md` | Complete Phase 6 guide (consolidated) |
| `PHASES_5_MASTER.md` | Complete Phase 5 guide (join validation) |
| `docs/join_log_1981_ed_qgis.md` | Phase 5 audit trail |
| `docs/phase6_indicator_documentation/PHASE_6_IMPLEMENTATION_REPORT.md` | Phase 6 technical report |

## Geography & Codes

### Manchester LAD Code

- **1981 Census:** `03BN` (Greater Manchester - Manchester district)
- **Geography Type:** Enumeration Districts (EDs)
- **Total Manchester EDs:** 1,053 (includes aggregate rows with prefix `03BN`)

### ED Code Format

- Example: `03BNFA01`, `03BNFA02`, ..., `03BNZZ99`
- Structure: `03BN` (LAD) + `FA` (ward/area) + `01` (ED number)

---

## Census Raw Data Inventory

All raw files are stored in `data/raw/` and excluded from version control (`.gitignore`). They must be obtained from the [UK Data Service](https://census.ukdataservice.ac.uk/) before running the pipeline.

### 1981 — Small Area Statistics (SAS)

Geography: Enumeration Districts (EDs). Manchester LAD prefix: `03BN`.

| Raw files | Table | Topic | Parts | Expected cols |
|-----------|-------|-------|-------|---------------|
| `1981_sas02_part{1-5}.csv` | SAS02 | Demographics – Total population by age/sex | 5 | 161 |
| `1981_sas04_part{1-5}.csv` | SAS04 | Country of birth (birthplace) | 5 | 61 |
| `1981_sas07_part{1-5}.csv` | SAS07 | Employment & economic activity | 5 | 28 |
| `1981_sas10_part{1-5}.csv` | SAS10 | Housing & tenure | 5 | 221 |

> Each file is a horizontal slice of the full national table. Parts are concatenated on `zoneid` and filtered to `03BN` by `01_ingest_1981_eds.py`.

#### 1981 Boundary & Lookup Files

| File | Purpose | Used by |
|------|---------|--------|
| `gis_boundaries/1981/ED_1981_EW.shp` | National ED polygons | `08_join_boundaries_1981_eds.py`, `11_harmonise_ward_boundaries.py` |
| `data/lookups/1981_geography_lookup.csv` | ED code → geography name | Reference |
| `data/lookups/1981_variable_lookup.csv` | SAS code → variable label | Reference |
| `data/lookups/1981_table_code_name_lookup.csv` | Table code → description | Reference |

---

### 1991 — Small Area Statistics (SAS)

Geography: Enumeration Districts (EDs) aggregated to electoral wards. Manchester prefix: `03BN`.

| Raw files | Table | Topic | Parts | Expected cols |
|-----------|-------|-------|-------|---------------|
| `s02ews/s02ews{1-4}.csv` | S02EWS | Demographics – age & marital status | 4 | ~155 |
| `s06ews/s06ews{1-4}.csv` | S06EWS | Ethnic group | 4 | ~12 |
| `s07ews/s07ews{1-4}.csv` | S07EWS | Country of birth | 4 | ~61 |
| `s09ews/s09ews{1-4}.csv` | S09EWS | Economic position | 4 | ~52 |
| `s16ew+s/s16ew{1-4}.csv` | S16EW+S | Tenure & amenities | 4 | ~227 |
| `s81ews/s81ews{1-4}.csv` | S81EWS | Communal establishments | 4 | ~28 |

> Variable columns use the `sXXXXXX` naming convention (e.g. `s020001`) rather than the 1981-style `81sasXXXXXX` prefix.

#### 1991 Boundary & Lookup Files

| File | Purpose | Used by |
|------|---------|--------|
| `gis_boundaries/1991/england_wa_1991.shp` | Electoral ward polygons | `11_harmonise_ward_boundaries.py` |
| `gis_boundaries/1991/1991_wards_ew.shp` | Ward polygons (alternative) | `09_join_boundaries_1991_wards.py` |
| `data/lookups/1991_england_wales_scotland_geography_lookup.csv` | Zone code → geography | Reference |
| `data/lookups/1991_England_Wales_Scotland_Small_Area_Statistics_variable_lookup.csv` | Variable labels | Reference |
| `data/lookups/1991_table_code_name_lookup.csv` | Table code → description | Reference |

---

### 2001 — Census Area Statistics (CAS)

Geography: Output Areas (OAs), aggregated to wards. Manchester prefix: `00BN`. OA codes are exactly 10 characters (e.g. `00BNFA0001`).

| Raw file | Table | Topic |
|----------|-------|-------|
| `c01cs001_ons.csv` | CS001EW | Total population |
| `c01ct003_ons.csv` | CT003EW | Ethnic group (incl. Chinese/Chinese British) |
| `c01cs015_ons.csv` | CS015EW | Country of birth – Asia proxy |
| `c01cs028_ons.csv` | CS028EW | Economic activity (ages 16–74) |
| `c01cs049_ons.csv` | CS049EW | Tenure |
| `c01cs052_ons.csv` | CS052EW | Persons per room (overcrowding) |
| `c01cs056_ons.csv` | CS056EW | Amenities (bath/WC) |
| `c01cs060_ons.csv` | CS060EW | Car or van ownership |

> Files are in long format (`zoneid | variable | value`). `03_ingest_2001_oas.py` pivots to wide, filters to `00BN`, and merges all tables into `2001_oas_combined_raw.csv`.

#### 2001 Boundary & Lookup Files

| File | Purpose | Used by |
|------|---------|--------|
| `gis_boundaries/2001/OA/england_oa_2001.shp` | Output Area polygons | `10_join_boundaries_2001_oas.py` |
| `gis_boundaries/2001/wards/england_caswa_2001_clipped.shp` | Ward polygons (harmonisation anchor) | `11_harmonise_ward_boundaries.py` |
| `data/lookups/2001_geography_lookup_england.csv` | OA → ward code mapping | `12_aggregate_2001_oas_to_wards.py` |
| `data/lookups/2001_variable_lookup_ew.csv` | Variable labels | Reference |
| `data/lookups/2001_table_code_and_names_ukcas_map.csv` | Table code → description | Reference |

---

## Data Dictionary

### 25 Computed Indicators (1981)

#### Demographics (SAS02)
- `TOTAL_RES_1981`: Total residents (count)
- `PCT_MALE_1981`: % male residents
- `PCT_FEMALE_1981`: % female residents

#### Ethnicity/Birthplace (SAS04)
- `CHINESE_BORN_1981`: Far East-born residents (count)
- `PCT_CHINESE_BORN_1981`: % Far East-born of total residents

#### Housing Quality (SAS10)
- `TOTAL_HH_1981`: Total households (denominator)
- `NO_CAR_HH_1981`: Households with no car (count)
- `PCT_NO_CAR_1981`: % households with no car
- `OVERCROWD_GT1P5_1981`: Overcrowded households >1.5 pp/room (count)
- `PCT_OVERCROWD_GT1P5_1981`: % overcrowded households
- `NO_BATH_OR_WC_HH_1981`: Households lacking bath or WC (count)
- `PCT_NO_BATH_OR_WC_1981`: % lacking bath/WC
- `NO_INSIDE_BATH_OR_WC_1981`: Households with no inside bath/WC (count)
- `PCT_NO_INSIDE_BATH_WC_1981`: % no inside bath/WC

#### Tenure (SAS10)
- `OWNER_OCC_HH_1981`: Owner-occupied households (count)
- `PCT_OWNER_OCC_1981`: % owner-occupied
- `SOCIAL_RENT_HH_1981`: Social rented households (count)
- `PCT_SOCIAL_RENT_1981`: % social rented

#### Employment (SAS07)
- `RES_16PLUS_1981`: Residents aged 16+ (count)
- `EMPLOYED_1981`: Employed residents (count)
- `UNEMPLOYED_1981`: Unemployed residents (count)
- `EMP_RATE_1981`: Employment rate (%)
- `UNEMP_RATE_1981`: Unemployment rate (%)

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
boundaries = gpd.read_file('gis_boundaries/1981/ED_1981_EW.shp')
boundaries = boundaries[boundaries['ED81CD'].str.startswith('03BN')]

# Load indicators
indicators = pd.read_csv('data/processed/indicators/1981/manchester_eds_1981_indicators.csv')

# Join
joined = boundaries.merge(indicators, left_on='ED81CD', right_on='zoneid', how='left')

# Export to GeoPackage
joined.to_file('outputs/manchester_1981_indicators.gpkg', driver='GPKG')
```

### Reproduce the Full Pipeline

```bash
source .venv/bin/activate

python scripts/01_ingest.py
python scripts/02_compute_indicators_1981.py
python scripts/03_compute_indicators_1991.py
python scripts/04_compute_indicators_2001.py
python scripts/05_join_boundaries.py
python scripts/06_harmonise_and_export.py
python scripts/07_analysis.py
```

---

### Testing

```bash
# Run unit tests (if available)
pytest tests/

# Validate join
python scripts/validate_join_manual.py
```

### Adding or Extending Data

1. Update `configs/indicators.yml` with new SAS codes if needed
2. Re-ingest if raw data changes: `python scripts/01_ingest.py`
3. Rerun the relevant compute script (`02_`, `03_`, or `04_compute_indicators_*.py`)
4. Regenerate harmonised output and web GeoJSON: `python scripts/06_harmonise_and_export.py`

---

## References

### Academic Sources

- Benton, G. and Gomez, E.T. (2008). *The Chinese in Britain, 1800–Present: Economy, Transnationalism, Identity*. Basingstoke: Palgrave Macmillan.
- Massey, D.S. and Denton, N.A. (1988). 'The dimensions of residential segregation', *Social Forces*, 67(2), pp. 281–315.
- Parker, D. (1998). 'Rethinking British Chinese identities', in T. Skelton and G. Valentine (eds) *Cool Places: Geographies of Youth Cultures*. London: Routledge, pp. 66–82.
- Peach, C. (1996). 'Does Britain have ghettos?', *Transactions of the Institute of British Geographers*, 21(1), pp. 216–235.
- Simpson, L. (2004). 'Statistics of racial segregation: measures, evidence and policy', *Urban Studies*, 41(3), pp. 661–681.

### Data & Technical Sources

- **Digital Artifact:** [https://mappingfyp.vercel.app](https://mappingfyp.vercel.app)
- **UK Data Service Census Archive:** [https://census.ukdataservice.ac.uk/](https://census.ukdataservice.ac.uk/)
- **EDINA Census Geography:** [https://edina.ac.uk/census/](https://edina.ac.uk/census/)
- **QGIS:** [https://qgis.org/](https://qgis.org/)
- **GeoPandas Documentation:** [https://geopandas.org/](https://geopandas.org/)
- **Pandas Documentation:** [https://pandas.pydata.org/docs/](https://pandas.pydata.org/docs/)

---

## Contributors

- **Author:** Jourdan Tan
- **Institution** (NUI) University College Cork
- **Supervisor:** Dr.Shawn Day

---

## License

Academic research project. Census data sourced from UK Data Service under End User License. Original data is Crown Copyright.

---

## Support

For queries regarding the pipeline or data:
- Open a GitHub issue in this repository
- Consult `docs/full_technical.md` for full technical reference
