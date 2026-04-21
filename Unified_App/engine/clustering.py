"""
Hierarchical clustering analysis engine.
Adapted from: Simulator Code Correct Version/Clustering_Analysis.py
(Original file not modified.)
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text


METHODS: List[str] = ["pert", "bb2", "lognormal"]
COMPLEXITY_FEATURES: List[str] = ["SP", "LA", "AD", "TF"]
DUMMY_FEATURES: List[str] = ["is_beta", "is_lognormal"]


def percentile_sort_key(token: str) -> Tuple[int, str]:
    if token.startswith("p"):
        try:
            return (int(token[1:].replace("_", "")), token)
        except ValueError:
            pass
    return (10_000, token)


def extract_percentile_token(column_name: str, prefix: str) -> Optional[str]:
    pattern = re.compile(rf"^{re.escape(prefix)}_(p\d+(?:_\d+)?)$")
    match = pattern.match(column_name)
    return match.group(1) if match else None


def validate_base_schema(df: pd.DataFrame) -> None:
    required = ["source_file", *COMPLEXITY_FEATURES, *DUMMY_FEATURES]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Input CSV missing required columns:\n" + "\n".join(f"- {c}" for c in missing))


def build_percentile_column_map(columns: Sequence[str]) -> Tuple[List[str], Dict, Dict[str, str]]:
    method_maps: Dict[str, Dict[str, str]] = {m: {} for m in METHODS}
    for method in METHODS:
        for col in columns:
            token = extract_percentile_token(col, method)
            if token is not None:
                method_maps[method][token] = col
    sim_map: Dict[str, str] = {}
    for col in columns:
        token = extract_percentile_token(col, "sim")
        if token is not None:
            sim_map[token] = col
    common = set(sim_map.keys())
    for m in METHODS:
        common &= set(method_maps[m].keys())
    if not common:
        raise ValueError("No shared percentile columns found across sim/pert/bb2/lognormal.")
    ordered = sorted(common, key=percentile_sort_key)
    return ordered, method_maps, sim_map


def compute_row_mape_columns(
    df: pd.DataFrame,
    percentile_tokens: Sequence[str],
    method_maps: Dict,
    sim_map: Dict[str, str],
    eps: float,
) -> pd.DataFrame:
    out: Dict[str, pd.Series] = {}
    for method in METHODS:
        ape_cols = []
        for token in percentile_tokens:
            method_col = method_maps[method][token]
            sim_col = sim_map[token]
            method_vals = pd.to_numeric(df[method_col], errors="coerce")
            sim_vals = pd.to_numeric(df[sim_col], errors="coerce")
            valid = sim_vals.abs() > eps
            ape = pd.Series(np.nan, index=df.index, dtype=float)
            ape.loc[valid] = (
                (method_vals.loc[valid] - sim_vals.loc[valid]).abs() / sim_vals.loc[valid].abs()
            ) * 100.0
            ape_cols.append(ape)
        ape_matrix = pd.concat(ape_cols, axis=1)
        out[f"mape_{method}"] = ape_matrix.mean(axis=1, skipna=True)
    mape_df = pd.DataFrame(out)
    all_nan = mape_df.isna().all(axis=1)
    best = mape_df.idxmin(axis=1).str.replace("mape_", "", regex=False)
    best.loc[all_nan] = np.nan
    mape_df["best_method"] = best
    return mape_df


def normalize_distribution_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in DUMMY_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["is_beta"] = (out["is_beta"] >= 0.5).astype(int)
    out["is_lognormal"] = (out["is_lognormal"] >= 0.5).astype(int)
    out["distribution"] = np.where(
        out["is_beta"] == 1, "beta",
        np.where(out["is_lognormal"] == 1, "lognormal", "triangular"),
    )
    return out


def build_weighted_feature_matrix(
    df: pd.DataFrame,
    complexity_weight: float,
    dummy_weight: float,
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    feature_cols = [*COMPLEXITY_FEATURES, *DUMMY_FEATURES]
    features = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    features = features.fillna(features.median(numeric_only=True))
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(features)
    weights = np.array(
        [complexity_weight, complexity_weight, complexity_weight, complexity_weight, dummy_weight, dummy_weight],
        dtype=float,
    )
    return features, x_scaled * weights, weights


def choose_cluster_count(x_weighted: np.ndarray, k_min: int, k_max: int) -> Tuple[int, pd.DataFrame]:
    n_rows = x_weighted.shape[0]
    if n_rows < 3:
        raise ValueError("Need at least 3 rows for silhouette-based cluster selection.")
    upper = min(k_max, n_rows - 1)
    lower = max(2, k_min)
    if lower > upper:
        raise ValueError(f"Invalid cluster search range: lower={lower}, upper={upper}.")
    records, best_k, best_score = [], lower, -np.inf
    for k in range(lower, upper + 1):
        model = AgglomerativeClustering(n_clusters=k, linkage="ward")
        labels = model.fit_predict(x_weighted)
        if len(np.unique(labels)) < 2:
            continue
        score = float(silhouette_score(x_weighted, labels, metric="euclidean"))
        records.append({"k": k, "silhouette": score})
        if score > best_score:
            best_score, best_k = score, k
    if not records:
        raise ValueError("Unable to compute silhouette scores for any candidate k.")
    return best_k, pd.DataFrame.from_records(records).sort_values("k").reset_index(drop=True)


def build_cluster_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cluster_id, group in df.groupby("cluster_id", dropna=False):
        mapes = {m: float(group[f"mape_{m}"].mean(skipna=True)) for m in METHODS}
        sorted_m = sorted(mapes.items(), key=lambda x: x[1])
        winner = sorted_m[0][0]
        gap = float(sorted_m[1][1] - sorted_m[0][1]) if len(sorted_m) > 1 else np.nan
        record: Dict = {
            "cluster_id": int(cluster_id),
            "row_count": int(len(group)),
            "best_method_cluster_mean": winner,
            "best_vs_second_gap_mape_pct": gap,
            "share_beta": float((group["distribution"] == "beta").mean()),
            "share_lognormal": float((group["distribution"] == "lognormal").mean()),
            "share_triangular": float((group["distribution"] == "triangular").mean()),
        }
        for feature in COMPLEXITY_FEATURES:
            record[f"mean_{feature}"] = float(pd.to_numeric(group[feature], errors="coerce").mean(skipna=True))
        for method in METHODS:
            record[f"cluster_mean_mape_{method}"] = mapes[method]
        rows.append(record)
    return pd.DataFrame(rows).sort_values("cluster_id").reset_index(drop=True)


def train_choice_tree(
    df: pd.DataFrame,
    output_dir: Path,
    test_size: float,
    max_depth: int,
    random_state: int,
) -> Dict:
    model_features = [*COMPLEXITY_FEATURES, *DUMMY_FEATURES]
    model_df = df[[*model_features, "best_method"]].dropna(subset=["best_method"]).copy()
    if model_df.empty:
        return {"status": "skipped", "reason": "No rows with non-null best_method."}
    x = model_df[model_features].apply(pd.to_numeric, errors="coerce")
    x = x.fillna(x.median(numeric_only=True))
    y = model_df["best_method"].astype(str)
    class_counts = y.value_counts()

    if class_counts.min() < 2 or len(class_counts) < 2:
        clf = DecisionTreeClassifier(max_depth=max_depth, random_state=random_state, class_weight="balanced")
        clf.fit(x, y)
        rules = export_text(clf, feature_names=model_features)
        (output_dir / "choice_tree_rules.txt").write_text(rules, encoding="utf-8")
        importance_df = pd.DataFrame({"feature": model_features, "importance": clf.feature_importances_}).sort_values("importance", ascending=False)
        importance_df.to_csv(output_dir / "choice_tree_feature_importance.csv", index=False)
        return {"status": "trained_no_holdout", "class_counts": {k: int(v) for k, v in class_counts.items()}}

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=random_state, stratify=y)
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=random_state, class_weight="balanced")
    clf.fit(x_train, y_train)
    y_pred = clf.predict(x_test)
    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"actual_{c}" for c in labels], columns=[f"pred_{c}" for c in labels])
    cm_df.to_csv(output_dir / "choice_tree_confusion_matrix.csv", index=True)
    rules = export_text(clf, feature_names=model_features)
    (output_dir / "choice_tree_rules.txt").write_text(rules, encoding="utf-8")
    importance_df = pd.DataFrame({"feature": model_features, "importance": clf.feature_importances_}).sort_values("importance", ascending=False)
    importance_df.to_csv(output_dir / "choice_tree_feature_importance.csv", index=False)
    return {
        "status": "trained_holdout", "accuracy": acc, "macro_f1": macro_f1,
        "n_train": int(len(x_train)), "n_test": int(len(x_test)),
        "class_counts": {k: int(v) for k, v in class_counts.items()},
    }


def run_clustering(
    input_csv: Path,
    output_dir: Path,
    k_min: int = 2,
    k_max: int = 10,
    complexity_weight: float = 1.0,
    dummy_weight: float = 0.5,
    eps: float = 1e-9,
    test_size: float = 0.2,
    tree_max_depth: int = 4,
    random_state: int = 42,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> Path:
    """Run full clustering pipeline. Returns output_dir."""
    input_csv = Path(input_csv)
    output_dir = Path(output_dir)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if k_min < 2:
        raise ValueError("k_min must be >= 2")
    if k_max < k_min:
        raise ValueError("k_max must be >= k_min")

    output_dir.mkdir(parents=True, exist_ok=True)

    def _cb(step, total, msg):
        if progress_cb:
            progress_cb(step, total, msg)

    _cb(0, 6, "Loading CSV...")
    df = pd.read_csv(input_csv)
    validate_base_schema(df)
    df = normalize_distribution_columns(df)

    if cancel_check and cancel_check():
        raise InterruptedError("Clustering cancelled by user.")

    _cb(1, 6, "Building percentile columns...")
    percentile_tokens, method_maps, sim_map = build_percentile_column_map(list(df.columns))
    mape_df = compute_row_mape_columns(df, percentile_tokens, method_maps, sim_map, eps)
    df = pd.concat([df, mape_df], axis=1)

    if cancel_check and cancel_check():
        raise InterruptedError("Clustering cancelled by user.")

    _cb(2, 6, "Building feature matrix...")
    features, x_weighted, weights = build_weighted_feature_matrix(df, complexity_weight, dummy_weight)

    _cb(3, 6, f"Selecting cluster count (k={k_min}..{k_max})...")
    best_k, silhouette_df = choose_cluster_count(x_weighted, k_min, k_max)
    silhouette_df.to_csv(output_dir / "silhouette_scores.csv", index=False)

    if cancel_check and cancel_check():
        raise InterruptedError("Clustering cancelled by user.")

    _cb(4, 6, f"Clustering with k={best_k}...")
    model = AgglomerativeClustering(n_clusters=best_k, linkage="ward")
    df["cluster_id"] = model.fit_predict(x_weighted)

    row_out = output_dir / "network_clusters_row_level.csv"
    df.to_csv(row_out, index=False)
    cluster_summary_df = build_cluster_summary(df)
    cluster_summary_df.to_csv(output_dir / "cluster_summary.csv", index=False)

    if cancel_check and cancel_check():
        raise InterruptedError("Clustering cancelled by user.")

    _cb(5, 6, "Training choice tree...")
    tree_info = train_choice_tree(df, output_dir, test_size, tree_max_depth, random_state)

    summary = {
        "metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "input_csv": str(input_csv),
            "output_dir": str(output_dir),
        },
        "settings": {
            "methods": METHODS,
            "complexity_features": COMPLEXITY_FEATURES,
            "dummy_features": DUMMY_FEATURES,
            "percentiles_used": list(percentile_tokens),
            "feature_weights": {"complexity_weight": float(weights[0]), "dummy_weight": float(weights[-1])},
        },
        "clustering": {
            "selected_k": int(best_k),
            "silhouette_by_k": silhouette_df.to_dict(orient="records"),
        },
        "choice_tree": tree_info,
    }
    with open(output_dir / "clustering_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    _cb(6, 6, "Done.")
    return output_dir
