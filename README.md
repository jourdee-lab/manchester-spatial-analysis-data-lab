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
├── 81sas04/                              # 1981 Census SAS04 (Country of Birth)
│   ├── 81sas04.ipynb                     # Jupyter notebook for data exploration
│   ├── 81sas04ews_0.csv                  # SAS04 data split (part 1)
│   ├── 81sas04ews_1.csv                  # SAS04 data split (part 2)
│   ├── 81sas04ews_2.csv                  # SAS04 data split (part 3)
│   ├── 81sas04ews_3.csv                  # SAS04 data split (part 4)
│   ├── 81sas04ews_4.csv                  # SAS04 data split (part 5)
│   ├── 1981_geography_lookup.csv          # Zone code → area name/type mapping
│   ├── 1981_table_code_name_lookup.csv    # SAS table metadata
│   ├── manchester_sas04_1981.csv          # Manchester (03BN) aggregate output
│   ├── README.md
│   └── README.md                          # (root-level documentation)
```

## Data Files

### Census Data (SAS04)

| File | Description | Rows | Purpose |
|------|---|---|---|
| `81sas04ews_0–4.csv` | Country of birth by zone (split 5 ways) | ~9,000 zones × 61 variables | Raw microdata; combine for full 1981 coverage |
| `1981_geography_lookup.csv` | Zone code ↔ area name mapping | ~7,500 zones | Link zone IDs (`03BNAA`, `03BNAB`, etc.) to ward/district names |
| `1981_table_code_name_lookup.csv` | SAS table metadata | 50 tables | Interpret column definitions (e.g., `81sas040359` = Far East births) |

### Key SAS04 Variables

- `81sas040359` — Total persons born in Far East
- `81sas040360` — Males born in Far East
- `81sas040361` — Females born in Far East

(See `1981_variable_lookup.csv` for full 61-variable breakdown)

## Quick Start

### 1. Load and Explore SAS04

```python
import pandas as pd

# Combine 5 SAS04 CSV files
base = "https://raw.githubusercontent.com/jourdee-lab/FYP_Data_Pipeline/main/81sas04"
files = [f"{base}/81sas04ews_{i}.csv" for i in range(5)]
dfs = [pd.read_csv(url, dtype={"zoneid": "string"}) for url in files]
sas04_1981 = pd.concat(dfs, ignore_index=True)

print(sas04_1981.shape)  # (9000+, 61)
print(sas04_1981.head())
```

### 2. Aggregate to Manchester City

```python
# Filter to Manchester (zone codes starting with 03BN)
manchester_agg = sas04_1981.loc[
    sas04_1981["zoneid"].str.startswith("03BN"),
    :
].sum(numeric_only=True)

print(manchester_agg[["81sas040359", "81sas040360", "81sas040361"]])
```

### 3. Extract Far East Births

```python
far_east = manchester_agg[[
    "81sas040359",  # Total
    "81sas040360",  # Male
    "81sas040361"   # Female
]].rename({
    "81sas040359": "total",
    "81sas040360": "male",
    "81sas040361": "female"
})

print(far_east)
```

See `81sas04.ipynb` for a complete walkthrough.

## Geography Codes

### Manchester Hierarchy

| Level | Code | Description |
|---|---|---|
| County | `03` | Greater Manchester (all 10 districts) |
| District | `03BN` | City of Manchester |
| Ward | `03BNAA`–`03BNBK` | 27 wards (e.g., Alexandra, Ardwick, Didsbury) |
| Enumeration District | `03BNAL01`–`03BNAL25` | ~200+ small enumeration districts |

**To aggregate Manchester:**
```python
manchester_codes = sas04_1981.loc[
    sas04_1981["zoneid"].str.startswith("03BN"),
    "zoneid"
].unique()
```

For full zone descriptions, consult `1981_geography_lookup.csv`.

## Data Dictionary

### Column Names

All columns follow the pattern `81sas04XXXX`, where `XXXX` is a 4-digit variable code.

- Columns 0001–0058: Standard country-of-birth categories (e.g., England, Scotland, India, China)
- Columns 0359–0361: **Far East births** (China/Hong Kong proxy; see Variable Lookup for interpretation)

### Row Structure

Each row represents a single zone (ward, enumeration district, or higher aggregate).

| Column | Type | Example | Notes |
|---|---|---|---|
| `zoneid` | string | `03BNAA` | Unique zone identifier; see geography lookup |
| `81sas040001` | int | 45771956 | Total persons born in England |
| `81sas040359` | int | 122488 | Total persons born in Far East |

## Usage

### For Researchers

1. **Reproduce 1981 Manchester aggregate**: Run `81sas04.ipynb`
2. **Custom queries**: Filter by ward code in `1981_geography_lookup.csv`, then sum SAS04 columns
3. **Longitudinal analysis**: Match 1981 zones to 1991 zones using geometry files (forthcoming)

### For Data Engineers

- **Schema**: Denormalized zone-level counts; no relational structure
- **Missing data**: Coded as 0 or absent; no explicit NA markers
- **Encoding**: UTF-8; UK local authority names include special chars (e.g., "St. John's")

## Limitations

- **Zone boundary changes**: Ward/ED boundaries differ between 1981, 1991, 2001; spatial joins required for comparison
- **Population small numbers**: Some EDs have <100 persons; aggregation to ward+ recommended for robust analysis
- **Far East category**: SAS04 variables 359–361 capture "Far East" as a Census category (likely Hong Kong, China, and other East Asian countries); not identical to "Chinese ethnicity"
- **Disclosure**: Original census records are anonymized; small-count suppression may apply in future releases

## Next Steps

- [ ] Ingest 1991 Census SAS04 data
- [ ] Create spatial join layer (1981 ↔ 1991 zone boundaries)
- [ ] Add 2001 Census (if available)
- [ ] Compute ward-level change metrics (growth, dispersion, concentration)
- [ ] Integrate housing tenure and occupation data (SAS10, SAS07)

## References

- **UK Census 1981**: Small Area Statistics, Office of Population Censuses and Surveys (OPCS)
- **Data Source**: [Census Microdata Lab](https://census.ac.uk) / Historical Census Data Archive
- **Geography**: Manchester Local Authority, 1981 Boundary Definitions
- **Method**: See *Final Year Project Plan Submission* for full methodology

## Contributors

- **Author**: Jourdan Tan
- **Supervisor**: Dr Shawn Day
- **Institution**: University College Cork 

## License

This project is part of an academic final year project. Data sourced from UK Census (public domain, OPCS). Analysis code licensed under [MIT/Apache 2.0 — specify].

## Questions?

For data structure questions, see `1981_variable_lookup.csv` (61 SAS04 columns explained).  
For geographic questions, see `1981_geography_lookup.csv` (zone ID → name mapping).  
For methodological questions, refer to the project plan PDF.

---

**Last Updated**: January 2026  
**Data Release**: 1981 Census (1981 geography)  
**Status**: In Progress
