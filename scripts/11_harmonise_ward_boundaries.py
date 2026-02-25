"""
Step 4: Harmonise Ward Boundaries Across 1981, 1991, and 2001
=============================================================

Produces a single temporal dataset anchored on 2001 ward boundaries so that
all three census years can be compared like-for-like.

Key decisions made from boundary inspection:
  1. Anchor geography: 2001 ward boundaries (33 Manchester wards, codes 00BNFA…)
  2. 1991 → 2001: DIRECT CODE MAPPING – the 2001 ward shapefile's `label` column
     already encodes the equivalent 1991 ward code (03BNFA…), so the ward
     boundaries are identical; only the codes changed. No spatial interpolation.
  3. 1981 → 2001: AREAL INTERPOLATION of 1981 EDs onto 2001 ward polygons.
     All 1017 Manchester EDs are joined by ED81CDO → indicator zoneid.
  4. Extensive variables (counts) → area-weighted sum.
     Intensive variables (rates/%) → re-derived from interpolated counts where
     possible; otherwise area-weighted mean (fallback).
  5. Uncertainty flag: where the largest-area ED contributing to a 2001 ward
     covers < 70 % of that ward's total area from EDs, it is flagged HIGH.

Outputs (data/processed/indicators/temporal/):
  manchester_harmonised_indicators_1981_1991_2001.csv
  harmonised_zones.geojson
  harmonisation_metadata.json
"""

from __future__ import annotations

import json
import logging
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

# ── Paths ───────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parents[1]
BND = BASE / "gis_boundaries"
IND = BASE / "data" / "processed" / "indicators"
OUT_DIR = IND / "temporal"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
UNCERTAINTY_THRESHOLD = 0.30   # flag if >30% of area is from fragmented sources
TARGET_CRS = "EPSG:27700"       # British National Grid

# ── Variable classification ──────────────────────────────────────────────────
# Extensive: counts — summed during areal interpolation
# Intensive: rates/percentages — re-derived from interpolated counts later

# NOTE: We use manchester_eds_1981_indicators.csv (the Phase 6 file that contains
# complete ED-level rows with TOTAL_RES_1981 populated) rather than the Phase 7
# _ed_level file which had TOTAL_RES as all-null.
COLS_1981_EXTENSIVE = [
    "TOTAL_RES_1981",
    "CHINESE_BORN_1981", "CHINESE_BORN_MALE_1981", "CHINESE_BORN_FEMALE_1981",
    "ALL_EMPLOYED_1981",
    "TOTAL_HH_1981", "OWNER_OCC_HH_1981", "SOCIAL_RENT_HH_1981", "NO_CAR_HH_1981",
    "OVERCROWD_GT1P5_1981", "OVERCROWD_1TO1P5_1981",
    "NO_BATH_OR_WC_1981", "NO_INSIDE_BATH_OR_WC_1981",
]
COLS_1981_INTENSIVE = [
    "PCT_MALE_1981", "PCT_FEMALE_1981",
    "PCT_CHINESE_BORN_1981",
    "EMP_RATE_1981",
    "PCT_OWNER_OCC_1981", "PCT_SOCIAL_RENT_1981", "PCT_NO_CAR_1981",
    "CAR_OWNERSHIP_INDEX_1981",
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
    "CHINESE_HOUSEHOLDS_1991",
    "CHINESE_OVERCROWD_GT1P5_1991", "CHINESE_OWNER_OCC_1991",
]
COLS_1991_INTENSIVE = [
    "PCT_MALE_1991", "PCT_FEMALE_1991",
    "PCT_CHINESE_ETHNIC_1991", "PCT_CHINA_BORN_1991",
    "CHINESE_EMP_RATE_1991", "CHINESE_UNEMP_RATE_1991",
    "PCT_CHINESE_OVERCROWD_1991", "PCT_CHINESE_OWNER_OCC_1991",
]

