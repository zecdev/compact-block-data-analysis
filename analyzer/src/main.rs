// Complete working implementation that fetches REAL data from Zebra and lightwalletd

use anyhow::Result;
use serde::{Deserialize, Serialize};

// Include generated gRPC client code
pub mod cash {
    pub mod z {
        pub mod wallet {
            pub mod sdk {
                pub mod rpc {
                    tonic::include_proto!("cash.z.wallet.sdk.rpc");
                }
            }
        }
    }
}

use cash::z::wallet::sdk::rpc::{
    compact_tx_streamer_client::CompactTxStreamerClient, BlockId, BlockRange,
};

// Import sampling module
mod sampling;
use sampling::*;

// Zebra RPC response structures
#[derive(Debug, Deserialize)]
struct ZebraBlock {
    hash: String,
    height: u64,
    tx: Vec<ZebraTransaction>,
}

#[derive(Debug, Deserialize)]
struct ZebraTransaction {
    txid: String,
    vin: Vec<ZebraVin>,
    vout: Vec<ZebraVout>,
}

#[derive(Debug, Deserialize)]
struct ZebraVin {
    txid: Option<String>,
    vout: Option<u32>,
    #[serde(rename = "scriptSig")]
    script_sig: Option<ScriptSig>,
    sequence: u32,
}

#[derive(Debug, Deserialize)]
struct ScriptSig {
    hex: String,
}

#[derive(Debug, Deserialize)]
struct ZebraVout {
    value: f64,
    n: u32,
    #[serde(rename = "scriptPubKey")]
    script_pubkey: ScriptPubKey,
}

#[derive(Debug, Deserialize)]
struct ScriptPubKey {
    hex: String,
}

// Analysis results
#[derive(Debug, Serialize)]
struct BlockAnalysis {
    height: u64,
    era: String,
    current_compact_size: usize,
    estimated_with_transparent: usize,
    delta_bytes: i64,
    delta_percent: f64,
    tx_count: usize,
    transparent_inputs: usize,
    transparent_outputs: usize,
}

struct TransparentEstimator {
    zebra_rpc_url: String,
    lightwalletd_url: String,
    http_client: reqwest::Client,
}

impl TransparentEstimator {
    fn new(zebra_rpc_url: String, lightwalletd_url: String) -> Self {
        Self {
            zebra_rpc_url,
            lightwalletd_url,
            http_client: reqwest::Client::new(),
        }
    }

    async fn get_current_tip(&self) -> Result<u64> {
        let request = serde_json::json!({
            "jsonrpc": "2.0",
            "method": "getblockcount",
            "params": [],
            "id": 1
        });

        let response: serde_json::Value = self
            .http_client
            .post(&self.zebra_rpc_url)
            .json(&request)
            .send()
            .await?
            .json()
            .await?;

        let tip = response["result"]
            .as_u64()
            .ok_or_else(|| anyhow::anyhow!("Failed to get block count"))?;

        Ok(tip)
    }

    async fn get_compact_block_from_lightwalletd(&self, height: u64) -> Result<Vec<u8>> {
        // Connect to lightwalletd gRPC service
        let mut client = CompactTxStreamerClient::connect(self.lightwalletd_url.clone()).await?;

        // Request a single block by creating a range with start=end=height
        let request = tonic::Request::new(BlockRange {
            start: Some(BlockId {
                height: height as u64,
                hash: vec![],
            }),
            end: Some(BlockId {
                height: height as u64,
                hash: vec![],
            }),
        });

        // Get the block stream (will have just one block)
        let mut stream = client.get_block_range(request).await?.into_inner();

        // Get the single block from the stream
        if let Some(compact_block) = stream.message().await? {
            // Encode the CompactBlock to bytes to measure its actual size
            use prost::Message;
            let mut buf = Vec::new();
            compact_block.encode(&mut buf)?;
            return Ok(buf);
        }

        anyhow::bail!("Block {} not found in lightwalletd", height)
    }

    async fn get_full_block_from_zebra(&self, height: u64) -> Result<ZebraBlock> {
        let request = serde_json::json!({
            "jsonrpc": "2.0",
            "method": "getblock",
            "params": [height.to_string(), 2],
            "id": 1
        });

        let response: serde_json::Value = self
            .http_client
            .post(&self.zebra_rpc_url)
            .json(&request)
            .send()
            .await?
            .json()
            .await?;

        let block: ZebraBlock = serde_json::from_value(response["result"].clone())?;
        Ok(block)
    }

