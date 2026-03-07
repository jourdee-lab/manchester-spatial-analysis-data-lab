"""Step 2b: Compute indicators from 1991 SAS data at both ED and ward level."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from utils import safe_rate

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW  = PROJECT_ROOT / "data" / "raw"
OUT  = PROJECT_ROOT / "data" / "processed" / "indicators" / "1991"

# SAS table config: raw folder, parts, relevant columns
SAS_TABLES = {
    "s02ews": {
        "parts": 4,
        "columns": {"TOTAL_RES": "s020001", "TOTAL_MALE": "s020002", "TOTAL_FEMALE": "s020005"},
    },
    "s06ews": {
        "parts": 4,
        "columns": {
            "TOTAL_ALL_ETHNIC": "s060001",
            "CHINESE_ETHNIC": "s060009",
            "CHINESE_ETHNIC_MALE": "s060021", "CHINESE_ETHNIC_FEMALE": "s060033",
            "CHINESE_AGE_0_4": "s060045", "CHINESE_AGE_5_15": "s060057",
            "CHINESE_AGE_16_29": "s060069", "CHINESE_AGE_30_PENSION": "s060081",
            "CHINESE_PENSIONABLE": "s060093", "CHINESE_LIMITING_ILLNESS": "s060105",
        },
    },
    "s07ews": {
        "parts": 4,
        "columns": {"CHINA_BORN_MALE": "s070041", "CHINA_BORN_FEMALE": "s070042"},
    },
    "s09ews": {
        "parts": 4,
        "columns": {
            "CHINESE_16PLUS": "s090005",
            "CHINESE_ECON_ACTIVE_MALE": "s090017", "CHINESE_UNEMPLOYED_MALE": "s090023",
            "CHINESE_ECON_ACTIVE_FEMALE": "s090041", "CHINESE_UNEMPLOYED_FEMALE": "s090047",
        },
    },
    "s49ews": {
        "parts": 4,
        "columns": {
            "CHINESE_HOUSEHOLDS": "s490005",
            "CHINESE_OVERCROWD_GT1P5": "s490019", "CHINESE_OWNER_OCC": "s490026",
        },
    },
}

# 1991 ward name lookup
WARD_NAMES = {
    "03BNFA": "Ardwick",      "03BNFB": "Baguley",       "03BNFC": "Barlow Moor",
    "03BNFD": "Benchill",     "03BNFE": "Beswick & Clayton", "03BNFF": "Blackley",
    "03BNFG": "Bradford",     "03BNFH": "Brooklands",    "03BNFJ": "Burnage",
    "03BNFK": "Central",      "03BNFL": "Charlestown",   "03BNFM": "Cheetham",
    "03BNFN": "Chorlton",     "03BNFP": "Crumpsall",     "03BNFQ": "Didsbury",
    "03BNFR": "Fallowfield",  "03BNFS": "Gorton North",  "03BNFT": "Gorton South",
    "03BNFU": "Harpurhey",    "03BNFV": "Hulme",         "03BNFW": "Levenshulme",
    "03BNFX": "Lightbowne",   "03BNFY": "Longsight",     "03BNFZ": "Moss Side",
    "03BNGA": "Moston",       "03BNGB": "Newton Heath",  "03BNGC": "Northenden",
    "03BNGD": "Old Moat",     "03BNGE": "Rusholme",      "03BNGF": "Sharston",
    "03BNGG": "Whalley Range","03BNGH": "Withington",    "03BNGJ": "Woodhouse Park",
}

# Load SAS tables
def _load_table(table: str, zone_pattern: str) -> pd.DataFrame:
    """Load all parts of a SAS table, concat, filter by zone_pattern regex."""
    table_dir = RAW / table
    cfg = SAS_TABLES[table]
    dfs = []
    for i in range(1, cfg["parts"] + 1):
        # s16ew files use the s16ew prefix (not s49ews), handle the exceptional case
        raw_prefix = "s49ew" if table == "s49ews" else table
        fp = table_dir / f"{raw_prefix}{i}.csv"
        if fp.exists():
            dfs.append(pd.read_csv(fp))
    if not dfs:
        log.warning("No parts found for %s", table)
        return pd.DataFrame()
    combined = pd.concat(dfs, ignore_index=True)
    combined["zoneid"] = combined["zoneid"].astype(str).str.strip()
    return combined[combined["zoneid"].str.match(zone_pattern)].copy()


def load_all_tables(zone_pattern: str) -> dict[str, pd.DataFrame]:
    """Load all SAS tables filtered to the given zone pattern."""
    return {t: _load_table(t, zone_pattern) for t in SAS_TABLES}


def merge_tables(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge all tables on zoneid using s02ews as the base."""
    base = tables.get("s02ews")
    if base is None or base.empty:
        log.error("No s02ews demographic data – cannot proceed")
        return pd.DataFrame()
    merged = base.copy()
    for table, df in tables.items():
        if table == "s02ews" or df.empty:
            continue
        needed_cols = ["zoneid"] + list(SAS_TABLES[table]["columns"].values())
        available = [c for c in needed_cols if c in df.columns]
        if len(available) > 1:
            merged = merged.merge(
                df[available].drop_duplicates("zoneid"),
                on="zoneid", how="left",
            )
    return merged

