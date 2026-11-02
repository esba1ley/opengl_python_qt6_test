"""Tests for the cube renderer, drawn into an offscreen framebuffer."""
import numpy as np
import pytest
from PyQt6.QtCore import QPointF

import config
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
    """Every uniform the paint call sets exists in the linked program."""
    for name in ("mvp_loc", "model_loc", "light_loc", "camera_loc"):
        assert getattr(renderer, name) >= 0, name


def test_paint_draws_cube_over_the_background(renderer, scene, fbo, image_to_array):
    """The centre of the frame is no longer the clear colour."""
    renderer.paint(scene)
    block = centre(image_to_array(fbo.toImage()))
    background = np.round(np.array(config.BACKGROUND_COLOR[::-1]) * 255)
    assert np.any(block != background)
    assert np.all(np.any(block != background, axis=2))


def test_rotating_the_scene_changes_the_image(renderer, scene, fbo, image_to_array):
    """A second paint after rotate_by differs from the first."""
    renderer.paint(scene)
    before = image_to_array(fbo.toImage())
    scene.rotate_by(QPointF(40.0, 25.0))
    renderer.paint(scene)
    after = image_to_array(fbo.toImage())
    assert np.any(before != after)
