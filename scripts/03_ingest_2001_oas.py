#!/usr/bin/env python3
"""
Step 1c: Ingest Raw Census 2001 OA-Level Data
=============================================

Loads the 2001 census CSV files (one per topic table), filters to Manchester
Output Areas (OA codes starting with '00BN'), pivots each file to wide format
(one row per OA, variable codes as columns), merges all tables on 'zoneid'
and saves a single combined CSV.

Input files (data/raw/):
  c01cs001_ons.csv  → CS001EW  Total population
  c01ct003_ons.csv  → CT003EW  Ethnic group inc. Chinese
  c01cs015_ons.csv  → CS015EW  Country of birth – Asia proxy
  c01cs028_ons.csv  → CS028EW  Economic activity (16-74)
  c01cs049_ons.csv  → CS049EW  Tenure
  c01cs052_ons.csv  → CS052EW  Persons per room / overcrowding
  c01cs056_ons.csv  → CS056EW  Amenities (bath/WC)
  c01cs060_ons.csv  → CS060EW  Car ownership

Lookups (data/lookups/):
  2001_geography_lookup_england.csv
  2001_variable_lookup_ew.csv
  2001_table_code_and_names_ukcas_map.csv

Output:
  data/processed/aggregates/census_2001/2001_oas_combined_raw.csv

Manchester filter: zoneid.str.startswith("00BN")

Note on 2001 data format:
  Each c01c*.csv file is typically in long format:
    zoneid | variable | value
  (or equivalent column names from the ONS dissemination files).
  If files are already wide (zoneid | var1 | var2 ...) the pivot step is
  skipped automatically.

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
RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOOKUP_DIR = PROJECT_ROOT / "data" / "lookups"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "aggregates" / "census_2001"

MANCHESTER_PREFIX = "00BN"  # 2001 Output Area prefix for Manchester

# Mapping of raw filename → expected table label (for logging only)
RAW_FILES = {
    "c01cs001_ons.csv": "CS001EW – Total population",
    "c01ct003_ons.csv": "CT003EW – Ethnic group",
    "c01cs015_ons.csv": "CS015EW – Country of birth (Asia proxy)",
    "c01cs028_ons.csv": "CS028EW – Economic activity",
    "c01cs049_ons.csv": "CS049EW – Tenure",
    "c01cs052_ons.csv": "CS052EW – Persons per room",
    "c01cs056_ons.csv": "CS056EW – Amenities",
    "c01cs060_ons.csv": "CS060EW – Car ownership",
}

# Possible column names used for the zone identifier across ONS file variants
# zone_code is the actual column name used in the ONS 2001 dissemination CSVs
ZONEID_CANDIDATES = ["zone_code", "ZONE_CODE", "zoneid", "ZONEID", "oa_code",
                     "OA_CODE", "geo_code", "GEO_CODE", "zone_id", "ZONE_ID",
                     "Zone Code", "GEO"]

# OA codes are exactly 10 characters (e.g. 00BNFA0001).
# The files also contain district (4 chars) and ward (6 chars) aggregate rows
# which must be excluded so each row represents exactly one Output Area.
OA_CODE_LENGTH = 10

# Possible column names for the variable code in long-format files
VARCODE_CANDIDATES = ["variable", "VARIABLE", "var_code", "VAR_CODE",
                      "cell", "CELL", "varname", "VARNAME", "Variable Code",
                      "varcode"]

# Possible column names for the cell value
VALUE_CANDIDATES = ["value", "VALUE", "count", "COUNT", "obs_value",
                    "OBS_VALUE"]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, candidates: list[str], label: str) -> str | None:
    """Return the first candidate column name that exists in *df*, else None."""
    for c in candidates:
        if c in df.columns:
            return c
    logger.warning(f"  Could not find {label} column. Tried: {candidates}")
    logger.warning(f"  Available columns: {list(df.columns)[:20]}")
    return None


def _normalise_zoneid(series: pd.Series) -> pd.Series:
    """Strip whitespace, uppercase, and return consistent zone IDs."""
    return series.astype(str).str.strip().str.upper()


def load_and_pivot(file_path: Path, label: str) -> pd.DataFrame | None:
    """
    Load a single raw ONS CSV and return a wide-format DataFrame
    (one row per OA, variable codes as columns), filtered to Manchester.

    Handles both:
      - Long format: zoneid | variable | value
      - Wide format: zoneid | var1 | var2 | ...

    Returns None if the file cannot be processed.
    """
    logger.info(f"  Loading: {file_path.name}  [{label}]")

    if not file_path.exists():
        logger.warning(f"    FILE NOT FOUND: {file_path}")
        return None

    try:
        df = pd.read_csv(file_path, dtype=str)
    except Exception as exc:
        logger.error(f"    Cannot read {file_path.name}: {exc}")
        return None

    logger.info(f"    Raw shape: {df.shape}  columns: {list(df.columns)[:8]}...")

    # ── Identify zone ID column ──────────────────────────────────────────────
    zoneid_col = _find_col(df, ZONEID_CANDIDATES, "zoneid")
    if zoneid_col is None:
        return None

    df[zoneid_col] = _normalise_zoneid(df[zoneid_col])

    # ── Filter to Manchester OAs (exactly OA_CODE_LENGTH chars) ──────────────
    # Rows with fewer characters are district/ward aggregates; exclude them.
    manchester_mask = (
        df[zoneid_col].str.startswith(MANCHESTER_PREFIX) &
        (df[zoneid_col].str.len() == OA_CODE_LENGTH)
    )
    df = df[manchester_mask].copy()
    logger.info(f"    Manchester OAs after filter: {len(df)}")

    if df.empty:
        logger.warning(f"    No Manchester OAs found in {file_path.name}!")
        return None

    # ── Detect long vs wide format ───────────────────────────────────────────
    varcode_col = _find_col(df, VARCODE_CANDIDATES, "variable-code")
    value_col = _find_col(df, VALUE_CANDIDATES, "value")

    if varcode_col is not None and value_col is not None:
        # ── LONG format → pivot to wide ──────────────────────────────────────
        logger.info(f"    Detected LONG format. Pivoting on '{varcode_col}'.")
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

        wide = (
            df.pivot_table(
                index=zoneid_col,
                columns=varcode_col,
                values=value_col,
                aggfunc="first",
            )
            .reset_index()
            .rename(columns={zoneid_col: "zoneid"})
        )
        # Flatten column index if MultiIndex
        wide.columns = [str(c).strip() for c in wide.columns]
    else:
        # ── WIDE format – use as-is ───────────────────────────────────────────
        logger.info(f"    Detected WIDE format. Using as-is.")
        df = df.rename(columns={zoneid_col: "zoneid"})
        # Convert all non-ID columns to numeric
        non_id_cols = [c for c in df.columns if c != "zoneid"]
        df[non_id_cols] = df[non_id_cols].apply(pd.to_numeric, errors="coerce")
        wide = df

    logger.info(f"    Wide shape after pivot: {wide.shape}")
    return wide


def validate_table(df: pd.DataFrame, label: str, expected_min_rows: int = 10) -> bool:
    """
    Basic validation checks on a processed table.
    Returns True if the table passes, False otherwise.
    """
    ok = True
    if len(df) < expected_min_rows:
        logger.warning(f"  [{label}] Only {len(df)} rows – expected ≥ {expected_min_rows}")
        ok = False

    dup_ids = df["zoneid"].duplicated().sum()
    if dup_ids > 0:
        logger.warning(f"  [{label}] {dup_ids} duplicate zone IDs (will dedup on merge)")
        ok = False

    return ok


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 65)
    logger.info("2001 OA-Level Census Ingestion")
    logger.info("=" * 65)

    tables: dict[str, pd.DataFrame] = {}
    missing_files: list[str] = []

    # ── Load each raw file ───────────────────────────────────────────────────
    for filename, label in RAW_FILES.items():
        file_path = RAW_DIR / filename
        wide_df = load_and_pivot(file_path, label)

        if wide_df is None:
            missing_files.append(filename)
            continue

        validate_table(wide_df, label)
        tables[filename] = wide_df

    if not tables:
        logger.error("No tables loaded – check data/raw/ for c01c*.csv files.")
        return

    # ── Merge all tables on 'zoneid' ─────────────────────────────────────────
    logger.info("")
    logger.info("Merging tables on zoneid…")

    # Start from the first successfully loaded table
    first_key = next(iter(tables))
    combined = tables[first_key].drop_duplicates(subset=["zoneid"])

    for fname, df in tables.items():
        if fname == first_key:
            continue
        deduped = df.drop_duplicates(subset=["zoneid"])
        # Identify overlapping non-ID columns and suffix them to avoid clash
        overlap_cols = set(combined.columns) & set(deduped.columns) - {"zoneid"}
        if overlap_cols:
            logger.warning(f"  Overlapping columns with {fname}: {overlap_cols} – suffixing")
        combined = combined.merge(deduped, on="zoneid", how="outer", suffixes=("", f"__{fname[:8]}"))
        logger.info(f"  Merged {fname}: cumulative shape {combined.shape}")

    # ── Final validation ─────────────────────────────────────────────────────
    combined["zoneid"] = _normalise_zoneid(combined["zoneid"])
    combined = combined.sort_values("zoneid").reset_index(drop=True)

    oa_count = len(combined)
    col_count = len(combined.columns)
    missing_any = combined.isnull().any(axis=1).sum()

    logger.info("")
    logger.info("Final combined dataset:")
    logger.info(f"  Rows (OAs)     : {oa_count}")
    logger.info(f"  Columns (vars) : {col_count}")
    logger.info(f"  OAs with ≥1 NaN: {missing_any}")

    # ── Save ─────────────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "2001_oas_combined_raw.csv"
    combined.to_csv(out_path, index=False)
    logger.info(f"  ✓ Saved: {out_path}")

    # ── Column inventory ─────────────────────────────────────────────────────
    logger.info("")
    logger.info("Column inventory (first 60):")
    for col in list(combined.columns)[:60]:
        n_null = combined[col].isnull().sum()
        logger.info(f"    {col:<30}  nulls={n_null}")

    # ── Report missing files ─────────────────────────────────────────────────
    if missing_files:
        logger.warning("")
        logger.warning("Files NOT found or failed to load:")
        for mf in missing_files:
            logger.warning(f"  ✗ {mf}")

    # ── Cross-check against geography lookup ────────────────────────────────
    geo_lookup = LOOKUP_DIR / "2001_geography_lookup_england.csv"
    if geo_lookup.exists():
        try:
            geo_df = pd.read_csv(geo_lookup, dtype=str)
            geo_zone_col = _find_col(geo_df, ZONEID_CANDIDATES, "zoneid")
            if geo_zone_col:
                geo_df[geo_zone_col] = _normalise_zoneid(geo_df[geo_zone_col])
                expected_oas = geo_df[
                    geo_df[geo_zone_col].str.startswith(MANCHESTER_PREFIX)
                ]
                expected_n = len(expected_oas)
                logger.info("")
                logger.info(f"Geography lookup check: {expected_n} Manchester OAs expected")
                logger.info(f"  Loaded in combined CSV: {oa_count}")
                if oa_count < expected_n:
                    logger.warning(f"  ⚠ {expected_n - oa_count} OAs may be missing!")
        except Exception as exc:
            logger.warning(f"  Could not cross-check geography lookup: {exc}")

    logger.info("")
    logger.info("=" * 65)
    logger.info("Ingestion complete.")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
