"""Shared helpers for the Manchester Chinese diaspora census pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safe arithmetic
# ---------------------------------------------------------------------------

def safe_rate(numerator: pd.Series, denominator: pd.Series, scale: float = 100.0) -> pd.Series:
    """Return numerator / denominator * scale; yields NaN where denominator <= 0 or NaN."""
    denom = denominator.replace(0, np.nan)
    return numerator / denom * scale


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Population-weighted mean; returns NaN if total weight is zero."""
    mask = values.notna() & weights.notna() & (weights > 0)
    w = weights[mask]
    if w.sum() == 0:
        return np.nan
    return float((values[mask] * w).sum() / w.sum())


def dissimilarity_index(group_pop: pd.Series, total_pop: pd.Series) -> float:
    """Duncan & Duncan dissimilarity index (0 = fully integrated, 1 = fully segregated)."""
    g = group_pop.fillna(0)
    t = total_pop.fillna(0)
    G = g.sum()
    T = t.sum()
    non_g = t - g
    NG = non_g.sum()
    if G == 0 or NG == 0:
        return np.nan
    return float(0.5 * abs(g / G - non_g / NG).sum())


# ---------------------------------------------------------------------------
# Column lookup (case-insensitive)
# ---------------------------------------------------------------------------

def get_col(df: pd.DataFrame, code: str) -> pd.Series:
    """Return column matching *code* (exact then case-insensitive); NaN Series if absent."""
    if code in df.columns:
        return df[code]
    lower_map = {c.lower(): c for c in df.columns}
    if code.lower() in lower_map:
        return df[lower_map[code.lower()]]
    log.warning("Column not found: %s – filling with NaN", code)
    return pd.Series(np.nan, index=df.index, name=code)


# ---------------------------------------------------------------------------
# Zone-ID normalisation
# ---------------------------------------------------------------------------

def normalise_zoneid(series: pd.Series) -> pd.Series:
    """Strip whitespace and uppercase zone IDs."""
    return series.astype(str).str.strip().str.upper()


# ---------------------------------------------------------------------------
# GeoPackage save helper
# ---------------------------------------------------------------------------

def save_gpkg(gdf, path: Path, crs: str = "EPSG:27700") -> None:
    """Ensure CRS is set and write a GeoPackage."""
    import geopandas as gpd  # local import to keep utils importable without geopandas
    if gdf.crs is None:
        gdf = gdf.set_crs(crs)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(str(path), driver="GPKG")
    log.info("Saved %d features: %s", len(gdf), path)
