#!/usr/bin/env python3
"""
Create 1991 Manchester Wards Joined GeoPackage for QGIS Mapping
================================================================

This script creates a spatial dataset joining 1991 Manchester ward indicators
with ward boundary polygons.

IMPORTANT: 1991 ward boundaries must be obtained separately.
Recommended source: UK Data Service - 1991 Census Ward Boundaries

Current status:
- Indicator CSV: READY (data/processed/indicators/1991/manchester_wards_1991_indicators.csv)
- Ward boundaries: REQUIRED (see instructions below)

Ward Boundary Sources:
1. UK Data Service: https://ukdataservice.ac.uk/
   - Search: "1991 Census Ward Boundaries England Wales"
   - Dataset: SN 5819 or similar
   
2. UK Borders Service: https://borders.ukdataservice.ac.uk/
   - 1991 Census Ward Boundaries

3. Alternative: Create synthetic boundaries by aggregating 1981 EDs
   (requires ED-to-ward lookup table)

Inputs:
  - Ward indicator CSV: data/processed/indicators/1991/manchester_wards_1991_indicators.csv
  - Ward boundary shapefile: gis_boundaries/1991/[ward_shapefile].shp (TO BE PROVIDED)

Output:
  - GeoPackage: data/processed/outputs/spatial/1991/manchester_wards_1991_joined_indicators.gpkg

Author: FYP Data Pipeline
Date: 2026-02-04
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURATION
# =====================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INDICATORS_PATH = DATA_DIR / "processed" / "indicators" / "1991" / "manchester_wards_1991_indicators.csv"
OUTPUT_DIR = DATA_DIR / "processed" / "outputs" / "spatial" / "1991"

# Ward boundary file - UPDATE THIS PATH when boundary file is available
WARD_BOUNDARY_PATH = PROJECT_ROOT / "gis_boundaries" / "1991" / "1991_wards_ew.shp"  # Placeholder

# Alternative boundary paths to check
ALTERNATIVE_BOUNDARY_PATHS = [
    PROJECT_ROOT / "gis_boundaries" / "1991" / "wards_1991.shp",
    PROJECT_ROOT / "gis_boundaries" / "1991" / "1991_wards.shp",
    PROJECT_ROOT / "gis_boundaries" / "1991" / "census_wards_1991.shp",
    PROJECT_ROOT / "gis_boundaries" / "1991" / "ewwd91.shp",  # Common UK Data Service name
]

# Manchester ward codes (1991 format: 03BNxx)
MANCHESTER_WARD_PREFIX = "03BN"


def find_ward_boundaries() -> Path | None:
    """
    Search for 1991 ward boundary file in expected locations.
    
    Returns:
        Path to boundary file if found, None otherwise
    """
    # Check primary path
    if WARD_BOUNDARY_PATH.exists():
        return WARD_BOUNDARY_PATH
    
    # Check alternatives
    for alt_path in ALTERNATIVE_BOUNDARY_PATHS:
        if alt_path.exists():
            logger.info(f"Found boundary file: {alt_path}")
            return alt_path
    
    # Search for any shapefile in 1991 directory that might be wards
    boundary_dir = PROJECT_ROOT / "gis_boundaries" / "1991"
    if boundary_dir.exists():
        for shp in boundary_dir.glob("*.shp"):
            # Skip known non-ward files
            if "urban" in shp.name.lower() or "ua" in shp.name.lower():
                continue
            logger.info(f"Found potential boundary file: {shp}")
            return shp
    
    return None


def load_indicators() -> pd.DataFrame:
    """Load the 1991 ward indicator CSV."""
    logger.info(f"Loading indicators from {INDICATORS_PATH}")
    
    if not INDICATORS_PATH.exists():
        raise FileNotFoundError(f"Indicator file not found: {INDICATORS_PATH}")
    
    df = pd.read_csv(INDICATORS_PATH)
    logger.info(f"  Loaded {len(df)} wards with {len(df.columns)} columns")
    
    return df


def load_boundaries(boundary_path: Path) -> gpd.GeoDataFrame:
    """
    Load ward boundary shapefile and filter to Manchester wards.
    
    Args:
        boundary_path: Path to boundary shapefile
        
    Returns:
        GeoDataFrame with Manchester ward boundaries
    """
    logger.info(f"Loading boundaries from {boundary_path}")
    
    gdf = gpd.read_file(boundary_path)
    logger.info(f"  Loaded {len(gdf)} features")
    logger.info(f"  Columns: {list(gdf.columns)}")
    logger.info(f"  CRS: {gdf.crs}")
    
    # Try to identify the ward code column
    code_col = None
    for col in ['WARD_CODE', 'WARDCODE', 'CODE', 'LABEL', 'zoneid', 'ZONEID', 'WD91CD']:
        if col in gdf.columns:
            code_col = col
            break
    
    if code_col is None:
        # Try to find column containing Manchester codes
        for col in gdf.columns:
            if gdf[col].dtype == 'object':
                sample = gdf[col].astype(str).str.strip()
                if sample.str.startswith(MANCHESTER_WARD_PREFIX).any():
                    code_col = col
                    break
    
    if code_col is None:
        logger.error("Could not identify ward code column!")
        logger.error(f"Available columns: {list(gdf.columns)}")
        raise ValueError("Cannot find ward code column in boundary file")
    
    logger.info(f"  Using '{code_col}' as ward code column")
    
    # Filter to Manchester wards
    gdf['zoneid'] = gdf[code_col].astype(str).str.strip()
    manchester = gdf[gdf['zoneid'].str.startswith(MANCHESTER_WARD_PREFIX)].copy()
    
    logger.info(f"  Filtered to {len(manchester)} Manchester wards")
    
    if len(manchester) == 0:
        logger.warning("No Manchester wards found in boundary file!")
        logger.warning(f"Sample codes: {gdf['zoneid'].head(10).tolist()}")
    
    return manchester


def join_indicators_to_boundaries(
    boundaries: gpd.GeoDataFrame,
    indicators: pd.DataFrame
) -> gpd.GeoDataFrame:
    """
    Join indicator data to ward boundaries.
    
    Args:
        boundaries: Ward boundary GeoDataFrame
        indicators: Ward indicator DataFrame
        
    Returns:
        Joined GeoDataFrame
    """
    logger.info("Joining indicators to boundaries...")
    
    # Ensure zoneid column exists and is clean in both
    boundaries['zoneid'] = boundaries['zoneid'].astype(str).str.strip()
    indicators['zoneid'] = indicators['zoneid'].astype(str).str.strip()
    
    # Perform left join (keep all boundaries, add indicators where matched)
    joined = boundaries.merge(
        indicators,
        on='zoneid',
        how='left',
        suffixes=('_boundary', '_indicator')
    )
    
    # Calculate match statistics
    indicator_cols = [c for c in indicators.columns if c != 'zoneid']
    if indicator_cols:
        first_indicator = indicator_cols[0]
        matched = joined[first_indicator].notna().sum()
        total = len(joined)
        match_rate = 100 * matched / total if total > 0 else 0
        
        logger.info(f"  Match rate: {matched}/{total} ({match_rate:.1f}%)")
        
        if match_rate < 95:
            logger.warning(f"  Low match rate! Check zoneid formatting.")
            unmatched = joined[joined[first_indicator].isna()]['zoneid'].tolist()
            logger.warning(f"  Unmatched zones: {unmatched[:10]}")
    
    return joined


def save_geopackage(gdf: gpd.GeoDataFrame, output_path: Path):
    """Save GeoDataFrame to GeoPackage format."""
    logger.info(f"Saving to {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure CRS is set (British National Grid)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:27700")
        logger.info("  Set CRS to EPSG:27700 (British National Grid)")
    
    gdf.to_file(output_path, driver="GPKG")
    logger.info(f"  Saved {len(gdf)} features to GeoPackage")


def create_qgis_ready_csv():
    """
    If no boundary file available, prepare a QGIS-ready CSV
    that can be joined manually to boundaries in QGIS.
    """
    logger.info("Creating QGIS-ready CSV (for manual join in QGIS)...")
    
    indicators = load_indicators()
    
    # Ensure clean zoneid for joining
    indicators['zoneid'] = indicators['zoneid'].astype(str).str.strip()
    
    # Save to output location
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "manchester_wards_1991_indicators_for_qgis.csv"
    indicators.to_csv(csv_path, index=False)
    
    logger.info(f"  Saved: {csv_path}")
    logger.info("")
    logger.info("=" * 60)
    logger.info("MANUAL QGIS JOIN INSTRUCTIONS")
    logger.info("=" * 60)
    logger.info("""
