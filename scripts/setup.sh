#!/bin/bash
set -e

echo "Setting up Compact Block Analyzer..."

# Check prerequisites
command -v rustc >/dev/null 2>&1 || { echo "Rust not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python3 not installed"; exit 1; }

# Fetch proto files
./scripts/fetch_protos.sh

# Build Rust analyzer
cd analyzer
cargo build --release
cd ..

# Setup Python environment
cd visualization
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

echo "✅ Setup complete!"
echo "Run: cd analyzer && cargo run --release -- --help"
