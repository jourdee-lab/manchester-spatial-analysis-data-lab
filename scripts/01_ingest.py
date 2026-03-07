"""Step 1: Ingest raw SAS census data for 1981 EDs, 1991 EDs, and 2001 OAs."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from utils import normalise_zoneid, get_col

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW = PROJECT_ROOT / "data" / "raw"
OUT = PROJECT_ROOT / "data" / "processed"

MANCHESTER_1981 = "03BN"   # 1981/1991 ED prefix
MANCHESTER_1991 = "03BN"
MANCHESTER_2001 = "00BN"   # 2001 OA prefix; codes are exactly 10 characters

# ---------------------------------------------------------------------------
# 1981 – five-part SAS tables
# ---------------------------------------------------------------------------

SAS_1981 = {
    "sas02": {"parts": 5, "description": "Demographics"},
    "sas04": {"parts": 5, "description": "Country of Birth"},
    "sas07": {"parts": 5, "description": "Employment"},
    "sas10": {"parts": 5, "description": "Housing & Tenure"},
}


def ingest_1981() -> None:
    """Load five-part SAS CSVs, merge on zoneid, filter to Manchester, save."""
    raw_dir = RAW / "sas"
    out_dir = OUT / "raw_ed_level" / "1981"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not raw_dir.exists():
        log.error("1981 raw directory not found: %s", raw_dir)
        return

    for table, cfg in SAS_1981.items():
        log.info("1981 %s (%s): loading %d parts", table, cfg["description"], cfg["parts"])
        parts = []
        for i in range(1, cfg["parts"] + 1):
            fp = raw_dir / f"1981_{table}_part{i}.csv"
            if not fp.exists():
                log.warning("  Missing: %s", fp)
                break
            parts.append(pd.read_csv(fp))

        if len(parts) != cfg["parts"]:
            log.error("  Incomplete parts for %s – skipping", table)
            continue

        merged = parts[0]
        for i, df in enumerate(parts[1:], 2):
            merged = merged.merge(df, on="zoneid", how="inner")

        merged["zoneid"] = normalise_zoneid(merged["zoneid"])
        out = merged[merged["zoneid"].str.startswith(MANCHESTER_1981)].copy()
        out_path = out_dir / f"{table}_1981_ed_level.csv"
        out.to_csv(out_path, index=False)
        log.info("  Saved %d EDs x %d cols -> %s", len(out), len(out.columns), out_path)


# ---------------------------------------------------------------------------
# 1991 – four-part SAS tables
# ---------------------------------------------------------------------------

SAS_1991 = {
    "sas02": {"raw_prefix": "s02ews", "parts": 4, "description": "Demographics"},
    "sas06": {"raw_prefix": "s06ews", "parts": 4, "description": "Ethnic Group"},
    "sas07": {"raw_prefix": "s07ews", "parts": 4, "description": "Country of Birth"},
    "sas09": {"raw_prefix": "s09ews", "parts": 4, "description": "Economic Position"},
    "sas20": {"raw_prefix": "s16ew",  "parts": 4, "description": "Tenure & Amenities"},
    "sas81": {"raw_prefix": "s81ews", "parts": 4, "description": "Communal Establishments"},
}


def ingest_1991() -> None:
    """Load four-part 1991 SAS CSVs, merge on zoneid, filter to Manchester, save."""
    out_dir = OUT / "raw_ed_level" / "1991"
    out_dir.mkdir(parents=True, exist_ok=True)

    for table, cfg in SAS_1991.items():
        prefix = cfg["raw_prefix"]
        table_dir = RAW / prefix
        log.info("1991 %s (%s): loading %d parts from %s/", table, cfg["description"], cfg["parts"], prefix)

        parts = []
        for i in range(1, cfg["parts"] + 1):
            fp = table_dir / f"{prefix}{i}.csv"
            if not fp.exists():
                log.warning("  Missing: %s", fp)
                break
            parts.append(pd.read_csv(fp))

        if len(parts) != cfg["parts"]:
            log.error("  Incomplete parts for %s – skipping", table)
            continue

        merged = parts[0]
        for i, df in enumerate(parts[1:], 2):
            merged = merged.merge(df, on="zoneid", how="inner")

        merged["zoneid"] = normalise_zoneid(merged["zoneid"])
        out = merged[merged["zoneid"].str.startswith(MANCHESTER_1991)].copy()
        out_path = out_dir / f"{table}_1991_ed_level.csv"
        out.to_csv(out_path, index=False)
        log.info("  Saved %d EDs x %d cols -> %s", len(out), len(out.columns), out_path)


# ---------------------------------------------------------------------------
# 2001 – wide/long ONS topic tables
# ---------------------------------------------------------------------------

RAW_FILES_2001 = {
    "c01cs001_ons.csv": "CS001EW – Total population",
    "c01ct003_ons.csv": "CT003EW – Ethnic group",
    "c01cs015_ons.csv": "CS015EW – Country of birth",
    "c01cs028_ons.csv": "CS028EW – Economic activity",
    "c01cs049_ons.csv": "CS049EW – Tenure",
    "c01cs052_ons.csv": "CS052EW – Persons per room",
    "c01cs056_ons.csv": "CS056EW – Amenities",
    "c01cs060_ons.csv": "CS060EW – Car ownership",
}

_ZONEID_CANDIDATES = ["zone_code", "ZONE_CODE", "zoneid", "ZONEID", "oa_code",
                      "OA_CODE", "geo_code", "GEO_CODE", "zone_id", "GEO"]
_VARCODE_CANDIDATES = ["variable", "VARIABLE", "var_code", "VAR_CODE", "cell",
                       "varname", "varcode", "Variable Code"]
_VALUE_CANDIDATES   = ["value", "VALUE", "count", "COUNT", "obs_value", "OBS_VALUE"]


def _load_and_pivot_2001(fp: Path, label: str) -> pd.DataFrame | None:
    """Load one 2001 ONS file and return wide format filtered to Manchester OAs."""
    if not fp.exists():
        log.warning("Not found: %s", fp)
        return None
    df = pd.read_csv(fp, dtype=str)
    zoneid_col = next((c for c in _ZONEID_CANDIDATES if c in df.columns), None)
    if zoneid_col is None:
        log.warning("No zone-id column in %s", fp.name)
        return None
    df[zoneid_col] = normalise_zoneid(df[zoneid_col])
    # Keep only proper OA rows (exactly 10 chars starting with Manchester prefix)
    mask = df[zoneid_col].str.startswith(MANCHESTER_2001) & (df[zoneid_col].str.len() == 10)
    df = df[mask].copy()
    if df.empty:
        log.warning("No Manchester OAs in %s", fp.name)
        return None
    varcode_col = next((c for c in _VARCODE_CANDIDATES if c in df.columns), None)
    value_col   = next((c for c in _VALUE_CANDIDATES   if c in df.columns), None)
    if varcode_col and value_col:
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        wide = (df.pivot_table(index=zoneid_col, columns=varcode_col,
                               values=value_col, aggfunc="first")
                  .reset_index()
                  .rename(columns={zoneid_col: "zoneid"}))
        wide.columns = [str(c).strip() for c in wide.columns]
    else:
        non_id = [c for c in df.columns if c != zoneid_col]
        df[non_id] = df[non_id].apply(pd.to_numeric, errors="coerce")
        wide = df.rename(columns={zoneid_col: "zoneid"})
    log.info("  %s: %d OAs x %d cols", label, len(wide), len(wide.columns))
    return wide


def ingest_2001() -> None:
    """Load 2001 ONS CSV tables, merge on zoneid, save combined raw CSV."""
    out_dir = OUT / "aggregates" / "census_2001"
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = {}
    for fname, label in RAW_FILES_2001.items():
        wide = _load_and_pivot_2001(RAW / fname, label)
        if wide is not None:
            tables[fname] = wide.drop_duplicates(subset=["zoneid"])

    if not tables:
        log.error("No 2001 tables loaded – check data/raw/ for c01c*.csv files")
        return

    combined = next(iter(tables.values()))
    for fname, df in list(tables.items())[1:]:
        combined = combined.merge(df, on="zoneid", how="outer")
    combined["zoneid"] = normalise_zoneid(combined["zoneid"])
    combined = combined.sort_values("zoneid").reset_index(drop=True)

    out_path = out_dir / "2001_oas_combined_raw.csv"
    combined.to_csv(out_path, index=False)
    log.info("2001 combined: %d OAs x %d cols -> %s", len(combined), len(combined.columns), out_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("=== Step 1: Ingest raw census data (1981 / 1991 / 2001) ===")
    log.info("--- 1981 ---")
    ingest_1981()
    log.info("--- 1991 ---")
    ingest_1991()
    log.info("--- 2001 ---")
    ingest_2001()
    log.info("=== Ingestion complete ===")


if __name__ == "__main__":
    main()
