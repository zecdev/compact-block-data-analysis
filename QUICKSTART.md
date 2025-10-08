# Quick Start Guide

Get started analyzing Zcash compact block overhead in 5 minutes.

## Prerequisites Check

```bash
# Check Rust is installed
rustc --version

# Check Python is installed  
python --version  # Should be 3.8+

# Check Zebrad is running
curl -X POST http://127.0.0.1:8232 -d '{"method":"getblockcount","params":[],"id":1}'

# Check lightwalletd is running
grpcurl -plaintext localhost:9067 list
```

## Setup (5 minutes)

### 1. Get the Project

```bash
cargo new compact_block_analyzer
cd compact_block_analyzer
mkdir proto
```

### 2. Get Protocol Buffers

```bash
# Clone the lightwallet-protocol repo
git clone https://github.com/zcash/lightwallet-protocol.git temp_proto
cd temp_proto
git fetch origin pull/1/head:pr-1
git checkout pr-1

# Copy proto files
cp compact_formats.proto ../proto/
cp service.proto ../proto/

cd ..
rm -rf temp_proto
```

### 3. Setup Build System

Create `build.rs`:
```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(false)
        .compile(
            &["proto/service.proto", "proto/compact_formats.proto"],
            &["proto/"],
        )?;
    Ok(())
}
```

### 4. Copy Code

Replace `Cargo.toml` and `src/main.rs` with the provided artifacts.

### 5. Build

```bash
cargo build --release
```

## Run Your First Analysis (2 minutes)

### Quick Test (100 blocks)

```bash
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  range 2400000 2400100 \
  test.csv
```

### Recommended Analysis (~30 minutes for 5000 blocks)

```bash
cargo run --release -- \
  http://127.0.0.1:9067 \
  http://127.0.0.1:8232 \
  recommended \
  results.csv
```

This will:
- Sample 5000 blocks strategically across all eras
- Take ~30 minutes (100ms delay between blocks)
- Provide statistically significant results

## Visualize Results (1 minute)

```bash
# Install Python dependencies
pip install pandas matplotlib seaborn numpy scipy

# Generate all charts
python visualize.py results.csv
```

Open `charts/statistical_report.txt` to see the analysis!

## Understanding the Output

### Key Metrics to Look At

1. **Median overhead** (in the report)
   - This is the "typical" overhead
   - Most important single number

2. **95th percentile** (in the report)
   - Worst-case planning
   - Important for capacity planning

3. **Distribution chart** (`charts/distribution.png`)
   - Shows the spread of overhead values
   - Look for the shape (normal, skewed, bimodal?)

4. **Bandwidth impact chart** (`charts/bandwidth_impact.png`)
   - Practical impact: MB per day, sync time, cost
   - This makes the numbers concrete

### Decision Framework

The report will tell you:

- **< 20% median overhead**: Low impact, consider making it default
- **20-50% median overhead**: Moderate impact, consider opt-in
- **> 50% median overhead**: High impact, needs separate method

## Common Issues

### "Connection refused" on port 9067
```bash
# Restart lightwalletd
lightwalletd --grpc-bind-addr=127.0.0.1:9067 --zcash-conf-path=/path/to/zebra.conf
```

### "Connection refused" on port 8232
```bash
# Check zebrad is running
ps aux | grep zebrad

# Check zebra.toml has RPC enabled
# Should have [rpc] section with listen_addr = "127.0.0.1:8232"
```

### Build errors about proto files
```bash
# Ensure proto files exist
ls -la proto/

# Clean and rebuild
cargo clean
cargo build --release
```

### Python import errors
```bash
# Install all dependencies
pip install -r requirements.txt
```

## Next Steps

### Experiment with Different Sampling

```bash
# Quick analysis (1500 blocks, ~15 minutes)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 quick quick.csv

# Thorough analysis (11000 blocks, ~2 hours)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 thorough thorough.csv

# Equal samples per era
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 equal equal.csv
```

### Compare Different Eras

```bash
# Pre-Sapling era (heavy transparent)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 100000 101000 pre_sapling.csv

# Recent blocks
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 2400000 2401000 recent.csv

# Visualize both
python visualize.py pre_sapling.csv -o charts_pre_sapling
python visualize.py recent.csv -o charts_recent
```

### Dive Deeper

- Read `statistical_report.txt` for detailed analysis
- Examine correlation charts to understand what drives overhead
- Look at heatmaps to see how overhead varies by transaction patterns
- Check time series to see trends over blockchain history

## Tips for Best Results

1. **Use 'recommended' mode** for most analyses
   - Balanced, statistically sound
   - Reasonable time (~30 minutes)

2. **Run multiple samples** if results seem unexpected
   - Sampling has some variance
   - Multiple runs can confirm findings

3. **Focus on recent blocks** for current decisions
   - Old blocks less relevant for current usage
   - But historical context helps understand trends

4. **Look at the whole picture**
   - Don't just look at mean/median
   - Check the distribution, outliers, worst-case

5. **Consider practical impact**
   - MB per day matters more than abstract percentages
   - Think about mobile users, limited bandwidth

## Getting Help

- Check `README.md` for full documentation
- Check `.claude_project_context.md` for technical details
- Check `AI_DISCLAIMER.md` for limitations
- Open an issue if you find bugs
- Validate results against your own calculations

Happy analyzing! 🚀
