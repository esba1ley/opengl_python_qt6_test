"""Tests for the vertex builders in ``geometry``."""
import numpy as np

import config
import geometry


def test_cube_vertices_count_and_layers():
    """The cube has 36 vertices and layers 0 to 5, six vertices each.

    **WHY:** The cube is drawn as 36 vertices, and each face selects its
    material by texture layer. A wrong count truncates the draw, and a wrong
    layer puts the wrong material on a face.
    """
    data = np.array(geometry.cube_vertices())
    assert data.size == 36 * geometry.FLOATS_PER_VERTEX
    layers = data.reshape(36, geometry.FLOATS_PER_VERTEX)[:, -1]
    assert sorted(set(layers)) == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert all(np.count_nonzero(layers == k) == 6 for k in range(6))


def test_cube_vertices_lie_on_faces_with_matching_normals():
    """Each vertex sits on its face plane, offset along its own normal.

    **WHY:** A normal that does not point out of its face lights that face from
    the wrong side, which looks plausible in a frame and is easy to miss by
    eye.
    """
    rows = np.array(geometry.cube_vertices()).reshape(36, -1)
    position, normal = rows[:, 0:3], rows[:, 3:6]
    assert np.allclose(np.abs(position).max(axis=1), 1.0)
    assert np.allclose(np.sum(position * normal, axis=1), 1.0)


def test_sphere_points_poles_and_equator():
    """Poles lie on Z, and latitude/longitude 0 and 90 lie on +X and +Y.

    **WHY:** This pins the convention in the README's sphere coordinate table:
    poles on Z, longitude from +X towards +Y. A swapped angle would rotate the
    whole grid relative to the axes.
    """
    r = config.SPHERE_RADIUS
    assert np.allclose(geometry.sphere_points(90.0, 0.0), [0, 0, r], atol=1e-12)
    assert np.allclose(geometry.sphere_points(-90.0, 0.0), [0, 0, -r], atol=1e-12)
    assert np.allclose(geometry.sphere_points(0.0, 0.0), [r, 0, 0], atol=1e-12)
    assert np.allclose(geometry.sphere_points(0.0, 90.0), [0, r, 0], atol=1e-12)


def test_sphere_points_broadcasts():
    """Latitude and longitude arrays broadcast to shape (..., 3).

    **WHY:** ``grid_vertices`` passes whole arrays of angles, so the function
    must accept arrays as well as scalars.
    """
    points = geometry.sphere_points(np.array([0.0, 10.0, 20.0]), 5.0)
    assert points.shape == (3, 3)


def test_curve_to_segments_doubles_interior_points():
    """Interior points appear twice and the endpoints once.

    **WHY:** ``GL_LINES`` draws independent pairs of points. Without the
    doubling, every other segment of each grid curve would be missing and the
    grid would draw dashed.
    """
    points = np.arange(12, dtype=float).reshape(4, 3)
    segments = geometry.curve_to_segments(points)
    assert segments.shape == (6, 3)
    assert np.array_equal(segments[0], points[0])
    assert np.array_equal(segments[-1], points[-1])
    assert np.array_equal(segments[1], segments[2])
    assert np.array_equal(segments[1], points[1])


def test_with_color_appends_color_to_every_point():
    """Colour columns are broadcast to every row after the position.

    **WHY:** The overlay's vertex layout is position then colour. A colour that
    did not reach every row would shift the layout of every vertex after it.
    """
    points = np.zeros((5, 3))
    out = geometry.with_color(points, (0.1, 0.2, 0.3))
    assert out.shape == (5, 6)
    assert np.allclose(out[:, 3:], [0.1, 0.2, 0.3])


def test_grid_vertices_count_and_radius():
    """The grid has the expected segment count and lies on the sphere.

    **WHY:** The overlay renderer splits one vertex buffer into grid, axes and
    dot by these counts, so a wrong count draws the axes from the wrong
    vertices. Every grid point must also lie on the sphere.
    """
    grid = geometry.grid_vertices()
    points_per_curve_lon = len(np.arange(-90.0, 90.0 + config.CURVE_STEP_DEGREES,
                                         config.CURVE_STEP_DEGREES))
    points_per_curve_lat = len(np.arange(0.0, 360.0 + config.CURVE_STEP_DEGREES,
                                         config.CURVE_STEP_DEGREES))
    meridians = len(range(0, 360, config.LONGITUDE_STEP))
    parallels = len(range(config.LATITUDE_STEP - 90, 90, config.LATITUDE_STEP))
    expected = (meridians * (2 * points_per_curve_lon - 2)
                + parallels * (2 * points_per_curve_lat - 2))
    assert grid.shape == (expected, 6)
    assert np.allclose(np.linalg.norm(grid[:, :3], axis=1), config.SPHERE_RADIUS)
    assert np.all(grid[:, 3:] == 0.0)


def test_axis_vertices_shape_and_extent():
    """Each axis runs from the origin to the sphere in its own colour.

    **WHY:** The axes are the reference for the README's colour key: X red, Y
    green, Z blue, from the origin to the sphere.
    """
    axes = geometry.axis_vertices()
    assert axes.shape == (6, 6)
    for axis in range(3):
        start, end = axes[2 * axis], axes[2 * axis + 1]
        assert np.all(start[:3] == 0.0)
        expected_tip = np.zeros(3)
        expected_tip[axis] = config.SPHERE_RADIUS
        assert np.allclose(end[:3], expected_tip)
        expected_color = np.zeros(3)
        expected_color[axis] = 1.0
        assert np.allclose(start[3:], expected_color)
        assert np.allclose(end[3:], expected_color)

