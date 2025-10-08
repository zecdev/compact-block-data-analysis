# Compact Block Analyzer for Zcash

A tool to analyze the bandwidth impact of adding transparent transaction data (`CompactTxIn` and `TxOut`) to Zcash's compact block protocol.

## Overview

This analyzer helps evaluate the proposed changes to the [lightwallet-protocol](https://github.com/zcash/lightwallet-protocol/pull/1) by measuring:

- Current compact block sizes from production lightwalletd
- Estimated sizes with transparent input/output data added
- Bandwidth impact on light clients syncing block ranges

The tool fetches **real compact blocks** from lightwalletd and compares them against estimated sizes calculated from full block data in Zebrad, giving accurate projections of the bandwidth impact.

## Background

The Zcash light client protocol currently omits transparent transaction inputs and outputs from compact blocks. [PR #1](https://github.com/zcash/lightwallet-protocol/pull/1) proposes adding:

- `CompactTxIn` - references to transparent inputs being spent
- `TxOut` - transparent outputs being created

This analysis helps decide whether to:
- Make transparent data part of the default `GetBlockRange` RPC
- Create a separate opt-in method for clients that need it
- Use pool-based filtering (as implemented in [librustzcash PR #1781](https://github.com/zcash/librustzcash/pull/1781))

## Prerequisites

- **Rust** 1.70+ ([install](https://rustup.rs/))
- **Zebrad** - synced Zcash full node with RPC enabled
- **Lightwalletd** - connected to your Zebrad instance

## Installation

### 1. Clone and Setup

```bash
# Create the project
cargo new compact_block_analyzer
cd compact_block_analyzer

# Create proto directory
mkdir proto
```

### 2. Get Protocol Buffer Definitions

```bash
# Clone the lightwallet-protocol repository
git clone https://github.com/zcash/lightwallet-protocol.git
cd lightwallet-protocol

# Checkout the PR with transparent data additions
git fetch origin pull/1/head:pr-1
git checkout pr-1

# Copy proto files to your project
cp compact_formats.proto ../compact_block_analyzer/proto/
cp service.proto ../compact_block_analyzer/proto/

cd ../compact_block_analyzer
```

### 3. Configure Build

Create `build.rs` in the project root:

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(false)  // Client only
        .compile(
            &["proto/service.proto", "proto/compact_formats.proto"],
            &["proto/"],
        )?;
    Ok(())
}
```

### 4. Update Dependencies

Replace `Cargo.toml` with the dependencies from the artifact, or copy `src/main.rs` from the artifact which includes the dependency list.

### 5. Build

```bash
cargo build --release
```

## Usage

### Start Required Services

#### Zebrad
```bash
# If not already running
zebrad start
```

Verify RPC is accessible:
```bash
curl -X POST http://127.0.0.1:8232 \
  -d '{"method":"getblockcount","params":[],"id":1}'
```

#### Lightwalletd
```bash
lightwalletd \
  --grpc-bind-addr=127.0.0.1:9067 \
  --zcash-conf-path=/path/to/zebra.conf \
  --log-file=/dev/stdout
```

Verify lightwalletd is running:
```bash
# With grpcurl installed
grpcurl -plaintext localhost:9067 list
# Should show: cash.z.wallet.sdk.rpc.CompactTxStreamer
```

### Run Analysis

The tool supports multiple analysis modes:

#### Quick Analysis (~1,500 blocks)
```bash
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  quick \
  quick_results.csv
```

#### Recommended Analysis (~5,000 blocks) - Best Balance
```bash
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  recommended \
  results.csv
```

This uses a **hybrid sampling strategy**:
- 750 samples from each protocol era (pre-Sapling, Sapling, Canopy, NU5)
- 2,000 additional samples from recent blocks (last 100K)
- Provides balanced historical context with focus on current usage

#### Thorough Analysis (~11,000 blocks)
```bash
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  thorough \
  thorough_results.csv
```

#### Equal Sampling Per Era (~4,000 blocks)
```bash
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  equal \
  equal_results.csv
```

#### Proportional Sampling (~5,000 blocks)
```bash
# Samples proportionally to era size
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  proportional \
  proportional_results.csv
```

#### Weighted Sampling (~5,000 blocks)
```bash
# Custom weights favoring recent blocks
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  weighted \
  weighted_results.csv
```

#### Specific Range (Original Mode)
```bash
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  range 2400000 2401000 \
  range_results.csv
```

### Sampling Strategies Explained

**Why use sampling?** The Zcash blockchain has 2.4M+ blocks. Analyzing every block would take days. Statistical sampling gives accurate results in minutes.

| Strategy | Description | Best For |
|----------|-------------|----------|
| **Quick** | Fast overview with fewer samples | Initial exploration |
| **Recommended** | Balanced approach with recent focus | Most use cases |
| **Thorough** | Comprehensive coverage | Final analysis |
| **Equal** | Same samples per era | Era comparison |
| **Proportional** | Samples match blockchain distribution | Representing whole chain |
| **Weighted** | More recent, less historical | Current state focus |

### Visualize Results

After running the analysis, generate charts and statistics:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Generate all visualizations
python visualize.py results.csv --output-dir ./charts
```

This creates:
- **distribution.png** - Histogram and box plot of overhead
- **time_series.png** - Overhead trends over blockchain height
- **by_era.png** - Comparison across protocol eras
- **correlations.png** - Relationship between overhead and transaction characteristics
- **cumulative.png** - Cumulative distribution functions
- **bandwidth_impact.png** - Practical bandwidth scenarios
- **heatmap.png** - Overhead by era and transaction patterns
- **statistical_report.txt** - Comprehensive statistical analysis

### Example Output

**Console output during analysis:**
```
Current blockchain tip: 2450000

Sampling Strategy: HybridRecent
Total samples: 5000

Distribution by era:
  pre_sapling: 750 samples (15.0% of total, 1 in 559 blocks)
  sapling: 750 samples (15.0% of total, 1 in 836 blocks)
  canopy: 750 samples (15.0% of total, 1 in 854 blocks)
  nu5: 2750 samples (55.0% of total, 1 in 295 blocks)

Analyzing 5000 blocks...
Progress: 0/5000 (0.0%)
Progress: 500/5000 (10.0%)
...

=== ANALYSIS SUMMARY ===
Blocks analyzed: 5000
Current compact blocks:
  Total: 76.23 MB
With transparent data:
  Estimated total: 93.45 MB
  Delta: +17.22 MB
  Overall increase: 22.58%

Per-block statistics:
  Median increase: 18.45%
  95th percentile: 35.21%
  Min: 5.32%
  Max: 47.83%

Practical impact:
  Current daily sync (~2880 blocks): 43.86 MB
  With transparent: 53.75 MB
  Additional bandwidth per day: 9.89 MB
```

**Statistical report snippet:**
```
DECISION FRAMEWORK
--------------------------------------------------------------------------------
Median overhead: 18.5%
95th percentile: 35.2%

RECOMMENDATION: LOW IMPACT
  The overhead is relatively small (<20%). Consider making transparent
  data part of the default GetBlockRange method. This would:
  - Simplify the API (single method)
  - Provide feature parity with full nodes
  - Have minimal bandwidth impact on users
```

## Output

### Console Output

The tool provides real-time progress and summary statistics during analysis.

### CSV Output

Detailed per-block analysis in CSV format:

```csv
height,era,current_compact_size,estimated_with_transparent,delta_bytes,delta_percent,tx_count,transparent_inputs,transparent_outputs
2400000,nu5,15234,18456,3222,21.15,45,12,89
2400001,nu5,12890,14234,1344,10.43,32,5,43
...
```

### Visualization Output

The Python script generates comprehensive visualizations:

1. **Distribution Analysis**
   - Histogram with kernel density estimation
   - Box plot showing quartiles and outliers
   - Marked median and mean values

2. **Time Series Analysis**
   - Overhead percentage over blockchain height
   - Absolute size increase over time
   - Rolling averages to show trends
   - Era boundaries marked

3. **Era Comparison**
   - Box plots comparing distributions across eras
   - Violin plots showing density
   - Bar charts with standard deviations
   - Sample size distribution

4. **Correlation Analysis**
   - Overhead vs transparent inputs
   - Overhead vs transparent outputs
   - Overhead vs transaction count
   - Overhead vs current block size

5. **Cumulative Distribution**
   - CDF of overhead percentages
   - CDF of absolute byte increases
   - Percentile markers (P50, P75, P90, P95, P99)

6. **Bandwidth Impact**
   - Daily sync bandwidth comparison
   - Full chain sync comparison
   - Mobile data cost estimates
   - Sync time projections

7. **Heatmaps**
   - Overhead by era and transaction count
   - Overhead by era and transparent I/O

8. **Statistical Report**
   - Summary statistics with confidence intervals
   - Statistics broken down by era
   - Practical bandwidth calculations
   - Correlation coefficients
   - Decision framework recommendations

## How It Works

1. **Fetch real compact block** from lightwalletd via gRPC
   - Gets the actual production compact block size
   - Includes all current fields (Sapling outputs, Orchard actions, etc.)

2. **Fetch full block** from Zebrad via RPC
   - Gets transparent input/output data
   - Provides transaction details needed for estimation

3. **Calculate overhead** using protobuf encoding rules
   - Estimates size of `CompactTxIn` messages (containing `OutPoint`)
   - Estimates size of `TxOut` messages (value + scriptPubKey)
   - Accounts for protobuf field tags, length prefixes, and nested messages

4. **Compare and report**
   - Current size vs. estimated size with transparent data
   - Per-block and aggregate statistics

## Protobuf Size Estimation

The estimator calculates sizes based on the proposed proto definitions:

```protobuf
message OutPoint {
    bytes txid = 1;      // 32 bytes
    uint32 index = 2;    // varint
}

message CompactTxIn {
    OutPoint prevout = 1;
}

message TxOut {
    uint32 value = 1;         // varint
    bytes scriptPubKey = 2;   // variable length
}
```

Added to `CompactTx`:
```protobuf
repeated CompactTxIn vin = 7;
repeated TxOut vout = 8;
```

The calculation includes:
- Field tags (1 byte per field)
- Length prefixes for bytes and nested messages (varint)
- Actual data sizes
- Nested message overhead

## Interpreting Results

### Decision Guidelines

- **< 20% increase**: Consider making transparent data default
  - Minimal impact on bandwidth
  - Simplifies API (single method)
  - Better for light client feature parity

- **20-50% increase**: Consider separate opt-in method
  - Significant but manageable overhead
  - Let clients choose based on their needs
  - Pool filtering could help (librustzcash PR #1781)

- **> 50% increase**: Likely needs separate method
  - Major bandwidth impact
  - Important for mobile/limited bandwidth users
  - Clear opt-in for clients that need transparent data

### Key Metrics to Examine

1. **Median increase** - typical overhead
2. **95th percentile** - worst-case for active blocks
3. **Daily bandwidth impact** - practical cost for staying synced
4. **Initial sync impact** - multiply by ~2.4M blocks
5. **Correlation with transparent usage** - understand which blocks drive overhead

## Troubleshooting

### Connection Errors

**Port 9067 (lightwalletd):**
```bash
# Check if running
ps aux | grep lightwalletd
netstat -tlnp | grep 9067

# Test connection
grpcurl -plaintext localhost:9067 list
```

**Port 8232 (zebrad):**
```bash
# Check if running
ps aux | grep zebrad
netstat -tlnp | grep 8232

# Test RPC
curl -X POST http://127.0.0.1:8232 \
  -d '{"method":"getblockcount","params":[],"id":1}'
```

### Build Errors

**Proto compilation fails:**
```bash
# Ensure proto files exist
ls -la proto/

# Clean and rebuild
cargo clean
cargo build --release
```

**"Block not found" errors:**
- Check if block height exists on mainnet
- Verify Zebrad is fully synced
- Ensure lightwalletd has indexed the blocks

### Rate Limiting

The tool includes a 100ms delay between blocks to avoid overwhelming your node. For faster analysis:

1. Reduce the delay in the code
2. Run multiple instances for different ranges
3. Use a more powerful machine for Zebrad

## Contributing

This tool is designed for protocol analysis. Contributions welcome:

- Improved size estimation accuracy
- Additional output formats (JSON, charts)
- Statistical analysis enhancements
- Performance optimizations

## Related Work

- [lightwallet-protocol PR #1](https://github.com/zcash/lightwallet-protocol/pull/1) - Proto definitions
- [librustzcash PR #1781](https://github.com/zcash/librustzcash/pull/1781) - Pool filtering implementation
- [Zcash Protocol Specification](https://zips.z.cash/) - Full protocol details

## License

Same license as the Zcash lightwallet-protocol project.

## Support

For questions or issues:
- Open an issue in this repository
- Discuss on Zcash Community Forum
- Zcash R&D Discord

## Acknowledgments

Built to support analysis for improving Zcash light client protocol bandwidth efficiency.
