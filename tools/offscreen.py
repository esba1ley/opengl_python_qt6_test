"""Offscreen rendering shared by the image tools.

``OffscreenScene`` keeps a hidden ``CubeWidget`` whose renderers are set up on
an offscreen OpenGL context and draw into a framebuffer object, so a tool can
render exactly what the window shows without opening one. The tools import
this module by name, since Python puts a script's own directory on the
import path.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from OpenGL import GL  # noqa: E402
from PyQt6.QtGui import (  # noqa: E402
    QOffscreenSurface,
    QOpenGLContext,
    QSurfaceFormat,
)
from PyQt6.QtOpenGL import (  # noqa: E402
    QOpenGLFramebufferObject,
    QOpenGLFramebufferObjectFormat,
)
from PyQt6.QtWidgets import QApplication  # noqa: E402

from widget import CubeWidget  # noqa: E402


def request_format():
    """Set the default surface format the program itself requests.

    These lines repeat ``main.main``, which sets the format inline.
    """
    surface = QSurfaceFormat()
    if sys.platform == "darwin":
        surface.setVersion(4, 1)
        surface.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    else:
        surface.setRenderableType(QSurfaceFormat.RenderableType.OpenGLES)
        surface.setVersion(3, 1)
    QSurfaceFormat.setDefaultFormat(surface)


class OffscreenScene:
    """A hidden window's renderers drawing into an offscreen framebuffer.

    Creating one requests the program's surface format, starts a
    ``QApplication`` if none exists, makes an offscreen context current and
    binds a square framebuffer with a depth buffer.

    Parameters
    ----------
    render_size : int
        Side length of the framebuffer, in pixels. The light dot is scaled
        so that it keeps its size relative to the scene in the 640-pixel
        window.

    Attributes
    ----------
    widget : widget.CubeWidget
        The hidden window. Send it events, and read or change ``widget.ctx``.
    """

    def __init__(self, render_size):
        """Create the context, the framebuffer and the widget."""
        request_format()
        self.app = QApplication.instance() or QApplication(sys.argv[:1])
        self.surface = QOffscreenSurface()
        self.surface.create()
        self.context = QOpenGLContext()
        if not self.context.create() or not self.context.makeCurrent(self.surface):
            sys.exit("offscreen: no OpenGL context")
        fmt = QOpenGLFramebufferObjectFormat()
        fmt.setAttachment(QOpenGLFramebufferObject.Attachment.Depth)
        self.target = QOpenGLFramebufferObject(render_size, render_size, fmt)
        self.target.bind()
        GL.glViewport(0, 0, render_size, render_size)

        self.widget = CubeWidget()
        self.widget.cube.initialize()
        self.widget.overlay.initialize()
        self.widget.ctx.pixel_ratio = render_size / self.widget.width()

    def render(self, paint=None):
        """Draw one frame and return it.

        Parameters
        ----------
        paint : callable, optional
            Draws the frame. Defaults to the widget's own ``paintGL``.

        Returns
        -------
        PyQt6.QtGui.QImage
            The framebuffer, at full render size.
        """
        (paint or self.widget.paintGL)()
        return self.target.toImage()

    def close(self):
        """Release the framebuffer and the context."""
        self.target.release()
        self.context.doneCurrent()
