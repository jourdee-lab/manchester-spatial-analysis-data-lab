#!/usr/bin/env python3
"""
Phase 7: Compute ED-Level Indicators for 1991 Manchester
=========================================================

Processes 1991 census data at Enumeration District (ED) level and creates
a spatial dataset for QGIS mapping.

Inputs:
  - 1991 raw SAS data: data/raw/s02ews/, s06ews/, s07ews/, s09ews/, s49ews/
  - 1991 ED boundaries: gis_boundaries/1991/England_ED/england_ed_1991.shp

Outputs:
  - ED-level indicator CSV: data/processed/indicators/1991/manchester_eds_1991_indicators.csv
  - Joined GeoPackage: data/processed/outputs/spatial/1991/manchester_eds_1991_joined_indicators.gpkg

Author: FYP Data Pipeline
Date: 2026-02-04
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import logging

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
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "processed" / "indicators" / "1991"
SPATIAL_OUTPUT_DIR = DATA_DIR / "processed" / "outputs" / "spatial" / "1991"
BOUNDARY_PATH = PROJECT_ROOT / "gis_boundaries" / "1991" / "England_ED" / "england_ed_1991.shp"

# Manchester ED pattern (8 characters: 03BN + 2 letter ward + 2 digit ED)
MANCHESTER_ED_PATTERN = r"^03BN[A-Z]{2}[0-9]{2}$"
MANCHESTER_PREFIX = "03BN"

# SAS table configurations
SAS_TABLES = {
    "s02ews": {
        "parts": ["s02ews1.csv", "s02ews2.csv", "s02ews3.csv", "s02ews4.csv"],
        "columns": ["s020001", "s020002", "s020005"]  # Total, Male, Female
    },
    "s06ews": {
        "parts": ["s06ews1.csv", "s06ews2.csv", "s06ews3.csv", "s06ews4.csv"],
        "columns": ["s060009", "s060021", "s060033", "s060045", "s060057", 
                   "s060069", "s060081", "s060093", "s060105"]
    },
    "s07ews": {
        "parts": ["s07ews1.csv", "s07ews2.csv", "s07ews3.csv", "s07ews4.csv"],
        "columns": ["s070041", "s070042"]  # China-born male/female
    },
    "s09ews": {
        "parts": ["s09ews1.csv", "s09ews2.csv", "s09ews3.csv", "s09ews4.csv"],
        "columns": ["s090005", "s090017", "s090023", "s090041", "s090047"]
    },
    "s49ews": {
        "parts": ["s49ew1.csv", "s49ew2.csv", "s49ew3.csv", "s49ew4.csv"],
        "columns": ["s490005", "s490019", "s490026"]
    },
}


def load_sas_table_eds(table_name: str) -> pd.DataFrame:
    """Load SAS table and filter to Manchester ED-level records."""
    table_config = SAS_TABLES.get(table_name)
    if not table_config:
        return pd.DataFrame()
    
    table_dir = RAW_DIR / table_name
    if not table_dir.exists():
        logger.warning(f"  Directory not found: {table_dir}")
        return pd.DataFrame()
    
    dfs = []
    for part_file in table_config["parts"]:
        part_path = table_dir / part_file
        if part_path.exists():
            try:
                df = pd.read_csv(part_path)
                dfs.append(df)
            except Exception as e:
                logger.warning(f"    Error loading {part_file}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    combined = pd.concat(dfs, ignore_index=True)
    combined['zoneid'] = combined['zoneid'].astype(str).str.strip()
    
    # Filter to Manchester EDs (8-character codes like 03BNFA01)
    ed_mask = combined['zoneid'].str.match(MANCHESTER_ED_PATTERN)
    manchester_eds = combined[ed_mask].copy()
    
    logger.info(f"  {table_name}: {len(manchester_eds)} Manchester EDs")
    
    return manchester_eds


def load_all_tables() -> dict:
    """Load all SAS tables for Manchester EDs."""
    logger.info("Loading 1991 SAS tables (ED-level)...")
    
    tables = {}
    for table_name in SAS_TABLES.keys():
        tables[table_name] = load_sas_table_eds(table_name)
    
    return tables


def merge_tables(tables: dict) -> pd.DataFrame:
    """Merge all SAS tables on zoneid."""
    logger.info("Merging tables...")
    
    base = tables.get('s02ews')
    if base is None or base.empty:
        logger.error("No base table (s02ews) available!")
        return pd.DataFrame()
    
    # Keep only needed columns plus zoneid
    cols_to_keep = ['zoneid'] + SAS_TABLES['s02ews']['columns']
    cols_to_keep = [c for c in cols_to_keep if c in base.columns]
    merged = base[cols_to_keep].copy()
    
    for table_name, df in tables.items():
        if table_name == 's02ews' or df.empty:
            continue
        
        cols_needed = ['zoneid'] + SAS_TABLES[table_name]['columns']
        cols_to_merge = [c for c in cols_needed if c in df.columns]
        
        if len(cols_to_merge) > 1:
            df_subset = df[cols_to_merge].drop_duplicates(subset=['zoneid'])
            merged = merged.merge(df_subset, on='zoneid', how='left')
            logger.info(f"  Merged {table_name}: {len(cols_to_merge)-1} columns")
    
    logger.info(f"  Final dataset: {len(merged)} EDs × {len(merged.columns)} columns")
    return merged


def compute_ed_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived indicators for each ED."""
    logger.info("Computing ED-level indicators...")
    
    df.columns = [c.lower() for c in df.columns]
    results = []
    
    for _, row in df.iterrows():
        ed_id = row['zoneid']
        ward_code = ed_id[:6] if len(ed_id) >= 6 else ed_id
        
        ind = {
            'zoneid': ed_id,
            'ward_code': ward_code,
            'year': 1991,
        }
        
        # Demographics
        total_res = row.get('s020001', np.nan)
        ind['TOTAL_RES_1991'] = total_res
        ind['TOTAL_MALE_1991'] = row.get('s020002', np.nan)
        ind['TOTAL_FEMALE_1991'] = row.get('s020005', np.nan)
        
        # Chinese ethnic group
        chinese = row.get('s060009', np.nan)
        ind['CHINESE_ETHNIC_1991'] = chinese
        ind['CHINESE_ETHNIC_MALE_1991'] = row.get('s060021', np.nan)
        ind['CHINESE_ETHNIC_FEMALE_1991'] = row.get('s060033', np.nan)
        
        if pd.notna(total_res) and total_res > 0 and pd.notna(chinese):
            ind['PCT_CHINESE_ETHNIC_1991'] = 100 * chinese / total_res
        else:
            ind['PCT_CHINESE_ETHNIC_1991'] = np.nan
        
        # Chinese age structure
        ind['CHINESE_AGE_0_4_1991'] = row.get('s060045', np.nan)
        ind['CHINESE_AGE_5_15_1991'] = row.get('s060057', np.nan)
        ind['CHINESE_AGE_16_29_1991'] = row.get('s060069', np.nan)
        ind['CHINESE_AGE_30_PENSION_1991'] = row.get('s060081', np.nan)
        ind['CHINESE_PENSIONABLE_1991'] = row.get('s060093', np.nan)
        ind['CHINESE_LIMITING_ILLNESS_1991'] = row.get('s060105', np.nan)
        
        # Country of birth
        china_m = row.get('s070041', np.nan)
        china_f = row.get('s070042', np.nan)
        if pd.notna(china_m) and pd.notna(china_f):
            china_born = china_m + china_f
        else:
            china_born = np.nan
        ind['CHINA_BORN_1991'] = china_born
        
        if pd.notna(total_res) and total_res > 0 and pd.notna(china_born):
            ind['PCT_CHINA_BORN_1991'] = 100 * china_born / total_res
        else:
            ind['PCT_CHINA_BORN_1991'] = np.nan
        
        # Economic position
        chinese_16plus = row.get('s090005', np.nan)
        econ_active_m = row.get('s090017', np.nan)
        econ_active_f = row.get('s090041', np.nan)
        unemployed_m = row.get('s090023', np.nan)
        unemployed_f = row.get('s090047', np.nan)
        
        ind['CHINESE_16PLUS_1991'] = chinese_16plus
        
        if pd.notna(econ_active_m) and pd.notna(econ_active_f):
            ind['CHINESE_ECON_ACTIVE_1991'] = econ_active_m + econ_active_f
        else:
            ind['CHINESE_ECON_ACTIVE_1991'] = np.nan
        
        if pd.notna(unemployed_m) and pd.notna(unemployed_f):
            ind['CHINESE_UNEMPLOYED_1991'] = unemployed_m + unemployed_f
        else:
            ind['CHINESE_UNEMPLOYED_1991'] = np.nan
        
        # Housing
        chinese_hh = row.get('s490005', np.nan)
        ind['CHINESE_HOUSEHOLDS_1991'] = chinese_hh
        ind['CHINESE_OVERCROWD_GT1P5_1991'] = row.get('s490019', np.nan)
        ind['CHINESE_OWNER_OCC_1991'] = row.get('s490026', np.nan)
        
        if pd.notna(chinese_hh) and chinese_hh > 0:
            overcrowd = row.get('s490019', np.nan)
            owner = row.get('s490026', np.nan)
            if pd.notna(overcrowd):
                ind['PCT_CHINESE_OVERCROWD_1991'] = 100 * overcrowd / chinese_hh
            if pd.notna(owner):
                ind['PCT_CHINESE_OWNER_OCC_1991'] = 100 * owner / chinese_hh
        
        results.append(ind)
    
    result_df = pd.DataFrame(results)
    logger.info(f"  Computed {len(result_df)} ED indicator records")
    return result_df