1. Obtain 1991 Ward Boundaries:
   - UK Data Service: https://borders.ukdataservice.ac.uk/
   - Search for "1991 Census Ward Boundaries"
   - Download shapefile for England & Wales

2. In QGIS:
   a) Add the ward boundary shapefile as a layer
   b) Add the CSV as a layer (Layer → Add Layer → Add Delimited Text)
      - Select "No geometry" option
   c) Right-click ward boundary layer → Properties → Joins
   d) Add join:
      - Join layer: the CSV
      - Join field: zoneid
      - Target field: [ward code column in shapefile]
   e) Export joined layer:
      - Right-click → Export → Save Features As
      - Format: GeoPackage
      - Output: data/processed/outputs/spatial/1991/manchester_wards_1991_joined.gpkg

3. Create choropleth:
   - Style the layer using PCT_CHINESE_ETHNIC_1991 or other indicators
""")
    
    return csv_path


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("1991 Manchester Wards GeoPackage Creator")
    logger.info("=" * 60)
    
    # Check for ward boundaries
    boundary_path = find_ward_boundaries()
    
    if boundary_path is None:
        logger.warning("=" * 60)
        logger.warning("Ward boundary file not found!")
        logger.warning("=" * 60)
        logger.warning(f"Expected locations checked:")
        logger.warning(f"  - {WARD_BOUNDARY_PATH}")
        for p in ALTERNATIVE_BOUNDARY_PATHS:
            logger.warning(f"  - {p}")
        logger.warning("")
        
        # Create QGIS-ready CSV as fallback
        csv_path = create_qgis_ready_csv()
        
        logger.info("")
        logger.info("OUTPUT: QGIS-ready CSV created (for manual join)")
        logger.info(f"  {csv_path}")
        return
    
    # Load data
    indicators = load_indicators()
    boundaries = load_boundaries(boundary_path)
    
    if len(boundaries) == 0:
        logger.error("No Manchester ward boundaries found. Cannot proceed.")
        return
    
    # Join
    joined = join_indicators_to_boundaries(boundaries, indicators)
    
    # Save
    output_path = OUTPUT_DIR / "manchester_wards_1991_joined_indicators.gpkg"
    save_geopackage(joined, output_path)
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUCCESS!")
    logger.info("=" * 60)
    logger.info(f"Output: {output_path}")
    logger.info(f"Features: {len(joined)} wards")
    logger.info(f"Indicators: {len([c for c in joined.columns if '_1991' in c])} columns")
    logger.info("")
    logger.info("Open in QGIS:")
    logger.info(f"  Layer → Add Layer → Add Vector Layer")
    logger.info(f"  Select: {output_path}")


if __name__ == "__main__":
    main()
