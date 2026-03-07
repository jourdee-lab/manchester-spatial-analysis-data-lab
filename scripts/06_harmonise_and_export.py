"""Step 4: Harmonise ward boundaries across 1981/1991/2001 and export web GeoJSON."""

from __future__ import annotations

import json
import logging
import math
import sys
import warnings
from datetime import datetime
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.validation import make_valid

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", ".*invalid.*")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

BASE    = Path(__file__).resolve().parents[1]
BND     = BASE / "gis_boundaries"
IND     = BASE / "data" / "processed" / "indicators"
OUT_DIR = IND / "temporal"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WEB_DIR = BASE.parent / "manchester-cityscape-explorer-main" / "public" / "geojson"
WEB_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CRS = "EPSG:27700"
UNCERTAINTY_THRESHOLD = 0.30

# Variable columns: extensive = counts, intensive = rates/%

COLS_1981_EXTENSIVE = [
    "TOTAL_RES_1981",
    "CHINESE_BORN_1981", "CHINESE_BORN_MALE_1981", "CHINESE_BORN_FEMALE_1981",
    "ALL_EMPLOYED_1981",
    "TOTAL_HH_1981", "OWNER_OCC_HH_1981", "SOCIAL_RENT_HH_1981", "NO_CAR_HH_1981",
    "OVERCROWD_GT1P5_1981", "OVERCROWD_1TO1P5_1981",
    "NO_BATH_OR_WC_1981", "NO_INSIDE_BATH_OR_WC_1981",
]
COLS_1981_INTENSIVE = [
    "PCT_MALE_1981", "PCT_FEMALE_1981", "PCT_CHINESE_BORN_1981", "EMP_RATE_1981",
    "PCT_OWNER_OCC_1981", "PCT_SOCIAL_RENT_1981", "PCT_NO_CAR_1981", "CAR_OWNERSHIP_INDEX_1981",
    "PCT_OVERCROWD_GT1P5_1981", "PCT_OVERCROWD_1TO1P5_1981",
    "PCT_NO_BATH_OR_WC_1981", "PCT_NO_INSIDE_BATH_OR_WC_1981",
]
COLS_1991_EXTENSIVE = [
    "TOTAL_RES_1991", "TOTAL_MALE_1991", "TOTAL_FEMALE_1991",
    "CHINESE_ETHNIC_1991", "CHINESE_ETHNIC_MALE_1991", "CHINESE_ETHNIC_FEMALE_1991",
    "CHINESE_AGE_0_4_1991", "CHINESE_AGE_5_15_1991",
    "CHINESE_AGE_16_29_1991", "CHINESE_AGE_30_PENSION_1991",
    "CHINESE_PENSIONABLE_1991", "CHINESE_LIMITING_ILLNESS_1991",
    "CHINA_BORN_1991", "CHINA_BORN_MALE_1991", "CHINA_BORN_FEMALE_1991",
    "CHINESE_16PLUS_1991", "CHINESE_ECON_ACTIVE_1991", "CHINESE_UNEMPLOYED_1991",
    "CHINESE_HOUSEHOLDS_1991", "CHINESE_OVERCROWD_GT1P5_1991", "CHINESE_OWNER_OCC_1991",
]
COLS_1991_INTENSIVE = [
    "PCT_MALE_1991", "PCT_FEMALE_1991", "PCT_CHINESE_ETHNIC_1991", "PCT_CHINA_BORN_1991",
    "CHINESE_EMP_RATE_1991", "CHINESE_UNEMP_RATE_1991",
    "PCT_CHINESE_OVERCROWD_1991", "PCT_CHINESE_OWNER_OCC_1991",
]
COLS_2001_EXTENSIVE = ["total_pop", "chinese_ethnic_count", "asia_born_count", "pop_16_74", "total_hh_spaces"]
COLS_2001_INTENSIVE = [
    "chinese_ethnic_pct", "asia_born_pct",
    "econ_active_rate", "unemployment_rate", "self_employment_rate",
    "owner_occ_rate", "council_rent_rate", "private_rent_rate",
    "overcrowd_rate", "overcrowd_severe_rate", "no_bath_wc_rate", "no_car_rate",
]


# STEP 1: load boundary files

