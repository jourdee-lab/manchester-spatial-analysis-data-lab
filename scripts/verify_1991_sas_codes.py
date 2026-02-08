#!/usr/bin/env python3
"""
Verify 1991 SAS Codes Against Lookup File
==========================================

This script uses the new 1991 SAS variable lookup to verify that indicator
computation codes are correct when ED-level data becomes available.

Purpose:
- Cross-check placeholder SAS codes in phase6_compute_indicators_1991.py
- Generate documentation of correct variable mappings
- Provide guidance for when 1991 ED-level data is ingested

Author: FYP Data Pipeline
Date: 2026-01-18
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURATION
# =====================================================================

LOOKUP_FILE = Path("data/lookups/1991_England_Wales_Scotland_Small_Area_Statistics_variable_lookup.csv")

# Indicator SAS codes we expect (from phase6_compute_indicators_1991.py)
# These are currently PLACEHOLDERS and need verification
EXPECTED_CODES = {
    "Demographics": {
        "TOTAL_RES": ("S02EWS", "S020001", "All ages TOTAL Persons"),
        "PCT_MALE": ("S02EWS", "S020002", "All ages Male"),
    },
    "Ethnic/Country of Birth": {
        "CHINESE_BORN": ("S07EWS", "S070001", "Total persons born (China/Far East)"),
    },
    "Employment": {
        "EMPLOYED": ("S09EWS", "S090001", "Employed residents"),
        "UNEMPLOYED": ("S09EWS", "S090002", "Unemployed residents"),
    },
    "Housing": {
        "TOTAL_HH": ("S16EWS", "S160001", "Households with residents (TOTAL tenure)"),
        "OWNER_OCC_HH": ("S16EWS", "S160010", "Owner-occupied households"),
        "NO_CAR_HH": ("S16EWS", "S160020", "Households with no car"),
    },
}

# =====================================================================
# FUNCTIONS
# =====================================================================

def load_lookup():
    """Load the 1991 SAS variable lookup file."""
    if not LOOKUP_FILE.exists():
        logger.error(f"✗ Lookup file not found: {LOOKUP_FILE}")
        return None
    
    try:
        df = pd.read_csv(LOOKUP_FILE)
        logger.info(f"✓ Loaded lookup file: {LOOKUP_FILE} ({len(df)} records)")
        return df
    except Exception as e:
        logger.error(f"✗ Failed to load lookup: {e}")
        return None


def verify_sas_codes(lookup_df: pd.DataFrame) -> Dict[str, Dict]:
    """Verify expected SAS codes exist in lookup."""
    results = {}
    
    for category, codes in EXPECTED_CODES.items():
        logger.info(f"\n{'─'*70}")
        logger.info(f"Category: {category}")
        logger.info(f"{'─'*70}")
        
        results[category] = {}
        
        for indicator, (table, code, description) in codes.items():
            logger.info(f"\n  Checking: {indicator} ({table}.{code})")
            
            # Search for exact code match
            match = lookup_df[lookup_df['table_column_name'] == code]
            
            if len(match) > 0:
                found_desc = match.iloc[0]['description']
                logger.info(f"    ✓ FOUND in {table}")
                logger.info(f"      Description: {found_desc[:80]}...")
                results[category][indicator] = {
                    'status': 'FOUND',
                    'table': table,
                    'code': code,
                    'lookup_description': found_desc,
                    'expected_description': description
                }
            else:
                logger.warning(f"    ⚠ NOT FOUND (code {code} may be placeholder)")
                # Try partial search
                partial = lookup_df[lookup_df['table_name'] == table]
                if len(partial) > 0:
                    logger.warning(f"      Table {table} exists with {len(partial)} records")
                    logger.warning(f"      First 3 codes: {partial['table_column_name'].head(3).tolist()}")
                results[category][indicator] = {
                    'status': 'NOT_FOUND',
                    'table': table,
                    'code': code,
                    'lookup_description': None,
                    'expected_description': description,
                    'table_records': len(partial) if len(partial) > 0 else 0
                }
    
    return results


def generate_report(results: Dict) -> None:
    """Generate human-readable report."""
    logger.info(f"\n\n{'='*70}")
    logger.info("VERIFICATION REPORT: 1991 SAS CODES")
    logger.info(f"{'='*70}\n")
    
    total_indicators = sum(len(codes) for codes in results.values())
    found_count = sum(1 for cat in results.values() for ind in cat.values() 
                      if ind['status'] == 'FOUND')
    not_found_count = total_indicators - found_count
    
    logger.info(f"Summary:")
    logger.info(f"  Total indicators checked: {total_indicators}")
    logger.info(f"  Found in lookup: {found_count} ✓")
    logger.info(f"  Not found: {not_found_count} ⚠")
    logger.info(f"  Verification rate: {(found_count/total_indicators*100):.1f}%\n")
    
    # Detailed results
    for category, codes in results.items():
        logger.info(f"\n{category}:")
        for indicator, result in codes.items():
            status_symbol = "✓" if result['status'] == 'FOUND' else "⚠"
            logger.info(f"  {status_symbol} {indicator:20} {result['code']:10} {result['status']}")
            if result['status'] == 'FOUND':
                logger.info(f"     └─ {result['lookup_description'][:70]}")


def save_verification_output(results: Dict) -> None:
    """Save verification results to CSV for documentation."""
    output_rows = []
    
    for category, codes in results.items():
        for indicator, result in codes.items():
            output_rows.append({
                'category': category,
                'indicator': indicator,
                'table': result['table'],
                'code': result['code'],
                'status': result['status'],
                'lookup_description': result.get('lookup_description', ''),
                'expected_description': result['expected_description'],
            })
    
    output_df = pd.DataFrame(output_rows)
    output_file = Path("data/processed/1991_sas_code_verification.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        output_df.to_csv(output_file, index=False)
        logger.info(f"\n✓ Verification results saved to: {output_file}")
    except Exception as e:
        logger.error(f"✗ Failed to save verification output: {e}")


def main():
    """Main execution."""
    logger.info("="*70)
    logger.info("VERIFY 1991 SAS CODES AGAINST LOOKUP")
    logger.info("="*70)
    
    # Load lookup
    lookup_df = load_lookup()
    if lookup_df is None:
        logger.error("\n✗ Cannot proceed without lookup file")
        return False
    
    # Verify codes
    results = verify_sas_codes(lookup_df)
    
    # Generate report
    generate_report(results)
    
    # Save output
    save_verification_output(results)
    
    logger.info("\n" + "="*70)
    logger.info("VERIFICATION COMPLETE")
    logger.info("="*70)
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
