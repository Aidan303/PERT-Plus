"""
Base class for all action panels in PERT+.

Each panel:
  - Builds its own form controls
  - Knows how to collect kwargs for the engine function
  - Calls self.run_job() to dispatch work
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QSizePolicy, QGroupBox,
)
from PySide6.QtCore import Qt, Signal

from config.settings import Settings
from worker.job_runner import JobWorker, JobManager
from ui.widgets.progress_panel import ProgressPanel


class BasePanel(QWidget):
    """
    Subclasses implement:
        _build_form() -> QWidget  (the scrollable form)
        _collect_kwargs() -> dict   (arguments for the engine function)
        _engine_fn() -> Callable  (the engine function to call)
        _on_finished(result)       (called on success)
    """

    status_message = Signal(str)

    def __init__(
        self,
        title: str,
        subtitle: str,
        settings: Settings,
        job_manager: JobManager,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._settings = settings
        self._job_manager = job_manager
        self._worker: Optional[JobWorker] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        # Header
        title_lbl = QLabel(title)
        title_lbl.setObjectName("sectionTitle")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setObjectName("sectionSubtitle")
        root.addWidget(title_lbl)
        root.addWidget(sub_lbl)

        # Scrollable form area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        form_widget = self._build_form()
        self._compact_output_groups(form_widget)
        scroll.setWidget(form_widget)
        root.addWidget(scroll, stretch=1)

        # Progress panel (always at the bottom)
        self._progress = ProgressPanel()
        self._progress.cancel_requested.connect(self._on_cancel)
        self._progress.force_stop_requested.connect(self._on_force_stop)
        root.addWidget(self._progress)

    # ── To be implemented by subclasses ──────────────────────────────────────

    def _build_form(self) -> QWidget:
        raise NotImplementedError

    def _collect_kwargs(self) -> Dict[str, Any]:
        raise NotImplementedError

    def _engine_fn(self) -> Callable:
        raise NotImplementedError

    def _on_finished(self, result: Any) -> None:
        self._progress.append_log(f"Done -> {result}")
        self._progress.set_running(False)
        self.status_message.emit("Done")

    # ── Job dispatch ──────────────────────────────────────────────────────────

    def run_job(self) -> None:
        kwargs = self._collect_kwargs()
        worker = JobWorker(self._engine_fn(), kwargs)
        worker.progress_updated.connect(self._progress.update_progress)
        worker.log_updated.connect(self._progress.append_log)
        worker.finished.connect(self._on_finished)
        worker.error_occurred.connect(self._on_error)
        self._worker = worker
        self._progress.clear()
        self._progress.set_running(True)
        self._job_manager.submit(worker)
        self.status_message.emit("Running...")

    # ── Cancel ────────────────────────────────────────────────────────────────

    def _on_cancel(self) -> None:
        self._job_manager.cancel_current()

    def _on_force_stop(self) -> None:
        self._job_manager.force_stop_current()
        self._progress.set_running(False)

    def _on_error(self, message: str) -> None:
        self._progress.append_log(f"[ERROR] {message}")
        self._progress.set_running(False)
        self.status_message.emit("Error")

    def _compact_output_groups(self, form_widget: QWidget) -> None:
        for box in form_widget.findChildren(QGroupBox):
            if box.title().strip().lower().startswith("output"):
                layout = box.layout()
                if layout is not None:
                    layout.setContentsMargins(8, 6, 8, 6)
                    layout.setSpacing(4)
                hinted = box.sizeHint().height()
                box.setMaximumHeight(max(72, int(hinted * 0.88)))
