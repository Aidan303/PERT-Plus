"""
Analysis panel — runs percent-error analysis on simulation CSVs.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QPushButton,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.base_panel import BasePanel
from ui.widgets.file_picker import FilePicker
import engine.analysis as analysis_engine


class AnalysisPanel(BasePanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            "Percent-Error Analysis",
            "Compute estimation error metrics from simulation output CSV files.",
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
            placeholder="Select simulation results CSV, or select a folder for batch",
            start_dir=self._settings.last_input_dir,
        )
        self._folder_picker = FilePicker(
            label="— OR batch folder —",
            mode="folder",
            placeholder="Select folder containing simulation CSVs",
            start_dir=self._settings.last_input_dir,
        )
        in_form.addRow("Single CSV:", self._input_picker)
        in_form.addRow(self._folder_picker)
        root.addWidget(in_box)

        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        self._out_picker = FilePicker(
            mode="folder",
            placeholder="Select output folder",
            start_dir=self._settings.last_output_dir,
        )
        out_form.addRow("Output folder:", self._out_picker)
        root.addWidget(out_box)

        run_btn = QPushButton("Run Analysis")
        run_btn.clicked.connect(self.run_job)
        root.addWidget(run_btn)
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        # If a folder is given, use batch mode
        if self._folder_picker.path:
            return analysis_engine.process_batch_folder
        return analysis_engine.run_analysis

    def _collect_kwargs(self) -> Dict[str, Any]:
        if self._folder_picker.path:
            return {
                "batch_folder": self._folder_picker.path,
                "output_dir": self._out_picker.path,
            }
        return {
            "input_csv": self._input_picker.path,
            "output_dir": self._out_picker.path,
        }
