# FYP Data Pipeline

A geospatial data engineering pipeline for analyzing the spatial evolution and economic integration of Chinese immigrant communities in Manchester (1981–2001).

## Overview

This project processes UK Census Small Area Statistics (SAS) microdata from the 1981 and 1991 censuses to extract, aggregate, and analyze country-of-birth demographics, with a focus on Far East and Chinese immigrant populations across Manchester's wards and enumeration districts.

## Project Scope

- **Research Question**: How did Chinese immigrant communities spatially organize and economically integrate in Manchester over two decades?
- **Geography**: Manchester (City of Manchester, 1981 zone code: `03BN`)
- **Census Years**: 1981, 1991 (2001 planned)
- **Key Variables**: Country of birth (SAS04), ancestry, occupation, housing tenure
- **Methodology**: GIS, data engineering, digital humanities

## Repository Structure

```
FYP_Data_Pipeline/
├── README.md                             # Project overview (this file)
├── pyproject.toml                        # Python project config + dependencies
├── .gitignore                            # Git exclusions (data/, *.pyc, etc.)
├── Makefile                              # Common commands (optional)
│
├── configs/
│   ├── sources.yml                       # Data source URLs, versions
│   ├── geography.yml                     # Manchester codes, ward filters
│   └── pipeline.yml                      # Run parameters, years, tables
│
├── data/
│   ├── raw/
│   │   └── census_1981/
│   │       ├── sas04_1981_full.csv       # ← Combined (single file, not splits)
│   │       ├── 1981_geography_lookup.csv # ← Zone ID ↔ name mapping
│   │       └── 1981_table_code_name_lookup.csv
│   ├── interim/
│   │   └── sas04_1981_validated.parquet  # Typed, indexed version (generated)
│   └── processed/
│       └── sas04_manchester_1981.csv     # Final aggregated dataset
│
├── outputs/
│   ├── aggregates/
│   │   └── manchester/
│   │       ├── 1981/
│   │       │   └── sas04_summary.csv
│   │       └── 1991/  # (forthcoming)
│   ├── figures/
│   └── logs/
│
├── notebooks/
│   ├── 01_ingest_validate.ipynb         # Load & validate raw SAS04
│   ├── 02_explore_sas04.ipynb           # EDA: distribution, patterns
│   └── 03_manchester_checks.ipynb       # Verify Manchester aggregates
│
├── src/fyp_pipeline/
│   ├── __init__.py
│   ├── io/
│   │   ├── read_sas.py                  # Load/concat SAS CSV → DataFrame
│   │   └── paths.py                     # Path helpers (raw/, processed/, etc.)
│   ├── lookups/
│   │   ├── geography.py                 # Manchester codes, ward lists
│   │   └── variables.py                 # Map 81sas04XXXX → labels
│   ├── transforms/
│   │   ├── clean.py                     # Column cleaning, type coercion
│   │   └── validate.py                  # Schema validation, checks
│   ├── aggregates/
│   │   └── manchester.py                # Sum zoneids starting with 03BN
│   └── cli.py                           # Optional CLI entrypoint
│
├── scripts/
│   ├── ingest_1981_sas04.py            # Download → combine → validate
│   ├── aggregate_manchester_1981.py    # Filter & sum → output
│   └── build_all.py                     # Run full pipeline end-to-end
│
└── tests/
    ├── test_geography_codes.py
    ├── test_aggregate_manchester.py
    └── conftest.py


### Census Data (SAS04)

| File | Location | Purpose |
|------|---|---|
| `sas04_1981_full.csv` | `data/raw/census_1981/` | **Single combined file** (not 5 splits); raw microdata |
| `1981_geography_lookup.csv` | `data/raw/census_1981/` | Link zone IDs to area names & types |
| `1981_table_code_name_lookup.csv` | `data/raw/census_1981/` | SAS table metadata (50 tables) |
| `sas04_1981_validated.parquet` | `data/interim/` | Typed, indexed version (auto-generated) |
| `sas04_manchester_1981.csv` | `data/processed/` | Manchester (03BN) aggregated final data |

### Key SAS04 Variables

- `81sas040359` — Total persons born in Far East
- `81sas040360` — Males born in Far East
- `81sas040361` — Females born in Far East

(See `1981_variable_lookup.csv` for full 61-variable breakdown)

## Quick Start

### 1. Set up environment

```bash
cd FYP_Data_Pipeline

# Install dependencies
pip install -r requirements.txt
# OR
pip install -e .  # if using pyproject.toml

