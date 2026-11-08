"""Shared pytest configuration and fixtures.

Puts ``src`` on the import path, requests the same default OpenGL format as
``main.py`` through ``main.request_surface_format``, and provides an
offscreen OpenGL context, a framebuffer object to render into, and a few small
helpers.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from PyQt6.QtGui import (
    QImage,
    QOffscreenSurface,
    QOpenGLContext,
    QSurfaceFormat,
)
from PyQt6.QtOpenGL import (
    QOpenGLFramebufferObject,
    QOpenGLFramebufferObjectFormat,
)

#: The program's source directory, put on ``sys.path``.
SRC_DIR = Path(__file__).resolve().parent.parent / "src"

#: Side length in pixels of the framebuffer object the ``fbo`` fixture makes.
FBO_SIZE = 256


def pytest_configure(config):
    """Set up the import path and the default surface format.

    Calls ``main.request_surface_format``, so that widgets created by the
    tests get the same context the program requests.

    Parameters
    ----------
    config : pytest.Config
        The pytest configuration object (unused).
    """
    sys.path.insert(0, str(SRC_DIR))
    import main

    main.request_surface_format()


@pytest.fixture(scope="session")
def _gl_resources(qapp):
    """Create the offscreen surface and OpenGL context once per session.

    The surface needs a running application, hence ``qapp``.
    """
    surface = QOffscreenSurface()
    surface.setFormat(QSurfaceFormat.defaultFormat())
    surface.create()
    assert surface.isValid(), "offscreen surface could not be created"
    context = QOpenGLContext()
    context.setFormat(QSurfaceFormat.defaultFormat())
    assert context.create()
    yield context, surface
    context.doneCurrent()
    surface.destroy()


@pytest.fixture
def gl_context(_gl_resources):
    """Make the shared offscreen OpenGL context current for one test."""
    context, surface = _gl_resources
    assert context.makeCurrent(surface)
    yield context
    context.doneCurrent()


@pytest.fixture
def fbo(gl_context):
    """Bind a cleared 256x256 framebuffer object with a depth attachment."""
    import config
    from OpenGL import GL

    fmt = QOpenGLFramebufferObjectFormat()
    fmt.setAttachment(QOpenGLFramebufferObject.Attachment.Depth)
    target = QOpenGLFramebufferObject(FBO_SIZE, FBO_SIZE, fmt)
    assert target.bind()
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glViewport(0, 0, FBO_SIZE, FBO_SIZE)
    GL.glClearColor(*config.BACKGROUND_COLOR, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    yield target
    target.release()


@pytest.fixture
def image_to_array():
    """Return a function that copies a QImage to an (h, w, 4) BGRA array."""

    def convert(image):
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        width, height = image.width(), image.height()
        buffer = image.constBits()
        buffer.setsize(height * image.bytesPerLine())
        rows = np.frombuffer(buffer, np.uint8).reshape(height, image.bytesPerLine())
        return rows[:, : width * 4].reshape(height, width, 4).copy()

    return convert


@pytest.fixture
def scene():
    """Return a fresh ``SceneContext`` with a square aspect ratio."""
    from context import SceneContext

    ctx = SceneContext()
    ctx.aspect_ratio = 1.0
    return ctx


@pytest.fixture(autouse=True)
def restore_default_format():
    """Restore the default surface format after each test."""
    saved = QSurfaceFormat.defaultFormat()
    yield
    QSurfaceFormat.setDefaultFormat(saved)
