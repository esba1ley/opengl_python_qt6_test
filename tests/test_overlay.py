"""Tests for the overlay renderer, drawn into an offscreen framebuffer."""
import types

import numpy as np
import pytest
from OpenGL import GL

import config
import overlay
import selftest
from overlay import OverlayRenderer


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
    """The width is clamped to what the driver supports."""
    assert 0 < renderer.axis_width <= config.AXIS_LINE_WIDTH


def test_uniform_locations_are_all_found(renderer):
    """Every uniform the paint methods set exists in the program."""
    assert all(location >= 0 for location in renderer.locs.values())


def test_light_dot_is_yellow(renderer, scene, fbo):
    """The dot is drawn at its projected position in the light colour."""
    renderer.paint(scene)
    widget = types.SimpleNamespace(ctx=scene)
    assert selftest.light_dot_is_yellow(widget, fbo.toImage())


def test_grid_lines_are_drawn(renderer, scene, fbo, image_to_array):
    """Many pixels differ from the clear colour once the grid is painted."""
    renderer.paint(scene)
    array = image_to_array(fbo.toImage())
    lit = np.count_nonzero(np.any(array[..., :3] != 0, axis=2))
    assert lit > 500


def test_es_context_does_not_enable_program_point_size(monkeypatch, renderer):
    """OpenGL ES rejects GL_PROGRAM_POINT_SIZE, so it is not requested."""
    calls = record_enables(monkeypatch)
    monkeypatch.setattr(overlay, "QOpenGLContext", stub_context(True))
    renderer.initialize()
    assert GL.GL_PROGRAM_POINT_SIZE not in calls


def test_desktop_context_enables_program_point_size(monkeypatch, renderer):
    """Desktop OpenGL needs GL_PROGRAM_POINT_SIZE for gl_PointSize."""
    calls = record_enables(monkeypatch)
    monkeypatch.setattr(overlay, "QOpenGLContext", stub_context(False))
    renderer.initialize()
    assert GL.GL_PROGRAM_POINT_SIZE in calls
