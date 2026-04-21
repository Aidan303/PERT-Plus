"""
Monte Carlo simulation engine for project networks.
Adapted from: Simulator Code Correct Version/Simulator.py
(Original file not modified.)

Key changes from original:
- Import of calculate_complexity_measures now uses local engine package
- Removed interactive __main__ block
- Added progress_cb / cancel_check callbacks for UI integration
- Added run_batch_simulation() wrapper for batch folder processing
- seed parameter added to enable reproducible runs
"""
from __future__ import annotations

import glob
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist
from scipy.stats import norm
from scipy.stats import lognorm

from .complexity_measures import calculate_complexity_measures


# ── Histogram ─────────────────────────────────────────────────────────────────

def save_histogram(
    data,
    output_dir,
    filename="completion_time_histogram.png",
    pert_mean=None,
    pert_sd=None,
    bb2_alpha=None,
    bb2_beta=None,
    bb2_optimistic=None,
    bb2_pessimistic=None,
    lognormal_mu=None,
    lognormal_sigma=None,
    lognormal_optimistic=None,
    distribution_name=None,
    percentile=0.99,
):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if distribution_name:
        output_dir = os.path.join(output_dir, distribution_name)
        filename = filename.replace(".png", f"_({distribution_name}).png")

    os.makedirs(output_dir, exist_ok=True)
    counts, bin_edges = np.histogram(data, bins=100)
    bin_width = bin_edges[1] - bin_edges[0]
    scale = len(data) * bin_width

    data_min = float(np.min(data))
    data_max = float(np.max(data))
    x_min = data_min
    x_max = data_max

    if (
        bb2_optimistic is not None
        and bb2_pessimistic is not None
        and bb2_pessimistic > bb2_optimistic
    ):
        x_min = min(x_min, float(bb2_optimistic))
        x_max = max(x_max, float(bb2_pessimistic))

    if (
        lognormal_mu is not None
        and lognormal_sigma is not None
        and lognormal_optimistic is not None
        and lognormal_sigma > 0
    ):
        lognorm_right = float(
            lognorm.ppf(percentile, s=lognormal_sigma, scale=np.exp(lognormal_mu), loc=lognormal_optimistic)
        )
        if np.isfinite(lognorm_right):
            x_min = min(x_min, float(lognormal_optimistic))
            x_max = max(x_max, lognorm_right)

    x_span = x_max - x_min
    x_padding = 0.08 * x_span if x_span > 0 else 1.0
    x_min -= x_padding
    x_max += x_padding

    title = "Monte Carlo Simulation: Project Completion Time Distribution"
    if distribution_name:
        title = f"Monte Carlo Simulation ({distribution_name.capitalize()}): Project Completion Time Distribution"

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(data, bins=100, color="black", edgecolor="black", label="Simulation")
    x = np.linspace(0, x_max + ((bb2_pessimistic or 0) + (bb2_optimistic or 0)), 500)

    if pert_mean is not None and pert_sd is not None and pert_sd > 0:
        ax.plot(x, norm.pdf(x, pert_mean, pert_sd) * scale, color="red", linewidth=2, label="PERT")

    if (
        bb2_alpha is not None
        and bb2_beta is not None
        and bb2_optimistic is not None
        and bb2_pessimistic is not None
        and bb2_pessimistic > bb2_optimistic
    ):
        ax.plot(
            x,
            beta_dist.pdf(x, bb2_alpha, bb2_beta, loc=bb2_optimistic, scale=bb2_pessimistic - bb2_optimistic) * scale,
            color="green",
            linewidth=2,
            label="BB/2 (Beta)",
        )

    if (
        lognormal_mu is not None
        and lognormal_sigma is not None
        and lognormal_optimistic is not None
        and lognormal_sigma > 0
    ):
        shifted = x - lognormal_optimistic
        valid = shifted > 0
        y = np.zeros_like(x)
        y[valid] = lognorm.pdf(shifted[valid], s=lognormal_sigma, scale=np.exp(lognormal_mu)) * scale
        ax.plot(x, y, color="blue", linewidth=2, label="Lognormal")

    ax.set_title(title)
    ax.set_xlabel("Project Completion Time")
    ax.set_ylabel("Frequency")
    ax.set_xlim(x_min, x_max)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()

    hist_path = os.path.join(output_dir, filename)
    plt.savefig(hist_path)
    plt.close()
    return hist_path


