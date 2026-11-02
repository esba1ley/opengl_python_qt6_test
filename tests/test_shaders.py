"""Tests for the GLSL shader bodies in ``shaders``."""
import pytest

import shaders

BODIES = {
    "CUBE_VERTEX_BODY": shaders.CUBE_VERTEX_BODY,
    "CUBE_FRAGMENT_BODY": shaders.CUBE_FRAGMENT_BODY,
    "OVERLAY_VERTEX_BODY": shaders.OVERLAY_VERTEX_BODY,
    "OVERLAY_FRAGMENT_BODY": shaders.OVERLAY_FRAGMENT_BODY,
}


@pytest.mark.parametrize("body", BODIES.values(), ids=BODIES.keys())
def test_body_has_main_and_no_version(body):
    """Bodies define main() and leave the #version line to the header."""
    assert "#version" not in body
    assert "void main(" in body


@pytest.mark.parametrize(
    "body", [shaders.CUBE_VERTEX_BODY, shaders.OVERLAY_VERTEX_BODY]
)
def test_vertex_bodies_write_gl_position(body):
    """Both vertex shaders write gl_Position."""
    assert "gl_Position =" in body


@pytest.mark.parametrize(
    "body", [shaders.CUBE_FRAGMENT_BODY, shaders.OVERLAY_FRAGMENT_BODY]
)
def test_fragment_bodies_declare_frag_color(body):
    """Both fragment shaders declare the out variable the programs bind."""
    assert "out vec4 fragColor;" in body
