"""
Cluster summary bar chart generator.
Adapted from: Simulator Code Correct Version/Cluster_Summary_Graphics_Generator.py
(Original file not modified.)
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


METRIC_COLUMNS: List[str] = [
    "share_lognormal","share_beta","share_triangular",
    "mean_SP","mean_LA","mean_AD","mean_TF",
]
MAPE_COLUMNS: Dict[str, str] = {
    "PERT": "cluster_mean_mape_pert",
    "BB2": "cluster_mean_mape_bb2",
    "Lognormal": "cluster_mean_mape_lognormal",
}
METHOD_COLORS: Dict[str, str] = {"PERT": "#bdbdbd", "BB2": "#969696", "Lognormal": "#737373"}
METHOD_HATCHES: Dict[str, str] = {"PERT": "/", "BB2": "x", "Lognormal": "."}
METRIC_STYLES: Dict[str, Tuple[str, str]] = {
    "share_lognormal": ("#f0f0f0", "."), "share_beta": ("#d9d9d9", "/"),
    "share_triangular": ("#bdbdbd", "x"), "mean_SP": ("#f0f0f0", "-"),
    "mean_LA": ("#d9d9d9", "\\"), "mean_AD": ("#bdbdbd", "|"), "mean_TF": ("#969696", "+"),
}


def _expand_ylim_for_labels(values: List[float], force_zero_bottom: bool = True) -> Tuple[float, float]:
    if not values:
        return (0.0, 1.0)
    y_min = min(values)
    y_max = max(values)
    span = max(y_max - y_min, 1.0)
    base_bottom = 0.0 if force_zero_bottom and y_min >= 0 else y_min - span * 0.1
    base_top = y_max + span * 0.1
    return base_bottom - span * 0.03, base_top + span * 0.12


def _label_text(v: float) -> str:
    return f"{v:.3f}" if abs(v) < 10 else f"{v:.2f}"


def _add_bar_labels(ax, bars) -> None:
    y0, y1 = ax.get_ylim()
    span = max(y1 - y0, 1.0)
    offset = span * 0.015
    for bar in bars:
        h = float(bar.get_height())
        x = bar.get_x() + bar.get_width() / 2
        y = h + offset if h >= 0 else h - offset
        va = "bottom" if h >= 0 else "top"
        ax.text(x, y, _label_text(h), ha="center", va=va, fontsize=8, clip_on=False)


def validate_schema(df: pd.DataFrame) -> None:
    required = ["cluster_id", *METRIC_COLUMNS, *MAPE_COLUMNS.values()]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"cluster_summary.csv missing columns:\n" + "\n".join(f"- {c}" for c in missing))


def plot_grouped_mape(df: pd.DataFrame, output_path: Path, dpi: int) -> None:
    cluster_ids = sorted(df["cluster_id"].unique())
    x = np.arange(len(cluster_ids))
    width = 0.25
    fig, ax = plt.subplots(figsize=(max(8, len(cluster_ids) * 1.5), 6))
    all_vals: List[float] = []
    all_bars = []
    for i, (label, col) in enumerate(MAPE_COLUMNS.items()):
        vals = [float(df.loc[df["cluster_id"] == cid, col].iloc[0]) for cid in cluster_ids]
        all_vals.extend(vals)
        offset = (i - 1) * width
        bars = ax.bar(x + offset, vals, width, label=label,
                      color=METHOD_COLORS[label], hatch=METHOD_HATCHES[label], edgecolor="black", linewidth=0.6)
        all_bars.extend(bars)
    y_bottom, y_top = _expand_ylim_for_labels(all_vals, force_zero_bottom=True)
    ax.set_ylim(y_bottom, y_top)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Cluster {cid}" for cid in cluster_ids])
    ax.set_ylabel("Mean MAPE (%)")
    ax.set_title("Cluster Mean MAPE by Method")
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    _add_bar_labels(ax, all_bars)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def plot_single_metric(df: pd.DataFrame, metric: str, output_path: Path, dpi: int) -> None:
    cluster_ids = sorted(df["cluster_id"].unique())
    vals = [float(df.loc[df["cluster_id"] == cid, metric].iloc[0]) for cid in cluster_ids]
    color, hatch = METRIC_STYLES.get(metric, ("#cccccc", ""))
    fig, ax = plt.subplots(figsize=(max(6, len(cluster_ids) * 1.2), 5))
    x = np.arange(len(cluster_ids))
    bars = ax.bar(x, vals, color=color, hatch=hatch, edgecolor="black", linewidth=0.6)
    y_bottom, y_top = _expand_ylim_for_labels(vals, force_zero_bottom=True)
    ax.set_ylim(y_bottom, y_top)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Cluster {cid}" for cid in cluster_ids])
    ax.set_ylabel(metric)
    ax.set_title(f"Cluster Summary: {metric}")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    _add_bar_labels(ax, bars)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def run_cluster_graphics(
    input_csv: Path,
    output_dir: Optional[Path] = None,
    dpi: int = 300,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> Path:
    """Generate cluster summary bar charts. Returns output_dir."""
    input_csv = Path(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if output_dir is None:
        output_dir = input_csv.parent / "graphics"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv)
    validate_schema(df)

    total = len(METRIC_COLUMNS) + 1
    step = 0

    if cancel_check and cancel_check():
        raise InterruptedError("Cluster graphics cancelled.")

    if progress_cb:
        progress_cb(step, total, "Generating grouped MAPE chart...")
    plot_grouped_mape(df, output_dir / "cluster_mape_grouped.png", dpi)
    step += 1

    for metric in METRIC_COLUMNS:
        if cancel_check and cancel_check():
            raise InterruptedError("Cluster graphics cancelled.")
        if progress_cb:
            progress_cb(step, total, f"Generating {metric} chart...")
        plot_single_metric(df, metric, output_dir / f"cluster_{metric}.png", dpi)
        step += 1

    if progress_cb:
        progress_cb(total, total, "Done.")
    return output_dir
