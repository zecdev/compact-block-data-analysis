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
    compact_tx_streamer_client::CompactTxStreamerClient, 
    BlockId, 
    BlockRange,
    CompactBlock,
};

// Zebra RPC structures
#[derive(Debug, Deserialize)]
struct ZebraBlock {
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

#[derive(Debug, Serialize)]
struct BlockAnalysis {
    height: u64,
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

    async fn get_compact_block_from_lightwalletd(&self, height: u64) -> Result<Vec<u8>> {
        // Connect to lightwalletd gRPC service
        let mut client = CompactTxStreamerClient::connect(self.lightwalletd_url.clone()).await?;
        
        // Request a single block by creating a range with start=end=height
        let request = tonic::Request::new(BlockRange {
            start: Some(BlockId { 
                height: height as u64, 
                hash: vec![] 
            }),
            end: Some(BlockId { 
                height: height as u64, 
                hash: vec![] 
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
        // Estimate protobuf size for transparent data based on PR definitions
        // 
        // CompactTxIn (from the PR):
        // - prevout_hash: bytes (32 bytes) -> ~34 bytes encoded (field tag + length + data)
        // - prevout_n: uint32 -> ~2-5 bytes encoded
        // - sequence: uint32 -> ~2-5 bytes encoded
        // - script_sig: bytes (variable) -> ~length+2 bytes encoded
        //
        // CompactTxOut (from the PR):
        // - value: int64 -> ~2-9 bytes encoded
        // - n: uint32 -> ~2-5 bytes encoded  
        // - script_pubkey: bytes (variable) -> ~length+2 bytes encoded

        let mut total_input_bytes = 0;
        let mut total_output_bytes = 0;
        let mut input_count = 0;
        let mut output_count = 0;

        for tx in &block.tx {
            // Estimate CompactTxIn overhead
            for vin in &tx.vin {
                if vin.txid.is_some() {
                    // Not a coinbase
                    let mut vin_size = 0;
                    
                    // prevout_hash: 32 bytes + protobuf overhead (~2 bytes for tag+len)
                    vin_size += 34;
                    
                    // prevout_n: varint, typically 1-2 bytes
                    vin_size += 2;
                    
                    // sequence: varint, typically 1-2 bytes  
                    vin_size += 2;
                    
                    // script_sig: variable length
                    if let Some(ref script) = vin.script_sig {
                        let script_len = script.hex.len() / 2; // hex to bytes
                        vin_size += 1 + Self::varint_size(script_len) + script_len;
                    }
                    
                    // Protobuf message overhead (field tag for the repeated field)
                    vin_size += 1 + Self::varint_size(vin_size);
                    
                    total_input_bytes += vin_size;
                    input_count += 1;
                }
            }

            // Estimate CompactTxOut overhead
            for vout in &tx.vout {
                let mut vout_size = 0;
                
                // value: int64, typically 1-9 bytes as varint
                vout_size += 9; // worst case
                
                // n: uint32, typically 1-2 bytes
                vout_size += 2;
                
                // script_pubkey: variable length
                let script_len = vout.script_pubkey.hex.len() / 2;
                vout_size += 1 + Self::varint_size(script_len) + script_len;
                
                // Protobuf message overhead
                vout_size += 1 + Self::varint_size(vout_size);
                
                total_output_bytes += vout_size;
                output_count += 1;
            }
        }

        (total_input_bytes + total_output_bytes, input_count, output_count)
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
            current_compact_size: current_size,
            estimated_with_transparent: estimated_size,
            delta_bytes: delta,
            delta_percent,
            tx_count: full_block.tx.len(),
            transparent_inputs: input_count,
            transparent_outputs: output_count,
        })
    }

    async fn analyze_range(&self, start: u64, end: u64) -> Result<Vec<BlockAnalysis>> {
        let mut results = Vec::new();

        for height in start..=end {
            match self.analyze_block(height).await {
                Ok(analysis) => {
                    println!(
                        "Block {}: current={} bytes, estimated={} bytes, delta=+{} bytes ({:.2}%), tx={}, tin={}, tout={}",
                        height,
                        analysis.current_compact_size,
                        analysis.estimated_with_transparent,
                        analysis.delta_bytes,
                        analysis.delta_percent,
                        analysis.tx_count,
                        analysis.transparent_inputs,
                        analysis.transparent_outputs
                    );
                    results.push(analysis);
                }
                Err(e) => {
                    eprintln!("Error analyzing block {}: {}", height, e);
                }
            }

            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }

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
        println!("  Total: {} bytes ({:.2} MB)", total_current, total_current as f64 / 1_000_000.0);
        println!("\nWith transparent data:");
        println!("  Estimated total: {} bytes ({:.2} MB)", total_estimated, total_estimated as f64 / 1_000_000.0);
        println!("  Delta: +{} bytes ({:.2} MB)", total_delta, total_delta as f64 / 1_000_000.0);
        println!("  Overall increase: {:.2}%", (total_delta as f64 / total_current as f64) * 100.0);
        println!("\nPer-block statistics:");
        println!("  Median increase: {:.2}%", median);
        println!("  95th percentile: {:.2}%", p95);
        println!("  Min: {:.2}%", deltas[0]);
        println!("  Max: {:.2}%", deltas[deltas.len() - 1]);
        
        // Practical impact examples
        println!("\nPractical impact:");
        let blocks_per_day = 24 * 60 * 2; // ~2 blocks per minute on Zcash
        let daily_current = (total_current as f64 / results.len() as f64) * blocks_per_day as f64;
        let daily_estimated = (total_estimated as f64 / results.len() as f64) * blocks_per_day as f64;
        println!("  Current daily sync (~{} blocks): {:.2} MB", blocks_per_day, daily_current / 1_000_000.0);
        println!("  With transparent: {:.2} MB", daily_estimated / 1_000_000.0);
        println!("  Additional bandwidth per day: {:.2} MB", (daily_estimated - daily_current) / 1_000_000.0);
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 5 {
        eprintln!("Usage: {} <lightwalletd-grpc-url> <zebrad-rpc-url> <start-height> <end-height> [output.csv]", args[0]);
        eprintln!("Example: {} http://localhost:9067 http://localhost:8232 2400000 2401000 results.csv", args[0]);
        std::process::exit(1);
    }

    let lightwalletd_url = &args[1];
    let zebra_rpc_url = &args[2];
    let start_height: u64 = args[3].parse()?;
    let end_height: u64 = args[4].parse()?;
    let output_file = args.get(5).map(|s| s.as_str()).unwrap_or("analysis.csv");

    let estimator = TransparentEstimator::new(
        zebra_rpc_url.to_string(),
        lightwalletd_url.to_string(),
    );

    println!("Analyzing blocks {} to {}...", start_height, end_height);
    println!("Fetching real compact blocks from lightwalletd: {}", lightwalletd_url);
    println!("Fetching full blocks from Zebrad: {}", zebra_rpc_url);
    println!();

    let results = estimator.analyze_range(start_height, end_height).await?;

    estimator.write_csv(&results, output_file)?;
    println!("\nDetailed results written to: {}", output_file);

    estimator.print_summary(&results);

    Ok(())
}
