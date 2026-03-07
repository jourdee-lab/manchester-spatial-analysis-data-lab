"""Step 2c: Compute OA-level indicators from the 2001 combined raw CSV."""

from __future__ import annotations

import logging
from pathlib import Path
import numpy as np
import pandas as pd
from utils import safe_rate, get_col

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "aggregates" / "census_2001" / "2001_oas_combined_raw.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "indicators" / "2001"
OUTPUT_PATH = OUTPUT_DIR / "manchester_oas_2001_indicators.csv"
MANCHESTER_PREFIX = "00BN"


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the full 2001 OA indicator set from the combined raw CSV."""
    out = pd.DataFrame()
    out["zoneid"]    = df["zoneid"]
    out["year"]      = 2001
    out["ward_code"] = df["zoneid"].str[:6]

    # Population [CS001EW]
    total_pop = get_col(df, "CS0010001")
    out["total_pop"] = total_pop

    # Ethnicity [CT003EW] – Chinese (all persons)
    chinese_ethnic = get_col(df, "CT0030016")
    out["chinese_ethnic_count"] = chinese_ethnic
    out["chinese_ethnic_pct"]   = safe_rate(chinese_ethnic, total_pop)

    # Country of birth [CS015EW] – born in Asia (broad proxy; no OA-level China-specific COB in 2001)
    asia_born = get_col(df, "CS0150049")
    out["asia_born_count"]      = asia_born
    out["asia_born_pct"]        = safe_rate(asia_born, total_pop)
    out["asia_born_pct_is_proxy"] = True  # flag for consumers

    # Economic activity [CS028EW] – base = all persons aged 16-74
    pop_16_74   = get_col(df, "CS0280001")
    econ_active = get_col(df, "CS0280002")
    self_emp    = get_col(df, "CS0280004")
    unemployed  = get_col(df, "CS0280005")
    out["pop_16_74"]           = pop_16_74
    out["econ_active_rate"]    = safe_rate(econ_active, pop_16_74)
    out["unemployment_rate"]   = safe_rate(unemployed,  pop_16_74)
    out["self_employment_rate"]= safe_rate(self_emp,    pop_16_74)

    # Tenure [CS049EW] – base = total household spaces
    total_hh    = get_col(df, "CS0490001")
    owner_occ   = get_col(df, "CS0490002")
    council_rent= get_col(df, "CS0490003")
    private_rent= get_col(df, "CS0490005")
    out["total_hh_spaces"]    = total_hh
    out["owner_occ_rate"]     = safe_rate(owner_occ,    total_hh)
    out["council_rent_rate"]  = safe_rate(council_rent, total_hh)
    out["private_rent_rate"]  = safe_rate(private_rent, total_hh)

    # Overcrowding [CS052EW] – 1.0-1.5 ppr + >1.5 ppr as share of all household spaces
    all_hh_052 = get_col(df, "CS0520001")
    oc_1_1p5   = get_col(df, "CS0520013")
    oc_gt1p5   = get_col(df, "CS0520017")
    out["overcrowd_rate"]        = safe_rate(oc_1_1p5.add(oc_gt1p5, fill_value=np.nan), all_hh_052)
    out["overcrowd_severe_rate"] = safe_rate(oc_gt1p5, all_hh_052)

    # Amenities [CS056EW] – lacks or shares bath/shower and toilet
    all_hh_056 = get_col(df, "CS0560001")
    no_bath_wc = get_col(df, "CS0560021")
    out["no_bath_wc_rate"] = safe_rate(no_bath_wc, all_hh_056)

    # Car ownership [CS060EW] – no car or van
    all_hh_060 = get_col(df, "CS0600001")
    no_car     = get_col(df, "CS0600005")
    out["no_car_rate"] = safe_rate(no_car, all_hh_060)

    log.info("Computed %d OA indicator rows", len(out))
    return out


def main() -> None:
    log.info("=== Step 2c: Compute 2001 OA indicators ===")
    if not INPUT_PATH.exists():
        log.error("Input not found: %s  (run 01_ingest.py first)", INPUT_PATH)
        return

    df = pd.read_csv(INPUT_PATH, dtype={"zoneid": str})
    df["zoneid"] = df["zoneid"].str.strip().str.upper()
    df = df[df["zoneid"].str.startswith(MANCHESTER_PREFIX)].copy()
    log.info("Loaded %d Manchester OAs", len(df))

    indicators = compute_indicators(df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    float_cols = indicators.select_dtypes(include="float").columns
    indicators[float_cols] = indicators[float_cols].round(2)
    indicators.to_csv(OUTPUT_PATH, index=False)
    log.info("Saved %s  (%d rows x %d cols)", OUTPUT_PATH, *indicators.shape)

    total_pop   = indicators["total_pop"].sum()
    chinese_n   = indicators["chinese_ethnic_count"].sum()
    log.info("Manchester total pop: %,.0f  |  Chinese ethnic: %,.0f (%.2f%%)",
             total_pop, chinese_n, 100 * chinese_n / total_pop if total_pop else 0)
    log.info("NOTE: asia_born_pct is a broad proxy; use chinese_ethnic_pct as primary indicator")


if __name__ == "__main__":
    main()
