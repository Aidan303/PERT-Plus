"""
PCA panel — principal component analysis on network features.
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
import engine.pca_analysis as pca_engine


class PCAPanel(ImagePreviewPanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            title="PCA Analysis",
            subtitle="Perform principal component analysis on network complexity features.",
            settings=settings,
            job_manager=job_manager,
            save_prefix="pca_graphics",
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
            placeholder="Select network features CSV",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("Features CSV:", self._input_picker)
        root.addWidget(in_box)

        param_box = QGroupBox("Parameters")
        param_form = QFormLayout(param_box)
        self._var = QDoubleSpinBox(); self._var.setRange(0.5, 0.9999); self._var.setSingleStep(0.01); self._var.setDecimals(4); self._var.setValue(self._settings.pca_variance_threshold)
        self._dpi = QSpinBox(); self._dpi.setRange(72, 600); self._dpi.setValue(self._settings.pca_dpi)
        param_form.addRow("Variance threshold:", self._var)
        param_form.addRow("Output DPI:", self._dpi)
        root.addWidget(param_box)

        repro_box = QGroupBox("Reproducibility")
        repro_form = QFormLayout(repro_box)
        self._seed_chk = QCheckBox("Use fixed seed"); self._seed_chk.setChecked(self._settings.pca_fixed_seed)
        self._seed_val = QSpinBox(); self._seed_val.setRange(0, 999999); self._seed_val.setValue(self._settings.pca_seed_value)
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
            button_text="Run PCA",
            run_message="Running PCA and generating temporary graphics...",
        )
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return pca_engine.run_pca

    def _collect_kwargs(self) -> Dict[str, Any]:
        seed = self._seed_val.value() if self._seed_chk.isChecked() else None

        self._settings.pca_variance_threshold = self._var.value()
        self._settings.pca_dpi = self._dpi.value()
        self._settings.pca_fixed_seed = self._seed_chk.isChecked()
        self._settings.pca_seed_value = self._seed_val.value()

        return {
            "input_csv": self._input_picker.path,
            "output_dir": self._temp_output_dir_str(),
            "variance_threshold": self._var.value(),
            "dpi": self._dpi.value(),
            "random_state": seed,
        }

    def _on_finished(self, result: Any) -> None:
        out_dir = self._resolve_result_output_dir(result)
        copied = self._autosave_non_image_to_picker(out_dir)
        if copied and self._autosave_picker is not None:
            self._progress.append_log(f"Autosaved {copied} non-image artifact(s) to {self._autosave_picker.path}")
        super()._on_finished(result)
