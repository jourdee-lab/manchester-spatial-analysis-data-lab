#!/usr/bin/env python3
"""
Step 2c: Compute Indicators for 1991 Manchester Wards
=====================================================

Implements Option B (Ward-Level Mapping) for 1991 census data.

1991 census data is available at ward level (34 Manchester wards: 03BNFA, 03BNFB, etc.)
This enables spatial mapping comparable to 1981 ED-level analysis.

Inputs:
  - 1991 raw SAS data: data/raw/s02ews/, s06ews/, s07ews/, s09ews/, s49ews/
  - Indicator configuration: configs/indicators.yml

Outputs:
  - Ward-level indicator table: data/processed/indicators/1991/manchester_wards_1991_indicators.csv
  - District-level summary: data/processed/indicators/1991/manchester_district_1991_indicators.csv
  - Temporal comparison: data/processed/indicators/temporal/manchester_1981_1991_comparison.csv

Key Tables:
  - S02EWS: Demographics (total population, age/sex)
  - S06EWS: Ethnic group (Chinese identification - NEW in 1991)
  - S07EWS: Country of birth (for comparison with 1981 Far East births)
  - S09EWS: Economic position by ethnic group
  - S49EW: Housing by ethnic group (overcrowding, tenure)

Author: FYP Data Pipeline
Date: 2026-02-04
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
from datetime import datetime

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
TEMPORAL_DIR = DATA_DIR / "processed" / "indicators" / "temporal"

# Manchester filter: district = 03BN, wards = 03BNxx (2-letter suffix)
MANCHESTER_DISTRICT = "03BN"
MANCHESTER_WARD_PATTERN = r"^03BN[A-Z]{2}$"  # e.g., 03BNFA, 03BNFB

# 1991 SAS code mappings (from variable lookup)
# Format: 's0XXXXX' (no year prefix, unlike 1981's '81sas...')
SAS_TABLES = {
    "s02ews": {  # Demographics
        "parts": ["s02ews1.csv", "s02ews2.csv", "s02ews3.csv", "s02ews4.csv"],
        "columns": {
            "TOTAL_RES": "s020001",
            "TOTAL_MALE": "s020002",
            "TOTAL_FEMALE": "s020005",
        }
    },
    "s06ews": {  # Ethnic group (PRIMARY - Chinese identification)
        "parts": ["s06ews1.csv", "s06ews2.csv", "s06ews3.csv", "s06ews4.csv"],
        "columns": {
            "TOTAL_ALL_ETHNIC": "s060001",
            "CHINESE_ETHNIC": "s060009",
            "CHINESE_ETHNIC_MALE": "s060021",
            "CHINESE_ETHNIC_FEMALE": "s060033",
            "CHINESE_AGE_0_4": "s060045",
            "CHINESE_AGE_5_15": "s060057",
            "CHINESE_AGE_16_29": "s060069",
            "CHINESE_AGE_30_PENSION": "s060081",
            "CHINESE_PENSIONABLE": "s060093",
            "CHINESE_LIMITING_ILLNESS": "s060105",
        }
    },
    "s07ews": {  # Country of birth
        "parts": ["s07ews1.csv", "s07ews2.csv", "s07ews3.csv", "s07ews4.csv"],
        "columns": {
            "CHINA_BORN_MALE": "s070041",
            "CHINA_BORN_FEMALE": "s070042",
        }
    },
    "s09ews": {  # Economic position by ethnic group
        "parts": ["s09ews1.csv", "s09ews2.csv", "s09ews3.csv", "s09ews4.csv"],
        "columns": {
            "CHINESE_16PLUS": "s090005",
            "CHINESE_ECON_ACTIVE_MALE": "s090017",
            "CHINESE_UNEMPLOYED_MALE": "s090023",
            "CHINESE_ECON_INACTIVE_MALE": "s090029",
            "CHINESE_ECON_ACTIVE_FEMALE": "s090041",
            "CHINESE_UNEMPLOYED_FEMALE": "s090047",
            "CHINESE_ECON_INACTIVE_FEMALE": "s090053",
        }
    },
    "s49ews": {  # Housing by ethnic group
        "parts": ["s49ew1.csv", "s49ew2.csv", "s49ew3.csv", "s49ew4.csv"],
        "columns": {
            "CHINESE_HOUSEHOLDS": "s490005",
            "CHINESE_OVERCROWD_1_1P5": "s490012",
            "CHINESE_OVERCROWD_GT1P5": "s490019",
            "CHINESE_OWNER_OCC": "s490026",
        }
    },
}

# Ward name lookup (Manchester 1991)
WARD_NAMES = {
    "03BNFA": "Ardwick",
    "03BNFB": "Baguley",
    "03BNFC": "Barlow Moor",
    "03BNFD": "Benchill",
    "03BNFE": "Beswick and Clayton",
    "03BNFF": "Blackley",
    "03BNFG": "Bradford",
    "03BNFH": "Brooklands",
    "03BNFJ": "Burnage",
    "03BNFK": "Central",
    "03BNFL": "Charlestown",
    "03BNFM": "Cheetham",
    "03BNFN": "Chorlton",
    "03BNFP": "Crumpsall",
    "03BNFQ": "Didsbury",
    "03BNFR": "Fallowfield",
    "03BNFS": "Gorton North",
    "03BNFT": "Gorton South",
    "03BNFU": "Harpurhey",
    "03BNFV": "Hulme",
    "03BNFW": "Levenshulme",
    "03BNFX": "Lightbowne",
    "03BNFY": "Longsight",
    "03BNFZ": "Moss Side",
    "03BNGA": "Moston",
    "03BNGB": "Newton Heath",
    "03BNGC": "Northenden",
    "03BNGD": "Old Moat",
    "03BNGE": "Rusholme",
    "03BNGF": "Sharston",
    "03BNGG": "Whalley Range",
    "03BNGH": "Withington",
    "03BNGJ": "Woodhouse Park",
}

# =====================================================================
# DATA LOADING FUNCTIONS
# =====================================================================

def load_sas_table(table_name: str) -> pd.DataFrame:
    """
    Load a 1991 SAS table from multiple parts and filter to Manchester wards.
    
    Args:
        table_name: Name of the SAS table (e.g., 's06ews')
    
    Returns:
        DataFrame with Manchester ward-level data
    """
    table_config = SAS_TABLES.get(table_name)
    if not table_config:
        logger.warning(f"  Unknown table: {table_name}")
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
                logger.debug(f"    Loaded {part_file}: {len(df)} rows")
            except Exception as e:
                logger.warning(f"    Error loading {part_file}: {e}")
    
    if not dfs:
        logger.warning(f"  No data loaded for {table_name}")
        return pd.DataFrame()
    
    # Combine all parts
    combined = pd.concat(dfs, ignore_index=True)
    
    # Ensure zoneid is string and strip whitespace
    combined['zoneid'] = combined['zoneid'].astype(str).str.strip()
    
    # Filter to Manchester wards (6-character codes: 03BNxx)
    ward_mask = combined['zoneid'].str.match(MANCHESTER_WARD_PATTERN)
    manchester_wards = combined[ward_mask].copy()
    
    logger.info(f"  {table_name}: {len(manchester_wards)} Manchester wards loaded")
    
    return manchester_wards


def load_all_tables() -> dict:
    """
    Load all required SAS tables for 1991 Manchester analysis.
    
    Returns:
        Dictionary of table_name -> DataFrame
    """
    logger.info("Loading 1991 SAS tables...")
    
    tables = {}
    for table_name in SAS_TABLES.keys():
        tables[table_name] = load_sas_table(table_name)
    
    return tables


def merge_tables(tables: dict) -> pd.DataFrame:
    """
    Merge all SAS tables on zoneid to create a single ward-level dataset.
    
    Args:
        tables: Dictionary of table_name -> DataFrame
    
    Returns:
        Merged DataFrame with all indicators per ward
    """
    logger.info("Merging tables...")
    
    # Start with demographics (s02ews) as the base
    base = tables.get('s02ews')
    if base is None or base.empty:
        logger.error("  No base table (s02ews) available!")
        return pd.DataFrame()
    
    merged = base.copy()
    
    # Merge other tables
    for table_name, df in tables.items():
        if table_name == 's02ews' or df.empty:
            continue
        
        # Keep only the columns we need plus zoneid
        cols_needed = list(SAS_TABLES[table_name]["columns"].values())
        cols_to_merge = ['zoneid'] + [c for c in cols_needed if c in df.columns]
        
        if len(cols_to_merge) > 1:
            df_subset = df[cols_to_merge].drop_duplicates(subset=['zoneid'])
            merged = merged.merge(df_subset, on='zoneid', how='left', suffixes=('', f'_{table_name}'))
            logger.info(f"  Merged {table_name}: {len(cols_to_merge)-1} columns")
    
    logger.info(f"  Final merged dataset: {len(merged)} wards × {len(merged.columns)} columns")
    
    return merged


# =====================================================================
# INDICATOR COMPUTATION
# =====================================================================

def compute_ward_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived indicators for each Manchester ward.
    
    Args:
        df: Merged ward-level census data
    
    Returns:
        DataFrame with computed indicators
    """
    logger.info("Computing ward-level indicators...")
    
    # Ensure column names are lowercase for consistent access
    df.columns = [c.lower() for c in df.columns]
    
    results = []
    
    for _, row in df.iterrows():
        ward_id = row['zoneid']
        ward_name = WARD_NAMES.get(ward_id, "Unknown")
        
        indicators = {
            'zoneid': ward_id,
            'ward_name': ward_name,
            'year': 1991,
            'geography_level': 'ward',
        }
        
        # === DEMOGRAPHICS ===
        total_res = row.get('s020001', np.nan)
        total_male = row.get('s020002', np.nan)
        total_female = row.get('s020005', np.nan)
        
        indicators['TOTAL_RES_1991'] = total_res
        indicators['TOTAL_MALE_1991'] = total_male
        indicators['TOTAL_FEMALE_1991'] = total_female
        
        if pd.notna(total_res) and total_res > 0:
            indicators['PCT_MALE_1991'] = 100 * total_male / total_res if pd.notna(total_male) else np.nan
            indicators['PCT_FEMALE_1991'] = 100 * total_female / total_res if pd.notna(total_female) else np.nan
        else:
            indicators['PCT_MALE_1991'] = np.nan
            indicators['PCT_FEMALE_1991'] = np.nan
        
        # === CHINESE ETHNIC GROUP (PRIMARY - direct identification) ===
        chinese_ethnic = row.get('s060009', np.nan)
        chinese_male = row.get('s060021', np.nan)
        chinese_female = row.get('s060033', np.nan)
        
        indicators['CHINESE_ETHNIC_1991'] = chinese_ethnic
        indicators['CHINESE_ETHNIC_MALE_1991'] = chinese_male
        indicators['CHINESE_ETHNIC_FEMALE_1991'] = chinese_female
        
        if pd.notna(total_res) and total_res > 0 and pd.notna(chinese_ethnic):
            indicators['PCT_CHINESE_ETHNIC_1991'] = 100 * chinese_ethnic / total_res
        else:
            indicators['PCT_CHINESE_ETHNIC_1991'] = np.nan
        
        # Chinese age structure
        indicators['CHINESE_AGE_0_4_1991'] = row.get('s060045', np.nan)
        indicators['CHINESE_AGE_5_15_1991'] = row.get('s060057', np.nan)
        indicators['CHINESE_AGE_16_29_1991'] = row.get('s060069', np.nan)
        indicators['CHINESE_AGE_30_PENSION_1991'] = row.get('s060081', np.nan)
        indicators['CHINESE_PENSIONABLE_1991'] = row.get('s060093', np.nan)
        indicators['CHINESE_LIMITING_ILLNESS_1991'] = row.get('s060105', np.nan)
        
        # === COUNTRY OF BIRTH (for comparison with 1981) ===
        china_born_male = row.get('s070041', np.nan)
        china_born_female = row.get('s070042', np.nan)
        
        if pd.notna(china_born_male) and pd.notna(china_born_female):
            china_born_total = china_born_male + china_born_female
        elif pd.notna(china_born_male):
            china_born_total = china_born_male
        elif pd.notna(china_born_female):
            china_born_total = china_born_female
        else:
            china_born_total = np.nan
        
        indicators['CHINA_BORN_1991'] = china_born_total
        indicators['CHINA_BORN_MALE_1991'] = china_born_male
        indicators['CHINA_BORN_FEMALE_1991'] = china_born_female
        
        if pd.notna(total_res) and total_res > 0 and pd.notna(china_born_total):
            indicators['PCT_CHINA_BORN_1991'] = 100 * china_born_total / total_res
        else:
            indicators['PCT_CHINA_BORN_1991'] = np.nan
        
        # === ECONOMIC POSITION (Chinese-specific) ===
        chinese_16plus = row.get('s090005', np.nan)
        econ_active_m = row.get('s090017', np.nan)
        econ_active_f = row.get('s090041', np.nan)
        unemployed_m = row.get('s090023', np.nan)
        unemployed_f = row.get('s090047', np.nan)
        
        indicators['CHINESE_16PLUS_1991'] = chinese_16plus
        
        # Total economically active
        if pd.notna(econ_active_m) and pd.notna(econ_active_f):
            chinese_econ_active = econ_active_m + econ_active_f
        else:
            chinese_econ_active = np.nan
        indicators['CHINESE_ECON_ACTIVE_1991'] = chinese_econ_active
        
        # Total unemployed
        if pd.notna(unemployed_m) and pd.notna(unemployed_f):
            chinese_unemployed = unemployed_m + unemployed_f
        else:
            chinese_unemployed = np.nan
        indicators['CHINESE_UNEMPLOYED_1991'] = chinese_unemployed
        
        # Economic rates
        if pd.notna(chinese_16plus) and chinese_16plus > 0:
            if pd.notna(chinese_econ_active):
                indicators['CHINESE_EMP_RATE_1991'] = 100 * chinese_econ_active / chinese_16plus
            else:
                indicators['CHINESE_EMP_RATE_1991'] = np.nan
            
            if pd.notna(chinese_unemployed):
                indicators['CHINESE_UNEMP_RATE_1991'] = 100 * chinese_unemployed / chinese_16plus
            else:
                indicators['CHINESE_UNEMP_RATE_1991'] = np.nan
        else:
            indicators['CHINESE_EMP_RATE_1991'] = np.nan
            indicators['CHINESE_UNEMP_RATE_1991'] = np.nan
        
        # === HOUSING (Chinese-specific) ===
        chinese_hh = row.get('s490005', np.nan)
        chinese_overcrowd = row.get('s490019', np.nan)
        chinese_owner = row.get('s490026', np.nan)
        
        indicators['CHINESE_HOUSEHOLDS_1991'] = chinese_hh
        indicators['CHINESE_OVERCROWD_GT1P5_1991'] = chinese_overcrowd
        indicators['CHINESE_OWNER_OCC_1991'] = chinese_owner
        
        if pd.notna(chinese_hh) and chinese_hh > 0:
            if pd.notna(chinese_overcrowd):
                indicators['PCT_CHINESE_OVERCROWD_1991'] = 100 * chinese_overcrowd / chinese_hh
            else:
                indicators['PCT_CHINESE_OVERCROWD_1991'] = np.nan
            
            if pd.notna(chinese_owner):
                indicators['PCT_CHINESE_OWNER_OCC_1991'] = 100 * chinese_owner / chinese_hh
            else:
                indicators['PCT_CHINESE_OWNER_OCC_1991'] = np.nan
        else:
            indicators['PCT_CHINESE_OVERCROWD_1991'] = np.nan
            indicators['PCT_CHINESE_OWNER_OCC_1991'] = np.nan
        
        results.append(indicators)
    
    result_df = pd.DataFrame(results)
    logger.info(f"  Computed {len(result_df)} ward indicator records")
    
    return result_df


