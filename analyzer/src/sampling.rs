// Add to Cargo.toml:
// rand = "0.8"

use rand::seq::SliceRandom;
use rand::SeedableRng;
use std::collections::BTreeSet;

#[derive(Debug, Clone)]
pub struct Era {
    pub name: String,
    pub start: u64,
    pub end: u64,
}

impl Era {
    pub fn zcash_eras(current_tip: u64) -> Vec<Self> {
        vec![
            Era {
                name: "sapling".to_string(),
                start: 419_200,
                end: 653_599,
            },
            Era {
                name: "blossom".to_string(),
                start: 653_600,
                end: 903_799,
            },
            Era {
                name: "heartwood".to_string(),
                start: 903_800,
                end: 1_046_399,
            },
            Era {
                name: "canopy".to_string(),
                start: 1_046_400,
                end: 1_687_103,
            },
            Era {
                name: "nu5".to_string(),
                start: 1_687_104,
                end: 2_726_399,
            },
            Era {
                name: "nu6".to_string(),
                start: 2_726_400,
                end: current_tip,
            },
        ]
    }

    pub fn size(&self) -> u64 {
        self.end - self.start + 1
    }

    pub fn get_era_for_height(height: u64, eras: &[Era]) -> String {
        for era in eras {
            if height >= era.start && height <= era.end {
                return era.name.clone();
            }
        }
        "unknown".to_string()
    }
}

#[derive(Debug)]
pub enum SamplingStrategy {
    // Sample N blocks from each era equally
    EqualPerEra {
        samples_per_era: usize,
    },

    // Sample proportionally to era size
    Proportional {
        total_samples: usize,
    },

    // Equal per era + additional recent samples
    HybridRecent {
        base_per_era: usize,
        recent_additional: usize,
        recent_window: u64, // e.g., last 100k blocks
    },

    // Fixed density: 1 in every N blocks
    FixedDensity {
        every_n: u64,
    },

    // Custom weights per era
    Weighted {
        weights: Vec<(String, f64)>, // (era_name, weight_0_to_1)
        total_samples: usize,
    },

    // All blocks in range (for small ranges)
    Complete {
        start: u64,
        end: u64,
    },
}

pub struct Sampler {
    strategy: SamplingStrategy,
    eras: Vec<Era>,
    seed: Option<u64>,
}

impl Sampler {
    pub fn new(strategy: SamplingStrategy, current_tip: u64, seed: Option<u64>) -> Self {
        let eras = Era::zcash_eras(current_tip);
        Self {
            strategy,
            eras,
            seed,
        }
    }

    pub fn generate_samples(&self) -> Vec<u64> {
        match &self.strategy {
            SamplingStrategy::EqualPerEra { samples_per_era } => {
                self.equal_per_era(*samples_per_era)
            }
            SamplingStrategy::Proportional { total_samples } => self.proportional(*total_samples),
            SamplingStrategy::HybridRecent {
                base_per_era,
                recent_additional,
                recent_window,
            } => self.hybrid_recent(*base_per_era, *recent_additional, *recent_window),
            SamplingStrategy::FixedDensity { every_n } => self.fixed_density(*every_n),
            SamplingStrategy::Weighted {
                weights,
                total_samples,
            } => self.weighted(weights, *total_samples),
            SamplingStrategy::Complete { start, end } => (*start..=*end).collect(),
        }
    }

    fn equal_per_era(&self, samples_per_era: usize) -> Vec<u64> {
        let mut all_samples = BTreeSet::new();

        for era in &self.eras {
            let samples = self.random_sample_from_range(
                era.start,
                era.end,
                samples_per_era.min(era.size() as usize),
            );
            all_samples.extend(samples);
        }

        all_samples.into_iter().collect()
    }

    fn proportional(&self, total_samples: usize) -> Vec<u64> {
        let mut all_samples = BTreeSet::new();
        let total_blocks: u64 = self.eras.iter().map(|e| e.size()).sum();

        for era in &self.eras {
            let era_proportion = era.size() as f64 / total_blocks as f64;
            let era_samples = (total_samples as f64 * era_proportion).round() as usize;

            let samples = self.random_sample_from_range(
                era.start,
                era.end,
                era_samples.min(era.size() as usize),
            );
            all_samples.extend(samples);
        }

        all_samples.into_iter().collect()
    }

    fn hybrid_recent(
        &self,
        base_per_era: usize,
        recent_additional: usize,
        recent_window: u64,
    ) -> Vec<u64> {
        let mut all_samples = BTreeSet::new();

        // Base samples from each era
        for era in &self.eras {
            let samples = self.random_sample_from_range(
                era.start,
                era.end,
                base_per_era.min(era.size() as usize),
            );
            all_samples.extend(samples);
        }

        // Additional samples from recent blocks
        if let Some(last_era) = self.eras.last() {
            let recent_start = last_era.end.saturating_sub(recent_window);
            let samples =
                self.random_sample_from_range(recent_start, last_era.end, recent_additional);
            all_samples.extend(samples);
        }

        all_samples.into_iter().collect()
    }

    fn fixed_density(&self, every_n: u64) -> Vec<u64> {
        let mut samples = Vec::new();

        for era in &self.eras {
            let mut height = era.start;
            while height <= era.end {
                samples.push(height);
                height += every_n;
            }
        }

        samples
    }

