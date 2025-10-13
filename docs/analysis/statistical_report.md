# Statistical Analysis Report

**Zcash Compact Block Transparent Data Overhead**

---

## Summary Statistics

- **Total blocks analyzed:** 13,984
- **Block height range:** 419,402 - 3,098,051

## Overhead Percentage

| Metric | Value |
|--------|-------|
| Mean   | 980.50% |
| Median | 173.81% |
| Std Dev| 6706.43% |
| Min    | 0.08% |
| Max    | 473783.33% |

## Percentiles

| Percentile | Overhead |
|------------|----------|
| P25 | 159.34% |
| P50 | 173.81% |
| P75 | 452.75% |
| P90 | 1657.47% |
| P95 | 3719.88% |
| P99 | 12968.45% |

### Cumulative

![Cumulative](docs/analysis/cumulative.png)

### Distribution
![Distribution](docs/analysis/distribution.png)

## Confidence Intervals (95%)

- **Mean overhead:** 980.50% ± 111.16%
- **Range:** [869.34%, 1091.67%]

## Statistics by Era

![Statistics by era](docs/analysis/by_era.png)
![heatmap by era](docs/analysis/heatmap.png)

| Era | Count | Mean | Std Dev | Median | Min | Max |
|-----|-------|------|---------|--------|-----|-----|
| Sapling | 1,500 | 3097.70% | 17510.41% | 540.90% | 18.55% | 473783.33% |
| Blossom | 1,500 | 1215.30% | 7770.75% | 303.57% | 1.58% | 281783.33% |
| Heartwood | 1,500 | 1435.15% | 2985.99% | 391.07% | 20.00% | 33155.95% |
| Canopy | 1,500 | 1777.54% | 4114.49% | 422.02% | 21.13% | 61611.90% |
| Nu5 | 1,500 | 633.78% | 4192.93% | 232.22% | 0.08% | 139238.89% |
| Nu6 | 6,484 | 227.05% | 518.88% | 159.34% | 0.65% | 19238.61% |

## Practical Bandwidth Impact

### Average Block Sizes

- **Current:** 2.13 KB
- **With transparent:** 3.75 KB
- **Delta:** 1.62 KB

### Daily Sync (~1152 blocks)

- **Current:** 2.46 MB
- **With transparent:** 4.32 MB
- **Additional:** 1.86 MB (75.9%)

![bandwidth impact](docs/analysis/bandwidth_impact.png)
## Correlations

![correlations](docs/analysis/correlations.png)

| Variables | Correlation (r) |
|-----------|----------------|
| Transparent inputs → delta bytes | 0.941 |
| Transparent outputs → delta bytes | 0.434 |
| Transaction count → overhead % | 0.136 |

## Decision Framework

- **Median overhead:** 173.8%
- **95th percentile:** 3719.9%

