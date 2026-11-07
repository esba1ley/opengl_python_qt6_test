"""Tests for the Qt widget: mouse handling on a hidden widget, painting on a shown one."""
import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QVector3D, QWheelEvent

import config
import selftest
from widget import CubeWidget

#: Keyboard modifiers for every synthetic event: none.
NO_MODIFIER = Qt.KeyboardModifier.NoModifier


def mouse_event(kind, pos, button, buttons):
    """Build a mouse event at ``pos`` (local and global coordinates equal)."""
    return QMouseEvent(kind, pos, pos, button, buttons, NO_MODIFIER)


def move_event(pos, buttons):
    """Build a mouse-move event with the given buttons held."""
    return mouse_event(
        QEvent.Type.MouseMove, pos, Qt.MouseButton.NoButton, buttons
    )


def wheel_event(notches):
    """Build a wheel event of ``notches`` notches over the origin."""
    pos = QPointF(10.0, 10.0)
    return QWheelEvent(
        pos,
        pos,
        QPoint(0, 0),
        QPoint(0, notches * 120),
        Qt.MouseButton.NoButton,
        NO_MODIFIER,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )


def snapshot(ctx):
    """Return copies of the rotation, light and pan (pan changes in place)."""
    return ctx.rotation, ctx.light, QVector3D(ctx.pan)


@pytest.fixture
def widget(qtbot):
    """Return a hidden widget; no GL context is created."""
    return CubeWidget()


@pytest.fixture
def pressed(widget):
    """Return a widget whose drag has started at (10, 10)."""
    start = QPointF(10.0, 10.0)
    widget.mousePressEvent(
        mouse_event(
            QEvent.Type.MouseButtonPress,
            start,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
        )
    )
    return widget


@pytest.fixture
def shown(qtbot, capsys):
    """Return ``(widget, printed)`` for a widget shown and exposed.

    ``printed`` is the stdout from ``initializeGL``, captured here so that it
    does not leak into the pytest output.
    """
    capsys.readouterr()
    window = CubeWidget()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window, capsys.readouterr().out


def test_init_sets_title_size_and_state(widget):
    """The constructor sets the title and size and builds the scene state.

    **WHY:** The title is the user's only on-screen hint at the controls, and
    the initial state must match ``config``.
    """
    assert widget.windowTitle() == "Qt6 OpenGL test: drag to rotate, wheel to zoom"
    assert (widget.width(), widget.height()) == (640, 640)
    assert widget.ctx.distance == config.DEFAULT_DISTANCE
    assert widget.cube is not None
    assert widget.overlay is not None
    assert widget.last_pos == QPointF()


def test_resize_clamps_zero_height(widget):
    """A zero height is treated as one pixel.

    **WHY:** Qt can send a zero-height resize, for instance while a window is
    minimised. The clamp keeps the aspect ratio finite.
    """
    widget.resizeGL(640, 0)
    assert widget.ctx.aspect_ratio == 640.0


def test_resize_sets_aspect_ratio(widget):
    """The aspect ratio is width over height.

    **WHY:** The projection matrix takes its aspect ratio from here, so the
    cube keeps its shape when the window does not.
    """
    widget.resizeGL(400, 200)
    assert widget.ctx.aspect_ratio == 2.0


