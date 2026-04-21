"""
Persistent application settings using QSettings.
Stores user preferences across sessions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QSettings


APP_NAME = "PERT+"
ORG_NAME = "PERTPlus"


class Settings:
    """Thin QSettings wrapper with typed getters/setters and reset support."""

    def __init__(self, portable: bool = False, portable_dir: Optional[Path] = None):
        if portable and portable_dir:
            ini_path = str(portable_dir / "settings.ini")
            self._qs = QSettings(ini_path, QSettings.Format.IniFormat)
        else:
            self._qs = QSettings(ORG_NAME, APP_NAME)

    # ── Theme ──────────────────────────────────────────────────────────────────
    @property
    def theme(self) -> str:
        return str(self._qs.value("ui/theme", "light"))

    @theme.setter
    def theme(self, value: str) -> None:
        self._qs.setValue("ui/theme", value)

    # ── Recent directories ─────────────────────────────────────────────────────
    @property
    def last_input_dir(self) -> str:
        return str(self._qs.value("dirs/last_input", ""))

    @last_input_dir.setter
    def last_input_dir(self, value: str) -> None:
        self._qs.setValue("dirs/last_input", value)

    @property
    def last_output_dir(self) -> str:
        return str(self._qs.value("dirs/last_output", ""))

    @last_output_dir.setter
    def last_output_dir(self, value: str) -> None:
        self._qs.setValue("dirs/last_output", value)

    # ── Simulation defaults ────────────────────────────────────────────────────
    @property
    def sim_num_simulations(self) -> int:
        return int(self._qs.value("sim/num_simulations", 10000))

    @sim_num_simulations.setter
    def sim_num_simulations(self, value: int) -> None:
        self._qs.setValue("sim/num_simulations", value)

    @property
    def sim_optimistic_scalar(self) -> float:
        return float(self._qs.value("sim/optimistic_scalar", 0.5))

    @sim_optimistic_scalar.setter
    def sim_optimistic_scalar(self, value: float) -> None:
        self._qs.setValue("sim/optimistic_scalar", value)

    @property
    def sim_pessimistic_scalar(self) -> float:
        return float(self._qs.value("sim/pessimistic_scalar", 1.5))

    @sim_pessimistic_scalar.setter
    def sim_pessimistic_scalar(self, value: float) -> None:
        self._qs.setValue("sim/pessimistic_scalar", value)

    @property
    def sim_percentile(self) -> float:
        return float(self._qs.value("sim/percentile", 0.999))

    @sim_percentile.setter
    def sim_percentile(self, value: float) -> None:
        self._qs.setValue("sim/percentile", value)

    @property
    def sim_fixed_seed(self) -> bool:
        return self._qs.value("sim/fixed_seed", False, type=bool)

    @sim_fixed_seed.setter
    def sim_fixed_seed(self, value: bool) -> None:
        self._qs.setValue("sim/fixed_seed", value)

    @property
    def sim_seed_value(self) -> int:
        return int(self._qs.value("sim/seed_value", 42))

    @sim_seed_value.setter
    def sim_seed_value(self, value: int) -> None:
        self._qs.setValue("sim/seed_value", value)

    @property
    def sim_parallel(self) -> bool:
        return self._qs.value("sim/parallel", False, type=bool)

    @sim_parallel.setter
    def sim_parallel(self, value: bool) -> None:
        self._qs.setValue("sim/parallel", value)

    @property
    def sim_max_workers(self) -> int:
        return int(self._qs.value("sim/max_workers", 4))

    @sim_max_workers.setter
    def sim_max_workers(self, value: int) -> None:
        self._qs.setValue("sim/max_workers", value)

    @property
    def sim_distribution(self) -> str:
        value = str(self._qs.value("sim/distribution", "beta"))
        if value not in {"beta", "triangular", "lognormal"}:
            return "beta"
        return value

    @sim_distribution.setter
    def sim_distribution(self, value: str) -> None:
        if value not in {"beta", "triangular", "lognormal"}:
            value = "beta"
        self._qs.setValue("sim/distribution", value)

    # ── Clustering defaults ────────────────────────────────────────────────────
    @property
    def cluster_k_min(self) -> int:
        return int(self._qs.value("cluster/k_min", 2))

    @cluster_k_min.setter
    def cluster_k_min(self, value: int) -> None:
        self._qs.setValue("cluster/k_min", value)

    @property
    def cluster_k_max(self) -> int:
        return int(self._qs.value("cluster/k_max", 10))

    @cluster_k_max.setter
    def cluster_k_max(self, value: int) -> None:
        self._qs.setValue("cluster/k_max", value)

    @property
    def cluster_complexity_weight(self) -> float:
        return float(self._qs.value("cluster/complexity_weight", 1.0))

    @cluster_complexity_weight.setter
    def cluster_complexity_weight(self, value: float) -> None:
        self._qs.setValue("cluster/complexity_weight", value)

    @property
    def cluster_dummy_weight(self) -> float:
        return float(self._qs.value("cluster/dummy_weight", 0.5))

    @cluster_dummy_weight.setter
    def cluster_dummy_weight(self, value: float) -> None:
        self._qs.setValue("cluster/dummy_weight", value)

    @property
    def cluster_test_size(self) -> float:
        return float(self._qs.value("cluster/test_size", 0.2))

    @cluster_test_size.setter
    def cluster_test_size(self, value: float) -> None:
        self._qs.setValue("cluster/test_size", value)

    @property
    def cluster_tree_depth(self) -> int:
        return int(self._qs.value("cluster/tree_depth", 4))

    @cluster_tree_depth.setter
    def cluster_tree_depth(self, value: int) -> None:
        self._qs.setValue("cluster/tree_depth", value)

    @property
    def cluster_fixed_seed(self) -> bool:
        return self._qs.value("cluster/fixed_seed", False, type=bool)

    @cluster_fixed_seed.setter
    def cluster_fixed_seed(self, value: bool) -> None:
        self._qs.setValue("cluster/fixed_seed", value)

    @property
    def cluster_seed_value(self) -> int:
        return int(self._qs.value("cluster/seed_value", 42))

    @cluster_seed_value.setter
    def cluster_seed_value(self, value: int) -> None:
        self._qs.setValue("cluster/seed_value", value)

    # ── PCA defaults ───────────────────────────────────────────────────────────
    @property
    def pca_variance_threshold(self) -> float:
        return float(self._qs.value("pca/variance_threshold", 0.95))

    @pca_variance_threshold.setter
    def pca_variance_threshold(self, value: float) -> None:
        self._qs.setValue("pca/variance_threshold", value)

    @property
    def pca_dpi(self) -> int:
        return int(self._qs.value("pca/dpi", 300))

    @pca_dpi.setter
    def pca_dpi(self, value: int) -> None:
        self._qs.setValue("pca/dpi", value)

    @property
    def pca_fixed_seed(self) -> bool:
        return self._qs.value("pca/fixed_seed", False, type=bool)

    @pca_fixed_seed.setter
    def pca_fixed_seed(self, value: bool) -> None:
        self._qs.setValue("pca/fixed_seed", value)

    @property
    def pca_seed_value(self) -> int:
        return int(self._qs.value("pca/seed_value", 42))

    @pca_seed_value.setter
    def pca_seed_value(self, value: int) -> None:
        self._qs.setValue("pca/seed_value", value)

    # ── Effect size defaults ───────────────────────────────────────────────────
    @property
    def effect_n_bootstrap(self) -> int:
        return int(self._qs.value("effect/n_bootstrap", 2000))

    @effect_n_bootstrap.setter
    def effect_n_bootstrap(self, value: int) -> None:
        self._qs.setValue("effect/n_bootstrap", value)

    @property
    def effect_ci_level(self) -> float:
        return float(self._qs.value("effect/ci_level", 0.95))

    @effect_ci_level.setter
    def effect_ci_level(self, value: float) -> None:
        self._qs.setValue("effect/ci_level", value)

    @property
    def effect_fixed_seed(self) -> bool:
        return self._qs.value("effect/fixed_seed", False, type=bool)

    @effect_fixed_seed.setter
    def effect_fixed_seed(self, value: bool) -> None:
        self._qs.setValue("effect/fixed_seed", value)

    @property
    def effect_seed_value(self) -> int:
        return int(self._qs.value("effect/seed_value", 42))

    @effect_seed_value.setter
    def effect_seed_value(self, value: int) -> None:
        self._qs.setValue("effect/seed_value", value)

    # ── Batch defaults ─────────────────────────────────────────────────────────
    @property
    def batch_parallel(self) -> bool:
        return self._qs.value("batch/parallel", False, type=bool)

    @batch_parallel.setter
    def batch_parallel(self, value: bool) -> None:
        self._qs.setValue("batch/parallel", value)

    @property
    def batch_max_workers(self) -> int:
        return int(self._qs.value("batch/max_workers", 4))

    @batch_max_workers.setter
    def batch_max_workers(self, value: int) -> None:
        self._qs.setValue("batch/max_workers", value)

    # ── Graphics DPI ───────────────────────────────────────────────────────────
    @property
    def graphics_dpi(self) -> int:
        return int(self._qs.value("graphics/dpi", 300))

    @graphics_dpi.setter
    def graphics_dpi(self, value: int) -> None:
        self._qs.setValue("graphics/dpi", value)

    # ── Utility ────────────────────────────────────────────────────────────────
    def reset_to_defaults(self) -> None:
        """Clear all stored settings (restores all defaults on next read)."""
        self._qs.clear()
        self._qs.sync()

    def sync(self) -> None:
        self._qs.sync()

    def get(self, key: str, default: Any = None) -> Any:
        return self._qs.value(key, default)

    def set(self, key: str, value: Any) -> None:
        self._qs.setValue(key, value)