# Indicator computation (shared between ED and ward levels)
def compute_indicators_df(df: pd.DataFrame, suffix: str, with_ward_name: bool = False) -> pd.DataFrame:
    """Compute the full 1991 indicator set from a merged SAS dataframe."""
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    rows = []
    for _, r in df.iterrows():
        zone_id = r["zoneid"]
        ind = {"zoneid": zone_id, "year": 1991}
        if with_ward_name:
            ind["ward_name"] = WARD_NAMES.get(zone_id, "Unknown")
            ind["ward_code"] = zone_id[:6] if len(zone_id) >= 6 else zone_id
        else:
            ind["ward_code"] = zone_id[:6] if len(zone_id) >= 6 else zone_id

        total_res = r.get("s020001", np.nan)
        ind[f"TOTAL_RES_{suffix}"]    = total_res
        ind[f"TOTAL_MALE_{suffix}"]   = r.get("s020002", np.nan)
        ind[f"TOTAL_FEMALE_{suffix}"] = r.get("s020005", np.nan)

        chinese = r.get("s060009", np.nan)
        ind[f"CHINESE_ETHNIC_{suffix}"]        = chinese
        ind[f"CHINESE_ETHNIC_MALE_{suffix}"]   = r.get("s060021", np.nan)
        ind[f"CHINESE_ETHNIC_FEMALE_{suffix}"] = r.get("s060033", np.nan)
        ind[f"PCT_CHINESE_ETHNIC_{suffix}"]    = safe_rate(pd.Series([chinese]), pd.Series([total_res])).iloc[0]

        for key, col in [
            (f"CHINESE_AGE_0_4_{suffix}", "s060045"),
            (f"CHINESE_AGE_5_15_{suffix}", "s060057"),
            (f"CHINESE_AGE_16_29_{suffix}", "s060069"),
            (f"CHINESE_AGE_30_PENSION_{suffix}", "s060081"),
            (f"CHINESE_PENSIONABLE_{suffix}", "s060093"),
            (f"CHINESE_LIMITING_ILLNESS_{suffix}", "s060105"),
        ]:
            ind[key] = r.get(col, np.nan)

        china_m = r.get("s070041", np.nan)
        china_f = r.get("s070042", np.nan)
        china_born = (china_m + china_f) if pd.notna(china_m) and pd.notna(china_f) else np.nan
        ind[f"CHINA_BORN_{suffix}"]       = china_born
        ind[f"CHINA_BORN_MALE_{suffix}"]  = china_m
        ind[f"CHINA_BORN_FEMALE_{suffix}"]= china_f
        ind[f"PCT_CHINA_BORN_{suffix}"]   = safe_rate(pd.Series([china_born]), pd.Series([total_res])).iloc[0]

        chinese_16plus = r.get("s090005", np.nan)
        econ_m  = r.get("s090017", np.nan)
        econ_f  = r.get("s090041", np.nan)
        unemp_m = r.get("s090023", np.nan)
        unemp_f = r.get("s090047", np.nan)
        econ_active = (econ_m + econ_f) if pd.notna(econ_m) and pd.notna(econ_f) else np.nan
        unemployed  = (unemp_m + unemp_f) if pd.notna(unemp_m) and pd.notna(unemp_f) else np.nan
        ind[f"CHINESE_16PLUS_{suffix}"]      = chinese_16plus
        ind[f"CHINESE_ECON_ACTIVE_{suffix}"] = econ_active
        ind[f"CHINESE_UNEMPLOYED_{suffix}"]  = unemployed
        ind[f"CHINESE_EMP_RATE_{suffix}"]    = safe_rate(pd.Series([econ_active]), pd.Series([chinese_16plus])).iloc[0]
        ind[f"CHINESE_UNEMP_RATE_{suffix}"]  = safe_rate(pd.Series([unemployed]),  pd.Series([chinese_16plus])).iloc[0]

        chinese_hh = r.get("s490005", np.nan)
        overcrowd  = r.get("s490019", np.nan)
        owner_occ  = r.get("s490026", np.nan)
        ind[f"CHINESE_HOUSEHOLDS_{suffix}"]      = chinese_hh
        ind[f"CHINESE_OVERCROWD_GT1P5_{suffix}"] = overcrowd
        ind[f"CHINESE_OWNER_OCC_{suffix}"]       = owner_occ
        ind[f"PCT_CHINESE_OVERCROWD_{suffix}"]   = safe_rate(pd.Series([overcrowd]), pd.Series([chinese_hh])).iloc[0]
        ind[f"PCT_CHINESE_OWNER_OCC_{suffix}"]   = safe_rate(pd.Series([owner_occ]), pd.Series([chinese_hh])).iloc[0]

        rows.append(ind)
    return pd.DataFrame(rows)

