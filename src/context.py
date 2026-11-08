"""The scene state shared by the widget, the renderers and the self-test."""
from PyQt6.QtGui import QMatrix4x4, QQuaternion, QVector3D

import config


def screen_rotation(delta):
    """Turn a mouse drag into a rotation about the screen axes.

    Using screen axes means a drag always follows the cursor, whatever the
    current orientation.

    Parameters
    ----------
    delta : PyQt6.QtCore.QPointF
        Mouse movement, in pixels.

    Returns
    -------
    PyQt6.QtGui.QQuaternion
        The rotation. It is the identity for a zero-length drag.
    """
    axis = QVector3D(delta.y(), delta.x(), 0.0)
    degrees = axis.length() * config.ROTATE_DEGREES_PER_PIXEL
    if degrees == 0.0:
        return QQuaternion()
    return QQuaternion.fromAxisAndAngle(axis.normalized(), degrees)


class SceneContext:
    """Everything the scene needs to know about the view and the light.

    The widget changes this state in response to input, and the renderers read
    it to draw a frame. Neither needs to know about the other.

    Attributes
    ----------
    rotation : PyQt6.QtGui.QQuaternion
        Orientation of the cube, sphere and axes.
    distance : float
        Distance from the camera to the origin.
    pan : PyQt6.QtGui.QVector3D
        Sideways and vertical camera offset.
    light : PyQt6.QtGui.QVector3D
        Unit vector pointing towards the light, in world space.
    aspect_ratio : float
        Viewport width divided by height.
    pixel_ratio : float
        Device pixels per logical pixel.
    cube_view : int
        Index into ``shaders.CUBE_VIEWS`` of the cube's debug view. Kept by
        ``reset_view``.
    """

    def __init__(self):
        """Start with the default view and a square viewport."""
        self.aspect_ratio = 1.0
        self.pixel_ratio = 1.0
        self.cube_view = config.DEFAULT_CUBE_VIEW
        self.reset_view()

    def reset_view(self):
        """Restore the default rotation, distance, pan and light."""
        self.rotation = QQuaternion.fromEulerAngles(
            config.DEFAULT_PITCH_DEGREES, config.DEFAULT_YAW_DEGREES, 0.0
        )
        self.distance = config.DEFAULT_DISTANCE
        self.pan = QVector3D(0.0, 0.0, 0.0)
        self.light = config.DEFAULT_LIGHT

    # --- Changing the scene ---

    def rotate_by(self, delta):
        """Rotate the cube, sphere and axes.

        Parameters
        ----------
        delta : PyQt6.QtCore.QPointF
            Mouse movement, in pixels.
        """
        self.rotation = (screen_rotation(delta) * self.rotation).normalized()

    def move_light_by(self, delta):
        """Move the light around the origin.

        Parameters
        ----------
        delta : PyQt6.QtCore.QPointF
            Mouse movement, in pixels.
        """
        self.light = screen_rotation(delta).rotatedVector(self.light).normalized()

    def pan_by(self, delta, viewport_height):
        """Move the camera sideways and vertically.

        Parameters
        ----------
        delta : PyQt6.QtCore.QPointF
            Mouse movement, in pixels.
        viewport_height : int
            Viewport height, in pixels. Together with the distance, this keeps
            the scene roughly under the cursor.
        """
        scale = 0.8 * self.distance / max(viewport_height, 1)
        self.pan += QVector3D(delta.x() * scale, -delta.y() * scale, 0.0)

    def zoom_by(self, notches):
        """Zoom, keeping the distance within the allowed range.

        Parameters
        ----------
        notches : float
            Mouse wheel notches. Positive values zoom in.
        """
        distance = self.distance * config.ZOOM_FACTOR_PER_NOTCH**notches
        self.distance = min(max(distance, config.MIN_DISTANCE), config.MAX_DISTANCE)

    # --- Reading the scene ---

    def model_matrix(self):
        """Build the rotation shared by the cube, sphere and axes.

        Returns
        -------
        PyQt6.QtGui.QMatrix4x4
            Transform from model space to world space.
        """
        model = QMatrix4x4()
        model.rotate(self.rotation)
        return model

    def view_matrix(self):
        """Build the view matrix from the zoom and pan.

        Returns
        -------
        PyQt6.QtGui.QMatrix4x4
            Transform from world space to camera space.
        """
        view = QMatrix4x4()
        view.translate(self.pan.x(), self.pan.y(), -self.distance)
        return view

    def projection_matrix(self):
        """Build the perspective matrix for the viewport.

        Returns
        -------
        PyQt6.QtGui.QMatrix4x4
            Transform from camera space to clip space.
        """
        projection = QMatrix4x4()
        projection.perspective(
            config.FOV_DEGREES, self.aspect_ratio, config.NEAR_PLANE, config.FAR_PLANE
        )
        return projection

    def view_projection_matrix(self):
        """Combine the projection and view matrices.

        Returns
        -------
        PyQt6.QtGui.QMatrix4x4
            Transform from world space to clip space.
        """
        return self.projection_matrix() * self.view_matrix()

    def camera_position(self):
        """Find the camera in world space.

        Returns
        -------
        PyQt6.QtGui.QVector3D
            Camera position. The view only translates, so this is the inverse
            of that translation.
        """
        return QVector3D(-self.pan.x(), -self.pan.y(), self.distance)

    def light_dot_position(self):
        """Find where the direction to the light meets the sphere.

        Returns
        -------
        PyQt6.QtGui.QVector3D
            Position of the light dot, in world space.
        """
        return self.light * config.SPHERE_RADIUS
