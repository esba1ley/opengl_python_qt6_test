"""The Qt widget: turns mouse input into scene changes and paints frames."""
from OpenGL import GL
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

import config
from context import SceneContext
from cube import CubeRenderer
from overlay import OverlayRenderer


class CubeWidget(QOpenGLWidget):
    """OpenGL widget showing the cube, sphere grid, axes and light dot.

    Attributes
    ----------
    ctx : context.SceneContext
        The scene state shared with the renderers.
    cube : cube.CubeRenderer
        Draws the cube.
    overlay : overlay.OverlayRenderer
        Draws the sphere grid, the axes and the light dot.
    last_pos : PyQt6.QtCore.QPointF
        Previous mouse position, used to measure drags.
    """

    def __init__(self):
        """Set the window size and request the surface format."""
        super().__init__()
        self.setWindowTitle("Qt6 OpenGL test: drag to rotate, wheel to zoom")
        self.resize(640, 640)

        surface = QSurfaceFormat.defaultFormat()  # keeps any profile set in main.py
        surface.setDepthBufferSize(24)  # without this, faces draw in the wrong order
        surface.setSamples(4)
        self.setFormat(surface)

        self.ctx = SceneContext()
        self.cube = CubeRenderer()
        self.overlay = OverlayRenderer()
        self.last_pos = QPointF()

    # --- OpenGL ---

    def initializeGL(self):
        """Report the OpenGL implementation and set up the renderers.

        Qt calls this once, with the widget's OpenGL context current.
        """
        print("Renderer:", GL.glGetString(GL.GL_RENDERER).decode())
        print("Version: ", GL.glGetString(GL.GL_VERSION).decode())
        print("GLSL:    ", GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode())
        self.cube.initialize()
        self.overlay.initialize()

    def resizeGL(self, width, height):
        """Record the viewport shape in the shared context.

        Parameters
        ----------
        width : int
            Viewport width, in device pixels.
        height : int
            Viewport height, in device pixels.
        """
        self.ctx.aspect_ratio = width / max(height, 1)
        self.ctx.pixel_ratio = self.devicePixelRatioF()

    def paintGL(self):
        """Clear the frame, then draw the cube and the overlay.

        Qt calls this whenever the widget needs repainting.
        """
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClearColor(*config.BACKGROUND_COLOR, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.cube.paint(self.ctx)
        self.overlay.paint(self.ctx)

    # --- Mouse ---

    def mousePressEvent(self, event):
        """Record where a drag starts.

        Parameters
        ----------
        event : PyQt6.QtGui.QMouseEvent
            The press event.
        """
        self.last_pos = event.position()

    def mouseMoveEvent(self, event):
        """Rotate, move the light or pan, depending on the held button.

        The left button rotates the cube and sphere, the right button moves
        the light and the middle button pans.

        Parameters
        ----------
        event : PyQt6.QtGui.QMouseEvent
            The move event.
        """
        delta = event.position() - self.last_pos
        self.last_pos = event.position()

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.ctx.rotate_by(delta)
        elif event.buttons() & Qt.MouseButton.RightButton:
            self.ctx.move_light_by(delta)
        elif event.buttons() & Qt.MouseButton.MiddleButton:
            self.ctx.pan_by(delta, self.height())
        self.update()

    def wheelEvent(self, event):
        """Zoom in or out.

        Parameters
        ----------
        event : PyQt6.QtGui.QWheelEvent
            The wheel event.
        """
        self.ctx.zoom_by(event.angleDelta().y() / 120.0)
        self.update()

    def mouseDoubleClickEvent(self, event):
        """Reset the view and the light.

        Parameters
        ----------
        event : PyQt6.QtGui.QMouseEvent
            The double-click event.
        """
        self.ctx.reset_view()
        self.update()
