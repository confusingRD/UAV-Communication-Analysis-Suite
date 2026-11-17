"""Time-boxed deployment compatibility smoke; not a UAV-CAS GUI."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6 import __version__ as pyside_version
from PySide6.QtWidgets import QApplication


def main() -> int:
    application = QApplication.instance() or QApplication([])
    figure = Figure(figsize=(2.0, 1.5))
    canvas = FigureCanvasQTAgg(figure)
    axis = figure.subplots()
    axis.plot([0.0, 1.0], [0.0, 1.0])
    canvas.draw()
    print(
        "Qt/Matplotlib smoke OK: "
        f"PySide6={pyside_version}, Matplotlib={matplotlib.__version__}, "
        f"canvas={canvas.width()}x{canvas.height()}"
    )
    application.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

