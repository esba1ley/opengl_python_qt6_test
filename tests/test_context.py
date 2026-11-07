"""Tests for the scene state in ``context``."""
import math

import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QQuaternion, QVector3D

import config
import context


def test_screen_rotation_zero_delta_is_identity():
    """A zero-length drag gives the identity rotation.

    **WHY:** A zero-length drag has no rotation axis. Without this branch,
    normalising the zero axis would give NaN and the cube would vanish after a
    click without movement.
    """
    assert context.screen_rotation(QPointF(0.0, 0.0)) == QQuaternion()


def test_screen_rotation_angle_follows_drag_length():
    """A drag rotates by length times degrees-per-pixel about a screen axis.

    **WHY:** The mouse sensitivity is ``ROTATE_DEGREES_PER_PIXEL``, and a
    horizontal drag must turn the scene about the screen's vertical axis, not
    the model's.
    """
    q = context.screen_rotation(QPointF(10.0, 0.0))
    axis, angle = q.getAxisAndAngle()
    assert angle == pytest.approx(10.0 * config.ROTATE_DEGREES_PER_PIXEL)
    assert (axis.x(), axis.y(), axis.z()) == pytest.approx((0.0, 1.0, 0.0))


def test_reset_view_restores_defaults(scene):
    """reset_view undoes every kind of change.

    **WHY:** The double-click reset is the user's way out of a lost view, so it
    must undo all four kinds of change.
    """
    scene.rotate_by(QPointF(30.0, 20.0))
    scene.move_light_by(QPointF(30.0, 20.0))
    scene.pan_by(QPointF(5.0, 5.0), 100)
    scene.zoom_by(3.0)
    scene.reset_view()
    expected = QQuaternion.fromEulerAngles(
        config.DEFAULT_PITCH_DEGREES, config.DEFAULT_YAW_DEGREES, 0.0
    )
    assert scene.rotation == expected
    assert scene.distance == config.DEFAULT_DISTANCE
    assert scene.pan == QVector3D(0.0, 0.0, 0.0)
    assert scene.light == config.DEFAULT_LIGHT


def test_rotate_by_changes_rotation_and_stays_normalized(scene):
    """Rotating changes the orientation and keeps a unit quaternion.

    **WHY:** Quaternion products drift from unit length. Without renormalising,
    a long drag session would slowly scale the cube.
    """
    before = scene.rotation
    scene.rotate_by(QPointF(12.0, -7.0))
    assert scene.rotation != before
    assert scene.rotation.length() == pytest.approx(1.0)


def test_rotate_by_zero_leaves_rotation(scene):
    """A zero drag leaves the orientation unchanged.

    **WHY:** The zero drag again, this time through the method the widget
    calls.
    """
    before = scene.rotation
    scene.rotate_by(QPointF(0.0, 0.0))
    assert scene.rotation.length() == pytest.approx(1.0)
    assert QQuaternion.dotProduct(scene.rotation, before) == pytest.approx(1.0)


def test_move_light_by_keeps_unit_length_and_moves(scene):
    """Moving the light changes its direction but not its length.

    **WHY:** The shader assumes a unit light direction, and the light dot is
    placed at ``SPHERE_RADIUS`` along it.
    """
    before = scene.light
    scene.move_light_by(QPointF(40.0, 25.0))
    assert scene.light != before
    assert scene.light.length() == pytest.approx(1.0)


def test_pan_by_scales_with_distance_and_viewport(scene):
    """Pan moves right for +x and up for +y drag (screen y is down).

    **WHY:** Panning should keep the scene under the cursor at any zoom and
    window size. Screen y runs down while scene y runs up; a missing sign flip
    would move the scene against the mouse.
    """
    scene.pan_by(QPointF(10.0, 20.0), 100)
    scale = 0.8 * config.DEFAULT_DISTANCE / 100
    assert scene.pan.x() == pytest.approx(10.0 * scale)
    assert scene.pan.y() == pytest.approx(-20.0 * scale)
    assert scene.pan.z() == 0.0


