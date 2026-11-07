"""Tests for the self-test: event helpers, the pass path and the fail path."""
import pytest
from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QColor, QImage

import selftest
from context import SceneContext
from widget import CubeWidget


class Recorder(QObject):
    """Records every mouse and wheel event it receives."""

    def __init__(self):
        super().__init__()
        self.events = []

    def event(self, event):
        """Record ``event`` and accept it."""
        self.events.append(event.clone())
        return True

    def width(self):
        """Return a fixed width."""
        return 200

    def height(self):
        """Return a fixed height."""
        return 100


class BlackWidget(Recorder):
    """Stub widget whose every frame is the same black image."""

    def __init__(self):
        super().__init__()
        self.ctx = SceneContext()

    def grabFramebuffer(self):
        """Return a constant black image."""
        image = QImage(8, 8, QImage.Format.Format_RGB32)
        image.fill(QColor(0, 0, 0))
        return image


@pytest.fixture
def exit_codes(monkeypatch):
    """Replace ``QApplication.exit`` with a recorder and return its list."""
    codes = []
    monkeypatch.setattr(selftest.QApplication, "exit", codes.append)
    return codes


def test_send_drag_delivers_press_move_release(qtbot):
    """A drag is a press at the centre, a move, then a release.

    ``--check`` drives the widget only through these synthetic events. If the
    helper sent the wrong button or position, the self-test would measure
    nothing.
    """
    target = Recorder()
    selftest.send_drag(target, Qt.MouseButton.RightButton, 20, -10)
    kinds = [event.type() for event in target.events]
    assert kinds == [
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseMove,
        QEvent.Type.MouseButtonRelease,
    ]
    press, move, release = target.events
    assert press.button() == Qt.MouseButton.RightButton
    assert move.buttons() == Qt.MouseButton.RightButton
    assert release.buttons() == Qt.MouseButton.NoButton
    assert (press.position().x(), press.position().y()) == (100.0, 50.0)
    assert (move.position().x(), move.position().y()) == (120.0, 40.0)


def test_send_wheel_delivers_notches(qtbot):
    """A wheel turn arrives as one event of 120 units per notch.

    Qt reports 120 units per wheel notch, and the widget converts back from
    those units.
    """
    target = Recorder()
    selftest.send_wheel(target, -2)
    (event,) = target.events
    assert event.type() == QEvent.Type.Wheel
    assert event.angleDelta().y() == -240


def test_check_passes_on_a_real_widget(qtbot, capsys, exit_codes):
    """The real self-test passes all six checks and exits with status 0.

    This runs ``--check`` inside pytest, so a self-test regression shows up in
    the suite and not only in a manual run.
    """
    window = CubeWidget()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    capsys.readouterr()
    selftest.check(window)
    lines = capsys.readouterr().out.splitlines()
    assert exit_codes == [0]
    assert lines == [
        "light dot: PASS",
        "rotate: PASS",
        "zoom: PASS",
        "light: PASS",
        "pan: PASS",
        "reset: PASS",
    ]


def test_check_fails_on_a_blank_widget(qapp, capsys, exit_codes):
    """Identical black frames fail every check and exit with status 1.

    A self-test that cannot fail proves nothing; this shows it reports FAIL and
    exits 1. The reset check compares the last frame with the first, so it
    passes when every frame is identical; this test records that limit.
    """
    selftest.check(BlackWidget())
    lines = capsys.readouterr().out.splitlines()
    assert exit_codes == [1]
    assert lines[0] == "light dot: FAIL"
    assert [line.split(":")[0] for line in lines[1:5]] == [
        "rotate",
        "zoom",
        "light",
        "pan",
    ]
    assert all(line.endswith("FAIL") for line in lines[:5])
    assert lines[5] == "reset: PASS"
