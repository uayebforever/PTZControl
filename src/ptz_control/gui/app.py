import sys

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def run(camera_host: str | None = None) -> int:
    app = QApplication(sys.argv)
    window = MainWindow(camera_host=camera_host)
    window.show()
    return app.exec()
