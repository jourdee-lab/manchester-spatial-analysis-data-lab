"""Step 2a: Compute indicators from 1981 ED-level SAS data using YAML config."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import yaml # type: ignore

import math

from utils import get_col, safe_rate

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ED_DIR    = PROJECT_ROOT / "data" / "processed" / "raw_ed_level" / "1981"
OUT_CSV   = PROJECT_ROOT / "data" / "processed" / "indicators" / "1981" / "manchester_eds_1981_indicators.csv"
OUT_META  = PROJECT_ROOT / "docs" / "indicator_documentation" / "1981" / "indicators_1981_metadata.json"
OUT_SUMM  = PROJECT_ROOT / "docs" / "indicator_documentation" / "1981" / "indicators_1981_summary.json"
CONFIG    = PROJECT_ROOT / "configs" / "indicators.yml"
YEAR      = 1981
ID_COL    = "zoneid"


def load_ed_data() -> pd.DataFrame:
    """Merge the four 1981 SAS ED-level CSVs on zoneid."""
    tables = sorted(ED_DIR.glob("sas*_1981_ed_level.csv"))
    if not tables:
        raise FileNotFoundError(f"No ED-level CSVs found in {ED_DIR}")
    merged = pd.read_csv(tables[0])
    for t in tables[1:]:
        df = pd.read_csv(t)
        extra = [c for c in df.columns if c != ID_COL]
        merged = merged.merge(df[[ID_COL] + extra], on=ID_COL, how="inner")
    log.info("Loaded %d EDs x %d cols", len(merged), len(merged.columns))
    return merged


def compute_indicator(
    df: pd.DataFrame,
    name: str,
    cfg: Dict,
    cache: Dict[str, pd.Series],
) -> Tuple[pd.Series, Dict]:
    """Compute a single indicator; return (series, metadata)."""
    ind_type   = cfg.get("type", "raw")
    sas_code   = cfg.get("code")
    denom_name = cfg.get("denominator")
    calc       = cfg.get("calculation", "")
    meta = {"name": name, "type": ind_type, "sas_code": sas_code,
            "description": cfg.get("description", ""), "status": "OK"}

    try:
        if ind_type in ("raw", "denominator"):
            col = get_col(df, sas_code) if sas_code else None
            if col is None or (col.isna().all() and sas_code not in df.columns
                               and sas_code.lower() not in {c.lower() for c in df.columns}): # type: ignore
                meta["status"] = "SAS_CODE_NOT_FOUND"
                return pd.Series(np.nan, index=df.index, name=name), meta
            s = col.astype(float)

        elif ind_type == "rate":
            if " - " in (calc or ""):
                ref = calc.split(" - ")[1].strip()
                base = float(calc.split(" - ")[0].strip())
                s = base - cache.get(ref, pd.Series(np.nan, index=df.index))
            elif denom_name and denom_name in cache:
                num = get_col(df, sas_code).astype(float) if sas_code else pd.Series(np.nan, index=df.index)
                s = safe_rate(num, cache[denom_name])
            else:
                meta["status"] = "MISSING_DENOMINATOR"
                return pd.Series(np.nan, index=df.index, name=name), meta
        else:
            meta["status"] = "UNKNOWN_TYPE"
            return pd.Series(np.nan, index=df.index, name=name), meta

    except Exception as exc:
        meta["status"] = f"ERROR: {exc}"
        return pd.Series(np.nan, index=df.index, name=name), meta

    s.name = name
    meta["non_null_count"] = int(s.notna().sum())
    meta["mean"] = float(s.mean()) if s.notna().any() else None
    return s, meta


def compute_all(df: pd.DataFrame, year_cfg: Dict) -> Tuple[pd.DataFrame, Dict]:
    """Two-pass computation: raw counts first, then derived rates."""
    indicators = pd.DataFrame({ID_COL: df[ID_COL]})
    cache: Dict[str, pd.Series] = {}
    metadata: Dict = {}

    for ind_type_filter in (("raw", "denominator"), ("rate",)):
        for name, cfg in year_cfg.items():
            if cfg.get("type", "raw") not in ind_type_filter or name in metadata:
                continue
            s, meta = compute_indicator(df, name, cfg, cache)
            indicators[name] = s
            cache[name] = s
            metadata[name] = meta

    log.info("Computed %d indicators", len(metadata))
    return indicators, metadata


def main() -> None:
    log.info("=== Step 2a: Compute 1981 indicators ===")
    with open(CONFIG) as f:
        config = yaml.safe_load(f)
    year_cfg = config["years"].get(YEAR)
    if not year_cfg:
        log.error("No config for year %d", YEAR)
        return

    df = load_ed_data()
    indicators, metadata = compute_all(df, year_cfg)

    summary = {
        "year": YEAR, "ed_count": len(indicators),
        "indicators_count": len(metadata),
        "produced_at": datetime.now().isoformat(),
    }

    for path in (OUT_CSV, OUT_META, OUT_SUMM):
        path.parent.mkdir(parents=True, exist_ok=True)
    def _json_safe(obj):
        if isinstance(obj, float) and math.isnan(obj):
            return None
        raise TypeError(repr(obj))

    indicators.to_csv(OUT_CSV, index=False)
    with open(OUT_META, "w") as f:
        json.dump(metadata, f, indent=2, default=_json_safe)
    with open(OUT_SUMM, "w") as f:
        json.dump(summary, f, indent=2, default=_json_safe)

    log.info("Saved %d EDs x %d indicators -> %s", len(indicators), len(metadata), OUT_CSV)
    ok = sum(1 for m in metadata.values() if m["status"] == "OK")
    log.info("Status: %d OK / %d total", ok, len(metadata))


if __name__ == "__main__":
    main()