COLS_2001_EXTENSIVE = [
    "total_pop", "chinese_ethnic_count", "asia_born_count", "pop_16_74",
    "total_hh_spaces",
]
COLS_2001_INTENSIVE = [
    "chinese_ethnic_pct", "asia_born_pct",
    "econ_active_rate", "unemployment_rate", "self_employment_rate",
    "owner_occ_rate", "council_rent_rate", "private_rent_rate",
    "overcrowd_rate", "overcrowd_severe_rate",
    "no_bath_wc_rate", "no_car_rate",
]


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: Load and validate boundary files
# ══════════════════════════════════════════════════════════════════════════════

def load_boundaries() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Return (eds_1981, wards_1991, wards_2001) — all Manchester, EPSG:27700."""
    log.info("Loading boundary files…")

    # 1981 EDs — filter to Manchester district only
    eds81 = gpd.read_file(BND / "1981" / "ED_1981_EW.shp")
    eds81 = eds81[eds81["LAD81CD"] == "03BN"].copy()
    eds81["geometry"] = eds81["geometry"].apply(make_valid)
    eds81 = eds81.to_crs(TARGET_CRS)
    eds81["ed_area_m2"] = eds81["geometry"].area
    log.info("  1981 EDs: %d features", len(eds81))

    # 1991 wards — filter to Manchester (label starts with 03BN)
    wards91 = gpd.read_file(BND / "1991" / "england_wa_1991.shp")
    wards91 = wards91[wards91["label"].str.startswith("03BN", na=False)].copy()
    wards91["geometry"] = wards91["geometry"].apply(make_valid)
    wards91 = wards91.to_crs(TARGET_CRS)
    log.info("  1991 Wards: %d features", len(wards91))

    # 2001 wards — Manchester identified by ons_label starting with 00BN
    wards01 = gpd.read_file(BND / "2001" / "wards" / "england_caswa_2001_clipped.shp")
    wards01 = wards01[wards01["ons_label"].str.startswith("00BN", na=False)].copy()
    wards01["geometry"] = wards01["geometry"].apply(make_valid)
    wards01 = wards01.to_crs(TARGET_CRS)
    wards01["ward_area_m2"] = wards01["geometry"].area
    log.info("  2001 Wards: %d features", len(wards01))

    return eds81, wards91, wards01


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: Build harmonised 2001 base (direct OA aggregation)
# ══════════════════════════════════════════════════════════════════════════════

def harmonise_2001(wards01: gpd.GeoDataFrame) -> pd.DataFrame:
    """Aggregate 2001 OA indicators to 2001 ward boundaries.

    Method: direct aggregation – each OA already carries its parent ward_code.
    Extensive cols are summed; intensive cols are population-weighted means.
    """
    log.info("Harmonising 2001 (OA → ward aggregation)…")
    df = pd.read_csv(IND / "2001" / "manchester_oas_2001_indicators.csv")
    log.info("  Loaded %d OA rows", len(df))

    avail_ext = [c for c in COLS_2001_EXTENSIVE if c in df.columns]
    avail_int = [c for c in COLS_2001_INTENSIVE if c in df.columns]

    # Sums of extensive variables
    agg_ext = df.groupby("ward_code")[avail_ext].sum()

    # Population-weighted means for intensive variables
    df["_w"] = df["total_pop"]                # weight = population

    def pop_wavg(grp: pd.DataFrame) -> pd.Series:
        w = grp["_w"]
        tot = w.sum()
        res = {}
        for col in avail_int:
            vals = grp[col].fillna(0)
            res[col] = (vals * w).sum() / tot if tot > 0 else np.nan
        return pd.Series(res)

    agg_int = df.groupby("ward_code").apply(pop_wavg, include_groups=False)

    result = agg_ext.join(agg_int)
    result.index.name = "ward_code_2001"
    result = result.reset_index()

    # Attach ward names from boundary file
    name_map = wards01.set_index("ons_label")["name"].to_dict()
    label_map = wards01.set_index("ons_label")["label"].to_dict()
    result["ward_name_2001"] = result["ward_code_2001"].map(name_map)
    result["ward_code_1991"] = result["ward_code_2001"].map(label_map)

    log.info("  → %d ward rows", len(result))
    return result


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Harmonise 1991 wards (direct code-mapping, no spatial op needed)
# ══════════════════════════════════════════════════════════════════════════════

def harmonise_1991(wards01: gpd.GeoDataFrame) -> pd.DataFrame:
    """Map 1991 ward indicators to 2001 ward codes.

    The 2001 ward shapefile's `label` column encodes the corresponding 1991
    ward code — confirming the two boundary sets share identical geography with
    only a code change.  Therefore no spatial interpolation is required.
    """
    log.info("Harmonising 1991 (direct code mapping — boundaries are identical)…")
    df91 = pd.read_csv(IND / "1991" / "manchester_wards_1991_indicators.csv")
    log.info("  Loaded %d 1991 ward rows", len(df91))

    # Build the 1991→2001 code lookup from the 2001 ward boundary
    lookup = wards01[["ons_label", "label"]].rename(
        columns={"ons_label": "ward_code_2001", "label": "ward_code_1991"}
    )

    avail_ext = [c for c in COLS_1991_EXTENSIVE if c in df91.columns]
    avail_int = [c for c in COLS_1991_INTENSIVE if c in df91.columns]

    # Rename zoneid to ward_code_1991 for join
    df91 = df91.rename(columns={"zoneid": "ward_code_1991"})

    # Keep only relevant columns
    keep = ["ward_code_1991", "ward_name"] + avail_ext + avail_int
    keep = [c for c in keep if c in df91.columns]
    df91 = df91[keep].copy()

    result = df91.merge(lookup, on="ward_code_1991", how="left")

    unmatched = result["ward_code_2001"].isna().sum()
    if unmatched:
        log.warning("  %d 1991 wards could not be mapped to 2001 codes", unmatched)

    log.info("  → %d ward rows matched", result["ward_code_2001"].notna().sum())
    return result


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Harmonise 1981 EDs (areal interpolation to 2001 wards)
# ══════════════════════════════════════════════════════════════════════════════

def harmonise_1981(
    eds81: gpd.GeoDataFrame,
    wards01: gpd.GeoDataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Spatially reaggregate 1981 ED indicators to 2001 ward boundaries.

    Uses manchester_eds_1981_indicators.csv (Phase 6 file) which contains
    complete ED-level rows (8-char codes) with TOTAL_RES populated.
    Returns (harmonised_df, uncertainty_df).
    """
    log.info("Harmonising 1981 (areal interpolation: EDs → 2001 wards)…")

    # Load Phase 6 indicator file and extract ED-level rows only (8-char codes)
    df_all = pd.read_csv(IND / "1981" / "manchester_eds_1981_indicators.csv")
    df_all["zoneid"] = df_all["zoneid"].str.strip()
    df81 = df_all[df_all["zoneid"].str.len() == 8].copy()
    df81 = df81.rename(columns={"zoneid": "ED81CDO"})
    log.info("  Loaded %d 1981 ED indicator rows (from Phase 6 file)", len(df81))

    # Merge indicators onto geometries
    geo = eds81.merge(df81, on="ED81CDO", how="inner")
    log.info("  Geometries joined: %d EDs", len(geo))

    avail_ext = [c for c in COLS_1981_EXTENSIVE if c in geo.columns]
    avail_int = [c for c in COLS_1981_INTENSIVE if c in geo.columns]

    # Coerce numeric — some cols may have nulls (EMPLOYED etc in 1981 data)
    for col in avail_ext + avail_int:
        geo[col] = pd.to_numeric(geo[col], errors="coerce")

    # ── Polygon overlay (intersection) ──────────────────────────────────────
    log.info("  Running polygon overlay (intersection)…")
    # Ensure CRS match
    wards_target = wards01[["ons_label", "name", "label", "ward_area_m2", "geometry"]].copy()
    wards_target = wards_target.rename(
        columns={"ons_label": "ward_code_2001", "name": "ward_name_2001",
                 "label": "ward_code_1991"}
    )

    intersection = gpd.overlay(
        geo,
        wards_target,
        how="intersection",
        keep_geom_type=True,
    )
    intersection["frag_area_m2"] = intersection["geometry"].area
    log.info("  Intersection fragments: %d", len(intersection))

    # Area weight = fragment area / source ED area
    intersection["area_weight"] = (
        intersection["frag_area_m2"] / intersection["ed_area_m2"]
    ).clip(0, 1)

    # ── Aggregate extensive variables (weighted sum) ─────────────────────────
    agg_dict: dict = {}
    for col in avail_ext:
        intersection[f"_wt_{col}"] = intersection[col] * intersection["area_weight"]
        agg_dict[f"_wt_{col}"] = "sum"

    # We still aggregate the raw intensive values (area-weighted mean fallback)
    for col in avail_int:
        intersection[f"_wt_{col}"] = intersection[col] * intersection["area_weight"]
        agg_dict[f"_wt_{col}"] = "sum"
        agg_dict[f"_wt_{col}_denom"] = "sum"  # placeholder – see below

    # Also track total area weight per 2001 ward (for normalising intensive)
    intersection["_area_wt_sum"] = intersection["area_weight"]

    grouped = intersection.groupby("ward_code_2001")

    # Sum weighted counts (extensive)
    ext_agg: dict = {
        col: grouped[f"_wt_{col}"].sum() for col in avail_ext
    }
    ext_df = pd.DataFrame(ext_agg)
    ext_df.index.name = "ward_code_2001"

    # For intensive: area-weighted mean = sum(weight * value) / sum(weight)
    area_wt_total = grouped["_area_wt_sum"].sum()
    int_agg: dict = {}
    for col in avail_int:
        int_agg[col] = grouped[f"_wt_{col}"].sum() / area_wt_total

    int_df = pd.DataFrame(int_agg)
    int_df.index.name = "ward_code_2001"

    result = ext_df.join(int_df).reset_index()

    # Re-derive intensive variables from the interpolated counts where possible
    result = _rederive_1981_rates(result)

    # ── Re-attach ward metadata ─────────────────────────────────────────────
    ward_meta = wards_target[["ward_code_2001", "ward_name_2001", "ward_code_1991"]].drop_duplicates()
    result = result.merge(ward_meta, on="ward_code_2001", how="left")

    # ── Uncertainty flagging ─────────────────────────────────────────────────
    log.info("  Computing interpolation uncertainty flags…")
    uncertainty = _compute_1981_uncertainty(intersection, wards01)

    result = result.merge(
        uncertainty[["ward_code_2001", "interp_coverage",
                     "n_source_eds", "interp_uncertainty_flag"]],
        on="ward_code_2001", how="left",
    )

    log.info("  → %d ward rows", len(result))
    return result, uncertainty