    fn estimate_transparent_overhead(&self, block: &ZebraBlock) -> (usize, usize, usize) {
        // Estimate protobuf size for transparent data based on actual PR definitions:
        //
        // message OutPoint {
        //     bytes txid = 1;        // 32 bytes
        //     uint32 index = 2;      // varint
        // }
        //
        // message CompactTxIn {
        //     OutPoint prevout = 1;  // nested message
        // }
        //
        // For coinbase, we'll estimate a fixed overhead since the .proto isn't finalized yet
        //
        // message TxOut {
        //     uint32 value = 1;      // varint (note: uint32, not uint64!)
        //     bytes scriptPubKey = 2; // variable length
        // }
        //
        // CompactTx gets:
        //     repeated CompactTxIn vin = 7;
        //     repeated TxOut vout = 8;

        let mut total_overhead = 0;
        let mut input_count = 0;
        let mut output_count = 0;

        for tx in &block.tx {
            // Estimate CompactTxIn (repeated field in CompactTx)
            for vin in &tx.vin {
                if let (Some(_txid), Some(vout_idx)) = (&vin.txid, &vin.vout) {
                    // Regular transparent input (not a coinbase)

                    // OutPoint message size:
                    let mut outpoint_size = 0;

                    // Field 1: bytes txid = 32 bytes
                    // Tag (1 byte) + length varint (1 byte) + 32 bytes
                    outpoint_size += 1 + 1 + 32;

                    // Field 2: uint32 index (varint)
                    // Tag (1 byte) + varint value (1-5 bytes, typically 1-2)
                    outpoint_size += 1 + Self::varint_size(*vout_idx as usize);

                    // CompactTxIn wraps OutPoint as field 1
                    let mut compact_txin_size = 0;
                    // Tag for field 1 (1 byte) + length of OutPoint + OutPoint data
                    compact_txin_size += 1 + Self::varint_size(outpoint_size) + outpoint_size;

                    // This CompactTxIn is in a repeated field (vin = 7) in CompactTx
                    // Tag for repeated field (1 byte) + length + message
                    let vin_entry_size =
                        1 + Self::varint_size(compact_txin_size) + compact_txin_size;

                    total_overhead += vin_entry_size;
                    input_count += 1;
                } else {
                    // Coinbase input
                    // Since the .proto isn't finalized, we estimate a fixed size
                    // Typical coinbase: ~40-100 bytes of data + sequence
                    // Conservative estimate for CompactTxIn with coinbase:
                    // - Field tag for coinbase data: 1 byte
                    // - Length prefix: 1 byte (for typical 40-100 byte coinbase)
                    // - Coinbase data: ~70 bytes average
                    // - Field tag for sequence: 1 byte
                    // - Sequence value: 4 bytes
                    // - Repeated field overhead: 1 byte tag + 1 byte length
                    // Total: ~79 bytes

                    const COINBASE_COMPACT_TXIN_SIZE: usize = 79;
                    total_overhead += COINBASE_COMPACT_TXIN_SIZE;
                    input_count += 1;
                }
            }

            // Estimate TxOut (repeated field in CompactTx)
            for vout in &tx.vout {
                let mut txout_size = 0;

                // Field 1: uint32 value (varint)
                let value_zatoshis = (vout.value * 100_000_000.0) as u64;
                txout_size += 1 + Self::varint_size(value_zatoshis as usize);

                // Field 2: bytes scriptPubKey
                let script_len = vout.script_pubkey.hex.len() / 2; // hex to bytes
                txout_size += 1 + Self::varint_size(script_len) + script_len;

                // This TxOut is in a repeated field (vout = 8) in CompactTx
                // Tag for repeated field (1 byte) + length + message
                let vout_entry_size = 1 + Self::varint_size(txout_size) + txout_size;

                total_overhead += vout_entry_size;
                output_count += 1;
            }
        }

        (total_overhead, input_count, output_count)
    }

    fn varint_size(value: usize) -> usize {
        // Protobuf varint encoding size
        match value {
            0..=127 => 1,
            128..=16383 => 2,
            16384..=2097151 => 3,
            2097152..=268435455 => 4,
            _ => 5,
        }
    }

