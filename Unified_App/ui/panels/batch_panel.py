"""
Batch simulation panel - run Monte Carlo simulation on all RCP files in a folder.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QComboBox,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.base_panel import BasePanel
from ui.widgets.file_picker import FilePicker
import engine.simulator as sim_engine


def _run_batch_from_folder(
    input_folder: str,
    output_dir: str,
    optimistic_scalar: float,
    pessimistic_scalar: float,
    distribution_type: str,
    num_simulations: int,
    percentile: float,
    parallel: bool,
    max_workers: int,
    seed: int | None = None,
    progress_cb=None,
    cancel_check=None,
):
    rcp_files = sim_engine.find_rcp_files(input_folder)
    return sim_engine.run_batch_simulation(
        rcp_files=rcp_files,
        output_dir=output_dir,
        optimistic_scalar=optimistic_scalar,
        pessimistic_scalar=pessimistic_scalar,
        distribution_types=[distribution_type],
        num_simulations=num_simulations,
        percentile=percentile,
        parallel=parallel,
        max_workers=max_workers,
        seed=seed,
        progress_cb=progress_cb,
        cancel_check=cancel_check,
    )


class BatchPanel(BasePanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            "Batch Simulation",
            "Run simulation for every RCP file discovered in a selected folder.",
            settings, job_manager, parent,
        )

    def _build_form(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)

        input_box = QGroupBox("Input")
        input_form = QFormLayout(input_box)
        self._folder_picker = FilePicker(
            mode="folder",
            placeholder="Select folder containing .rcp files",
            start_dir=self._settings.last_input_dir,
        )
        input_form.addRow("RCP folder:", self._folder_picker)
        root.addWidget(input_box)

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

        param_box = QGroupBox("Parameters")
        param_form = QFormLayout(param_box)
        self._n_sim = QSpinBox(); self._n_sim.setRange(100, 1_000_000); self._n_sim.setValue(self._settings.sim_num_simulations)
        self._opt_scalar = QDoubleSpinBox(); self._opt_scalar.setRange(0.01, 0.99); self._opt_scalar.setSingleStep(0.05); self._opt_scalar.setValue(self._settings.sim_optimistic_scalar)
        self._pes_scalar = QDoubleSpinBox(); self._pes_scalar.setRange(1.01, 10.0); self._pes_scalar.setSingleStep(0.1); self._pes_scalar.setValue(self._settings.sim_pessimistic_scalar)
        self._percentile = QDoubleSpinBox(); self._percentile.setRange(0.5, 0.9999); self._percentile.setSingleStep(0.001); self._percentile.setDecimals(4); self._percentile.setValue(self._settings.sim_percentile)
        param_form.addRow("Simulations:", self._n_sim)
        param_form.addRow("Optimistic scalar:", self._opt_scalar)
        param_form.addRow("Pessimistic scalar:", self._pes_scalar)
        param_form.addRow("Completion percentile:", self._percentile)
        root.addWidget(param_box)

        repro_box = QGroupBox("Reproducibility")
        repro_form = QFormLayout(repro_box)
        self._seed_chk = QCheckBox("Use fixed seed"); self._seed_chk.setChecked(self._settings.sim_fixed_seed)
        self._seed_val = QSpinBox(); self._seed_val.setRange(0, 999999); self._seed_val.setValue(self._settings.sim_seed_value)
        repro_form.addRow(self._seed_chk)
        repro_form.addRow("Seed value:", self._seed_val)
        root.addWidget(repro_box)

        batch_box = QGroupBox("Execution")
        batch_form = QFormLayout(batch_box)
        self._parallel_chk = QCheckBox("Run files in parallel")
        self._parallel_chk.setChecked(self._settings.batch_parallel)
        self._workers_spin = QSpinBox(); self._workers_spin.setRange(1, 32); self._workers_spin.setValue(self._settings.batch_max_workers)
        batch_form.addRow(self._parallel_chk)
        batch_form.addRow("Max workers:", self._workers_spin)
        root.addWidget(batch_box)

        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        self._out_picker = FilePicker(
            mode="folder",
            placeholder="Select output folder",
            start_dir=self._settings.last_output_dir,
        )
        out_form.addRow("Output folder:", self._out_picker)
        root.addWidget(out_box)

        run_btn = QPushButton("Run Batch")
        run_btn.clicked.connect(self.run_job)
        root.addWidget(run_btn)
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return _run_batch_from_folder

    def _collect_kwargs(self) -> Dict[str, Any]:
        selected_distribution = str(self._dist_combo.currentData())

        seed = self._seed_val.value() if self._seed_chk.isChecked() else None

        self._settings.sim_distribution = selected_distribution

        return {
            "input_folder": self._folder_picker.path,
            "output_dir": self._out_picker.path,
            "optimistic_scalar": self._opt_scalar.value(),
            "pessimistic_scalar": self._pes_scalar.value(),
            "distribution_type": selected_distribution,
            "num_simulations": self._n_sim.value(),
            "percentile": self._percentile.value(),
            "parallel": self._parallel_chk.isChecked(),
            "max_workers": self._workers_spin.value(),
            "seed": seed,
        }
