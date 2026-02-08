#!/usr/bin/env python3
"""
Create Joined GeoPackage: Merge 1981 ED Boundaries with Indicator CSV

This script:
1. Loads ED boundary shapefile
2. Loads indicator CSV (ward-level, 1053 rows)
3. Merges them on WD81CD (ward code)
4. Exports as GeoPackage with all joined attributes permanent

Usage:
    python scripts/create_joined_gpkg_1981.py

Outputs:
    - data/processed/outputs/spatial/1981/manchester_eds_1981_joined_indicators.gpkg
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("CREATE JOINED GEOPACKAGE: 1981 ED Boundaries + Indicators")
    print("=" * 70)
    
    # Paths
    project_root = Path(__file__).parent.parent
    shp_path = project_root / 'gis_boundaries/ED_1981_EW.shp'
    csv_path = project_root / 'data/processed/indicators/1981/manchester_eds_1981_indicators.csv'
    output_gpkg = project_root / 'data/processed/outputs/spatial/1981/manchester_eds_1981_joined_indicators.gpkg'
    
    # Ensure output directory exists
    output_gpkg.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n[1/4] Loading boundary shapefile...")
    # Load shapefile
    gdf_boundary = gpd.read_file(str(shp_path))
    logger.info(f"  - Loaded {len(gdf_boundary)} features")
    logger.info(f"  - Columns: {gdf_boundary.columns.tolist()}")
    
    # Filter to Manchester EDs only
    gdf_manchester = gdf_boundary[gdf_boundary['LAD81CD'] == '03BN'].copy()
    logger.info(f"  - Filtered to Manchester: {len(gdf_manchester)} EDs")
    
    print("\n[2/4] Loading indicator CSV...")
    # Load indicator CSV
    df_indicators = pd.read_csv(str(csv_path))
    logger.info(f"  - Loaded {len(df_indicators)} rows, {len(df_indicators.columns)} columns")
    logger.info(f"  - Sample zoneids: {df_indicators['zoneid'].head().tolist()}")
    
    # Trim zoneid to match WD81CD (ward code)
    df_indicators['zoneid_trimmed'] = df_indicators['zoneid'].str.strip()
    logger.info(f"  - Trimmed zoneid; unique values: {df_indicators['zoneid_trimmed'].nunique()}")
    
    print("\n[3/4] Performing join...")
    # Join: left join on boundaries (each ED gets ward-level indicator values)
    # Multiple EDs per ward will have identical indicator values (normal)
    joined = gdf_manchester.merge(
        df_indicators,
        left_on='WD81CD',
        right_on='zoneid_trimmed',
        how='left'
    )
    logger.info(f"  - Joined result: {len(joined)} features")
    
    # Check for unmatched EDs (should be 0)
    unmatched = joined[joined['zoneid'].isna()]
    if len(unmatched) > 0:
        logger.warning(f"  - WARNING: {len(unmatched)} unmatched EDs!")
        logger.warning(f"    Unmatched WD81CD values: {unmatched['WD81CD'].unique().tolist()}")
    else:
        logger.info(f"  - ✓ All {len(joined)} EDs matched successfully (100%)")
    
    # Check joined column integrity
    sample_col = 'TOTAL_RES_1981'
    non_null = joined[sample_col].notna().sum()
    logger.info(f"  - Non-NULL {sample_col}: {non_null} / {len(joined)}")
    
    print(f"\n[4/4] Exporting to GeoPackage...")
    # Export to GeoPackage
    joined.to_file(
        str(output_gpkg),
        driver='GPKG',
        layer='manchester_eds_1981_joined'
    )
    logger.info(f"  - ✓ Exported to: {output_gpkg}")
    logger.info(f"    Layer: manchester_eds_1981_joined")
    logger.info(f"    Features: {len(joined)}")
    logger.info(f"    Columns: {len(joined.columns)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"\nGeoPackage: {output_gpkg}")
    print(f"Features: {len(joined)}")
    print(f"Columns: {', '.join(joined.columns[:5])}... (and more)")
    print(f"\nNext steps:")
    print(f"  1. In QGIS: Layer → Add Layer → Add Vector Layer")
    print(f"  2. Select: {output_gpkg}")
    print(f"  3. Create choropleth using: ind_PCT_CHINESE_BORN_1981")
    print(f"  4. Export map as PNG to figures/")
    print("=" * 70)

if __name__ == '__main__':
    main()