    async fn analyze_block(&self, height: u64) -> Result<BlockAnalysis> {
        // Get actual compact block from lightwalletd
        let compact_block_bytes = self.get_compact_block_from_lightwalletd(height).await?;
        let current_size = compact_block_bytes.len();

        // Get full block from Zebra to calculate transparent overhead
        let full_block = self.get_full_block_from_zebra(height).await?;
        let (transparent_overhead, input_count, output_count) =
            self.estimate_transparent_overhead(&full_block);

        let estimated_size = current_size + transparent_overhead;
        let delta = estimated_size as i64 - current_size as i64;
        let delta_percent = if current_size > 0 {
            (delta as f64 / current_size as f64) * 100.0
        } else {
            0.0
        };

        Ok(BlockAnalysis {
            height,
            era: String::new(), // Will be set by analyze_blocks
            current_compact_size: current_size,
            estimated_with_transparent: estimated_size,
            delta_bytes: delta,
            delta_percent,
            tx_count: full_block.tx.len(),
            transparent_inputs: input_count,
            transparent_outputs: output_count,
        })
    }

    async fn analyze_blocks(&self, heights: &[u64]) -> Result<Vec<BlockAnalysis>> {
        let mut results = Vec::new();
        let total = heights.len();
        let eras = Era::zcash_eras(*heights.last().unwrap_or(&2_400_000));

        for (i, &height) in heights.iter().enumerate() {
            if i % 10 == 0 {
                println!(
                    "Progress: {}/{} ({:.1}%)",
                    i,
                    total,
                    (i as f64 / total as f64) * 100.0
                );
            }

            match self.analyze_block(height).await {
                Ok(mut analysis) => {
                    analysis.era = Era::get_era_for_height(height, &eras);
                    println!(
                        "Block {}: current={} bytes, estimated={} bytes, delta=+{} bytes ({:.2}%), era={}",
                        height,
                        analysis.current_compact_size,
                        analysis.estimated_with_transparent,
                        analysis.delta_bytes,
                        analysis.delta_percent,
                        analysis.era
                    );
                    results.push(analysis);
                }
                Err(e) => {
                    eprintln!("Error analyzing block {}: {}", height, e);
                }
            }

            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }

        println!("Progress: {}/{} (100.0%)", total, total);
        Ok(results)
    }

    fn write_csv(&self, results: &[BlockAnalysis], filename: &str) -> Result<()> {
        let mut wtr = csv::Writer::from_path(filename)?;
        for result in results {
            wtr.serialize(result)?;
        }
        wtr.flush()?;
        Ok(())
    }

