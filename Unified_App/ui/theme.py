"""
Light / dark theme manager for PERT+.
"""
from __future__ import annotations

from PySide6.QtWidgets import QApplication


LIGHT_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #f5f5f5;
    color: #1a1a1a;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
}
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #bbbbbb;
    border-radius: 3px;
    padding: 3px 6px;
    color: #1a1a1a;
}
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #bbbbbb;
    border-radius: 3px;
    color: #1a1a1a;
    padding: 2px 20px 2px 6px;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #2980b9;
}
QPushButton {
    background-color: #2980b9;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}
QPushButton:hover { background-color: #3498db; }
QPushButton:pressed { background-color: #1f6391; }
QPushButton:disabled { background-color: #aaaaaa; }
QPushButton#btnSecondary {
    background-color: #e0e0e0;
    color: #1a1a1a;
}
QPushButton#btnSecondary:hover { background-color: #cccccc; }
QPushButton#btnDanger {
    background-color: #c0392b;
}
QPushButton#btnDanger:hover { background-color: #e74c3c; }
QProgressBar {
    border: 1px solid #bbbbbb;
    border-radius: 4px;
    text-align: center;
    background-color: #e0e0e0;
}
QProgressBar::chunk { background-color: #2980b9; border-radius: 3px; }
QListWidget {
    background-color: #e8e8e8;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #d0d0d0;
}
QListWidget::item:selected {
    background-color: #2980b9;
    color: #ffffff;
}
QListWidget::item:hover:!selected { background-color: #d0d8e4; }
QScrollBar:vertical {
    background: #e8e8e8;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #b0b0b0;
    border-radius: 5px;
    min-height: 20px;
}
QTabWidget::pane { border: 1px solid #cccccc; }
QTabBar::tab {
    background-color: #e0e0e0;
    padding: 6px 14px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom: 2px solid #2980b9;
}
QLabel#sectionTitle {
    font-size: 16px;
    font-weight: bold;
    color: #2c3e50;
}
QLabel#sectionSubtitle {
    font-size: 12px;
    color: #666666;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
}
"""

DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
}
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 3px;
    padding: 3px 6px;
    color: #cdd6f4;
}
QSpinBox, QDoubleSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 3px;
    color: #cdd6f4;
    padding: 2px 20px 2px 6px;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #89b4fa;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}
QPushButton:hover { background-color: #b4befe; }
QPushButton:pressed { background-color: #7287fd; }
QPushButton:disabled { background-color: #45475a; color: #6c7086; }
QPushButton#btnSecondary {
    background-color: #45475a;
    color: #cdd6f4;
}
QPushButton#btnSecondary:hover { background-color: #585b70; }
QPushButton#btnDanger {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#btnDanger:hover { background-color: #eb6f92; }
QProgressBar {
    border: 1px solid #45475a;
    border-radius: 4px;
    text-align: center;
    background-color: #313244;
    color: #cdd6f4;
}
QProgressBar::chunk { background-color: #89b4fa; border-radius: 3px; }
QListWidget {
    background-color: #181825;
    border: none;
    outline: none;
    color: #cdd6f4;
}
QListWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #313244;
}
QListWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}
QListWidget::item:hover:!selected { background-color: #313244; }
QScrollBar:vertical {
    background: #181825;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 20px;
}
QTabWidget::pane { border: 1px solid #45475a; }
QTabBar::tab {
    background-color: #313244;
    padding: 6px 14px;
    color: #cdd6f4;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #1e1e2e;
    border-bottom: 2px solid #89b4fa;
}
QLabel#sectionTitle {
    font-size: 16px;
    font-weight: bold;
    color: #cba6f7;
}
QLabel#sectionSubtitle {
    font-size: 12px;
    color: #a6adc8;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
}
"""


def apply_theme(theme: str) -> None:
    """Apply 'light' or 'dark' theme to the running QApplication."""
    app = QApplication.instance()
    if app is None:
        return
    stylesheet = DARK_STYLESHEET if theme == "dark" else LIGHT_STYLESHEET
    app.setStyleSheet(stylesheet)


def toggle_theme(current: str) -> str:
    """Return the opposite theme name."""
    return "dark" if current == "light" else "light"