# Verify data structure
ls data/raw/census_1981/
```

### 2. Run full pipeline

```bash
# End-to-end build
python scripts/build_all.py

# Check outputs
ls outputs/aggregates/manchester/1981/
```

### 3. Load Manchester aggregate in Python

```python
import pandas as pd

# Load final processed file
manchester = pd.read_csv("data/processed/sas04_manchester_1981.csv")
print(manchester[["81sas040359", "81sas040360", "81sas040361"]])
```

### 4. Explore in notebooks

```bash
jupyter notebook notebooks/02_explore_sas04.ipynb
```

## Geography Codes

### Manchester Hierarchy

| Level | Code | Description |
|---|---|---|
| County | `03` | Greater Manchester (all 10 districts) |
| District | `03BN` | City of Manchester |
| Ward | `03BNAA`–`03BNBK` | 27 wards (e.g., Alexandra, Ardwick, Didsbury) |
| Enumeration District | `03BNAL01`–`03BNAL25` | ~200+ small enumeration districts |

**To filter Manchester:**
```python
manchester_data = sas04.loc[sas04["zoneid"].str.startswith("03BN")]
```

For full zone descriptions, see `data/raw/census_1981/1981_geography_lookup.csv`.

## Data Dictionary

### Column Names

All columns follow the pattern `81sas04XXXX`, where `XXXX` is a 4-digit variable code.

- Columns 0001–0358: Country-of-birth categories
- Columns 0359–0361: **Far East births** (China/Hong Kong proxy)

### Row Structure

Each row represents a single zone (ward, enumeration district, or aggregate).

| Column | Type | Example | Notes |
|---|---|---|---|
| `zoneid` | string | `03BNAA` | Unique zone identifier |
| `81sas040001` | int | 45771956 | Total persons born in England |
| `81sas040359` | int | 122488 | Total persons born in Far East |

## Usage

### For Researchers

1. **Quick Manchester summary**: Load `data/processed/sas04_manchester_1981.csv`
2. **Ward-level analysis**: Use `notebooks/02_explore_sas04.ipynb`; filter by `03BN*` codes in `1981_geography_lookup.csv`
3. **Reproduce pipeline**: Run `python scripts/build_all.py`

### For Data Engineers

- **Pipeline structure**: Modular scripts in `scripts/`; reusable functions in `src/fyp_pipeline/`
- **Testing**: Run tests with `pytest tests/`
- **Adding 1991 data**: Copy pipeline structure; parameterize year in `configs/pipeline.yml`

**Example `.gitignore`:**
```
# Data
data/raw/census_1981/sas04*.csv
data/interim/
data/processed/
outputs/

# Python
__pycache__/
*.pyc
*.pyo
.venv/
.egg-info/

# IDE
.vscode/
.idea/
```

## Limitations

- **Zone boundary changes**: Ward/ED boundaries differ between 1981, 1991, 2001; spatial joins required for comparison
- **Population small numbers**: Some EDs have <100 persons; aggregation to ward+ recommended
- **Far East category**: SAS04 variables 359–361 capture Census-defined "Far East" (not identical to "Chinese ethnicity")
- **Disclosure**: Anonymized records; small-count suppression may apply

## Next Steps

- [ ] Ingest 1991 Census SAS04 data (use same pipeline structure)
- [ ] Create spatial join layer (1981 ↔ 1991 zone boundaries)
- [ ] Add 2001 Census (if available)
- [ ] Compute ward-level change metrics (growth, dispersion, concentration)
- [ ] Integrate housing tenure (SAS10) and occupation data (SAS07)

## References

- **UK Census 1981**: Small Area Statistics, Office of Population Censuses and Surveys (OPCS)
- **Data Source**: Census Microdata Lab / Historical Census Data Archive
- **Geography**: Manchester Local Authority, 1981 Boundary Definitions
- **Method**: See *Final Year Project Plan Submission* for full methodology

## Contributors

- **Author**: Jourdan Tan   
- **Supervisor**: Dr.Shawn Day
- **Institution**: (NUI) University College Cork

## License

This project is part of an academic final year project. Data sourced from UK Census (public domain, OPCS). Analysis code licensed under [MIT/Apache 2.0].

## Questions?

- **Data structure**: See `data/raw/census_1981/1981_variable_lookup.csv` (61 SAS04 columns)
- **Geography codes**: See `data/raw/census_1981/1981_geography_lookup.csv` (zone ID → name)
- **Methodology**: See *Final Year Project Plan Submission* PDF

---

**Last Updated**: January 2026  
**Data Release**: 1981 Census (1981 geography)  
**Status**: Active Development
