#!/usr/bin/env python3
"""Test OpenGL in Qt6 with a textured cube inside a sphere grid.

Each face of the cube has its own material. Colour and height are generated in
code, and a normal map is derived from the height, so no image files are
needed.

A latitude/longitude sphere and the +X, +Y and +Z axes are fixed to the cube.
The poles are on the Z axis, +X is at latitude 0, longitude 0 and +Y is at
latitude 0, longitude +90. A yellow dot on the sphere marks the direction to
the light.

Notes
-----
Mouse controls:

- Left-drag rotates the cube and sphere.
- Right-drag moves the light.
- Middle-drag pans.
- The wheel zooms.
- Double-click resets the view and the light.

Examples
--------
Open the window, which runs until it is closed::

    python3 src/main.py

Run the self-test, which simulates mouse input and then exits::

    python3 src/main.py --check
"""
import sys
from pathlib import Path

__version__ = "0.1.0"

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QSurfaceFormat
from PyQt6.QtWidgets import QApplication

import selftest
from widget import CubeWidget

ICON_PATH = Path(__file__).resolve().parent.parent / "icon.png"


def main():
    """Show the widget and run the application.

    Returns
    -------
    int
        The application's exit status.
    """
    if sys.platform == "darwin":
        # macOS only offers OpenGL 2.1 unless a core profile is requested,
        # and Qt needs the request in the default format before the
        # application exists so the shared context matches.
        surface = QSurfaceFormat()
        surface.setVersion(3, 2)
        surface.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        QSurfaceFormat.setDefaultFormat(surface)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    widget = CubeWidget()
    widget.show()
    if "--check" in sys.argv:
        QTimer.singleShot(1000, lambda: selftest.check(widget))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
