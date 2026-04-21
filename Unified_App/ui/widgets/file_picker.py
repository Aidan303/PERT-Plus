"""
Reusable file / folder picker widget.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QVBoxLayout,
)
from PySide6.QtCore import Signal


class FilePicker(QWidget):
    """
    A label + line edit + browse button for picking a single file or folder.

    Signals:
        path_changed(str)  -- emitted whenever the path changes
    """

    path_changed = Signal(str)

    def __init__(
        self,
        label: str = "",
        mode: str = "file",          # "file", "files", or "folder"
        filter_str: str = "All Files (*)",
        placeholder: str = "",
        start_dir: str = "",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._mode = mode
        self._filter = filter_str
        self._start_dir = start_dir

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        if label:
            lbl = QLabel(label)
            layout.addWidget(lbl)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.textChanged.connect(self.path_changed)
        row.addWidget(self._edit)

        btn = QPushButton("Browse...")
        btn.setObjectName("btnSecondary")
        btn.setFixedWidth(96)
        btn.setStyleSheet("padding-left: 14px; padding-right: 10px;")
        btn.clicked.connect(self._browse)
        row.addWidget(btn)
        layout.addLayout(row)

    # ── Public API ─────────────────────────────────────────────────────────────
    @property
    def path(self) -> str:
        return self._edit.text().strip()

    @path.setter
    def path(self, value: str) -> None:
        self._edit.setText(value)

    def set_start_dir(self, directory: str) -> None:
        self._start_dir = directory

    # ── Browse dialog ──────────────────────────────────────────────────────────
    def _browse(self) -> None:
        start = self._start_dir or self._edit.text() or ""

        if self._mode == "folder":
            result = QFileDialog.getExistingDirectory(self, "Select Folder", start)
            if result:
                self._edit.setText(result)
                self._start_dir = result

        elif self._mode == "files":
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Files", start, self._filter
            )
            if paths:
                self._edit.setText(";".join(paths))
                self._start_dir = str(Path(paths[0]).parent)

        else:  # single file
            path, _ = QFileDialog.getOpenFileName(
                self, "Select File", start, self._filter
            )
            if path:
                self._edit.setText(path)
                self._start_dir = str(Path(path).parent)
