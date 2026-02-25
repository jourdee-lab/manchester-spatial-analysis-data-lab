#!/usr/bin/env python3
"""
Step 5: Aggregate 2001 OA Indicators to Ward Level
===================================================

Aggregates 2001 OA-level indicators to ward level, then merges them into the
existing 1981–1991 temporal comparison CSV, producing a unified three-decade
cross-sectional dataset.

Inputs:
  data/processed/indicators/2001/manchester_oas_2001_indicators.csv
  data/processed/indicators/temporal/manchester_1981_1991_comparison.csv
  data/lookups/2001_geography_lookup_england.csv  (OA → ward code mapping)

Outputs:
  data/processed/indicators/temporal/manchester_1981_1991_2001_comparison.csv
  (also overwrites manchester_1981_1991_comparison.csv for backwards compatibility)

Notes on cross-decade geography alignment
──────────────────────────────────────────
• 1981/1991 use '03BN' ward codes; 2001 uses '00BN' OA codes.
• Ward codes change between census decades due to boundary revisions.
• This script attempts to match on ward *name* if numeric codes differ.
• Unmatched wards are appended as new rows; common indicators are aligned
  by column name regardless of decade.
• A 'GEOGRAPHY_MATCH_TYPE' column records the match confidence:
    'exact'   – codes matched directly
    'name'    – matched on ward name after normalisation
    'code_prefix' – matched by stripping prefix (03BN → BN prefix matching)
    'new_2001'    – 2001 ward with no 1981/1991 counterpart

Common indicators aligned across all three years:
  total_pop, chinese_ethnic_pct (or proxy), unemployment_rate,
  owner_occ_rate, council_rent_rate, no_car_rate

Author: FYP Data Pipeline
Date: 2026-02-25
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

INDICATORS_2001_PATH = (
    DATA_DIR / "processed" / "indicators" / "2001" / "manchester_oas_2001_indicators.csv"
)
TEMPORAL_DIR = DATA_DIR / "processed" / "indicators" / "temporal"
TEMPORAL_IN = TEMPORAL_DIR / "manchester_1981_1991_comparison.csv"
TEMPORAL_OUT_FULL = TEMPORAL_DIR / "manchester_1981_1991_2001_comparison.csv"
TEMPORAL_OUT_COMPAT = TEMPORAL_DIR / "manchester_1981_1991_comparison.csv"  # overwritten

GEO_LOOKUP_PATH = DATA_DIR / "lookups" / "2001_geography_lookup_england.csv"

# ONS 2001 geography lookup: typical column names for the OA→ward mapping
OA_CODE_CANDIDATES = ["oa_code", "OA_CODE", "OA01CD", "oa01cd"]
WARD_CODE_2001_CANDIDATES = ["ward_code", "WARD_CODE", "WD01CD", "wd01cd", "ward01cd", "WARD01CD"]
WARD_NAME_CANDIDATES = ["ward_name", "WARD_NAME", "WD01NM", "wd01nm", "ward01nm", "WARD01NM"]
GEO_ZONEID_CANDIDATES = ["zoneid", "ZONEID"] + OA_CODE_CANDIDATES

MANCHESTER_PREFIX = "00BN"  # 2001 OA prefix

# Indicators to aggregate from OA to ward (weighted by total_pop for rates)
# Format: (oa_col, ward_col_2001, aggregation_type)
INDICATORS_TO_AGGREGATE = [
    ("total_pop",            "TOTAL_POP_2001",          "sum"),
    ("chinese_ethnic_count", "CHINESE_ETHNIC_2001",     "sum"),
    ("chinese_ethnic_pct",   "PCT_CHINESE_ETHNIC_2001", "wavg"),   # weighted average
    ("asia_born_count",      "ASIA_BORN_2001",          "sum"),
    ("asia_born_pct",        "PCT_ASIA_BORN_2001",      "wavg"),   # PROXY
    ("unemployment_rate",    "UNEMPLOYMENT_RATE_2001",  "wavg"),
    ("econ_active_rate",     "ECON_ACTIVE_RATE_2001",   "wavg"),
    ("self_employment_rate", "SELF_EMP_RATE_2001",      "wavg"),
    ("owner_occ_rate",       "PCT_OWNER_OCC_2001",      "wavg"),
    ("council_rent_rate",    "PCT_COUNCIL_RENT_2001",   "wavg"),
    ("private_rent_rate",    "PCT_PRIVATE_RENT_2001",   "wavg"),
    ("overcrowd_rate",       "PCT_OVERCROWD_2001",      "wavg"),
    ("no_bath_wc_rate",      "PCT_NO_BATH_WC_2001",     "wavg"),
    ("no_car_rate",          "PCT_NO_CAR_2001",         "wavg"),
]

# Columns in the existing temporal CSV that map to the common cross-decade set
CROSS_DECADE_MAP = {
    "total_pop": {
        "1981": "TOTAL_RES_1981",
        "1991": "TOTAL_RES_1991",
        "2001": "TOTAL_POP_2001",
    },
    "chinese_ethnic_pct": {
        "1981": "PCT_CHINESE_1981",   # COB proxy in 1981
        "1991": "PCT_CHINESE_1991",   # ethnic self-id in 1991
        "2001": "PCT_CHINESE_ETHNIC_2001",
    },
    "unemployment_rate": {
        "1981": None,                      # Not available in 1981
        "1991": None,                      # Not in existing temporal CSV
        "2001": "UNEMPLOYMENT_RATE_2001",
    },
    "owner_occ_rate": {
        "1981": "PCT_OWNER_OCC_1981",
        "1991": None,
        "2001": "PCT_OWNER_OCC_2001",
    },
    "council_rent_rate": {
        "1981": None,
        "1991": None,
        "2001": "PCT_COUNCIL_RENT_2001",
    },
    "no_car_rate": {
        "1981": "PCT_NO_CAR_1981",
        "1991": None,
        "2001": "PCT_NO_CAR_2001",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def weighted_avg(group: pd.DataFrame, value_col: str, weight_col: str = "total_pop") -> float:
    """Population-weighted mean, ignoring NaN."""
    valid = group[[value_col, weight_col]].dropna()
    if valid.empty or valid[weight_col].sum() == 0:
        return np.nan
    return np.average(valid[value_col], weights=valid[weight_col])


# ─────────────────────────────────────────────────────────────────────────────
# LOAD 2001 INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def load_2001_indicators() -> pd.DataFrame | None:
    if not INDICATORS_2001_PATH.exists():
        logger.error(f"2001 indicator file not found: {INDICATORS_2001_PATH}")
        logger.error("Run scripts/07_compute_indicators_2001_oas.py first.")
        return None

    df = pd.read_csv(INDICATORS_2001_PATH, dtype={"zoneid": str})
    df["zoneid"] = df["zoneid"].str.strip().str.upper()
    logger.info(f"Loaded 2001 OA indicators: {len(df)} OAs")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# OA → WARD MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def build_oa_ward_lookup(oas: pd.DataFrame) -> pd.DataFrame:
    """
    Build an OA-to-ward mapping for Manchester 2001 OAs.

    Strategy (in order of preference):
    1. Use gis_boundaries/2001 geography lookup CSV if available
    2. Fall back to deriving ward code from OA code first 6 chars
       (00BNxx → ward = 00BNxx, where xx is the ward suffix)
    """
    if GEO_LOOKUP_PATH.exists():
        logger.info(f"  Using geography lookup: {GEO_LOOKUP_PATH}")
        geo = pd.read_csv(GEO_LOOKUP_PATH, dtype=str)

        oa_col = _find_col(geo, OA_CODE_CANDIDATES + GEO_ZONEID_CANDIDATES)
        ward_col = _find_col(geo, WARD_CODE_2001_CANDIDATES)
        name_col = _find_col(geo, WARD_NAME_CANDIDATES)

        if oa_col and ward_col:
            geo[oa_col] = geo[oa_col].str.strip().str.upper()
            # Filter to Manchester
            lookup = geo[geo[oa_col].str.startswith(MANCHESTER_PREFIX)][
                [oa_col, ward_col] + ([name_col] if name_col else [])
            ].copy()
            lookup = lookup.rename(columns={
                oa_col: "zoneid",
                ward_col: "ward_code_2001",
                **({name_col: "ward_name_2001"} if name_col else {}),
            })
            logger.info(f"  Lookup: {len(lookup)} Manchester OAs mapped")
            return lookup
        else:
            logger.warning(
                f"  Geography lookup columns not found (oa={oa_col}, ward={ward_col})"
            )

    # Fallback: derive ward code from OA prefix
    logger.warning("  Falling back to OA-prefix ward derivation (first 6 chars of OA code)")
    lookup = pd.DataFrame({
        "zoneid": oas["zoneid"],
        "ward_code_2001": oas["zoneid"].str[:6],
        "ward_name_2001": np.nan,
    })
    return lookup


# ─────────────────────────────────────────────────────────────────────────────
# AGGREGATE OA → WARD
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_to_ward(oas: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate 2001 OA indicators to ward level.
    Counts are summed; rates are population-weighted averages.
    """
    logger.info("Aggregating 2001 OAs to ward level…")

    # Attach ward codes
    merged = oas.merge(lookup, on="zoneid", how="left")
    n_unmatched = merged["ward_code_2001"].isna().sum()
    if n_unmatched > 0:
        logger.warning(f"  {n_unmatched} OAs have no ward code – using OA prefix fallback")
        merged.loc[merged["ward_code_2001"].isna(), "ward_code_2001"] = (
            merged.loc[merged["ward_code_2001"].isna(), "zoneid"].str[:6]
        )

    ward_rows = []
    for ward_code, group in merged.groupby("ward_code_2001"):
        row = {"ward_code_2001": ward_code}

        # Ward name (first non-null)
        if "ward_name_2001" in group.columns:
            names = group["ward_name_2001"].dropna()
            row["ward_name_2001"] = names.iloc[0] if len(names) > 0 else np.nan
        else:
            row["ward_name_2001"] = np.nan

        row["oa_count"] = len(group)

        for oa_col, ward_col, agg_type in INDICATORS_TO_AGGREGATE:
            if oa_col not in group.columns:
                row[ward_col] = np.nan
                continue
            if agg_type == "sum":
                row[ward_col] = group[oa_col].sum(min_count=1)
            elif agg_type == "wavg":
                row[ward_col] = weighted_avg(group, oa_col)
            else:
                row[ward_col] = group[oa_col].mean()

        ward_rows.append(row)

    ward_df = pd.DataFrame(ward_rows)
    logger.info(f"  Aggregated to {len(ward_df)} wards")
    return ward_df