def load_boundaries():
    """Return (eds_1981, wards_1991, wards_2001) – all Manchester, EPSG:27700."""
    log.info("Loading boundary files...")
    eds81 = gpd.read_file(BND / "1981" / "ED_1981_EW.shp")
    eds81 = eds81[eds81["LAD81CD"] == "03BN"].copy()
    eds81["geometry"] = eds81["geometry"].apply(make_valid) # type: ignore
    eds81 = eds81.to_crs(TARGET_CRS)
    eds81["ed_area_m2"] = eds81["geometry"].area
    log.info("  1981 EDs: %d", len(eds81))

    wards91 = gpd.read_file(BND / "1991" / "england_wa_1991.shp")
    wards91 = wards91[wards91["label"].str.startswith("03BN", na=False)].copy()
    wards91["geometry"] = wards91["geometry"].apply(make_valid) # type: ignore
    wards91 = wards91.to_crs(TARGET_CRS)
    log.info("  1991 wards: %d", len(wards91))

    wards01 = gpd.read_file(BND / "2001" / "wards" / "england_caswa_2001_clipped.shp")
    wards01 = wards01[wards01["ons_label"].str.startswith("00BN", na=False)].copy()
    wards01["geometry"] = wards01["geometry"].apply(make_valid) # type: ignore
    wards01 = wards01.to_crs(TARGET_CRS)
    wards01["ward_area_m2"] = wards01["geometry"].area
    log.info("  2001 wards: %d", len(wards01))

    return eds81, wards91, wards01


# STEP 2: harmonise 2001 OA -> ward aggregation

def harmonise_2001(wards01: gpd.GeoDataFrame) -> pd.DataFrame:
    """Aggregate 2001 OA indicators to ward level (sum extensive; pop-weighted mean intensive)."""
    log.info("Harmonising 2001 (OA -> ward)...")
    df = pd.read_csv(IND / "2001" / "manchester_oas_2001_indicators.csv")
    log.info("  Loaded %d OA rows", len(df))

    avail_ext = [c for c in COLS_2001_EXTENSIVE if c in df.columns]
    avail_int = [c for c in COLS_2001_INTENSIVE if c in df.columns]

    agg_ext = df.groupby("ward_code")[avail_ext].sum()
    df["_w"] = df["total_pop"]

    def pop_wavg(grp):
        w, tot = grp["_w"], grp["_w"].sum()
        return pd.Series({c: (grp[c].fillna(0) * w).sum() / tot if tot > 0 else np.nan for c in avail_int})

    agg_int = df.groupby("ward_code").apply(pop_wavg, include_groups=False) # type: ignore
    result = agg_ext.join(agg_int).reset_index().rename(columns={"ward_code": "ward_code_2001"})

    name_map  = wards01.set_index("ons_label")["name"].to_dict()
    label_map = wards01.set_index("ons_label")["label"].to_dict()
    result["ward_name_2001"]  = result["ward_code_2001"].map(name_map)
    result["ward_code_1991"]  = result["ward_code_2001"].map(label_map)
    log.info("  2001 harmonised: %d wards", len(result))
    return result


# STEP 3: harmonise 1991 – direct code mapping (boundaries identical to 2001)

def harmonise_1991(wards01: gpd.GeoDataFrame) -> pd.DataFrame:
    """Map 1991 ward codes to 2001 codes via the 2001 ward boundary label column."""
    log.info("Harmonising 1991 (direct code mapping)...")
    df91 = pd.read_csv(IND / "1991" / "manchester_wards_1991_indicators.csv")
    log.info("  Loaded %d 1991 wards", len(df91))

    lookup = wards01[["ons_label", "label"]].rename(
        columns={"ons_label": "ward_code_2001", "label": "ward_code_1991"}
    )
    avail_ext = [c for c in COLS_1991_EXTENSIVE if c in df91.columns]
    avail_int = [c for c in COLS_1991_INTENSIVE if c in df91.columns]

    df91 = df91.rename(columns={"zoneid": "ward_code_1991"})
    keep = ["ward_code_1991", "ward_name"] + [c for c in avail_ext + avail_int if c in df91.columns]
    result = df91[keep].merge(lookup, on="ward_code_1991", how="left")

    unmatched = result["ward_code_2001"].isna().sum()
    if unmatched:
        log.warning("  %d 1991 wards could not be mapped to 2001 codes", unmatched)
    log.info("  1991 harmonised: %d wards", result["ward_code_2001"].notna().sum())
    return result


# STEP 4: harmonise 1981 – areal interpolation (EDs -> 2001 wards)

