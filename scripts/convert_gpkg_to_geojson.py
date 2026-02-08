#!/usr/bin/env python3
"""
Convert GeoPackage (.gpkg) files to GeoJSON for web consumption.
Simplifies geometries and optimizes file size for Leaflet rendering.
"""

import geopandas as gpd
import json
import os
from pathlib import Path
from typing import List, Dict, Any


def simplify_geojson(gdf: gpd.GeoDataFrame, tolerance: float = 10) -> gpd.GeoDataFrame:
    """
    Simplify geometries to reduce file size while maintaining visual accuracy.
    
    Args:
        gdf: GeoDataFrame to simplify
        tolerance: Simplification tolerance in map units (meters for BNG)
    
    Returns:
        Simplified GeoDataFrame
    """
    # Simplify geometries
    gdf['geometry'] = gdf['geometry'].simplify(tolerance, preserve_topology=True)
    return gdf


def round_coordinates(geojson_dict: Dict[str, Any], precision: int = 6) -> Dict[str, Any]:
    """
    Round coordinate values to reduce file size.
    
    Args:
        geojson_dict: GeoJSON dictionary
        precision: Number of decimal places
    
    Returns:
        GeoJSON with rounded coordinates
    """
    def round_coords(coords):
        if isinstance(coords[0], (int, float)):
            return [round(c, precision) for c in coords]
        return [round_coords(c) for c in coords]
    
    for feature in geojson_dict['features']:
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            geom['coordinates'] = [round_coords(ring) for ring in geom['coordinates']]
        elif geom['type'] == 'MultiPolygon':
            geom['coordinates'] = [[round_coords(ring) for ring in polygon] for polygon in geom['coordinates']]
        elif geom['type'] == 'Point':
            geom['coordinates'] = round_coords(geom['coordinates'])
        elif geom['type'] == 'LineString':
            geom['coordinates'] = round_coords(geom['coordinates'])
    
    return geojson_dict


def convert_gpkg_to_geojson(
    input_gpkg: Path,
    output_dir: Path,
    output_name: str = None,
    simplify_tolerance: float = 10,
    coordinate_precision: int = 6,
    target_crs: str = "EPSG:4326"
) -> Path:
    """
    Convert a GeoPackage to optimized GeoJSON for web use.
    
    Args:
        input_gpkg: Path to input .gpkg file
        output_dir: Directory to save GeoJSON output
        output_name: Custom output filename (without extension)
        simplify_tolerance: Geometry simplification tolerance
        coordinate_precision: Decimal places for coordinates
        target_crs: Target CRS for output (default WGS84 for web maps)
    
    Returns:
        Path to created GeoJSON file
    """
    print(f"\n📦 Processing: {input_gpkg.name}")
    
    # Read GeoPackage
    gdf = gpd.read_file(input_gpkg)
    print(f"  • Loaded {len(gdf)} features")
    print(f"  • Original CRS: {gdf.crs}")
    print(f"  • Columns: {list(gdf.columns)}")
    
    # Reproject to WGS84 (EPSG:4326) for web mapping
    if str(gdf.crs) != target_crs:
        gdf = gdf.to_crs(target_crs)
        print(f"  • Reprojected to {target_crs}")
    
    # Simplify geometries
    gdf = simplify_geojson(gdf, tolerance=simplify_tolerance)
    print(f"  • Simplified geometries (tolerance={simplify_tolerance}m)")
    
    # Convert to GeoJSON dictionary
    geojson_dict = json.loads(gdf.to_json())
    
    # Round coordinates
    geojson_dict = round_coordinates(geojson_dict, precision=coordinate_precision)
    print(f"  • Rounded coordinates to {coordinate_precision} decimal places")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    if output_name is None:
        output_name = input_gpkg.stem
    output_path = output_dir / f"{output_name}.geojson"
    
    # Write GeoJSON
    with open(output_path, 'w') as f:
        json.dump(geojson_dict, f, separators=(',', ':'))  # Compact JSON
    
    # Report file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ Saved to: {output_path}")
    print(f"  • File size: {size_mb:.2f} MB")
    
    return output_path


def batch_convert_census_data():
    """
    Convert all census GeoPackages to GeoJSON for the web app.
    """
    # Base directories
    project_root = Path(__file__).parent.parent
    spatial_data_dir = project_root / "data" / "processed" / "outputs" / "spatial"
    web_output_dir = project_root.parent / "manchester-cityscape-explorer-main" / "public" / "geojson"
    
    # Files to convert
    conversions = [
        {
            "input": spatial_data_dir / "1981" / "manchester_eds_1981_joined_indicators.gpkg",
            "output_name": "manchester_eds_1981",
            "description": "1981 Enumeration Districts with indicators"
        },
        {
            "input": spatial_data_dir / "1991" / "manchester_eds_1991_joined_indicators.gpkg",
            "output_name": "manchester_eds_1991",
            "description": "1991 Enumeration Districts with indicators"
        }
    ]
    
    print("=" * 70)
    print("GeoPackage to GeoJSON Conversion for Web Application")
    print("=" * 70)
    
    converted_files = []
    
    for config in conversions:
        input_path = config["input"]
        
        if not input_path.exists():
            print(f"\n⚠️  Skipping: {input_path.name} (file not found)")
            continue
        
        try:
            output_path = convert_gpkg_to_geojson(
                input_gpkg=input_path,
                output_dir=web_output_dir,
                output_name=config["output_name"],
                simplify_tolerance=10,  # 10m simplification for visual quality
                coordinate_precision=6  # ~10cm precision (good for web)
            )
            converted_files.append({
                "year": config["output_name"].split("_")[-1],
                "path": str(output_path.relative_to(web_output_dir.parent)),
                "description": config["description"]
            })
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Create metadata file
    if converted_files:
        metadata = {
            "generated": "2026-02-04",
            "crs": "EPSG:4326 (WGS84)",
            "datasets": converted_files
        }
        
        metadata_path = web_output_dir / "datasets.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("\n" + "=" * 70)
        print(f"✅ Conversion complete! {len(converted_files)} datasets created")
        print(f"📄 Metadata saved to: {metadata_path}")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Start your web app: cd manchester-cityscape-explorer-main && npm run dev")
        print("2. Access GeoJSON files from: /geojson/<filename>.geojson")
        print("3. Use the ChoroplethMapContainer component to display the data")


if __name__ == "__main__":
    batch_convert_census_data()
