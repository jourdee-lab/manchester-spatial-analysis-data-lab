# Manchester Spatial Analysis FYP — Condensed PRD v2.0

**Project:** Chinese Immigrant Integration in Manchester (1981–2001)  
**Version:** 2.0  
**Date:** 2026-01-18  
**Status:** Phase 6 Complete → Phase 7-15 Planning  
**Owner:** Jourdee

---

## 1. Executive Summary

Dual-system project analyzing spatial evolution and economic integration of Chinese immigrants in Manchester using census microdata (1981/1991/2001).

**Components:**
1. **Data Pipeline** (Python/QGIS) — Census ingestion, indicator computation, spatial analysis
2. **Web Application** (TypeScript/React/Mapbox) — Interactive visualization platform

**Current State:** 
- ✅ Phase 6 complete: 1,017 Manchester EDs, 25 indicators computed
- 🔄 Phase 7 in progress: QGIS mapping
- 📅 Phases 8-15 planned

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────┐
│         DATA PIPELINE (Python/QGIS)                  │
│                                                      │
│  Raw SAS CSVs → ED Tables → Indicators → GeoPackage │
│    (20/year)     (4/year)     (29)       (spatial)  │
└────────────────────┬─────────────────────────────────┘
                     │ GeoJSON Export
                     ▼
┌──────────────────────────────────────────────────────┐
│       WEB APPLICATION (React/Mapbox/TypeScript)      │
│                                                      │
│  Interactive Choropleth Maps + Business Locations   │
│  • Year slider (1981/1991/2001)                     │
│  • 29 indicators per year                           │
│  • Click → ED details panel                         │
│  • Dashboard (correlations, time series)            │
└──────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### Data Pipeline
| Component | Technology |
|-----------|-----------|
| Ingestion | Python 3.9+, pandas |
| Config | YAML |
| Spatial Join | QGIS 3.22+ |
| Validation | pytest |
| Output | GeoPackage, CSV, GeoJSON |

### Web Application
| Component | Technology |
|-----------|-----------|
| Framework | React 18 (functional) |
| Language | TypeScript (strict) |
| Mapping | Mapbox GL JS |
| State | React Context + Hooks |
| Styling | Tailwind CSS |
| Build | Vite |

---

## 4. Data Flow

```
Raw SAS Files (GB: 112,261 EDs)
    ↓ [Filter: 03BN* → 1,017 Manchester EDs]
ED-Level Census Tables (4 CSVs/year)
    ↓ [Compute 29 indicators from YAML config]
Indicator CSV (1,017 × 30 columns)
    ↓ [QGIS Join to ED Boundaries]
GeoPackage Spatial Layer
    ↓ [Export to GeoJSON]
Web Application (Interactive Map)
```

---

## 5. Repository Structure

```
fyp_main/
├── configs/
│   ├── indicators.yml          # 29 indicator definitions (544 lines)
│   └── sas_raw_file_mapping.yml
├── data/
│   ├── raw/sas/                # 20 CSV files per year
│   ├── processed/
│   │   ├── raw_ed_level/census_1981/  # 4 ED-level CSVs
│   │   ├── indicators/1981/            # Computed indicators
│   │   └── outputs/spatial/1981/       # GeoPackage exports
│   └── web_ready/              # 🆕 GeoJSON for web app
├── docs/
│   ├── phase6_indicator_documentation/
│   └── VERIFIED_NEXT_STEPS_PHASE6.md
├── figures/phase6_choropleth_maps/
├── gis_boundaries/ED_1981_EW.*
├── qgis/
│   └── phase6_indicator_mapping_1981.qgz
├── scripts/
│   ├── 01_ingest_1981_eds.py
│   ├── 04_compute_indicators_1981_eds.py
│   └── web_integration/        # 🆕 Conversion scripts
└── src/                        # 🆕 Web application
    ├── components/map/
    ├── components/ui/
    ├── contexts/
    └── data/geojson/
```

---

## 6. Core Indicators (29 Total)

### Demographics (3)
- `TOTAL_RES_1981` — Total residents
- `PCT_MALE_1981`, `PCT_FEMALE_1981`

### Ethnic Presence (5)
- `CHINESE_BORN_1981` — Chinese-born count
- `PCT_CHINESE_BORN_1981` — % Chinese-born
- `CHINESE_SEX_RATIO_1981`

### Employment (2)
- `ALL_EMPLOYED_1981` — Employed residents
- `EMP_RATE_1981` — Employment rate

### Housing & Tenure (17)
**Tenure:**
- `PCT_OWNER_OCC_1981` — % Owner-occupied
- `PCT_SOCIAL_RENT_1981` — % Social rented

**Deprivation:**
- `PCT_NO_CAR_1981` — % No car
- `PCT_OVERCROWD_GT1P5_1981` — % Overcrowded >1.5 pp/room
- `PCT_NO_BATH_OR_WC_1981` — % No bath or WC

**Composite:**
- `CAR_OWNERSHIP_INDEX_1981` — 100 - % no car
- `HOUSING_QUALITY_INDEX_1981` — Deprivation composite

---

## 7. Phase-by-Phase Plan

| Phase | Name | Status | Duration | Key Deliverables |
|-------|------|--------|----------|------------------|
| **1-6** | Data Ingestion & Indicators | ✅ Complete | 8 weeks | 25 indicators, metadata, CSVs |
| **7** | QGIS Mapping | 🔄 In Progress | 1 week | 5 choropleth maps, GeoPackage |
| **8** | Extend to 1991/2001 | 📅 Planned | 3 weeks | Multi-year indicators |
| **9** | Web Foundation | 📅 Planned | 2 weeks | Map renders, year selector |
| **10** | Interactive Features | 📅 Planned | 3 weeks | Hover, click, layer toggles |
| **11** | Dashboard & Analytics | 📅 Planned | 2 weeks | Correlation, time series |
| **12** | Business Layer | 📅 Planned | 2 weeks | Point layer with clustering |
| **13** | Longitudinal Analysis | 📅 Planned | 2 weeks | Change maps, diffusion metrics |
| **14** | Deployment | 📅 Planned | 1 week | Production build |
| **15** | Dissertation | 📅 Planned | 4 weeks | Final report |

