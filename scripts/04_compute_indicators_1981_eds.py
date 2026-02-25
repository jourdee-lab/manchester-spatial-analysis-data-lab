#!/usr/bin/env python3
"""
Step 2a: Compute Indicators from ED-Level SAS Data (1981)
=========================================================

Updated to load real ED-level data (after raw SAS ingestion).

Inputs:
  - ED-level SAS data (CSV): data/processed/raw_ed_level/1981/sas0X_1981_ed_level.csv
  - OR ED-level template (if raw data not yet available): gis_boundaries/1981_ed_manchester/manchester_ed_level_sas_template.csv
  - Indicator configuration: configs/indicators.yml

Outputs:
  - Indicator table (CSV): data/processed/indicators/1981/manchester_eds_1981_indicators.csv
  - Indicator metadata (JSON): docs/phase6_indicator_documentation/indicators_1981_metadata.json
  - Summary statistics (JSON): docs/phase6_indicator_documentation/indicators_1981_summary.json

Author: FYP Data Pipeline
Date: 2026-01-14
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURATION & PATHS
# =====================================================================

CONFIG_PATH = Path("configs/indicators.yml")

# Try to load real ED-level data first; fall back to template if not available
ED_LEVEL_PATHS = [
    # Priority 1: Real ED-level data (from raw SAS ingestion)
    Path("data/processed/raw_ed_level/1981/sas02_1981_ed_level.csv"),
    Path("data/processed/raw_ed_level/1981/sas04_1981_ed_level.csv"),
    Path("data/processed/raw_ed_level/1981/sas07_1981_ed_level.csv"),
    Path("data/processed/raw_ed_level/1981/sas10_1981_ed_level.csv"),
    # Priority 2: Template (zero-filled, for structure validation)
    Path("gis_boundaries/1981_ed_manchester/manchester_ed_level_sas_template.csv"),
]

OUTPUT_CSV_PATH = Path("data/processed/indicators/1981/manchester_eds_1981_indicators.csv")
OUTPUT_METADATA_PATH = Path("docs/phase6_indicator_documentation/indicators_1981_metadata.json")
OUTPUT_SUMMARY_PATH = Path("docs/phase6_indicator_documentation/indicators_1981_summary.json")

YEAR = 1981
ED_ID_COLUMN = "zoneid"

# =====================================================================
# INDICATOR COMPUTATION FUNCTIONS
# =====================================================================

def load_config(config_path: Path) -> Dict:
    """Load indicator configuration from YAML file."""
    logger.info(f"Loading indicator configuration from {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    logger.info(f"Loaded configuration for years: {list(config['years'].keys())}")
    return config

def load_ed_data(data_paths: List[Path]) -> Tuple[pd.DataFrame, str]:
    """
    Load ED-level SAS data from CSV.
    
    Tries multiple paths in order (real data first, template fallback).
    If multiple files found (one per SAS table), merges them horizontally.
    
    Args:
        data_paths: List of potential data file paths
    
    Returns:
        Tuple of (DataFrame, data_source_description)
    """
    
    logger.info("Loading ED-level SAS data...")
    
    # Filter to existing files
    existing_files = [p for p in data_paths if p.exists()]
    
    if not existing_files:
        logger.error(f"No ED-level data files found")
        logger.error(f"Expected one of:")
        for p in data_paths:
            logger.error(f"  - {p}")
        raise FileNotFoundError("No ED-level data files found")
    
    dfs = []
    file_sources = []
    
    # Load all available files
    for fpath in existing_files:
        logger.info(f"  Loading: {fpath}")
        df = pd.read_csv(fpath)
        logger.info(f"    Shape: {df.shape} (rows, cols)")
        dfs.append(df)
        file_sources.append(fpath.name)
        
        # If this looks like real ED-level data (1017 rows), use it
        if len(df) == 1017:
            logger.info(f"    ✓ Real ED-level data (1,017 Manchester EDs)")
            # Continue loading other files to merge
        elif len(df) == 1:
            logger.warning(f"    ⚠ Single-row aggregate data (Manchester LAD level)")
    
    # Merge all loaded files on zoneid
    if len(dfs) > 1:
        logger.info(f"\nMerging {len(dfs)} tables horizontally...")
        merged = dfs[0]
        for i, df in enumerate(dfs[1:], 2):
            # Check if zoneid column exists in both
            if 'zoneid' in merged.columns and 'zoneid' in df.columns:
                # Merge on zoneid, dropping duplicate zoneid from df
                merged = merged.merge(df.drop('zoneid', axis=1), 
                                    left_index=True, right_index=True,
                                    how='inner')
                logger.info(f"  Merged table {i}: {merged.shape[1]} total columns")
        df = merged
        source = f"Merged from {len(file_sources)} tables"
    elif len(dfs) == 1:
        df = dfs[0]
        source = file_sources[0]
    else:
        raise FileNotFoundError("No ED-level data files could be loaded")
    
    logger.info(f"\nLoaded {len(df)} EDs with {len(df.columns)} columns")
    logger.info(f"Source: {source}")
    
    return df, source

def compute_indicator(
    df: pd.DataFrame,
    indicator_name: str,
    indicator_config: Dict,
    computed_indicators: Dict[str, pd.Series]
) -> Tuple[pd.Series, Dict]:
    """
    Compute a single indicator from raw data or other indicators.
    
    Args:
        df: DataFrame with raw SAS data
        indicator_name: Name of the indicator to compute
        indicator_config: Configuration dict for this indicator
        computed_indicators: Dict of already-computed indicators
    
    Returns:
        Tuple of (computed Series, metadata dict)
    """
    
    ind_type = indicator_config.get('type', 'raw')
    sas_code = indicator_config.get('code')
    description = indicator_config.get('description', '')
    calculation = indicator_config.get('calculation')
    denominator_name = indicator_config.get('denominator')
    
    metadata = {
        'name': indicator_name,
        'type': ind_type,
        'description': description,
        'sas_code': sas_code,
        'calculation': calculation,
        'denominator': denominator_name,
        'source_table': indicator_config.get('table'),
    }
    
    try:
        if ind_type == 'raw' or ind_type == 'denominator':
            # Raw count from SAS column
            if sas_code not in df.columns:
                logger.warning(f"SAS code {sas_code} not found in data for {indicator_name}")
                series = pd.Series(np.nan, index=df.index, name=indicator_name)
                metadata['status'] = 'SAS_CODE_NOT_FOUND'
                metadata['non_null_count'] = 0
            else:
                series = df[sas_code].astype(float)
                non_null = series.notna().sum()
                non_zero = (series > 0).sum()
                metadata['status'] = 'OK'
                metadata['non_null_count'] = int(non_null)
                metadata['non_zero_count'] = int(non_zero)
                metadata['sum'] = float(series.sum())
                metadata['mean'] = float(series.mean())
                metadata['max'] = float(series.max())
                logger.info(f"  {indicator_name}: {non_null} non-null, {non_zero} non-zero values")
        
        elif ind_type == 'rate':
            # Derived rate calculation
            if calculation:
                # Parse calculation string and compute
                # Expected format: "100 * NUMERATOR / DENOMINATOR"
                # For now, use simple evaluation if both components exist
                
                # Special case: inverse rates like "100 - PCT_NO_CAR"
                if " - " in calculation and indicator_name not in computed_indicators:
                    parts = calculation.split(" - ")
                    base = float(parts[0].strip())
                    ref_indicator = parts[1].strip()
                    if ref_indicator in computed_indicators:
                        series = base - computed_indicators[ref_indicator]
                        metadata['status'] = 'OK'
                        non_null = series.notna().sum()
                        metadata['non_null_count'] = int(non_null)
                        metadata['mean'] = float(series.mean())
                        logger.info(f"  {indicator_name}: composite from {ref_indicator}")
                    else:
                        logger.warning(f"Referenced indicator {ref_indicator} not yet computed")
                        series = pd.Series(np.nan, index=df.index, name=indicator_name)
                        metadata['status'] = 'MISSING_REFERENCE'
                
                # Standard rate: numerator / denominator * 100
                elif denominator_name and denominator_name in computed_indicators:
                    # Get numerator SAS code
                    numerator = df[sas_code].astype(float) if sas_code and sas_code in df.columns else pd.Series(np.nan, index=df.index)
                    denominator = computed_indicators[denominator_name].astype(float)
                    
                    # Compute rate: handle division by zero
                    series = pd.Series(index=df.index, dtype=float)
                    valid_mask = (denominator > 0) & (numerator.notna()) & (denominator.notna())
                    series[valid_mask] = 100 * numerator[valid_mask] / denominator[valid_mask]
                    series[~valid_mask] = np.nan
                    
                    metadata['status'] = 'OK'
                    valid_count = valid_mask.sum()
                    metadata['non_null_count'] = int(valid_count)
                    metadata['mean'] = float(series.mean())
                    metadata['min'] = float(series.min())
                    metadata['max'] = float(series.max())
                    logger.info(f"  {indicator_name}: {valid_count} valid rates (0-100 scale)")
                
                else:
                    logger.warning(f"Cannot compute {indicator_name}: denominator {denominator_name} not found")
                    series = pd.Series(np.nan, index=df.index, name=indicator_name)
                    metadata['status'] = 'MISSING_DENOMINATOR'
            
            else:
                logger.warning(f"No calculation formula for {indicator_name}")
                series = pd.Series(np.nan, index=df.index, name=indicator_name)
                metadata['status'] = 'NO_FORMULA'
        
        else:
            logger.warning(f"Unknown indicator type: {ind_type}")
            series = pd.Series(np.nan, index=df.index, name=indicator_name)
            metadata['status'] = 'UNKNOWN_TYPE'
        
        series.name = indicator_name
        return series, metadata
    
    except Exception as e:
        logger.error(f"Error computing {indicator_name}: {str(e)}")
        series = pd.Series(np.nan, index=df.index, name=indicator_name)
        metadata['status'] = f'ERROR: {str(e)}'
        return series, metadata

def compute_all_indicators(
    df: pd.DataFrame,
    config: Dict,
    year: int = 1981
) -> Tuple[pd.DataFrame, Dict]:
    """
    Compute all indicators for a given year.
    
    Args:
        df: ED-level SAS data
        config: Indicator configuration
        year: Census year
    
    Returns:
        Tuple of (indicators DataFrame, metadata dict)
    """
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Computing indicators for {year}")
    logger.info(f"{'='*60}")
    
    year_config = config['years'].get(year)
    if not year_config:
        logger.error(f"No configuration found for year {year}")
        return None, None
    
    indicators = pd.DataFrame(index=df.index)
    indicators[ED_ID_COLUMN] = df[ED_ID_COLUMN]
    
    computed_indicators = {}  # Cache for computed series
    metadata_dict = {}
    
    # Iterate through indicators in order of dependency
    # (denominators first, then rates that depend on them)
    
    # Phase 1: Denominators and raw counts
    logger.info("\nPhase 1: Loading raw counts and denominators...")
    for ind_name, ind_config in year_config.items():
        if ind_config.get('type') in ['raw', 'denominator']:
            series, meta = compute_indicator(df, ind_name, ind_config, computed_indicators)
            indicators[ind_name] = series
            computed_indicators[ind_name] = series
            metadata_dict[ind_name] = meta
    
    # Phase 2: Derived rates
    logger.info("\nPhase 2: Computing derived rates...")
    for ind_name, ind_config in year_config.items():
        if ind_config.get('type') == 'rate' and ind_name not in metadata_dict:
            series, meta = compute_indicator(df, ind_name, ind_config, computed_indicators)
            indicators[ind_name] = series
            computed_indicators[ind_name] = series
            metadata_dict[ind_name] = meta
    
    logger.info(f"\nComputed {len(metadata_dict)} indicators")
    
    return indicators, metadata_dict

def generate_summary_statistics(indicators: pd.DataFrame, metadata: Dict) -> Dict:
    """Generate summary statistics across all indicators."""
    
    summary = {
        'year': YEAR,
        'ed_count': len(indicators),
        'indicators_count': len(metadata),
        'computation_date': datetime.now().isoformat(),
        'indicators': {}
    }
    
    for ind_name, meta in metadata.items():
        summary['indicators'][ind_name] = {
            'description': meta.get('description'),
            'type': meta.get('type'),
            'status': meta.get('status'),
            'sas_code': meta.get('sas_code'),
            'non_null_count': meta.get('non_null_count', 0),
            'coverage_percent': round(100 * meta.get('non_null_count', 0) / len(indicators), 1),
            'mean': meta.get('mean'),
            'min': meta.get('min'),
            'max': meta.get('max'),
        }
    
    return summary

def save_outputs(
    indicators: pd.DataFrame,
    metadata: Dict,
    summary: Dict,
    csv_path: Path,
    metadata_path: Path,
    summary_path: Path,
):
    """Save indicator outputs to CSV and JSON."""
    
    # Ensure output directories exist
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save indicators CSV
    logger.info(f"\nSaving indicators to {csv_path}")
    indicators.to_csv(csv_path, index=False)
    logger.info(f"  ✓ Saved {len(indicators)} rows × {len(indicators.columns)} columns")
    
    # Save metadata JSON
    logger.info(f"Saving metadata to {metadata_path}")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"  ✓ Saved metadata for {len(metadata)} indicators")
    
    # Save summary JSON
    logger.info(f"Saving summary to {summary_path}")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"  ✓ Saved summary statistics")

def main():
    """Main pipeline: load, compute, validate, save."""
    
    logger.info("="*60)
    logger.info("PHASE 6: INDICATOR COMPUTATION (1981)")
    logger.info("="*60)
    
    # Load configuration
    try:
        config = load_config(CONFIG_PATH)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {CONFIG_PATH}")
        return False
    
    # Load ED-level data (real or template)
    try:
        ed_data, data_source = load_ed_data(ED_LEVEL_PATHS)
        logger.info(f"Using data source: {data_source}")
    except FileNotFoundError as e:
        logger.error(f"{e}")
        return False
    
    # Compute indicators
    indicators, metadata = compute_all_indicators(ed_data, config, year=YEAR)
    
    if indicators is None:
        logger.error("Failed to compute indicators")
        return False
    
    # Generate summary statistics
    summary = generate_summary_statistics(indicators, metadata)
    
    # Save outputs
    save_outputs(
        indicators, metadata, summary,
        OUTPUT_CSV_PATH,
        OUTPUT_METADATA_PATH,
        OUTPUT_SUMMARY_PATH
    )
    
    # Print summary report
    logger.info("\n" + "="*60)
    logger.info("SUMMARY REPORT")
    logger.info("="*60)
    logger.info(f"Enumeration Districts: {summary['ed_count']}")
    logger.info(f"Indicators Computed: {summary['indicators_count']}")
    logger.info(f"\nIndicator Status:")
    
    status_counts = {}
    for ind_name, ind_summary in summary['indicators'].items():
        status = ind_summary['status']
        status_counts[status] = status_counts.get(status, 0) + 1
        coverage = ind_summary['coverage_percent']
        logger.info(f"  {ind_name:30s} | {status:20s} | Coverage: {coverage:6.1f}%")
    
    logger.info(f"\nStatus Summary:")
    for status, count in sorted(status_counts.items()):
        logger.info(f"  {status}: {count}")
    
    logger.info("\n" + "="*60)
    logger.info("✓ Phase 6 indicator computation complete")
    logger.info("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
