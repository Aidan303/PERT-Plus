"""
Complexity measure calculations from RCP project network files.
Adapted from: Network Complexity Calculator/Complexity_Measure_Generator.py
(Original file not modified.)
"""
from __future__ import annotations

import os
import pandas as pd


# ── RCP File Parser ────────────────────────────────────────────────────────────

def parse_rcp_file(filename: str) -> list[list[int]]:
    with open(filename, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    num_nodes = int(lines[0].split()[0])
    node_successors: list[list[int]] = [[] for _ in range(num_nodes)]
    for idx, line in enumerate(lines[2 : 2 + num_nodes]):
        parts = line.split()
        num_succ = int(parts[5])
        if num_succ > 0:
            successors = [int(x) - 1 for x in parts[6 : 6 + num_succ]]
            node_successors[idx] = successors
    return node_successors


def build_predecessors(node_successors: list[list[int]]) -> list[list[int]]:
    num_nodes = len(node_successors)
    predecessors: list[list[int]] = [[] for _ in range(num_nodes)]
    for node, succs in enumerate(node_successors):
        for succ in succs:
            predecessors[succ].append(node)
    return predecessors


# ── Progressive / Regressive Levels ───────────────────────────────────────────

def calculate_progressive_levels(filename: str) -> list[int | None]:
    node_successors = parse_rcp_file(filename)
    num_nodes = len(node_successors)
    predecessors = build_predecessors(node_successors)
    progressive: list[int | None] = [None] * num_nodes

    for i in range(num_nodes):
        filtered_preds = [p for p in predecessors[i] if p != 0 and p != num_nodes - 1]
        if not filtered_preds:
            progressive[i] = 1

    changed = True
    while changed:
        changed = False
        for i in range(num_nodes):
            filtered_preds = [p for p in predecessors[i] if p != 0 and p != num_nodes - 1]
            if progressive[i] is None and filtered_preds:
                pred_levels = [progressive[p] for p in filtered_preds if progressive[p] is not None]
                if len(pred_levels) == len(filtered_preds):
                    new_val = max(pred_levels) + 1  # type: ignore[arg-type]
                    if progressive[i] != new_val:
                        progressive[i] = new_val
                        changed = True

    for i in range(num_nodes):
        filtered_preds = [p for p in predecessors[i] if p != 0 and p != num_nodes - 1]
        if not filtered_preds:
            progressive[i] = 1

    return progressive


def calculate_mpl(filename: str) -> tuple[int, list]:
    progressive = calculate_progressive_levels(filename)
    max_level = max(p for p in progressive if p is not None)
    return max_level - 1, []


def calculate_regressive_levels(filename: str) -> list[int | None]:
    node_successors = parse_rcp_file(filename)
    num_nodes = len(node_successors)
    mpl, _ = calculate_mpl(filename)
    regressive: list[int | None] = [None] * num_nodes

    for i in range(num_nodes):
        filtered_succs = [s for s in node_successors[i] if s != 0 and s != num_nodes - 1]
        if not filtered_succs:
            regressive[i] = mpl

    changed = True
    while changed:
        changed = False
        for i in range(num_nodes):
            filtered_succs = [s for s in node_successors[i] if s != 0 and s != num_nodes - 1]
            if regressive[i] is None and filtered_succs:
                succ_levels = [regressive[s] for s in filtered_succs if regressive[s] is not None]
                if len(succ_levels) == len(filtered_succs):
                    new_val = min(succ_levels) - 1  # type: ignore[arg-type]
                    if regressive[i] != new_val:
                        regressive[i] = new_val
                        changed = True

    for i in range(num_nodes):
        filtered_succs = [s for s in node_successors[i] if s != 0 and s != num_nodes - 1]
        if not filtered_succs:
            regressive[i] = mpl

    return regressive


# ── Complexity Measures ────────────────────────────────────────────────────────

def calculate_SP(filename: str) -> float:
    node_successors = parse_rcp_file(filename)
    num_nodes = len(node_successors)
    mpl, _ = calculate_mpl(filename)
    effective_nodes = num_nodes - 2 if num_nodes > 2 else 1
    if effective_nodes == 1:
        return 1.0
    return round((mpl - 1) / (effective_nodes - 1), 3)


def calculate_TF(filename: str) -> float:
    node_successors = parse_rcp_file(filename)
    num_nodes = len(node_successors)
    mpl, _ = calculate_mpl(filename)
    effective_nodes = num_nodes - 2 if num_nodes > 2 else 1
    if mpl == 1 or mpl == effective_nodes:
        return 0.0
    progressive = calculate_progressive_levels(filename)
    regressive = calculate_regressive_levels(filename)
    total = sum(
        (regressive[i] or 0) - (progressive[i] or 0) for i in range(num_nodes)
    )
    denominator = (mpl - 1) * (effective_nodes - mpl)
    if denominator == 0:
        return 0.0
    return round(total / denominator, 3)


def calculate_AD(filename: str) -> float:
    node_successors = parse_rcp_file(filename)
    num_nodes = len(node_successors)
    mpl, _ = calculate_mpl(filename)
    non_dummy_indices = list(range(1, num_nodes - 1)) if num_nodes > 2 else []
    num_non_dummy = len(non_dummy_indices)
    if mpl == 1 or mpl == num_non_dummy:
        return 0.0
    progressive = calculate_progressive_levels(filename)
    w_hat = num_non_dummy / mpl
    wa_by_level: dict[int, int] = {level: 0 for level in range(1, mpl + 1)}
    for i in non_dummy_indices:
        pl = progressive[i]
        if pl is not None and 1 <= pl <= mpl:
            wa_by_level[pl] += 1
    aw = sum(abs(wa_by_level[a] - w_hat) for a in range(1, mpl + 1))
    amax = 2 * (mpl - 1) * (w_hat - 1)
    if amax == 0:
        return 0.0
    return round(aw / amax, 3)


def calculate_LA(filename: str) -> float:
    node_successors = parse_rcp_file(filename)
    num_nodes = len(node_successors)
    mpl, _ = calculate_mpl(filename)
    non_dummy_indices = list(range(1, num_nodes - 1)) if num_nodes > 2 else []
    n = len(non_dummy_indices)
    if n == 0 or mpl < 2:
        return 0.0
    progressive = calculate_progressive_levels(filename)
    wa_by_level: dict[int, int] = {level: 0 for level in range(1, mpl + 1)}
    for i in non_dummy_indices:
        pl = progressive[i]
        if pl is not None and 1 <= pl <= mpl:
            wa_by_level[pl] += 1
    w1 = wa_by_level[1]
    n0_1 = 0
    for i in non_dummy_indices:
        for j in node_successors[i]:
            if j in non_dummy_indices:
                pi = progressive[i]
                pj = progressive[j]
                if pi is not None and pj is not None and pj - pi == 1:
                    n0_1 += 1
    D = sum(wa_by_level[a] * wa_by_level[a + 1] for a in range(1, mpl))
    if D == n - w1:
        return 1.0
    elif D > n - w1:
        return round((n0_1 - n + w1) / (D - n + w1), 3)
    return 0.0


def calculate_complexity_measures(filename: str) -> tuple[float, float, float, float]:
    """Return (SP, TF, AD, LA) for the given RCP file."""
    sp = calculate_SP(filename)
    tf = calculate_TF(filename)
    ad = calculate_AD(filename)
    la = calculate_LA(filename)
    return sp, tf, ad, la
