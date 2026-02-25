# Phase 7: 1991 Data Pipeline Status & Requirements

**Date:** 4 February 2026  
**Status:** ✅ COMPLETE  
**Approach:** ED-Level Analysis (906 EDs) + Ward-Level Analysis (34 wards)

---

## Summary

Phase 7 successfully replicates the 1981 workflow for 1991 data at **ED level** (906 Manchester EDs) with additional ward-level aggregation.

### Completed ✓
1. ✅ Created `05_compute_indicators_1991_eds.py` script (ED-level)
2. ✅ Created `06_compute_indicators_1991_wards.py` script (ward-level)
3. ✅ Loaded all 1991 SAS tables (S02, S06, S07, S09, S49)
4. ✅ Computed 26 ED-level indicators including Chinese ethnic identification
5. ✅ Joined to 1991 ED boundaries (100% match rate - 906/906)
6. ✅ Created GeoPackage for QGIS mapping
7. ✅ Aggregated to district level for temporal comparison
8. ✅ Created 1981-1991 temporal comparison dataset

### Output Files
```
data/processed/indicators/1991/
├── manchester_eds_1991_indicators.csv       # 965 EDs × 26 indicators
├── manchester_wards_1991_indicators.csv     # 34 wards × 29 indicators
└── manchester_district_1991_indicators.csv  # District summary

data/processed/outputs/spatial/1991/
└── manchester_eds_1991_joined_indicators.gpkg  # 906 EDs with geometry

data/processed/indicators/temporal/
└── manchester_1981_1991_comparison.csv      # Complete comparison
```

---

## Key Findings

### Chinese Population in Manchester (ED-Level)
| Metric | Value | Notes |
|--------|-------|-------|
| Total population | 403,055 | Across 906 EDs in GeoPackage |
| Chinese ethnic | 2,979 (0.74%) | Self-identified Chinese ethnic group |
| Top ED | 03BNFK22 | 39 Chinese residents (22.5% of ED) |

### Top 10 EDs by Chinese % (1991)
| ED Code | Chinese | Total Pop | % Chinese |
|---------|---------|-----------|-----------|
| 03BNFK22 | 39 | 173 | 22.5% |
| 03BNFW27 | 27 | 203 | 13.3% |
| 03BNFW24 | 15 | 136 | 11.0% |
| 03BNFA02 | 34 | 348 | 9.8% |
| 03BNFW12 | 5 | 54 | 9.3% |
| 03BNFW20 | 25 | 275 | 9.1% |
| 03BNFS01 | 58 | 654 | 8.9% |
| 03BNFW16 | 8 | 92 | 8.7% |
| 03BNFH04 | 16 | 185 | 8.6% |
| 03BNFW19 | 25 | 299 | 8.4% |

### Temporal Comparison (District Level)
| Metric | 1981 | 1991 | Notes |
|--------|------|------|-------|
| Chinese-born / Chinese ethnic | 7,142 | 3,103 | Different measurement: 1981=country of birth, 1991=ethnic self-ID |
| % of population | 0.54% | 0.77% | Relative presence increased |
| China-born (1991 only) | - | 655 | Subset who were born in mainland China |
| Chinese households | - | 2,934 | New data available in 1991 |

### Chinese Housing Indicators (1991)
- **Owner-occupation rate:** 38.4%
- **Overcrowding (>1.5 pp/room):** 2.2%

### Top Wards by Chinese Population (1991)
1. Central (03BNFK) - 487 Chinese residents
2. Ardwick (03BNFA) - 202 Chinese residents
3. Rusholme (03BNGE) - 175 Chinese residents

---

## Data Sources Used

### Available ✓ (All processed successfully)
| Table | Description | Rows | Columns Used |
|-------|-------------|------|--------------|
| S02EWS | Demographics | 34 | s020001, s020002, s020005 |
| S06EWS | Ethnic group | 34 | s060009, s060021, s060033, s060045-s060105 |
| S07EWS | Country of birth | 34 | s070041, s070042 |
| S09EWS | Economic position | 34 | s090005, s090017, s090023, s090041, s090047 |
| S49EW | Housing by ethnicity | 34 | s490005, s490012, s490019, s490026 |

---

## Key Indicators Requiring Additional Data

### Chinese Presence (CRITICAL - requires S06EWS)
| Indicator | 1991 SAS Code | Description |
|-----------|---------------|-------------|
| `CHINESE_ETHNIC_1991` | s060009 | Chinese ethnic group (TOTAL) |
| `PCT_CHINESE_ETHNIC_1991` | s060009 / s020001 | % of population Chinese |

**Note:** 1991 introduced direct ethnic group identification, superior to 1981's "country of birth" proxy.

