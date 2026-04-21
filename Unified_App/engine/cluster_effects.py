"""
Per-cluster effect size and bootstrap confidence interval analysis.
Adapted from: Simulator Code Correct Version/Cluster_Effect_Size_Analysis.py
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


METHODS: List[str] = ["pert", "bb2", "lognormal"]
MAPE_COLS: Dict[str, str] = {"pert": "mape_pert", "bb2": "mape_bb2", "lognormal": "mape_lognormal"}
COMPARISONS: List[Tuple[str, str]] = [("bb2", "pert"), ("bb2", "lognormal"), ("lognormal", "pert")]


def apply_plot_style() -> None:
    plt.rcParams.update({
        "font.family": "serif", "font.size": 11, "axes.titlesize": 13,
        "axes.labelsize": 12, "axes.edgecolor": "black", "axes.linewidth": 1.0,
        "xtick.direction": "out", "ytick.direction": "out",
        "legend.frameon": True, "legend.edgecolor": "black",
        "figure.facecolor": "white", "axes.facecolor": "white",
    })


def bootstrap_ci(diff: np.ndarray, n_bootstrap: int, ci_level: float, seed: int) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    means = [rng.choice(diff, size=len(diff), replace=True).mean() for _ in range(n_bootstrap)]
    alpha = (1 - ci_level) / 2
    return float(np.quantile(means, alpha)), float(np.quantile(means, 1 - alpha))


def cohens_d(diff: np.ndarray) -> float:
    if diff.std(ddof=1) == 0:
        return 0.0
    return float(diff.mean() / diff.std(ddof=1))


def analyze_cluster_effects(
    df: pd.DataFrame,
    n_bootstrap: int,
    ci_level: float,
    seed: int,
) -> pd.DataFrame:
    records = []
    for cluster_id, group in df.groupby("cluster_id", dropna=False):
        for method_a, method_b in COMPARISONS:
            col_a = MAPE_COLS[method_a]
            col_b = MAPE_COLS[method_b]
            if col_a not in group.columns or col_b not in group.columns:
                continue
            vals_a = pd.to_numeric(group[col_a], errors="coerce").dropna().values
            vals_b = pd.to_numeric(group[col_b], errors="coerce").dropna().values
            n = min(len(vals_a), len(vals_b))
            if n < 3:
                continue
            diff = vals_a[:n] - vals_b[:n]
            mean_diff = float(diff.mean())
            d = cohens_d(diff)
            ci_low, ci_high = bootstrap_ci(diff, n_bootstrap, ci_level, seed + int(cluster_id) * 100)
            records.append({
                "cluster_id": int(cluster_id),
                "comparison": f"{method_a}_vs_{method_b}",
                "method_a": method_a, "method_b": method_b,
                "n": n, "mean_diff_mape": mean_diff,
                "cohens_d": d,
                f"ci_{int(ci_level*100)}_low": ci_low,
                f"ci_{int(ci_level*100)}_high": ci_high,
            })
    return pd.DataFrame(records)


def make_forest_plot(
    results_df: pd.DataFrame,
    comparison: str,
    output_path: Path,
    ci_level: float,
    dpi: int,
) -> None:
    subset = results_df[results_df["comparison"] == comparison].sort_values("cluster_id")
    if subset.empty:
        return
    ci_low_col = f"ci_{int(ci_level*100)}_low"
    ci_high_col = f"ci_{int(ci_level*100)}_high"
    fig, ax = plt.subplots(figsize=(8, max(4, len(subset) * 0.7)))
    y_pos = np.arange(len(subset))
    for i, (_, row) in enumerate(subset.iterrows()):
        err_low = row["mean_diff_mape"] - row[ci_low_col]
        err_high = row[ci_high_col] - row["mean_diff_mape"]
        ax.errorbar(
            row["mean_diff_mape"], y_pos[i],
            xerr=[[max(0, err_low)], [max(0, err_high)]],
            fmt="o", color="black", markersize=6, capsize=4, elinewidth=1.5,
        )
    ax.axvline(0, color="red", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"Cluster {int(r['cluster_id'])} (n={int(r['n'])})" for _, r in subset.iterrows()])
    parts = comparison.split("_vs_")
    ax.set_xlabel(f"Mean MAPE difference: {parts[0].upper()} − {parts[1].upper()} (%)")
    ax.set_title(f"Forest Plot: {parts[0].upper()} vs {parts[1].upper()}\n{int(ci_level*100)}% Bootstrap CI")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def run_effect_size_analysis(
    input_csv: Path,
    output_dir: Optional[Path] = None,
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
    seed: int = 42,
    dpi: int = 300,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> Path:
    """Compute effect sizes and forest plots. Returns output_dir."""
    input_csv = Path(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if output_dir is None:
        output_dir = input_csv.parent / "effect_size_analysis"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    apply_plot_style()

    if progress_cb:
        progress_cb(0, 3, "Loading data...")
    df = pd.read_csv(input_csv)
    required = ["cluster_id", *MAPE_COLS.values()]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Input CSV missing columns: {missing}")

    if cancel_check and cancel_check():
        raise InterruptedError("Effect size analysis cancelled.")

    if progress_cb:
        progress_cb(1, 3, "Computing bootstrap CIs...")
    results_df = analyze_cluster_effects(df, n_bootstrap, ci_level, seed)
    results_df.to_csv(output_dir / "effect_size_results.csv", index=False)

    if cancel_check and cancel_check():
        raise InterruptedError("Effect size analysis cancelled.")

    if progress_cb:
        progress_cb(2, 3, "Generating forest plots...")
    for comparison in [f"{a}_vs_{b}" for a, b in COMPARISONS]:
        if cancel_check and cancel_check():
            raise InterruptedError("Effect size analysis cancelled.")
        make_forest_plot(results_df, comparison, output_dir / f"forest_{comparison}.png", ci_level, dpi)

    if progress_cb:
        progress_cb(3, 3, "Done.")
    return output_dir