def load_boundaries() -> gpd.GeoDataFrame:
    """Load 1991 ED boundaries and filter to Manchester."""
    logger.info(f"Loading boundaries from {BOUNDARY_PATH}")
    
    gdf = gpd.read_file(BOUNDARY_PATH)
    logger.info(f"  Loaded {len(gdf)} total EDs")
    
    # Filter to Manchester
    gdf['zoneid'] = gdf['label'].astype(str).str.strip()
    manchester = gdf[gdf['zoneid'].str.startswith(MANCHESTER_PREFIX)].copy()
    
    logger.info(f"  Filtered to {len(manchester)} Manchester EDs")
    return manchester


def join_indicators_to_boundaries(
    boundaries: gpd.GeoDataFrame,
    indicators: pd.DataFrame
) -> gpd.GeoDataFrame:
    """Join indicator data to ED boundaries."""
    logger.info("Joining indicators to boundaries...")
    
    boundaries['zoneid'] = boundaries['zoneid'].astype(str).str.strip()
    indicators['zoneid'] = indicators['zoneid'].astype(str).str.strip()
    
    joined = boundaries.merge(indicators, on='zoneid', how='left')
    
    # Calculate match rate
    matched = joined['TOTAL_RES_1991'].notna().sum()
    total = len(joined)
    match_rate = 100 * matched / total if total > 0 else 0
    
    logger.info(f"  Match rate: {matched}/{total} ({match_rate:.1f}%)")
    
    if match_rate < 90:
        unmatched = joined[joined['TOTAL_RES_1991'].isna()]['zoneid'].head(10).tolist()
        logger.warning(f"  Sample unmatched: {unmatched}")
    
    return joined