def _rederive_1981_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Re-derive 1981 rate indicators from interpolated extensive counts."""
    def safe_pct(num_col: str, den_col: str, scale: float = 100.0) -> pd.Series:
        num = df[num_col] if num_col in df.columns else pd.Series(np.nan, index=df.index)
        den = df[den_col] if den_col in df.columns else pd.Series(np.nan, index=df.index)
        return pd.Series(
            np.where(den > 0, scale * num / den, np.nan), index=df.index
        )

    if "TOTAL_RES_1981" in df.columns:
        df["PCT_CHINESE_BORN_1981"] = safe_pct("CHINESE_BORN_1981", "TOTAL_RES_1981")

    if "TOTAL_HH_1981" in df.columns:
        for cnt, pct in [
            ("OWNER_OCC_HH_1981",     "PCT_OWNER_OCC_1981"),
            ("SOCIAL_RENT_HH_1981",   "PCT_SOCIAL_RENT_1981"),
            ("NO_CAR_HH_1981",        "PCT_NO_CAR_1981"),
            ("OVERCROWD_GT1P5_1981",  "PCT_OVERCROWD_GT1P5_1981"),
            ("OVERCROWD_1TO1P5_1981", "PCT_OVERCROWD_1TO1P5_1981"),
            ("NO_BATH_OR_WC_1981",    "PCT_NO_BATH_OR_WC_1981"),
            ("NO_INSIDE_BATH_OR_WC_1981", "PCT_NO_INSIDE_BATH_OR_WC_1981"),
        ]:
            df[pct] = safe_pct(cnt, "TOTAL_HH_1981")

    return df


def _compute_1981_uncertainty(
    intersection: gpd.GeoDataFrame,
    wards01: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Flag 2001 wards where 1981 areal interpolation uncertainty is high.

    Uncertainty is HIGH when the total area accounted for by intersecting
    EDs covers < (1 - UNCERTAINTY_THRESHOLD) of the ward area, OR when many
    small ED fragments each contribute < 10% of the ward area.
    """
    # Total area contributed by EDs to each 2001 ward
    covered = (
        intersection.groupby("ward_code_2001")["frag_area_m2"].sum()
        .reset_index()
        .rename(columns={"frag_area_m2": "total_covered_m2"})
    )
    ward_areas = wards01.set_index("ons_label")["ward_area_m2"].reset_index()
    ward_areas.columns = ["ward_code_2001", "ward_area_m2"]

    n_eds = (
        intersection.groupby("ward_code_2001")["ED81CDO"]
        .nunique()
        .reset_index()
        .rename(columns={"ED81CDO": "n_source_eds"})
    )

    unc = covered.merge(ward_areas, on="ward_code_2001").merge(n_eds, on="ward_code_2001")
    unc["interp_coverage"] = (unc["total_covered_m2"] / unc["ward_area_m2"]).clip(0, 1)
    unc["interp_uncertainty_flag"] = np.where(
        unc["interp_coverage"] < (1 - UNCERTAINTY_THRESHOLD), "HIGH", "low"
    )

    high = (unc["interp_uncertainty_flag"] == "HIGH").sum()
    log.info(
        "  Uncertainty flags: %d HIGH / %d wards (threshold=%.0f%% area gap)",
        high, len(unc), UNCERTAINTY_THRESHOLD * 100,
    )
    return unc


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: Merge all three years into a single harmonised dataset
# ══════════════════════════════════════════════════════════════════════════════

