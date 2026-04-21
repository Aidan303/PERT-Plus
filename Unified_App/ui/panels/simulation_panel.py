"""
Simulation panel — runs Monte Carlo simulation on one or more RCP files.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QLabel, QComboBox,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.base_panel import BasePanel
from ui.widgets.file_picker import FilePicker
import engine.simulator as sim_engine


class SimulationPanel(BasePanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            "Monte Carlo Simulation",
            "Run PERT-based Monte Carlo simulation on one or more RCP project files.",
            settings, job_manager, parent,
        )

    # ── Form ──────────────────────────────────────────────────────────────────

    def _build_form(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)

        # Inputs
        input_box = QGroupBox("Input")
        input_form = QFormLayout(input_box)
        self._rcp_picker = FilePicker(
            mode="files",
            filter_str="RCP Files (*.rcp);;All Files (*)",
            placeholder="Select one or more .rcp files",
            start_dir=self._settings.last_input_dir,
        )
        self._rcp_picker.path_changed.connect(
            lambda p: self._settings.__setattr__("last_input_dir", str(__import__("pathlib").Path(p.split(";")[0]).parent)) if p else None
        )
        input_form.addRow("RCP file(s):", self._rcp_picker)
        root.addWidget(input_box)

        # Distribution (single select)
        dist_box = QGroupBox("Distribution")
        dist_form = QFormLayout(dist_box)
        self._dist_combo = QComboBox()
        self._dist_combo.addItem("Beta", "beta")
        self._dist_combo.addItem("Triangular", "triangular")
        self._dist_combo.addItem("Lognormal", "lognormal")
        dist_idx = self._dist_combo.findData(self._settings.sim_distribution)
        self._dist_combo.setCurrentIndex(dist_idx if dist_idx >= 0 else 0)
        dist_form.addRow("Type:", self._dist_combo)
        root.addWidget(dist_box)

        # Parameters
        param_box = QGroupBox("Parameters")
        param_form = QFormLayout(param_box)

        self._n_sim = QSpinBox(); self._n_sim.setRange(100, 1_000_000)
        self._n_sim.setValue(self._settings.sim_num_simulations)

        self._opt_scalar = QDoubleSpinBox(); self._opt_scalar.setRange(0.01, 0.99)
        self._opt_scalar.setSingleStep(0.05); self._opt_scalar.setValue(self._settings.sim_optimistic_scalar)

        self._pes_scalar = QDoubleSpinBox(); self._pes_scalar.setRange(1.01, 10.0)
        self._pes_scalar.setSingleStep(0.1); self._pes_scalar.setValue(self._settings.sim_pessimistic_scalar)

        self._percentile = QDoubleSpinBox(); self._percentile.setRange(0.5, 0.9999)
        self._percentile.setSingleStep(0.001); self._percentile.setDecimals(4)
        self._percentile.setValue(self._settings.sim_percentile)

        param_form.addRow("Simulations:", self._n_sim)
        param_form.addRow("Optimistic scalar:", self._opt_scalar)
        param_form.addRow("Pessimistic scalar:", self._pes_scalar)
        param_form.addRow("Completion percentile:", self._percentile)
        root.addWidget(param_box)

        # Reproducibility
        repro_box = QGroupBox("Reproducibility")
        repro_form = QFormLayout(repro_box)
        self._fixed_seed_chk = QCheckBox("Use fixed seed")
        self._fixed_seed_chk.setChecked(self._settings.sim_fixed_seed)
        self._seed_spin = QSpinBox(); self._seed_spin.setRange(0, 999999)
        self._seed_spin.setValue(self._settings.sim_seed_value)
        repro_form.addRow(self._fixed_seed_chk)
        repro_form.addRow("Seed value:", self._seed_spin)
        root.addWidget(repro_box)

        # Batch / parallel
        batch_box = QGroupBox("Batch Execution")
        batch_form = QFormLayout(batch_box)
        self._parallel_chk = QCheckBox("Run files in parallel")
        self._parallel_chk.setChecked(self._settings.sim_parallel)
        self._workers_spin = QSpinBox(); self._workers_spin.setRange(1, 32)
        self._workers_spin.setValue(self._settings.sim_max_workers)
        batch_form.addRow(self._parallel_chk)
        batch_form.addRow("Max workers:", self._workers_spin)
        root.addWidget(batch_box)

        # Output
        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        self._out_picker = FilePicker(
            mode="folder",
            placeholder="Select output folder",
            start_dir=self._settings.last_output_dir,
        )
        out_form.addRow("Output folder:", self._out_picker)
        root.addWidget(out_box)

        # Run button
        run_btn = QPushButton("Run Simulation")
        run_btn.clicked.connect(self.run_job)
        root.addWidget(run_btn)
        root.addStretch()
        return w

    # ── Engine wiring ─────────────────────────────────────────────────────────

    def _engine_fn(self) -> Callable:
        return sim_engine.run_batch_simulation

    def _collect_kwargs(self) -> Dict[str, Any]:
        rcp_paths = [p.strip() for p in self._rcp_picker.path.split(";") if p.strip()]
        selected_distribution = str(self._dist_combo.currentData())

        seed = self._seed_spin.value() if self._fixed_seed_chk.isChecked() else None

        # Persist settings
        self._settings.sim_num_simulations = self._n_sim.value()
        self._settings.sim_optimistic_scalar = self._opt_scalar.value()
        self._settings.sim_pessimistic_scalar = self._pes_scalar.value()
        self._settings.sim_percentile = self._percentile.value()
        self._settings.sim_fixed_seed = self._fixed_seed_chk.isChecked()
        self._settings.sim_seed_value = self._seed_spin.value()
        self._settings.sim_parallel = self._parallel_chk.isChecked()
        self._settings.sim_max_workers = self._workers_spin.value()
        self._settings.sim_distribution = selected_distribution
        if self._out_picker.path:
            self._settings.last_output_dir = self._out_picker.path

        return {
            "rcp_files": rcp_paths,
            "output_dir": self._out_picker.path,
            "optimistic_scalar": self._opt_scalar.value(),
            "pessimistic_scalar": self._pes_scalar.value(),
            "distribution_types": [selected_distribution],
            "num_simulations": self._n_sim.value(),
            "percentile": self._percentile.value(),
            "parallel": self._parallel_chk.isChecked(),
            "max_workers": self._workers_spin.value(),
            "seed": seed,
        }
