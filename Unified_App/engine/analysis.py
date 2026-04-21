"""
Batch percent-error analysis of simulator CSV outputs.
Adapted from: Simulator Code Correct Version/Analysis.py
(Original file not modified.)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


METHODS = ["pert", "bb2", "lognormal"]
SIM_PREFIX = "sim"
PERCENTILES = [
    "p1", "p10", "p20", "p25", "p30", "p40", "p50",
    "p60", "p70", "p75", "p80", "p90", "p95", "p99", "p99_9",
]
ERROR_TYPES = ["signed", "absolute"]


def method_percentile_col(method, percentile):
    return f"{method}_{percentile}"


def sim_percentile_col(percentile):
    return f"{SIM_PREFIX}_{percentile}"


def raw_error_col(method, percentile, error_type):
    return f"error_{error_type}_{method}_{percentile}"


def row_method_mean_col(method, error_type):
    return f"row_mean_{error_type}_{method}"


def row_percentile_cross_method_mean_col(percentile, error_type):
    return f"row_mean_{error_type}_cross_method_{percentile}"


def validate_schema(df: pd.DataFrame) -> None:
    missing_cols: List[str] = []
    for percentile in PERCENTILES:
        sim_col = sim_percentile_col(percentile)
        if sim_col not in df.columns:
            missing_cols.append(sim_col)
        for method in METHODS:
            col = method_percentile_col(method, percentile)
            if col not in df.columns:
                missing_cols.append(col)
    if missing_cols:
        missing_display = "\n".join(f"- {name}" for name in missing_cols)
        raise ValueError(
            "Input file is missing required percentile columns:\n"
            f"{missing_display}\n"
            "Expected fixed percentile set: " + ", ".join(PERCENTILES)
        )


def compute_raw_errors(df: pd.DataFrame) -> pd.DataFrame:
    error_data: Dict[str, pd.Series] = {}
    for method in METHODS:
        for percentile in PERCENTILES:
            method_col = method_percentile_col(method, percentile)
            sim_col = sim_percentile_col(percentile)
            method_vals = pd.to_numeric(df[method_col], errors="coerce")
            sim_vals = pd.to_numeric(df[sim_col], errors="coerce")
            valid_denominator = sim_vals != 0
            signed = pd.Series(np.nan, index=df.index, dtype=float)
            absolute = pd.Series(np.nan, index=df.index, dtype=float)
            signed.loc[valid_denominator] = (
                (method_vals.loc[valid_denominator] - sim_vals.loc[valid_denominator])
                / sim_vals.loc[valid_denominator]
            ) * 100.0
            absolute.loc[valid_denominator] = signed.loc[valid_denominator].abs()
            error_data[raw_error_col(method, percentile, "signed")] = signed
            error_data[raw_error_col(method, percentile, "absolute")] = absolute
    return pd.DataFrame(error_data)


def compute_row_method_means(raw_errors: pd.DataFrame) -> pd.DataFrame:
    out: Dict[str, pd.Series] = {}
    for method in METHODS:
        for error_type in ERROR_TYPES:
            cols = [raw_error_col(method, p, error_type) for p in PERCENTILES]
            out[row_method_mean_col(method, error_type)] = raw_errors[cols].mean(axis=1, skipna=True)
    return pd.DataFrame(out)


def compute_row_percentile_cross_method_means(raw_errors: pd.DataFrame) -> pd.DataFrame:
    out: Dict[str, pd.Series] = {}
    for percentile in PERCENTILES:
        for error_type in ERROR_TYPES:
            cols = [raw_error_col(method, percentile, error_type) for method in METHODS]
            out[row_percentile_cross_method_mean_col(percentile, error_type)] = raw_errors[cols].mean(axis=1, skipna=True)
    return pd.DataFrame(out)


def aggregate_method_final(row_method_means: pd.DataFrame) -> pd.DataFrame:
    records = []
    for error_type in ERROR_TYPES:
        for method in METHODS:
            col = row_method_mean_col(method, error_type)
            series = row_method_means[col]
            records.append({
                "record_type": "aggregate",
                "aggregate_scope": "method_final",
                "error_type": error_type,
                "method": method,
                "percentile": np.nan,
                "value": float(series.mean(skipna=True)),
                "n_contributing_rows": int(series.notna().sum()),
            })
    return pd.DataFrame(records)


def aggregate_percentile_cross_method_final(row_percentile_means: pd.DataFrame) -> pd.DataFrame:
    records = []
    for error_type in ERROR_TYPES:
        for percentile in PERCENTILES:
            col = row_percentile_cross_method_mean_col(percentile, error_type)
            series = row_percentile_means[col]
            records.append({
                "record_type": "aggregate",
                "aggregate_scope": "percentile_cross_method_final",
                "error_type": error_type,
                "method": "cross_method",
                "percentile": percentile,
                "value": float(series.mean(skipna=True)),
                "n_contributing_rows": int(series.notna().sum()),
            })
    return pd.DataFrame(records)


def aggregate_percentile_by_method_final(raw_errors: pd.DataFrame) -> pd.DataFrame:
    records = []
    for error_type in ERROR_TYPES:
        for percentile in PERCENTILES:
            for method in METHODS:
                col = raw_error_col(method, percentile, error_type)
                series = raw_errors[col]
                records.append({
                    "record_type": "aggregate",
                    "aggregate_scope": "percentile_by_method_final",
                    "error_type": error_type,
                    "method": method,
                    "percentile": percentile,
                    "value": float(series.mean(skipna=True)),
                    "n_contributing_rows": int(series.notna().sum()),
                })
    return pd.DataFrame(records)


def build_summary_json(
    input_csv: Path,
    df_row_level: pd.DataFrame,
    method_final_df: pd.DataFrame,
    percentile_cross_method_final_df: pd.DataFrame,
    percentile_by_method_final_df: pd.DataFrame,
) -> Dict:
    distribution_value = "unknown"
    if "distribution" in df_row_level.columns:
        unique_distributions = [
            str(v).strip().lower()
            for v in df_row_level["distribution"].dropna().unique().tolist()
            if str(v).strip()
        ]
        if len(unique_distributions) == 1:
            distribution_value = unique_distributions[0]
        elif len(unique_distributions) > 1:
            distribution_value = "mixed"

    summary: Dict = {
        "metadata": {
            "analysis_version": "1.0.0",
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "input_csv": str(input_csv),
            "distribution": distribution_value,
            "row_count": int(len(df_row_level)),
            "methods": METHODS,
            "percentiles": PERCENTILES,
        },
        "signed": {"method_final": {}, "percentile_cross_method_final": {}, "percentile_by_method_final": {}},
        "absolute": {"method_final": {}, "percentile_cross_method_final": {}, "percentile_by_method_final": {}},
    }
    for error_type in ERROR_TYPES:
        subset_method = method_final_df[method_final_df["error_type"] == error_type]
        subset_cross = percentile_cross_method_final_df[percentile_cross_method_final_df["error_type"] == error_type]
        subset_by_method = percentile_by_method_final_df[percentile_by_method_final_df["error_type"] == error_type]

        summary[error_type]["method_final"] = {
            row["method"]: {"value": row["value"], "n_contributing_rows": int(row["n_contributing_rows"])}
            for _, row in subset_method.iterrows()
        }
        summary[error_type]["percentile_cross_method_final"] = {
            row["percentile"]: {"value": row["value"], "n_contributing_rows": int(row["n_contributing_rows"])}
            for _, row in subset_cross.iterrows()
        }

        by_method_payload: Dict = {}
        for _, row in subset_by_method.iterrows():
            percentile = row["percentile"]
            method = row["method"]
            if percentile not in by_method_payload:
                by_method_payload[percentile] = {}
            by_method_payload[percentile][method] = {
                "value": row["value"],
                "n_contributing_rows": int(row["n_contributing_rows"]),
            }
        summary[error_type]["percentile_by_method_final"] = by_method_payload
    return summary


def run_analysis(
    input_csv: Path | str,
    output_dir: Path | str,
    progress_cb: Optional[Callable] = None,
) -> Tuple[Path, Path]:
    """Analyze a single batch CSV. Returns (csv_out, json_out)."""
    input_csv = Path(input_csv)
    output_dir = Path(output_dir)

    if progress_cb:
        progress_cb(0, 4, "Loading CSV...")
    df = pd.read_csv(input_csv)
    validate_schema(df)

    if progress_cb:
        progress_cb(1, 4, "Computing errors...")
    raw_errors = compute_raw_errors(df)
    row_method_means = compute_row_method_means(raw_errors)
    row_percentile_means = compute_row_percentile_cross_method_means(raw_errors)

    if progress_cb:
        progress_cb(2, 4, "Aggregating...")
    row_level = pd.concat([df, raw_errors, row_method_means, row_percentile_means], axis=1)
    row_level.insert(0, "record_type", "row")

    method_final_df = aggregate_method_final(row_method_means)
    percentile_cross_method_final_df = aggregate_percentile_cross_method_final(row_percentile_means)
    percentile_by_method_final_df = aggregate_percentile_by_method_final(raw_errors)
    aggregates = pd.concat(
        [method_final_df, percentile_cross_method_final_df, percentile_by_method_final_df],
        axis=0, ignore_index=True,
    )
    final_csv = pd.concat([row_level, aggregates], axis=0, ignore_index=True, sort=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_csv.stem
    csv_out = output_dir / f"{stem}_analysis_results.csv"
    json_out = output_dir / f"{stem}_analysis_summary.json"

    if progress_cb:
        progress_cb(3, 4, "Saving outputs...")

    final_csv.to_csv(csv_out, index=False)
    summary = build_summary_json(
        input_csv=input_csv,
        df_row_level=row_level,
        method_final_df=method_final_df,
        percentile_cross_method_final_df=percentile_cross_method_final_df,
        percentile_by_method_final_df=percentile_by_method_final_df,
    )
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if progress_cb:
        progress_cb(4, 4, "Done.")
    return csv_out, json_out


def find_batch_csvs(batch_folder: Path | str) -> List[Path]:
    batch_folder = Path(batch_folder)
    if not batch_folder.is_dir():
        raise ValueError(f"Input path is not a directory: {batch_folder}")
    csv_files = sorted(batch_folder.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in batch folder: {batch_folder}")
    return csv_files


def process_batch_folder(
    batch_folder: Path | str,
    output_dir: Path | str,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> List[Tuple[Path, Path]]:
    batch_folder = Path(batch_folder)
    output_dir = Path(output_dir)

    csv_files = find_batch_csvs(batch_folder)
    results: List[Tuple[Path, Path]] = []
    total = len(csv_files)
    for idx, csv_file in enumerate(csv_files):
        if cancel_check and cancel_check():
            raise InterruptedError("Analysis cancelled by user.")
        try:
            csv_out, json_out = run_analysis(input_csv=csv_file, output_dir=output_dir)
            results.append((csv_out, json_out))
            if progress_cb:
                progress_cb(idx + 1, total, f"[OK] {csv_file.name}")
        except Exception as e:
            if progress_cb:
                progress_cb(idx + 1, total, f"[ERR] {csv_file.name}: {e}")
    return results