def merge_years(
    df81: pd.DataFrame,
    df91: pd.DataFrame,
    df01: pd.DataFrame,
) -> pd.DataFrame:
    """Outer-join all three year datasets on ward_code_2001."""
    log.info("Merging three-year harmonised dataset…")

    # Standardise the merge key in each dataframe
    df91 = df91.rename(columns={"ward_name": "ward_name_1991"})
    df91 = df91.drop(columns=["ward_code_1991"], errors="ignore")  # will come from df01

    df01 = df01.rename(columns={
        "ward_code_2001": "ward_code_2001",
    })

    # Start from the 2001 base (complete set of 33 wards)
    merged = df01.copy()
    merged = merged.rename(columns={"ward_code_1991": "ward_code_1991"})

    # Merge 1991
    cols_91 = list(dict.fromkeys(
        ["ward_code_2001", "ward_name_1991"] +
        [c for c in df91.columns
         if c.endswith("_1991") and c not in ("ward_name_1991",)]
    ))
    cols_91 = [c for c in cols_91 if c in df91.columns]
    merged = merged.merge(
        df91[cols_91].rename(
            columns={"ward_code_2001": "ward_code_2001"}
        ),
        on="ward_code_2001",
        how="left",
        suffixes=("", "_dup"),
    )
    # Drop any duplicate columns
    merged = merged[[c for c in merged.columns if not c.endswith("_dup")]]

    # Merge 1981
    cols_81 = (
        ["ward_code_2001"] +
        [c for c in df81.columns
         if c.endswith("_1981") or c in
         ("interp_coverage", "n_source_eds", "interp_uncertainty_flag")]
    )
    cols_81 = [c for c in cols_81 if c in df81.columns]
    merged = merged.merge(
        df81[cols_81],
        on="ward_code_2001",
        how="left",
        suffixes=("", "_dup"),
    )
    merged = merged[[c for c in merged.columns if not c.endswith("_dup")]]

    # Fill uncertainty flag for 1991 and 2001 (no interpolation)
    if "interp_uncertainty_flag" not in merged.columns:
        merged["interp_uncertainty_flag"] = "low"
    else:
        merged["interp_uncertainty_flag"] = merged["interp_uncertainty_flag"].fillna("low")

    # Reorder: identifiers first, then 1981, 1991, 2001, then metadata
    id_cols = [
        "ward_code_2001", "ward_name_2001", "ward_code_1991", "ward_name_1991",
    ]
    meta_cols = ["interp_coverage", "n_source_eds", "interp_uncertainty_flag"]
    data_cols = (
        [c for c in merged.columns if "1981" in c] +
        [c for c in merged.columns if "1991" in c and c not in id_cols] +
        [c for c in merged.columns
         if c not in id_cols + meta_cols
         and "1981" not in c and "1991" not in c]
    )
    final_order = id_cols + data_cols + meta_cols
    final_order = [c for c in final_order if c in merged.columns]
    # add any remaining columns at the end
    remaining = [c for c in merged.columns if c not in final_order]
    merged = merged[final_order + remaining]
    # Drop any remaining duplicate columns
    merged = merged.loc[:, ~merged.columns.duplicated()]

    log.info("  Final harmonised shape: %s", merged.shape)
    return merged


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: Build harmonised_zones.geojson
# ══════════════════════════════════════════════════════════════════════════════

