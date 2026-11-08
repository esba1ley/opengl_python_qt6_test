"""Procedural materials and normal maps for the cube faces.

This module only uses NumPy, so it works without an OpenGL context.
"""
from typing import NamedTuple

import numpy as np

import config


def smoothstep(low, high, x):
    """Interpolate smoothly from 0 to 1 between two thresholds.

    Parameters
    ----------
    low : float
        Input value that maps to 0.
    high : float
        Input value that maps to 1. Must differ from `low`.
    x : numpy.ndarray
        Values to interpolate.

    Returns
    -------
    numpy.ndarray
        Values from 0 to 1, with the same shape as `x`.
    """
    t = np.clip((x - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, t):
    """Blend two colours or values using a mask.

    Parameters
    ----------
    a : array_like
        Value used where `t` is 0. Either a single RGB colour, a 2D field or an
        RGB image.
    b : array_like
        Value used where `t` is 1, in the same forms as `a`.
    t : numpy.ndarray
        2D blend mask, with values from 0 to 1.

    Returns
    -------
    numpy.ndarray
        The blended result. It is an RGB image if either input is a colour or an
        image, and a 2D field otherwise.
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.ndim == 1 or b.ndim == 1 or a.ndim == 3 or b.ndim == 3:
        t = t[..., None]
    return a * (1.0 - t) + b * t


def uv_grid(size):
    """Create texture coordinates for a square image.

    Parameters
    ----------
    size : int
        Width and height of the image, in pixels.

    Returns
    -------
    u : numpy.ndarray
        Horizontal coordinates from 0 to 1, of shape ``(size, size)``.
    v : numpy.ndarray
        Vertical coordinates from 0 to 1, of shape ``(size, size)``.
    """
    v, u = np.mgrid[0:size, 0:size] / size
    return u, v


def value_noise(size, cells, rng):
    """Generate one octave of smooth value noise.

    Parameters
    ----------
    size : int
        Width and height of the output, in pixels.
    cells : int
        Number of random grid cells along each side. More cells give finer
        detail.
    rng : numpy.random.Generator
        Source of randomness.

    Returns
    -------
    numpy.ndarray
        Noise of shape ``(size, size)``, with values from 0 to 1.
    """
    grid = rng.random((cells + 1, cells + 1))
    position = np.linspace(0, cells, size, endpoint=False)
    index = position.astype(int)
    fraction = position - index
    fraction = fraction * fraction * (3.0 - 2.0 * fraction)
    fx, fy = fraction[None, :], fraction[:, None]
    top = grid[np.ix_(index, index)] * (1 - fx) + grid[np.ix_(index, index + 1)] * fx
    low = (
        grid[np.ix_(index + 1, index)] * (1 - fx)
        + grid[np.ix_(index + 1, index + 1)] * fx
    )
    return top * (1 - fy) + low * fy


def fractal_noise(size, rng, cells=4, octaves=5):
    """Generate noise by summing octaves of value noise.

    Each octave doubles the number of cells and halves the amplitude.

    Parameters
    ----------
    size : int
        Width and height of the output, in pixels.
    rng : numpy.random.Generator
        Source of randomness.
    cells : int, optional
        Number of grid cells along each side in the first octave.
    octaves : int, optional
        Number of octaves to sum.

    Returns
    -------
    numpy.ndarray
        Noise of shape ``(size, size)``, normalised to the range 0 to 1.
    """
    total = np.zeros((size, size))
    amplitude = 1.0
    for _ in range(octaves):
        total += amplitude * value_noise(size, cells, rng)
        amplitude *= 0.5
        cells *= 2
    return (total - total.min()) / np.ptp(total)


def seam(f):
    """Measure how far a position inside a cell is from the nearest cell edge.

    ``f`` is a fraction across one cell: 0 at its left edge, 1 at its right
    edge. The nearest edge is the left one when ``f`` is below one half and the
    right one otherwise, so the result is ``min(f, 1 - f)``. It rises linearly
    from 0 at either edge to 0.5 at the centre, a triangle wave of period 1.

    Parameters
    ----------
    f : numpy.ndarray
        Fraction across a cell, from 0 to 1, in cell widths.

    Returns
    -------
    numpy.ndarray
        Distance to the nearest edge, from 0 to 0.5, in cell widths. Same shape
        as ``f``.
    """
    return np.minimum(f, 1 - f)


def cell_lattice(u, v, columns, rows, stagger=0.0):
    """Divide the texture into a lattice of cells, optionally staggered.

    Scaling ``u`` by ``columns`` and ``v`` by ``rows`` makes each cell one unit
    wide and tall. The integer part of a scaled coordinate says which cell a
    pixel is in; the fractional part says where it is inside that cell. Odd
    rows are shifted sideways by ``stagger`` cells, which turns a square grid
    into running-bond brickwork when ``stagger`` is 0.5.

    Parameters
    ----------
    u, v : numpy.ndarray
        Texture coordinates, from 0 to 1.
    columns, rows : int
        Number of cells across and down the texture.
    stagger : float, optional
        Sideways shift of odd rows, in cell widths. The default 0 gives a
        plain grid.

    Returns
    -------
    column, row : numpy.ndarray
        Whole-number cell indices, stored as floats. ``row`` runs from 0 to
        ``rows - 1``; ``column`` runs from 0 to ``columns - 1``, or to
        ``columns`` when ``stagger`` is positive.
    fx, fy : numpy.ndarray
        Position inside the cell, from 0 up to but not including 1, in cell
        widths and heights.
    """
    scaled_v = v * rows
    row = np.floor(scaled_v)
    x = u * columns + stagger * (row % 2)
    column = np.floor(x)
    return column, row, x - column, scaled_v - row


def edge_distance(fx, fy, columns, rows):
    """Measure the distance to the nearest edge of a cell, in texture units.

    :func:`seam` gives the distance to the nearest edge along each axis in
    cell widths. Dividing by ``columns`` and ``rows`` converts them to texture
    coordinate units, so a cell that is wider than it is tall still gets a
    border of equal thickness on all sides. The smaller of the two is the
    distance to the nearest edge of either kind.

    Parameters
    ----------
    fx, fy : numpy.ndarray
        Position inside the cell, from 0 to 1, as returned by
        :func:`cell_lattice`.
    columns, rows : int
        Number of cells across and down the texture.

    Returns
    -------
    numpy.ndarray
        Distance to the nearest cell edge, in texture coordinate units: 0 on
        an edge, and at most ``0.5 / max(columns, rows)`` at a cell centre.
    """
    return np.minimum(seam(fx) / columns, seam(fy) / rows)


def checker(column, row):
    """Alternate between two values like the squares of a chessboard.

    Neighbouring cells differ by one in ``column + row``, so the parity of the
    sum flips from cell to cell in both directions.

    Parameters
    ----------
    column, row : numpy.ndarray
        Whole-number cell indices, as returned by :func:`cell_lattice`.

    Returns
    -------
    numpy.ndarray
        Float array of 0.0 and 1.0, 0 where ``column + row`` is even. It is
        kept as a float so :func:`mix` can use it directly as a blend weight.
    """
    return (column + row) % 2


def voronoi(u, v, points):
    """Assign every pixel to its nearest point and measure how contested it is.

    A Voronoi diagram splits the plane into regions, each holding the pixels
    closer to one seed point than to any other. The gap between the nearest
    and second-nearest distance is zero on the border between two regions and
    grows towards the middle of a region, so it works as an edge detector.

    The distance to every point is computed for every pixel, a volume of
    ``size * size * len(points)`` values. It is stored as ``float32`` to halve
    its memory; the gap is therefore ``float32`` too.

    Parameters
    ----------
    u, v : numpy.ndarray
        Texture coordinates, from 0 to 1, each of shape ``(size, size)``.
    points : numpy.ndarray
        Seed points of shape ``(n, 2)`` with ``n >= 2``, as ``(u, v)`` pairs
        in texture coordinate units.

    Returns
    -------
    nearest : numpy.ndarray
        Integer index into ``points`` of the closest point, shape
        ``(size, size)``.
    gap : numpy.ndarray
        Second-nearest minus nearest distance, in texture coordinate units,
        ``float32`` of shape ``(size, size)``. Never negative.
    """
    distance = np.hypot(
        u[..., None] - points[:, 0], v[..., None] - points[:, 1]
    ).astype(np.float32)
    nearest = distance.argmin(axis=2)
    closest = np.partition(distance, 1, axis=2)
    gap = closest[..., 1] - closest[..., 0]
    return nearest, gap


def dome(fx, fy, radius):
    """Give the height of a hemisphere centred in a cell.

    With ``r`` the distance from the cell centre as a fraction of ``radius``,
    a hemisphere of unit radius has height ``sqrt(1 - r**2)``. Outside the
    radius that is not real, so ``1 - r**2`` is clipped at 0 and the dome
    meets a flat floor.

    Parameters
    ----------
    fx, fy : numpy.ndarray
        Position relative to the dome centre, in the same units as
        ``radius``, so 0 is the centre. Pass ``fx - 0.5`` for a cell
        fraction.
    radius : float
        Radius of the dome, in the units of ``fx`` and ``fy``.

    Returns
    -------
    numpy.ndarray
        Height from 0 at and beyond ``radius`` to 1 at the centre.
    """
    r = np.hypot(fx, fy) / radius
    return np.sqrt(np.clip(1.0 - r * r, 0.0, 1.0))


class Material(NamedTuple):
    """The result of building one material: its layers and how it was built.

    A material is built in small steps, each producing an image or a field
    that a person can look at. Keeping them lets the documentation show how a
    flat brick wall grows from a distance field, a mask and some noise, rather
    than only the finished result.

    Parameters
    ----------
    color : numpy.ndarray
        Float RGB image of shape ``(size, size, 3)``, with values from 0 to 1.
    height : numpy.ndarray
        Float height field of shape ``(size, size)``, where 1 is highest.
    steps : dict
        Intermediate results in the order they were built, from a short
        readable step name to the array at that step: either a 2D field of
        shape ``(size, size)`` or an RGB image of shape ``(size, size, 3)``.
        The last two entries are ``"colour"`` and ``"height"``, the same
        arrays as `color` and `height`. Nothing recorded here is changed
        after it is stored.
    """

    color: np.ndarray
    height: np.ndarray
    steps: dict


def bricks(size, rng):
    """Generate a staggered red brick wall with recessed mortar.

    Parameters
    ----------
    size : int
        Width and height of the texture, in pixels.
    rng : numpy.random.Generator
        Source of randomness for the brick shades and surface noise.

    Returns
    -------
    Material
        The colour, the height and the build steps: ``"distance to edge"``,
        ``"mortar mask"``, ``"surface noise"``, ``"brick shade"``,
        ``"brick colour"``, ``"colour"`` and ``"height"``.
    """
    u, v = uv_grid(size)
    rows, columns = 8, 4
    column, row, fx, fy = cell_lattice(u, v, columns, rows, stagger=0.5)
    distance = edge_distance(fx, fy, columns, rows)
    mask = smoothstep(0.008, 0.02, distance)
    noise = fractal_noise(size, rng, cells=8)
    shade = rng.random((rows, columns + 2))[row.astype(int), column.astype(int)]
    brick = mix([0.62, 0.22, 0.16], [0.80, 0.36, 0.24], shade * 0.6 + noise * 0.4)
    color = mix([0.62, 0.60, 0.55], brick, mask)
    height = mask * (0.85 + 0.15 * noise)
    steps = {
        "distance to edge": distance,
        "mortar mask": mask,
        "surface noise": noise,
        "brick shade": shade,
        "brick colour": brick,
        "colour": color,
        "height": height,
    }
    return Material(color, height, steps)


def cobbles(size, rng):
    """Generate irregular cobblestones from a Voronoi pattern.

    Parameters
    ----------
    size : int
        Width and height of the texture, in pixels.
    rng : numpy.random.Generator
        Source of randomness for the stone positions, shades and surface noise.

    Returns
    -------
    Material
        The colour, the height and the build steps: ``"distance gap"``,
        ``"mortar mask"``, ``"surface noise"``, ``"stone shade"``,
        ``"stone colour"``, ``"colour"`` and ``"height"``.
    """
    u, v = uv_grid(size)
    points = rng.random((40, 2))
    nearest, gap = voronoi(u, v, points)
    mask = smoothstep(0.0, 0.05, gap)
    noise = fractal_noise(size, rng, cells=8)
    shade = rng.random(len(points))[nearest]
    stone = mix([0.42, 0.42, 0.44], [0.72, 0.70, 0.66], shade * 0.7 + noise * 0.3)
    color = mix([0.16, 0.14, 0.12], stone, mask)
    height = mask * (0.8 + 0.2 * noise)
    steps = {
        "distance gap": gap,
        "mortar mask": mask,
        "surface noise": noise,
        "stone shade": shade,
        "stone colour": stone,
        "colour": color,
        "height": height,
    }
    return Material(color, height, steps)


def tiles(size, rng):
    """Generate a checkerboard of bevelled teal and cream tiles.

    Parameters
    ----------
    size : int
        Width and height of the texture, in pixels.
    rng : numpy.random.Generator
        Source of randomness. It is unused, but keeps the signature shared by all
        materials.

    Returns
    -------
    Material
        The colour, the height and the build steps: ``"distance to edge"``,
        ``"grout mask"``, ``"checker"``, ``"glaze"``, ``"colour"`` and
        ``"height"``.
    """
    u, v = uv_grid(size)
    count = 4
    column, row, fx, fy = cell_lattice(u, v, count, count)
    distance = edge_distance(fx, fy, count, count)
    mask = smoothstep(0.004, 0.03, distance)
    parity = checker(column, row)
    glaze = mix([0.10, 0.48, 0.50], [0.82, 0.86, 0.80], parity)
    color = mix([0.30, 0.28, 0.26], glaze, smoothstep(0.0, 0.3, mask))
    steps = {
        "distance to edge": distance,
        "grout mask": mask,
        "checker": parity,
        "glaze": glaze,
        "colour": color,
        "height": mask,
    }
    return Material(color, mask, steps)


def wood(size, rng):
    """Generate vertical wooden planks with a wavy grain.

    Parameters
    ----------
    size : int
        Width and height of the texture, in pixels.
    rng : numpy.random.Generator
        Source of randomness for the plank offsets and grain wobble.

    Returns
    -------
    Material
        The colour, the height and the build steps: ``"plank offset"``,
        ``"grain wobble"``, ``"grain"``, ``"plank gap"``, ``"wood colour"``,
        ``"colour"`` and ``"height"``.
    """
    u, v = uv_grid(size)
    planks = 5
    plank = np.floor(u * planks)
    x = u * planks - plank
    offset = rng.random(planks)[plank.astype(int)]
    wobble = fractal_noise(size, rng, cells=3, octaves=4)
    grain = 0.5 + 0.5 * np.sin(38.0 * (x + 0.5 * wobble + offset) + 3.0 * v)
    gap = smoothstep(0.0, 0.03, seam(x))
    wood_color = mix(
        [0.36, 0.20, 0.09], [0.68, 0.45, 0.24], grain * (0.6 + 0.4 * offset)
    )
    color = mix([0.08, 0.05, 0.03], wood_color, gap)
    height = gap * (0.85 + 0.15 * grain)
    steps = {
        "plank offset": offset,
        "grain wobble": wobble,
        "grain": grain,
        "plank gap": gap,
        "wood colour": wood_color,
        "colour": color,
        "height": height,
    }
    return Material(color, height, steps)


def rivets(size, rng):
    """Generate a brushed metal plate with a grid of domed rivets.

    Parameters
    ----------
    size : int
        Width and height of the texture, in pixels.
    rng : numpy.random.Generator
        Source of randomness for the brushed finish.

    Returns
    -------
    Material
        The colour, the height and the build steps: ``"dome"``,
        ``"brushed streaks"``, ``"brushed finish"``, ``"plate colour"``,
        ``"colour"`` and ``"height"``.
    """
    u, v = uv_grid(size)
    count = 5
    _, _, fx, fy = cell_lattice(u, v, count, count)
    bump = dome(fx - 0.5, fy - 0.5, 0.16)
    streaks = np.tile(rng.random((size, 1)), (1, size))
    brushed = 0.5 * streaks + 0.5 * fractal_noise(size, rng, cells=6)
    plate = mix([0.42, 0.44, 0.48], [0.62, 0.64, 0.68], brushed)
    color = mix(plate, [0.74, 0.74, 0.76], bump)
    height = 0.8 * bump + 0.04 * brushed
    steps = {
        "dome": bump,
        "brushed streaks": streaks,
        "brushed finish": brushed,
        "plate colour": plate,
        "colour": color,
        "height": height,
    }
    return Material(color, height, steps)


def weave(size, rng):
    """Generate a basket weave of straw strands.

    Parameters
    ----------
    size : int
        Width and height of the texture, in pixels.
    rng : numpy.random.Generator
        Source of randomness. It is unused, but keeps the signature shared by all
        materials.

    Returns
    -------
    Material
        The colour, the height and the build steps: ``"over or under"`` (1
        where the strand running across is on top), ``"strands across"``,
        ``"strands along"``, ``"height"`` and ``"colour"``.
    """
    u, v = uv_grid(size)
    count = 10
    column, row, fx, fy = cell_lattice(u, v, count, count)
    over = checker(column, row) == 0
    across = np.sin(np.pi * fy) * (0.55 + 0.45 * np.sin(np.pi * fx))
    along = np.sin(np.pi * fx) * (0.55 + 0.45 * np.sin(np.pi * fy))
    height = np.where(over, across, along)
    color = mix([0.30, 0.22, 0.10], [0.86, 0.72, 0.42], height)
    steps = {
        "over or under": over.astype(float),
        "strands across": across,
        "strands along": along,
        "height": height,
        "colour": color,
    }
    return Material(color, height, steps)


# Texture layer order; matches the faces in cube_vertices().
MATERIALS = (bricks, cobbles, tiles, weave, rivets, wood)


def height_to_normals(height):
    """Encode a height field as a tangent-space normal map.

    Parameters
    ----------
    height : numpy.ndarray
        2D height field. Rows run along v and columns along u, matching the
        tangent and bitangent in `cube_vertices`.

    Returns
    -------
    numpy.ndarray
        Normals of shape ``(rows, columns, 3)``, encoded from the range -1 to 1
        into 0 to 1 so they can be stored as RGB. The relief is scaled by
        ``config.BUMP_STRENGTH``.
    """
    # Rows run along v and columns along u, matching the tangent and bitangent.
    slope_v, slope_u = np.gradient(height)
    strength = config.BUMP_STRENGTH * height.shape[0]
    normals = np.dstack(
        (-slope_u * strength, -slope_v * strength, np.ones_like(height))
    )
    normals /= np.linalg.norm(normals, axis=2, keepdims=True)
    return normals * 0.5 + 0.5


def to_rgba_bytes(images):
    """Stack float RGB images into bytes for a texture array.

    Parameters
    ----------
    images : sequence of numpy.ndarray
        Same-sized float RGB images. Values outside 0 to 1 are clipped.

    Returns
    -------
    bytes
        Tightly packed RGBA8 pixels with opaque alpha, one image per layer.
    """
    rgb = np.clip(np.stack(images), 0.0, 1.0)
    alpha = np.ones((*rgb.shape[:3], 1))
    return (np.concatenate((rgb, alpha), axis=3) * 255.0 + 0.5).astype(np.uint8).tobytes()


def iter_materials(size, seed=None):
    """Build every material in layer order, one at a time.

    All materials share one random generator, so each one draws from where
    the previous one stopped. Building them through this function therefore
    gives exactly the layers that :func:`generate_texture_layers` packs.

    Parameters
    ----------
    size : int
        Width and height of every texture, in pixels.
    seed : int, optional
        Seed for the random generator. The default, ``None``, uses
        ``config.TEXTURE_SEED`` as it is when the function is called.

    Yields
    ------
    function : callable
        The material function, one of `MATERIALS`.
    material : Material
        The result of calling it with `size`.
    """
    if seed is None:
        seed = config.TEXTURE_SEED
    rng = np.random.default_rng(seed)
    for function in MATERIALS:
        yield function, function(size, rng)


def generate_texture_layers():
    """Generate the colour and normal maps for every material.

    Only each material's colour and height are kept, so the intermediate
    steps are freed as soon as the next material starts.

    Returns
    -------
    albedo : bytes
        RGBA8 colour pixels, one layer per material.
    normals : bytes
        RGBA8 normal map pixels, one layer per material.
    layers : int
        Number of layers.
    """
    colors, heights = [], []
    for _, material in iter_materials(config.TEXTURE_SIZE):
        colors.append(material.color)
        heights.append(material.height)
    albedo = to_rgba_bytes(colors)
    normals = to_rgba_bytes([height_to_normals(height) for height in heights])
    return albedo, normals, len(colors)
