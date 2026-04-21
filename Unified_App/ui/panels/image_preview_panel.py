"""
Base panel for workflows that generate image artifacts.

Image artifacts are always generated to a temp directory and only persisted
when the user explicitly clicks Save Graphics.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Dict, Optional

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout

from ui.panels.base_panel import BasePanel
from ui.widgets.generated_image_preview import GeneratedImagePreview, HTML_EXTENSIONS, IMAGE_EXTENSIONS
from ui.widgets.file_picker import FilePicker


class ImagePreviewPanel(BasePanel):
    def __init__(
        self,
        title: str,
        subtitle: str,
        settings,
        job_manager,
        save_prefix: str,
        parent=None,
    ):
        self._save_prefix = save_prefix
        self._temp_output_dir: Optional[Path] = None
        self._preview_widget: Optional[GeneratedImagePreview] = None
        self._autosave_picker: Optional[FilePicker] = None
        super().__init__(title, subtitle, settings, job_manager, parent)

    def _build_graphics_output_group(
        self,
        include_autosave_picker: bool = False,
        autosave_placeholder: str = "Select autosave folder for non-image files",
        show_html_note: bool = False,
    ) -> QGroupBox:
        out_box = QGroupBox("Output")
        out_form = QFormLayout(out_box)
        out_form.addRow("Images:", QLabel("Generated to temp; click Save Graphics to keep"))
        if show_html_note:
            out_form.addRow("HTML:", QLabel("Not auto-saved and cannot be previewed"))
        if include_autosave_picker:
            self._autosave_picker = FilePicker(
                mode="folder",
                placeholder=autosave_placeholder,
                start_dir=self._settings.last_output_dir,
            )
            out_form.addRow("Autosave folder:", self._autosave_picker)
        return out_box

    def _add_generate_and_preview(self, root: QVBoxLayout, button_text: str, run_message: str) -> None:
        run_btn = QPushButton(button_text)
        run_btn.clicked.connect(lambda: self._start_generate_with_preview(run_message))
        root.addWidget(run_btn)
        root.addWidget(self._build_preview_widget(), stretch=1)

    def _build_preview_widget(self) -> GeneratedImagePreview:
        preview = GeneratedImagePreview(self._save_prefix)
        preview.status_message.connect(self.status_message.emit)
        self._preview_widget = preview
        return preview

    def _start_generate_with_preview(self, run_message: str) -> None:
        temp_dir = self._create_temp_output_dir()
        if self._preview_widget is not None:
            self._preview_widget.prepare_for_run(temp_dir, run_message)
        self.run_job()

    def _create_temp_output_dir(self) -> Path:
        self.cleanup_temp_outputs()
        self._temp_output_dir = Path(tempfile.mkdtemp(prefix=f"pert_{self._save_prefix}_"))
        return self._temp_output_dir

    def _temp_output_dir_str(self) -> str:
        if self._temp_output_dir is None:
            self._create_temp_output_dir()
        return str(self._temp_output_dir)

    def _resolve_result_output_dir(self, result: Any) -> Path:
        if isinstance(result, dict) and result.get("output_dir"):
            return Path(str(result.get("output_dir")))
        if isinstance(result, (str, Path)):
            return Path(result)
        if self._temp_output_dir is not None:
            return self._temp_output_dir
        raise ValueError("Unable to resolve output directory from result")

    def _autosave_non_image_artifacts(self, source_dir: Path, autosave_dir: Path) -> int:
        if not source_dir.exists():
            return 0
        autosave_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        ignore_ext = IMAGE_EXTENSIONS | HTML_EXTENSIONS
        for src in source_dir.rglob("*"):
            if not src.is_file():
                continue
            if src.suffix.lower() in ignore_ext:
                continue
            rel = src.relative_to(source_dir)
            dst = autosave_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
        return copied

    def _autosave_non_image_to_picker(self, out_dir: Path) -> int:
        if self._autosave_picker is None or not self._autosave_picker.path:
            return 0
        self._settings.last_output_dir = self._autosave_picker.path
        return self._autosave_non_image_artifacts(out_dir, Path(self._autosave_picker.path))

    def _on_finished(self, result: Any) -> None:
        super()._on_finished(result)
        if self._preview_widget is None:
            return
        out_dir = self._resolve_result_output_dir(result)
        self._preview_widget.load_from_output_dir(out_dir)

    def cleanup_temp_outputs(self) -> None:
        if self._preview_widget is not None:
            self._preview_widget.discard_temp_dir()
        elif self._temp_output_dir is not None and self._temp_output_dir.exists():
            shutil.rmtree(self._temp_output_dir, ignore_errors=True)
        self._temp_output_dir = None
