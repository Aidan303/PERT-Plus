"""
PCA analysis of network features.
Adapted from: Simulator Code Correct Version/PCA_Network_Feature_Analysis.py
(Original file not modified.)
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


BASE_FEATURES: List[str] = ["SP", "LA", "AD", "TF", "network_most_likely"]
DISTRIBUTION_SOURCE: List[str] = ["is_beta", "is_lognormal"]
ONE_HOT_DIST: List[str] = ["dist_beta", "dist_lognormal", "dist_triangular"]
NODE_COL = "number_of_nodes"


def apply_plot_style() -> None:
    plt.rcParams.update({
        "font.family": "serif", "font.size": 11, "axes.titlesize": 13,
        "axes.labelsize": 12, "axes.edgecolor": "black", "axes.linewidth": 1.0,
        "xtick.direction": "out", "ytick.direction": "out",
        "legend.frameon": True, "legend.edgecolor": "black",
        "figure.facecolor": "white", "axes.facecolor": "white",
    })


def build_feature_set(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str]]:
    available = [c for c in BASE_FEATURES if c in df.columns]
    if NODE_COL in df.columns:
        available.append(NODE_COL)

    # One-hot encode distribution
    if "is_beta" in df.columns and "is_lognormal" in df.columns:
        is_beta = pd.to_numeric(df["is_beta"], errors="coerce").fillna(0) >= 0.5
        is_lognormal = pd.to_numeric(df["is_lognormal"], errors="coerce").fillna(0) >= 0.5
        df = df.copy()
        df["dist_beta"] = is_beta.astype(int)
        df["dist_lognormal"] = is_lognormal.astype(int)
        df["dist_triangular"] = (~is_beta & ~is_lognormal).astype(int)
        available += [c for c in ONE_HOT_DIST if c not in available]
    elif "distribution" in df.columns:
        df = df.copy()
        df["dist_beta"] = (df["distribution"] == "beta").astype(int)
        df["dist_lognormal"] = (df["distribution"] == "lognormal").astype(int)
        df["dist_triangular"] = (df["distribution"] == "triangular").astype(int)
        available += [c for c in ONE_HOT_DIST if c not in available]

    feature_df = df[available].apply(pd.to_numeric, errors="coerce")
    feature_df = feature_df.fillna(feature_df.median(numeric_only=True))
    feature_df = feature_df.dropna(axis=1, how="all")
    return feature_df, list(feature_df.columns)


def fit_pca(feature_df: pd.DataFrame) -> tuple[PCA, np.ndarray, StandardScaler]:
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(feature_df)
    pca = PCA(svd_solver="full")
    components = pca.fit_transform(x_scaled)
    return pca, components, scaler


def retained_component_count(pca: PCA, threshold: float) -> int:
    cumulative = np.cumsum(pca.explained_variance_ratio_)
    n = int(np.searchsorted(cumulative, threshold) + 1)
    return min(n, len(pca.explained_variance_ratio_))


def plot_scree(pca: PCA, output_path: Path, dpi: int) -> None:
    n = len(pca.explained_variance_ratio_)
    x = np.arange(1, n + 1)
    bar_vals = pca.explained_variance_ratio_ * 100
    fig, ax1 = plt.subplots(figsize=(9, 5))
    bars = ax1.bar(x, bar_vals, color="#bdbdbd", edgecolor="black", linewidth=0.6)
    top = float(max(bar_vals)) if len(bar_vals) else 1.0
    ax1.set_ylim(0, top * 1.18)
    for bar in bars:
        h = float(bar.get_height())
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            h + max(top, 1.0) * 0.015,
            f"{h:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
            clip_on=False,
        )
    ax1.set_xlabel("Principal Component")
    ax1.set_ylabel("Explained Variance (%)")
    ax1.set_title("PCA Scree Plot")
    ax2 = ax1.twinx()
    cumulative = np.cumsum(pca.explained_variance_ratio_) * 100
    ax2.plot(x, cumulative, "o-", color="black", linewidth=1.5, markersize=4)
    ax2.axhline(95, color="red", linestyle="--", linewidth=1, alpha=0.6, label="95%")
    ax2.set_ylabel("Cumulative Explained Variance (%)")
    ax2.set_ylim(0, 105)
    ax2.legend(loc="center right")
    ax1.set_xticks(x)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def plot_loadings_heatmap(pca: PCA, feature_names: List[str], n_components: int, output_path: Path, dpi: int) -> None:
    loadings = pca.components_[:n_components]
    fig, ax = plt.subplots(figsize=(max(8, len(feature_names) * 0.9), max(4, n_components * 0.8)))
    im = ax.imshow(loadings, cmap="RdBu_r", aspect="auto", vmin=-1, vmax=1)
    ax.set_xticks(range(len(feature_names)))
    ax.set_xticklabels(feature_names, rotation=45, ha="right")
    ax.set_yticks(range(n_components))
    ax.set_yticklabels([f"PC{i+1}" for i in range(n_components)])
    ax.set_title(f"PCA Loadings Heatmap (first {n_components} components)")
    plt.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def export_tables(pca: PCA, feature_names: List[str], n_retained: int, output_dir: Path) -> None:
    ev_df = pd.DataFrame({
        "component": [f"PC{i+1}" for i in range(len(pca.explained_variance_ratio_))],
        "explained_variance_ratio": pca.explained_variance_ratio_,
        "cumulative_variance_ratio": np.cumsum(pca.explained_variance_ratio_),
        "eigenvalue": pca.explained_variance_,
    })
    ev_df.to_csv(output_dir / "pca_explained_variance.csv", index=False)

    loadings_df = pd.DataFrame(
        pca.components_[:n_retained],
        index=[f"PC{i+1}" for i in range(n_retained)],
        columns=feature_names,
    )
    loadings_df.to_csv(output_dir / "pca_loadings.csv")


def run_pca(
    input_csv: Path,
    output_dir: Optional[Path] = None,
    variance_threshold: float = 0.95,
    dpi: int = 300,
    random_state: int = 42,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> Path:
    """Run PCA analysis. Returns output_dir."""
    input_csv = Path(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if output_dir is None:
        output_dir = input_csv.parent / "PCA_analysis"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    apply_plot_style()

    if progress_cb:
        progress_cb(0, 5, "Loading data...")
    df = pd.read_csv(input_csv)

    if cancel_check and cancel_check():
        raise InterruptedError("PCA cancelled by user.")

    if progress_cb:
        progress_cb(1, 5, "Building feature set...")
    feature_df, feature_names = build_feature_set(df)
    if feature_df.empty:
        raise ValueError("No usable feature columns found in input CSV.")

    if progress_cb:
        progress_cb(2, 5, "Fitting PCA...")
    pca, components, scaler = fit_pca(feature_df)
    n_retained = retained_component_count(pca, variance_threshold)

    if cancel_check and cancel_check():
        raise InterruptedError("PCA cancelled by user.")

    if progress_cb:
        progress_cb(3, 5, "Exporting tables...")
    export_tables(pca, feature_names, n_retained, output_dir)

    # Save projected components
    components_df = pd.DataFrame(
        components[:, :n_retained],
        columns=[f"PC{i+1}" for i in range(n_retained)],
        index=feature_df.index,
    )
    components_df.to_csv(output_dir / "pca_components.csv", index=False)

    if cancel_check and cancel_check():
        raise InterruptedError("PCA cancelled by user.")

    if progress_cb:
        progress_cb(4, 5, "Generating plots...")
    plot_scree(pca, output_dir / "pca_scree.png", dpi)
    plot_loadings_heatmap(pca, feature_names, n_retained, output_dir / "pca_loadings_heatmap.png", dpi)

    if progress_cb:
        progress_cb(5, 5, f"Done. Retained {n_retained} components ({variance_threshold*100:.0f}% variance).")
    return output_dir