def test_press_records_position(widget):
    """A press stores the click position for the next drag.

    **WHY:** Each drag is measured from where the button went down; without
    this, the first move would jump.
    """
    widget.mousePressEvent(
        mouse_event(
            QEvent.Type.MouseButtonPress,
            QPointF(7.0, 9.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
        )
    )
    assert widget.last_pos == QPointF(7.0, 9.0)


def test_left_drag_rotates(pressed):
    """Dragging with the left button changes only the rotation.

    **WHY:** This is the first row of the README's mouse table. Each button
    must change only its own state.
    """
    before = snapshot(pressed.ctx)
    pressed.mouseMoveEvent(move_event(QPointF(30.0, 20.0), Qt.MouseButton.LeftButton))
    assert pressed.ctx.rotation != before[0]
    assert pressed.ctx.light == before[1]
    assert pressed.ctx.pan == before[2]
    assert pressed.last_pos == QPointF(30.0, 20.0)


def test_right_drag_moves_light(pressed):
    """Dragging with the right button changes only the light.

    **WHY:** This is the README's right-drag row.
    """
    before = snapshot(pressed.ctx)
    pressed.mouseMoveEvent(move_event(QPointF(30.0, 20.0), Qt.MouseButton.RightButton))
    assert pressed.ctx.light != before[1]
    assert pressed.ctx.rotation == before[0]
    assert pressed.ctx.pan == before[2]


def test_middle_drag_pans(pressed):
    """Dragging with the middle button changes only the pan.

    **WHY:** This is the README's middle-drag row.
    """
    before = snapshot(pressed.ctx)
    pressed.mouseMoveEvent(
        move_event(QPointF(30.0, 20.0), Qt.MouseButton.MiddleButton)
    )
    assert pressed.ctx.pan != before[2]
    assert pressed.ctx.rotation == before[0]
    assert pressed.ctx.light == before[1]


def test_left_takes_precedence_over_right(pressed):
    """With both buttons held, the left button's action wins.

    **WHY:** The widget tests the buttons in order, so a reordering would
    quietly change what a two-button drag does.
    """
    rotation, light, _ = snapshot(pressed.ctx)
    both = Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
    pressed.mouseMoveEvent(move_event(QPointF(30.0, 20.0), both))
    assert pressed.ctx.rotation != rotation
    assert pressed.ctx.light == light


def test_hover_changes_nothing_but_still_updates(pressed, monkeypatch):
    """A move with no button held tracks the position and schedules a repaint.

    **WHY:** Recording the position on hover keeps the next press from jumping.
    Hovering falls through every button test, so the repaint is its only other
    effect, and the spy confirms it still happens.
    """
    calls = []
    monkeypatch.setattr(pressed, "update", lambda: calls.append(1))
    before = snapshot(pressed.ctx)
    pressed.mouseMoveEvent(move_event(QPointF(30.0, 20.0), Qt.MouseButton.NoButton))
    assert snapshot(pressed.ctx) == before
    assert pressed.last_pos == QPointF(30.0, 20.0)
    assert calls == [1]


def test_wheel_zooms_both_ways(widget):
    """Positive notches move the camera in, negative notches out.

    **WHY:** The wheel delta reaches ``zoom_by`` with its sign intact, and that
    sign decides the zoom direction.
    """
    start = widget.ctx.distance
    widget.wheelEvent(wheel_event(1))
    zoomed_in = widget.ctx.distance
    assert zoomed_in < start
    widget.wheelEvent(wheel_event(-2))
    assert widget.ctx.distance > start


def test_double_click_restores_defaults(pressed):
    """A double-click undoes every mouse change.

    **WHY:** All four pieces of state are changed first, and checked to have
    changed, so the reset is shown to restore each one.
    """
    for button, target in (
        (Qt.MouseButton.LeftButton, QPointF(30.0, 20.0)),
        (Qt.MouseButton.RightButton, QPointF(50.0, 5.0)),
        (Qt.MouseButton.MiddleButton, QPointF(60.0, 40.0)),
    ):
        pressed.mouseMoveEvent(move_event(target, button))
    pressed.wheelEvent(wheel_event(3))
    fresh = CubeWidget().ctx
    assert pressed.ctx.rotation != fresh.rotation
    assert pressed.ctx.distance != fresh.distance
    assert pressed.ctx.pan != fresh.pan
    assert pressed.ctx.light != fresh.light
    pressed.mouseDoubleClickEvent(
        mouse_event(
            QEvent.Type.MouseButtonDblClick,
            QPointF(10.0, 10.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
        )
    )
    assert pressed.ctx.rotation == fresh.rotation
    assert pressed.ctx.distance == fresh.distance
    assert pressed.ctx.pan == fresh.pan
    assert pressed.ctx.light == fresh.light


def test_shown_widget_renders_a_frame(shown):
    """The exposed widget grabs a frame of the expected size with a yellow dot.

    **WHY:** This is the only test of the full widget path: the real context,
    both renderers and the framebuffer, at the screen's device pixel ratio.
    """
    window, _ = shown
    image = window.grabFramebuffer()
    expected = window.size() * window.devicePixelRatio()
    assert (image.width(), image.height()) == (expected.width(), expected.height())
    assert selftest.light_dot_is_yellow(window, image)


def test_initialize_reports_the_gl_implementation(shown):
    """initializeGL prints the renderer, version and GLSL lines once.

    **WHY:** These three lines are the first thing to read when diagnosing a
    new platform, so their format is part of the program's behaviour.
    """
    _, printed = shown
    lines = printed.splitlines()
    assert [line.split(":")[0] for line in lines] == ["Renderer", "Version", "GLSL"]
