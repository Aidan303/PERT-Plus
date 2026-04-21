"""
Clustering panel — hierarchical clustering + decision-tree analysis.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QPushButton,
    QSpinBox, QDoubleSpinBox, QCheckBox,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.base_panel import BasePanel
from ui.widgets.file_picker import FilePicker
import engine.clustering as cl_engine


class ClusteringPanel(BasePanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            "Clustering Analysis",
            "Run hierarchical clustering and decision-tree classification on complexity data.",
            settings, job_manager, parent,
        )

    def _build_form(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)

        in_box = QGroupBox("Input")
        in_form = QFormLayout(in_box)
        self._input_picker = FilePicker(
            mode="file",
            filter_str="CSV Files (*.csv);;All Files (*)",
            placeholder="Select network features CSV",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("Features CSV:", self._input_picker)
        root.addWidget(in_box)

        param_box = QGroupBox("Parameters")
        param_form = QFormLayout(param_box)

        self._kmin = QSpinBox(); self._kmin.setRange(2, 20); self._kmin.setValue(self._settings.cluster_k_min)
        self._kmax = QSpinBox(); self._kmax.setRange(2, 50); self._kmax.setValue(self._settings.cluster_k_max)
        self._cw = QDoubleSpinBox(); self._cw.setRange(0.0, 10.0); self._cw.setSingleStep(0.1); self._cw.setValue(self._settings.cluster_complexity_weight)
        self._dw = QDoubleSpinBox(); self._dw.setRange(0.0, 10.0); self._dw.setSingleStep(0.1); self._dw.setValue(self._settings.cluster_dummy_weight)
        self._ts = QDoubleSpinBox(); self._ts.setRange(0.05, 0.5); self._ts.setSingleStep(0.05); self._ts.setValue(self._settings.cluster_test_size)
        self._td = QSpinBox(); self._td.setRange(1, 20); self._td.setValue(self._settings.cluster_tree_depth)

        param_form.addRow("K min:", self._kmin)
        param_form.addRow("K max:", self._kmax)
        param_form.addRow("Complexity feature weight:", self._cw)
        param_form.addRow("Dummy feature weight:", self._dw)
        param_form.addRow("Decision tree test size:", self._ts)
        param_form.addRow("Decision tree max depth:", self._td)
        root.addWidget(param_box)

        repro_box = QGroupBox("Reproducibility")
        repro_form = QFormLayout(repro_box)
        self._seed_chk = QCheckBox("Use fixed seed"); self._seed_chk.setChecked(self._settings.cluster_fixed_seed)
        self._seed_val = QSpinBox(); self._seed_val.setRange(0, 999999); self._seed_val.setValue(self._settings.cluster_seed_value)
        repro_form.addRow(self._seed_chk)
        repro_form.addRow("Seed:", self._seed_val)
        root.addWidget(repro_box)

        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        self._out_picker = FilePicker(
            mode="folder",
            placeholder="Select output folder",
            start_dir=self._settings.last_output_dir,
        )
        out_form.addRow("Output folder:", self._out_picker)
        root.addWidget(out_box)

        run_btn = QPushButton("Run Clustering")
        run_btn.clicked.connect(self.run_job)
        root.addWidget(run_btn)
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return cl_engine.run_clustering

    def _collect_kwargs(self) -> Dict[str, Any]:
        seed = self._seed_val.value() if self._seed_chk.isChecked() else None

        self._settings.cluster_k_min = self._kmin.value()
        self._settings.cluster_k_max = self._kmax.value()
        self._settings.cluster_complexity_weight = self._cw.value()
        self._settings.cluster_dummy_weight = self._dw.value()
        self._settings.cluster_test_size = self._ts.value()
        self._settings.cluster_tree_depth = self._td.value()
        self._settings.cluster_fixed_seed = self._seed_chk.isChecked()
        self._settings.cluster_seed_value = self._seed_val.value()

        return {
            "input_csv": self._input_picker.path,
            "output_dir": self._out_picker.path,
            "k_min": self._kmin.value(),
            "k_max": self._kmax.value(),
            "complexity_weight": self._cw.value(),
            "dummy_weight": self._dw.value(),
            "test_size": self._ts.value(),
            "tree_max_depth": self._td.value(),
            "random_state": seed,
        }
