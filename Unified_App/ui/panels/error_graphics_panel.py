"""
Error graphics panel — generates estimation-error charts from analysis JSON files.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.image_preview_panel import ImagePreviewPanel
from ui.widgets.file_picker import FilePicker
import engine.error_graphics as eg_engine


class ErrorGraphicsPanel(ImagePreviewPanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            title="Error Analysis Graphics",
            subtitle="Generate estimation-error charts from analysis JSON file(s).",
            settings=settings,
            job_manager=job_manager,
            save_prefix="error_graphics",
            parent=parent,
        )

    def _build_form(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)

        in_box = QGroupBox("Input (JSON file or folder)")
        in_form = QFormLayout(in_box)
        self._input_picker = FilePicker(
            mode="file",
            filter_str="JSON Files (*.json);;All Files (*)",
            placeholder="Select an analysis JSON file or a folder of JSON files",
            start_dir=self._settings.last_input_dir,
        )
        self._folder_picker = FilePicker(
            label="— OR folder of JSON files —",
            mode="folder",
            placeholder="Folder with analysis JSON files",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("JSON file:", self._input_picker)
        in_form.addRow(self._folder_picker)
        root.addWidget(in_box)

        out_box = self._build_graphics_output_group(include_autosave_picker=False)
        root.addWidget(out_box)

        self._add_generate_and_preview(
            root,
            button_text="Generate Graphics",
            run_message="Generating error graphics into temporary output...",
        )
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return eg_engine.run_error_graphics

    def _collect_kwargs(self) -> Dict[str, Any]:
        input_path = self._folder_picker.path or self._input_picker.path
        return {
            "input_path": input_path,
            "output_dir": self._temp_output_dir_str(),
        }