    fn weighted(&self, weights: &[(String, f64)], total_samples: usize) -> Vec<u64> {
        let mut all_samples = BTreeSet::new();
        let weight_sum: f64 = weights.iter().map(|(_, w)| w).sum();

        for (era_name, weight) in weights {
            if let Some(era) = self.eras.iter().find(|e| &e.name == era_name) {
                let era_samples = ((total_samples as f64) * (weight / weight_sum)).round() as usize;
                let samples = self.random_sample_from_range(
                    era.start,
                    era.end,
                    era_samples.min(era.size() as usize),
                );
                all_samples.extend(samples);
            }
        }

        all_samples.into_iter().collect()
    }

    fn random_sample_from_range(&self, start: u64, end: u64, sample_size: usize) -> Vec<u64> {
        let range_size = (end - start + 1) as usize;

        if sample_size >= range_size {
            // If we want more samples than available, just return all
            return (start..=end).collect();
        }

        let mut rng = if let Some(seed) = self.seed {
            rand::rngs::StdRng::seed_from_u64(seed)
        } else {
            rand::rngs::StdRng::from_entropy()
        };

        let all_heights: Vec<u64> = (start..=end).collect();
        let mut samples: Vec<u64> = all_heights
            .choose_multiple(&mut rng, sample_size)
            .cloned()
            .collect();

        samples.sort();
        samples
    }

    pub fn describe(&self) -> String {
        let samples = self.generate_samples();
        let total = samples.len();

        let mut description = format!("Sampling Strategy: {:?}\n", self.strategy);
        description.push_str(&format!("Total samples: {}\n\n", total));
        description.push_str("Distribution by era:\n");

        for era in &self.eras {
            let era_samples = samples
                .iter()
                .filter(|&&h| h >= era.start && h <= era.end)
                .count();
            let percentage = (era_samples as f64 / total as f64) * 100.0;
            let density = era_samples as f64 / era.size() as f64;

            description.push_str(&format!(
                "  {}: {} samples ({:.1}% of total, 1 in {:.0} blocks)\n",
                era.name,
                era_samples,
                percentage,
                1.0 / density
            ));
        }

        description
    }
}

// Example usage in main
pub fn create_recommended_sampler(current_tip: u64) -> Sampler {
    // Hybrid approach: 750 samples per era + 2000 from recent 100k blocks
    Sampler::new(
        SamplingStrategy::HybridRecent {
            base_per_era: 750,
            recent_additional: 2000,
            recent_window: 100_000,
        },
        current_tip,
        Some(42), // Fixed seed for reproducibility
    )
}

pub fn create_quick_sampler(current_tip: u64) -> Sampler {
    // Quick analysis: fewer samples
    Sampler::new(
        SamplingStrategy::HybridRecent {
            base_per_era: 250,
            recent_additional: 500,
            recent_window: 50_000,
        },
        current_tip,
        Some(42),
    )
}

pub fn create_thorough_sampler(current_tip: u64) -> Sampler {
    // Thorough analysis: more samples
    Sampler::new(
        SamplingStrategy::HybridRecent {
            base_per_era: 1500,
            recent_additional: 5000,
            recent_window: 200_000,
        },
        current_tip,
        Some(42),
    )
}

pub fn create_equal_sampler(current_tip: u64) -> Sampler {
    // Equal samples per era
    Sampler::new(
        SamplingStrategy::EqualPerEra {
            samples_per_era: 1000,
        },
        current_tip,
        Some(42),
    )
}

pub fn create_proportional_sampler(current_tip: u64) -> Sampler {
    // Proportional to era size
    Sampler::new(
        SamplingStrategy::Proportional {
            total_samples: 5000,
        },
        current_tip,
        Some(42),
    )
}

pub fn create_weighted_sampler(current_tip: u64) -> Sampler {
    // Custom weights - focus on recent
    Sampler::new(
        SamplingStrategy::Weighted {
            weights: vec![
                ("sapling".to_string(), 0.10),
                ("blossom".to_string(), 0.10),
                ("heartwood".to_string(), 0.10),
                ("canopy".to_string(), 0.20),
                ("nu5".to_string(), 0.30),
                ("nu6".to_string(), 0.20),
            ],
            total_samples: 5000,
        },
        current_tip,
        Some(42),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_equal_per_era() {
        let sampler = create_equal_sampler(2_400_000);
        let samples = sampler.generate_samples();

        // Should have roughly 4000 samples (1000 per era)
        assert!(samples.len() >= 3800 && samples.len() <= 4200);

        // Samples should be sorted
        assert!(samples.windows(2).all(|w| w[0] < w[1]));
    }

    #[test]
    fn test_hybrid_recent() {
        let sampler = create_recommended_sampler(2_400_000);
        let samples = sampler.generate_samples();

        println!("{}", sampler.describe());

        // Should have base + recent samples
        assert!(samples.len() >= 4500 && samples.len() <= 5500);
    }

    #[test]
    fn test_reproducibility() {
        let sampler1 = create_equal_sampler(2_400_000);
        let sampler2 = create_equal_sampler(2_400_000);

        let samples1 = sampler1.generate_samples();
        let samples2 = sampler2.generate_samples();

        // Same seed should produce identical samples
        assert_eq!(samples1, samples2);
    }
}
