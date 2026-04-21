"""
Preferences dialog for PERT+.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QGroupBox, QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt

from config.settings import Settings


class PreferencesDialog(QDialog):
    """Application preferences dialog."""

    def __init__(self, settings: Settings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Preferences — PERT+")
        self.setMinimumWidth(460)
        self.setModal(True)

        root = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_simulation_tab(), "Simulation")
        tabs.addTab(self._build_clustering_tab(), "Clustering")
        tabs.addTab(self._build_pca_effects_tab(), "PCA / Effects")
        tabs.addTab(self._build_graphics_tab(), "Graphics")
        tabs.addTab(self._build_batch_tab(), "Batch")
        root.addWidget(tabs)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("btnDanger")
        reset_btn.clicked.connect(self._reset)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._save_and_accept)
        btn_box.rejected.connect(self.reject)

        bottom = QHBoxLayout()
        bottom.addWidget(reset_btn)
        bottom.addStretch()
        bottom.addWidget(btn_box)
        root.addLayout(bottom)

    # ── Tab builders ──────────────────────────────────────────────────────────

    def _build_simulation_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)

        self._sim_n = QSpinBox(); self._sim_n.setRange(100, 1_000_000); self._sim_n.setValue(self._settings.sim_num_simulations)
        self._sim_opt = QDoubleSpinBox(); self._sim_opt.setRange(0.01, 0.99); self._sim_opt.setSingleStep(0.05); self._sim_opt.setValue(self._settings.sim_optimistic_scalar)
        self._sim_pes = QDoubleSpinBox(); self._sim_pes.setRange(1.01, 10.0); self._sim_pes.setSingleStep(0.1); self._sim_pes.setValue(self._settings.sim_pessimistic_scalar)
        self._sim_pct = QDoubleSpinBox(); self._sim_pct.setRange(0.5, 0.9999); self._sim_pct.setSingleStep(0.001); self._sim_pct.setDecimals(4); self._sim_pct.setValue(self._settings.sim_percentile)
        self._sim_dist = QComboBox()
        self._sim_dist.addItem("Beta", "beta")
        self._sim_dist.addItem("Triangular", "triangular")
        self._sim_dist.addItem("Lognormal", "lognormal")
        dist_idx = self._sim_dist.findData(self._settings.sim_distribution)
        self._sim_dist.setCurrentIndex(dist_idx if dist_idx >= 0 else 0)
        self._sim_seed_chk = QCheckBox("Enable fixed seed"); self._sim_seed_chk.setChecked(self._settings.sim_fixed_seed)
        self._sim_seed_val = QSpinBox(); self._sim_seed_val.setRange(0, 999999); self._sim_seed_val.setValue(self._settings.sim_seed_value)

        form.addRow("Simulations per run:", self._sim_n)
        form.addRow("Optimistic scalar:", self._sim_opt)
        form.addRow("Pessimistic scalar:", self._sim_pes)
        form.addRow("Completion percentile:", self._sim_pct)
        form.addRow("Distribution:", self._sim_dist)
        form.addRow(self._sim_seed_chk)
        form.addRow("Seed value:", self._sim_seed_val)
        return w

    def _build_clustering_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)

        self._cl_kmin = QSpinBox(); self._cl_kmin.setRange(2, 20); self._cl_kmin.setValue(self._settings.cluster_k_min)
        self._cl_kmax = QSpinBox(); self._cl_kmax.setRange(2, 50); self._cl_kmax.setValue(self._settings.cluster_k_max)
        self._cl_cw = QDoubleSpinBox(); self._cl_cw.setRange(0.0, 10.0); self._cl_cw.setSingleStep(0.1); self._cl_cw.setValue(self._settings.cluster_complexity_weight)
        self._cl_dw = QDoubleSpinBox(); self._cl_dw.setRange(0.0, 10.0); self._cl_dw.setSingleStep(0.1); self._cl_dw.setValue(self._settings.cluster_dummy_weight)
        self._cl_ts = QDoubleSpinBox(); self._cl_ts.setRange(0.05, 0.5); self._cl_ts.setSingleStep(0.05); self._cl_ts.setValue(self._settings.cluster_test_size)
        self._cl_td = QSpinBox(); self._cl_td.setRange(1, 20); self._cl_td.setValue(self._settings.cluster_tree_depth)
        self._cl_seed_chk = QCheckBox("Enable fixed seed"); self._cl_seed_chk.setChecked(self._settings.cluster_fixed_seed)
        self._cl_seed_val = QSpinBox(); self._cl_seed_val.setRange(0, 999999); self._cl_seed_val.setValue(self._settings.cluster_seed_value)

        form.addRow("K min:", self._cl_kmin)
        form.addRow("K max:", self._cl_kmax)
        form.addRow("Complexity feature weight:", self._cl_cw)
        form.addRow("Dummy feature weight:", self._cl_dw)
        form.addRow("Decision tree test size:", self._cl_ts)
        form.addRow("Decision tree max depth:", self._cl_td)
        form.addRow(self._cl_seed_chk)
        form.addRow("Seed value:", self._cl_seed_val)
        return w

    def _build_pca_effects_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        pca_box = QGroupBox("PCA")
        pca_form = QFormLayout(pca_box)
        self._pca_var = QDoubleSpinBox(); self._pca_var.setRange(0.5, 0.9999); self._pca_var.setSingleStep(0.01); self._pca_var.setDecimals(4); self._pca_var.setValue(self._settings.pca_variance_threshold)
        self._pca_seed_chk = QCheckBox("Enable fixed seed"); self._pca_seed_chk.setChecked(self._settings.pca_fixed_seed)
        self._pca_seed_val = QSpinBox(); self._pca_seed_val.setRange(0, 999999); self._pca_seed_val.setValue(self._settings.pca_seed_value)
        pca_form.addRow("Variance threshold:", self._pca_var)
        pca_form.addRow(self._pca_seed_chk)
        pca_form.addRow("Seed value:", self._pca_seed_val)
        layout.addWidget(pca_box)

        eff_box = QGroupBox("Effect Size")
        eff_form = QFormLayout(eff_box)
        self._eff_n = QSpinBox(); self._eff_n.setRange(100, 100000); self._eff_n.setValue(self._settings.effect_n_bootstrap)
        self._eff_ci = QDoubleSpinBox(); self._eff_ci.setRange(0.5, 0.999); self._eff_ci.setSingleStep(0.01); self._eff_ci.setDecimals(3); self._eff_ci.setValue(self._settings.effect_ci_level)
        self._eff_seed_chk = QCheckBox("Enable fixed seed"); self._eff_seed_chk.setChecked(self._settings.effect_fixed_seed)
        self._eff_seed_val = QSpinBox(); self._eff_seed_val.setRange(0, 999999); self._eff_seed_val.setValue(self._settings.effect_seed_value)
        eff_form.addRow("Bootstrap samples:", self._eff_n)
        eff_form.addRow("CI level:", self._eff_ci)
        eff_form.addRow(self._eff_seed_chk)
        eff_form.addRow("Seed value:", self._eff_seed_val)
        layout.addWidget(eff_box)
        layout.addStretch()
        return w

    def _build_graphics_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)
        self._dpi = QSpinBox(); self._dpi.setRange(72, 600); self._dpi.setValue(self._settings.graphics_dpi)
        form.addRow("Output DPI:", self._dpi)
        return w

    def _build_batch_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)
        self._b_parallel = QCheckBox("Enable parallel execution"); self._b_parallel.setChecked(self._settings.batch_parallel)
        self._b_workers = QSpinBox(); self._b_workers.setRange(1, 32); self._b_workers.setValue(self._settings.batch_max_workers)
        form.addRow(self._b_parallel)
        form.addRow("Max worker threads:", self._b_workers)
        return w

    # ── Save / reset ──────────────────────────────────────────────────────────

    def _save_and_accept(self) -> None:
        s = self._settings
        # Simulation
        s.sim_num_simulations = self._sim_n.value()
        s.sim_optimistic_scalar = self._sim_opt.value()
        s.sim_pessimistic_scalar = self._sim_pes.value()
        s.sim_percentile = self._sim_pct.value()
        s.sim_distribution = str(self._sim_dist.currentData())
        s.sim_fixed_seed = self._sim_seed_chk.isChecked()
        s.sim_seed_value = self._sim_seed_val.value()
        # Clustering
        s.cluster_k_min = self._cl_kmin.value()
        s.cluster_k_max = self._cl_kmax.value()
        s.cluster_complexity_weight = self._cl_cw.value()
        s.cluster_dummy_weight = self._cl_dw.value()
        s.cluster_test_size = self._cl_ts.value()
        s.cluster_tree_depth = self._cl_td.value()
        s.cluster_fixed_seed = self._cl_seed_chk.isChecked()
        s.cluster_seed_value = self._cl_seed_val.value()
        # PCA
        s.pca_variance_threshold = self._pca_var.value()
        s.pca_fixed_seed = self._pca_seed_chk.isChecked()
        s.pca_seed_value = self._pca_seed_val.value()
        # Effect size
        s.effect_n_bootstrap = self._eff_n.value()
        s.effect_ci_level = self._eff_ci.value()
        s.effect_fixed_seed = self._eff_seed_chk.isChecked()
        s.effect_seed_value = self._eff_seed_val.value()
        # Graphics
        s.graphics_dpi = self._dpi.value()
        # Batch
        s.batch_parallel = self._b_parallel.isChecked()
        s.batch_max_workers = self._b_workers.value()
        s.sync()
        self.accept()

    def _reset(self) -> None:
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "This will clear all saved preferences. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._settings.reset_to_defaults()
            self.reject()
