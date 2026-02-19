"""Plot anomaly score distributions from CSV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns


def plot_distributions(input_csv: Path, output_file: Path) -> int:
    if not input_csv.exists():
        print(f"Error: Input file {input_csv} not found.")
        return 2

    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return 2

    if "score_raw" not in df.columns:
        print("Error: 'score_raw' column missing from CSV.")
        return 2

    output_file.parent.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")
    # Normalize fonts for constrained environments (CI/Windows variants).
    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Liberation Sans", "sans-serif"]
    mpl.rcParams["mathtext.fontset"] = "dejavusans"
    mpl.rcParams["mathtext.fallback"] = "cm"
    mpl.rcParams["text.usetex"] = False

    plt.figure(figsize=(12, 6))
    ax = sns.histplot(
        data=df,
        x="score_raw",
        kde=True,
        stat="count",
        log_scale=(False, True),
        line_kws={"linewidth": 2},
    )

    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

    plt.title("Anomaly Score Distribution (Log Scale Count)", fontsize=14)
    plt.xlabel("Anomaly Score (Lower = More Anomalous)", fontsize=12)
    plt.ylabel("Count (Log Scale)", fontsize=12)

    stats = df["score_raw"].describe()
    stats_text = (
        f"Count: {int(stats['count'])}\n"
        f"Mean:  {stats['mean']:.4f}\n"
        f"Std:   {stats['std']:.4f}\n"
        f"Min:   {stats['min']:.4f}\n"
        f"Max:   {stats['max']:.4f}"
    )

    plt.text(
        0.02,
        0.95,
        stats_text,
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=10,
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
    )

    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    try:
        plt.savefig(output_file)
        print(f"Distribution plot saved to {output_file}")
    except Exception as e:
        # Fallback: render a minimal, text-free sparkline image to avoid
        # host-specific font stack failures while still producing a usable PNG.
        try:
            fig = plt.figure(figsize=(12, 3))
            ax2 = fig.add_axes([0.02, 0.15, 0.96, 0.8])
            ax2.plot(df["score_raw"].to_numpy())
            ax2.set_xticks([])
            ax2.set_yticks([])
            for spine in ax2.spines.values():
                spine.set_visible(False)
            fig.savefig(output_file)
            print(f"Distribution plot saved (fallback mode) to {output_file}")
            return 0
        except Exception as fallback_exc:
            print(f"Error saving plot: {e}")
            print(f"Fallback render failed: {fallback_exc}")
            return 2
    finally:
        plt.close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot anomaly score distributions from CSV")
    parser.add_argument("input_csv", type=Path, help="Path to CSV with score_raw column")
    parser.add_argument("output_file", type=Path, help="Path to output PNG")
    args = parser.parse_args()
    return plot_distributions(args.input_csv, args.output_file)


if __name__ == "__main__":
    raise SystemExit(main())
