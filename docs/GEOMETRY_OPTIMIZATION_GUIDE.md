# Geometry Optimization Guide for Web Mapping

## Overview
This guide explains how to optimize GeoJSON boundary files for clean, performant web rendering with proper topological relationships.

## Key Issues & Solutions

### 1. Boundary Line Visibility
**Problem**: Heavy, opaque boundaries overwhelm the choropleth colors and create visual clutter.

**Solution**: 
- Use thin boundaries (`weight: 0.5-1.0`)
- Low opacity (`opacity: 0.10-0.20`)
- White or light color separators (`color: '#ffffff'`)
- This creates subtle polygon separation without dominating the visualization

### 2. Color Schemes
**Problem**: Default palettes lack perceptual uniformity, making it hard to interpret data accurately.

**Solution**: Use ColorBrewer schemes
- **Sequential single-hue**: Best for single-variable data (e.g., population density)
  - Blues, Reds, Greens, Purples
- **Sequential multi-hue**: Better visual discrimination
  - YellowGreenBlue, YellowOrangeRed
- **Diverging**: For data with meaningful midpoint (e.g., change over time)
  - RedBlue, BrownTeal

Reference: https://colorbrewer2.org/

### 3. Legend Clarity
**Problem**: Arbitrary decimal breaks (e.g., 3.742% – 7.891%) are hard to interpret.

**Solution**: Use custom breaks for percentage data
- 0-2%, 2-5%, 5-10%, 10-20%, etc.
- Round numbers aid quick visual interpretation
- Maintain data integrity while improving readability

### 4. Topological Issues (Gaps & Overlaps)

#### Common Problems:
- **Gaps**: Visible white space between adjacent polygons
- **Overlaps**: Polygons sharing area, causing rendering artifacts
- **Slivers**: Tiny polygons from imperfect boundaries

#### Solutions in QGIS:

**A. Topology Checker (Pre-validation)**
1. Vector → Topology Checker
2. Configure rules:
   - "Must not have gaps"
   - "Must not overlap"
   - "Must not have invalid geometries"
3. Run check and fix errors

**B. Fix Geometries Tool**
```
Processing Toolbox → Vector Geometry → Fix geometries
```
Repairs common issues: self-intersections, duplicate vertices, invalid rings

**C. Snap Geometries**
```
Processing Toolbox → Vector Geometry → Snap geometries to layer
Input: Your boundary layer
Reference: Same layer
Tolerance: 0.1-1.0 meters (adjust based on coordinate system)
```
Ensures adjacent polygons share exact boundary coordinates

**D. V.clean (GRASS)**
For advanced topology cleaning:
```
Processing Toolbox → GRASS → v.clean
Cleaning tools: rmsa, break, rmdupl, snap
Threshold: 0.1-1.0 (depending on units)
```

### 5. Geometry Simplification

#### When to Simplify:
- File size > 5MB for web delivery
- Zoom levels don't require ED-level precision
- Performance issues in browser rendering

#### Methods:

**A. QGIS Simplify Geometries**
```
Processing Toolbox → Vector Geometry → Simplify
Tolerance: 10-20 meters for Manchester ED-level data
Method: Douglas-Peucker (default)
```

**B. Mapshaper (Recommended for Web)**
```bash
# Install: npm install -g mapshaper

# Basic simplification
mapshaper input.geojson -simplify 20% -o output.geojson

# Topology-preserving simplification
mapshaper input.geojson \
  -simplify 20% keep-shapes \
  -clean \
  -o output.geojson
```

**C. Topology-Preserving Simplification in QGIS**
```
Processing Toolbox → Vector Geometry → Simplify (preserve topology)
Tolerance: Start with 10m, increase if needed
```

#### Recommended Tolerances by Scale:
- **ED-level (1:10,000 - 1:50,000)**: 10-20 meters
- **Ward-level (1:50,000 - 1:100,000)**: 20-50 meters
- **City-level (1:100,000+)**: 50-100 meters

### 6. Export Settings for Web

#### GeoJSON Export from QGIS:
```
Right-click layer → Export → Save Features As...
Format: GeoJSON
CRS: EPSG:4326 (WGS 84) - required for web maps
Coordinate precision: 6 decimal places (sufficient for ~10cm accuracy)
Options:
  ☑ RFC7946 (for maximum web compatibility)
  ☐ Write non-standard bbox member (usually not needed)
```

#### GeoPackage to GeoJSON Conversion:
```python
# Using the project's conversion script
python scripts/utils_convert_gpkg_to_geojson.py \
  --input data/processed/outputs/spatial/1991/manchester_eds_1991.gpkg \
  --output public/geojson/manchester_eds_1991.geojson \
  --simplify 15
```

## Validation Checklist

Before deploying GeoJSON to web app:

- [ ] Run QGIS Topology Checker (no errors)
- [ ] Visual inspection at multiple zoom levels
- [ ] File size < 10MB (ideally < 5MB)
- [ ] All features have required attribute fields
- [ ] CRS is EPSG:4326
- [ ] No self-intersections (use Check Validity tool)
- [ ] No duplicate features
- [ ] Coordinate precision: 6 decimal places
- [ ] Test load in web browser (should render in < 2 seconds)

## Performance Targets

- **File size**: < 5MB per year/geography
- **Feature count**: < 1000 polygons per layer
- **Load time**: < 2 seconds on 4G connection
- **Render time**: < 500ms for initial draw
- **Interaction**: < 100ms hover/click response

## Tools Reference

### QGIS Processing Tools
- Vector Geometry → Fix geometries
- Vector Geometry → Check validity
- Vector Geometry → Simplify
- Vector Geometry → Snap geometries to layer
- Vector → Topology Checker

### Command-line Tools
- **mapshaper**: Simplification, format conversion
- **ogr2ogr**: Format conversion, reprojection
- **tippecanoe**: Vector tile generation (for large datasets)

### Python Libraries
- **geopandas**: Geometry manipulation, validation
- **shapely**: Geometric operations, simplification
- **rtree**: Spatial indexing for performance

## Further Reading

- ColorBrewer: https://colorbrewer2.org/
- Mapshaper: https://mapshaper.org/ (web interface available)
- QGIS Topology Documentation: https://docs.qgis.org/latest/en/docs/user_manual/processing_algs/qgis/vectorgeometry.html
- GeoJSON RFC7946: https://tools.ietf.org/html/rfc7946