    fn print_summary(&self, results: &[BlockAnalysis]) {
        if results.is_empty() {
            return;
        }

        let total_current: usize = results.iter().map(|r| r.current_compact_size).sum();
        let total_estimated: usize = results.iter().map(|r| r.estimated_with_transparent).sum();
        let total_delta = total_estimated as i64 - total_current as i64;

        let mut deltas: Vec<f64> = results.iter().map(|r| r.delta_percent).collect();
        deltas.sort_by(|a, b| a.partial_cmp(b).unwrap());

        let median = deltas[deltas.len() / 2];
        let p95_idx = ((deltas.len() as f64) * 0.95) as usize;
        let p95 = deltas[p95_idx.min(deltas.len() - 1)];

        println!("\n=== ANALYSIS SUMMARY ===");
        println!("Blocks analyzed: {}", results.len());
        println!("\nCurrent compact blocks:");
        println!(
            "  Total: {} bytes ({:.2} MB)",
            total_current,
            total_current as f64 / 1_000_000.0
        );
        println!("\nWith transparent data:");
        println!(
            "  Estimated total: {} bytes ({:.2} MB)",
            total_estimated,
            total_estimated as f64 / 1_000_000.0
        );
        println!(
            "  Delta: +{} bytes ({:.2} MB)",
            total_delta,
            total_delta as f64 / 1_000_000.0
        );
        println!(
            "  Overall increase: {:.2}%",
            (total_delta as f64 / total_current as f64) * 100.0
        );
        println!("\nPer-block statistics:");
        println!("  Median increase: {:.2}%", median);
        println!("  95th percentile: {:.2}%", p95);
        println!("  Min: {:.2}%", deltas[0]);
        println!("  Max: {:.2}%", deltas[deltas.len() - 1]);

        // Practical impact examples
        println!("\nPractical impact:");
        let blocks_per_day = 1152; // Post-Blossom (75s blocks)
        let daily_current = (total_current as f64 / results.len() as f64) * blocks_per_day as f64;
        let daily_estimated =
            (total_estimated as f64 / results.len() as f64) * blocks_per_day as f64;
        println!(
            "  Current daily sync (~{} blocks): {:.2} MB",
            blocks_per_day,
            daily_current / 1_000_000.0
        );
        println!(
            "  With transparent: {:.2} MB",
            daily_estimated / 1_000_000.0
        );
        println!(
            "  Additional bandwidth per day: {:.2} MB",
            (daily_estimated - daily_current) / 1_000_000.0
        );
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 4 {
        eprintln!(
            "Usage: {} <lightwalletd-grpc-url> <zebrad-rpc-url> <mode> [output.csv]",
            args[0]
        );
        eprintln!();
        eprintln!("Modes:");
        eprintln!("  range <start> <end>     - Analyze specific block range");
        eprintln!("  quick                   - Quick sampling (~1500 blocks)");
        eprintln!("  recommended             - Balanced sampling (~5000 blocks)");
        eprintln!("  thorough                - Thorough sampling (~11000 blocks)");
        eprintln!("  equal                   - Equal samples per era (~4000 blocks)");
        eprintln!("  proportional            - Proportional to era size (~5000 blocks)");
        eprintln!("  weighted                - Weighted toward recent (~5000 blocks)");
        eprintln!();
        eprintln!("Examples:");
        eprintln!(
            "  {} http://127.0.0.1:9067 http://127.0.0.1:8232 range 2400000 2401000",
            args[0]
        );
        eprintln!(
            "  {} http://127.0.0.1:9067 http://127.0.0.1:8232 recommended results.csv",
            args[0]
        );
        std::process::exit(1);
    }

    let lightwalletd_url = &args[1];
    let zebra_rpc_url = &args[2];
    let mode = &args[3];

    // Get current tip from Zebra
    let estimator =
        TransparentEstimator::new(zebra_rpc_url.to_string(), lightwalletd_url.to_string());

    let current_tip = estimator.get_current_tip().await?;
    println!("Current blockchain tip: {}", current_tip);
    println!();

    let (blocks, output_file) = match mode.as_str() {
        "range" => {
            if args.len() < 6 {
                eprintln!("Error: range mode requires <start> <end>");
                std::process::exit(1);
            }
            let start: u64 = args[4].parse()?;
            let end: u64 = args[5].parse()?;
            let output = args.get(6).map(|s| s.as_str()).unwrap_or("results.csv");
            ((start..=end).collect(), output.to_string())
        }
        "quick" => {
            let sampler = create_quick_sampler(current_tip);
            println!("{}", sampler.describe());
            let output = args
                .get(4)
                .map(|s| s.as_str())
                .unwrap_or("quick_sample.csv");
            (sampler.generate_samples(), output.to_string())
        }
        "recommended" => {
            let sampler = create_recommended_sampler(current_tip);
            println!("{}", sampler.describe());
            let output = args
                .get(4)
                .map(|s| s.as_str())
                .unwrap_or("recommended_sample.csv");
            (sampler.generate_samples(), output.to_string())
        }
        "thorough" => {
            let sampler = create_thorough_sampler(current_tip);
            println!("{}", sampler.describe());
            let output = args
                .get(4)
                .map(|s| s.as_str())
                .unwrap_or("thorough_sample.csv");
            (sampler.generate_samples(), output.to_string())
        }
        "equal" => {
            let sampler = create_equal_sampler(current_tip);
            println!("{}", sampler.describe());
            let output = args
                .get(4)
                .map(|s| s.as_str())
                .unwrap_or("equal_sample.csv");
            (sampler.generate_samples(), output.to_string())
        }
        "proportional" => {
            let sampler = create_proportional_sampler(current_tip);
            println!("{}", sampler.describe());
            let output = args
                .get(4)
                .map(|s| s.as_str())
                .unwrap_or("proportional_sample.csv");
            (sampler.generate_samples(), output.to_string())
        }
        "weighted" => {
            let sampler = create_weighted_sampler(current_tip);
            println!("{}", sampler.describe());
            let output = args
                .get(4)
                .map(|s| s.as_str())
                .unwrap_or("weighted_sample.csv");
            (sampler.generate_samples(), output.to_string())
        }
        _ => {
            eprintln!("Error: Unknown mode '{}'", mode);
            std::process::exit(1);
        }
    };

    println!("Analyzing {} blocks...", blocks.len());
    println!(
        "Fetching real compact blocks from lightwalletd: {}",
        lightwalletd_url
    );
    println!("Fetching full blocks from Zebra: {}", zebra_rpc_url);
    println!();

    let results = estimator.analyze_blocks(&blocks).await?;

    estimator.write_csv(&results, &output_file)?;
    println!("\nDetailed results written to: {}", output_file);

    estimator.print_summary(&results);

    Ok(())
}
