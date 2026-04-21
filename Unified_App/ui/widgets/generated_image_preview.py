"""
Reusable preview box for generated image artifacts.

Features:
- In-window image preview with carousel controls
- Temp session save/discard controls
- Optional HTML note for non-previewable artifacts
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
from typing import Iterable, List, Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
HTML_EXTENSIONS = {".html", ".htm"}


class GeneratedImagePreview(QGroupBox):
    status_message = Signal(str)

    def __init__(self, save_prefix: str, parent: Optional[QWidget] = None):
        super().__init__("Preview", parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._save_prefix = save_prefix
        self._temp_dir: Optional[Path] = None
        self._image_paths: List[Path] = []
        self._html_paths: List[Path] = []
        self._current_index = 0
        self._original_pixmap: Optional[QPixmap] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self._preview_info = QLabel("Generate output to preview images here.")
        self._preview_info.setObjectName("sectionSubtitle")
        self._preview_info.setWordWrap(True)
        root.addWidget(self._preview_info)

        nav_row = QHBoxLayout()
        self._prev_btn = QPushButton("<")
        self._prev_btn.setObjectName("btnSecondary")
        self._prev_btn.setFixedWidth(36)
        self._prev_btn.clicked.connect(self._show_previous)
        self._next_btn = QPushButton(">")
        self._next_btn.setObjectName("btnSecondary")
        self._next_btn.setFixedWidth(36)
        self._next_btn.clicked.connect(self._show_next)
        self._index_label = QLabel("Image 0 of 0")
        self._index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_row.addWidget(self._prev_btn)
        nav_row.addWidget(self._index_label, stretch=1)
        nav_row.addWidget(self._next_btn)
        root.addLayout(nav_row)

        self._preview_label = QLabel("No image generated yet")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumHeight(320)
        # Ignore pixmap width hint to avoid runaway growth, but expand vertically for visibility.
        self._preview_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self._preview_label.setStyleSheet("border: 1px solid #888888; padding: 6px;")
        root.addWidget(self._preview_label, stretch=1)

        action_row = QHBoxLayout()
        self._save_btn = QPushButton("Save Graphics")
        self._save_btn.setObjectName("btnPrimary")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_session)
        self._discard_btn = QPushButton("Don't Save")
        self._discard_btn.setObjectName("btnSecondary")
        self._discard_btn.setEnabled(False)
        self._discard_btn.clicked.connect(self._discard_session)
        self._open_temp_btn = QPushButton("Open Temp Folder")
        self._open_temp_btn.setObjectName("btnSecondary")
        self._open_temp_btn.setEnabled(False)
        self._open_temp_btn.clicked.connect(self._open_temp_folder)
        action_row.addWidget(self._save_btn)
        action_row.addWidget(self._discard_btn)
        action_row.addWidget(self._open_temp_btn)
        root.addLayout(action_row)

        self._update_nav_buttons()

    def prepare_for_run(self, temp_dir: Path, run_message: str) -> None:
        self.discard_temp_dir()
        self._temp_dir = temp_dir
        self._image_paths = []
        self._html_paths = []
        self._current_index = 0
        self._original_pixmap = None
        self._preview_label.setPixmap(QPixmap())
        self._preview_label.setText("Generating images...")
        self._preview_info.setText(run_message)
        self._index_label.setText("Image 0 of 0")
        self._set_session_actions_enabled(False)
        self._update_nav_buttons()

    def load_from_output_dir(self, output_dir: Path) -> None:
        self._temp_dir = output_dir
        self._image_paths = self._find_artifacts(output_dir, IMAGE_EXTENSIONS)
        self._html_paths = self._find_artifacts(output_dir, HTML_EXTENSIONS)
        self._current_index = 0

        has_artifacts = bool(self._image_paths or self._html_paths)
        self._set_session_actions_enabled(has_artifacts)

        if not has_artifacts:
            self._preview_label.setPixmap(QPixmap())
            self._preview_label.setText("No previewable images were generated.")
            self._preview_info.setText("No image or HTML artifacts were found in this run.")
            self._index_label.setText("Image 0 of 0")
            self._update_nav_buttons()
            return

        details = [f"Generated {len(self._image_paths)} image(s)"]
        if self._html_paths:
            details.append(f"{len(self._html_paths)} HTML file(s) cannot be previewed")
        details.append(f"Temp folder: {output_dir}")
        self._preview_info.setText(" | ".join(details))

        if self._image_paths:
            self._show_image(0)
        else:
            self._preview_label.setPixmap(QPixmap())
            self._preview_label.setText("HTML output cannot be previewed.")
            self._index_label.setText("Image 0 of 0")
            self._update_nav_buttons()

    def discard_temp_dir(self) -> None:
        if self._temp_dir is not None and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        self._temp_dir = None
        self._image_paths = []
        self._html_paths = []
        self._current_index = 0
        self._original_pixmap = None
        self._preview_label.setPixmap(QPixmap())
        self._preview_label.setText("No image generated yet")
        self._preview_info.setText("Generate output to preview images here.")
        self._index_label.setText("Image 0 of 0")
        self._set_session_actions_enabled(False)
        self._update_nav_buttons()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh_preview_pixmap()

    def _find_artifacts(self, folder: Path, extensions: Iterable[str]) -> List[Path]:
        exts = {e.lower() for e in extensions}
        return sorted([p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in exts])

    def _save_session(self) -> None:
        if self._temp_dir is None or not self._temp_dir.exists():
            self.status_message.emit("No temp output available to save")
            return
        if not (self._image_paths or self._html_paths):
            self.status_message.emit("No image/HTML artifacts to save")
            return

        destination_root = QFileDialog.getExistingDirectory(self, "Choose Save Folder")
        if not destination_root:
            return

        target_root = Path(destination_root)
        base_name = f"{self._save_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        target_dir = target_root / base_name
        suffix = 1
        while target_dir.exists():
            target_dir = target_root / f"{base_name}_{suffix}"
            suffix += 1
        target_dir.mkdir(parents=True, exist_ok=True)

        copied = 0
        for src in [*self._image_paths, *self._html_paths]:
            rel = src.relative_to(self._temp_dir)
            dst = target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1

        self.status_message.emit(f"Saved {copied} artifact(s) to: {target_dir}")

    def _discard_session(self) -> None:
        self.discard_temp_dir()
        self.status_message.emit("Temporary graphics discarded")

    def _open_temp_folder(self) -> None:
        if self._temp_dir is None or not self._temp_dir.exists():
            self.status_message.emit("Temp folder is not available")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._temp_dir)))

    def _set_session_actions_enabled(self, enabled: bool) -> None:
        self._save_btn.setEnabled(enabled)
        self._discard_btn.setEnabled(enabled)
        self._open_temp_btn.setEnabled(enabled)

    def _show_image(self, index: int) -> None:
        if not self._image_paths:
            self._preview_label.setPixmap(QPixmap())
            self._preview_label.setText("No image generated yet")
            self._index_label.setText("Image 0 of 0")
            self._original_pixmap = None
            self._update_nav_buttons()
            return

        self._current_index = max(0, min(index, len(self._image_paths) - 1))
        img_path = self._image_paths[self._current_index]
        pixmap = QPixmap(str(img_path))
        if pixmap.isNull():
            self._preview_label.setPixmap(QPixmap())
            self._preview_label.setText("Failed to load selected image.")
            self._original_pixmap = None
        else:
            self._original_pixmap = pixmap
            self._refresh_preview_pixmap()

        self._index_label.setText(f"Image {self._current_index + 1} of {len(self._image_paths)}")
        self._update_nav_buttons()

    def _refresh_preview_pixmap(self) -> None:
        if self._original_pixmap is None or self._original_pixmap.isNull():
            return
        target = self._preview_label.contentsRect().size()
        if target.width() <= 1 or target.height() <= 1:
            return
        scaled = self._original_pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview_label.setPixmap(scaled)

    def _show_previous(self) -> None:
        if self._image_paths and self._current_index > 0:
            self._show_image(self._current_index - 1)

    def _show_next(self) -> None:
        if self._image_paths and self._current_index < len(self._image_paths) - 1:
            self._show_image(self._current_index + 1)

    def _update_nav_buttons(self) -> None:
        total = len(self._image_paths)
        self._prev_btn.setEnabled(total > 1 and self._current_index > 0)
        self._next_btn.setEnabled(total > 1 and self._current_index < total - 1)
