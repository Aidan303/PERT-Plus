"""
Progress panel: progress bar + log viewer + cancel / force-stop buttons.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QProgressBar,
    QPushButton, QPlainTextEdit, QLabel,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor


class ProgressPanel(QWidget):
    """
    Reusable panel displayed beneath each action panel while a job runs.

    Signals:
        cancel_requested()
        force_stop_requested()
    """

    cancel_requested = Signal()
    force_stop_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Status label
        self._status_label = QLabel("Idle")
        layout.addWidget(self._status_label)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        layout.addWidget(self._bar)

        # Log output
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(180)
        self._log.setPlaceholderText("Output will appear here...")
        layout.addWidget(self._log)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addStretch()

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setObjectName("btnSecondary")
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._btn_cancel)

        self._btn_force = QPushButton("Force Stop")
        self._btn_force.setObjectName("btnDanger")
        self._btn_force.setEnabled(False)
        self._btn_force.setVisible(False)
        self._btn_force.clicked.connect(self._on_force_stop)
        btn_row.addWidget(self._btn_force)

        layout.addLayout(btn_row)

        self._cancel_requested_once = False

    # ── Slot: update progress ─────────────────────────────────────────────────

    def update_progress(self, current: int, total: int, message: str) -> None:
        if total > 0:
            self._bar.setRange(0, total)
            self._bar.setValue(current)
        else:
            self._bar.setRange(0, 0)  # indeterminate
        self._status_label.setText(message)

    def append_log(self, message: str) -> None:
        self._log.appendPlainText(message)
        self._log.moveCursor(QTextCursor.MoveOperation.End)

    # ── State management ──────────────────────────────────────────────────────

    def set_running(self, running: bool) -> None:
        self._btn_cancel.setEnabled(running)
        self._btn_force.setEnabled(running)
        self._btn_force.setVisible(running)
        if not running:
            self._cancel_requested_once = False

    def clear(self) -> None:
        self._log.clear()
        self._bar.setValue(0)
        self._bar.setRange(0, 100)
        self._status_label.setText("Idle")
        self._cancel_requested_once = False

    # ── Button handlers ───────────────────────────────────────────────────────

    def _on_cancel(self) -> None:
        if self._cancel_requested_once:
            # User is pressing cancel a second time - show force-stop context.
            self.append_log("[Warning] Cancel requested - press 'Force Stop' to terminate immediately.")
            self._btn_force.setVisible(True)
        else:
            self._cancel_requested_once = True
            self.append_log("[Info] Cancel requested - finishing current step...")
            self.cancel_requested.emit()

    def _on_force_stop(self) -> None:
        self.append_log("[Warning] Force-stopping job.")
        self.force_stop_requested.emit()
