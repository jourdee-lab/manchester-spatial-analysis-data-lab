#!/usr/bin/env python3
"""
Step 2d: Compute OA-Level Indicators for 2001 Manchester
========================================================

Processes the 2001 combined raw CSV (produced by 03_ingest_2001_oas.py)
and produces a tidy indicators CSV at Output Area level.

Inputs:
  data/processed/aggregates/census_2001/2001_oas_combined_raw.csv

Outputs:
  data/processed/indicators/2001/manchester_oas_2001_indicators.csv

Indicator catalogue
───────────────────
POPULATION
  total_pop              = CS0010001  (all people)

ETHNICITY  [CT003EW]
  chinese_ethnic_count   = CT0030016  (Chinese, all persons)
  chinese_ethnic_pct     = chinese_ethnic_count / total_pop * 100

COUNTRY OF BIRTH  [CS015EW – Asia proxy only]
  asia_born_count        = CS0150049  (born in Asia)
  asia_born_pct          = asia_born_count / total_pop * 100
  NOTE: No China-specific COB at OA level in 2001. asia_born_pct is a
        broad proxy only – includes all Asian birth countries.

ECONOMIC ACTIVITY  [CS028EW, base = all persons 16-74 = CS0280001]
  econ_active_rate       = CS0280002 / CS0280001 * 100
  unemployment_rate      = CS0280005 / CS0280001 * 100
  self_employment_rate   = CS0280004 / CS0280001 * 100

TENURE  [CS049EW, base = total household spaces = CS0490001]
  owner_occ_rate         = CS0490002 / CS0490001 * 100
  council_rent_rate      = CS0490003 / CS0490001 * 100
  private_rent_rate      = CS0490005 / CS0490001 * 100

OVERCROWDING  [CS052EW, base = all household spaces = CS0520001]
  overcrowd_rate         = (CS0520013 + CS0520017) / CS0520001 * 100
  (1.0–1.5 ppr  +  >1.5 ppr  as share of all household spaces)

AMENITIES  [CS056EW, base = CS0560001]
  no_bath_wc_rate        = CS0560021 / CS0560001 * 100

CAR OWNERSHIP  [CS060EW, base = CS0600001]
  no_car_rate            = CS0600005 / CS0600001 * 100

Division-by-zero rule: replace with NaN (never 0).

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

INPUT_PATH = (
    DATA_DIR / "processed" / "aggregates" / "census_2001" / "2001_oas_combined_raw.csv"
)
OUTPUT_DIR = DATA_DIR / "processed" / "indicators" / "2001"
OUTPUT_PATH = OUTPUT_DIR / "manchester_oas_2001_indicators.csv"

MANCHESTER_PREFIX = "00BN"  # 2001 OA prefix for Manchester


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def safe_rate(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """
    Return numerator / denominator * 100.
    Cells where denominator is zero or NaN yield NaN (never 0).
    """
    denom = denominator.replace(0, np.nan)
    return numerator / denom * 100


def get_col(df: pd.DataFrame, code: str) -> pd.Series:
    """
    Return the column matching *code* (case-insensitive).
    Returns a Series of NaN if the column is not present.
    """
    # Try exact match first
    if code in df.columns:
        return df[code]

    # Case-insensitive fallback
    lower_map = {c.lower(): c for c in df.columns}
    if code.lower() in lower_map:
        return df[lower_map[code.lower()]]

    logger.warning(f"  Column not found: {code} – filling with NaN")
    return pd.Series(np.nan, index=df.index, name=code)


# ─────────────────────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────────────────────

def load_combined_raw() -> pd.DataFrame:
    """Load the combined 2001 OA raw CSV produced by the ingestion script."""
    logger.info(f"Loading combined raw CSV: {INPUT_PATH}")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Combined raw file not found: {INPUT_PATH}\n"
            "Run scripts/03_ingest_2001_oas.py first."
        )

    df = pd.read_csv(INPUT_PATH, dtype={"zoneid": str})
    df["zoneid"] = df["zoneid"].str.strip().str.upper()

    # Ensure we only have Manchester OAs
    before = len(df)
    df = df[df["zoneid"].str.startswith(MANCHESTER_PREFIX)].copy()
    logger.info(f"  Loaded {before} rows → {len(df)} Manchester OAs")
    logger.info(f"  Columns: {len(df.columns)}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive the full indicator set for each OA.
    Column codes follow the ONS 2001 cell reference convention:
      CS001EW  → CS0010001  (table code + 4-digit cell number)
      CT003EW  → CT0030016
    """
    logger.info("Computing OA-level indicators…")

    out = pd.DataFrame()
    out["zoneid"] = df["zoneid"]
    out["year"] = 2001

    # ── Ward code: first 6 characters of OA code (00BN + 2-char ward suffix) ──
    out["ward_code"] = df["zoneid"].str[:6]

    # ─────────────────────────────────────────────────────────────────────────
    # POPULATION  [CS001EW]
    # ─────────────────────────────────────────────────────────────────────────
    total_pop = get_col(df, "CS0010001")  # All usual residents
    out["total_pop"] = total_pop

    # ─────────────────────────────────────────────────────────────────────────
    # ETHNICITY  [CT003EW]
    # CT0030016 = Chinese (all persons)
    # ─────────────────────────────────────────────────────────────────────────
    chinese_ethnic = get_col(df, "CT0030016")  # Chinese ethnic group, total persons
    out["chinese_ethnic_count"] = chinese_ethnic
    out["chinese_ethnic_pct"] = safe_rate(chinese_ethnic, total_pop)

    # ─────────────────────────────────────────────────────────────────────────
    # COUNTRY OF BIRTH  [CS015EW]
    # CS0150049 = Born in Asia (broad ONS region)
    # ⚠ PROXY ONLY: includes all Asian birth countries (India, Pakistan, etc.)
    #   No China-specific COB variable available at OA level in 2001 census.
    # ─────────────────────────────────────────────────────────────────────────
    asia_born = get_col(df, "CS0150049")  # Born in Asia – PROXY for China-born
    out["asia_born_count"] = asia_born
    out["asia_born_pct"] = safe_rate(asia_born, total_pop)
    # Flag column so consumers know this is a broad proxy
    out["asia_born_pct_is_proxy"] = True

    # ─────────────────────────────────────────────────────────────────────────
    # ECONOMIC ACTIVITY  [CS028EW]
    # CS0280001 = All persons aged 16-74 (denominator)
    # CS0280002 = Economically active total
    # CS0280004 = Self-employed
    # CS0280005 = Unemployed (ILO definition)
    # ─────────────────────────────────────────────────────────────────────────
    pop_16_74 = get_col(df, "CS0280001")    # All persons 16–74 (base)
    econ_active = get_col(df, "CS0280002")  # Economically active
    self_emp = get_col(df, "CS0280004")     # Self-employed (inc. unpaid family workers)
    unemployed = get_col(df, "CS0280005")   # Unemployed (ILO)

    out["pop_16_74"] = pop_16_74
    out["econ_active_rate"] = safe_rate(econ_active, pop_16_74)
    out["unemployment_rate"] = safe_rate(unemployed, pop_16_74)
    out["self_employment_rate"] = safe_rate(self_emp, pop_16_74)

    # ─────────────────────────────────────────────────────────────────────────
    # TENURE  [CS049EW]
    # CS0490001 = Total household spaces (denominator)
    # CS0490002 = Owner occupied
    # CS0490003 = Rented from council / registered social landlord (council rent)
    # CS0490005 = Private rented
    # ─────────────────────────────────────────────────────────────────────────
    total_hh_spaces = get_col(df, "CS0490001")  # All household spaces
    owner_occ = get_col(df, "CS0490002")         # Owner occupied
    council_rent = get_col(df, "CS0490003")      # Council / RSL rented
    private_rent = get_col(df, "CS0490005")      # Private rented

    out["total_hh_spaces"] = total_hh_spaces
    out["owner_occ_rate"] = safe_rate(owner_occ, total_hh_spaces)
    out["council_rent_rate"] = safe_rate(council_rent, total_hh_spaces)
    out["private_rent_rate"] = safe_rate(private_rent, total_hh_spaces)

    # ─────────────────────────────────────────────────────────────────────────
    # OVERCROWDING  [CS052EW]
    # CS0520001  = All household spaces (denominator)
    # CS0520013  = 1.0–1.5 persons per room
    # CS0520017  = >1.5 persons per room (severe overcrowding)
    # ─────────────────────────────────────────────────────────────────────────
    all_hh_052 = get_col(df, "CS0520001")   # All household spaces (tenure base)
    oc_1_1p5 = get_col(df, "CS0520013")     # 1.0–1.5 ppr
    oc_gt1p5 = get_col(df, "CS0520017")     # >1.5 ppr (severe)

    # Combined overcrowding: moderate + severe as share of all household spaces
    overcrowd_combined = oc_1_1p5.add(oc_gt1p5, fill_value=np.nan)
    out["overcrowd_rate"] = safe_rate(overcrowd_combined, all_hh_052)
    out["overcrowd_severe_rate"] = safe_rate(oc_gt1p5, all_hh_052)

    # ─────────────────────────────────────────────────────────────────────────
    # AMENITIES  [CS056EW]
    # CS0560001 = All household spaces (denominator)
    # CS0560021 = Lacks or shares use of bath/shower and toilet
    # ─────────────────────────────────────────────────────────────────────────
    all_hh_056 = get_col(df, "CS0560001")   # All household spaces
    no_bath_wc = get_col(df, "CS0560021")   # No exclusive bath/shower + toilet

    out["no_bath_wc_rate"] = safe_rate(no_bath_wc, all_hh_056)

    # ─────────────────────────────────────────────────────────────────────────
    # CAR OWNERSHIP  [CS060EW]
    # CS0600001 = All household spaces (denominator)
    # CS0600005 = No car or van (1st category: 0 cars)
    # ─────────────────────────────────────────────────────────────────────────
    all_hh_060 = get_col(df, "CS0600001")  # All household spaces
    no_car = get_col(df, "CS0600005")      # No car or van

    out["no_car_rate"] = safe_rate(no_car, all_hh_060)

    # ─────────────────────────────────────────────────────────────────────────
    # SUMMARY STATS
    # ─────────────────────────────────────────────────────────────────────────
    n_oas = len(out)
    logger.info(f"  Indicator computation complete: {n_oas} OAs")

    rate_cols = [
        c for c in out.columns
        if c.endswith("_rate") or c.endswith("_pct")
    ]
    for col in rate_cols:
        n_null = out[col].isnull().sum()
        col_mean = out[col].mean()
        logger.info(f"  {col:<30} mean={col_mean:6.2f}%  nulls={n_null}")

    return out


# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────

def save_indicators(df: pd.DataFrame) -> None:
    """Save indicators CSV and print final summary."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Round all float columns to 2 decimal places
    float_cols = df.select_dtypes(include="float").columns
    df[float_cols] = df[float_cols].round(2)
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"✓ Indicators saved: {OUTPUT_PATH}")
    logger.info(f"  Shape: {df.shape}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 65)
    logger.info("Phase 8: 2001 OA-Level Indicator Computation")
    logger.info("=" * 65)

    # Load
    raw = load_combined_raw()

    # Compute
    indicators = compute_indicators(raw)

    # Save
    save_indicators(indicators)

    # ── Headline summary ─────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 65)
    logger.info("SUMMARY")
    logger.info("=" * 65)
    logger.info(f"OAs processed           : {len(indicators)}")

    total_pop = indicators["total_pop"].sum()
    chinese_n = indicators["chinese_ethnic_count"].sum()
    if total_pop > 0:
        logger.info(f"Manchester total pop    : {total_pop:,.0f}")
        logger.info(
            f"Chinese ethnic total    : {chinese_n:,.0f} "
            f"({100 * chinese_n / total_pop:.2f}% of total)"
        )

    logger.info("")
    logger.info("Output file:")
    logger.info(f"  {OUTPUT_PATH}")
    logger.info("")
    logger.info("CAVEATS")
    logger.info("  asia_born_pct  is a PROXY – no China-specific COB at OA level in 2001.")
    logger.info("  Use chinese_ethnic_pct (CT003) as the primary ethnic presence indicator.")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
