"""Smoke test for the shared fixtures in ``conftest.py``."""
import numpy as np

import config


def test_gl_context_is_valid_and_current(gl_context):
    """The offscreen context is valid and current.

    **WHY:** Every GL test depends on this fixture. If the offscreen context
    cannot be created, as may happen under a new display server, this test
    fails first and names the cause, instead of dozens of GL tests failing with
    unrelated errors.
    """
    from PyQt6.QtGui import QOpenGLContext

    assert gl_context.isValid()
    assert QOpenGLContext.currentContext() == gl_context


def test_fbo_reads_back_as_background(fbo, image_to_array):
    """A freshly cleared framebuffer is all background colour.

    **WHY:** The renderer tests compare pixels against the clear colour, so the
    framebuffer must read back exactly that colour before anything is drawn. It
    also pins the BGRA byte order that ``image_to_array`` returns.
    """
    pixels = image_to_array(fbo.toImage())
    expected = [round(255 * c) for c in reversed(config.BACKGROUND_COLOR)]
    assert pixels.shape == (256, 256, 4)
    assert np.all(pixels[..., :3] == expected)
