#!/bin/bash
cd "$(dirname "$0")/.."
./analyzer/target/release/compact-block-analyzer \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  recommended \
  results/recommended_$(date +%Y%m%d).csv
