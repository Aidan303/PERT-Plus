"""
Cluster graphics panel — bar chart summaries per cluster.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QSpinBox,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.image_preview_panel import ImagePreviewPanel
from ui.widgets.file_picker import FilePicker
import engine.cluster_graphics as cg_engine


class ClusterGraphicsPanel(ImagePreviewPanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            title="Cluster Summary Graphics",
            subtitle="Generate grouped bar charts summarising MAPE per cluster.",
            settings=settings,
            job_manager=job_manager,
            save_prefix="cluster_graphics",
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
            placeholder="Select cluster_summary.csv",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("Cluster summary CSV:", self._input_picker)
        root.addWidget(in_box)

        param_box = QGroupBox("Parameters")
        param_form = QFormLayout(param_box)
        self._dpi = QSpinBox(); self._dpi.setRange(72, 600); self._dpi.setValue(self._settings.graphics_dpi)
        param_form.addRow("Output DPI:", self._dpi)
        root.addWidget(param_box)

        out_box = self._build_graphics_output_group(include_autosave_picker=False)
        root.addWidget(out_box)

        self._add_generate_and_preview(
            root,
            button_text="Generate Cluster Graphics",
            run_message="Generating cluster graphics into temporary output...",
        )
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return cg_engine.run_cluster_graphics

    def _collect_kwargs(self) -> Dict[str, Any]:
        return {
            "input_csv": self._input_picker.path,
            "output_dir": self._temp_output_dir_str(),
            "dpi": self._dpi.value(),
        }