**Total Duration:** ~25 weeks

---

## 8. Phase 7: QGIS Mapping (Current Week)

### Objectives
- Create 5 publication-quality choropleth maps
- Export GeoPackage with all indicators

### Tasks
1. ✅ Filter shapefile to Manchester (1,017 EDs)
2. ✅ Load indicator CSV as attribute table
3. 🔄 Configure join (`ED81CDO` ↔ `zoneid`)
4. ⏳ Validate 100% match rate
5. ⏳ Create 5 choropleth maps:
   - Chinese population (`PCT_CHINESE_BORN_1981`)
   - Housing deprivation (`PCT_NO_CAR_1981`)
   - Homeownership (`PCT_OWNER_OCC_1981`)
   - Employment rate (`EMP_RATE_1981`)
   - Overcrowding (`PCT_OVERCROWD_GT1P5_1981`)
6. ⏳ Export GeoPackage to `data/processed/outputs/spatial/1981`

### Known Issue
- **Whitespace padding in CSV `zoneid`** → Solution: Clean CSV or trim in QGIS

---

## 9. Phase 8-9: Web Integration (Next Steps)

### Phase 8: Data Conversion (Week 15-17)
**Deliverables:**
- `data/web_ready/1981/manchester_eds_1981.geojson` (< 10 MB)
- `data/web_ready/1981/indicators_metadata.json`
- Conversion script: `scripts/web_integration/gpkg_to_geojson.py`

**Process:**
```bash
ogr2ogr -f GeoJSON \
  -t_srs EPSG:4326 \
  -simplify 10 \
  data/web_ready/1981/manchester_eds_1981.geojson \
  data/processed/outputs/spatial/1981/manchester_eds_1981_indicators_FULL.gpkg
```

### Phase 9: Web Foundation (Week 18-19)
**Components:**
1. `src/components/map/Map.tsx` — Mapbox GL JS container
2. `src/components/map/EDChoroplethLayer.tsx` — Data-driven polygon layer
3. `src/components/ui/IndicatorSelector.tsx` — Dropdown UI
4. `src/hooks/useIndicatorData.ts` — GeoJSON loader

**Acceptance Criteria:**
- [ ] Map renders Manchester viewport
- [ ] Choropleth displays `PCT_CHINESE_BORN_1981`
- [ ] Dropdown switches between 29 indicators
- [ ] Legend shows color scale

---

## 10. Key Design Principles

1. **Configuration-Driven**: All indicators defined in `indicators.yml`
2. **Reproducible**: Every step documented with logs & metadata
3. **Extensible**: Add 1991/2001 by extending YAML config
4. **Auditable**: JSON metadata tracks quality, coverage, issues
5. **Performance-Optimized**: Vector tiles/clustering for web app

---

## 11. Success Criteria

### Minimum Viable Product (Phase 7-9)
- [ ] ✅ 1981 choropleth maps exported (5 maps, 300 dpi)
- [ ] ✅ GeoPackage contains 1,017 EDs + 25 indicators
- [ ] ✅ Web app loads 1981 data with interactive choropleth
- [ ] ✅ ED click shows popup with statistics

### Full Success (Phase 15)
- [ ] ✅ All 3 years (1981/1991/2001) integrated
- [ ] ✅ Business location layer with clustering
- [ ] ✅ Dashboard with correlation matrix & time series
- [ ] ✅ Dissertation complete with reproducible methodology

---

## 12. Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| GeoJSON file too large | Medium | High | Aggressive simplification + TopoJSON |
| 1991 boundary changes | High | Medium | Areal interpolation or ward aggregation |
| Mapbox performance issues | Low | High | Implement vector tiles |
| Indicator code mismatch | Low | Medium | Automated validation script |

---

## 13. Documentation Deliverables

1. **WEB_INTEGRATION_GUIDE.md** — GeoJSON conversion process
2. **API_SPECIFICATION.md** — Component props, data schemas
3. **PERFORMANCE_REPORT.md** — Optimization techniques
4. **USER_GUIDE.md** — How to use web explorer
5. **DISSERTATION.md** — Final academic write-up

---

## 14. Immediate Next Actions

### This Week (Phase 7 Completion)
1. **Fix CSV join issue**: Run Python cleaning script or QGIS Field Calculator
2. **Validate join**: Check for 100% match rate (1,017/1,017)
3. **Create 5 choropleth maps**: Export as PNG (300 dpi)
4. **Export GeoPackage**: Save with all 25 indicators
5. **Update join log**: Document final configuration

### Next Week (Phase 8 Start)
1. **Create conversion script**: `gpkg_to_geojson.py`
2. **Generate GeoJSON**: Convert 1981 GeoPackage
3. **Create metadata JSON**: Indicator definitions for UI
4. **Validate GeoJSON**: Load in QGIS and web browser
5. **Initialize web repo**: Vite + React + TypeScript setup

---

## 15. Contact & Resources

**Key Configs:**
- `configs/indicators.yml` — Indicator definitions
- `configs/sas_raw_file_mapping.yml` — File structure docs

**Documentation Hub:**
- `docs/VERIFIED_NEXT_STEPS_PHASE6.md`
- `docs/phase6_indicator_documentation/master_guide.md`

---

**Last Updated:** 2026-01-18  
**Status:** Ready for Phase 7 completion & Phase 8 planning
