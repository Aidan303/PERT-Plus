"""
PERT+ - Application entry point.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config.settings import Settings
from ui.main_window import MainWindow
from ui import theme as theme_module


def main() -> None:
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PERT+")
    app.setOrganizationName("PERTPlus")

    # Portable mode: settings.ini next to the executable
    exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    portable_ini = exe_dir / "settings.ini"
    portable = portable_ini.exists()

    settings = Settings(portable=portable, portable_dir=exe_dir if portable else None)

    # Apply theme before showing the window
    theme_module.apply_theme(settings.theme)

    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
