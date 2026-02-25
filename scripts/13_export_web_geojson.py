#!/usr/bin/env python3
"""
Step 6: Export Ward-Level GeoJSON for Manchester Cityscape Explorer Web App
==========================================================================
Loads the harmonised 1981/1991/2001 ward indicators CSV + geometry, normalises
to a shared snake_case schema, and writes three decade-specific GeoJSON files
plus an updated datasets.json manifest.

Output:
  manchester-cityscape-explorer-main/public/geojson/
    manchester_wards_1981.geojson
    manchester_wards_1991.geojson
    manchester_wards_2001.geojson
    datasets.json
"""

import json
import logging
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPORAL_DIR = PROJECT_ROOT / "data" / "processed" / "indicators" / "temporal"
WEB_GEOJSON_DIR = (
    PROJECT_ROOT.parent
    / "manchester-cityscape-explorer-main"
    / "public"
    / "geojson"
)
WEB_GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH  = TEMPORAL_DIR / "manchester_harmonised_indicators_1981_1991_2001.csv"
GEO_PATH  = TEMPORAL_DIR / "harmonised_zones.geojson"
META_PATH = TEMPORAL_DIR / "harmonisation_metadata.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared normalised schema
# Each entry: (output_col, {year: source_col_or_None})
# None means the column is absent for that year → written as null.
# ---------------------------------------------------------------------------
SCHEMA: list[tuple[str, dict]] = [
    # Geographic identifiers (always present)
    ("ward_code",  {1981: "ward_code_2001", 1991: "ward_code_2001", 2001: "ward_code_2001"}),
    ("ward_name",  {1981: "ward_name_2001", 1991: "ward_name_2001", 2001: "ward_name_2001"}),

    # ---- Population --------------------------------------------------------
    ("total_population",    {1981: "TOTAL_RES_1981",   1991: "TOTAL_RES_1991",   2001: "total_pop"}),
    ("pct_male",            {1981: "PCT_MALE_1981",    1991: "PCT_MALE_1991",    2001: None}),
    ("pct_female",          {1981: "PCT_FEMALE_1981",  1991: "PCT_FEMALE_1991",  2001: None}),

    # ---- Ethnicity / Origin -----------------------------------------------
    # 1981: born in Far East (China proxy)
    # 1991: Chinese ethnic group
    # 2001: Chinese ethnic group (CT003EW)
    ("chinese_ethnic_count",  {1981: "CHINESE_BORN_1981",      1991: "CHINESE_ETHNIC_1991", 2001: "chinese_ethnic_count"}),
    ("pct_chinese_ethnic",    {1981: "PCT_CHINESE_BORN_1981",  1991: "PCT_CHINESE_ETHNIC_1991", 2001: "chinese_ethnic_pct"}),

    # Country of birth – China / Far East / Asia proxy
    ("china_born_count",  {1981: "CHINESE_BORN_1981",     1991: "CHINA_BORN_1991",  2001: "asia_born_count"}),
    ("pct_china_born",    {1981: "PCT_CHINESE_BORN_1981", 1991: "PCT_CHINA_BORN_1991", 2001: "asia_born_pct"}),

    # ---- Housing / Tenure -------------------------------------------------
    ("total_hh",            {1981: "TOTAL_HH_1981",       1991: None,                   2001: "total_hh_spaces"}),
    ("pct_owner_occ",       {1981: "PCT_OWNER_OCC_1981",  1991: "PCT_CHINESE_OWNER_OCC_1991", 2001: "owner_occ_rate"}),
    ("pct_social_rent",     {1981: "PCT_SOCIAL_RENT_1981",  1991: None,                 2001: "council_rent_rate"}),
    ("pct_private_rent",    {1981: None,                    1991: None,                 2001: "private_rent_rate"}),
    ("pct_no_car",          {1981: "PCT_NO_CAR_1981",     1991: None,                   2001: "no_car_rate"}),
    ("pct_overcrowd",       {1981: "PCT_OVERCROWD_GT1P5_1981", 1991: "PCT_CHINESE_OVERCROWD_1991", 2001: "overcrowd_rate"}),
    ("pct_no_bath_wc",      {1981: "PCT_NO_BATH_OR_WC_1981",   1991: None,              2001: "no_bath_wc_rate"}),

    # ---- Economy ----------------------------------------------------------
    # 1981: general employment rate for all residents
    # 1991: Chinese sub-population rates (only available breakdown)
    # 2001: general economically active + unemployment
    ("emp_rate",             {1981: "EMP_RATE_1981",          1991: "CHINESE_EMP_RATE_1991",  2001: "econ_active_rate"}),
    ("unemployment_rate",    {1981: None,                      1991: "CHINESE_UNEMP_RATE_1991", 2001: "unemployment_rate"}),
    ("self_employment_rate", {1981: None,                      1991: None,                      2001: "self_employment_rate"}),

    # ---- Data quality (useful for front-end tooltips) ---------------------
    ("interp_coverage",       {1981: "interp_coverage",  1991: "interp_coverage",  2001: "interp_coverage"}),
    ("interp_uncertainty",    {1981: "interp_uncertainty_flag", 1991: "interp_uncertainty_flag", 2001: "interp_uncertainty_flag"}),
]

