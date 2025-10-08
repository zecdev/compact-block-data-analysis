# Results Directory

This directory contains analysis outputs. Each run creates a timestamped subdirectory:

```
results/
├── 20250108_143022/
│   ├── recommended.csv          # Raw data
│   ├── charts/                  # Generated visualizations
│   │   ├── distribution.png
│   │   ├── time_series.png
│   │   ├── by_era.png
│   │   ├── correlations.png
│   │   ├── cumulative.png
│   │   ├── bandwidth_impact.png
│   │   ├── heatmap.png
│   │   └── statistical_report.txt
│   └── ...
└── 20250108_150314/
    └── ...
```

Results are gitignored to avoid bloating the repository.
To save results permanently, copy them elsewhere or commit specific files.