def compute_district_summary(ward_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate ward-level indicators to Manchester district total.
    
    Args:
        ward_df: Ward-level indicators
    
    Returns:
        Single-row DataFrame with district-level indicators
    """
    logger.info("Computing district summary...")
    
    # Columns to sum (raw counts)
    sum_cols = [c for c in ward_df.columns if c.endswith('_1991') and not c.startswith('PCT_') and not c.startswith('CHINESE_EMP') and not c.startswith('CHINESE_UNEMP')]
    sum_cols = [c for c in sum_cols if c not in ['zoneid', 'ward_name', 'year', 'geography_level']]
    
    district = {
        'zoneid': MANCHESTER_DISTRICT,
        'ward_name': 'Manchester (District Total)',
        'year': 1991,
        'geography_level': 'district',
    }
    
    # Sum numeric columns
    for col in sum_cols:
        if col in ward_df.columns:
            district[col] = ward_df[col].sum()
    
    # Recompute rates from totals
    total_res = district.get('TOTAL_RES_1991', 0)
    if total_res > 0:
        district['PCT_MALE_1991'] = 100 * district.get('TOTAL_MALE_1991', 0) / total_res
        district['PCT_FEMALE_1991'] = 100 * district.get('TOTAL_FEMALE_1991', 0) / total_res
        district['PCT_CHINESE_ETHNIC_1991'] = 100 * district.get('CHINESE_ETHNIC_1991', 0) / total_res
        district['PCT_CHINA_BORN_1991'] = 100 * district.get('CHINA_BORN_1991', 0) / total_res
    
    chinese_16plus = district.get('CHINESE_16PLUS_1991', 0)
    if chinese_16plus > 0:
        district['CHINESE_EMP_RATE_1991'] = 100 * district.get('CHINESE_ECON_ACTIVE_1991', 0) / chinese_16plus
        district['CHINESE_UNEMP_RATE_1991'] = 100 * district.get('CHINESE_UNEMPLOYED_1991', 0) / chinese_16plus
    
    chinese_hh = district.get('CHINESE_HOUSEHOLDS_1991', 0)
    if chinese_hh > 0:
        district['PCT_CHINESE_OVERCROWD_1991'] = 100 * district.get('CHINESE_OVERCROWD_GT1P5_1991', 0) / chinese_hh
        district['PCT_CHINESE_OWNER_OCC_1991'] = 100 * district.get('CHINESE_OWNER_OCC_1991', 0) / chinese_hh
    
    return pd.DataFrame([district])


# =====================================================================
# TEMPORAL COMPARISON
# =====================================================================

def create_temporal_comparison(district_1991: pd.DataFrame) -> pd.DataFrame:
    """
    Create temporal comparison between 1981 and 1991.
    
    For Option B (ward-level), we aggregate 1981 ED data to district level
    to compare with 1991 district totals.
    
    Args:
        district_1991: 1991 district-level indicators
    
    Returns:
        Comparison DataFrame
    """
    logger.info("Creating temporal comparison (1981 vs 1991)...")
    
    # Load 1981 ward indicators
    indicators_1981_path = DATA_DIR / "processed" / "indicators" / "1981" / "manchester_eds_1981_indicators.csv"
    
    if not indicators_1981_path.exists():
        logger.warning(f"  1981 indicators not found: {indicators_1981_path}")
        return pd.DataFrame()
    
    df_1981 = pd.read_csv(indicators_1981_path)
    logger.info(f"  Loaded 1981 indicators: {len(df_1981)} EDs")
    
    # Aggregate 1981 EDs to district level
    district_1981 = {
        'zoneid': MANCHESTER_DISTRICT,
        'year': 1981,
    }
    
    # Sum key indicators
    sum_cols_1981 = ['TOTAL_RES_1981', 'CHINESE_BORN_1981', 'CHINESE_BORN_MALE_1981', 'CHINESE_BORN_FEMALE_1981',
                     'TOTAL_HH_1981', 'OWNER_OCC_HH_1981', 'NO_CAR_HH_1981', 'OVERCROWD_GT1P5_1981']
    
    for col in sum_cols_1981:
        if col in df_1981.columns:
            district_1981[col] = df_1981[col].sum()
    
    # Compute rates
    total_res_1981 = district_1981.get('TOTAL_RES_1981', 0)
    if total_res_1981 > 0:
        district_1981['PCT_CHINESE_BORN_1981'] = 100 * district_1981.get('CHINESE_BORN_1981', 0) / total_res_1981
    
    total_hh_1981 = district_1981.get('TOTAL_HH_1981', 0)
    if total_hh_1981 > 0:
        district_1981['PCT_OWNER_OCC_1981'] = 100 * district_1981.get('OWNER_OCC_HH_1981', 0) / total_hh_1981
        district_1981['PCT_NO_CAR_1981'] = 100 * district_1981.get('NO_CAR_HH_1981', 0) / total_hh_1981
        district_1981['PCT_OVERCROWD_1981'] = 100 * district_1981.get('OVERCROWD_GT1P5_1981', 0) / total_hh_1981
    
    # Build comparison
    comparison = {
        'zoneid': MANCHESTER_DISTRICT,
        'geography_name': 'Manchester',
        
        # Population
        'TOTAL_RES_1981': district_1981.get('TOTAL_RES_1981'),
        'TOTAL_RES_1991': district_1991['TOTAL_RES_1991'].iloc[0],
        'POP_CHANGE_PCT': None,  # Computed below
        
        # Chinese presence (1981: country of birth proxy; 1991: ethnic group direct)
        'CHINESE_BORN_1981': district_1981.get('CHINESE_BORN_1981'),
        'CHINESE_ETHNIC_1991': district_1991['CHINESE_ETHNIC_1991'].iloc[0],
        'PCT_CHINESE_1981': district_1981.get('PCT_CHINESE_BORN_1981'),
        'PCT_CHINESE_1991': district_1991['PCT_CHINESE_ETHNIC_1991'].iloc[0],
        
        # China-born (comparable measure)
        'CHINA_BORN_1991': district_1991['CHINA_BORN_1991'].iloc[0],
        'PCT_CHINA_BORN_1991': district_1991['PCT_CHINA_BORN_1991'].iloc[0],
        
        # Housing (general population)
        'TOTAL_HH_1981': district_1981.get('TOTAL_HH_1981'),
        'PCT_OWNER_OCC_1981': district_1981.get('PCT_OWNER_OCC_1981'),
        'PCT_NO_CAR_1981': district_1981.get('PCT_NO_CAR_1981'),
        'PCT_OVERCROWD_1981': district_1981.get('PCT_OVERCROWD_1981'),
        
        # Chinese-specific housing (1991 only)
        'CHINESE_HOUSEHOLDS_1991': district_1991['CHINESE_HOUSEHOLDS_1991'].iloc[0],
        'PCT_CHINESE_OWNER_OCC_1991': district_1991['PCT_CHINESE_OWNER_OCC_1991'].iloc[0],
        'PCT_CHINESE_OVERCROWD_1991': district_1991['PCT_CHINESE_OVERCROWD_1991'].iloc[0],
    }
    
    # Compute changes
    if comparison['TOTAL_RES_1981'] and comparison['TOTAL_RES_1981'] > 0:
        comparison['POP_CHANGE_PCT'] = 100 * (comparison['TOTAL_RES_1991'] - comparison['TOTAL_RES_1981']) / comparison['TOTAL_RES_1981']
    
    result = pd.DataFrame([comparison])
    logger.info(f"  Temporal comparison created")
    
    return result


# =====================================================================
# MAIN EXECUTION
# =====================================================================

def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Phase 7: 1991 Manchester Ward Indicator Computation")
    logger.info("=" * 60)
    
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPORAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load all SAS tables
    tables = load_all_tables()
    
    # Check we have data
    if not tables.get('s02ews') is None and tables['s02ews'].empty:
        logger.error("No demographic data loaded. Exiting.")
        return
    
    # Step 2: Merge tables
    merged = merge_tables(tables)
    
    if merged.empty:
        logger.error("Failed to merge tables. Exiting.")
        return
    
    # Step 3: Compute ward-level indicators
    ward_indicators = compute_ward_indicators(merged)
    
    # Step 4: Save ward-level output
    ward_output_path = OUTPUT_DIR / "manchester_wards_1991_indicators.csv"
    ward_indicators.to_csv(ward_output_path, index=False)
    logger.info(f"✓ Ward indicators saved: {ward_output_path}")
    
    # Step 5: Compute district summary
    district_summary = compute_district_summary(ward_indicators)
    
    district_output_path = OUTPUT_DIR / "manchester_district_1991_indicators.csv"
    district_summary.to_csv(district_output_path, index=False)
    logger.info(f"✓ District summary saved: {district_output_path}")
    
    # Step 6: Create temporal comparison
    temporal = create_temporal_comparison(district_summary)
    
    if not temporal.empty:
        temporal_path = TEMPORAL_DIR / "manchester_1981_1991_comparison.csv"
        temporal.to_csv(temporal_path, index=False)
        logger.info(f"✓ Temporal comparison saved: {temporal_path}")
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Wards processed: {len(ward_indicators)}")
    logger.info(f"Indicators computed: {len([c for c in ward_indicators.columns if c.endswith('_1991')])}")
    
    # Key stats
    if 'CHINESE_ETHNIC_1991' in district_summary.columns:
        chinese_total = district_summary['CHINESE_ETHNIC_1991'].iloc[0]
        chinese_pct = district_summary.get('PCT_CHINESE_ETHNIC_1991', pd.Series([np.nan])).iloc[0]
        logger.info(f"Manchester Chinese population (1991): {chinese_total:,.0f} ({chinese_pct:.2f}%)")
    
    if 'TOTAL_RES_1991' in district_summary.columns:
        total_pop = district_summary['TOTAL_RES_1991'].iloc[0]
        logger.info(f"Manchester total population (1991): {total_pop:,.0f}")
    
    logger.info("")
    logger.info("Phase 7 complete!")


if __name__ == "__main__":
    main()
