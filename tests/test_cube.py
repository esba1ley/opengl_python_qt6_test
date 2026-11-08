"""Tests for the cube renderer, drawn into an offscreen framebuffer."""
import numpy as np
import pytest
from OpenGL import GL
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QQuaternion, QVector3D

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


def test_specular_view_is_grey_where_the_highlight_falls(
    renderer, scene, fbo, image_to_array
):
    """With the light mirrored into the camera, the specular view is grey.

    **WHY:** The specular term is one float, drawn as ``vec3(specular)``, so a
    colour cast would mean the wrong term is shown. With the default light the
    highlight may miss the examined block and the check would pass on black,
    so the light is placed to put the highlight on the front face: the mirror
    direction ``2 (n . v) n - v`` of the face normal ``n`` about the unit
    vector ``v`` to the camera.
    """
    normal = scene.rotation.rotatedVector(QVector3D(0, 0, 1))
    to_camera = (scene.camera_position() - normal).normalized()
    mirror = 2.0 * QVector3D.dotProduct(normal, to_camera) * normal - to_camera
    scene.light = mirror.normalized()
    scene.cube_view = shaders.CUBE_VIEWS.index("specular")
    renderer.paint(scene)
    block = centre(image_to_array(fbo.toImage()))
    assert np.any(block > 0)
    assert np.all(block[..., 0] == block[..., 1])
    assert np.all(block[..., 1] == block[..., 2])


#: Expected (red, green, blue) in 0 to 1 of the +Z face seen head-on, per
#: geometry view.
GEOMETRY_VIEWS = [
    ("layer", (0.8, 0.8, 0.8)),
    ("tangent", (1.0, 0.5, 0.5)),
    ("bitangent", (0.5, 1.0, 0.5)),
    ("face_normal", (0.5, 0.5, 1.0)),
]


@pytest.mark.parametrize(("name", "expected"), GEOMETRY_VIEWS)
def test_geometry_view_shows_its_input_on_the_front_face(
    renderer, scene, fbo, image_to_array, name, expected
):
    """Each geometry view colours the +Z face with its one vertex input.

    **WHY:** Each view is computed from a single input (layer, tangent,
    bitangent or normal), so a wrong input or a swapped axis would picture
    the wrong data in the manual. With the identity rotation the +Z face
    (layer 4) faces the camera, with tangent +X, bitangent +Y and normal +Z.
    """
    scene.rotation = QQuaternion()
    scene.cube_view = shaders.CUBE_VIEWS.index(name)
    renderer.paint(scene)
    block = centre(image_to_array(fbo.toImage()))
    rgb = block[..., 2::-1].astype(float) / 255.0
    for channel in range(3):
        assert np.all(np.abs(rgb[..., channel] - expected[channel]) <= 2 / 255)


def test_uv_view_ramps_across_the_front_face(renderer, scene, fbo, image_to_array):
    """The uv view has blue 0 and a block mean near (0.5, 0.5).

    **WHY:** The view draws ``vec3(textureCoords, 0.0)``, so blue must be
    zero and red and green must be the texture coordinates. The central block
    is not exactly centred on the face (the perspective and the pan shift it
    slightly), so the mean gets a 0.05 tolerance rather than rounding error,
    and red must increase from left to right (u runs along +X).
    """
    scene.rotation = QQuaternion()
    scene.cube_view = shaders.CUBE_VIEWS.index("uv")
    renderer.paint(scene)
    block = centre(image_to_array(fbo.toImage()))
    rgb = block[..., 2::-1].astype(float) / 255.0
    assert np.all(rgb[..., 2] == 0.0)
    assert np.all(np.abs(rgb[..., :2].mean(axis=(0, 1)) - 0.5) <= 0.05)
    assert rgb[:, -1, 0].mean() > rgb[:, 0, 0].mean()