# ── Activity Samplers ──────────────────────────────────────────────────────────

def sample_beta_activities(most_likely_list, optimistic_list, pessimistic_list, num_simulations):
    activity_samples = []
    for m, o, p in zip(most_likely_list, optimistic_list, pessimistic_list):
        if m is None or o is None or p is None:
            activity_samples.append(np.zeros(num_simulations))
            continue
        mean = (o + 4 * m + p) / 6
        sd = (p - o) / 6
        if p > o and sd > 0:
            alpha = ((mean - o) / (p - o)) * (((mean - o) * (p - mean) / (sd**2)) - 1)
            beta_param = ((p - mean) / (p - o)) * (((mean - o) * (p - mean) / (sd**2)) - 1)
        else:
            alpha, beta_param = 2, 2
        if alpha <= 0 or beta_param <= 0 or np.isnan(alpha) or np.isnan(beta_param):
            alpha, beta_param = 2, 2
        samples = np.random.beta(alpha, beta_param, num_simulations)
        samples = o + samples * (p - o)
        activity_samples.append(samples)
    return activity_samples


def sample_lognormal_activities(most_likely_list, optimistic_list, pessimistic_list, num_simulations):
    activity_samples = []
    zscore = norm.ppf(0.99)
    for m, o, p in zip(most_likely_list, optimistic_list, pessimistic_list):
        if m is None or o is None or p is None or p <= o or m <= o:
            activity_samples.append(np.zeros(num_simulations))
            continue
        try:
            ln_p_o = np.log(p - o)
            ln_m_o = np.log(m - o)
            sd = (-zscore + np.sqrt(zscore**2 - 4 * (ln_m_o - ln_p_o))) / 2
            mu = ln_p_o - zscore * sd
            samples = np.random.lognormal(mu, sd, num_simulations) + o
            activity_samples.append(samples)
        except Exception:
            activity_samples.append(np.zeros(num_simulations))
    return activity_samples


def sample_triangular_activities(most_likely_list, optimistic_list, pessimistic_list, num_simulations):
    activity_samples = []
    for m, o, p in zip(most_likely_list, optimistic_list, pessimistic_list):
        if m is None or o is None or p is None:
            activity_samples.append(np.zeros(num_simulations))
            continue
        activity_samples.append(np.random.triangular(o, m, p, num_simulations))
    return activity_samples


# ── Path Finding & RCP Parser ──────────────────────────────────────────────────

def find_all_paths(activities, start_idx=0, end_idx=None):
    if end_idx is None:
        end_idx = len(activities) - 1
    paths = []
    stack = [(start_idx, [start_idx])]
    while stack:
        current, path = stack.pop()
        if current == end_idx:
            paths.append(path)
        else:
            for succ in activities[current]["successors"]:
                if succ not in path:
                    stack.append((succ - 1, path + [succ - 1]))
    return paths


