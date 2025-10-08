#!/usr/bin/env python3
"""
Visualization and statistical analysis for Zcash compact block overhead data.

Usage:
    python visualize.py results.csv [--output-dir ./charts]
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import argparse
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

class CompactBlockAnalyzer:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.df['delta_mb'] = self.df['delta_bytes'] / 1_000_000
        self.df['current_mb'] = self.df['current_compact_size'] / 1_000_000
        self.df['estimated_mb'] = self.df['estimated_with_transparent'] / 1_000_000
        
    def generate_all_charts(self, output_dir='./charts'):
        """Generate all visualization charts"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("Generating visualizations...")
        
        self.plot_distribution(output_path / 'distribution.png')
        self.plot_time_series(output_path / 'time_series.png')
        self.plot_by_era(output_path / 'by_era.png')
        self.plot_correlations(output_path / 'correlations.png')
        self.plot_cumulative(output_path / 'cumulative.png')
        self.plot_bandwidth_impact(output_path / 'bandwidth_impact.png')
        self.plot_heatmap(output_path / 'heatmap.png')
        
        # Generate statistical report
        self.generate_report(output_path / 'statistical_report.txt')
        
        print(f"\nAll visualizations saved to: {output_path}")
        
    def plot_distribution(self, filename):
        """Histogram of overhead percentage distribution"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram with KDE
        axes[0].hist(self.df['delta_percent'], bins=50, alpha=0.7, 
                     edgecolor='black', density=True, label='Distribution')
        
        # Add KDE
        kde_x = np.linspace(self.df['delta_percent'].min(), 
                           self.df['delta_percent'].max(), 100)
        kde = stats.gaussian_kde(self.df['delta_percent'])
        axes[0].plot(kde_x, kde(kde_x), 'r-', linewidth=2, label='KDE')
        
        # Add median and mean
        median = self.df['delta_percent'].median()
        mean = self.df['delta_percent'].mean()
        axes[0].axvline(median, color='green', linestyle='--', 
                       linewidth=2, label=f'Median: {median:.1f}%')
        axes[0].axvline(mean, color='orange', linestyle='--', 
                       linewidth=2, label=f'Mean: {mean:.1f}%')
        
        axes[0].set_xlabel('Overhead Percentage (%)')
        axes[0].set_ylabel('Density')
        axes[0].set_title('Distribution of Compact Block Overhead')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Box plot
        axes[1].boxplot(self.df['delta_percent'], vert=True)
        axes[1].set_ylabel('Overhead Percentage (%)')
        axes[1].set_title('Overhead Distribution (Box Plot)')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Distribution chart saved: {filename}")
        
    def plot_time_series(self, filename):
        """Overhead over blockchain height"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Scatter plot with trend
        axes[0].scatter(self.df['height'], self.df['delta_percent'], 
                       alpha=0.4, s=10, c=self.df['delta_percent'], 
                       cmap='YlOrRd')
        
        # Add rolling mean
        window = max(len(self.df) // 50, 10)
        rolling_mean = self.df.set_index('height')['delta_percent'].rolling(window).mean()
        axes[0].plot(rolling_mean.index, rolling_mean.values, 
                    'b-', linewidth=2, label=f'Rolling Mean (window={window})')
        
        # Add era boundaries
        eras = [
            (419_200, 'Sapling', 'red'),
            (653_600, 'Blossom', 'blue'),
            (903_800, 'Heartwood', 'purple'),
            (1_046_400, 'Canopy', 'orange'),
            (1_687_104, 'NU5', 'green'),
            (2_726_400, 'NU6', 'brown'),
        ]
        
        for height, name, color in eras:
            if height >= self.df['height'].min() and height <= self.df['height'].max():
                axes[0].axvline(height, color=color, alpha=0.3, 
                              linestyle='--', linewidth=1.5)
                axes[0].text(height, axes[0].get_ylim()[1] * 0.95, name, 
                           rotation=90, verticalalignment='top', color=color)
        
        axes[0].set_xlabel('Block Height')
        axes[0].set_ylabel('Overhead (%)')
        axes[0].set_title('Compact Block Overhead Over Time')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Absolute size over time
        axes[1].scatter(self.df['height'], self.df['delta_mb'], 
                       alpha=0.4, s=10, c=self.df['delta_mb'], 
                       cmap='YlOrRd')
        
        rolling_delta = self.df.set_index('height')['delta_mb'].rolling(window).mean()
        axes[1].plot(rolling_delta.index, rolling_delta.values, 
                    'b-', linewidth=2, label=f'Rolling Mean')
        
        for height, name, color in eras:
            if height >= self.df['height'].min() and height <= self.df['height'].max():
                axes[1].axvline(height, color=color, alpha=0.3, 
                              linestyle='--', linewidth=1.5)
        
        axes[1].set_xlabel('Block Height')
        axes[1].set_ylabel('Delta Size (MB)')
        axes[1].set_title('Absolute Size Increase Over Time')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Time series chart saved: {filename}")
        
    def plot_by_era(self, filename):
        """Compare distributions across eras"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Box plot by era
        era_order = ['sapling', 'blossom', 'heartwood', 'canopy', 'nu5', 'nu6']
        available_eras = [e for e in era_order if e in self.df['era'].values]
        
        box_data = [self.df[self.df['era'] == era]['delta_percent'].values 
                    for era in available_eras]
        
        colors = ['lightgreen', 'lightyellow', 'lightpink', 'lightcoral', 'lavender', 'peachpuff']
        bp = axes[0, 0].boxplot(box_data, labels=available_eras, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors[:len(available_eras)]):
            patch.set_facecolor(color)
        
        axes[0, 0].set_ylabel('Overhead (%)')
        axes[0, 0].set_title('Overhead Distribution by Era')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Violin plot
        if len(available_eras) > 0:
            era_df = self.df[self.df['era'].isin(available_eras)]
            sns.violinplot(data=era_df, x='era', y='delta_percent', 
                          order=available_eras, ax=axes[0, 1])
            axes[0, 1].set_ylabel('Overhead (%)')
            axes[0, 1].set_title('Overhead Distribution by Era (Violin Plot)')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Bar chart of means
        era_stats = self.df.groupby('era')['delta_percent'].agg(['mean', 'std'])
        era_stats = era_stats.reindex(available_eras)
        
        x = np.arange(len(available_eras))
        axes[1, 0].bar(x, era_stats['mean'], yerr=era_stats['std'], 
                      capsize=5, alpha=0.7, color=colors[:len(available_eras)])
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(available_eras, rotation=45)
        axes[1, 0].set_ylabel('Mean Overhead (%)')
        axes[1, 0].set_title('Average Overhead by Era (with Std Dev)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Sample sizes
        era_counts = self.df['era'].value_counts().reindex(available_eras)
        axes[1, 1].bar(available_eras, era_counts.values, 
                      color=colors[:len(available_eras)])
        axes[1, 1].set_ylabel('Number of Samples')
        axes[1, 1].set_title('Sample Distribution by Era')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Era comparison chart saved: {filename}")
        
    def plot_correlations(self, filename):
        """Correlation between overhead and transaction characteristics"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Overhead vs transparent inputs
        axes[0, 0].scatter(self.df['transparent_inputs'], self.df['delta_bytes'], 
                          alpha=0.5, s=20)
        z = np.polyfit(self.df['transparent_inputs'], self.df['delta_bytes'], 1)
        p = np.poly1d(z)
        axes[0, 0].plot(self.df['transparent_inputs'], 
                       p(self.df['transparent_inputs']), 
                       "r--", linewidth=2, label=f'Trend')
        
        corr = self.df['transparent_inputs'].corr(self.df['delta_bytes'])
        axes[0, 0].set_xlabel('Transparent Inputs')
        axes[0, 0].set_ylabel('Delta (bytes)')
        axes[0, 0].set_title(f'Overhead vs Transparent Inputs (r={corr:.3f})')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Overhead vs transparent outputs
        axes[0, 1].scatter(self.df['transparent_outputs'], self.df['delta_bytes'], 
                          alpha=0.5, s=20, color='orange')
        z = np.polyfit(self.df['transparent_outputs'], self.df['delta_bytes'], 1)
        p = np.poly1d(z)
        axes[0, 1].plot(self.df['transparent_outputs'], 
                       p(self.df['transparent_outputs']), 
                       "r--", linewidth=2, label='Trend')
        
        corr = self.df['transparent_outputs'].corr(self.df['delta_bytes'])
        axes[0, 1].set_xlabel('Transparent Outputs')
        axes[0, 1].set_ylabel('Delta (bytes)')
        axes[0, 1].set_title(f'Overhead vs Transparent Outputs (r={corr:.3f})')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Overhead vs total transactions
        axes[1, 0].scatter(self.df['tx_count'], self.df['delta_percent'], 
                          alpha=0.5, s=20, color='green')
        
        corr = self.df['tx_count'].corr(self.df['delta_percent'])
        axes[1, 0].set_xlabel('Transaction Count')
        axes[1, 0].set_ylabel('Overhead (%)')
        axes[1, 0].set_title(f'Overhead % vs Transaction Count (r={corr:.3f})')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Current size vs overhead
        axes[1, 1].scatter(self.df['current_compact_size'], 
                          self.df['delta_percent'], 
                          alpha=0.5, s=20, color='purple')
        
        corr = self.df['current_compact_size'].corr(self.df['delta_percent'])
        axes[1, 1].set_xlabel('Current Compact Block Size (bytes)')
        axes[1, 1].set_ylabel('Overhead (%)')
        axes[1, 1].set_title(f'Overhead % vs Block Size (r={corr:.3f})')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Correlation chart saved: {filename}")
        
    def plot_cumulative(self, filename):
        """Cumulative distribution function"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # CDF of overhead percentage
        sorted_overhead = np.sort(self.df['delta_percent'])
        cumulative = np.arange(1, len(sorted_overhead) + 1) / len(sorted_overhead)
        
        axes[0].plot(sorted_overhead, cumulative * 100, linewidth=2)
        
        # Mark percentiles
        percentiles = [50, 75, 90, 95, 99]
        for p in percentiles:
            value = np.percentile(sorted_overhead, p)
            axes[0].axvline(value, linestyle='--', alpha=0.5, 
                          label=f'P{p}: {value:.1f}%')
            axes[0].axhline(p, linestyle=':', alpha=0.3)
        
        axes[0].set_xlabel('Overhead (%)')
        axes[0].set_ylabel('Cumulative Percentage of Blocks')
        axes[0].set_title('Cumulative Distribution of Overhead')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # CDF of absolute delta
        sorted_delta = np.sort(self.df['delta_bytes'])
        axes[1].plot(sorted_delta / 1000, cumulative * 100, linewidth=2, color='orange')
        
        for p in percentiles:
            value = np.percentile(sorted_delta, p) / 1000
            axes[1].axvline(value, linestyle='--', alpha=0.5, 
                          label=f'P{p}: {value:.1f}KB')
        
        axes[1].set_xlabel('Delta Size (KB)')
        axes[1].set_ylabel('Cumulative Percentage of Blocks')
        axes[1].set_title('Cumulative Distribution of Absolute Overhead')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Cumulative distribution chart saved: {filename}")
        
    def plot_bandwidth_impact(self, filename):
        """Practical bandwidth impact scenarios"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Calculate metrics
        avg_current = self.df['current_compact_size'].mean()
        avg_with_transparent = self.df['estimated_with_transparent'].mean()
        avg_delta = avg_with_transparent - avg_current
        
        # Daily sync (assume 2880 blocks per day)
        blocks_per_day = 2880
        daily_current_mb = (avg_current * blocks_per_day) / 1_000_000
        daily_with_mb = (avg_with_transparent * blocks_per_day) / 1_000_000
        
        axes[0, 0].bar(['Current', 'With\nTransparent'], 
                      [daily_current_mb, daily_with_mb],
                      color=['steelblue', 'coral'])
        axes[0, 0].set_ylabel('MB')
        axes[0, 0].set_title('Daily Sync Bandwidth\n(~2880 blocks)')
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        for i, v in enumerate([daily_current_mb, daily_with_mb]):
            axes[0, 0].text(i, v + 1, f'{v:.1f} MB', 
                          ha='center', va='bottom', fontweight='bold')
        
        # Full sync (assume 2.4M blocks)
        total_blocks = len(self.df) * 500  # Estimate full chain
        full_current_gb = (avg_current * total_blocks) / 1_000_000_000
        full_with_gb = (avg_with_transparent * total_blocks) / 1_000_000_000
        
        axes[0, 1].bar(['Current', 'With\nTransparent'], 
                      [full_current_gb, full_with_gb],
                      color=['steelblue', 'coral'])
        axes[0, 1].set_ylabel('GB')
        axes[0, 1].set_title(f'Full Chain Sync\n(~{total_blocks:,} blocks)')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        for i, v in enumerate([full_current_gb, full_with_gb]):
            axes[0, 1].text(i, v + 0.1, f'{v:.1f} GB', 
                          ha='center', va='bottom', fontweight='bold')
        
        # Mobile data cost (assume $10/GB)
        cost_per_gb = 10
        daily_cost_current = (daily_current_mb / 1000) * cost_per_gb
        daily_cost_with = (daily_with_mb / 1000) * cost_per_gb
        monthly_cost_current = daily_cost_current * 30
        monthly_cost_with = daily_cost_with * 30
        
        x = np.arange(2)
        width = 0.35
        axes[1, 0].bar(x - width/2, [daily_cost_current, monthly_cost_current], 
                      width, label='Current', color='steelblue')
        axes[1, 0].bar(x + width/2, [daily_cost_with, monthly_cost_with], 
                      width, label='With Transparent', color='coral')
        
        axes[1, 0].set_ylabel('Cost (USD)')
        axes[1, 0].set_title('Mobile Data Cost\n(@$10/GB)')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(['Daily', 'Monthly'])
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Sync time (assume 5 Mbps connection)
        bandwidth_mbps = 5
        bandwidth_mb_per_sec = bandwidth_mbps / 8
        
        daily_time_current = daily_current_mb / bandwidth_mb_per_sec / 60  # minutes
        daily_time_with = daily_with_mb / bandwidth_mb_per_sec / 60
        full_time_current = full_current_gb * 1000 / bandwidth_mb_per_sec / 3600  # hours
        full_time_with = full_with_gb * 1000 / bandwidth_mb_per_sec / 3600
        
        x = np.arange(2)
        axes[1, 1].bar(x - width/2, [daily_time_current, full_time_current], 
                      width, label='Current', color='steelblue')
        axes[1, 1].bar(x + width/2, [daily_time_with, full_time_with], 
                      width, label='With Transparent', color='coral')
        
        axes[1, 1].set_ylabel('Time')
        axes[1, 1].set_title(f'Sync Time\n(@{bandwidth_mbps} Mbps)')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(['Daily\n(minutes)', 'Full\n(hours)'])
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Bandwidth impact chart saved: {filename}")
        
    def plot_heatmap(self, filename):
        """Heatmap of overhead by era and transaction characteristics"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Create bins for transaction count
        self.df['tx_bin'] = pd.cut(self.df['tx_count'], 
                                    bins=[0, 10, 50, 100, 500, 10000],
                                    labels=['1-10', '11-50', '51-100', '101-500', '500+'])
        
        # Pivot table: era vs tx_bin
        if 'era' in self.df.columns and not self.df['era'].isna().all():
            pivot = self.df.pivot_table(
                values='delta_percent',
                index='era',
                columns='tx_bin',
                aggfunc='mean'
            )
            
            sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', 
                       ax=axes[0], cbar_kws={'label': 'Overhead (%)'})
            axes[0].set_title('Average Overhead by Era and Transaction Count')
            axes[0].set_ylabel('Era')
            axes[0].set_xlabel('Transactions per Block')
        
        # Pivot table: transparent usage
        self.df['transparent_bin'] = pd.cut(
            self.df['transparent_inputs'] + self.df['transparent_outputs'],
            bins=[0, 10, 50, 100, 500, 10000],
            labels=['1-10', '11-50', '51-100', '101-500', '500+']
        )
        
        if 'era' in self.df.columns and not self.df['era'].isna().all():
            pivot2 = self.df.pivot_table(
                values='delta_percent',
                index='era',
                columns='transparent_bin',
                aggfunc='mean'
            )
            
            sns.heatmap(pivot2, annot=True, fmt='.1f', cmap='YlOrRd', 
                       ax=axes[1], cbar_kws={'label': 'Overhead (%)'})
            axes[1].set_title('Average Overhead by Era and Transparent I/O')
            axes[1].set_ylabel('Era')
            axes[1].set_xlabel('Transparent Inputs + Outputs')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Heatmap saved: {filename}")
        
    def generate_report(self, filename):
        """Generate statistical report"""
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("STATISTICAL ANALYSIS REPORT\n")
            f.write("Zcash Compact Block Transparent Data Overhead\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total blocks analyzed: {len(self.df):,}\n")
            f.write(f"Block height range: {self.df['height'].min():,} - {self.df['height'].max():,}\n\n")
            
            # Overhead statistics
            f.write("OVERHEAD PERCENTAGE\n")
            f.write(f"  Mean:   {self.df['delta_percent'].mean():>8.2f}%\n")
            f.write(f"  Median: {self.df['delta_percent'].median():>8.2f}%\n")
            f.write(f"  Std Dev:{self.df['delta_percent'].std():>8.2f}%\n")
            f.write(f"  Min:    {self.df['delta_percent'].min():>8.2f}%\n")
            f.write(f"  Max:    {self.df['delta_percent'].max():>8.2f}%\n\n")
            
            # Percentiles
            f.write("PERCENTILES\n")
            for p in [25, 50, 75, 90, 95, 99]:
                value = np.percentile(self.df['delta_percent'], p)
                f.write(f"  P{p:>2}: {value:>8.2f}%\n")
            f.write("\n")
            
            # Confidence intervals
            f.write("CONFIDENCE INTERVALS (95%)\n")
            mean = self.df['delta_percent'].mean()
            std_err = stats.sem(self.df['delta_percent'])
            ci = stats.t.interval(0.95, len(self.df)-1, loc=mean, scale=std_err)
            f.write(f"  Mean overhead: {mean:.2f}% ± {(ci[1]-mean):.2f}%\n")
            f.write(f"  Range: [{ci[0]:.2f}%, {ci[1]:.2f}%]\n\n")
            
            # By era
            f.write("STATISTICS BY ERA\n")
            f.write("-" * 80 + "\n")
            if 'era' in self.df.columns:
                era_stats = self.df.groupby('era').agg({
                    'delta_percent': ['count', 'mean', 'std', 'median', 'min', 'max']
                })
                f.write(era_stats.to_string())
                f.write("\n\n")
            
            # Bandwidth impact
            f.write("PRACTICAL BANDWIDTH IMPACT\n")
            f.write("-" * 80 + "\n")
            
            avg_current = self.df['current_compact_size'].mean()
            avg_with = self.df['estimated_with_transparent'].mean()
            avg_delta = avg_with - avg_current
            
            blocks_per_day = 2880
            daily_current_mb = (avg_current * blocks_per_day) / 1_000_000
            daily_with_mb = (avg_with * blocks_per_day) / 1_000_000
            daily_delta_mb = daily_with_mb - daily_current_mb
            
            f.write(f"Average block sizes:\n")
            f.write(f"  Current:         {avg_current/1000:>10.2f} KB\n")
            f.write(f"  With transparent:{avg_with/1000:>10.2f} KB\n")
            f.write(f"  Delta:           {avg_delta/1000:>10.2f} KB\n\n")
            
            f.write(f"Daily sync (~{blocks_per_day} blocks):\n")
            f.write(f"  Current:         {daily_current_mb:>10.2f} MB\n")
            f.write(f"  With transparent:{daily_with_mb:>10.2f} MB\n")
            f.write(f"  Additional:      {daily_delta_mb:>10.2f} MB ({(daily_delta_mb/daily_current_mb)*100:.1f}%)\n\n")
            
            # Correlations
            f.write("CORRELATIONS\n")
            f.write("-" * 80 + "\n")
            corr_inputs = self.df['transparent_inputs'].corr(self.df['delta_bytes'])
            corr_outputs = self.df['transparent_outputs'].corr(self.df['delta_bytes'])
            corr_tx = self.df['tx_count'].corr(self.df['delta_percent'])
            
            f.write(f"  Transparent inputs vs delta:  r = {corr_inputs:>6.3f}\n")
            f.write(f"  Transparent outputs vs delta: r = {corr_outputs:>6.3f}\n")
            f.write(f"  Transaction count vs %%:       r = {corr_tx:>6.3f}\n\n")
            
            # Recommendations
            f.write("DECISION FRAMEWORK\n")
            f.write("-" * 80 + "\n")
            median_overhead = self.df['delta_percent'].median()
            p95_overhead = np.percentile(self.df['delta_percent'], 95)
            
            f.write(f"Median overhead: {median_overhead:.1f}%\n")
            f.write(f"95th percentile: {p95_overhead:.1f}%\n\n")
            
            if median_overhead < 20:
                f.write("RECOMMENDATION: LOW IMPACT\n")
                f.write("  The overhead is relatively small (<20%). Consider making transparent\n")
                f.write("  data part of the default GetBlockRange method. This would:\n")
                f.write("  - Simplify the API (single method)\n")
                f.write("  - Provide feature parity with full nodes\n")
                f.write("  - Have minimal bandwidth impact on users\n")
            elif median_overhead < 50:
                f.write("RECOMMENDATION: MODERATE IMPACT\n")
                f.write("  The overhead is significant (20-50%). Consider:\n")
                f.write("  - Separate opt-in method for transparent data\n")
                f.write("  - Pool-based filtering (as in librustzcash PR #1781)\n")
                f.write("  - Let clients choose based on their needs\n")
                f.write("  - Important for mobile/bandwidth-limited users\n")
            else:
                f.write("RECOMMENDATION: HIGH IMPACT\n")
                f.write("  The overhead is substantial (>50%). Strongly consider:\n")
                f.write("  - Separate method required\n")
                f.write("  - Clear opt-in for clients needing transparent data\n")
                f.write("  - Critical for mobile and bandwidth-limited users\n")
                f.write("  - May significantly impact sync times\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("End of Report\n")
            f.write("=" * 80 + "\n")
        
        print(f"  ✓ Statistical report saved: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate visualizations and statistical analysis for compact block data'
    )
    parser.add_argument('csv_file', help='Path to CSV file with analysis results')
    parser.add_argument('--output-dir', '-o', default='./charts',
                       help='Output directory for charts (default: ./charts)')
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.csv_file).exists():
        print(f"Error: File not found: {args.csv_file}")
        return 1
    
    print(f"Loading data from: {args.csv_file}")
    analyzer = CompactBlockAnalyzer(args.csv_file)
    
    print(f"Loaded {len(analyzer.df)} blocks")
    print()
    
    # Generate all visualizations
    analyzer.generate_all_charts(args.output_dir)
    
    print("\n✅ Analysis complete!")
    print(f"\nView the statistical report: {args.output_dir}/statistical_report.txt")
    print(f"View charts in: {args.output_dir}/")
    
    return 0


if __name__ == '__main__':
    exit(main())