### Country of Birth (requires S07EWS)
| Indicator | 1991 SAS Code | Description |
|-----------|---------------|-------------|
| `CHINA_BORN_MALE_1991` | s070041 | Male born in China (PRC) |
| `CHINA_BORN_FEMALE_1991` | s070042 | Female born in China (PRC) |

### Economic Position (requires S09EWS)
| Indicator | 1991 SAS Code | Description |
|-----------|---------------|-------------|
| `CHINESE_ECON_ACTIVE_1991` | s090017 + s090041 | Chinese economically active |
| `CHINESE_UNEMPLOYED_1991` | s090023 + s090047 | Chinese unemployed |

### Housing (requires S49EW)
| Indicator | 1991 SAS Code | Description |
|-----------|---------------|-------------|
| `CHINESE_HOUSEHOLDS_1991` | s490005 | Chinese households total |
| `CHINESE_OWNER_OCC_1991` | s490026 | Chinese owner-occupied |
| `CHINESE_OVERCROWD_GT1P5_1991` | s490019 | Chinese overcrowded (>1.5 pp/room) |

---

## How to Obtain Missing Data

### UK Data Service
1. Visit: https://ukdataservice.ac.uk/
2. Search for: "1991 Census Small Area Statistics"
3. Dataset: SN 3035 - 1991 Census: Small Area Statistics
4. Download required tables (S06EWS, S07EWS, S09EWS, S16EW, S49EW)
5. Filter to Manchester district (zoneid = 03BN)

### Expected File Structure
```
data/raw/
├── s06ews/
│   ├── s06ews1.csv  (part 1)
│   ├── s06ews2.csv  (part 2)
│   ├── s06ews3.csv  (part 3)
│   └── s06ews4.csv  (part 4)
├── s07ews/
│   ├── s07ews1.csv
│   └── ...
├── s09ews/
│   ├── s09ews1.csv
│   └── ...
└── s16ew+s/
    ├── s16ews1.csv
    └── ...
```

---

## Current Temporal Comparison (Partial)

| Indicator | 1981 | 1991 | Change |
|-----------|------|------|--------|
| **Total Residents** | 1,312,935 | 1,214,004 | -7.5% |
| **Chinese/Far East Born** | 7,142 (0.54%) | *Missing* | — |
| **Chinese Ethnic Group** | *N/A* | *Missing* | — |

### Note on Comparability
- **1981**: Uses "country of birth (Far East)" as proxy for Chinese population
- **1991**: Uses direct "ethnic group (Chinese)" identification
- **Interpretation**: These are NOT directly comparable due to different definitions
  - 1981 captures foreign-born only (excludes UK-born Chinese)
  - 1991 captures self-identified ethnicity (includes UK-born)

---

## Next Steps

### Immediate (This Week)
1. **Obtain missing 1991 SAS tables** from UK Data Service
2. Place raw files in correct directories
3. Re-run `02_ingest_1991_eds.py` to process raw data
4. Re-run `06_compute_indicators_1991_wards.py` for full indicators

### After Data Obtained
1. Validate 1991 indicators against published statistics
2. Complete temporal comparison (1981 vs 1991)
3. Create comparison visualizations (bar charts, tables)
4. Document methodology and caveats

### Future (Phase 8+)
1. Obtain 2001 census data for three-period comparison
2. Consider boundary harmonization if ward-level data becomes available
3. Integrate into web application

---

## Script Usage

Once data is obtained:

```bash
# Step 1: Process raw 1991 SAS files
python scripts/02_ingest_1991_eds.py

# Step 2: Compute 1991 indicators (ward level)
python scripts/06_compute_indicators_1991_wards.py

# Step 3: Review outputs
cat data/processed/indicators/1991/manchester_district_1991_indicators.csv
cat data/processed/indicators/temporal/manchester_1981_1991_comparison.csv
```

---

## Files Created This Session

1. `scripts/06_compute_indicators_1991_wards.py` - Main computation script
2. `data/processed/indicators/1991/manchester_district_1991_indicators.csv` - 1991 indicators (partial)
3. `data/processed/indicators/temporal/manchester_1981_1991_comparison.csv` - Comparison dataset
4. `data/processed/indicators/temporal/temporal_comparison_metadata.json` - Methodology metadata
5. `docs/PHASE7_1991_STATUS_REPORT.md` - This document

---

## Questions for Supervisor

1. **Data Access**: Do you have access to the full 1991 SAS dataset (S06EWS, S07EWS, etc.)?
2. **Alternative Sources**: Are there other sources for 1991 ethnic group data for Manchester?
3. **Scope Reduction**: Should we proceed with demographics-only comparison if ethnic data unavailable?
4. **Comparability**: How should we handle the definitional change (country of birth → ethnic group)?
