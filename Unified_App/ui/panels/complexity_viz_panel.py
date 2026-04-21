"""
Complexity visualizer panel — 3D scatter / Plotly HTML from complexity CSV.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QSpinBox, QCheckBox, QLineEdit,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.image_preview_panel import ImagePreviewPanel
from ui.widgets.file_picker import FilePicker
import engine.complexity_viz as viz_engine


_DEFAULT_COLS = {
    "x": "SP",
    "y": "TF",
    "z": "AD",
    "color": "LA",
}


class ComplexityVizPanel(ImagePreviewPanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            title="Complexity Visualizer",
            subtitle="Generate 3D scatter plots (and optional interactive HTML) from complexity data.",
            settings=settings,
            job_manager=job_manager,
            save_prefix="complexity_viz",
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
            placeholder="Select complexity measures CSV",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("Complexity CSV:", self._input_picker)
        root.addWidget(in_box)

        col_box = QGroupBox("Axis / Color Columns")
        col_form = QFormLayout(col_box)
        self._x_col = QLineEdit(_DEFAULT_COLS["x"])
        self._y_col = QLineEdit(_DEFAULT_COLS["y"])
        self._z_col = QLineEdit(_DEFAULT_COLS["z"])
        self._color_col = QLineEdit(_DEFAULT_COLS["color"])
        col_form.addRow("X axis column:", self._x_col)
        col_form.addRow("Y axis column:", self._y_col)
        col_form.addRow("Z axis column:", self._z_col)
        col_form.addRow("Color column:", self._color_col)
        root.addWidget(col_box)

        opt_box = QGroupBox("Options")
        opt_form = QFormLayout(opt_box)
        self._html_chk = QCheckBox("Generate interactive HTML (requires Plotly)")
        self._html_chk.setChecked(False)
        self._dpi = QSpinBox(); self._dpi.setRange(72, 600); self._dpi.setValue(self._settings.graphics_dpi)
        opt_form.addRow(self._html_chk)
        opt_form.addRow("Output DPI:", self._dpi)
        root.addWidget(opt_box)

        out_box = self._build_graphics_output_group(include_autosave_picker=False, show_html_note=True)
        root.addWidget(out_box)

        self._add_generate_and_preview(
            root,
            button_text="Generate Visualization",
            run_message="Generating complexity visualizations into temporary output...",
        )
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return viz_engine.run_complexity_viz

    def _collect_kwargs(self) -> Dict[str, Any]:
        return {
            "input_csv": self._input_picker.path,
            "x_col": self._x_col.text().strip() or _DEFAULT_COLS["x"],
            "y_col": self._y_col.text().strip() or _DEFAULT_COLS["y"],
            "z_col": self._z_col.text().strip() or _DEFAULT_COLS["z"],
            "color_col": self._color_col.text().strip() or _DEFAULT_COLS["color"],
            "generate_html": self._html_chk.isChecked(),
            "dpi": self._dpi.value(),
            "output_dir": self._temp_output_dir_str(),
        }
