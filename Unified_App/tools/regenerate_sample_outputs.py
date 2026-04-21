from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

UNIFIED_ROOT = Path(__file__).resolve().parents[1]
if str(UNIFIED_ROOT) not in sys.path:
    sys.path.insert(0, str(UNIFIED_ROOT))

from engine import analysis
from engine import build_rcp
from engine import cluster_effects
from engine import cluster_graphics
from engine import clustering
from engine import complexity_measures
from engine import complexity_viz
from engine import error_graphics
from engine import path_generator
from engine import pca_analysis
from engine import simulator


def _require_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input for {label}: {path}")


def main() -> None:
    unified_root = UNIFIED_ROOT
    workspace_root = unified_root.parent

    sample_root = unified_root / "sample_outputs"
    legacy_root = unified_root / "test_outputs"

    if sample_root.exists():
        shutil.rmtree(sample_root)
    sample_root.mkdir(parents=True, exist_ok=True)

    # Keep packaging clean by removing the old test_outputs directory.
    if legacy_root.exists():
        shutil.rmtree(legacy_root)

    # Shared sample inputs
    rcp_ev1 = workspace_root / "MT" / "MT30" / "Set 1 SP" / "EV1.rcp"
    rcp_ev2 = workspace_root / "MT" / "MT30" / "Set 1 SP" / "EV2.rcp"
    rcp_ev3 = workspace_root / "MT" / "MT30" / "Set 1 SP" / "EV3.rcp"
    rcp_folder = workspace_root / "MT" / "MT30" / "Set 1 SP"

    clustering_csv = (
        workspace_root
        / "Simulator Code Correct Version"
        / "output"
        / "Output 10k Sims Divide by 2"
        / "Master_Output_File_CSV_Version.csv"
    )
    pca_csv = (
        workspace_root
        / "Simulator Code Correct Version"
        / "output"
        / "Output 10k Sims Divide by 2"
        / "PCA_analysis"
        / "pca_feature_matrix.csv"
    )
    build_rcp_xlsx = workspace_root / "DSLIB" / "Excel" / "C2011-10 Building a House.xlsx"

    for p, label in [
        (rcp_ev1, "simulation/path generator/complexity"),
        (rcp_ev2, "path generator/complexity"),
        (rcp_ev3, "path generator/complexity"),
        (rcp_folder, "batch simulation"),
        (clustering_csv, "clustering"),
        (pca_csv, "pca/complexity viz"),
        (build_rcp_xlsx, "build rcp"),
    ]:
        _require_exists(p, label)

    # 1) Monte Carlo simulation sample
    simulation_dir = sample_root / "simulation"
    simulation_dir.mkdir(parents=True, exist_ok=True)
    sim_csv = simulator.run_batch_simulation(
        rcp_files=[str(rcp_ev1)],
        optimistic_scalar=0.8,
        pessimistic_scalar=1.2,
        distribution_types=["triangular"],
        num_simulations=1000,
        output_dir=str(simulation_dir),
        output_filename="batch_results.csv",
        percentile=0.99,
        parallel=False,
        max_workers=1,
        seed=123,
    )

    # 2) Batch simulation sample
    batch_dir = sample_root / "batch_simulation"
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch_rcps = [str(p) for p in sorted(rcp_folder.glob("EV*.rcp"))[:4]]
    simulator.run_batch_simulation(
        rcp_files=batch_rcps,
        optimistic_scalar=0.8,
        pessimistic_scalar=1.2,
        distribution_types=["triangular"],
        num_simulations=600,
        output_dir=str(batch_dir),
        output_filename="batch_results.csv",
        percentile=0.99,
        parallel=True,
        max_workers=3,
        seed=123,
    )

    # 3) Percent-error analysis sample
    analysis_dir = sample_root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    analysis_csv, analysis_json = analysis.run_analysis(
        input_csv=sim_csv,
        output_dir=analysis_dir,
    )

    # 4) Error graphics sample
    err_graphics_dir = sample_root / "error_graphics"
    err_graphics_dir.mkdir(parents=True, exist_ok=True)
    error_graphics.run_error_graphics(input_path=analysis_json, output_dir=err_graphics_dir)

    # 5) Clustering sample
    clustering_dir = sample_root / "clustering"
    clustering_dir.mkdir(parents=True, exist_ok=True)
    clustering.run_clustering(
        input_csv=clustering_csv,
        output_dir=clustering_dir,
        k_min=2,
        k_max=8,
        complexity_weight=1.0,
        dummy_weight=0.5,
        test_size=0.2,
        tree_max_depth=4,
        random_state=42,
    )

    # 6) Cluster effect sizes sample
    cluster_effects_dir = sample_root / "cluster_effects"
    cluster_effects_dir.mkdir(parents=True, exist_ok=True)
    cluster_effects.run_effect_size_analysis(
        input_csv=clustering_dir / "network_clusters_row_level.csv",
        output_dir=cluster_effects_dir,
        n_bootstrap=1000,
        ci_level=0.95,
        seed=42,
        dpi=180,
    )

    # 7) Cluster graphics sample
    cluster_graphics_dir = sample_root / "cluster_graphics"
    cluster_graphics_dir.mkdir(parents=True, exist_ok=True)
    cluster_graphics.run_cluster_graphics(
        input_csv=clustering_dir / "cluster_summary.csv",
        output_dir=cluster_graphics_dir,
        dpi=180,
    )

    # 8) PCA sample
    pca_dir = sample_root / "pca"
    pca_dir.mkdir(parents=True, exist_ok=True)
    pca_analysis.run_pca(
        input_csv=pca_csv,
        output_dir=pca_dir,
        variance_threshold=0.95,
        dpi=180,
        random_state=42,
    )

    # 9) Complexity visualizer sample
    complexity_viz_dir = sample_root / "complexity_viz"
    complexity_viz_dir.mkdir(parents=True, exist_ok=True)
    complexity_viz.run_complexity_viz(
        input_csv=pca_csv,
        output_dir=complexity_viz_dir,
        x_col="SP",
        y_col="TF",
        z_col="AD",
        color_col="LA",
        generate_html=True,
        dpi=160,
    )

    # 10) Path generator sample
    path_dir = sample_root / "path_generator"
    path_dir.mkdir(parents=True, exist_ok=True)
    path_generator.run_path_generator_batch(
        rcp_files=[str(rcp_ev1), str(rcp_ev2), str(rcp_ev3)],
        output_dir=str(path_dir),
        output_folder_name="path_generator_sample",
        dpi=180,
    )

    # 11) Complexity measures sample
    complexity_dir = sample_root / "complexity_measures"
    complexity_dir.mkdir(parents=True, exist_ok=True)
    complexity_rows = []
    for rcp in [rcp_ev1, rcp_ev2, rcp_ev3]:
        sp, tf, ad, la = complexity_measures.calculate_complexity_measures(str(rcp))
        complexity_rows.append({"file": rcp.name, "SP": sp, "TF": tf, "AD": ad, "LA": la})
    pd.DataFrame(complexity_rows).to_csv(complexity_dir / "complexity_measures.csv", index=False)

    # 12) Build RCP sample
    build_dir = sample_root / "build_rcp"
    build_dir.mkdir(parents=True, exist_ok=True)
    build_rcp.run_build_rcp(
        project_path=build_rcp_xlsx,
        output_dir=build_dir,
        output_filename="C2011-10 Building a House.rcp",
    )

    print("Generated sample outputs at:", sample_root)
    print("Subfolders:")
    for sub in sorted([p for p in sample_root.iterdir() if p.is_dir()]):
        file_count = sum(1 for _ in sub.rglob("*") if _.is_file())
        print(f"- {sub.name}: {file_count} files")


if __name__ == "__main__":
    main()
