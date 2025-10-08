# Architecture

## System Overview

```
┌─────────────┐         ┌──────────────┐
│ Lightwalletd│◄────────┤   Analyzer   │
│   (gRPC)    │         │   (Rust)     │
└─────────────┘         └──────┬───────┘
                               │
┌─────────────┐                │
│   Zebrad    │◄───────────────┘
│ (JSON-RPC)  │
└─────────────┘

        │
        ├─────► CSV Output
        │
        ▼
┌──────────────┐
│ Visualizer   │
│  (Python)    │
└──────┬───────┘
       │
       ├─────► Charts (PNG)
       └─────► Statistical Report (TXT)
```

## Data Flow

1. **Sampling**: Generate block heights to analyze
2. **Fetch Real Data**: Get CompactBlock from lightwalletd
3. **Fetch Full Data**: Get full block from Zebrad
4. **Estimate**: Calculate transparent overhead
5. **Output**: Write to CSV
6. **Visualize**: Generate charts and statistics

## Key Components

### Sampling Module
- Multiple strategies (equal, proportional, hybrid, etc.)
- Era-aware sampling
- Reproducible with fixed seeds

### Estimator Module
- Protobuf size calculations
- Transparent I/O overhead estimation
- Accurate field-level sizing

### RPC Clients
- gRPC client for lightwalletd
- JSON-RPC client for Zebrad
- Error handling and retries

### Visualizer
- Statistical analysis
- Chart generation
- Decision recommendations
