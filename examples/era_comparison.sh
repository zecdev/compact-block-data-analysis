#!/bin/bash
# Compare overhead across different eras

cd "$(dirname "$0")/.."
ANALYZER="./analyzer/target/release/compact-block-analyzer"
OUTPUT="results/era_comparison_$(date +%Y%m%d)"
mkdir -p "$OUTPUT"

echo "🔬 Running era comparison analysis..."

# Sample each era
echo "📊 Analyzing Sapling era..."
$ANALYZER http://127.0.0.1:9067 http://127.0.0.1:8232 range 500000 500500 "$OUTPUT/sapling.csv"

echo "📊 Analyzing Blossom era..."
$ANALYZER http://127.0.0.1:9067 http://127.0.0.1:8232 range 750000 750500 "$OUTPUT/blossom.csv"

echo "📊 Analyzing Canopy era..."
$ANALYZER http://127.0.0.1:9067 http://127.0.0.1:8232 range 1300000 1300500 "$OUTPUT/canopy.csv"

echo "📊 Analyzing NU5 era..."
$ANALYZER http://127.0.0.1:9067 http://127.0.0.1:8232 range 2000000 2000500 "$OUTPUT/nu5.csv"

echo "📊 Analyzing NU6 era..."
$ANALYZER http://127.0.0.1:9067 http://127.0.0.1:8232 range 2800000 2800500 "$OUTPUT/nu6.csv"

# Visualize each
echo "📈 Generating visualizations..."
cd visualization
source venv/bin/activate
for csv in "../$OUTPUT"/*.csv; do
    basename="${csv%.csv}"
    python visualize.py "$csv" -o "${basename}_charts"
done
cd ..

echo "✅ Era comparison complete: $OUTPUT"
