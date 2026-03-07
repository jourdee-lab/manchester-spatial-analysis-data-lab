"""Step 3: Join indicator CSVs to their respective boundary files (1981, 1991, 2001)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd
from utils import normalise_zoneid, save_gpkg

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BND  = PROJECT_ROOT / "gis_boundaries"
IND  = PROJECT_ROOT / "data" / "processed" / "indicators"
SPAT = PROJECT_ROOT / "data" / "processed" / "outputs" / "spatial"

# Candidate column names for the zone-code field across different boundary files
CODE_CANDIDATES = [
    "OA01CDOLD", "oa01cdold", "OA01CD", "oa01cd",
    "WD91CD", "WARD_CODE", "WARDCODE", "CODE", "LABEL", "label",
    "zoneid", "ZONEID", "OA_CODE", "oa_code", "geo_code", "GEO_CODE", "code",
]


def _find_boundary(candidates: list[Path]) -> Path | None:
    """Return the first existing path from a list of candidates."""
    for p in candidates:
        if p.exists():
            return p
    # Fallback: first .shp or .gpkg found in the parent directory of the first candidate
    search_dir = candidates[0].parent
    if search_dir.exists():
        for ext in ("*.shp", "*.gpkg"):
            found = sorted(search_dir.glob(ext))
            if found:
                return found[0]
    return None


def _detect_code_col(gdf: gpd.GeoDataFrame, prefix: str) -> str | None:
    """Detect the code column by trying known names then scanning for prefix matches."""
    for c in CODE_CANDIDATES:
        if c in gdf.columns:
            return c
    for c in gdf.columns:
        if gdf[c].dtype == object:
            sample = gdf[c].astype(str).str.strip().str.upper()
            if sample.str.startswith(prefix).any():
                log.info("  Auto-detected code column: '%s'", c)
                return c
    return None


def join_1981() -> None:
    """Join 1981 ED boundaries to ward-level indicators on WD81CD.

    Note: the 1981 indicator file operates at ward level; each ED in this
    GeoPackage shares the same indicator values as its parent ward.
    This output is for QGIS validation only; harmonisation uses script 06.
    """
    shp_path = BND / "1981" / "ED_1981_EW.shp"
    if not shp_path.exists():
        log.warning("1981 boundary not found: %s – skipping", shp_path)
        return

    ind_path = IND / "1981" / "manchester_eds_1981_indicators.csv"
    if not ind_path.exists():
        log.warning("1981 indicators not found: %s – skipping", ind_path)
        return

    gdf = gpd.read_file(shp_path)
    gdf = gdf[gdf["LAD81CD"] == "03BN"].copy()
    log.info("1981 EDs: %d features", len(gdf))

    indicators = pd.read_csv(ind_path)
    indicators["zoneid_trimmed"] = normalise_zoneid(indicators["zoneid"])

    # Join on WD81CD (ward code); multiple EDs share the same ward-level value
    joined = gdf.merge(indicators, left_on="WD81CD", right_on="zoneid_trimmed", how="left")
    unmatched = joined["zoneid"].isna().sum()
    if unmatched:
        log.warning("  %d unmatched EDs", unmatched)
    else:
        log.info("  All %d EDs matched", len(joined))

    out = SPAT / "1981" / "manchester_eds_1981_joined_indicators.gpkg"
    save_gpkg(joined, out)


def join_1991() -> None:
    """Join 1991 ward boundaries to ward-level indicators."""
    boundary_path = _find_boundary([
        BND / "1991" / "1991_wards_ew.shp",
        BND / "1991" / "wards_1991.shp",
        BND / "1991" / "census_wards_1991.shp",
        BND / "1991" / "ewwd91.shp",
    ])
    if boundary_path is None:
        log.warning("1991 ward boundary not found in gis_boundaries/1991/ – skipping")
        return

    ind_path = IND / "1991" / "manchester_wards_1991_indicators.csv"
    if not ind_path.exists():
        log.warning("1991 indicators not found: %s – skipping", ind_path)
        return

    gdf = gpd.read_file(boundary_path)
    code_col = _detect_code_col(gdf, "03BN")
    if code_col is None:
        log.error("Cannot identify ward code column in %s", boundary_path)
        return

    gdf["zoneid"] = normalise_zoneid(gdf[code_col])
    gdf = gdf[gdf["zoneid"].str.startswith("03BN")].copy()
    log.info("1991 wards: %d features", len(gdf))

    indicators = pd.read_csv(ind_path)
    indicators["zoneid"] = normalise_zoneid(indicators["zoneid"])
    joined = gdf.merge(indicators, on="zoneid", how="left")
    matched = joined.iloc[:, -1].notna().sum()
    log.info("  Match rate: %d/%d", matched, len(joined))

    out = SPAT / "1991" / "manchester_wards_1991_joined_indicators.gpkg"
    save_gpkg(joined, out)


def join_2001() -> None:
    """Join 2001 OA boundaries to OA-level indicators."""
    boundary_path = _find_boundary([
        BND / "2001" / "england_oa_2001.shp",
        BND / "2001" / "OA_2001_EW_BGC.shp",
        BND / "2001" / "oas_2001.shp",
        BND / "2001" / "OA_2001_EW_BGC.gpkg",
    ])
    if boundary_path is None:
        log.error("No 2001 OA boundary found in gis_boundaries/2001/ – download from geoportal.statistics.gov.uk")
        return

    ind_path = IND / "2001" / "manchester_oas_2001_indicators.csv"
    if not ind_path.exists():
        log.warning("2001 indicators not found: %s – skipping", ind_path)
        return

    gdf = gpd.read_file(boundary_path)
    code_col = _detect_code_col(gdf, "00BN")
    if code_col is None:
        log.error("Cannot identify OA code column in %s", boundary_path)
        return

    gdf["zoneid"] = normalise_zoneid(gdf[code_col])
    gdf = gdf[gdf["zoneid"].str.startswith("00BN")].copy()
    log.info("2001 OAs: %d features", len(gdf))

    indicators = pd.read_csv(ind_path, dtype={"zoneid": str})
    indicators["zoneid"] = normalise_zoneid(indicators["zoneid"])
    joined = gdf.merge(indicators, on="zoneid", how="left")
    matched = joined["total_pop"].notna().sum()
    match_rate = 100 * matched / len(joined) if len(joined) else 0
    log.info("  Match rate: %d/%d (%.1f%%)", matched, len(joined), match_rate)
    if match_rate < 95:
        unmatched = joined.loc[joined["total_pop"].isna(), "zoneid"].head(5).tolist()
        log.warning("  Sample unmatched OAs: %s", unmatched)

    out = SPAT / "2001" / "manchester_oas_2001_joined_indicators.gpkg"
    save_gpkg(joined, out)


def main() -> None:
    log.info("=== Step 3: Join boundaries to indicators (1981 / 1991 / 2001) ===")
    join_1981()
    join_1991()
    join_2001()
    log.info("=== Boundary joins complete ===")


if __name__ == "__main__":
    main()