def _rederive_1981_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Re-derive 1981 rate indicators from area-interpolated counts."""
    def safe_pct(num, den):
        n = df.get(num, pd.Series(np.nan, index=df.index))
        d = df.get(den, pd.Series(np.nan, index=df.index))
        return pd.Series(np.where(d > 0, 100 * n / d, np.nan), index=df.index)

    if "TOTAL_RES_1981" in df.columns:
        df["PCT_CHINESE_BORN_1981"] = safe_pct("CHINESE_BORN_1981", "TOTAL_RES_1981")
    if "TOTAL_HH_1981" in df.columns:
        for cnt, pct in [
            ("OWNER_OCC_HH_1981",         "PCT_OWNER_OCC_1981"),
            ("SOCIAL_RENT_HH_1981",        "PCT_SOCIAL_RENT_1981"),
            ("NO_CAR_HH_1981",             "PCT_NO_CAR_1981"),
            ("OVERCROWD_GT1P5_1981",       "PCT_OVERCROWD_GT1P5_1981"),
            ("OVERCROWD_1TO1P5_1981",      "PCT_OVERCROWD_1TO1P5_1981"),
            ("NO_BATH_OR_WC_1981",         "PCT_NO_BATH_OR_WC_1981"),
            ("NO_INSIDE_BATH_OR_WC_1981",  "PCT_NO_INSIDE_BATH_OR_WC_1981"),
        ]:
            df[pct] = safe_pct(cnt, "TOTAL_HH_1981")
    return df


def _compute_uncertainty(intersection: gpd.GeoDataFrame, wards01: gpd.GeoDataFrame) -> pd.DataFrame:
    """Flag 2001 wards where 1981 areal interpolation covers < (1 - threshold) of ward area."""
    covered = (intersection.groupby("ward_code_2001")["frag_area_m2"].sum()
               .reset_index().rename(columns={"frag_area_m2": "total_covered_m2"}))
    ward_areas = wards01.set_index("ons_label")["ward_area_m2"].reset_index()
    ward_areas.columns = ["ward_code_2001", "ward_area_m2"]
    n_eds = (intersection.groupby("ward_code_2001")["ED81CDO"].nunique()
             .reset_index().rename(columns={"ED81CDO": "n_source_eds"}))

    unc = covered.merge(ward_areas, on="ward_code_2001").merge(n_eds, on="ward_code_2001")
    unc["interp_coverage"] = (unc["total_covered_m2"] / unc["ward_area_m2"]).clip(0, 1)
    unc["interp_uncertainty_flag"] = np.where(
        unc["interp_coverage"] < (1 - UNCERTAINTY_THRESHOLD), "HIGH", "low"
    )
    high = (unc["interp_uncertainty_flag"] == "HIGH").sum()
    log.info("  Uncertainty: %d HIGH / %d wards", high, len(unc))
    return unc


def harmonise_1981(eds81: gpd.GeoDataFrame, wards01: gpd.GeoDataFrame):
    """Spatially reaggregate 1981 ED indicators to 2001 ward boundaries via areal interpolation."""
    log.info("Harmonising 1981 (areal interpolation: EDs -> 2001 wards)...")

    df_all = pd.read_csv(IND / "1981" / "manchester_eds_1981_indicators.csv")
    df_all["zoneid"] = df_all["zoneid"].astype(str).str.strip()
    df81 = df_all[df_all["zoneid"].str.len() == 8].copy().rename(columns={"zoneid": "ED81CDO"})
    log.info("  Loaded %d 1981 ED rows", len(df81))

    geo = eds81.merge(df81, on="ED81CDO", how="inner")
    log.info("  Geometries joined: %d EDs", len(geo))

    avail_ext = [c for c in COLS_1981_EXTENSIVE if c in geo.columns]
    avail_int = [c for c in COLS_1981_INTENSIVE if c in geo.columns]
    for col in avail_ext + avail_int:
        geo[col] = pd.to_numeric(geo[col], errors="coerce")

    wards_target = wards01[["ons_label", "name", "label", "ward_area_m2", "geometry"]].copy()
    wards_target = wards_target.rename(columns={
        "ons_label": "ward_code_2001", "name": "ward_name_2001", "label": "ward_code_1991"
    })

    log.info("  Running polygon overlay (intersection)...")
    intersection = gpd.overlay(geo, wards_target, how="intersection", keep_geom_type=True)
    intersection["frag_area_m2"] = intersection["geometry"].area
    intersection["area_weight"]  = (intersection["frag_area_m2"] / intersection["ed_area_m2"]).clip(0, 1)
    log.info("  Intersection fragments: %d", len(intersection))

    grouped = intersection.groupby("ward_code_2001")

    ext_df = pd.DataFrame({col: grouped.apply(lambda g: (g[col] * g["area_weight"]).sum()) for col in avail_ext})
    ext_df.index.name = "ward_code_2001"

    area_wt_total = grouped["area_weight"].sum()
    int_df = pd.DataFrame({
        col: grouped.apply(lambda g: (g[col] * g["area_weight"]).sum()) / area_wt_total
        for col in avail_int
    })
    int_df.index.name = "ward_code_2001"

    result = ext_df.join(int_df).reset_index()
    result = _rederive_1981_rates(result)

    ward_meta = wards_target[["ward_code_2001", "ward_name_2001", "ward_code_1991"]].drop_duplicates()
    result = result.merge(ward_meta, on="ward_code_2001", how="left")

    uncertainty = _compute_uncertainty(intersection, wards01)
    result = result.merge(
        uncertainty[["ward_code_2001", "interp_coverage", "n_source_eds", "interp_uncertainty_flag"]],
        on="ward_code_2001", how="left",
    )
    log.info("  1981 harmonised: %d wards", len(result))
    return result, uncertainty


# STEP 5: merge three years

def merge_years(df81: pd.DataFrame, df91: pd.DataFrame, df01: pd.DataFrame) -> pd.DataFrame:
    """Outer-join the three year datasets on ward_code_2001."""
    log.info("Merging three-year dataset...")
    df91 = df91.rename(columns={"ward_name": "ward_name_1991"}).drop(columns=["ward_code_1991"], errors="ignore")

    merged = df01.copy()

    cols_91 = [c for c in ["ward_code_2001", "ward_name_1991"] + [c for c in df91.columns if c.endswith("_1991")] if c in df91.columns]
    merged = merged.merge(df91[cols_91], on="ward_code_2001", how="left", suffixes=("", "_dup"))
    merged = merged[[c for c in merged.columns if not c.endswith("_dup")]]

    cols_81 = ["ward_code_2001"] + [c for c in df81.columns if c.endswith("_1981") or c in ("interp_coverage", "n_source_eds", "interp_uncertainty_flag")]
    cols_81 = [c for c in cols_81 if c in df81.columns]
    merged = merged.merge(df81[cols_81], on="ward_code_2001", how="left", suffixes=("", "_dup"))
    merged = merged[[c for c in merged.columns if not c.endswith("_dup")]]

    if "interp_uncertainty_flag" in merged.columns:
        merged["interp_uncertainty_flag"] = merged["interp_uncertainty_flag"].fillna("low")
    else:
        merged["interp_uncertainty_flag"] = "low"

    id_cols   = ["ward_code_2001", "ward_name_2001", "ward_code_1991", "ward_name_1991"]
    meta_cols = ["interp_coverage", "n_source_eds", "interp_uncertainty_flag"]
    data_cols = ([c for c in merged.columns if "1981" in c] +
                 [c for c in merged.columns if "1991" in c and c not in id_cols] +
                 [c for c in merged.columns if c not in id_cols + meta_cols and "1981" not in c and "1991" not in c])
    order = [c for c in id_cols + data_cols + meta_cols if c in merged.columns]
    remaining = [c for c in merged.columns if c not in order]
    merged = merged[order + remaining].loc[:, ~pd.Index(order + remaining).duplicated()]
    log.info("  Harmonised shape: %s", merged.shape)
    return merged


# STEP 6: write harmonisation metadata JSON

def write_metadata(harmonised: pd.DataFrame, uncertainty: pd.DataFrame) -> None:
    high_flag = (uncertainty[uncertainty["interp_uncertainty_flag"] == "HIGH"]
                 [["ward_code_2001", "interp_coverage", "n_source_eds"]].to_dict(orient="records"))
    meta = {
        "produced_at": datetime.utcnow().isoformat() + "Z",
        "anchor_geography": "2001 ward boundaries (england_caswa_2001_clipped.shp)",
        "n_harmonised_zones": int(len(harmonised)),
        "crs": TARGET_CRS,
        "years_included": [1981, 1991, 2001],
        "methods": {
            "1981": "Areal interpolation via polygon overlay; extensive = area-weighted sum; intensive = re-derived from counts",
            "1991": "Direct code mapping (1991 and 2001 ward boundaries are geographically identical)",
            "2001": "Direct OA aggregation to parent ward_code; extensive = sum; intensive = pop-weighted mean",
        },
        "uncertainty_summary": {
            "n_high_uncertainty_zones": len(high_flag),
            "high_uncertainty_zones": high_flag,
            "note": f"HIGH = total ED coverage < {(1 - UNCERTAINTY_THRESHOLD)*100:.0f}% of 2001 ward area",
        },
    }
    out = OUT_DIR / "harmonisation_metadata.json"
    with open(out, "w") as f:
        json.dump(meta, f, indent=2)
    log.info("Metadata saved: %s", out)


# STEP 7: export web GeoJSON files + datasets.json manifest

# Normalised column schema: (output_col, {year: source_col})
SCHEMA: list[tuple[str, dict]] = [
    ("ward_code",  {1981: "ward_code_2001", 1991: "ward_code_2001", 2001: "ward_code_2001"}),
    ("ward_name",  {1981: "ward_name_2001", 1991: "ward_name_2001", 2001: "ward_name_2001"}),
    ("total_population",     {1981: "TOTAL_RES_1981",        1991: "TOTAL_RES_1991",          2001: "total_pop"}),
    ("pct_male",             {1981: "PCT_MALE_1981",         1991: "PCT_MALE_1991",            2001: None}),
    ("pct_female",           {1981: "PCT_FEMALE_1981",       1991: "PCT_FEMALE_1991",          2001: None}),
    ("chinese_ethnic_count", {1981: "CHINESE_BORN_1981",     1991: "CHINESE_ETHNIC_1991",      2001: "chinese_ethnic_count"}),
    ("pct_chinese_ethnic",   {1981: "PCT_CHINESE_BORN_1981", 1991: "PCT_CHINESE_ETHNIC_1991",  2001: "chinese_ethnic_pct"}),
    ("china_born_count",     {1981: "CHINESE_BORN_1981",     1991: "CHINA_BORN_1991",          2001: "asia_born_count"}),
    ("pct_china_born",       {1981: "PCT_CHINESE_BORN_1981", 1991: "PCT_CHINA_BORN_1991",      2001: "asia_born_pct"}),
    ("total_hh",             {1981: "TOTAL_HH_1981",         1991: None,                       2001: "total_hh_spaces"}),
    ("pct_owner_occ",        {1981: "PCT_OWNER_OCC_1981",    1991: "PCT_CHINESE_OWNER_OCC_1991", 2001: "owner_occ_rate"}),
    ("pct_social_rent",      {1981: "PCT_SOCIAL_RENT_1981",  1991: None,                       2001: "council_rent_rate"}),
    ("pct_private_rent",     {1981: None,                    1991: None,                       2001: "private_rent_rate"}),
    ("pct_no_car",           {1981: "PCT_NO_CAR_1981",       1991: None,                       2001: "no_car_rate"}),
    ("pct_overcrowd",        {1981: "PCT_OVERCROWD_GT1P5_1981", 1991: "PCT_CHINESE_OVERCROWD_1991", 2001: "overcrowd_rate"}),
    ("pct_no_bath_wc",       {1981: "PCT_NO_BATH_OR_WC_1981", 1991: None,                     2001: "no_bath_wc_rate"}),
    ("emp_rate",             {1981: "EMP_RATE_1981",          1991: "CHINESE_EMP_RATE_1991",   2001: "econ_active_rate"}),
    ("unemployment_rate",    {1981: None,                     1991: "CHINESE_UNEMP_RATE_1991", 2001: "unemployment_rate"}),
    ("self_employment_rate", {1981: None,                     1991: None,                      2001: "self_employment_rate"}),
    ("interp_coverage",      {1981: "interp_coverage",        1991: "interp_coverage",         2001: "interp_coverage"}),
    ("interp_uncertainty",   {1981: "interp_uncertainty_flag", 1991: "interp_uncertainty_flag", 2001: "interp_uncertainty_flag"}),
]

PROXY_NOTE = {2001: {"pct_china_born": "asia_born_proxy", "china_born_count": "asia_born_proxy"}}
ALL_KEYS = ["year"] + [col for col, _ in SCHEMA]


def _round(v, decimals=2):
    if v is None:
        return None
    try:
        return None if math.isnan(float(v)) else round(float(v), decimals)
    except (TypeError, ValueError):
        return v


def _build_decade_df(df: pd.DataFrame, year: int) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["year"] = year
    for out_col, mapping in SCHEMA:
        src = mapping.get(year)
        out[out_col] = df[src] if src and src in df.columns else None
    return out


def _geojson_features(gdf: gpd.GeoDataFrame, decade_df: pd.DataFrame, year: int) -> list:
    features = []
    for _, geo_row in gdf.iterrows():
        wc = geo_row.get("ward_code_2001") or geo_row.get("ward_code")
        data_row = decade_df.loc[decade_df["ward_code"] == wc]
        if data_row.empty:
            props = {k: None for k in ALL_KEYS}
            props.update({"ward_code": wc, "year": year}) # type: ignore
        else:
            row = data_row.iloc[0]
            props = {k: _round(row.get(k)) for k in ALL_KEYS}
        if year in PROXY_NOTE:
            for field, note in PROXY_NOTE[year].items():
                if field in props:
                    props[f"{field}_note"] = note # type: ignore
        features.append({"type": "Feature", "geometry": geo_row.geometry.__geo_interface__, "properties": props})
    return features


def export_web_geojson(harmonised: pd.DataFrame, gdf: gpd.GeoDataFrame) -> None:
    """Write decade-specific GeoJSON files and datasets.json manifest for the web app."""
    log.info("Exporting web GeoJSON...")
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.0001, preserve_topology=True)

    for candidate in ("ward_code_2001", "ward_code", "WD01CD", "code"):
        if candidate in gdf.columns:
            if candidate != "ward_code_2001":
                gdf = gdf.rename(columns={candidate: "ward_code_2001"})
            break

    manifest_layers = []
    indicator_keys = [col for col, _ in SCHEMA if col not in ("ward_code", "ward_name", "interp_coverage", "interp_uncertainty")]

    for year in [1981, 1991, 2001]:
        decade_df = _build_decade_df(harmonised, year)
        features  = _geojson_features(gdf, decade_df, year)
        geojson   = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }
        out_path = WEB_DIR / f"manchester_wards_{year}.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, separators=(",", ":"))
        size_kb = out_path.stat().st_size / 1024
        log.info("  %d: %d features  -> %s  (%.1f KB)", year, len(features), out_path, size_kb)

        available = [k for k in indicator_keys if any(f["properties"].get(k) is not None for f in features)]
        manifest_layers.append({
            "year": year, "geojson": f"/geojson/manchester_wards_{year}.geojson",
            "featureCount": len(features), "indicators": available,
        })

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
                2001: "Asia-born proxy (no OA-level China COB in 2001)",
            },
            "emp_rate": {
                1981: "% employed (all residents)",
                1991: "% economically active (Chinese sub-population only)",
                2001: "% economically active aged 16-74 (CS028EW)",
            },
            "pct_owner_occ": {1991: "Chinese households only"},
            "pct_overcrowd":  {1991: "Chinese households only"},
        },
    }
    manifest_path = WEB_DIR / "datasets.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info("Manifest saved: %s", manifest_path)


# main

def main() -> None:
    log.info("=== Step 4: Harmonise ward boundaries + export web GeoJSON ===")

    eds81, wards91, wards01 = load_boundaries()

    harm_2001 = harmonise_2001(wards01)
    harm_1991 = harmonise_1991(wards01)
    harm_1981, uncertainty_df = harmonise_1981(eds81, wards01)

    harmonised = merge_years(harm_1981, harm_1991, harm_2001)

    csv_path = OUT_DIR / "manchester_harmonised_indicators_1981_1991_2001.csv"
    harmonised.to_csv(csv_path, index=False)
    log.info("Harmonised CSV: %s  (%d rows x %d cols)", csv_path, *harmonised.shape)

    geojson_path = OUT_DIR / "harmonised_zones.geojson"
    harm_gdf = wards01[["ons_label", "geometry"]].rename(columns={"ons_label": "ward_code_2001"})
    harm_gdf = harm_gdf.merge(harmonised, on="ward_code_2001", how="left")
    harm_gdf = gpd.GeoDataFrame(harm_gdf, geometry="geometry", crs=TARGET_CRS)
    harm_gdf.to_crs("EPSG:4326").to_file(geojson_path, driver="GeoJSON")
    log.info("GeoJSON saved: %s", geojson_path)

    write_metadata(harmonised, uncertainty_df)

    export_web_geojson(harmonised, harm_gdf.copy())

    high = (uncertainty_df["interp_uncertainty_flag"] == "HIGH").sum()
    log.info("=== Harmonisation complete: %d zones / %d high-uncertainty ===", len(harmonised), high)


if __name__ == "__main__":
    main()