def save_outputs(indicators: pd.DataFrame, joined: gpd.GeoDataFrame):
    """Save indicator CSV and GeoPackage."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SPATIAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    csv_path = OUTPUT_DIR / "manchester_eds_1991_indicators.csv"
    indicators.to_csv(csv_path, index=False)
    logger.info(f"✓ Indicators CSV: {csv_path}")
    
    # Save GeoPackage
    gpkg_path = SPATIAL_OUTPUT_DIR / "manchester_eds_1991_joined_indicators.gpkg"
    if joined.crs is None:
        joined = joined.set_crs("EPSG:27700")
    joined.to_file(gpkg_path, driver="GPKG")
    logger.info(f"✓ GeoPackage: {gpkg_path}")


def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("Phase 7: 1991 ED-Level Indicator Computation")
    logger.info("=" * 60)
    
    # Load and merge census data
    tables = load_all_tables()
    merged = merge_tables(tables)
    
    if merged.empty:
        logger.error("No data to process!")
        return
    
    # Compute indicators
    indicators = compute_ed_indicators(merged)
    
    # Load boundaries and join
    boundaries = load_boundaries()
    joined = join_indicators_to_boundaries(boundaries, indicators)
    
    # Save outputs
    save_outputs(indicators, joined)
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"EDs processed: {len(indicators)}")
    logger.info(f"EDs in GeoPackage: {len(joined)}")
    
    chinese_total = indicators['CHINESE_ETHNIC_1991'].sum()
    total_pop = indicators['TOTAL_RES_1991'].sum()
    if total_pop > 0:
        logger.info(f"Manchester Chinese population: {chinese_total:,.0f} ({100*chinese_total/total_pop:.2f}%)")
        logger.info(f"Manchester total population: {total_pop:,.0f}")
    
    logger.info("")
    logger.info("Open in QGIS:")
    logger.info(f"  {SPATIAL_OUTPUT_DIR / 'manchester_eds_1991_joined_indicators.gpkg'}")


if __name__ == "__main__":
    main()
