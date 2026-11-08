"""Self-test that simulates mouse input and checks the rendered frames."""
import itertools

from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QWheelEvent
from PyQt6.QtWidgets import QApplication


def send_drag(widget, button, dx, dy):
    """Simulate a mouse drag that starts at the widget's centre.

    Parameters
    ----------
    widget : QWidget
        Widget that receives the events.
    button : PyQt6.QtCore.Qt.MouseButton
        Button held during the drag.
    dx : float
        Horizontal movement, in pixels.
    dy : float
        Vertical movement, in pixels.
    """
    no_modifier = Qt.KeyboardModifier.NoModifier
    start = QPointF(widget.width() / 2, widget.height() / 2)
    end = start + QPointF(dx, dy)
    for kind, pos, active in (
        (QEvent.Type.MouseButtonPress, start, button),
        (QEvent.Type.MouseMove, end, button),
        (QEvent.Type.MouseButtonRelease, end, Qt.MouseButton.NoButton),
    ):
        event_button = Qt.MouseButton.NoButton if kind == QEvent.Type.MouseMove else button
        event = QMouseEvent(kind, pos, pos, event_button, active, no_modifier)
        QApplication.sendEvent(widget, event)


def send_wheel(widget, notches):
    """Simulate turning the mouse wheel over the widget's centre.

    Parameters
    ----------
    widget : QWidget
        Widget that receives the event.
    notches : int
        Number of wheel notches. Positive values zoom in.
    """
    pos = QPointF(widget.width() / 2, widget.height() / 2)
    event = QWheelEvent(
        pos,
        pos,
        QPoint(0, 0),
        QPoint(0, notches * 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(widget, event)


def light_dot_is_yellow(widget, image):
    """Check that the light dot was drawn where it should be.

    Parameters
    ----------
    widget : CubeWidget
        Widget that produced the image.
    image : PyQt6.QtGui.QImage
        Rendered frame.

    Returns
    -------
    bool
        True if the pixel at the dot's projected position is yellow.
    """
    ctx = widget.ctx
    ndc = ctx.view_projection_matrix().map(ctx.light_dot_position())
    x = round((ndc.x() + 1.0) / 2.0 * (image.width() - 1))
    y = round((1.0 - ndc.y()) / 2.0 * (image.height() - 1))
    color = image.pixelColor(x, y)
    return min(color.red(), color.green()) > color.blue() + 80


def check(widget):
    """Run the self-test, then exit the application.

    Confirms the light dot is drawn, each mouse control changes the rendered image
    and a double-click restores the starting image. Results are printed, and the
    application exits with status 0 if everything passed and 1 otherwise.

    Parameters
    ----------
    widget : CubeWidget
        A shown widget to test. Its view is reset at the end.
    """
    frames = [("start", widget.grabFramebuffer())]
    dot_ok = light_dot_is_yellow(widget, frames[0][1])
    print(f"light dot: {'PASS' if dot_ok else 'FAIL'}")
    send_drag(widget, Qt.MouseButton.LeftButton, 60, 30)
    frames.append(("rotate", widget.grabFramebuffer()))
    send_wheel(widget, 3)
    frames.append(("zoom", widget.grabFramebuffer()))
    send_drag(widget, Qt.MouseButton.RightButton, 80, -40)
    frames.append(("light", widget.grabFramebuffer()))
    send_drag(widget, Qt.MouseButton.MiddleButton, 80, -40)
    frames.append(("pan", widget.grabFramebuffer()))

    ok = dot_ok
    for (_, previous), (name, image) in itertools.pairwise(frames):
        changed = image != previous
        ok = ok and changed
        print(f"{name}: {'PASS' if changed else 'FAIL'}")

    # Qt delivers a widget's second press as the double-click event, so the
    # double-click event alone is all a widget sees.
    pos = QPointF(widget.width() / 2, widget.height() / 2)
    QApplication.sendEvent(
        widget,
        QMouseEvent(
            QEvent.Type.MouseButtonDblClick,
            pos,
            pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        ),
    )
    restored = widget.grabFramebuffer() == frames[0][1]
    ok = ok and restored
    print(f"reset: {'PASS' if restored else 'FAIL'}")
    QApplication.exit(0 if ok else 1)
