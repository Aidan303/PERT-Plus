"""
Cluster effects panel — bootstrap effect-size analysis with forest plots.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.image_preview_panel import ImagePreviewPanel
from ui.widgets.file_picker import FilePicker
import engine.cluster_effects as ce_engine


class ClusterEffectsPanel(ImagePreviewPanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            title="Cluster Effect Size Analysis",
            subtitle="Compute bootstrap confidence intervals and forest plots for per-cluster paired effects.",
            settings=settings,
            job_manager=job_manager,
            save_prefix="cluster_effects",
            parent=parent,
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
            placeholder="Select network_clusters_row_level.csv",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("Cluster CSV:", self._input_picker)
        root.addWidget(in_box)

        param_box = QGroupBox("Parameters")
        param_form = QFormLayout(param_box)
        self._n_boot = QSpinBox(); self._n_boot.setRange(100, 100000); self._n_boot.setValue(self._settings.effect_n_bootstrap)
        self._ci = QDoubleSpinBox(); self._ci.setRange(0.5, 0.999); self._ci.setSingleStep(0.01); self._ci.setDecimals(3); self._ci.setValue(self._settings.effect_ci_level)
        self._dpi = QSpinBox(); self._dpi.setRange(72, 600); self._dpi.setValue(self._settings.graphics_dpi)
        param_form.addRow("Bootstrap samples:", self._n_boot)
        param_form.addRow("CI level:", self._ci)
        param_form.addRow("Output DPI:", self._dpi)
        root.addWidget(param_box)

        repro_box = QGroupBox("Reproducibility")
        repro_form = QFormLayout(repro_box)
        self._seed_chk = QCheckBox("Use fixed seed"); self._seed_chk.setChecked(self._settings.effect_fixed_seed)
        self._seed_val = QSpinBox(); self._seed_val.setRange(0, 999999); self._seed_val.setValue(self._settings.effect_seed_value)
        repro_form.addRow(self._seed_chk)
        repro_form.addRow("Seed:", self._seed_val)
        root.addWidget(repro_box)

        out_box = self._build_graphics_output_group(
            include_autosave_picker=True,
            autosave_placeholder="Select autosave folder for non-image files (CSV)",
        )
        root.addWidget(out_box)

        self._add_generate_and_preview(
            root,
            button_text="Run Effect Size Analysis",
            run_message="Running effect-size analysis and generating temporary graphics...",
        )
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return ce_engine.run_effect_size_analysis

    def _collect_kwargs(self) -> Dict[str, Any]:
        seed = self._seed_val.value() if self._seed_chk.isChecked() else None
        return {
            "input_csv": self._input_picker.path,
            "output_dir": self._temp_output_dir_str(),
            "n_bootstrap": self._n_boot.value(),
            "ci_level": self._ci.value(),
            "seed": seed,
            "dpi": self._dpi.value(),
        }

    def _on_finished(self, result: Any) -> None:
        out_dir = self._resolve_result_output_dir(result)
        copied = self._autosave_non_image_to_picker(out_dir)
        if copied and self._autosave_picker is not None:
            self._progress.append_log(f"Autosaved {copied} non-image artifact(s) to {self._autosave_picker.path}")
        super()._on_finished(result)
