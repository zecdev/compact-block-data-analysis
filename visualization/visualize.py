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
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10


class CompactBlockAnalyzer:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.df["delta_mb"] = self.df["delta_bytes"] / 1_000_000
        self.df["current_mb"] = self.df["current_compact_size"] / 1_000_000
        self.df["estimated_mb"] = self.df["estimated_with_transparent"] / 1_000_000

    def generate_all_charts(self, output_dir="./charts"):
        """Generate all visualization charts"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print("Generating visualizations...")

        self.plot_distribution(output_path / "distribution.png")
        self.plot_time_series(output_path / "time_series.png")
        self.plot_by_era(output_path / "by_era.png")
        self.plot_correlations(output_path / "correlations.png")
        self.plot_cumulative(output_path / "cumulative.png")
        self.plot_bandwidth_impact(output_path / "bandwidth_impact.png")
        self.plot_heatmap(output_path / "heatmap.png")

        # Generate statistical report
        self.generate_report(output_path / "statistical_report.txt")

        print(f"\nAll visualizations saved to: {output_path}")

    def plot_distribution(self, filename):
        """Histogram of overhead distribution - both percentage and absolute"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Top row: Percentage overhead
        # Histogram with KDE
        axes[0, 0].hist(
            self.df["delta_percent"],
            bins=50,
            alpha=0.7,
            edgecolor="black",
            density=True,
            label="Distribution",
        )

        # Add KDE
        kde_x = np.linspace(
            self.df["delta_percent"].min(), self.df["delta_percent"].max(), 100
        )
        kde = stats.gaussian_kde(self.df["delta_percent"])
        axes[0, 0].plot(kde_x, kde(kde_x), "r-", linewidth=2, label="KDE")

        # Add median and mean
        median = self.df["delta_percent"].median()
        mean = self.df["delta_percent"].mean()
        axes[0, 0].axvline(
            median,
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Median: {median:.1f}%",
        )
        axes[0, 0].axvline(
            mean,
            color="orange",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean:.1f}%",
        )

        axes[0, 0].set_xlabel("Overhead Percentage (%)")
        axes[0, 0].set_ylabel("Density")
        axes[0, 0].set_title("Distribution of Overhead (Percentage)")
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Box plot - percentage
        axes[0, 1].boxplot(self.df["delta_percent"], vert=True)
        axes[0, 1].set_ylabel("Overhead Percentage (%)")
        axes[0, 1].set_title("Overhead Distribution (Box Plot - Percentage)")
        axes[0, 1].grid(True, alpha=0.3)

        # Bottom row: Absolute overhead in KB
        self.df["delta_kb"] = self.df["delta_bytes"] / 1000

        # Histogram with KDE - absolute
        axes[1, 0].hist(
            self.df["delta_kb"],
            bins=50,
            alpha=0.7,
            edgecolor="black",
            density=True,
            label="Distribution",
            color="coral",
        )

        # Add KDE
        kde_x_kb = np.linspace(
            self.df["delta_kb"].min(), self.df["delta_kb"].max(), 100
        )
        kde_kb = stats.gaussian_kde(self.df["delta_kb"])
        axes[1, 0].plot(kde_x_kb, kde_kb(kde_x_kb), "r-", linewidth=2, label="KDE")

        # Add median and mean
        median_kb = self.df["delta_kb"].median()
        mean_kb = self.df["delta_kb"].mean()
        axes[1, 0].axvline(
            median_kb,
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Median: {median_kb:.1f} KB",
        )
        axes[1, 0].axvline(
            mean_kb,
            color="orange",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean_kb:.1f} KB",
        )

        axes[1, 0].set_xlabel("Overhead (KB per block)")
        axes[1, 0].set_ylabel("Density")
        axes[1, 0].set_title("Distribution of Overhead (Absolute Size)")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Box plot - absolute
        axes[1, 1].boxplot(self.df["delta_kb"], vert=True)
        axes[1, 1].set_ylabel("Overhead (KB per block)")
        axes[1, 1].set_title("Overhead Distribution (Box Plot - Absolute)")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Distribution chart saved: {filename}")

    def plot_time_series(self, filename):
        """Overhead over blockchain height"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))

        # Scatter plot with trend
        axes[0].scatter(
            self.df["height"],
            self.df["delta_percent"],
            alpha=0.4,
            s=10,
            c=self.df["delta_percent"],
            cmap="YlOrRd",
        )

        # Add rolling mean
        window = max(len(self.df) // 50, 10)
        rolling_mean = (
            self.df.set_index("height")["delta_percent"].rolling(window).mean()
        )
        axes[0].plot(
            rolling_mean.index,
            rolling_mean.values,
            "b-",
            linewidth=2,
            label=f"Rolling Mean (window={window})",
        )

        # Add era boundaries
        eras = [
            (419_200, "Sapling", "red"),
            (653_600, "Blossom", "blue"),
            (903_800, "Heartwood", "purple"),
            (1_046_400, "Canopy", "orange"),
            (1_687_104, "NU5", "green"),
            (2_726_400, "NU6", "brown"),
        ]

        for height, name, color in eras:
            if height >= self.df["height"].min() and height <= self.df["height"].max():
                axes[0].axvline(
                    height, color=color, alpha=0.3, linestyle="--", linewidth=1.5
                )
                axes[0].text(
                    height,
                    axes[0].get_ylim()[1] * 0.95,
                    name,
                    rotation=90,
                    verticalalignment="top",
                    color=color,
                )

        axes[0].set_xlabel("Block Height")
        axes[0].set_ylabel("Overhead (%)")
        axes[0].set_title("Compact Block Overhead Over Time")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Absolute size over time
        axes[1].scatter(
            self.df["height"],
            self.df["delta_mb"],
            alpha=0.4,
            s=10,
            c=self.df["delta_mb"],
            cmap="YlOrRd",
        )

        rolling_delta = self.df.set_index("height")["delta_mb"].rolling(window).mean()
        axes[1].plot(
            rolling_delta.index,
            rolling_delta.values,
            "b-",
            linewidth=2,
            label=f"Rolling Mean",
        )

        for height, name, color in eras:
            if height >= self.df["height"].min() and height <= self.df["height"].max():
                axes[1].axvline(
                    height, color=color, alpha=0.3, linestyle="--", linewidth=1.5
                )

        axes[1].set_xlabel("Block Height")
        axes[1].set_ylabel("Delta Size (MB)")
        axes[1].set_title("Absolute Size Increase Over Time")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Time series chart saved: {filename}")

    def plot_by_era(self, filename):
        """Compare distributions across eras - both percentage and absolute"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))

        era_order = ["sapling", "blossom", "heartwood", "canopy", "nu5", "nu6"]
        available_eras = [e for e in era_order if e in self.df["era"].values]

        colors = [
            "lightgreen",
            "lightyellow",
            "lightpink",
            "lightcoral",
            "lavender",
            "peachpuff",
        ]

        # Add KB column
        self.df["delta_kb"] = self.df["delta_bytes"] / 1000

        # Top row: Percentage overhead
        # Box plot by era - percentage
        box_data_pct = [
            self.df[self.df["era"] == era]["delta_percent"].values
            for era in available_eras
        ]

        bp1 = axes[0, 0].boxplot(box_data_pct, labels=available_eras, patch_artist=True)
        for patch, color in zip(bp1["boxes"], colors[: len(available_eras)]):
            patch.set_facecolor(color)

        axes[0, 0].set_ylabel("Overhead (%)")
        axes[0, 0].set_title("Overhead Distribution by Era (Percentage)")
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis="x", rotation=45)

        # Violin plot - percentage
        if len(available_eras) > 0:
            era_df = self.df[self.df["era"].isin(available_eras)]
            sns.violinplot(
                data=era_df,
                x="era",
                y="delta_percent",
                order=available_eras,
                ax=axes[0, 1],
            )
            axes[0, 1].set_ylabel("Overhead (%)")
            axes[0, 1].set_title("Overhead Distribution by Era (Violin - Percentage)")
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis="x", rotation=45)

        # Bar chart of means - percentage
        era_stats_pct = self.df.groupby("era")["delta_percent"].agg(["mean", "std"])
        era_stats_pct = era_stats_pct.reindex(available_eras)

        x = np.arange(len(available_eras))
        axes[0, 2].bar(
            x,
            era_stats_pct["mean"],
            yerr=era_stats_pct["std"],
            capsize=5,
            alpha=0.7,
            color=colors[: len(available_eras)],
        )
        axes[0, 2].set_xticks(x)
        axes[0, 2].set_xticklabels(available_eras, rotation=45)
        axes[0, 2].set_ylabel("Mean Overhead (%)")
        axes[0, 2].set_title("Average Overhead by Era (Percentage)")
        axes[0, 2].grid(True, alpha=0.3)

        # Bottom row: Absolute KB overhead
        # Box plot by era - KB
        box_data_kb = [
            self.df[self.df["era"] == era]["delta_kb"].values for era in available_eras
        ]

        bp2 = axes[1, 0].boxplot(box_data_kb, labels=available_eras, patch_artist=True)
        for patch, color in zip(bp2["boxes"], colors[: len(available_eras)]):
            patch.set_facecolor(color)

        axes[1, 0].set_ylabel("Overhead (KB per block)")
        axes[1, 0].set_title("Overhead Distribution by Era (Absolute)")
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].tick_params(axis="x", rotation=45)

        # Violin plot - KB
        if len(available_eras) > 0:
            sns.violinplot(
                data=era_df,
                x="era",
                y="delta_kb",
                order=available_eras,
                ax=axes[1, 1],
                color="coral",
            )
            axes[1, 1].set_ylabel("Overhead (KB per block)")
            axes[1, 1].set_title("Overhead Distribution by Era (Violin - Absolute)")
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].tick_params(axis="x", rotation=45)

        # Bar chart of means - KB
        era_stats_kb = self.df.groupby("era")["delta_kb"].agg(["mean", "std"])
        era_stats_kb = era_stats_kb.reindex(available_eras)

        axes[1, 2].bar(
            x,
            era_stats_kb["mean"],
            yerr=era_stats_kb["std"],
            capsize=5,
            alpha=0.7,
            color=colors[: len(available_eras)],
        )
        axes[1, 2].set_xticks(x)
        axes[1, 2].set_xticklabels(available_eras, rotation=45)
        axes[1, 2].set_ylabel("Mean Overhead (KB per block)")
        axes[1, 2].set_title("Average Overhead by Era (Absolute)")
        axes[1, 2].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Era comparison chart saved: {filename}")

    def plot_correlations(self, filename):
        """Correlation between overhead and transaction characteristics"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Overhead vs transparent inputs
        axes[0, 0].scatter(
            self.df["transparent_inputs"], self.df["delta_bytes"], alpha=0.5, s=20
        )
        z = np.polyfit(self.df["transparent_inputs"], self.df["delta_bytes"], 1)
        p = np.poly1d(z)
        axes[0, 0].plot(
            self.df["transparent_inputs"],
            p(self.df["transparent_inputs"]),
            "r--",
            linewidth=2,
            label=f"Trend",
        )

        corr = self.df["transparent_inputs"].corr(self.df["delta_bytes"])
        axes[0, 0].set_xlabel("Transparent Inputs")
        axes[0, 0].set_ylabel("Delta (bytes)")
        axes[0, 0].set_title(f"Overhead vs Transparent Inputs (r={corr:.3f})")
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Overhead vs transparent outputs
        axes[0, 1].scatter(
            self.df["transparent_outputs"],
            self.df["delta_bytes"],
            alpha=0.5,
            s=20,
            color="orange",
        )
        z = np.polyfit(self.df["transparent_outputs"], self.df["delta_bytes"], 1)
        p = np.poly1d(z)
        axes[0, 1].plot(
            self.df["transparent_outputs"],
            p(self.df["transparent_outputs"]),
            "r--",
            linewidth=2,
            label="Trend",
        )

        corr = self.df["transparent_outputs"].corr(self.df["delta_bytes"])
        axes[0, 1].set_xlabel("Transparent Outputs")
        axes[0, 1].set_ylabel("Delta (bytes)")
        axes[0, 1].set_title(f"Overhead vs Transparent Outputs (r={corr:.3f})")
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Overhead vs total transactions
        axes[1, 0].scatter(
            self.df["tx_count"],
            self.df["delta_percent"],
            alpha=0.5,
            s=20,
            color="green",
        )

        corr = self.df["tx_count"].corr(self.df["delta_percent"])
        axes[1, 0].set_xlabel("Transaction Count")
        axes[1, 0].set_ylabel("Overhead (%)")
        axes[1, 0].set_title(f"Overhead % vs Transaction Count (r={corr:.3f})")
        axes[1, 0].grid(True, alpha=0.3)

        # Current size vs overhead
        axes[1, 1].scatter(
            self.df["current_compact_size"],
            self.df["delta_percent"],
            alpha=0.5,
            s=20,
            color="purple",
        )

        corr = self.df["current_compact_size"].corr(self.df["delta_percent"])
        axes[1, 1].set_xlabel("Current Compact Block Size (bytes)")
        axes[1, 1].set_ylabel("Overhead (%)")
        axes[1, 1].set_title(f"Overhead % vs Block Size (r={corr:.3f})")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Correlation chart saved: {filename}")

    def plot_cumulative(self, filename):
        """Cumulative distribution function"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # CDF of overhead percentage
        sorted_overhead = np.sort(self.df["delta_percent"])
        cumulative = np.arange(1, len(sorted_overhead) + 1) / len(sorted_overhead)

        axes[0].plot(sorted_overhead, cumulative * 100, linewidth=2)

        # Mark percentiles
        percentiles = [50, 75, 90, 95, 99]
        for p in percentiles:
            value = np.percentile(sorted_overhead, p)
            axes[0].axvline(
                value, linestyle="--", alpha=0.5, label=f"P{p}: {value:.1f}%"
            )
            axes[0].axhline(p, linestyle=":", alpha=0.3)

        axes[0].set_xlabel("Overhead (%)")
        axes[0].set_ylabel("Cumulative Percentage of Blocks")
        axes[0].set_title("Cumulative Distribution of Overhead")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # CDF of absolute delta
        sorted_delta = np.sort(self.df["delta_bytes"])
        axes[1].plot(sorted_delta / 1000, cumulative * 100, linewidth=2, color="orange")

        for p in percentiles:
            value = np.percentile(sorted_delta, p) / 1000
            axes[1].axvline(
                value, linestyle="--", alpha=0.5, label=f"P{p}: {value:.1f}KB"
            )

        axes[1].set_xlabel("Delta Size (KB)")
        axes[1].set_ylabel("Cumulative Percentage of Blocks")
        axes[1].set_title("Cumulative Distribution of Absolute Overhead")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Cumulative distribution chart saved: {filename}")

    def plot_bandwidth_impact(self, filename):
        """Practical bandwidth impact scenarios"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Calculate metrics
        avg_current = self.df["current_compact_size"].mean()
        avg_with_transparent = self.df["estimated_with_transparent"].mean()
        avg_delta = avg_with_transparent - avg_current

        # Calculate blocks per day based on current network (post-Blossom)
        # Post-Blossom (after block 653,600): 75s blocks = 1,152 blocks/day
        # This is what matters for current light clients
        blocks_per_day = 1152

        daily_current_mb = (avg_current * blocks_per_day) / 1_000_000
        daily_with_mb = (avg_with_transparent * blocks_per_day) / 1_000_000
        daily_delta_mb = daily_with_mb - daily_current_mb

        # Daily sync with absolute delta
        axes[0, 0].bar(
            ["Current", "With\nTransparent"],
            [daily_current_mb, daily_with_mb],
            color=["steelblue", "coral"],
        )
        axes[0, 0].set_ylabel("MB")
        axes[0, 0].set_title(f"Daily Sync Bandwidth\n(~{blocks_per_day} blocks/day)")
        axes[0, 0].grid(True, alpha=0.3, axis="y")

        for i, v in enumerate([daily_current_mb, daily_with_mb]):
            axes[0, 0].text(
                i, v + 1, f"{v:.1f} MB", ha="center", va="bottom", fontweight="bold"
            )

        # Add delta annotation
        axes[0, 0].text(
            0.5,
            max(daily_current_mb, daily_with_mb) * 0.5,
            f"Δ = +{daily_delta_mb:.1f} MB\n({(daily_delta_mb/daily_current_mb)*100:.1f}%)",
            ha="center",
            fontsize=12,
            fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.3),
        )

        # Full sync (estimate based on current tip)
        max_height = self.df["height"].max()
        total_blocks = max_height  # Approximate total blocks
        full_current_gb = (avg_current * total_blocks) / 1_000_000_000
        full_with_gb = (avg_with_transparent * total_blocks) / 1_000_000_000
        full_delta_gb = full_with_gb - full_current_gb

        axes[0, 1].bar(
            ["Current", "With\nTransparent"],
            [full_current_gb, full_with_gb],
            color=["steelblue", "coral"],
        )
        axes[0, 1].set_ylabel("GB")
        axes[0, 1].set_title(f"Full Chain Sync\n(~{total_blocks:,} blocks)")
        axes[0, 1].grid(True, alpha=0.3, axis="y")

        for i, v in enumerate([full_current_gb, full_with_gb]):
            axes[0, 1].text(
                i, v + 0.1, f"{v:.2f} GB", ha="center", va="bottom", fontweight="bold"
            )

        # Add delta annotation
        axes[0, 1].text(
            0.5,
            max(full_current_gb, full_with_gb) * 0.5,
            f"Δ = +{full_delta_gb:.2f} GB\n({(full_delta_gb/full_current_gb)*100:.1f}%)",
            ha="center",
            fontsize=12,
            fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.3),
        )

        # Absolute delta chart - use MB consistently
        x = np.arange(3)
        width = 0.35

        # Calculate for different time periods (all in MB)
        daily_delta_mb = daily_delta_mb
        weekly_delta_mb = daily_delta_mb * 7
        monthly_delta_mb = daily_delta_mb * 30

        deltas = [daily_delta_mb, weekly_delta_mb, monthly_delta_mb]
        labels = [
            f"Daily\n({blocks_per_day} blocks)",
            "Weekly\n(7 days)",
            "Monthly\n(30 days)",
        ]

        bars = axes[1, 0].bar(x, deltas, color="coral", alpha=0.7)
        axes[1, 0].set_ylabel("Additional Bandwidth (MB)")
        axes[1, 0].set_title("Absolute Bandwidth Increase\n(Transparent Data Overhead)")
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(labels)
        axes[1, 0].grid(True, alpha=0.3, axis="y")

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, deltas)):
            height = bar.get_height()
            axes[1, 0].text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"+{val:.2f} MB",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Sync time (assume 5 Mbps connection)
        bandwidth_mbps = 5
        bandwidth_mb_per_sec = bandwidth_mbps / 8

        daily_time_current = daily_current_mb / bandwidth_mb_per_sec / 60  # minutes
        daily_time_with = daily_with_mb / bandwidth_mb_per_sec / 60
        daily_time_delta = daily_time_with - daily_time_current

        full_time_current = (
            full_current_gb * 1000 / bandwidth_mb_per_sec / 3600
        )  # hours
        full_time_with = full_with_gb * 1000 / bandwidth_mb_per_sec / 3600
        full_time_delta = full_time_with - full_time_current

        x = np.arange(2)
        axes[1, 1].bar(
            x - width / 2,
            [daily_time_current, full_time_current],
            width,
            label="Current",
            color="steelblue",
        )
        axes[1, 1].bar(
            x + width / 2,
            [daily_time_with, full_time_with],
            width,
            label="With Transparent",
            color="coral",
        )

        axes[1, 1].set_ylabel("Time")
        axes[1, 1].set_title(f"Sync Time\n(@{bandwidth_mbps} Mbps)")
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(["Daily\n(minutes)", "Full\n(hours)"])
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis="y")

        # Add delta annotations
        for i, delta in enumerate([daily_time_delta, full_time_delta]):
            y_pos = (
                max(
                    [daily_time_current, full_time_current][i],
                    [daily_time_with, full_time_with][i],
                )
                * 1.05
            )
            unit = "min" if i == 0 else "hrs"
            axes[1, 1].text(
                i,
                y_pos,
                f"+{delta:.1f} {unit}",
                ha="center",
                fontsize=10,
                fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.3),
            )

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Bandwidth impact chart saved: {filename}")

    def plot_heatmap(self, filename):
        """Heatmap of overhead by era and transaction characteristics"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Create bins for transaction count
        self.df["tx_bin"] = pd.cut(
            self.df["tx_count"],
            bins=[0, 10, 50, 100, 500, 10000],
            labels=["1-10", "11-50", "51-100", "101-500", "500+"],
        )

        # Pivot table: era vs tx_bin
        if "era" in self.df.columns and not self.df["era"].isna().all():
            pivot = self.df.pivot_table(
                values="delta_percent", index="era", columns="tx_bin", aggfunc="mean"
            )

            sns.heatmap(
                pivot,
                annot=True,
                fmt=".1f",
                cmap="YlOrRd",
                ax=axes[0],
                cbar_kws={"label": "Overhead (%)"},
            )
            axes[0].set_title("Average Overhead by Era and Transaction Count")
            axes[0].set_ylabel("Era")
            axes[0].set_xlabel("Transactions per Block")

        # Pivot table: transparent usage
        self.df["transparent_bin"] = pd.cut(
            self.df["transparent_inputs"] + self.df["transparent_outputs"],
            bins=[0, 10, 50, 100, 500, 10000],
            labels=["1-10", "11-50", "51-100", "101-500", "500+"],
        )

        if "era" in self.df.columns and not self.df["era"].isna().all():
            pivot2 = self.df.pivot_table(
                values="delta_percent",
                index="era",
                columns="transparent_bin",
                aggfunc="mean",
            )

            sns.heatmap(
                pivot2,
                annot=True,
                fmt=".1f",
                cmap="YlOrRd",
                ax=axes[1],
                cbar_kws={"label": "Overhead (%)"},
            )
            axes[1].set_title("Average Overhead by Era and Transparent I/O")
            axes[1].set_ylabel("Era")
            axes[1].set_xlabel("Transparent Inputs + Outputs")

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Heatmap saved: {filename}")

    def generate_report(self, filename):
        """Generate statistical report in Markdown format"""
        with open(filename, "w") as f:
            f.write("# Statistical Analysis Report\n\n")
            f.write("**Zcash Compact Block Transparent Data Overhead**\n\n")
            f.write("---\n\n")

            # Summary statistics
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total blocks analyzed:** {len(self.df):,}\n")
            f.write(
                f"- **Block height range:** {self.df['height'].min():,} - {self.df['height'].max():,}\n\n"
            )

            # Overhead statistics
            f.write("## Overhead Percentage\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Mean   | {self.df['delta_percent'].mean():.2f}% |\n")
            f.write(f"| Median | {self.df['delta_percent'].median():.2f}% |\n")
            f.write(f"| Std Dev| {self.df['delta_percent'].std():.2f}% |\n")
            f.write(f"| Min    | {self.df['delta_percent'].min():.2f}% |\n")
            f.write(f"| Max    | {self.df['delta_percent'].max():.2f}% |\n\n")

            # Percentiles
            f.write("## Percentiles\n\n")
            f.write("| Percentile | Overhead |\n")
            f.write("|------------|----------|\n")
            for p in [25, 50, 75, 90, 95, 99]:
                value = np.percentile(self.df["delta_percent"], p)
                f.write(f"| P{p} | {value:.2f}% |\n")
            f.write("\n")

            # Confidence intervals
            f.write("## Confidence Intervals (95%)\n\n")
            mean = self.df["delta_percent"].mean()
            std_err = stats.sem(self.df["delta_percent"])
            ci = stats.t.interval(0.95, len(self.df) - 1, loc=mean, scale=std_err)
            f.write(f"- **Mean overhead:** {mean:.2f}% ± {(ci[1]-mean):.2f}%\n")
            f.write(f"- **Range:** [{ci[0]:.2f}%, {ci[1]:.2f}%]\n\n")

            # By era
            f.write("## Statistics by Era\n\n")
            if "era" in self.df.columns:
                f.write("| Era | Count | Mean | Std Dev | Median | Min | Max |\n")
                f.write("|-----|-------|------|---------|--------|-----|-----|\n")

                era_order = ["sapling", "blossom", "heartwood", "canopy", "nu5", "nu6"]
                for era in era_order:
                    if era in self.df["era"].values:
                        era_data = self.df[self.df["era"] == era]["delta_percent"]
                        f.write(
                            f"| {era.capitalize()} | {len(era_data):,} | {era_data.mean():.2f}% | "
                            f"{era_data.std():.2f}% | {era_data.median():.2f}% | "
                            f"{era_data.min():.2f}% | {era_data.max():.2f}% |\n"
                        )
                f.write("\n")

            # Bandwidth impact
            f.write("## Practical Bandwidth Impact\n\n")

            avg_current = self.df["current_compact_size"].mean()
            avg_with = self.df["estimated_with_transparent"].mean()
            avg_delta = avg_with - avg_current

            f.write("### Average Block Sizes\n\n")
            f.write(f"- **Current:** {avg_current/1000:.2f} KB\n")
            f.write(f"- **With transparent:** {avg_with/1000:.2f} KB\n")
            f.write(f"- **Delta:** {avg_delta/1000:.2f} KB\n\n")

            blocks_per_day = 1152
            daily_current_mb = (avg_current * blocks_per_day) / 1_000_000
            daily_with_mb = (avg_with * blocks_per_day) / 1_000_000
            daily_delta_mb = daily_with_mb - daily_current_mb

            f.write(f"### Daily Sync (~{blocks_per_day} blocks)\n\n")
            f.write(f"- **Current:** {daily_current_mb:.2f} MB\n")
            f.write(f"- **With transparent:** {daily_with_mb:.2f} MB\n")
            f.write(
                f"- **Additional:** {daily_delta_mb:.2f} MB ({(daily_delta_mb/daily_current_mb)*100:.1f}%)\n\n"
            )

            # Correlations
            f.write("## Correlations\n\n")
            corr_inputs = self.df["transparent_inputs"].corr(self.df["delta_bytes"])
            corr_outputs = self.df["transparent_outputs"].corr(self.df["delta_bytes"])
            corr_tx = self.df["tx_count"].corr(self.df["delta_percent"])

            f.write("| Variables | Correlation (r) |\n")
            f.write("|-----------|----------------|\n")
            f.write(f"| Transparent inputs → delta bytes | {corr_inputs:.3f} |\n")
            f.write(f"| Transparent outputs → delta bytes | {corr_outputs:.3f} |\n")
            f.write(f"| Transaction count → overhead % | {corr_tx:.3f} |\n\n")

            # Recommendations
            f.write("## Decision Framework\n\n")
            median_overhead = self.df["delta_percent"].median()
            p95_overhead = np.percentile(self.df["delta_percent"], 95)

            f.write(f"- **Median overhead:** {median_overhead:.1f}%\n")
            f.write(f"- **95th percentile:** {p95_overhead:.1f}%\n\n")

            if median_overhead < 20:
                f.write("### ✅ Recommendation: LOW IMPACT\n\n")
                f.write(
                    "The overhead is relatively small (<20%). Consider making transparent "
                )
                f.write(
                    "data part of the default GetBlockRange method. This would:\n\n"
                )
                f.write("- Simplify the API (single method)\n")
                f.write("- Provide feature parity with full nodes\n")
                f.write("- Have minimal bandwidth impact on users\n")
            elif median_overhead < 50:
                f.write("### ⚠️ Recommendation: MODERATE IMPACT\n\n")
                f.write("The overhead is significant (20-50%). Consider:\n\n")
                f.write("- Separate opt-in method for transparent data\n")
                f.write("- Pool-based filtering (as in librustzcash PR #1781)\n")
                f.write("- Let clients choose based on their needs\n")
                f.write("- Important for mobile/bandwidth-limited users\n")
            else:
                f.write("### 🚨 Recommendation: HIGH IMPACT\n\n")
                f.write("The overhead is substantial (>50%). Strongly consider:\n\n")
                f.write("- Separate method required\n")
                f.write("- Clear opt-in for clients needing transparent data\n")
                f.write("- Critical for mobile and bandwidth-limited users\n")
                f.write("- May significantly impact sync times\n")

            f.write("\n---\n\n")
            f.write("*Report generated by Compact Block Analyzer*\n")

        print(f"  ✓ Statistical report saved: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate visualizations and statistical analysis for compact block data"
    )
    parser.add_argument("csv_file", help="Path to CSV file with analysis results")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./charts",
        help="Output directory for charts (default: ./charts)",
    )

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


if __name__ == "__main__":
    exit(main())
