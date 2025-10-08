#!/bin/bash
set -e

ANALYZER="./analyzer/target/release/compact-block-analyzer"
LIGHTWALLETD=${1:-"http://127.0.0.1:9067"}
ZEBRAD=${2:-"http://127.0.0.1:8232"}
OUTPUT_DIR="results/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUTPUT_DIR"

echo "🔬 Running comprehensive analysis suite..."
echo "📁 Output directory: $OUTPUT_DIR"
echo ""

# Quick analysis
echo "⚡ Running quick analysis..."
$ANALYZER "$LIGHTWALLETD" "$ZEBRAD" quick "$OUTPUT_DIR/quick.csv"

# Recommended analysis
echo "📊 Running recommended analysis..."
$ANALYZER "$LIGHTWALLETD" "$ZEBRAD" recommended "$OUTPUT_DIR/recommended.csv"

# Generate visualizations
echo "📈 Generating visualizations..."
cd visualization
source venv/bin/activate
python visualize.py "../$OUTPUT_DIR/recommended.csv" -o "../$OUTPUT_DIR/charts"
cd ..

echo ""
echo "✅ Analysis complete!"
echo "📊 Results in: $OUTPUT_DIR"
echo "📈 Charts in: $OUTPUT_DIR/charts"
echo "📄 Report: $OUTPUT_DIR/charts/statistical_report.txt"
