#!/usr/bin/env python3
"""
Step 3c: Join 2001 Manchester Output Area Boundaries with Indicator CSV
=======================================================================

Joins the 2001 OA-level indicator CSV to 2001 OA boundary polygons and writes
a GeoPackage ready for QGIS.

Inputs:
  data/processed/indicators/2001/manchester_oas_2001_indicators.csv
  gis_boundaries/2001/  (2001 OA boundaries for Manchester / England)

Output:
  data/processed/outputs/spatial/2001/manchester_oas_2001_joined_indicators.gpkg

Boundary sources (if not yet downloaded):
  • ONS Open Geography Portal:
    https://geoportal.statistics.gov.uk/
    Dataset: Output Areas (December 2001) Full Clipped Boundaries EW
  • UK Data Service:
    https://borders.ukdataservice.ac.uk/
    Census Output Area boundaries 2001

The script auto-searches gis_boundaries/2001/ for any .shp or .gpkg file
matching OA boundaries and tries several candidate OA-code column names.

Author: FYP Data Pipeline
Date: 2026-02-25
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import logging
import sys

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

INDICATORS_PATH = (
    DATA_DIR / "processed" / "indicators" / "2001" / "manchester_oas_2001_indicators.csv"
)
OUTPUT_DIR = DATA_DIR / "processed" / "outputs" / "spatial" / "2001"
OUTPUT_GPKG = OUTPUT_DIR / "manchester_oas_2001_joined_indicators.gpkg"

BOUNDARY_DIR = PROJECT_ROOT / "gis_boundaries" / "2001"

MANCHESTER_PREFIX = "00BN"  # 2001 OA prefix for Manchester

# Primary boundary file path (update when file is placed in the repo)
BOUNDARY_PRIMARY = BOUNDARY_DIR / "england_oa_2001.shp"

# Alternative paths to try
BOUNDARY_ALTERNATIVES = [
    BOUNDARY_DIR / "OA_2001_EW_BGC.shp",
    BOUNDARY_DIR / "oas_2001.shp",
    BOUNDARY_DIR / "census_oas_2001.shp",
    BOUNDARY_DIR / "manchester_oas_2001.shp",
    BOUNDARY_DIR / "england_oa_2001.gpkg",
    BOUNDARY_DIR / "OA_2001_EW_BGC.gpkg",
]

# Candidate column names for the OA code field.
# OA01CDOLD is listed first because the raw SAS census data uses the pre-2011
# alphanumeric OA codes (e.g. 00BNFA01) rather than the E-code system introduced
# later (e.g. E00000001 stored in OA01CD). We must join on the same code format
# that was used during ingestion.
OA_CODE_CANDIDATES = [
    "OA01CDOLD", "oa01cdold", "OA01CD", "oa01cd",
    "OA_CODE", "oa_code", "LABEL", "label",
    "zoneid", "ZONEID", "OA_ID", "oa_id", "geo_code", "GEO_CODE",
    "code", "CODE", "OAC_CODE",
]

# Target join rate
TARGET_MATCH_RATE_PCT = 95.0


# ─────────────────────────────────────────────────────────────────────────────
# BOUNDARY DISCOVERY
# ─────────────────────────────────────────────────────────────────────────────

def find_boundary_file() -> Path | None:
    """
    Search for a 2001 OA boundary file in gis_boundaries/2001/.
    Returns the first file found, preference order: primary → alternatives → any shp/gpkg.
    """
    if BOUNDARY_PRIMARY.exists():
        return BOUNDARY_PRIMARY

    for alt in BOUNDARY_ALTERNATIVES:
        if alt.exists():
            logger.info(f"  Found alternative boundary: {alt}")
            return alt

    # Last resort: any .shp or .gpkg in the 2001 boundary dir
    if BOUNDARY_DIR.exists():
        for ext in ["*.shp", "*.gpkg"]:
            for found in sorted(BOUNDARY_DIR.glob(ext)):
                logger.info(f"  Auto-discovered boundary file: {found}")
                return found

    return None


# ─────────────────────────────────────────────────────────────────────────────
# LOAD INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def load_indicators() -> pd.DataFrame:
    """Load the 2001 OA indicator CSV."""
    logger.info(f"Loading indicators: {INDICATORS_PATH}")

    if not INDICATORS_PATH.exists():
        raise FileNotFoundError(
            f"Indicator file not found: {INDICATORS_PATH}\n"
            "Run scripts/07_compute_indicators_2001_oas.py first."
        )

    df = pd.read_csv(INDICATORS_PATH, dtype={"zoneid": str})
    df["zoneid"] = df["zoneid"].astype(str).str.strip().str.upper()
    logger.info(f"  Loaded {len(df)} OAs, {len(df.columns)} columns")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# LOAD BOUNDARIES
# ─────────────────────────────────────────────────────────────────────────────

def load_boundaries(boundary_path: Path) -> gpd.GeoDataFrame:
    """
    Load 2001 OA boundary file and filter to Manchester OAs.
    Auto-detects the OA code column.
    """
    logger.info(f"Loading boundaries: {boundary_path}")

    gdf = gpd.read_file(boundary_path)
    logger.info(f"  Total features loaded : {len(gdf)}")
    logger.info(f"  CRS                   : {gdf.crs}")
    logger.info(f"  Columns               : {list(gdf.columns)}")

    # ── Identify OA code column ──────────────────────────────────────────────
    code_col = None
    for candidate in OA_CODE_CANDIDATES:
        if candidate in gdf.columns:
            code_col = candidate
            break

    if code_col is None:
        # Try to find any column whose values start with the Manchester prefix
        for col in gdf.columns:
            if gdf[col].dtype == object:
                sample = gdf[col].astype(str).str.strip().str.upper()
                if sample.str.startswith(MANCHESTER_PREFIX).any():
                    code_col = col
                    logger.info(f"  Auto-detected code column: '{col}'")
                    break

    if code_col is None:
        logger.error("Cannot identify OA code column in boundary file!")
        logger.error(f"Available columns: {list(gdf.columns)}")
        raise ValueError("No OA code column found. Check boundary file.")

    logger.info(f"  Using OA code column: '{code_col}'")
    gdf["zoneid"] = gdf[code_col].astype(str).str.strip().str.upper()

    # ── Filter to Manchester ─────────────────────────────────────────────────
    manchester = gdf[gdf["zoneid"].str.startswith(MANCHESTER_PREFIX)].copy()
    logger.info(f"  Manchester OAs after filter: {len(manchester)}")

    if len(manchester) == 0:
        logger.warning("No Manchester OAs found in boundary file!")
        logger.warning(f"  Sample codes: {gdf['zoneid'].head(10).tolist()}")

    return manchester


# ─────────────────────────────────────────────────────────────────────────────
# JOIN
# ─────────────────────────────────────────────────────────────────────────────

def join_indicators_to_boundaries(
    boundaries: gpd.GeoDataFrame,
    indicators: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """
    Left-join indicator data onto OA boundaries (all boundaries kept).
    Reports match rate; warns if below TARGET_MATCH_RATE_PCT.
    """
    logger.info("Joining indicators to boundaries…")

    boundaries["zoneid"] = boundaries["zoneid"].astype(str).str.strip().str.upper()
    indicators["zoneid"] = indicators["zoneid"].astype(str).str.strip().str.upper()

    joined = boundaries.merge(indicators, on="zoneid", how="left", suffixes=("", "_ind"))

    # ── Match statistics ─────────────────────────────────────────────────────
    matched = joined["total_pop"].notna().sum()
    total = len(joined)
    match_rate = 100.0 * matched / total if total > 0 else 0.0

    logger.info(f"  Match rate: {matched}/{total} ({match_rate:.1f}%)")

    if match_rate < TARGET_MATCH_RATE_PCT:
        logger.warning(f"  ⚠ Match rate below target ({TARGET_MATCH_RATE_PCT}%)!")
        unmatched = joined.loc[joined["total_pop"].isna(), "zoneid"].head(10).tolist()
        logger.warning(f"  Sample unmatched OAs: {unmatched}")
    else:
        logger.info(f"  ✓ Match rate meets target (≥ {TARGET_MATCH_RATE_PCT}%)")

    # ── Check indicator-side OAs not in boundaries ───────────────────────────
    boundary_ids = set(boundaries["zoneid"])
    indicator_ids = set(indicators["zoneid"])
    orphan_indicators = indicator_ids - boundary_ids
    if orphan_indicators:
        logger.warning(
            f"  {len(orphan_indicators)} indicator OAs have no matching boundary "
            f"(first 5: {sorted(orphan_indicators)[:5]})"
        )

    return joined


# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────

def save_gpkg(joined: gpd.GeoDataFrame) -> None:
    """Write the joined GeoDataFrame to a GeoPackage."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure a valid CRS (default to BNG if unknown)
    if joined.crs is None:
        joined = joined.set_crs("EPSG:27700")
        logger.warning("  CRS was None – set to EPSG:27700 (British National Grid)")

    joined.to_file(OUTPUT_GPKG, driver="GPKG")
    size_mb = OUTPUT_GPKG.stat().st_size / (1024 * 1024)
    logger.info(f"✓ GeoPackage saved: {OUTPUT_GPKG}  ({size_mb:.2f} MB)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 65)
    logger.info("Create 2001 OA Joined GeoPackage")
    logger.info("=" * 65)

    # ── Load indicators ──────────────────────────────────────────────────────
    indicators = load_indicators()

    # ── Find and load boundary file ──────────────────────────────────────────
    boundary_path = find_boundary_file()
    if boundary_path is None:
        logger.error("No 2001 OA boundary file found in gis_boundaries/2001/")
        logger.error("Download from:")
        logger.error("  https://geoportal.statistics.gov.uk/")
        logger.error("  Search: 'Output Areas December 2001 Full Clipped Boundaries EW'")
        logger.error("Place the .shp or .gpkg in: gis_boundaries/2001/")
        sys.exit(1)

    boundaries = load_boundaries(boundary_path)
    if boundaries.empty:
        logger.error("No Manchester OA boundaries loaded. Exiting.")
        sys.exit(1)

    # ── Join ─────────────────────────────────────────────────────────────────
    joined = join_indicators_to_boundaries(boundaries, indicators)

    # ── Save ─────────────────────────────────────────────────────────────────
    save_gpkg(joined)

    # ── Summary ─────────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 65)
    logger.info("SUMMARY")
    logger.info("=" * 65)
    logger.info(f"OA boundaries loaded     : {len(boundaries)}")
    logger.info(f"Indicators loaded        : {len(indicators)}")
    logger.info(f"Features in GeoPackage   : {len(joined)}")
    logger.info(f"Columns in GeoPackage    : {len(joined.columns)}")
    logger.info("")
    logger.info("Open in QGIS:")
    logger.info(f"  {OUTPUT_GPKG}")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
