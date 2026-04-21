"""
Complexity measures panel — compute SP, TF, AD, LA from RCP files.
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
import engine.complexity_measures as cm_engine


def _batch_complexity(rcp_files, output_dir, progress_cb=None, cancel_check=None):
    """Compute complexity measures for a list of RCP files and save to CSV."""
    import pathlib, pandas as pd

    results = []
    total = len(rcp_files)
    for i, rcp in enumerate(rcp_files):
        if cancel_check and cancel_check():
            break
        if progress_cb:
            progress_cb(i, total, f"Processing {pathlib.Path(rcp).name}")
        sp, tf, ad, la = cm_engine.calculate_complexity_measures(rcp)
        results.append({
            "file": pathlib.Path(rcp).name,
            "SP": sp, "TF": tf, "AD": ad, "LA": la,
        })
    df = pd.DataFrame(results)
    out = pathlib.Path(output_dir) / "complexity_measures.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    if progress_cb:
        progress_cb(total, total, "Done")
    return out


class ComplexityMeasuresPanel(BasePanel):

    def __init__(self, settings: Settings, job_manager: JobManager, parent=None):
        super().__init__(
            "Complexity Measures",
            "Calculate SP, TF, AD, and LA complexity measures from RCP project files.",
            settings, job_manager, parent,
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

        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        self._out_picker = FilePicker(
            mode="folder",
            placeholder="Select output folder",
            start_dir=self._settings.last_output_dir,
        )
        out_form.addRow("Output folder:", self._out_picker)
        root.addWidget(out_box)

        run_btn = QPushButton("Calculate Complexity Measures")
        run_btn.clicked.connect(self.run_job)
        root.addWidget(run_btn)
        root.addStretch()
        return w

    def _engine_fn(self) -> Callable:
        return _batch_complexity

    def _collect_kwargs(self) -> Dict[str, Any]:
        rcp_files = [p.strip() for p in self._rcp_picker.path.split(";") if p.strip()]
        return {
            "rcp_files": rcp_files,
            "output_dir": self._out_picker.path,
        }
