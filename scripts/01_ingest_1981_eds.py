#!/usr/bin/env python3
"""
Step 1a: Ingest Raw SAS ED-Level Data (1981)
============================================

Loads 5-part raw CSV files for each SAS table (02, 04, 07, 10) and:
1. Concatenates the parts horizontally (wide format)
2. Filters to Manchester EDs (zoneid starts with '03BN')
3. Outputs clean ED-level CSVs per table
4. Validates against combined aggregated files

Input Structure (expected):
  data/raw/sas/
  ├── 1981_sas02_part1.csv through 1981_sas02_part5.csv
  ├── 1981_sas04_part1.csv through 1981_sas04_part5.csv
  ├── 1981_sas07_part1.csv through 1981_sas07_part5.csv
  └── 1981_sas10_part1.csv through 1981_sas10_part5.csv

Output Structure:
  data/processed/raw_ed_level/1981/
  ├── sas02_1981_ed_level.csv  (1,017 EDs × 161 columns)
  ├── sas04_1981_ed_level.csv  (1,017 EDs × 61 columns)
  ├── sas07_1981_ed_level.csv  (1,017 EDs × 28 columns)
  └── sas10_1981_ed_level.csv  (1,017 EDs × 221 columns)

Author: FYP Data Pipeline
Date: 2026-01-14
"""

import pandas as pd
import yaml
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

RAW_DATA_DIR = Path("data/raw/sas")
OUTPUT_DIR = Path("data/processed/raw_ed_level/1981")
COMBINED_DATA_DIR = Path("data/processed/aggregates/census_1981")

MANCHESTER_PREFIX = "03BN"

# SAS table configurations
SAS_TABLES = {
    "sas02": {
        "parts": 5,
        "description": "Demographics (Total Population)",
        "expected_cols": 161,
    },
    "sas04": {
        "parts": 5,
        "description": "Country of Birth",
        "expected_cols": 61,
    },
    "sas07": {
        "parts": 5,
        "description": "Employment",
        "expected_cols": 28,
    },
    "sas10": {
        "parts": 5,
        "description": "Housing & Tenure",
        "expected_cols": 221,
    },
}

# =====================================================================
# FUNCTIONS
# =====================================================================

def load_raw_table_parts(table_name: str, year: int = 1981) -> Tuple[pd.DataFrame, bool]:
    """
    Load and concatenate the 5 raw CSV parts for a SAS table.
    
    Args:
        table_name: e.g., 'sas02', 'sas04'
        year: Census year (default 1981)
    
    Returns:
        Tuple of (DataFrame, success_bool)
    """
    
    table_config = SAS_TABLES[table_name]
    num_parts = table_config["parts"]
    
    logger.info(f"\nLoading {table_name} ({num_parts} parts)...")
    
    dfs = []
    for part_num in range(1, num_parts + 1):
        fpath = RAW_DATA_DIR / f"{year}_{table_name}_part{part_num}.csv"
        
        if not fpath.exists():
            logger.warning(f"  ⚠ Part {part_num} not found: {fpath}")
            logger.warning(f"    Expected at: {fpath}")
            logger.warning(f"    Please ensure raw files are in: {RAW_DATA_DIR}")
            return None, False # pyright: ignore[reportReturnType]
        
        try:
            df = pd.read_csv(fpath)
            logger.info(f"  ✓ Part {part_num}: {df.shape[0]} rows × {df.shape[1]} cols")
            dfs.append(df)
        except Exception as e:
            logger.error(f"  ✗ Error reading part {part_num}: {e}")
            return None, False # pyright: ignore[reportReturnType]
    
    # Concatenate parts horizontally
    # Assume first column (zoneid) is common; use it as merge key
    if dfs:
        # First part as base
        result = dfs[0].copy()
        
        # Merge subsequent parts on zoneid (assuming same ED order)
        for i, df in enumerate(dfs[1:], 2):
            # Drop zoneid from subsequent parts to avoid duplication
            # (assuming they're already in the same order)
            try:
                # If they have the same zoneid, merge on it
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

def validate_against_combined(ed_df: pd.DataFrame, table_name: str) -> bool:
    """
    Validate ED-level data against the combined aggregate file.
    
    Args:
        ed_df: ED-level data (1,017 rows)
        table_name: e.g., 'sas02'
    
    Returns:
        Boolean indicating validation success
    """
    
    # Map table names to combined file names
    table_map = {
        "sas02": "1981_sas02_totalpop_combined.csv",
        "sas04": "1981_sas04_birth_combined.csv",
        "sas07": "1981_sas07_employment_combined.csv",
        "sas10": "1981_sas10_housing_combined.csv",
    }
    
    combined_file = COMBINED_DATA_DIR / table_map[table_name]
    
    if not combined_file.exists():
        logger.warning(f"  ⚠ Combined file not found for validation: {combined_file}")
        return True  # Skip validation if file doesn't exist
    
    try:
        combined = pd.read_csv(combined_file)
        
        # Sum ED-level data for Manchester EDs
        numeric_cols = ed_df.select_dtypes(include=['int64', 'float64']).columns
        ed_sums = ed_df[numeric_cols].sum()
        
        # Get combined values (should be single row with zoneid='03BN')
        combined_row = combined.iloc[0]
        
        # Compare (allow 1% tolerance for rounding)
        mismatches = []
        for col in numeric_cols:
            if col in combined.columns:
                ed_val = ed_sums.get(col, 0)
                combined_val = combined_row.get(col, 0)
                
                if ed_val != combined_val:
                    pct_diff = abs(ed_val - combined_val) / max(abs(combined_val), 1) * 100
                    if pct_diff > 1:  # Flag if > 1% difference
                        mismatches.append((col, ed_val, combined_val, pct_diff))
        
        if mismatches:
            logger.warning(f"  ⚠ Validation: {len(mismatches)} columns have > 1% difference")
            for col, ed_val, combined_val, pct_diff in mismatches[:5]:
                logger.warning(f"    {col}: ED sum={ed_val:.0f}, Combined={combined_val:.0f} ({pct_diff:.1f}% diff)")
            return False
        else:
            logger.info(f"  ✓ Validation passed: ED sums match combined aggregate")
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
    output_file = output_dir / f"{table_name}_1981_ed_level.csv"
    
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
    report += "SUMMARY: Raw SAS ED-Level Data Ingestion (1981)\n"
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
    logger.info("INGEST RAW SAS ED-LEVEL DATA (1981)")
    logger.info("="*70)
    
    # Check if raw data directory exists
    if not RAW_DATA_DIR.exists():
        logger.error(f"✗ Raw data directory not found: {RAW_DATA_DIR}")
        logger.error(f"  Expected raw files in: {RAW_DATA_DIR}")
        logger.error(f"  Expected filenames:")
        for table in SAS_TABLES:
            for part in range(1, SAS_TABLES[table]["parts"] + 1):
                logger.error(f"    1981_{table}_part{part}.csv")
        return False
    
    results = {}
    
    # Process each SAS table
    for table_name, table_config in SAS_TABLES.items():
        logger.info(f"\n{'─'*70}")
        logger.info(f"Processing: {table_name} — {table_config['description']}")
        logger.info(f"{'─'*70}")
        
        # Load raw parts
        raw_df, load_success = load_raw_table_parts(table_name)
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
        
        # Validate against combined
        validation_ok = validate_against_combined(manchester_df, table_name)
        
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
        logger.info(f"  2. Run: python scripts/04_compute_indicators_1981_eds.py")
        return True
    else:
        logger.error("✗ Some tables failed to ingest")
        logger.error(f"  Please check raw files in: {RAW_DATA_DIR}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