def test_pan_by_zero_viewport_height_is_clamped(scene):
    """A zero-height viewport divides by 1, not 0.

    **WHY:** Qt can report a zero-height viewport, for instance while a window
    is minimised. The clamp keeps a pan from dividing by zero.
    """
    scene.pan_by(QPointF(1.0, 0.0), 0)
    assert scene.pan.x() == pytest.approx(0.8 * config.DEFAULT_DISTANCE)
    assert math.isfinite(scene.pan.x())


def test_zoom_by_positive_zooms_in(scene):
    """One notch multiplies the distance by the zoom factor.

    **WHY:** One notch must scale the distance by ``ZOOM_FACTOR_PER_NOTCH``,
    and the sign decides which way the wheel zooms.
    """
    scene.zoom_by(1.0)
    assert scene.distance == pytest.approx(
        config.DEFAULT_DISTANCE * config.ZOOM_FACTOR_PER_NOTCH
    )


def test_zoom_by_clamps_at_both_limits(scene):
    """Extreme zooming stops at the minimum and maximum distances.

    **WHY:** Without the clamps the camera could enter the cube or zoom out
    without bound. One test reaches both branches.
    """
    scene.zoom_by(1000.0)
    assert scene.distance == config.MIN_DISTANCE
    scene.zoom_by(-1000.0)
    assert scene.distance == config.MAX_DISTANCE


def test_matrices_are_consistent(scene):
    """The model matrix is the rotation and the view matrix applies pan and distance.

    **WHY:** The model matrix must apply exactly the stored rotation, and the
    view matrix must move the origin to the pan offset at the zoom distance.
    The cube, sphere and axes all rely on these matrices staying anchored
    together.
    """
    scene.aspect_ratio = 1.5
    scene.pan_by(QPointF(10.0, 5.0), 100)
    point = QVector3D(1.0, 2.0, 3.0)
    mapped = scene.model_matrix().map(point)
    rotated = scene.rotation.rotatedVector(point)
    assert (mapped.x(), mapped.y(), mapped.z()) == pytest.approx(
        (rotated.x(), rotated.y(), rotated.z()), abs=1e-5
    )
    view_origin = scene.view_matrix().map(QVector3D(0.0, 0.0, 0.0))
    assert (view_origin.x(), view_origin.y(), view_origin.z()) == pytest.approx(
        (scene.pan.x(), scene.pan.y(), -scene.distance)
    )


def test_projection_matrix_uses_aspect_ratio(scene):
    """A wider viewport shrinks the horizontal scale term.

    **WHY:** Without the aspect ratio the cube would stretch in any window that
    is not square.
    """
    scene.aspect_ratio = 1.0
    square = scene.projection_matrix().column(0).x()
    scene.aspect_ratio = 2.0
    wide = scene.projection_matrix().column(0).x()
    assert wide == pytest.approx(square / 2.0)


def test_camera_position_distance_equals_distance(scene):
    """Without pan, the camera is at the zoom distance on +Z; with pan, offset.

    **WHY:** The cube shader computes specular highlights from the camera
    position, so it must agree with the view matrix, pan included.
    """
    assert scene.camera_position().length() == pytest.approx(scene.distance)
    scene.pan_by(QPointF(10.0, 5.0), 100)
    camera = scene.camera_position()
    assert (camera.x(), camera.y(), camera.z()) == pytest.approx(
        (-scene.pan.x(), -scene.pan.y(), scene.distance)
    )


def test_light_dot_position_is_on_the_sphere(scene):
    """The light dot sits at SPHERE_RADIUS along the light direction.

    **WHY:** The yellow dot marks the light direction on the sphere; off the
    sphere it would float inside or outside the grid.
    """
    scene.move_light_by(QPointF(15.0, -9.0))
    dot = scene.light_dot_position()
    assert dot.length() == pytest.approx(config.SPHERE_RADIUS)
    assert QVector3D.dotProduct(dot.normalized(), scene.light) == pytest.approx(1.0)
