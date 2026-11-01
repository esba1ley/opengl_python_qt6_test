"""Vertex data for the cube, the sphere grid and the axes.

The sphere uses geographic coordinates with its poles on the Z axis.
"""
import numpy as np

import config

VERTEX_ATTRIBUTES = (
    ("position", 3),
    ("normal", 3),
    ("tangent", 3),
    ("bitangent", 3),
    ("uv", 2),
    ("layer", 1),
)
FLOATS_PER_VERTEX = sum(size for _, size in VERTEX_ATTRIBUTES)


def cube_vertices():
    """Build the vertex data for a 2x2x2 cube centred on the origin.

    Each face has its own vertices, so it can have its own normal, tangent axes
    and texture layer. The face order matches ``MATERIALS``.

    Returns
    -------
    list of float
        36 vertices laid out as described by ``VERTEX_ATTRIBUTES``.
    """
    faces = ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1))
    data = []
    for layer, (axis, sign) in enumerate(faces):
        u, v = [i for i in range(3) if i != axis]
        normal, tangent, bitangent = [0.0] * 3, [0.0] * 3, [0.0] * 3
        normal[axis] = float(sign)
        tangent[u] = 1.0
        bitangent[v] = 1.0
        corners = []
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            point = [0.0, 0.0, 0.0]
            point[axis], point[u], point[v] = float(sign), float(a), float(b)
            corners.append((point, (a + 1) / 2.0, (b + 1) / 2.0))
        for index in (0, 1, 2, 0, 2, 3):
            point, tex_u, tex_v = corners[index]
            data += [*point, *normal, *tangent, *bitangent, tex_u, tex_v, float(layer)]
    return data


def sphere_points(latitude, longitude):
    """Convert latitude and longitude to points on the sphere.

    The poles are on the Z axis, +X is at latitude 0 and longitude 0, and +Y is at
    latitude 0 and longitude +90.

    Parameters
    ----------
    latitude : numpy.ndarray or float
        Latitudes, in degrees.
    longitude : numpy.ndarray or float
        Longitudes, in degrees. Must be broadcastable with `latitude`.

    Returns
    -------
    numpy.ndarray
        Cartesian points of shape ``(..., 3)``, at radius
        ``config.SPHERE_RADIUS``.
    """
    lat, lon = np.radians(latitude), np.radians(longitude)
    return config.SPHERE_RADIUS * np.stack(
        (np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)), axis=-1
    )


def curve_to_segments(points):
    """Convert a polyline into pairs of points for ``GL_LINES``.

    Parameters
    ----------
    points : numpy.ndarray
        Polyline of shape ``(n, 3)``.

    Returns
    -------
    numpy.ndarray
        Segment endpoints of shape ``(2 * n - 2, 3)``.
    """
    return np.repeat(points, 2, axis=0)[1:-1]


def with_color(points, color):
    """Append the same colour to every point.

    Parameters
    ----------
    points : numpy.ndarray
        Points of shape ``(n, 3)``.
    color : sequence of float
        RGB colour.

    Returns
    -------
    numpy.ndarray
        Vertices of shape ``(n, 6)``, laid out as position then colour.
    """
    return np.hstack((points, np.tile(color, (len(points), 1))))


def grid_vertices():
    """Build the latitude and longitude lines of the sphere.

    Longitude lines run pole to pole every ``config.LONGITUDE_STEP`` degrees.
    Latitude lines are spaced ``config.LATITUDE_STEP`` degrees apart, excluding
    the poles.

    Returns
    -------
    numpy.ndarray
        ``GL_LINES`` vertices of shape ``(n, 6)``. The colour columns are unused,
        because the fragment shader chooses the gray for each side of the sphere.
    """
    curves = []
    step = config.CURVE_STEP_DEGREES
    meridian_lat = np.arange(-90.0, 90.0 + step, step)
    for longitude in range(0, 360, config.LONGITUDE_STEP):
        curves.append(sphere_points(meridian_lat, np.full_like(meridian_lat, longitude)))
    parallel_lon = np.arange(0.0, 360.0 + step, step)
    for latitude in range(config.LATITUDE_STEP - 90, 90, config.LATITUDE_STEP):
        curves.append(sphere_points(np.full_like(parallel_lon, latitude), parallel_lon))
    segments = np.vstack([curve_to_segments(curve) for curve in curves])
    return with_color(segments, (0.0, 0.0, 0.0))  # the shader picks the grey


def axis_vertices():
    """Build the +X, +Y and +Z axes as red, green and blue lines.

    Each line runs from the origin to the surface of the sphere.

    Returns
    -------
    numpy.ndarray
        ``GL_LINES`` vertices of shape ``(6, 6)``, laid out as position then
        colour.
    """
    data = []
    for axis in range(3):
        tip = np.zeros(3)
        tip[axis] = config.SPHERE_RADIUS
        color = np.zeros(3)
        color[axis] = 1.0
        data += [(0, 0, 0, *color), (*tip, *color)]
    return np.array(data)
