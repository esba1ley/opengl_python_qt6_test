"""Tests for the cube renderer, drawn into an offscreen framebuffer."""
import numpy as np
import pytest
from OpenGL import GL
from PyQt6.QtCore import QPointF

import config
import shaders
from cube import CubeRenderer

#: Pixel offset from the centre that the checks examine.
CENTRE_HALF_WIDTH = 16


@pytest.fixture
def renderer(fbo):
    """Return a cube renderer initialised on the current context."""
    cube = CubeRenderer()
    cube.initialize()
    return cube


def centre(array):
    """Return the central block of an image array."""
    mid = array.shape[0] // 2
    return array[
        mid - CENTRE_HALF_WIDTH : mid + CENTRE_HALF_WIDTH,
        mid - CENTRE_HALF_WIDTH : mid + CENTRE_HALF_WIDTH,
        :3,
    ]


def test_uniform_locations_are_all_found(renderer):
    """Every uniform the paint call sets exists in the linked program.

    **WHY:** GLSL compilers remove uniforms the shader does not use, and
    setting a missing uniform fails silently. A uniform renamed in the shader
    but not here is caught by this test, not by a black frame.
    """
    for name in ("mvp_loc", "model_loc", "light_loc", "camera_loc", "view_loc"):
        assert getattr(renderer, name) >= 0, name


def test_paint_draws_cube_over_the_background(renderer, scene, fbo, image_to_array):
    """The centre of the frame is no longer the clear colour.

    **WHY:** A broken pipeline usually leaves the clear colour untouched, so
    drawn pixels at the centre show that geometry, shaders and textures all
    work together.
    """
    renderer.paint(scene)
    block = centre(image_to_array(fbo.toImage()))
    background = np.round(np.array(config.BACKGROUND_COLOR[::-1]) * 255)
    assert np.any(block != background)
    assert np.all(np.any(block != background, axis=2))


def test_rotating_the_scene_changes_the_image(renderer, scene, fbo, image_to_array):
    """A second paint after rotate_by differs from the first.

    **WHY:** This shows that the model matrix reaches the shader, which drawing
    a single frame cannot.
    """
    renderer.paint(scene)
    before = image_to_array(fbo.toImage())
    scene.rotate_by(QPointF(40.0, 25.0))
    renderer.paint(scene)
    after = image_to_array(fbo.toImage())
    assert np.any(before != after)


def render_views(renderer, scene, fbo, image_to_array):
    """Return the central block of the cube drawn in every debug view.

    The depth buffer is cleared before each draw, or the depth test would
    reject every pass after the first.
    """
    blocks = []
    for index in range(len(shaders.CUBE_VIEWS)):
        scene.cube_view = index
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        renderer.paint(scene)
        blocks.append(centre(image_to_array(fbo.toImage())).copy())
    return blocks


def test_every_debug_view_differs_from_the_final_image(
    renderer, scene, fbo, image_to_array
):
    """Each view in ``CUBE_VIEWS`` renders and differs from view 0.

    **WHY:** The ``view`` uniform is set by an integer index, so a branch
    missing from the shader, or an index that does not match the name list,
    would silently draw the final image under another stage's name in the
    manual.
    """
    blocks = render_views(renderer, scene, fbo, image_to_array)
    for index in range(1, len(blocks)):
        assert np.any(blocks[index] != blocks[0]), shaders.CUBE_VIEWS[index]


def test_albedo_view_is_unlit_and_specular_view_is_grey(
    renderer, scene, fbo, image_to_array
):
    """The albedo view is not the lit colour, and the specular view is grey.

    **WHY:** The albedo view must show the texture without lighting, so it
    cannot equal the lit image. The specular term is one float, drawn as
    ``vec3(specular)``, so a colour cast would mean the wrong term is shown.
    """
    blocks = render_views(renderer, scene, fbo, image_to_array)
    assert np.any(blocks[1] != blocks[0])
    specular = blocks[5]
    assert np.all(specular[..., 0] == specular[..., 1])
    assert np.all(specular[..., 1] == specular[..., 2])