# Main
def main() -> None:
    log.info("=== Step 2b: Compute 1991 indicators (ED and ward level) ===")
    OUT.mkdir(parents=True, exist_ok=True)

    # ED level (8-char codes: 03BN + 2-letter ward + 2-digit ED)
    log.info("--- ED level ---")
    ed_tables = load_all_tables(r"^03BN[A-Z]{2}[0-9]{2}$")
    ed_merged  = merge_tables(ed_tables)
    if not ed_merged.empty:
        ed_indicators = compute_indicators_df(ed_merged, "1991", with_ward_name=False)
        out_ed = OUT / "manchester_eds_1991_indicators.csv"
        ed_indicators.to_csv(out_ed, index=False)
        log.info("Saved %d EDs -> %s", len(ed_indicators), out_ed)

    # Ward level (6-char codes: 03BN + 2-letter ward)
    log.info("--- Ward level ---")
    ward_tables = load_all_tables(r"^03BN[A-Z]{2}$")
    ward_merged  = merge_tables(ward_tables)
    if not ward_merged.empty:
        ward_indicators = compute_indicators_df(ward_merged, "1991", with_ward_name=True)
        out_ward = OUT / "manchester_wards_1991_indicators.csv"
        ward_indicators.to_csv(out_ward, index=False)
        log.info("Saved %d wards -> %s", len(ward_indicators), out_ward)

        # District summary (aggregate ward counts; recompute rates)
        sum_cols  = [c for c in ward_indicators.columns if c.endswith("_1991") and not c.startswith("PCT_") and c not in ("CHINESE_EMP_RATE_1991", "CHINESE_UNEMP_RATE_1991")]
        district  = ward_indicators[sum_cols].sum().to_dict()
        district["zoneid"] = "03BN"
        district["ward_name"] = "Manchester (District)"
        total_res = district.get("TOTAL_RES_1991", 0)
        if total_res > 0:
            district["PCT_CHINESE_ETHNIC_1991"] = 100 * district.get("CHINESE_ETHNIC_1991", 0) / total_res
            district["PCT_CHINA_BORN_1991"]     = 100 * district.get("CHINA_BORN_1991", 0) / total_res
        chinese_16plus = district.get("CHINESE_16PLUS_1991", 0)
        if chinese_16plus > 0:
            district["CHINESE_EMP_RATE_1991"]  = 100 * district.get("CHINESE_ECON_ACTIVE_1991", 0) / chinese_16plus
            district["CHINESE_UNEMP_RATE_1991"] = 100 * district.get("CHINESE_UNEMPLOYED_1991", 0) / chinese_16plus
        pd.DataFrame([district]).to_csv(OUT / "manchester_district_1991_indicators.csv", index=False)
        log.info("District summary saved")

    log.info("=== 1991 indicator computation complete ===")


if __name__ == "__main__":
    main()
