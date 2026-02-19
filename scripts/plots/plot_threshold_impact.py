"""Visualize anomaly threshold impact over score distribution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns


def visualize_threshold(input_csv: Path, threshold: float, output_file: Path) -> int:
    if not input_csv.exists():
        print(f"Error: Input file {input_csv} not found.")
        return 2

    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return 2

    if "score_raw" not in df.columns:
        print("Error: 'score_raw' column missing.")
        return 2

    output_file.parent.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 6))

    ax = sns.histplot(
        data=df,
        x="score_raw",
        bins=50,
        stat="count",
        log_scale=(False, True),
        element="step",
        color="skyblue",
        alpha=0.6,
        label="Scores",
    )

    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

    xmin, _ = ax.get_xlim()
    plot_min = min(float(df["score_raw"].min()), float(xmin))

    plt.axvline(x=threshold, color="red", linestyle="--", linewidth=2, label=f"Threshold ({threshold:.4f})")
    plt.axvspan(plot_min, threshold, color="red", alpha=0.1, label="Flagged region")

    n_total = len(df)
    n_flagged = int((df["score_raw"] < threshold).sum())
    fpr = (n_flagged / n_total) * 100 if n_total else 0.0

    plt.title(f"Threshold Impact Analysis (Flagged rate: {fpr:.4f}%)", fontsize=14)
    plt.xlabel("Anomaly Score (Lower = More Anomalous)", fontsize=12)
    plt.ylabel("Count (Log Scale)", fontsize=12)
    plt.legend(loc="upper right")

    stats_text = (
        f"Total Samples: {n_total}\n"
        f"Threshold:     {threshold:.4f}\n"
        f"Flagged:       {n_flagged}\n"
        f"Flagged Rate:  {fpr:.4f}%"
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
        print(f"Threshold plot saved to {output_file}")
    except Exception as e:
        print(f"Error saving plot: {e}")
        return 2
    finally:
        plt.close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualize threshold impact for anomaly scores")
    parser.add_argument("input_csv", type=Path, help="Path to CSV with score_raw column")
    parser.add_argument("threshold", type=float, help="Threshold value")
    parser.add_argument("output_file", type=Path, help="Path to output PNG")
    args = parser.parse_args()
    return visualize_threshold(args.input_csv, args.threshold, args.output_file)


if __name__ == "__main__":
    raise SystemExit(main())
