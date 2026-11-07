"""Tests for the overlay renderer, drawn into an offscreen framebuffer."""
import types

import numpy as np
import pytest
from OpenGL import GL
from PyQt6.QtGui import QVector3D

import config
import geometry
import overlay
import selftest
from overlay import OverlayRenderer

#: Latitude and longitude pairs, in degrees, where a parallel crosses a
#: meridian. Each is a multiple of the grid steps in ``config``.
GRID_INTERSECTIONS = ((0.0, 45.0), (30.0, 60.0), (-20.0, 120.0))


@pytest.fixture
def renderer(fbo):
    """Return an overlay renderer initialised on the current context."""
    drawing = OverlayRenderer()
    drawing.initialize()
    return drawing


def stub_context(is_es):
    """Return a stand-in for QOpenGLContext reporting the given kind."""

    class Stub:
        @staticmethod
        def currentContext():
            return types.SimpleNamespace(isOpenGLES=lambda: is_es)

    return Stub


def record_enables(monkeypatch):
    """Record glEnable enums, swallowing GL_PROGRAM_POINT_SIZE."""
    real_enable = GL.glEnable
    calls = []

    def wrapper(capability):
        calls.append(capability)
        if capability != GL.GL_PROGRAM_POINT_SIZE:
            real_enable(capability)

    monkeypatch.setattr(overlay.GL, "glEnable", wrapper)
    return calls


def test_axis_width_never_exceeds_the_request(renderer):
    """The width is clamped to what the driver supports.

    **WHY:** Drivers cap line width, macOS at one pixel, and a core profile may
    reject wider lines with a GL error, so the width is clamped to the driver's
    range.
    """
    assert 0 < renderer.axis_width <= config.AXIS_LINE_WIDTH


def test_uniform_locations_are_all_found(renderer):
    """Every uniform the paint methods set exists in the program.

    **WHY:** GLSL compilers remove uniforms the shader does not use, and
    setting a missing uniform fails silently. A uniform renamed in the shader
    but not here is caught by this test, not by a black frame.
    """
    assert all(location >= 0 for location in renderer.locs.values())


def test_light_dot_is_yellow(renderer, scene, fbo):
    """The dot is drawn at its projected position in the light colour.

    **WHY:** This reuses the self-test's own pixel check on an offscreen frame,
    so the dot's position and colour are tested without a window.
    """
    renderer.paint(scene)
    widget = types.SimpleNamespace(ctx=scene)
    assert selftest.light_dot_is_yellow(widget, fbo.toImage())


def test_grid_lines_are_drawn_where_projected(
    renderer, scene, fbo, image_to_array, monkeypatch
):
    """Grid intersections land on lit pixels, with axes and dot switched off.

    **WHY:** Projecting known intersections checks that the grid geometry, the
    model matrix and the shader agree on where the sphere is. Switching off the
    axes and dot keeps them from lighting the same pixels. The 3x3 window
    absorbs one pixel of rounding.
    """
    monkeypatch.setattr(renderer, "paint_axes", lambda ctx: None)
    monkeypatch.setattr(renderer, "paint_light_dot", lambda ctx: None)
    renderer.paint(scene)
    lit = np.any(image_to_array(fbo.toImage())[..., :3] != 0, axis=2)
    size = lit.shape[0]
    mvp = scene.view_projection_matrix() * scene.model_matrix()
    for latitude, longitude in GRID_INTERSECTIONS:
        point = geometry.sphere_points(latitude, longitude)
        ndc = mvp.map(QVector3D(*point))
        x = int((ndc.x() + 1.0) / 2.0 * size)
        y = int((1.0 - ndc.y()) / 2.0 * size)  # image rows run top-down
        assert lit[y - 1 : y + 2, x - 1 : x + 2].any(), (latitude, longitude)


def test_es_context_does_not_enable_program_point_size(monkeypatch, renderer):
    """OpenGL ES rejects GL_PROGRAM_POINT_SIZE, so it is not requested.

    **WHY:** OpenGL ES rejects ``GL_PROGRAM_POINT_SIZE`` with an invalid-enum
    error. The context is stubbed so that this branch runs on macOS too.
    """
    calls = record_enables(monkeypatch)
    monkeypatch.setattr(overlay, "QOpenGLContext", stub_context(True))
    renderer.initialize()
    assert GL.GL_PROGRAM_POINT_SIZE not in calls


def test_desktop_context_enables_program_point_size(monkeypatch, renderer):
    """Desktop OpenGL needs GL_PROGRAM_POINT_SIZE for gl_PointSize.

    **WHY:** Desktop OpenGL ignores ``gl_PointSize`` unless this is enabled,
    which would leave the light dot one pixel wide. The recorder swallows the
    call so the test also runs under an ES context.
    """
    calls = record_enables(monkeypatch)
    monkeypatch.setattr(overlay, "QOpenGLContext", stub_context(False))
    renderer.initialize()
    assert GL.GL_PROGRAM_POINT_SIZE in calls
