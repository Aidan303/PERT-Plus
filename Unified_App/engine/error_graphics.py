"""
Error analysis graphics generator.
Adapted from: Simulator Code Correct Version/Error_Analysis_Graphics_Generator.py
(Original file not modified.)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


PERCENTILE_ORDER: List[str] = [
    "p1","p10","p20","p25","p30","p40","p50",
    "p60","p70","p75","p80","p90","p95","p99","p99_9",
]
PERCENTILE_LABELS: List[str] = [
    "p1","p10","p20","p25","p30","p40","p50",
    "p60","p70","p75","p80","p90","p95","p99","p99.9",
]
METHODS: List[str] = ["pert","bb2","lognormal"]
METHOD_COLORS: Dict[str,str] = {"pert":"#1f77b4","bb2":"#ff7f0e","lognormal":"#2ca02c","cross_method":"#d62728"}
DISTRIBUTION_COLORS: Dict[str,str] = {"beta":"#1f77b4","triangular":"#ff7f0e","lognormal":"#2ca02c"}
DISTRIBUTION_HATCHES: Dict[str,str] = {"beta":"/","triangular":"x","lognormal":"."}
METHOD_HATCHES: Dict[str,str] = {"pert":"/","bb2":"x","lognormal":"."}
DISTRIBUTION_LINE_STYLES: Dict[str,str] = {"beta":"-","triangular":"--","lognormal":"-."}
DISTRIBUTION_MARKERS: Dict[str,str] = {"beta":"o","triangular":"s","lognormal":"^"}
SINGLE_CURVE_STYLES: Dict[str,Dict[str,str]] = {
    "pert":{"linestyle":"-","marker":"o"},"bb2":{"linestyle":"--","marker":"s"},
    "lognormal":{"linestyle":"-.","marker":"^"},"cross_method":{"linestyle":":","marker":"D"},
}
FIGURE_SIZE = (12, 6)
KNOWN_DISTRIBUTIONS = {"beta", "triangular", "lognormal"}


def _expand_ylim_for_bar_labels(y_bottom: float, y_top: float) -> tuple[float, float]:
    span = max(y_top - y_bottom, 1.0)
    extra = span * 0.12
    return y_bottom - extra * 0.25, y_top + extra


def _fmt_bar_value(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}%"
    if abs(value) >= 10:
        return f"{value:.1f}%"
    return f"{value:.2f}%"


def _add_bar_value_labels(ax, bars) -> None:
    y0, y1 = ax.get_ylim()
    span = max(y1 - y0, 1.0)
    offset = span * 0.015
    for bar in bars:
        h = float(bar.get_height())
        x = bar.get_x() + bar.get_width() / 2
        y = h + offset if h >= 0 else h - offset
        va = "bottom" if h >= 0 else "top"
        ax.text(x, y, _fmt_bar_value(h), ha="center", va=va, fontsize=8, clip_on=False)


def extract_distribution_name(input_csv_path: str) -> str:
    stem = Path(input_csv_path).stem.lower()
    for candidate in ("beta","lognormal","triangular"):
        if candidate in stem:
            return candidate
    stem = re.sub(r"^batch_results_","",stem)
    return stem or "unknown"


def _normalize_distribution_name(value: str) -> str:
    candidate = str(value).strip().lower()
    if candidate in KNOWN_DISTRIBUTIONS:
        return candidate
    return "unknown"


def _infer_distribution_from_analysis_csv(summary_path: Path) -> str:
    # Try the common paired file naming first.
    if summary_path.name.endswith("_analysis_summary.json"):
        candidate_csv = summary_path.with_name(
            summary_path.name.replace("_analysis_summary.json", "_analysis_results.csv")
        )
        if candidate_csv.exists():
            try:
                df = pd.read_csv(candidate_csv)
                if "distribution" in df.columns:
                    values = [
                        _normalize_distribution_name(v)
                        for v in df["distribution"].dropna().unique().tolist()
                    ]
                    values = [v for v in values if v != "unknown"]
                    if len(values) == 1:
                        return values[0]
            except Exception:
                pass
    return "unknown"


def get_distribution_label(summary: Dict, summary_path: Optional[Path] = None) -> str:
    metadata = summary.get("metadata", {})
    declared = _normalize_distribution_name(str(metadata.get("distribution", "")))
    if declared != "unknown":
        return declared

    from_input_csv = _normalize_distribution_name(
        extract_distribution_name(str(metadata.get("input_csv", "")))
    )
    if from_input_csv != "unknown":
        return from_input_csv

    if summary_path is not None:
        from_analysis_csv = _infer_distribution_from_analysis_csv(summary_path)
        if from_analysis_csv != "unknown":
            return from_analysis_csv

    return "unknown"


def load_distribution_summaries(json_folder: Path) -> Dict[str,Dict]:
    json_files = sorted(json_folder.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found in folder: {json_folder}")
    summaries: Dict[str,Dict] = {}
    for json_file in json_files:
        with open(json_file,"r",encoding="utf-8") as f:
            summary = json.load(f)
        distribution = get_distribution_label(summary, json_file)
        summaries[distribution] = summary
    required = {"beta","triangular","lognormal"}
    missing = required - set(summaries.keys())
    if missing:
        raise ValueError(
            "Folder must include summaries for beta, triangular, and lognormal. "
            f"Missing: {', '.join(sorted(missing))}"
        )
    return summaries


def extract_line_data(summary: Dict, error_type: str) -> tuple:
    block = summary[error_type]
    cross_method_values = [block["percentile_cross_method_final"][p]["value"] for p in PERCENTILE_ORDER]
    by_method = {
        method: [block["percentile_by_method_final"][p][method]["value"] for p in PERCENTILE_ORDER]
        for method in METHODS
    }
    return cross_method_values, by_method


def extract_bar_data(summary: Dict, error_type: str) -> Dict[str,float]:
    block = summary[error_type]["method_final"]
    return {method: block[method]["value"] for method in METHODS}


def calculate_shared_ylim(curves_by_method: Dict, error_type: str) -> Tuple[float,float]:
    all_values: List[float] = []
    for method_curves in curves_by_method.values():
        for curve in method_curves.values():
            all_values.extend(curve)
    y_min, y_max = min(all_values), max(all_values)
    span = max(abs(y_max - y_min), 1.0)
    pad = span * 0.12
    if error_type == "absolute":
        return 0.0, y_max + pad
    return y_min - pad, y_max + pad


def calculate_shared_ylim_from_values(values_by_method: Dict, error_type: str) -> Tuple[float,float]:
    all_values: List[float] = []
    for v in values_by_method.values():
        all_values.extend(v.values())
    y_min, y_max = min(all_values), max(all_values)
    span = max(abs(y_max - y_min), 1.0)
    pad = span * 0.12
    if error_type == "absolute":
        return 0.0, y_max + pad
    return y_min - pad, y_max + pad


def plot_combined_method_comparison(
    distribution_summaries: Dict[str,Dict],
    error_type: str,
    output_path: Path,
) -> None:
    x = np.arange(len(PERCENTILE_ORDER))
    distributions = ["beta","triangular","lognormal"]
    curves_by_method = {method: {} for method in METHODS}
    for method in METHODS:
        for dist in distributions:
            block = distribution_summaries[dist][error_type]["percentile_by_method_final"]
            curves_by_method[method][dist] = [block[p][method]["value"] for p in PERCENTILE_ORDER]
    y_bottom, y_top = calculate_shared_ylim(curves_by_method, error_type)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)
    for idx, method in enumerate(METHODS):
        ax = axes[idx]
        for dist in distributions:
            ax.plot(
                x, curves_by_method[method][dist],
                label=dist.capitalize(),
                color=DISTRIBUTION_COLORS[dist], linewidth=2.0,
                linestyle=DISTRIBUTION_LINE_STYLES[dist],
                marker=DISTRIBUTION_MARKERS[dist], markersize=4.2,
                markeredgecolor="black", markeredgewidth=0.3,
            )
        ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-", alpha=0.4)
        ax.set_ylim(y_bottom, y_top)
        ax.set_xticks(x)
        ax.set_xticklabels(PERCENTILE_LABELS, rotation=45, ha="right")
        ax.set_title(method.upper())
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.tick_params(axis="y", labelleft=True)
        if idx == 0:
            label = "Signed Percent Error (%)" if error_type == "signed" else "Absolute Percent Error (%)"
            ax.set_ylabel(label)
    for ax in axes:
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
        ax.set_xlabel("Percentile")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02), frameon=True)
    title = "Signed" if error_type == "signed" else "Absolute"
    fig.suptitle(f"Combined Distribution Comparison — {title} % Error by Method and Percentile", y=1.06)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_single_distribution(
    summary: Dict,
    distribution: str,
    error_type: str,
    output_path: Path,
) -> None:
    x = np.arange(len(PERCENTILE_ORDER))
    cross_method_values, by_method = extract_line_data(summary, error_type)
    all_values = list(cross_method_values)
    for v in by_method.values():
        all_values.extend(v)
    y_min, y_max = min(all_values), max(all_values)
    span = max(abs(y_max - y_min), 1.0)
    pad = span * 0.12
    y_bottom = 0.0 if error_type == "absolute" else y_min - pad
    y_top = y_max + pad

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    for method in METHODS:
        style = SINGLE_CURVE_STYLES[method]
        ax.plot(
            x, by_method[method], label=method.upper(),
            color=METHOD_COLORS[method], linewidth=2.0,
            linestyle=style["linestyle"], marker=style["marker"],
            markersize=4.5, markeredgecolor="black", markeredgewidth=0.3,
        )
    style = SINGLE_CURVE_STYLES["cross_method"]
    ax.plot(
        x, cross_method_values, label="Cross-Method Avg",
        color=METHOD_COLORS["cross_method"], linewidth=1.5,
        linestyle=style["linestyle"], marker=style["marker"],
        markersize=4.0, markeredgecolor="black", markeredgewidth=0.3, alpha=0.75,
    )
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-", alpha=0.4)
    ax.set_ylim(y_bottom, y_top)
    ax.set_xticks(x)
    ax.set_xticklabels(PERCENTILE_LABELS, rotation=45, ha="right")
    label = "Signed Percent Error (%)" if error_type == "signed" else "Absolute Percent Error (%)"
    ax.set_ylabel(label)
    ax.set_xlabel("Percentile")
    title = "Signed" if error_type == "signed" else "Absolute"
    ax.set_title(f"{distribution.capitalize()} Distribution — {title} % Error by Percentile")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_bar_single_distribution(
    summary: Dict,
    distribution: str,
    error_type: str,
    output_path: Path,
) -> None:
    values = extract_bar_data(summary, error_type)
    x = np.arange(len(METHODS))
    y_values = [values[m] for m in METHODS]

    y_min, y_max = min(y_values), max(y_values)
    span = max(abs(y_max - y_min), 1.0)
    pad = span * 0.12
    y_bottom = 0.0 if error_type == "absolute" else y_min - pad
    y_top = y_max + pad
    y_bottom, y_top = _expand_ylim_for_bar_labels(y_bottom, y_top)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    bars = ax.bar(
        x,
        y_values,
        color=[METHOD_COLORS[m] for m in METHODS],
        hatch=[METHOD_HATCHES[m] for m in METHODS],
        edgecolor="black",
        linewidth=0.6,
    )
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-", alpha=0.4)
    ax.set_ylim(y_bottom, y_top)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.set_xticks(x)
    ax.set_xticklabels([m.upper() for m in METHODS])
    label = "Signed Percent Error (%)" if error_type == "signed" else "Absolute Percent Error (%)"
    ax.set_ylabel(label)
    title = "Signed" if error_type == "signed" else "Absolute"
    ax.set_title(f"{distribution.capitalize()} Distribution — Method Final Mean {title} % Error")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    legend_handles = [
        Patch(facecolor=METHOD_COLORS[m], edgecolor="black", hatch=METHOD_HATCHES[m], label=m.upper())
        for m in METHODS
    ]
    ax.legend(handles=legend_handles, frameon=True)
    _add_bar_value_labels(ax, bars)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_bar_combined(
    distribution_summaries: Dict[str,Dict],
    error_type: str,
    output_path: Path,
) -> None:
    distributions = ["beta","triangular","lognormal"]
    values_by_dist: Dict[str,Dict[str,float]] = {}
    for dist in distributions:
        values_by_dist[dist] = extract_bar_data(distribution_summaries[dist], error_type)

    y_bottom, y_top = calculate_shared_ylim_from_values(values_by_dist, error_type)
    y_bottom, y_top = _expand_ylim_for_bar_labels(y_bottom, y_top)
    x = np.arange(len(METHODS))
    width = 0.25
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    all_bars = []
    for i, dist in enumerate(distributions):
        vals = [values_by_dist[dist][m] for m in METHODS]
        offset = (i - 1) * width
        bars = ax.bar(
            x + offset, vals, width,
            label=dist.capitalize(),
            color=DISTRIBUTION_COLORS[dist],
            hatch=DISTRIBUTION_HATCHES[dist],
            edgecolor="black", linewidth=0.6,
        )
        all_bars.extend(bars)
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="-", alpha=0.4)
    ax.set_ylim(y_bottom, y_top)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.set_xticks(x)
    ax.set_xticklabels([m.upper() for m in METHODS])
    label = "Signed Percent Error (%)" if error_type == "signed" else "Absolute Percent Error (%)"
    ax.set_ylabel(label)
    title = "Signed" if error_type == "signed" else "Absolute"
    ax.set_title(f"Method Final Mean {title} % Error by Distribution")
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    _add_bar_value_labels(ax, all_bars)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def run_error_graphics(
    input_path: Path,
    output_dir: Optional[Path] = None,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> Path:
    """
    Generate all error graphics from a JSON summary file or folder of JSON files.
    Returns the output directory.
    """
    input_path = Path(input_path)

    if input_path.is_dir():
        json_files = sorted(input_path.glob("*.json"))
        if not json_files:
            raise ValueError(f"No JSON files found in: {input_path}")
        is_folder = True
    elif input_path.suffix.lower() == ".json":
        json_files = [input_path]
        is_folder = False
    else:
        raise ValueError(f"Input must be a JSON file or a folder containing JSON files: {input_path}")

    if output_dir is None:
        output_dir = input_path.parent / "graphics" if is_folder else input_path.parent / "graphics"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_steps = len(json_files) * 4 + (4 if is_folder and len(json_files) >= 3 else 0)
    step = 0

    for json_file in json_files:
        if cancel_check and cancel_check():
            raise InterruptedError("Graphics cancelled by user.")
        with open(json_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
        distribution = get_distribution_label(summary, json_file)
        dist_dir = output_dir / distribution
        dist_dir.mkdir(parents=True, exist_ok=True)

        for error_type in ("signed", "absolute"):
            if cancel_check and cancel_check():
                raise InterruptedError("Graphics cancelled by user.")
            plot_single_distribution(summary, distribution, error_type, dist_dir / f"{error_type}_line.png")
            step += 1
            if progress_cb:
                progress_cb(step, total_steps, f"Line chart: {distribution}/{error_type}")

            if cancel_check and cancel_check():
                raise InterruptedError("Graphics cancelled by user.")
            plot_bar_single_distribution(summary, distribution, error_type, dist_dir / f"{error_type}_bar.png")
            step += 1
            if progress_cb:
                progress_cb(step, total_steps, f"Bar chart: {distribution}/{error_type}")

    # Combined plots (need all 3 distributions)
    if is_folder or len(json_files) >= 3:
        try:
            summaries = load_distribution_summaries(input_path if is_folder else input_path.parent)
            combined_dir = output_dir / "combined"
            combined_dir.mkdir(parents=True, exist_ok=True)
            for error_type in ("signed", "absolute"):
                if cancel_check and cancel_check():
                    raise InterruptedError("Graphics cancelled by user.")
                plot_combined_method_comparison(summaries, error_type, combined_dir / f"combined_line_{error_type}.png")
                step += 1
                if progress_cb:
                    progress_cb(step, total_steps, f"Combined line chart: {error_type}")

                if cancel_check and cancel_check():
                    raise InterruptedError("Graphics cancelled by user.")
                plot_bar_combined(summaries, error_type, combined_dir / f"combined_bar_{error_type}.png")
                step += 1
                if progress_cb:
                    progress_cb(step, total_steps, f"Combined bar chart: {error_type}")
        except ValueError:
            pass  # Not enough distributions for combined plots

    if progress_cb:
        progress_cb(total_steps, total_steps, "Done.")
    return output_dir