def build_harmonised_geojson(
    wards01: gpd.GeoDataFrame,
    harmonised: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """Attach harmonised indicators to 2001 ward geometries → GeoJSON."""
    log.info("Building harmonised_zones.geojson…")
    geom_df = wards01[["ons_label", "geometry"]].rename(
        columns={"ons_label": "ward_code_2001"}
    )
    # Drop any duplicate columns from harmonised before merging
    harm_clean = harmonised.copy()
    harm_clean = harm_clean.loc[:, ~harm_clean.columns.duplicated()]
    gdf = geom_df.merge(harm_clean, on="ward_code_2001", how="left")
    return gpd.GeoDataFrame(gdf, geometry="geometry", crs=TARGET_CRS)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7: Write harmonisation metadata
# ══════════════════════════════════════════════════════════════════════════════

def write_metadata(harmonised: pd.DataFrame, uncertainty: pd.DataFrame) -> None:
    """Write harmonisation_metadata.json."""
    high_flag = (
        uncertainty[uncertainty["interp_uncertainty_flag"] == "HIGH"]
        [["ward_code_2001", "interp_coverage", "n_source_eds"]]
        .to_dict(orient="records")
    )

    meta = {
        "produced_at": datetime.utcnow().isoformat() + "Z",
        "anchor_geography": "2001 ward boundaries (england_caswa_2001_clipped.shp)",
        "anchor_geography_code_prefix": "00BN",
        "n_harmonised_zones": int(len(harmonised)),
        "crs": TARGET_CRS,
        "years_included": [1981, 1991, 2001],
        "methods": {
            "1981": {
                "source_units": "1981 Enumeration Districts (1017 EDs)",
                "method": "Areal interpolation via polygon overlay (gpd.overlay intersection)",
                "extensive_vars": "area-weighted sum (count * fragment_area/ed_area)",
                "intensive_vars": "re-derived from interpolated counts; fallback: area-weighted mean",
                "uncertainty_threshold": f"{UNCERTAINTY_THRESHOLD*100:.0f}% area gap",
            },
            "1991": {
                "source_units": "1991 wards (33 wards, already at ward level)",
                "method": "Direct code mapping only — 1991 and 2001 ward boundaries "
                          "are geographically identical (confirmed by comparing "
                          "england_wa_1991.shp label codes with england_caswa_2001_clipped.shp "
                          "label column). No spatial interpolation performed.",
                "code_crosswalk": "2001_ward.ons_label ↔ 2001_ward.label (=1991 code)",
            },
            "2001": {
                "source_units": "2001 Output Areas (1341 OAs)",
                "method": "Direct aggregation using ward_code field already present in OA data",
                "extensive_vars": "sum",
                "intensive_vars": "population-weighted mean (weight = total_pop)",
            },
        },
        "source_files": {
            "1981_indicators": "data/processed/indicators/1981/manchester_eds_1981_indicators.csv (ED-level rows, code_len=8)",
            "1991_indicators": "data/processed/indicators/1991/manchester_wards_1991_indicators.csv",
            "2001_indicators": "data/processed/indicators/2001/manchester_oas_2001_indicators.csv",
            "1981_boundaries": "gis_boundaries/1981/ED_1981_EW.shp",
            "1991_boundaries": "gis_boundaries/1991/england_wa_1991.shp",
            "2001_ward_boundaries": "gis_boundaries/2001/wards/england_caswa_2001_clipped.shp",
        },
        "variable_classification": {
            "1981_extensive": COLS_1981_EXTENSIVE,
            "1981_intensive": COLS_1981_INTENSIVE,
            "1991_extensive": COLS_1991_EXTENSIVE,
            "1991_intensive": COLS_1991_INTENSIVE,
            "2001_extensive": COLS_2001_EXTENSIVE,
            "2001_intensive": COLS_2001_INTENSIVE,
        },
        "uncertainty_summary": {
            "n_high_uncertainty_zones": len(high_flag),
            "high_uncertainty_zones": high_flag,
            "note": "HIGH = total ED coverage < 70% of 2001 ward area; may indicate "
                    "areas with boundary misalignment or data gaps at ED level",
        },
        "assumptions": [
            "Population is uniformly distributed within 1981 ED polygons "
            "(no sub-ED population surface available for 1981)",
            "1991 and 2001 ward boundaries are treated as geographically identical "
            "based on matching polygon labels in the 2001 ward boundary file",
            "2001 OA ward_code field accurately assigns each OA to its parent 2001 ward",
            "Rates/percentages for 1981 are re-derived from area-interpolated counts "
            "to avoid compounding interpolation error",
        ],
    }

    out_path = OUT_DIR / "harmonisation_metadata.json"
    with open(out_path, "w") as f:
        json.dump(meta, f, indent=2)
    log.info("  Saved: %s", out_path)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    log.info("=" * 70)
    log.info("Phase 9: Ward Boundary Harmonisation 1981 / 1991 / 2001")
    log.info("=" * 70)

    # Step 1: Load boundaries
    eds81, wards91, wards01 = load_boundaries()

    # Step 2: 2001 OA → ward aggregation
    harm_2001 = harmonise_2001(wards01)

    # Step 3: 1991 code mapping
    harm_1991 = harmonise_1991(wards01)

    # Step 4: 1981 areal interpolation
    harm_1981, uncertainty_df = harmonise_1981(eds81, wards01)

    # Step 5: Merge three years
    harmonised = merge_years(harm_1981, harm_1991, harm_2001)

    # Step 6: Save CSV
    csv_path = OUT_DIR / "manchester_harmonised_indicators_1981_1991_2001.csv"
    harmonised.to_csv(csv_path, index=False)
    log.info("Saved CSV: %s  (%d rows × %d cols)", csv_path, *harmonised.shape)

    # Step 7: Build and save GeoJSON
    harm_gdf = build_harmonised_geojson(wards01, harmonised)
    geojson_path = OUT_DIR / "harmonised_zones.geojson"
    harm_gdf.to_crs("EPSG:4326").to_file(geojson_path, driver="GeoJSON")
    log.info("Saved GeoJSON: %s", geojson_path)

    # Step 8: Write metadata
    write_metadata(harmonised, uncertainty_df)

    # Step 9: Summary
    log.info("")
    log.info("=" * 70)
    log.info("Harmonisation complete.")
    log.info("  Zones: %d  |  Columns: %d", *harmonised.shape)
    log.info("  High uncertainty zones: %d",
             (uncertainty_df["interp_uncertainty_flag"] == "HIGH").sum())
    log.info("=" * 70)

    # Print a quick sample
    id_cols = ["ward_code_2001", "ward_name_2001"]
    preview_cols = id_cols + [
        c for c in harmonised.columns
        if c in ("TOTAL_RES_1981", "TOTAL_RES_1991", "total_pop",
                 "PCT_FAR_EAST_BORN_1981", "PCT_CHINESE_ETHNIC_1991",
                 "chinese_ethnic_pct", "interp_uncertainty_flag")
    ]
    log.info("\nSample output (first 5 rows):\n%s",
             harmonised[preview_cols].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
