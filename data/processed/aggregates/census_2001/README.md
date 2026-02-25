# Census 2001 – Manchester Output Area Aggregates

## Overview

This directory holds the raw-aggregate output of the 2001 census ingestion pipeline
for Manchester Output Areas (OAs). It is the intermediate product produced by
`scripts/03_ingest_2001_oas.py` before indicator computation.

---

## Directory contents

| File | Description |
|------|-------------|
| `2001_oas_combined_raw.csv` | Wide-format merged table: one row per Manchester OA, all census variables as columns |
| `README.md` | This file |

---

## Source data

Raw census files ingested are located in `data/raw/` and must be obtained from
[CASWEB / UKDS Nesstar](https://ukdataservice.ac.uk/) or the
[ONS Nomis custom download](https://www.nomisweb.co.uk/):

| Raw file | Table | Description |
|----------|-------|-------------|
| `c01cs001_ons.csv` | CS001EW | Total population (all usual residents) |
| `c01ct003_ons.csv` | CT003EW | Ethnic group – includes Chinese category |
| `c01cs015_ons.csv` | CS015EW | Country of birth – Asia sub-region (proxy) |
| `c01cs028_ons.csv` | CS028EW | Economic activity, persons 16–74 |
| `c01cs049_ons.csv` | CS049EW | Tenure (household spaces) |
| `c01cs052_ons.csv` | CS052EW | Persons per room / overcrowding |
| `c01cs056_ons.csv` | CS056EW | Amenities – bath/shower and WC |
| `c01cs060_ons.csv` | CS060EW | Car and van ownership |

---

## Geography

| Attribute | Value |
|-----------|-------|
| Geography unit | Output Area (OA) |
| Manchester OA prefix | `00BN` |
| Geography epoch | 2001 Census OA boundaries |
| CRS (for spatial work) | EPSG:27700 (British National Grid) |
| GIS boundary source | ONS Open Geography Portal – *Output Areas (December 2001) Full Clipped Boundaries EW* |

> **Note:** 2001 OA codes (`00BN…`) are **not directly comparable** with
> 1981/1991 Enumeration District codes (`03BN…`). Cross-decade comparisons
> require aggregation to ward level using the geography lookup:
> `data/lookups/2001_geography_lookup_england.csv`.

---

## Key differences from 1981 / 1991 pipelines

| Aspect | 1991 | 2001 |
|--------|------|------|
| Geography unit | Enumeration District (ED) | Output Area (OA) |
| OA/ED prefix | `03BN` | `00BN` |
| Table prefix | `s0Xews` (SAS) | `cs0XX_ons` / `ct003_ons` |
| Ethnic ID column | S06EWS self-ID | CT003EW self-ID |
| China-born proxy | s070041 + s070042 | **CS015 Asia-born only** |
| Employment table | S09EWS | CS028EW (all pop 16–74) |
| Tenure table | S16EW | CS049EW |
| Overcrowding | S16EW persons/room | CS052EW persons/room |
| Amenities | S16EW bath/WC | CS056EW bath/WC |
| Car ownership | S16EW | CS060EW |

---

## ⚠ Important caveats

### No China-specific Country of Birth at OA level
The 2001 census does not publish a China-specific COB variable at Output Area
level. `CS015EW` cell `CS0150049` covers **all of Asia** as a birth region
(including India, Pakistan, Bangladesh, China, Hong Kong, etc.). This is used
only as a broad proxy and is flagged `asia_born_pct_is_proxy = True` in the
indicator output.

**For primary Chinese identification, always use CT003EW (`chinese_ethnic_pct`).**

### CT003 vs CS015 distinction
| Field | Source | Specificity |
|-------|--------|-------------|
| `chinese_ethnic_pct` | CT003EW cell 0016 | ✅ Specific to Chinese ethnic group |
| `asia_born_pct` | CS015EW cell 0049 | ⚠ Broad Asia COB proxy only |

---

## Pipeline order

Run the following scripts in sequence:

```bash
# Step 1 – Ingest raw CSVs
python scripts/03_ingest_2001_oas.py

# Step 2 – Compute indicators
python scripts/07_compute_indicators_2001_oas.py

# Step 3 – Spatial join (requires gis_boundaries/2001/ boundary file)
python scripts/10_join_boundaries_2001_oas.py

# Step 4 – Export to GeoJSON for web app
python scripts/13_export_web_geojson.py

# Step 5 – Extend temporal comparison
python scripts/12_aggregate_2001_oas_to_wards.py
```

---

## Output files (produced by the pipeline)

| File | Path |
|------|------|
| Combined raw CSV | `data/processed/aggregates/census_2001/2001_oas_combined_raw.csv` |
| Indicator CSV | `data/processed/indicators/2001/manchester_oas_2001_indicators.csv` |
| Spatial GeoPackage | `data/processed/outputs/spatial/2001/manchester_oas_2001_joined_indicators.gpkg` |
| GeoJSON (web) | `manchester-cityscape-explorer-main/public/geojson/manchester_oas_2001.geojson` |
| Temporal comparison | `data/processed/indicators/temporal/manchester_1981_1991_2001_comparison.csv` |

---

## Variable code reference

Cell codes follow the ONS convention: `TableCode` + 4-digit cell number.

| Indicator | Code | Table |
|-----------|------|-------|
| Total population | `CS0010001` | CS001EW |
| Chinese ethnic group | `CT0030016` | CT003EW |
| Asia-born (proxy) | `CS0150049` | CS015EW |
| All persons 16–74 | `CS0280001` | CS028EW |
| Economically active | `CS0280002` | CS028EW |
| Self-employed | `CS0280004` | CS028EW |
| Unemployed (ILO) | `CS0280005` | CS028EW |
| Total household spaces | `CS0490001` | CS049EW |
| Owner occupied | `CS0490002` | CS049EW |
| Council/RSL rented | `CS0490003` | CS049EW |
| Private rented | `CS0490005` | CS049EW |
| Overcrowd 1.0–1.5 ppr | `CS0520013` | CS052EW |
| Overcrowd >1.5 ppr | `CS0520017` | CS052EW |
| No bath/WC | `CS0560021` | CS056EW |
| No car or van | `CS0600005` | CS060EW |

---

*Generated: 2026-02-25 | FYP Data Pipeline – Manchester Spatial Lab*
