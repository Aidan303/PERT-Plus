"""
5D complexity slice visualizer (3D scatter + Plotly HTML).
Adapted from: Simulator Code Correct Version/Complexity_5D_Slice_Visualizer.py
(Original file not modified.)
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
import numpy as np

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


COMPLEXITY_COLS: List[str] = ["SP", "LA", "AD", "TF"]
DISTRIBUTIONS: List[str] = ["beta", "lognormal", "triangular"]
CLUSTER_COLORS: List[str] = [
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
    "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
]
DISTRIBUTION_SYMBOLS: Dict[str, str] = {"beta": "circle", "lognormal": "square", "triangular": "diamond"}


def _scatter_3d_matplotlib(
    subset: pd.DataFrame,
    x_col: str, y_col: str, z_col: str, color_col: str,
    distribution: str, output_path: Path, dpi: int,
) -> None:
    if subset.empty:
        return
    x = pd.to_numeric(subset[x_col], errors="coerce")
    y = pd.to_numeric(subset[y_col], errors="coerce")
    z = pd.to_numeric(subset[z_col], errors="coerce")
    c = pd.to_numeric(subset[color_col], errors="coerce")
    valid = ~(x.isna() | y.isna() | z.isna() | c.isna())
    x, y, z, c = x[valid], y[valid], z[valid], c[valid]

    cmap = plt.cm.viridis  # type: ignore[attr-defined]
    c_norm = (c - c.min()) / (c.max() - c.min() + 1e-9)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    sc = ax.scatter(x, y, z, c=c_norm, cmap=cmap, s=18, alpha=0.7, edgecolors="none")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_zlabel(z_col)
    ax.set_title(f"{distribution.capitalize()} — 5D Slice\n(color = {color_col})")
    fig.colorbar(sc, ax=ax, shrink=0.6, label=color_col)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def _save_interactive_html(
    subset: pd.DataFrame,
    x_col: str, y_col: str, z_col: str, color_col: str,
    distribution: str, cluster_col: Optional[str],
    output_path: Path,
) -> None:
    if not PLOTLY_AVAILABLE or subset.empty:
        return
    x = pd.to_numeric(subset[x_col], errors="coerce")
    y = pd.to_numeric(subset[y_col], errors="coerce")
    z = pd.to_numeric(subset[z_col], errors="coerce")
    c = pd.to_numeric(subset[color_col], errors="coerce")
    valid = ~(x.isna() | y.isna() | z.isna() | c.isna())
    subset_v = subset[valid]
    x, y, z, c = x[valid], y[valid], z[valid], c[valid]

    marker_kwargs: dict = dict(color=c, colorscale="Viridis", size=5, opacity=0.7, showscale=True, colorbar=dict(title=color_col))
    if cluster_col and cluster_col in subset_v.columns:
        marker_kwargs["symbol"] = [DISTRIBUTION_SYMBOLS.get(distribution, "circle")] * len(x)

    fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode="markers", marker=marker_kwargs)])
    fig.update_layout(
        title=f"{distribution.capitalize()} — 5D Complexity Slice",
        scene=dict(xaxis_title=x_col, yaxis_title=y_col, zaxis_title=z_col),
    )
    fig.write_html(str(output_path))


def run_complexity_viz(
    input_csv: Path,
    output_dir: Optional[Path] = None,
    x_col: str = "SP",
    y_col: str = "LA",
    z_col: str = "AD",
    color_col: str = "TF",
    generate_html: bool = True,
    dpi: int = 300,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> Path:
    """Generate 3D scatter plots (PNG + optional HTML). Returns output_dir."""
    input_csv = Path(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if output_dir is None:
        output_dir = input_csv.parent / "graphics" / "complexity_5d_slices"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv)
    for col in [x_col, y_col, z_col, color_col]:
        if col not in df.columns:
            raise ValueError(f"Column not found in CSV: {col}")

    dist_col = "distribution" if "distribution" in df.columns else None
    cluster_col = "cluster_id" if "cluster_id" in df.columns else None

    distributions_present: list = []
    if dist_col:
        distributions_present = [d for d in DISTRIBUTIONS if d in df[dist_col].values]
    if not distributions_present:
        distributions_present = ["all"]

    total = len(distributions_present)
    for i, dist in enumerate(distributions_present):
        if cancel_check and cancel_check():
            raise InterruptedError("Complexity visualizer cancelled.")
        if progress_cb:
            progress_cb(i, total, f"Rendering {dist}...")

        if dist == "all":
            subset = df
        else:
            subset = df[df[dist_col] == dist]  # type: ignore[index]

        png_path = output_dir / f"5d_slice_{dist}.png"
        _scatter_3d_matplotlib(subset, x_col, y_col, z_col, color_col, dist, png_path, dpi)

        if generate_html and PLOTLY_AVAILABLE:
            html_path = output_dir / f"5d_slice_{dist}.html"
            _save_interactive_html(subset, x_col, y_col, z_col, color_col, dist, cluster_col, html_path)

    if progress_cb:
        progress_cb(total, total, "Done.")
    return output_dir
