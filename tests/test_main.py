"""Tests for ``main``: startup, the platform arms and the ``__main__`` guard.

``QApplication`` is replaced by a fake because pytest-qt already owns the one
real application and PyQt6 refuses a second.
"""
import configparser
import runpy
import sys
from pathlib import Path

import pytest
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QApplication

import main

REPO_DIR = Path(__file__).resolve().parent.parent


class FakeApplication:
    """Stand-in for ``QApplication`` that records its use."""

    argv = None
    icon = None
    # pytest-qt calls QApplication.instance() after the test body.
    instance = staticmethod(QApplication.instance)

    def __init__(self, argv):
        FakeApplication.argv = list(argv)

    def setWindowIcon(self, icon):  # noqa: N802 - Qt naming
        """Record the icon."""
        FakeApplication.icon = icon

    def exec(self):
        """Return a recognisable exit status."""
        return 7


class StubWidget:
    """Stand-in for ``CubeWidget``."""

    def __init__(self):
        self.shown = False

    def show(self):
        """Record the call."""
        self.shown = True


@pytest.fixture
def run_main(monkeypatch, qapp):
    """Return a function running ``main.main`` with the given argv.

    ``qapp`` is requested because ``QIcon`` needs a real application. The function returns ``(status, widget, timers)``.
    """
    FakeApplication.argv = None
    FakeApplication.icon = None
    widgets = []
    timers = []

    def make_widget():
        widgets.append(StubWidget())
        return widgets[-1]

    monkeypatch.setattr(main, "QApplication", FakeApplication)
    monkeypatch.setattr(main, "CubeWidget", make_widget)
    monkeypatch.setattr(
        main.QTimer, "singleShot",
        lambda ms, func: timers.append((ms, func)))

    def run(argv, platform):
        monkeypatch.setattr(main.sys, "argv", argv)
        monkeypatch.setattr(main.sys, "platform", platform)
        return main.main(), widgets[0], timers

    return run


def test_darwin_requests_41_core(run_main):
    """On macOS the default format is a 4.1 core profile."""
    status, widget, timers = run_main(["prog"], "darwin")
    fmt = QSurfaceFormat.defaultFormat()
    assert status == 7
    assert (fmt.majorVersion(), fmt.minorVersion()) == (4, 1)
    assert fmt.profile() == QSurfaceFormat.OpenGLContextProfile.CoreProfile
    assert widget.shown
    assert timers == []
    assert FakeApplication.argv == ["prog"]
    assert FakeApplication.icon is not None


def test_linux_requests_es_31(run_main):
    """Elsewhere the default format is OpenGL ES 3.1."""
    status, _, timers = run_main(["prog"], "linux")
    fmt = QSurfaceFormat.defaultFormat()
    assert status == 7
    assert fmt.renderableType() == QSurfaceFormat.RenderableType.OpenGLES
    assert (fmt.majorVersion(), fmt.minorVersion()) == (3, 1)
    assert timers == []


def test_check_registers_selftest_timer(run_main, monkeypatch):
    """``--check`` schedules the self-test on the widget after 1000 ms."""
    status, widget, timers = run_main(["prog", "--check"], "darwin")
    assert status == 7
    assert len(timers) == 1
    assert timers[0][0] == 1000
    received = []
    monkeypatch.setattr(main.selftest, "check", received.append)
    timers[0][1]()
    assert received == [widget]


def test_icon_path_exists():
    """The application icon is where ``ICON_PATH`` says."""
    assert main.ICON_PATH == REPO_DIR / "icon.png"
    assert main.ICON_PATH.is_file()


def test_version_matches_bumpversion():
    """``__version__`` agrees with ``.bumpversion.cfg``."""
    cfg = configparser.ConfigParser()
    cfg.read(REPO_DIR / ".bumpversion.cfg")
    assert main.__version__ == cfg["bumpversion"]["current_version"]


def test_dunder_main_guard_exits_with_status(qapp, monkeypatch):
    """Running the file as a script exits with ``main()``'s status."""
    import widget  # noqa: F401 - must be in sys.modules to patch
    import PyQt6.QtWidgets as qtwidgets

    with monkeypatch.context() as m:
        m.setattr(qtwidgets, "QApplication", FakeApplication)
        m.setattr(sys.modules["widget"], "CubeWidget", StubWidget)
        m.setattr(sys, "argv", ["prog"])
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(
                str(REPO_DIR / "src" / "main.py"), run_name="__main__")
    assert excinfo.value.code == 7
