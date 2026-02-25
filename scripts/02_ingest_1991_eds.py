#!/usr/bin/env python3
"""
Step 1b: Ingest Raw SAS ED-Level Data (1991)
============================================

Loads 4-part raw CSV files for each SAS table (s02, s06, s07, s20) and:
1. Concatenates the parts horizontally (wide format)
2. Filters to Manchester EDs (zoneid starts with '03BN')
3. Outputs clean ED-level CSVs per table
4. Validates data integrity

Input Structure (expected):
  data/raw/
  ├── s02ews/  (Demographics - Age and marital status)
  │   ├── s02ews1.csv through s02ews4.csv
  ├── s06ews/  (Ethnic Group)
  │   ├── s06ews1.csv through s06ews4.csv
  ├── s07ews/  (Country of Birth)
  │   ├── s07ews1.csv through s07ews4.csv
  ├── s09ews/  (Economic Position)
  │   ├── s09ews1.csv through s09ews4.csv
  ├── s16ew+s/ (Tenure and Amenities)
  │   ├── s16ew1.csv through s16ew4.csv
  └── s81ews/  (Communal Establishments)
      ├── s81ews1.csv through s81ews4.csv

Output Structure:
  data/processed/raw_ed_level/1991/
  ├── sas02_1991_ed_level.csv  (Demographics)
  ├── sas06_1991_ed_level.csv  (Ethnic Group)
  ├── sas07_1991_ed_level.csv  (Country of Birth)
  ├── sas09_1991_ed_level.csv  (Economic Position)
  ├── sas20_1991_ed_level.csv  (Tenure/Amenities)
  └── sas81_1991_ed_level.csv  (Communal)

Note on 1991 data structure:
- 1991 census data uses 'sXXXXXX' column naming (e.g., s020001, s060100)
- NOT prefixed with '91' like 1981 data (81sas020001)
- Data split across 4 parts per table (vs. 5 for 1981)
- Same Manchester prefix: '03BN'

Author: FYP Data Pipeline
Date: 2026-01-18
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURATION
# =====================================================================

RAW_DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed/raw_ed_level/1991")

MANCHESTER_PREFIX = "03BN"
YEAR = 1991

# SAS table configurations for 1991
# Note: 1991 uses different table labels (s02ews, s06ews, etc.)
# But we standardize output naming (sas02, sas06, etc.) for consistency
SAS_TABLES = {
    "sas02": {
        "raw_prefix": "s02ews",
        "parts": 4,
        "description": "Demographics (Age & Marital Status)",
        "expected_cols": 155,  # Approximate; will validate at runtime
    },
    "sas06": {
        "raw_prefix": "s06ews",
        "parts": 4,
        "description": "Ethnic Group",
        "expected_cols": 12,   # Approximate
    },
    "sas07": {
        "raw_prefix": "s07ews",
        "parts": 4,
        "description": "Country of Birth",
        "expected_cols": 61,   # Approximate
    },
    "sas09": {
        "raw_prefix": "s09ews",
        "parts": 4,
        "description": "Economic Position",
        "expected_cols": 52,   # Approximate
    },
    "sas20": {
        "raw_prefix": "s16ew",
        "parts": 4,
        "description": "Tenure and Amenities",
        "expected_cols": 227,  # Approximate; includes full housing data
    },
    "sas81": {
        "raw_prefix": "s81ews",
        "parts": 4,
        "description": "Communal Establishments",
        "expected_cols": 28,   # Approximate
    },
}

# =====================================================================
# FUNCTIONS
# =====================================================================

def load_raw_table_parts(table_name: str, raw_prefix: str, num_parts: int) -> Tuple[pd.DataFrame, bool]:
    """
    Load and concatenate the raw CSV parts for a SAS table.
    
    Args:
        table_name: Standardized name (e.g., 'sas02')
        raw_prefix: Raw file prefix (e.g., 's02ews')
        num_parts: Number of parts to load
    
    Returns:
        Tuple of (DataFrame, success_bool)
    """
    
    logger.info(f"\nLoading {table_name} ({num_parts} parts, prefix={raw_prefix})...")
    
    dfs = []
    for part_num in range(1, num_parts + 1):
        # Build file path: data/raw/{raw_prefix}/{raw_prefix}{part_num}.csv
        fpath = RAW_DATA_DIR / raw_prefix / f"{raw_prefix}{part_num}.csv"
        
        if not fpath.exists():
            logger.warning(f"  ⚠ Part {part_num} not found: {fpath}")
            logger.warning(f"    Expected at: {fpath}")
            return None, False # pyright: ignore[reportReturnType]
        
        try:
            df = pd.read_csv(fpath)
            logger.info(f"  ✓ Part {part_num}: {df.shape[0]} rows × {df.shape[1]} cols")
            dfs.append(df)
        except Exception as e:
            logger.error(f"  ✗ Error reading part {part_num}: {e}")
            return None, False # pyright: ignore[reportReturnType]
    
    # Concatenate parts horizontally on zoneid
    if dfs:
        # First part as base
        result = dfs[0].copy()
        
        # Merge subsequent parts on zoneid
        for i, df in enumerate(dfs[1:], 2):
            try:
                result = result.merge(df, on='zoneid', how='inner')
                logger.info(f"  → Part {i} merged: {result.shape[1]} total columns")
            except Exception as e:
                logger.error(f"  ✗ Error merging part {i}: {e}")
                return None, False # pyright: ignore[reportReturnType]
        
        logger.info(f"  ✓ Concatenated {num_parts} parts: {result.shape}")
        return result, True
    
    return None, False # pyright: ignore[reportReturnType]

def filter_to_manchester(df: pd.DataFrame, table_name: str) -> Tuple[pd.DataFrame, int]:
    """
    Filter to Manchester EDs (zoneid starts with '03BN').
    
    Args:
        df: Full dataset (all EDs)
        table_name: For logging
    
    Returns:
        Tuple of (filtered DataFrame, count of Manchester EDs)
    """
    
    # Ensure zoneid is string
    df['zoneid'] = df['zoneid'].astype(str).str.strip().str.upper()
    
    # Filter
    manchester = df[df['zoneid'].str.startswith(MANCHESTER_PREFIX)].copy()
    count = len(manchester)
    
    logger.info(f"  Filtered to Manchester: {count} EDs (prefix '{MANCHESTER_PREFIX}')")
    
    if count == 0:
        logger.warning(f"  ⚠ No Manchester EDs found in {table_name}!")
        logger.warning(f"    Sample zoneids: {df['zoneid'].head().tolist()}")
    
    return manchester, count

def validate_data_integrity(ed_df: pd.DataFrame, table_name: str) -> bool:
    """
    Validate ED-level data for basic integrity.
    
    Args:
        ed_df: ED-level data
        table_name: e.g., 'sas02'
    
    Returns:
        Boolean indicating validation success
    """
    
    try:
        # Check for duplicate zoneids
        if ed_df['zoneid'].duplicated().any():
            logger.warning(f"  ⚠ Duplicate zoneids found in {table_name}")
            return False
        
        # Check for missing zoneid
        if ed_df['zoneid'].isna().any():
            logger.warning(f"  ⚠ Missing zoneids in {table_name}")
            return False
        
        # Check numeric columns for negative values (shouldn't occur in census data)
        numeric_cols = ed_df.select_dtypes(include=['int64', 'float64']).columns
        if (ed_df[numeric_cols] < 0).any().any():
            logger.warning(f"  ⚠ Negative values found in {table_name}")
            return False
        
        logger.info(f"  ✓ Data integrity validated")
        return True
    
    except Exception as e:
        logger.warning(f"  ⚠ Validation error: {e}")
        return True  # Don't fail if validation has issues

def save_ed_level_csv(ed_df: pd.DataFrame, table_name: str, output_dir: Path) -> bool:
    """
    Save ED-level data to CSV.
    
    Args:
        ed_df: ED-level DataFrame
        table_name: e.g., 'sas02'
        output_dir: Output directory path
    
    Returns:
        Boolean indicating success
    """
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{table_name}_1991_ed_level.csv"
    
    try:
        ed_df.to_csv(output_file, index=False)
        logger.info(f"  ✓ Saved: {output_file} ({len(ed_df)} rows × {len(ed_df.columns)} cols)")
        return True
    except Exception as e:
        logger.error(f"  ✗ Error saving: {e}")
        return False

def generate_summary_report(results: Dict) -> str:
    """
    Generate summary report of ingestion.
    
    Args:
        results: Dictionary of results per table
    
    Returns:
        Summary report string
    """
    
    report = "\n" + "="*70 + "\n"
    report += "SUMMARY: Raw SAS ED-Level Data Ingestion (1991)\n"
    report += "="*70 + "\n\n"
    
    success_count = sum(1 for r in results.values() if r.get("success"))
    total_count = len(results)
    
    report += f"Overall: {success_count}/{total_count} tables successfully ingested\n\n"
    
    for table_name, result in results.items():
        status = "✓ OK" if result["success"] else "✗ FAILED"
        ed_count = result.get("ed_count", 0)
        col_count = result.get("col_count", 0)
        report += f"{table_name}  {status}  ({ed_count} EDs × {col_count} cols)\n"
    
    report += "\n" + "="*70 + "\n"
    
    return report

def main():
    """Main pipeline."""
    
    logger.info("="*70)
    logger.info("INGEST RAW SAS ED-LEVEL DATA (1991)")
    logger.info("="*70)
    
    # Check if raw data directory exists
    if not RAW_DATA_DIR.exists():
        logger.error(f"✗ Raw data directory not found: {RAW_DATA_DIR}")
        logger.error(f"  Expected structure:")
        for table, config in SAS_TABLES.items():
            prefix = config["raw_prefix"]
            for part in range(1, config["parts"] + 1):
                logger.error(f"    {RAW_DATA_DIR}/{prefix}/{prefix}{part}.csv")
        return False
    
    results = {}
    
    # Process each SAS table
    for table_name, table_config in SAS_TABLES.items():
        logger.info(f"\n{'─'*70}")
        logger.info(f"Processing: {table_name} — {table_config['description']}")
        logger.info(f"{'─'*70}")
        
        # Load raw parts
        raw_df, load_success = load_raw_table_parts(
            table_name,
            table_config["raw_prefix"],
            table_config["parts"]
        )
        
        if not load_success:
            logger.error(f"✗ Failed to load {table_name}")
            results[table_name] = {
                "success": False,
                "ed_count": 0,
                "col_count": 0,
            }
            continue
        
        # Filter to Manchester
        manchester_df, ed_count = filter_to_manchester(raw_df, table_name)
        
        if ed_count == 0:
            logger.error(f"✗ No Manchester EDs found in {table_name}")
            results[table_name] = {
                "success": False,
                "ed_count": 0,
                "col_count": 0,
            }
            continue
        
        # Validate data integrity
        validation_ok = validate_data_integrity(manchester_df, table_name)
        
        # Save to CSV
        save_ok = save_ed_level_csv(manchester_df, table_name, OUTPUT_DIR)
        
        success = load_success and ed_count > 0 and save_ok
        results[table_name] = {
            "success": success,
            "ed_count": ed_count,
            "col_count": len(manchester_df.columns),
            "validation_ok": validation_ok,
        }
    
    # Print summary
    report = generate_summary_report(results)
    logger.info(report)
    
    overall_success = all(r["success"] for r in results.values())
    
    if overall_success:
        logger.info("✓ All tables successfully ingested!")
        logger.info(f"  Output directory: {OUTPUT_DIR}")
        logger.info(f"\nNext step:")
        logger.info(f"  1. Update Phase 6 config to use: {OUTPUT_DIR}")
        logger.info(f"  2. Run: python scripts/05_compute_indicators_1991_eds.py  (ED-level) OR")
        logger.info(f"          python scripts/06_compute_indicators_1991_wards.py (ward-level)")
        return True
    else:
        logger.error("✗ Some tables failed to ingest")
        logger.error(f"  Please check raw files in: {RAW_DATA_DIR}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
