"""
Main application window for PERT+.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QStatusBar, QToolBar, QPushButton, QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent

from config.settings import Settings
from worker.job_runner import JobManager
from ui import theme as theme_module
from ui.widgets.preferences_dialog import PreferencesDialog

# Action panels
from ui.panels.simulation_panel import SimulationPanel
from ui.panels.analysis_panel import AnalysisPanel
from ui.panels.error_graphics_panel import ErrorGraphicsPanel
from ui.panels.clustering_panel import ClusteringPanel
from ui.panels.cluster_effects_panel import ClusterEffectsPanel
from ui.panels.cluster_graphics_panel import ClusterGraphicsPanel
from ui.panels.pca_panel import PCAPanel
from ui.panels.complexity_viz_panel import ComplexityVizPanel
from ui.panels.build_rcp_panel import BuildRCPPanel
from ui.panels.complexity_measures_panel import ComplexityMeasuresPanel
from ui.panels.path_generator_panel import PathGeneratorPanel
from ui.panels.batch_panel import BatchPanel


_NAV_ITEMS = [
    ("Monte Carlo Simulation",   SimulationPanel),
    ("Percent-Error Analysis",   AnalysisPanel),
    ("Error Graphics",           ErrorGraphicsPanel),
    ("Clustering Analysis",      ClusteringPanel),
    ("Cluster Effect Sizes",     ClusterEffectsPanel),
    ("Cluster Graphics",         ClusterGraphicsPanel),
    ("PCA Analysis",             PCAPanel),
    ("Complexity Visualizer",    ComplexityVizPanel),
    ("Complexity Measures",      ComplexityMeasuresPanel),
    ("Path Generator",           PathGeneratorPanel),
    ("Batch Simulation",         BatchPanel),
    ("Build RCP",                BuildRCPPanel),
]


class MainWindow(QMainWindow):

    def __init__(self, settings: Settings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._settings = settings
        self._job_manager = JobManager()
        self._current_theme = settings.theme

        self.setWindowTitle("PERT+")
        self.setMinimumSize(960, 680)

        self._build_toolbar()
        self._build_statusbar()
        self._build_central()

        # Apply persisted theme
        theme_module.apply_theme(self._current_theme)
        self._update_theme_btn_label()

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        tb.setFloatable(False)

        app_label = QLabel("  PERT+  ")
        app_label.setObjectName("sectionTitle")
        tb.addWidget(app_label)

        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy(),
            spacer.sizePolicy().verticalPolicy(),
        )
        from PySide6.QtWidgets import QSizePolicy
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self._theme_btn = QPushButton("Light")
        self._theme_btn.setObjectName("btnSecondary")
        self._theme_btn.setFixedWidth(90)
        self._theme_btn.clicked.connect(self._toggle_theme)
        tb.addWidget(self._theme_btn)

        prefs_btn = QPushButton("Preferences")
        prefs_btn.setObjectName("btnSecondary")
        prefs_btn.clicked.connect(self._open_preferences)
        tb.addWidget(prefs_btn)

        self.addToolBar(tb)

    # ── Central layout (sidebar + stacked pages) ──────────────────────────────

    def _build_central(self) -> None:
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Sidebar nav list
        self._nav = QListWidget()
        self._nav.setFixedWidth(210)
        self._nav.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for label, _ in _NAV_ITEMS:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._nav.addItem(item)
        self._nav.currentRowChanged.connect(self._switch_panel)
        h_layout.addWidget(self._nav)

        # Stacked panels
        self._stack = QStackedWidget()
        for _, PanelClass in _NAV_ITEMS:
            panel = PanelClass(self._settings, self._job_manager)
            panel.status_message.connect(self._show_status)
            self._stack.addWidget(panel)
        h_layout.addWidget(self._stack, stretch=1)

        self.setCentralWidget(container)
        self._nav.setCurrentRow(0)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self) -> None:
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _switch_panel(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        if hasattr(self, "_status_bar"):
            self._status_bar.showMessage("Ready")

    def _show_status(self, message: str) -> None:
        if hasattr(self, "_status_bar"):
            self._status_bar.showMessage(message)

    def _toggle_theme(self) -> None:
        self._current_theme = theme_module.toggle_theme(self._current_theme)
        self._settings.theme = self._current_theme
        self._settings.sync()
        theme_module.apply_theme(self._current_theme)
        self._update_theme_btn_label()

    def _update_theme_btn_label(self) -> None:
        if self._current_theme == "dark":
            self._theme_btn.setText("Light")
        else:
            self._theme_btn.setText("Dark")

    def _open_preferences(self) -> None:
        dlg = PreferencesDialog(self._settings, self)
        dlg.exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        for idx in range(self._stack.count()):
            panel = self._stack.widget(idx)
            cleanup = getattr(panel, "cleanup_temp_outputs", None)
            if callable(cleanup):
                cleanup()
        super().closeEvent(event)