def parse_rcp_file(rcp_path: str) -> list[dict]:
    with open(rcp_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    num_activities = int(lines[0].split()[0])
    activities = []
    for row in lines[2:]:
        parts = row.split()
        duration = int(parts[0])
        num_successors = int(parts[5])
        successors = [int(x) for x in parts[6 : 6 + num_successors]] if num_successors > 0 else []
        activities.append({"duration": duration, "successors": successors})
    return activities


# ── Core Simulation ────────────────────────────────────────────────────────────

def run_monte_carlo_simulator(
    rcp_path: str,
    optimistic_scalar: float,
    pessimistic_scalar: float,
    distribution_type: str,
    num_simulations: int,
    output_dir: Optional[str] = None,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
):
    activities = parse_rcp_file(rcp_path)
    all_paths = find_all_paths(activities)

    for activity in activities:
        ml = activity["duration"]
        activity["optimistic"] = ml * optimistic_scalar
        activity["pessimistic"] = ml * pessimistic_scalar

    most_likely_list, optimistic_list, pessimistic_list = [], [], []
    for idx, activity in enumerate(activities):
        if idx == 0 or idx == len(activities) - 1:
            most_likely_list.append(None)
            optimistic_list.append(None)
            pessimistic_list.append(None)
        else:
            most_likely_list.append(activity["duration"])
            optimistic_list.append(activity["optimistic"])
            pessimistic_list.append(activity["pessimistic"])

    if distribution_type == "beta":
        activity_samples = sample_beta_activities(most_likely_list, optimistic_list, pessimistic_list, num_simulations)
    elif distribution_type == "lognormal":
        activity_samples = sample_lognormal_activities(most_likely_list, optimistic_list, pessimistic_list, num_simulations)
    elif distribution_type == "triangular":
        activity_samples = sample_triangular_activities(most_likely_list, optimistic_list, pessimistic_list, num_simulations)
    else:
        raise ValueError(f"Unsupported distribution type: {distribution_type}")

    max_durations = []
    chunk = max(1, num_simulations // 20)
    for sim_idx in range(num_simulations):
        if cancel_check and cancel_check():
            raise InterruptedError("Simulation cancelled by user.")
        path_durations = []
        for path in all_paths:
            activity_indices = path[1:-1] if len(path) > 2 else []
            duration = sum(activity_samples[idx][sim_idx] for idx in activity_indices)
            path_durations.append(duration)
        max_durations.append(max(path_durations) if path_durations else 0)
        if progress_cb and sim_idx % chunk == 0:
            progress_cb(sim_idx + 1, num_simulations, f"Simulating run {sim_idx + 1}/{num_simulations}")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    return max_durations, all_paths, activities


# ── Deterministic Path Calculations ───────────────────────────────────────────

def critical_path_duration(duration_list, all_paths):
    path_durations = []
    for path in all_paths:
        activity_indices = path[1:-1] if len(path) > 2 else []
        duration = sum(duration_list[idx] for idx in activity_indices if duration_list[idx] is not None)
        path_durations.append(duration)
    return max(path_durations) if path_durations else 0


PERCENTILE_LEVELS = [1, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99, 99.9]


def percentile_label(percentile):
    return str(percentile).replace(".", "_")


def add_prefixed_percentiles(metrics, prefix, percentile_values):
    for percentile, value in percentile_values.items():
        metrics[f"{prefix}_p{percentile_label(percentile)}"] = value


def beta_triplet_percentiles(optimistic, most_likely, pessimistic, percentiles, shape_weight=4):
    if (
        optimistic is None
        or most_likely is None
        or pessimistic is None
        or pessimistic <= optimistic
        or most_likely < optimistic
        or most_likely > pessimistic
    ):
        return {p: -1 for p in percentiles}, None, None

    scale = pessimistic - optimistic
    alpha = 1 + shape_weight * (most_likely - optimistic) / scale
    beta_param = 1 + shape_weight * (pessimistic - most_likely) / scale
    values = {
        p: float(beta_dist.ppf(p / 100.0, alpha, beta_param, loc=optimistic, scale=scale))
        for p in percentiles
    }
    return values, alpha, beta_param


# ── Simulation Metrics ─────────────────────────────────────────────────────────

def get_simulation_metrics(
    rcp_path: str,
    optimistic_scalar: float,
    pessimistic_scalar: float,
    distribution_type: str,
    num_simulations: int,
    complexity_func=None,
    percentile: float = 0.99,
    distribution_name: Optional[str] = None,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    if seed is not None:
        np.random.seed(seed)

    simulation_start_time = time.perf_counter()
    max_durations, all_paths, activities = run_monte_carlo_simulator(
        rcp_path,
        optimistic_scalar,
        pessimistic_scalar,
        distribution_type,
        num_simulations,
        output_dir=None,
        progress_cb=progress_cb,
        cancel_check=cancel_check,
    )
    simulation_runtime_seconds = time.perf_counter() - simulation_start_time

    max_durations = np.array(max_durations)

    most_likely_list, optimistic_list, pessimistic_list = [], [], []
    for idx, activity in enumerate(activities):
        if idx == 0 or idx == len(activities) - 1:
            most_likely_list.append(None)
            optimistic_list.append(None)
            pessimistic_list.append(None)
        else:
            most_likely_list.append(activity["duration"])
            optimistic_list.append(activity["optimistic"])
            pessimistic_list.append(activity["pessimistic"])

    pert_durations = [
        (o + 4 * m + p) / 6 if m is not None else 0
        for m, o, p in zip(most_likely_list, optimistic_list, pessimistic_list)
    ]
    pert_critical = critical_path_duration(pert_durations, all_paths)

    alpha_val = None
    beta_val = None
    ln_mu = None
    ln_sigma = None

    path_durations = []
    path_optimistics = []
    path_pessimistics = []
    for path in all_paths:
        activity_indices = path[1:-1] if len(path) > 2 else []
        path_durations.append(sum(most_likely_list[i] or 0 for i in activity_indices))
        path_optimistics.append(sum(optimistic_list[i] or 0 for i in activity_indices))
        path_pessimistics.append(sum(pessimistic_list[i] or 0 for i in activity_indices))

    if path_durations:
        crit_idx = int(np.argmax(path_durations))
        crit_most_likely = path_durations[crit_idx]
        crit_optimistic = max(path_optimistics)
        crit_pessimistic = max(path_pessimistics)

        # Lognormal
        zscore = np.float32(norm.ppf(np.float32(percentile)))
        try:
            ln_p_o = np.log(crit_pessimistic - crit_optimistic)
            ln_m_o = np.log(crit_most_likely - crit_optimistic)
            sigma = (-zscore + np.sqrt(zscore**2 + 4 * (ln_p_o - ln_m_o))) / 2
            mu = ln_p_o - zscore * sigma
            ln_mu = mu
            ln_sigma = sigma
            lognormal_critical_mean = float(np.exp(mu + (sigma**2) / 2) + crit_optimistic)
            lognormal_critical_sd = float(np.sqrt((np.exp(sigma**2) - 1) * np.exp(2 * mu + sigma**2)))
            lognormal_critical_p99 = float(np.exp(mu + sigma * norm.ppf(np.float32(0.99))) + crit_optimistic)
            lognormal_percentiles = {
                p: float(np.exp(mu + sigma * norm.ppf(np.float32(p) / 100.0)) + crit_optimistic)
                for p in PERCENTILE_LEVELS
            }
        except Exception:
            lognormal_critical_mean = lognormal_critical_sd = lognormal_critical_p99 = -1
            ln_mu = ln_sigma = None
            lognormal_percentiles = {p: -1 for p in PERCENTILE_LEVELS}

        # BB/2
        mu_bb2 = (crit_optimistic + 4 * crit_most_likely + crit_pessimistic) / 6
        sigma_bb2 = ((crit_pessimistic - crit_optimistic) / 6) / 2
        if crit_pessimistic > crit_optimistic and sigma_bb2 > 0:
            alpha_val = ((mu_bb2 - crit_optimistic) / (crit_pessimistic - crit_optimistic)) * (
                ((mu_bb2 - crit_optimistic) * (crit_pessimistic - mu_bb2) / (sigma_bb2**2)) - 1
            )
            beta_val = ((crit_pessimistic - mu_bb2) / (crit_pessimistic - crit_optimistic)) * (
                ((mu_bb2 - crit_optimistic) * (crit_pessimistic - mu_bb2) / (sigma_bb2**2)) - 1
            )
        else:
            alpha_val = beta_val = 2

        if alpha_val <= 0 or beta_val <= 0 or np.isnan(alpha_val) or np.isnan(beta_val):
            alpha_val = beta_val = 2

        bb2_critical_mean = mu_bb2
        bb2_critical_sd = sigma_bb2
        bb2_critical_p99 = float(
            beta_dist.ppf(0.99, alpha_val, beta_val, loc=crit_optimistic, scale=crit_pessimistic - crit_optimistic)
        )
        bb2_percentiles = {
            p: float(
                beta_dist.ppf(p / 100.0, alpha_val, beta_val, loc=crit_optimistic, scale=crit_pessimistic - crit_optimistic)
            )
            for p in PERCENTILE_LEVELS
        }
    else:
        bb2_critical_mean = bb2_critical_sd = bb2_critical_p99 = -1
        lognormal_critical_mean = lognormal_critical_sd = lognormal_critical_p99 = -1
        bb2_percentiles = {p: -1 for p in PERCENTILE_LEVELS}
        lognormal_percentiles = {p: -1 for p in PERCENTILE_LEVELS}
        crit_optimistic = crit_pessimistic = crit_most_likely = 0

    network_optimistic = critical_path_duration(optimistic_list, all_paths)
    network_pessimistic = critical_path_duration(pessimistic_list, all_paths)
    network_most_likely = critical_path_duration(most_likely_list, all_paths)

    crit_path = []
    max_d = -1
    for path in all_paths:
        idxs = path[1:-1] if len(path) > 2 else []
        d = sum(pert_durations[i] for i in idxs)
        if d > max_d:
            max_d = d
            crit_path = idxs

    pert_variance = 0.0
    for i in crit_path:
        o, p = optimistic_list[i], pessimistic_list[i]
        if o is not None and p is not None:
            pert_variance += ((p - o) / 6) ** 2
    pert_sd = float(np.sqrt(pert_variance))

    pert_percentiles, _, _ = beta_triplet_percentiles(
        network_optimistic, network_most_likely, network_pessimistic, PERCENTILE_LEVELS, shape_weight=4
    )
    sim_percentiles = {p: float(np.percentile(max_durations, p)) for p in PERCENTILE_LEVELS}

    parent_folder = os.path.basename(os.path.dirname(rcp_path))
    file_stem = os.path.splitext(os.path.basename(rcp_path))[0]
    source_name = f"{parent_folder}_{file_stem}"

    metrics: dict = {
        "source_file": source_name,
        "distribution": distribution_type,
        "num_simulations": num_simulations,
        "network_optimistic": network_optimistic,
        "network_pessimistic": network_pessimistic,
        "network_most_likely": network_most_likely,
        "pert_critical": pert_critical,
        "pert_sd": pert_sd,
        "bb2_critical_mean": bb2_critical_mean,
        "bb2_critical_sd": bb2_critical_sd,
        "bb2_critical_p99": bb2_critical_p99,
        "bb2_critical_p10": bb2_percentiles[10],
        "bb2_critical_p25": bb2_percentiles[25],
        "lognormal_critical_mean": lognormal_critical_mean,
        "lognormal_critical_sd": lognormal_critical_sd,
        "lognormal_critical_p99": lognormal_critical_p99,
        "lognormal_critical_p10": lognormal_percentiles[10],
        "lognormal_critical_p25": lognormal_percentiles[25],
        "sim_mean": float(np.mean(max_durations)),
        "sim_std": float(np.std(max_durations)),
        "sim_min": float(np.min(max_durations)),
        "sim_p10": sim_percentiles[10],
        "sim_p25": sim_percentiles[25],
        "sim_max": float(np.max(max_durations)),
        "sim_p50": float(np.percentile(max_durations, 50)),
        "sim_p90": float(np.percentile(max_durations, 90)),
        "sim_p95": float(np.percentile(max_durations, 95)),
        "sim_p99": float(np.percentile(max_durations, 99)),
    }

    add_prefixed_percentiles(metrics, "pert", pert_percentiles)
    add_prefixed_percentiles(metrics, "bb2", bb2_percentiles)
    add_prefixed_percentiles(metrics, "lognormal", lognormal_percentiles)
    add_prefixed_percentiles(metrics, "sim", sim_percentiles)

    try:
        sp, tf, ad, la = calculate_complexity_measures(rcp_path)
        metrics["SP"] = sp
        metrics["TF"] = tf
        metrics["AD"] = ad
        metrics["LA"] = la
    except Exception as e:
        metrics["SP"] = metrics["TF"] = metrics["AD"] = metrics["LA"] = None

    metrics["number_of_nodes"] = len(activities) - 2
    metrics["is_beta"] = 1 if distribution_type == "beta" else 0
    metrics["is_lognormal"] = 1 if distribution_type == "lognormal" else 0
    metrics["simulation_runtime_seconds"] = simulation_runtime_seconds

    return pd.DataFrame([metrics])


# ── RCP Discovery ──────────────────────────────────────────────────────────────

def find_rcp_files(folder: str) -> list[str]:
    return [y for x in os.walk(folder) for y in glob.glob(os.path.join(x[0], "*.rcp"))]


# ── Batch Simulation ───────────────────────────────────────────────────────────

def run_batch_simulation(
    rcp_files: list[str],
    optimistic_scalar: float,
    pessimistic_scalar: float,
    distribution_types: list[str],
    num_simulations: int,
    output_dir: str,
    output_filename: str = "batch_results.csv",
    percentile: float = 0.999,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
    seed: Optional[int] = None,
    parallel: bool = False,
    max_workers: int = 4,
) -> Path:
    """
    Process multiple RCP files across multiple distribution types.
    Returns path to the saved master CSV.
    """
    jobs = [(rcp, dist) for dist in distribution_types for rcp in rcp_files]
    total = len(jobs)
    results = []
    completed = 0

    def _run_one(rcp_path: str, dist: str, job_seed: Optional[int]) -> pd.DataFrame:
        return get_simulation_metrics(
            rcp_path=rcp_path,
            optimistic_scalar=optimistic_scalar,
            pessimistic_scalar=pessimistic_scalar,
            distribution_type=dist,
            num_simulations=num_simulations,
            percentile=percentile,
            distribution_name=dist,
            cancel_check=cancel_check,
            seed=job_seed,
        )

    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(_run_one, rcp, dist, seed): (rcp, dist)
                for rcp, dist in jobs
            }
            for future in as_completed(future_map):
                if cancel_check and cancel_check():
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise InterruptedError("Batch cancelled by user.")
                rcp, dist = future_map[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    if progress_cb:
                        progress_cb(completed, total, f"ERROR {os.path.basename(rcp)} ({dist}): {e}")
                completed += 1
                if progress_cb:
                    progress_cb(completed, total, f"[{completed}/{total}] {os.path.basename(rcp)} ({dist})")
    else:
        for idx, (rcp, dist) in enumerate(jobs):
            if cancel_check and cancel_check():
                raise InterruptedError("Batch cancelled by user.")
            try:
                df = _run_one(rcp, dist, seed)
                results.append(df)
            except InterruptedError:
                raise
            except Exception as e:
                if progress_cb:
                    progress_cb(idx + 1, total, f"ERROR {os.path.basename(rcp)} ({dist}): {e}")
            completed = idx + 1
            if progress_cb:
                progress_cb(completed, total, f"[{completed}/{total}] {os.path.basename(rcp)} ({dist})")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    if not output_filename.endswith(".csv"):
        output_filename += ".csv"
    save_path = out_path / output_filename

    if results:
        all_df = pd.concat(results, ignore_index=True)
        all_df.to_csv(save_path, index=False)

    return save_path
