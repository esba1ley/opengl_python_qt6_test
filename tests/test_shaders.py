"""Tests for the GLSL shader bodies in ``shaders``."""
import pytest

import shaders

#: Every shader body, keyed by its name in ``shaders``.
BODIES = {
    "CUBE_VERTEX_BODY": shaders.CUBE_VERTEX_BODY,
    "CUBE_FRAGMENT_BODY": shaders.CUBE_FRAGMENT_BODY,
    "OVERLAY_VERTEX_BODY": shaders.OVERLAY_VERTEX_BODY,
    "OVERLAY_FRAGMENT_BODY": shaders.OVERLAY_FRAGMENT_BODY,
}


@pytest.mark.parametrize("body", BODIES.values(), ids=BODIES.keys())
def test_body_has_main_and_no_version(body):
    """Bodies define main() and leave the #version line to the header.

    **WHY:** ``gl_utils.glsl_header`` prepends the ``#version`` line, so a body
    that carried its own would hold two. Drivers differ in how they treat that,
    so it could pass on one platform and fail on another.
    """
    assert "#version" not in body
    assert "void main(" in body

