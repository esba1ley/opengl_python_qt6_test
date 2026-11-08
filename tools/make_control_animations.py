#!/usr/bin/env python3
"""Render a short animation of each mouse control, for the README.

A hidden ``CubeWidget`` receives synthetic mouse and wheel events through
``QApplication.sendEvent``, so the animations go through the program's real
input handling. After each event the widget's own ``paintGL`` draws the frame
into an offscreen framebuffer at twice the output size, which is then scaled
down to smooth the lines. A cursor and a label naming the gesture are painted
on top, and the frames are saved as looping animated WebP files with Pillow.
Every sequence ends where it began, so the loops have no jump.

Examples
--------
Regenerate the animations in ``docs/images``::

    python3 tools/make_control_animations.py docs/images
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from OpenGL import GL  # noqa: E402
from PIL import Image  # noqa: E402
from PyQt6.QtCore import QEvent, QPoint, QPointF, QRectF, Qt  # noqa: E402
from PyQt6.QtGui import (  # noqa: E402
    QColor,
    QFont,
    QImage,
    QMouseEvent,
    QOffscreenSurface,
    QOpenGLContext,
    QPainter,
    QPainterPath,
    QPen,
    QWheelEvent,
)
from PyQt6.QtOpenGL import (  # noqa: E402
    QOpenGLFramebufferObject,
    QOpenGLFramebufferObjectFormat,
)
from PyQt6.QtWidgets import QApplication  # noqa: E402

from make_face_images import request_format  # noqa: E402
from widget import CubeWidget  # noqa: E402

#: Side length of each output frame, in pixels.
OUTPUT_SIZE = 240

#: Side length of the offscreen render, before scaling down.
RENDER_SIZE = 2 * OUTPUT_SIZE

#: Display time of an ordinary frame and of a pause, in milliseconds.
FRAME_MS, PAUSE_MS = 60, 700

#: WebP quality, 0 to 100. Lower is smaller and blurrier.
QUALITY = 70

NO_BUTTON = Qt.MouseButton.NoButton
LEFT, RIGHT, MIDDLE = (
    Qt.MouseButton.LeftButton,
    Qt.MouseButton.RightButton,
    Qt.MouseButton.MiddleButton,
)


class Recorder:
    """Drives the widget and collects one rendered frame per step.

    Parameters
    ----------
    widget : widget.CubeWidget
        Hidden widget whose renderers are initialised on the current context.
    target : PyQt6.QtOpenGL.QOpenGLFramebufferObject
        Bound framebuffer that ``paintGL`` draws into.
    """

    def __init__(self, widget, target):
        """Start with an empty frame list and the cursor at the centre."""
        self.widget = widget
        self.target = target
        self.frames = []
        self.durations = []
        self.pos = QPointF(widget.width() / 2, widget.height() / 2)

    def send_mouse(self, kind, button, buttons):
        """Send one mouse event at the cursor position."""
        event = QMouseEvent(
            kind, self.pos, self.pos, button, buttons,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(self.widget, event)

    def drag(self, button, label, steps):
        """Press ``button``, move by each ``(dx, dy)`` in ``steps``, release.

        One frame is captured after every move.
        """
        self.send_mouse(QEvent.Type.MouseButtonPress, button, button)
        for dx, dy in steps:
            self.pos += QPointF(dx, dy)
            self.send_mouse(QEvent.Type.MouseMove, NO_BUTTON, button)
            self.capture(label, held=True)
        self.send_mouse(QEvent.Type.MouseButtonRelease, button, NO_BUTTON)

    def wheel(self, label, units, count):
        """Turn the wheel by ``units`` (120 per notch) ``count`` times."""
        for _ in range(count):
            event = QWheelEvent(
                self.pos, self.pos, QPoint(0, 0), QPoint(0, units), NO_BUTTON,
                Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase,
                False,
            )
            QApplication.sendEvent(self.widget, event)
            self.capture(label)

    def double_click(self, label):
        """Double-click at the cursor and capture the flash of the click."""
        self.send_mouse(QEvent.Type.MouseButtonPress, LEFT, LEFT)
        self.send_mouse(QEvent.Type.MouseButtonRelease, LEFT, NO_BUTTON)
        self.send_mouse(QEvent.Type.MouseButtonDblClick, LEFT, LEFT)
        self.send_mouse(QEvent.Type.MouseButtonRelease, LEFT, NO_BUTTON)
        self.capture(label, held=True, duration=PAUSE_MS)

    def pause(self, label):
        """Hold the current view for one long frame."""
        self.capture(label, duration=PAUSE_MS)

    def capture(self, label, held=False, duration=FRAME_MS):
        """Render the scene, add the cursor and label, and store the frame."""
        self.widget.paintGL()
        image = self.target.toImage().scaled(
            OUTPUT_SIZE, OUTPUT_SIZE,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        scale = OUTPUT_SIZE / self.widget.width()
        decorate(image, QPointF(self.pos.x() * scale, self.pos.y() * scale),
                 label, held)
        self.frames.append(to_pillow(image))
        self.durations.append(duration)


def decorate(image, tip, label, held):
    """Paint an arrow cursor at ``tip`` and ``label`` along the bottom.

    Parameters
    ----------
    image : PyQt6.QtGui.QImage
        Frame to paint on, in place.
    tip : PyQt6.QtCore.QPointF
        Cursor hot spot, in image pixels.
    label : str
        Name of the gesture.
    held : bool
        Whether a button is down; draws a ring around the hot spot.
    """
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if held:
        painter.setPen(QPen(QColor(255, 210, 60), 2.0))
        painter.setBrush(QColor(255, 210, 60, 70))
        painter.drawEllipse(tip, 9.0, 9.0)
    arrow = QPainterPath(QPointF(0, 0))
    for x, y in ((0, 16), (4, 12), (7, 19), (10, 18), (7, 11), (12, 11)):
        arrow.lineTo(x, y)
    arrow.closeSubpath()
    painter.translate(tip)
    painter.setPen(QPen(QColor(0, 0, 0), 1.2))
    painter.setBrush(QColor(255, 255, 255))
    painter.drawPath(arrow)
    painter.resetTransform()

    font = QFont()
    font.setPixelSize(14)
    font.setBold(True)
    painter.setFont(font)
    box = QRectF(0, image.height() - 24, image.width(), 24)
    painter.fillRect(box, QColor(0, 0, 0, 170))
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(box, Qt.AlignmentFlag.AlignCenter, label)
    painter.end()


def to_pillow(image):
    """Copy a QImage into a Pillow RGB image.

    Parameters
    ----------
    image : PyQt6.QtGui.QImage
        Source frame.

    Returns
    -------
    PIL.Image.Image
        An independent RGB copy.
    """
    image = image.convertToFormat(QImage.Format.Format_RGB888)
    data = image.constBits().asstring(image.sizeInBytes())
    return Image.frombuffer(
        "RGB", (image.width(), image.height()), data, "raw", "RGB",
        image.bytesPerLine(), 1,
    ).copy()


def there_and_back(dx, dy, count):
    """Return ``count`` moves of ``(dx, dy)`` followed by the reverse.

    Parameters
    ----------
    dx, dy : float
        Movement per frame, in widget pixels.
    count : int
        Frames in each direction.

    Returns
    -------
    list of tuple of float
        The moves, ending where they began.
    """
    return [(dx, dy)] * count + [(-dx, -dy)] * count


def rotate(rec):
    """Left-drag across and back, then down and back."""
    label = "Left-drag: rotate"
    rec.pause(label)
    rec.drag(LEFT, label, there_and_back(9.0, 0.0, 12))
    rec.drag(LEFT, label, there_and_back(0.0, 7.0, 12))


def light(rec):
    """Right-drag across and back, then up and back."""
    label = "Right-drag: move the light"
    rec.pause(label)
    rec.drag(RIGHT, label, there_and_back(-10.0, 0.0, 12))
    rec.drag(RIGHT, label, there_and_back(0.0, 8.0, 12))


def pan(rec):
    """Middle-drag right and back, then down and back."""
    label = "Middle-drag: pan"
    rec.pause(label)
    rec.drag(MIDDLE, label, there_and_back(8.0, 0.0, 12))
    rec.drag(MIDDLE, label, there_and_back(0.0, 7.0, 12))


def zoom(rec):
    """Wheel forward a quarter notch at a time, pause, then back."""
    rec.pause("Wheel: zoom")
    rec.wheel("Wheel forward: zoom in", 30, 14)
    rec.pause("Wheel forward: zoom in")
    rec.wheel("Wheel back: zoom out", -30, 14)


def reset(rec):
    """Rotate, move the light and zoom, then double-click back."""
    rec.pause("Double-click: reset")
    rec.drag(LEFT, "Left-drag: rotate", [(8.0, 3.0)] * 10)
    rec.drag(RIGHT, "Right-drag: move the light", [(-6.0, 6.0)] * 8)
    rec.wheel("Wheel: zoom", 30, 8)
    rec.pause("Double-click: reset")
    rec.double_click("Double-click: reset")
    rec.pause("Double-click: reset")


#: Animations in the README's table order, keyed by output file stem.
SEQUENCES = {
    "control-rotate": rotate,
    "control-light": light,
    "control-pan": pan,
    "control-zoom": zoom,
    "control-reset": reset,
}


def main():
    """Parse the arguments, render each sequence and save it."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="where to write the files")
    args = parser.parse_args()

    request_format()
    app = QApplication(sys.argv[:1])  # noqa: F841 - needed for the widget
    surface = QOffscreenSurface()
    surface.create()
    context = QOpenGLContext()
    if not context.create() or not context.makeCurrent(surface):
        sys.exit("make_control_animations: no OpenGL context")
    fmt = QOpenGLFramebufferObjectFormat()
    fmt.setAttachment(QOpenGLFramebufferObject.Attachment.Depth)
    target = QOpenGLFramebufferObject(RENDER_SIZE, RENDER_SIZE, fmt)
    target.bind()
    GL.glViewport(0, 0, RENDER_SIZE, RENDER_SIZE)

    widget = CubeWidget()
    widget.cube.initialize()
    widget.overlay.initialize()
    # Keep the light dot the same size relative to the scene as in the window.
    widget.ctx.pixel_ratio = RENDER_SIZE / widget.width()

    args.directory.mkdir(parents=True, exist_ok=True)
    for stem, sequence in SEQUENCES.items():
        widget.ctx.reset_view()
        rec = Recorder(widget, target)
        sequence(rec)
        path = args.directory / f"{stem}.webp"
        rec.frames[0].save(
            path, save_all=True, append_images=rec.frames[1:],
            duration=rec.durations, loop=0, quality=QUALITY, method=6,
        )
        print(f"{path}: {len(rec.frames)} frames, {path.stat().st_size // 1024} kB")
    target.release()
    context.doneCurrent()


if __name__ == "__main__":
    main()
