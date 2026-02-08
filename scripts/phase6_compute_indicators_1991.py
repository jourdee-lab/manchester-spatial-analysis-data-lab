#!/usr/bin/env python3
"""
Phase 6: Compute Indicators from ED-Level SAS Data (1991)
==========================================================

This script is a TEMPLATE for 1991 indicator computation.
It follows the same pattern as 1981 but with 1991 SAS column codes.

⚠️ IMPORTANT: This script requires ED-LEVEL 1991 census data.
The current repository contains COUNTY-LEVEL data only.

See: docs/1991_DATA_AVAILABILITY_CRITICAL.md

Inputs (when available):
  - ED-level SAS data: data/processed/raw_ed_level/1991/sas0X_1991_ed_level.csv

Outputs:
  - Indicator table: data/processed/indicators/1991/manchester_eds_1991_indicators.csv
  - Summary: data/processed/indicators/1991/indicators_summary.txt

Author: FYP Data Pipeline
Date: 2026-01-18
Status: TEMPLATE (awaiting 1991 ED-level data)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
SAS02_PATH = Path("data/processed/raw_ed_level/1991/sas02_1991_ed_level.csv")
SAS06_PATH = Path("data/processed/raw_ed_level/1991/sas06_1991_ed_level.csv")
SAS07_PATH = Path("data/processed/raw_ed_level/1991/sas07_1991_ed_level.csv")
SAS09_PATH = Path("data/processed/raw_ed_level/1991/sas09_1991_ed_level.csv")
SAS20_PATH = Path("data/processed/raw_ed_level/1991/sas20_1991_ed_level.csv")
OUTPUT_PATH = Path("data/processed/indicators/1991/manchester_eds_1991_indicators.csv")
SUMMARY_PATH = Path("data/processed/indicators/1991/indicators_summary.txt")

# =====================================================================
# IMPORTANT: SAS Code Mappings for 1991
# =====================================================================
# These are PLACEHOLDERS - exact codes need to be verified from:
# - 1991 SAS documentation
# - Variable lookup tables if available
# - Comparison with 1981 codes and table structure
#
# 1991 uses different table organization:
# - SAS06 contains ethnic group (replaces some of SAS04/SAS06 from 1981)
# - SAS07 is country of birth (like 1981 SAS06)
# - SAS09 is economic position (like 1981 SAS07/SAS08)
# - SAS20 is tenure and amenities (like 1981 SAS10, but reorganized)
#
# Column codes DO NOT have "91" prefix like 1981 (no "91sas020050")
# Instead: s020050, s060001, s070001, s090001, s160001, etc.
# =====================================================================

# 1991 SAS Column Mappings (REQUIRE VERIFICATION)
SAS_CODES_1991 = {
    # Demographics (SAS02)
    "TOTAL_RES": "s020050",           # PLACEHOLDER - verify exact code
    "MALE": "s020051",                # PLACEHOLDER
    "FEMALE": "s020054",              # PLACEHOLDER
    
    # Ethnic Group (SAS06) - note: replaces SAS04/SAS06 structure
    "CHINESE_BORN": "s060100",        # PLACEHOLDER - needs verification
    "CHINESE_MALE": "s060101",        # PLACEHOLDER
    "CHINESE_FEMALE": "s060102",      # PLACEHOLDER
    
    # Country of Birth (SAS07)
    "BORN_CHINA": "s070040",          # PLACEHOLDER - needs verification
    "BORN_FAR_EAST": "s070041",       # PLACEHOLDER
    
    # Employment (SAS09)
    "ALL_EMPLOYED": "s090040",        # PLACEHOLDER - SAS09 structure differs from SAS07
    "RESIDENTS_16PLUS": "s090001",    # PLACEHOLDER
    
    # Tenure & Amenities (SAS20, using s16ew codes)
    "TOTAL_HH": "s160001",            # PLACEHOLDER - total households
    "OWNER_OCC": "s160010",           # PLACEHOLDER
    "SOCIAL_RENT": "s160015",         # PLACEHOLDER
    "NO_CAR": "s160040",              # PLACEHOLDER
    "OVERCROWD_GT1P5": "s160050",     # PLACEHOLDER
    "NO_BATH_WC": "s160060",          # PLACEHOLDER
}

# =====================================================================
# VALIDATION FUNCTION
# =====================================================================

def check_data_availability():
    """Check if 1991 ED-level data is available."""
    
    required_files = [SAS02_PATH, SAS06_PATH, SAS07_PATH, SAS09_PATH, SAS20_PATH]
    missing = [f for f in required_files if not f.exists()]
    
    if missing:
        logger.error("="*70)
        logger.error("❌ CANNOT PROCEED: 1991 ED-LEVEL DATA NOT FOUND")
        logger.error("="*70)
        logger.error("\nMissing files:")
        for f in missing:
            logger.error(f"  - {f}")
        logger.error("\nStatus: The repository contains COUNTY-LEVEL 1991 data only.")
        logger.error("\nSolution: See docs/1991_DATA_AVAILABILITY_CRITICAL.md")
        logger.error("\nOptions:")
        logger.error("  A. Source 1991 ED-level census data separately")
        logger.error("  B. Focus Phase 6 on 1981 only (recommended short-term)")
        logger.error("  C. Use county-level data (loses spatial granularity)")
        logger.error("\n" + "="*70)
        return False
    
    return True

# =====================================================================
# MAIN COMPUTATION (TEMPLATE)
# =====================================================================

def main():
    """Load data and compute indicators."""
    
    logger.info("="*70)
    logger.info("PHASE 6: INDICATOR COMPUTATION (1991)")
    logger.info("="*70)
    
    # Check if data exists
    if not check_data_availability():
        logger.error("\nPlease acquire 1991 ED-level data before running this script.")
        sys.exit(1)
    
    # Load all SAS tables
    logger.info("\nLoading 1991 ED-level SAS tables...")
    try:
        sas02 = pd.read_csv(SAS02_PATH)
        sas06 = pd.read_csv(SAS06_PATH)
        sas07 = pd.read_csv(SAS07_PATH)
        sas09 = pd.read_csv(SAS09_PATH)
        sas20 = pd.read_csv(SAS20_PATH)
        
        logger.info(f"  SAS02: {sas02.shape}")
        logger.info(f"  SAS06: {sas06.shape}")
        logger.info(f"  SAS07: {sas07.shape}")
        logger.info(f"  SAS09: {sas09.shape}")
        logger.info(f"  SAS20: {sas20.shape}")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        sys.exit(1)
    
    # Merge all on zoneid
    logger.info("\nMerging tables on zoneid...")
    try:
        df = sas02.copy()
        df = df.merge(sas06[['zoneid'] + [c for c in sas06.columns if c != 'zoneid']], 
                      on='zoneid', how='inner')
        df = df.merge(sas07[['zoneid'] + [c for c in sas07.columns if c != 'zoneid']], 
                      on='zoneid', how='inner')
        df = df.merge(sas09[['zoneid'] + [c for c in sas09.columns if c != 'zoneid']], 
                      on='zoneid', how='inner')
        df = df.merge(sas20[['zoneid'] + [c for c in sas20.columns if c != 'zoneid']], 
                      on='zoneid', how='inner')
        
        logger.info(f"  Merged: {df.shape[0]} EDs × {df.shape[1]} columns")
    except Exception as e:
        logger.error(f"Error merging tables: {e}")
        sys.exit(1)
    
    # Create indicators dataframe
    indicators = pd.DataFrame({'zoneid': df['zoneid']})
    
    logger.info("\n" + "="*70)
    logger.info("COMPUTING INDICATORS")
    logger.info("="*70)
    
    try:
        # ===== DEMOGRAPHICS (SAS02) =====
        logger.info("\nComputing DEMOGRAPHIC indicators...")
        indicators['TOTAL_RES_1991'] = df[SAS_CODES_1991['TOTAL_RES']].astype(float)
        indicators['PCT_MALE_1991'] = (df[SAS_CODES_1991['MALE']] / df[SAS_CODES_1991['TOTAL_RES']] * 100).fillna(0)
        indicators['PCT_FEMALE_1991'] = (df[SAS_CODES_1991['FEMALE']] / df[SAS_CODES_1991['TOTAL_RES']] * 100).fillna(0)
        
        # ===== ETHNIC PRESENCE (SAS06) =====
        logger.info("Computing ETHNIC PRESENCE indicators...")
        indicators['CHINESE_BORN_1991'] = df[SAS_CODES_1991['CHINESE_BORN']].astype(float)
        indicators['CHINESE_BORN_MALE_1991'] = df[SAS_CODES_1991['CHINESE_MALE']].astype(float)
        indicators['CHINESE_BORN_FEMALE_1991'] = df[SAS_CODES_1991['CHINESE_FEMALE']].astype(float)
        indicators['PCT_CHINESE_BORN_1991'] = (df[SAS_CODES_1991['CHINESE_BORN']] / df[SAS_CODES_1991['TOTAL_RES']] * 100).fillna(0)
        
        # ===== EMPLOYMENT (SAS09) =====
        logger.info("Computing EMPLOYMENT indicators...")
        indicators['RES_16PLUS_1991'] = df[SAS_CODES_1991['RESIDENTS_16PLUS']].astype(float)
        indicators['ALL_EMPLOYED_1991'] = df[SAS_CODES_1991['ALL_EMPLOYED']].astype(float)
        indicators['EMP_RATE_1991'] = (df[SAS_CODES_1991['ALL_EMPLOYED']] / df[SAS_CODES_1991['RESIDENTS_16PLUS']] * 100).fillna(0)
        
        # ===== HOUSING (SAS20) =====
        logger.info("Computing HOUSING indicators...")
        
        # Total households
        indicators['TOTAL_HH_1991'] = df[SAS_CODES_1991['TOTAL_HH']].astype(float)
        
        # Tenure
        indicators['OWNER_OCC_HH_1991'] = df[SAS_CODES_1991['OWNER_OCC']].astype(float)
        indicators['PCT_OWNER_OCC_1991'] = (df[SAS_CODES_1991['OWNER_OCC']] / df[SAS_CODES_1991['TOTAL_HH']] * 100).fillna(0)
        
        indicators['SOCIAL_RENT_HH_1991'] = df[SAS_CODES_1991['SOCIAL_RENT']].astype(float)
        indicators['PCT_SOCIAL_RENT_1991'] = (df[SAS_CODES_1991['SOCIAL_RENT']] / df[SAS_CODES_1991['TOTAL_HH']] * 100).fillna(0)
        
        # Car ownership
        indicators['NO_CAR_HH_1991'] = df[SAS_CODES_1991['NO_CAR']].astype(float)
        indicators['PCT_NO_CAR_1991'] = (df[SAS_CODES_1991['NO_CAR']] / df[SAS_CODES_1991['TOTAL_HH']] * 100).fillna(0)
        indicators['CAR_OWNERSHIP_INDEX_1991'] = 100 - indicators['PCT_NO_CAR_1991']
        
        # Overcrowding
        indicators['OVERCROWD_GT1P5_1991'] = df[SAS_CODES_1991['OVERCROWD_GT1P5']].astype(float)
        indicators['PCT_OVERCROWD_GT1P5_1991'] = (df[SAS_CODES_1991['OVERCROWD_GT1P5']] / df[SAS_CODES_1991['TOTAL_HH']] * 100).fillna(0)
        
        # Amenities
        indicators['NO_BATH_OR_WC_1991'] = df[SAS_CODES_1991['NO_BATH_WC']].astype(float)
        indicators['PCT_NO_BATH_OR_WC_1991'] = (df[SAS_CODES_1991['NO_BATH_WC']] / df[SAS_CODES_1991['TOTAL_HH']] * 100).fillna(0)
        
        logger.info(f"\n✓ Computed {len(indicators.columns) - 1} indicators")
        
    except KeyError as e:
        logger.error(f"✗ SAS code not found in data: {e}")
        logger.error("\nNote: SAS_CODES_1991 dictionary contains PLACEHOLDERS")
        logger.error("These must be verified against actual 1991 SAS documentation")
        sys.exit(1)
    
    # Save indicators
    logger.info(f"\nSaving indicators to {OUTPUT_PATH}...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    indicators.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"  ✓ {len(indicators)} EDs × {len(indicators.columns)} columns")
    
    # Summary statistics
    logger.info(f"\nGenerating summary...")
    summary = pd.DataFrame({
        'indicator': indicators.columns[1:],
        'non_null_count': [indicators[col].notna().sum() for col in indicators.columns[1:]],
        'mean': [indicators[col].mean() for col in indicators.columns[1:]],
        'std': [indicators[col].std() for col in indicators.columns[1:]],
        'min': [indicators[col].min() for col in indicators.columns[1:]],
        'max': [indicators[col].max() for col in indicators.columns[1:]],
    })
    
    with open(SUMMARY_PATH, 'w') as f:
        f.write("INDICATOR SUMMARY STATISTICS (1991)\n")
        f.write("="*80 + "\n\n")
        f.write(summary.to_string(index=False))
        f.write("\n\n")
        f.write(f"Total EDs: {len(indicators)}\n")
        f.write(f"Total indicators computed: {len(indicators.columns) - 1}\n")
    
    logger.info(f"  ✓ Saved summary to {SUMMARY_PATH}")
    
    # Final report
    logger.info("\n" + "="*70)
    logger.info("SUCCESS")
    logger.info("="*70)
    logger.info(f"Output file: {OUTPUT_PATH}")
    logger.info(f"Summary file: {SUMMARY_PATH}")
    logger.info("\nNext steps:")
    logger.info("1. Load boundary shapefile in QGIS (1991 ED boundaries)")
    logger.info("2. Join indicator CSV to boundaries using zoneid")
    logger.info("3. Create choropleth maps")
    logger.info("4. Export to GeoPackage")

if __name__ == "__main__":
    main()
