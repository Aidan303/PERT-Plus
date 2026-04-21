"""
Path generator engine.
Creates a network PNG from an RCP file and highlights the critical path.

Adapted from:
course_files_export V1/Project Time Completion Project/Python Code/Path Generator/path_generator.py
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyArrowPatch


def parse_rcp_file(rcp_path: str) -> list[dict]:
    """Parse Patterson-format RCP into activity dicts."""
    with open(rcp_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 3:
        raise ValueError(f"Invalid RCP file (too short): {rcp_path}")

    activities = []
    for row in lines[2:]:
        parts = row.split()
        if len(parts) < 6:
            raise ValueError(f"Invalid activity row in RCP: {row}")
        duration = int(parts[0])
        num_successors = int(parts[5])
        successors = [int(x) for x in parts[6 : 6 + num_successors]] if num_successors > 0 else []
        activities.append({"duration": duration, "successors": successors})

    return activities


def find_all_paths(activities: list[dict], start_idx: int = 0, end_idx: Optional[int] = None) -> list[list[int]]:
    """Return all simple paths from start node to end node (0-based indices)."""
    if end_idx is None:
        end_idx = len(activities) - 1

    paths: list[list[int]] = []
    stack: list[tuple[int, list[int]]] = [(start_idx, [start_idx])]

    while stack:
        current, path = stack.pop()
        if current == end_idx:
            paths.append(path)
            continue
        for succ in activities[current]["successors"]:
            succ_idx = succ - 1  # RCP successors are 1-based
            if succ_idx not in path:
                stack.append((succ_idx, path + [succ_idx]))

    return paths


def _path_duration(path: list[int], activities: list[dict]) -> int:
    return sum(activities[idx]["duration"] for idx in path)


def _critical_path(paths: list[list[int]], activities: list[dict]) -> tuple[list[int], int]:
    if not paths:
        raise ValueError("No paths found in network.")
    durations = [_path_duration(path, activities) for path in paths]
    max_idx = max(range(len(paths)), key=lambda i: durations[i])
    return paths[max_idx], durations[max_idx]


def _build_graph(activities: list[dict]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for idx, activity in enumerate(activities, start=1):
        graph.add_node(idx, duration=activity["duration"])
    for idx, activity in enumerate(activities, start=1):
        for succ in activity["successors"]:
            graph.add_edge(idx, succ)
    return graph


def _calculate_positions(graph: nx.DiGraph) -> Dict[int, tuple[float, float]]:
    """Hierarchical left-to-right layout with stable per-level ordering."""
    depths: Dict[int, int] = {}

    def depth_of(node: int) -> int:
        if node in depths:
            return depths[node]
        predecessors = list(graph.predecessors(node))
        if not predecessors:
            depths[node] = 0
        else:
            depths[node] = max(depth_of(pred) for pred in predecessors) + 1
        return depths[node]

    for node in graph.nodes():
        depth_of(node)

    depth_groups: Dict[int, list[int]] = {}
    for node, depth in depths.items():
        depth_groups.setdefault(depth, []).append(node)

    positions: Dict[int, tuple[float, float]] = {}
    for depth in sorted(depth_groups.keys()):
        nodes_at_depth = sorted(depth_groups[depth])
        count = len(nodes_at_depth)
        spacing = 1.2 if count <= 1 else 2.6 / (count - 1)
        for idx, node in enumerate(nodes_at_depth):
            x = depth * 3.3
            y = idx * spacing - (count - 1) * spacing / 2
            positions[node] = (x, y)

    return positions


def _node_label(node_id: int, total_nodes: int, duration: int) -> str:
    if node_id == 1:
        display = "0"
    elif node_id == total_nodes:
        display = "End"
    else:
        display = str(node_id - 1)
    return f"{display}\n({duration})"


def run_path_generator(
    rcp_file: str,
    output_dir: str,
    output_filename: Optional[str] = None,
    dpi: int = 300,
) -> Path:
    """
    Generate network PNG with critical path highlighted.

    Returns the output PNG path.
    """
    rcp_path = Path(rcp_file)
    if not rcp_path.exists():
        raise FileNotFoundError(f"RCP file not found: {rcp_file}")

    activities = parse_rcp_file(str(rcp_path))
    paths = find_all_paths(activities)
    critical_path, critical_duration = _critical_path(paths, activities)

    graph = _build_graph(activities)
    positions = _calculate_positions(graph)

    critical_edges = set()
    for i in range(len(critical_path) - 1):
        # Convert 0-based path indices to graph node labels (1-based).
        critical_edges.add((critical_path[i] + 1, critical_path[i + 1] + 1))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if output_filename:
        filename = output_filename if output_filename.lower().endswith(".png") else f"{output_filename}.png"
    else:
        filename = f"{rcp_path.stem}_network_critical_path.png"
    out_path = out_dir / filename

    fig, ax = plt.subplots(figsize=(16, 10))

    for u, v in graph.edges():
        is_critical = (u, v) in critical_edges
        arrow = FancyArrowPatch(
            positions[u],
            positions[v],
            arrowstyle="->",
            mutation_scale=22,
            linewidth=2.6 if is_critical else 1.3,
            color="red" if is_critical else "gray",
            connectionstyle="arc3,rad=0.07",
            shrinkA=20,
            shrinkB=20,
            zorder=1,
        )
        ax.add_patch(arrow)

    total_nodes = len(activities)
    node_colors = ["lightgray" if node in (1, total_nodes) else "lightblue" for node in graph.nodes()]
    nx.draw_networkx_nodes(
        graph,
        positions,
        node_color=node_colors,
        node_size=1050,
        node_shape="o",
        edgecolors="black",
        linewidths=0.8,
        ax=ax,
    )

    labels = {
        node: _node_label(node, total_nodes, int(graph.nodes[node]["duration"]))
        for node in graph.nodes()
    }
    nx.draw_networkx_labels(graph, positions, labels=labels, font_size=9, font_weight="bold", ax=ax)

    # Display path without dummy start/end and with dummy-adjusted numbering.
    trimmed_critical = critical_path[1:-1]
    critical_display = " ".join(str(node) for node in trimmed_critical)
    parent_name = rcp_path.parent.name
    ax.set_title(
        f"Project Network: {parent_name} {rcp_path.stem}\n"
        f"Critical Path: {critical_display if critical_display else '(none)'} | Duration: {critical_duration}",
        fontsize=14,
        fontweight="bold",
    )
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return out_path


def run_path_generator_batch(
    rcp_files: list[str],
    output_dir: str,
    output_folder_name: Optional[str] = None,
    dpi: int = 300,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> dict:
    """
    Generate network PNGs for multiple RCP files.

    All outputs are written into a single run subfolder inside output_dir.

    Returns:
        {
            "output_dir": "...",
            "image_paths": ["...png", ...],
            "count": int,
        }
    """
    if not rcp_files:
        raise ValueError("No RCP files were provided.")

    base_output = Path(output_dir)
    base_output.mkdir(parents=True, exist_ok=True)

    if output_folder_name and output_folder_name.strip():
        folder_name = output_folder_name.strip()
    else:
        folder_name = f"path_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    run_output = base_output / folder_name
    if run_output.exists():
        suffix = 1
        while (base_output / f"{folder_name}_{suffix}").exists():
            suffix += 1
        run_output = base_output / f"{folder_name}_{suffix}"
    run_output.mkdir(parents=True, exist_ok=True)

    image_paths: list[str] = []
    total = len(rcp_files)

    for idx, rcp_file in enumerate(rcp_files, start=1):
        if cancel_check and cancel_check():
            raise InterruptedError("Path generation cancelled by user.")

        rcp_path = Path(rcp_file)
        safe_name = f"{rcp_path.parent.name}_{rcp_path.stem}_network_critical_path.png"
        png_path = run_path_generator(
            rcp_file=str(rcp_path),
            output_dir=str(run_output),
            output_filename=safe_name,
            dpi=dpi,
        )
        image_paths.append(str(png_path))

        if progress_cb:
            progress_cb(idx, total, f"[{idx}/{total}] Generated {png_path.name}")

    return {
        "output_dir": str(run_output),
        "image_paths": image_paths,
        "count": len(image_paths),
    }