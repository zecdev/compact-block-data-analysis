# Sampling Strategies

## Overview

Analyzing 2.7M+ blocks would take days. Statistical sampling provides accurate results in minutes.

## Available Strategies

### 1. Quick (~1,500 blocks, 15 min)
- 250 per era
- 500 additional recent samples
- Good for initial exploration

### 2. Recommended (~5,000 blocks, 30 min)
- 750 per era
- 2,000 additional recent samples
- Best balance of accuracy and speed
- **Use this for most analyses**

### 3. Thorough (~11,000 blocks, 2 hr)
- 1,500 per era
- 5,000 additional recent samples
- Highest confidence intervals
- Use for final analysis

### 4. Equal (~4,000 blocks)
- 1,000 samples per era
- Good for comparing eras
- May over-represent old eras

### 5. Proportional (~5,000 blocks)
- Samples match blockchain distribution
- Statistically representative
- Gives equal weight to old and new

### 6. Weighted (~5,000 blocks)
- Custom weights per era
- Default: heavier on recent
- Flexible for specific needs

## Choosing a Strategy

**For protocol decisions**: Use Recommended or Thorough
**For era comparison**: Use Equal
**For quick validation**: Use Quick
**For custom needs**: Use Weighted

## Sample Size Calculations

For 95% confidence and ±2% margin of error:
n = (1.96² × 0.5 × 0.5) / 0.02² ≈ 2,401

We use 5,000+ samples for better confidence.