# ─────────────────────────────────────────────────────────────────────────────
# MERGE WITH EXISTING TEMPORAL COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

def match_wards(
    existing: pd.DataFrame,
    ward_2001: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join 2001 ward data onto the existing 1981–1991 temporal comparison.

    Matching strategies (in priority order):
    1. Exact zoneid match (unlikely across decades)
    2. Ward suffix match: strip '03BN'/'00BN' prefix and match 2-char suffix
    3. Ward name normalised match
    4. Unmatched 2001 wards appended as new rows
    """
    logger.info("Matching 2001 wards to existing temporal zones…")

    existing = existing.copy()
    ward_2001 = ward_2001.copy()

    # Extract ward suffix (last 2 chars) for fuzzy matching
    existing["_suffix"] = existing["zoneid"].astype(str).str[-2:].str.upper()
    ward_2001["_suffix"] = ward_2001["ward_code_2001"].astype(str).str[-2:].str.upper()

    # Track which 2001 wards have been matched
    matched_ward_codes: set[str] = set()
    match_types: list[str] = []

    cols_2001 = [c for c in ward_2001.columns if c not in ("ward_code_2001", "_suffix")]

    # Initialise 2001 columns in existing df as NaN
    for col in cols_2001:
        existing[col] = np.nan
    existing["GEOGRAPHY_MATCH_TYPE"] = "unmatched"
    existing["WARD_CODE_2001"] = np.nan

    # Strategy 1 & 2: match by suffix
    suffix_map = ward_2001.set_index("_suffix")

    for idx, row in existing.iterrows():
        suffix = row["_suffix"]
        if suffix in suffix_map.index:
            matched_row = suffix_map.loc[suffix]
            # Handle duplicate suffixes (take first match)
            if isinstance(matched_row, pd.DataFrame):
                matched_row = matched_row.iloc[0]
            for col in cols_2001:
                existing.at[idx, col] = matched_row.get(col, np.nan)
            existing.at[idx, "GEOGRAPHY_MATCH_TYPE"] = "code_suffix"
            existing.at[idx, "WARD_CODE_2001"] = matched_row["ward_code_2001"]
            matched_ward_codes.add(matched_row["ward_code_2001"])

    # Strategy 3: ward name matching (if available)
    if "ward_name_2001" in ward_2001.columns and "geography_name" in existing.columns:
        def _norm(s):
            return str(s).lower().strip().replace(" ", "")
        existing["_name_norm"] = existing["geography_name"].apply(_norm)
        ward_2001["_name_norm"] = ward_2001["ward_name_2001"].apply(_norm)
        name_map = ward_2001[~ward_2001["ward_code_2001"].isin(matched_ward_codes)].set_index("_name_norm")

        for idx, row in existing.iterrows():
            if existing.at[idx, "GEOGRAPHY_MATCH_TYPE"] != "unmatched":
                continue
            name_norm = row.get("_name_norm", "")
            if name_norm in name_map.index:
                matched_row = name_map.loc[name_norm]
                if isinstance(matched_row, pd.DataFrame):
                    matched_row = matched_row.iloc[0]
                for col in cols_2001:
                    existing.at[idx, col] = matched_row.get(col, np.nan)
                existing.at[idx, "GEOGRAPHY_MATCH_TYPE"] = "name"
                existing.at[idx, "WARD_CODE_2001"] = matched_row["ward_code_2001"]
                matched_ward_codes.add(matched_row["ward_code_2001"])

    # Append unmatched 2001 wards as new rows
    unmatched_2001 = ward_2001[~ward_2001["ward_code_2001"].isin(matched_ward_codes)]
    if len(unmatched_2001) > 0:
        logger.info(f"  Appending {len(unmatched_2001)} new 2001-only ward rows")
        new_rows = []
        for _, r in unmatched_2001.iterrows():
            new_row = {c: np.nan for c in existing.columns}
            new_row["zoneid"] = r["ward_code_2001"]
            new_row["WARD_CODE_2001"] = r["ward_code_2001"]
            new_row["GEOGRAPHY_MATCH_TYPE"] = "new_2001"
            if "ward_name_2001" in r:
                new_row["geography_name"] = r["ward_name_2001"]
            for col in cols_2001:
                new_row[col] = r.get(col, np.nan)
            new_rows.append(new_row)
        existing = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)

    # Clean up temp columns
    for c in ["_suffix", "_name_norm"]:
        if c in existing.columns:
            existing = existing.drop(columns=[c])

    # Summary stats
    by_type = existing["GEOGRAPHY_MATCH_TYPE"].value_counts()
    logger.info("  Match type breakdown:")
    for mtype, cnt in by_type.items():
        logger.info(f"    {mtype:<20}: {cnt}")

    return existing


# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────

def save_temporal(df: pd.DataFrame) -> None:
    """Save the updated temporal comparison."""
    TEMPORAL_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(TEMPORAL_OUT_FULL, index=False)
    logger.info(f"✓ Full temporal comparison saved: {TEMPORAL_OUT_FULL}")

    # Overwrite legacy filename for backward compatibility
    df.to_csv(TEMPORAL_OUT_COMPAT, index=False)
    logger.info(f"✓ Compatibility file updated: {TEMPORAL_OUT_COMPAT}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 65)
    logger.info("Update Temporal Comparison: Extend to 2001")
    logger.info("=" * 65)

    # ── Load 2001 OA indicators ──────────────────────────────────────────────
    oas_2001 = load_2001_indicators()
    if oas_2001 is None:
        logger.error("Aborting – 2001 indicator file not available.")
        return

    # ── Build OA → ward lookup ───────────────────────────────────────────────
    logger.info("Building OA-to-ward lookup…")
    oa_ward_lookup = build_oa_ward_lookup(oas_2001)

    # ── Aggregate OAs to ward level ──────────────────────────────────────────
    ward_2001 = aggregate_to_ward(oas_2001, oa_ward_lookup)

    # ── Load existing 1981–1991 temporal comparison ──────────────────────────
    if not TEMPORAL_IN.exists():
        logger.error(f"Existing temporal comparison not found: {TEMPORAL_IN}")
        logger.info("Saving 2001 ward aggregates only as standalone file.")
        ward_2001.to_csv(
            TEMPORAL_DIR / "manchester_wards_2001.csv", index=False
        )
        return

    logger.info(f"Loading 1981–1991 temporal comparison: {TEMPORAL_IN}")
    existing = pd.read_csv(TEMPORAL_IN, dtype={"zoneid": str})
    logger.info(f"  {len(existing)} zones, {len(existing.columns)} columns")

    # ── Merge 2001 data in ───────────────────────────────────────────────────
    updated = match_wards(existing, ward_2001)

    # ── Save ─────────────────────────────────────────────────────────────────
    save_temporal(updated)

    # ── Summary ─────────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 65)
    logger.info("SUMMARY")
    logger.info("=" * 65)
    logger.info(f"Zones in output         : {len(updated)}")
    logger.info(f"Columns in output       : {len(updated.columns)}")

    has_2001 = updated["TOTAL_POP_2001"].notna().sum()
    logger.info(f"Zones with 2001 data    : {has_2001}")

    # Cross-decade indicator availability
    logger.info("")
    logger.info("Cross-decade indicator availability:")
    for label, decade_map in CROSS_DECADE_MAP.items():
        avail = {yr: (col and col in updated.columns and updated[col].notna().sum() > 0)
                 for yr, col in decade_map.items()}
        avail_str = "  ".join(f"{yr}={'✓' if ok else '✗'}" for yr, ok in avail.items())
        logger.info(f"  {label:<25} {avail_str}")

    logger.info("")
    logger.info("CAVEAT: PCT_ASIA_BORN_2001 is a PROXY for Chinese origin.")
    logger.info("        Use PCT_CHINESE_ETHNIC_2001 as the primary ethnic indicator.")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
