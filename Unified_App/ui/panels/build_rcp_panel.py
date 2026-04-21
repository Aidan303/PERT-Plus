"""
Build RCP panel — convert Excel project workbook to RCP format.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QPushButton,
    QLineEdit,
)

from config.settings import Settings
from worker.job_runner import JobManager
from ui.panels.base_panel import BasePanel
from ui.widgets.file_picker import FilePicker
import engine.build_rcp as rcp_engine


class BuildRCPPanel(BasePanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            "Build RCP File",
            "Convert an Excel project workbook (.xlsx) into an RCP project file.",
            settings, job_manager, parent,
        )

    def _build_form(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)

        in_box = QGroupBox("Input")
        in_form = QFormLayout(in_box)
        self._xlsx_picker = FilePicker(
            mode="file",
            filter_str="Excel Files (*.xlsx *.xlsm);;All Files (*)",
            placeholder="Select project Excel workbook",
            start_dir=self._settings.last_input_dir,
        )
        self._sheet_name = QLineEdit()
        self._sheet_name.setPlaceholderText("Baseline (leave blank to use default)")
        in_form.addRow("Excel workbook:", self._xlsx_picker)
        in_form.addRow("Baseline sheet name:", self._sheet_name)
        root.addWidget(in_box)

        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        self._out_filename = QLineEdit()
        self._out_filename.setPlaceholderText("output.rcp (leave blank to auto-name)")
        self._out_picker = FilePicker(
            mode="folder",
            placeholder="Select output folder",
            start_dir=self._settings.last_output_dir,
        )
        out_form.addRow("Output filename:", self._out_filename)
        out_form.addRow("Output folder:", self._out_picker)
        root.addWidget(out_box)

        run_btn = QPushButton("Build RCP")
        run_btn.clicked.connect(self.run_job)
        root.addWidget(run_btn)
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return rcp_engine.run_build_rcp

    def _collect_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "project_path": self._xlsx_picker.path,
            "output_dir": self._out_picker.path,
        }
        if self._out_filename.text().strip():
            kwargs["output_filename"] = self._out_filename.text().strip()
        if self._sheet_name.text().strip():
            kwargs["baseline_sheet"] = self._sheet_name.text().strip()
        return kwargs
