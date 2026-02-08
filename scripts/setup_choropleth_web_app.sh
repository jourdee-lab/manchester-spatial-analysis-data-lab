#!/bin/bash

# Quick Start Script for Choropleth Integration
# This script automates the setup process for census data visualization

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Manchester Census Choropleth - Quick Start Setup            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Define paths
PROJECT_ROOT="/home/jourdee/Workspace/manchester_spatial_lab/fyp_main"
WEB_APP_ROOT="/home/jourdee/Workspace/manchester_spatial_lab/manchester-cityscape-explorer-main"

# Step 1: Convert GeoPackages to GeoJSON
echo "📦 Step 1: Converting GeoPackages to GeoJSON..."
echo "─────────────────────────────────────────────────────────────────"
cd "$PROJECT_ROOT"

if [ -f "scripts/convert_gpkg_to_geojson.py" ]; then
    python3 scripts/convert_gpkg_to_geojson.py
    echo "✅ Conversion complete!"
else
    echo "❌ Error: Conversion script not found"
    exit 1
fi

echo ""

# Step 2: Verify output files
echo "🔍 Step 2: Verifying output files..."
echo "─────────────────────────────────────────────────────────────────"
GEOJSON_DIR="$WEB_APP_ROOT/public/geojson"

if [ -d "$GEOJSON_DIR" ]; then
    echo "GeoJSON directory contents:"
    ls -lh "$GEOJSON_DIR"
    
    # Count files
    file_count=$(find "$GEOJSON_DIR" -name "*.geojson" | wc -l)
    echo ""
    echo "Found $file_count GeoJSON file(s)"
else
    echo "⚠️  Warning: GeoJSON directory not found at $GEOJSON_DIR"
    echo "Creating directory..."
    mkdir -p "$GEOJSON_DIR"
fi

echo ""

# Step 3: Check web app dependencies
echo "📚 Step 3: Checking web app dependencies..."
echo "─────────────────────────────────────────────────────────────────"
cd "$WEB_APP_ROOT"

if [ ! -d "node_modules" ]; then
    echo "⚠️  Node modules not installed. Installing..."
    npm install
else
    echo "✅ Dependencies already installed"
fi

echo ""

# Step 4: Ready message
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    🎉 Setup Complete! 🎉                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Start the development server:"
echo "   cd $WEB_APP_ROOT"
echo "   npm run dev"
echo ""
echo "2. Open your browser to:"
echo "   http://localhost:5173/census-explorer"
echo ""
echo "3. Use the interface to:"
echo "   • Toggle between 1981 and 1991 census years"
echo "   • Select different indicators from the dropdown"
echo "   • Hover over polygons to see values"
echo "   • Click polygons for detailed information"
echo ""
echo "📚 For more information, see:"
echo "   $WEB_APP_ROOT/CHOROPLETH_INTEGRATION.md"
echo ""
