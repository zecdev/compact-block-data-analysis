# Zcash Network Upgrades Reference

This document provides context for the protocol eras used in sampling and analysis.

## Network Upgrade Timeline

| Era | Activation Block | Date | Key Features |
|-----|-----------------|------|--------------|
| **Sapling** | 419,200 - 653,599 | Oct 2018 - Dec 2019 | New shielded pool, improved performance |
| **Blossom** | 653,600 - 903,799 | Dec 2019 - Jul 2020 | Block time 150s → 75s |
| **Heartwood** | 903,800 - 1,046,399 | Jul 2020 - Nov 2020 | Shielded coinbase, FlyClient |
| **Canopy** | 1,046,400 - 1,687,103 | Nov 2020 - May 2022 | Dev fund activation |
| **NU5** | 1,687,104 - 2,726,399 | May 2022 - Apr 2024 | Orchard pool, unified addresses |
| **NU6** | 2,726,400 - current | Apr 2024 - present | Current protocol |

## Why These Eras Matter for Analysis

### Sapling (419,200 - 653,599)
**Characteristics:**
- New efficient shielded pool introduced
- Gradual adoption of shielded transactions
- Transparent still common but declining
- Block time: 150 seconds

**Relevance to Analysis:**
- Transition period from transparent to shielded
- Mixed usage patterns
- Baseline for early shielded adoption

### Blossom (653,600 - 903,799)
**Characteristics:**
- **Block time reduced to 75 seconds**
- Twice as many blocks per day (from ~576 to ~1152)
- Continued Sapling adoption
- More blocks = more overhead for initial sync

**Relevance to Analysis:**
- **Critical**: Block time change affects bandwidth calculations
- Must account for 2x blocks per day after Blossom
- Same MB/block but different MB/day after this upgrade

### Heartwood (903,800 - 1,046,399)
**Characteristics:**
- Shielded coinbase enabled (miners can receive directly to Sapling)
- FlyClient support for light clients
- ZIP 213 (shielded coinbase)

**Relevance to Analysis:**
- Shielded coinbase reduces transparent coinbase outputs
- May show decrease in transparent transactions
- Short era but important transition

### Canopy (1,046,400 - 1,687,103)
**Characteristics:**
- Dev fund activation (20% of block rewards)
- Mature Sapling usage
- Longest single-upgrade era
- Stable protocol period

**Relevance to Analysis:**
- Good baseline for "normal" modern usage
- Large sample available
- Represents stable state before Orchard

### NU5 (1,687,104 - 2,726,399)
**Characteristics:**
- **Orchard pool introduced** (new shielded pool)
- **Unified addresses** (single address for all pools)
- Halo 2 proving system
- Transaction version 5

**Relevance to Analysis:**
- Introduction of Orchard changes transaction mix
- Unified addresses may affect usage patterns
- Large era, represents recent "stable" state

### NU6 (2,726,400 - current)
**Characteristics:**
- Current protocol version
- Most recent upgrade (April 2024)
- Active development and adoption

**Relevance to Analysis:**
- **Most relevant for current decisions**
- Represents actual current usage
- Should be heavily sampled
- Ongoing changes as ecosystem adapts

## Impact on Compact Block Analysis

### Transparent Usage Trends

```
Sapling:      ████████████░░░░░░░░ (High → Medium)
Blossom:      ████████░░░░░░░░░░░░ (Medium)
Heartwood:    ██████░░░░░░░░░░░░░░ (Medium → Low)
Canopy:       ████░░░░░░░░░░░░░░░░ (Low)
NU5:          ███░░░░░░░░░░░░░░░░░ (Low)
NU6:          ███░░░░░░░░░░░░░░░░░ (Low, current)
```

### Block Frequency (Important!)

**Before Blossom:**
- Block time: 150 seconds
- Blocks per day: ~576
- Daily bandwidth = avg_block_size × 576

**After Blossom:**
- Block time: 75 seconds  
- Blocks per day: ~1,152
- Daily bandwidth = avg_block_size × 1,152

⚠️ **When calculating daily bandwidth, account for this doubling after block 653,600!**

### Sampling Recommendations

**For Current State Analysis:**
- Focus on NU6 (current) and NU5 (recent stable)
- 60-70% of samples from these eras

**For Historical Context:**
- Sapling through Canopy shows evolution of usage patterns
- Important to understand how transparent usage declined

**For Bandwidth Calculations:**
- Separate pre-Blossom and post-Blossom blocks
- Use correct blocks/day multiplier
- Daily sync = avg_size × (576 or 1,152) depending on era

## Querying Specific Eras

```bash
# Sapling (transition period)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 500000 501000 sapling.csv

# Blossom (block time change)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 750000 751000 blossom.csv

# Heartwood (shielded coinbase)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 950000 951000 heartwood.csv

# Canopy (mature Sapling)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 1300000 1301000 canopy.csv

# NU5 (Orchard introduction)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 2000000 2001000 nu5.csv

# NU6 (current)
cargo run --release -- http://127.0.0.1:9067 http://127.0.0.1:8232 range 2800000 2801000 nu6.csv
```

## References

- [Zcash Network Upgrade Timeline](https://z.cash/upgrade/)
- [ZIP 200: Network Upgrade Mechanism](https://zips.z.cash/zip-0200)
- [ZIP 206: Deployment of the Blossom Network Upgrade](https://zips.z.cash/zip-0206)
- [ZIP 221: FlyClient - Consensus-Layer Changes](https://zips.z.cash/zip-0221)
- [ZIP 224: Orchard Shielded Protocol](https://zips.z.cash/zip-0224)
- [Zcash Protocol Specification](https://zips.z.cash/protocol/protocol.pdf)