# Only pct_china_born for 2001 is a proxy (Asia-born, not China-specific)
PROXY_NOTE = {
    2001: {"pct_china_born": "asia_born_proxy", "china_born_count": "asia_born_proxy"}
}

# All output keys (including 'year') — used to ensure GeoJSON parity
ALL_KEYS = ["year"] + [col for col, _ in SCHEMA]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _round(v, decimals=2):
    """Round a value to `decimals` places; return None if NaN/None."""
    if v is None:
        return None
    try:
        if math.isnan(float(v)):
            return None
        return round(float(v), decimals)
    except (TypeError, ValueError):
        return v  # strings (ward_code, ward_name, flags) returned as-is


def build_decade_df(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Return a DataFrame with normalised columns for a single decade."""
    out = pd.DataFrame()
    out["year"] = year

    for out_col, mapping in SCHEMA:
        src_col = mapping.get(year)
        if src_col is None or src_col not in df.columns:
            out[out_col] = None
        else:
            out[out_col] = df[src_col]

    # Copy index from source for alignment
    out.index = df.index
    return out


def df_to_geojson_features(gdf: gpd.GeoDataFrame, decade_df: pd.DataFrame, year: int) -> list:
    """Merge geometry + data and return a list of GeoJSON Feature dicts."""
    features = []
    for _, geo_row in gdf.iterrows():
        wc = geo_row.get("ward_code_2001") or geo_row.get("ward_code") or geo_row.get("WD01CD")

        data_row = decade_df.loc[decade_df["ward_code"] == wc]
        if data_row.empty:
            log.warning(f"  [year={year}] No data row for ward_code={wc!r} – writing nulls")
            props = {k: None for k in ALL_KEYS}
            props["ward_code"] = wc
            props["year"] = year # type: ignore
        else:
            row = data_row.iloc[0]
            props = {}
            for key in ALL_KEYS:
                val = row.get(key)
                props[key] = _round(val)

        # Tag proxy fields
        if year in PROXY_NOTE:
            for field, note in PROXY_NOTE[year].items():
                if field in props:
                    props[f"{field}_note"] = note # type: ignore

        features.append({
            "type": "Feature",
            "geometry": geo_row.geometry.__geo_interface__,
            "properties": props,
        })
    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("=" * 70)
    log.info("Phase 10: Export Ward GeoJSON for Web App")
    log.info("=" * 70)

    # --- Load source data ---------------------------------------------------
    log.info(f"Loading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    log.info(f"  CSV shape: {df.shape}")
    log.info(f"  Unique wards: {df['ward_code_2001'].nunique()}")

    log.info(f"Loading geometry: {GEO_PATH}")
    gdf = gpd.read_file(GEO_PATH)
    log.info(f"  GeoDataFrame shape: {gdf.shape}  CRS: {gdf.crs}")
    log.info(f"  Geometry columns: {list(gdf.columns)}")

    # Reproject to WGS-84 if needed
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        log.info("  Reprojecting to EPSG:4326 (WGS-84)…")
        gdf = gdf.to_crs(epsg=4326)

    # Simplify geometry to keep files small (tolerance ~11m at Manchester lat)
    log.info("  Simplifying geometry (tolerance=0.0001°)…")
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.0001, preserve_topology=True)

    # --- Detect ward_code column in geodataframe ----------------------------
    ward_col_candidates = ["ward_code_2001", "ward_code", "WD01CD", "code", "CODE"]
    geo_ward_col = next((c for c in ward_col_candidates if c in gdf.columns), None)
    if geo_ward_col is None:
        raise ValueError(f"Cannot find ward code column in GeoDataFrame. Columns: {list(gdf.columns)}")
    if geo_ward_col != "ward_code_2001":
        gdf = gdf.rename(columns={geo_ward_col: "ward_code_2001"})
    log.info(f"  Using ward column: {geo_ward_col!r}")

    # --- Build decade-specific DataFrames -----------------------------------
    manifest_layers = []
    all_indicator_keys = [col for col, _ in SCHEMA if col not in ("ward_code", "ward_name", "interp_coverage", "interp_uncertainty")]

    for year in [1981, 1991, 2001]:
        log.info(f"\n--- Year {year} ---")
        decade_df = build_decade_df(df, year)
        log.info(f"  decade_df shape: {decade_df.shape}")

        features = df_to_geojson_features(gdf, decade_df, year)
        log.info(f"  Features generated: {len(features)}")

        geojson_obj = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }

        out_path = WEB_GEOJSON_DIR / f"manchester_wards_{year}.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(geojson_obj, f, separators=(",", ":"))  # compact JSON

        size_kb = out_path.stat().st_size / 1024
        log.info(f"  ✓ Written: {out_path}  ({size_kb:.1f} KB)")

        if size_kb > 2048:
            log.warning(f"  ⚠️  File exceeds 2MB target ({size_kb:.1f} KB) – consider increasing simplification")

        # Collect indicator keys with actual data (non-null in ≥1 feature)
        available_indicators = []
        for key in all_indicator_keys:
            has_data = any(f["properties"].get(key) is not None for f in features)
            if has_data:
                available_indicators.append(key)

        manifest_layers.append({
            "year": year,
            "geojson": f"/geojson/manchester_wards_{year}.geojson",
            "featureCount": len(features),
            "indicators": available_indicators,
        })

    # --- Write datasets.json manifest ---------------------------------------
    manifest = {
        "schema": "harmonised-ward-v1",
        "generatedAt": pd.Timestamp.now().isoformat(),
        "geographyLevel": "ward",
        "boundaryYear": 2001,
        "decades": manifest_layers,
        "indicatorNotes": {
            "pct_chinese_ethnic": {
                1981: "Proxy: % born in Far East (no ethnic group question in 1981 census)",
                1991: "% residents of Chinese ethnic group",
                2001: "% residents of Chinese ethnic group (CT003EW)",
            },
            "pct_china_born": {
                1981: "% born in China / Far East",
                1991: "% born in China",
                2001: "Asia-born proxy (no OA-level China-specific COB in 2001)",
            },
            "emp_rate": {
                1981: "% employed (all residents)",
                1991: "% economically active (Chinese sub-population only)",
                2001: "% economically active aged 16–74 (CS028EW)",
            },
            "pct_owner_occ": {
                1991: "Chinese households only",
            },
            "pct_overcrowd": {
                1991: "Chinese households only",
            },
        },
    }

    manifest_path = WEB_GEOJSON_DIR / "datasets.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"\n✓ Manifest written: {manifest_path}")

    # --- Summary ------------------------------------------------------------
    log.info("\n" + "=" * 70)
    log.info("Phase 10 complete.")
    log.info(f"  Output dir : {WEB_GEOJSON_DIR}")
    log.info(f"  Files      : {[p.name for p in sorted(WEB_GEOJSON_DIR.glob('manchester_wards_*.geojson'))]}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
