"""
Path generator panel — create a network PNG from an RCP file and highlight critical path.
"""
from __future__ import annotations

from typing import Any, Callable, Dict
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QPushButton, QSpinBox,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.image_preview_panel import ImagePreviewPanel
from ui.widgets.file_picker import FilePicker
import engine.path_generator as path_engine


class PathGeneratorPanel(ImagePreviewPanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            title="Path Generator",
            subtitle="Generate network PNGs from one or more RCP files and highlight each critical path.",
            settings=settings,
            job_manager=job_manager,
            save_prefix="path_graphics",
            parent=parent,
        )

    def _build_form(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)

        in_box = QGroupBox("Input")
        in_form = QFormLayout(in_box)
        self._rcp_picker = FilePicker(
            mode="files",
            filter_str="RCP Files (*.rcp);;All Files (*)",
            placeholder="Select one or more .rcp files",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("RCP file(s):", self._rcp_picker)
        root.addWidget(in_box)

        out_box = self._build_graphics_output_group(include_autosave_picker=False)
        out_form = out_box.layout()
        self._dpi = QSpinBox()
        self._dpi.setRange(72, 600)
        self._dpi.setValue(self._settings.graphics_dpi)
        out_form.addRow("Output DPI:", self._dpi)  # type: ignore[attr-defined]
        root.addWidget(out_box)

        self._add_generate_and_preview(
            root,
            button_text="Generate Path PNG",
            run_message="Running path generation for selected file(s)...",
        )

        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return path_engine.run_path_generator_batch

    def _collect_kwargs(self) -> Dict[str, Any]:
        if self._rcp_picker.path:
            first_path = self._rcp_picker.path.split(";")[0].strip()
            if first_path:
                self._settings.last_input_dir = str(Path(first_path).parent)
        self._settings.graphics_dpi = self._dpi.value()

        rcp_files = [p.strip() for p in self._rcp_picker.path.split(";") if p.strip()]
        return {
            "rcp_files": rcp_files,
            "output_dir": self._temp_output_dir_str(),
            "dpi": self._dpi.value(),
        }
