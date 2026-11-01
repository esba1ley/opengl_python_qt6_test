"""Procedural materials and normal maps for the cube faces.

This module only uses NumPy, so it works without an OpenGL context.
"""
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
    color : numpy.ndarray
        Float RGB image of shape ``(size, size, 3)``, with values from 0 to 1.
    height : numpy.ndarray
        Float height field of shape ``(size, size)``, where 1 is highest.
    """
    u, v = uv_grid(size)
    rows, columns = 8, 4
    row = np.floor(v * rows)
    x = u * columns + 0.5 * (row % 2)
    column = np.floor(x)
    fx, fy = x - column, v * rows - row
    edge = np.minimum(
        np.minimum(fx, 1 - fx) / columns, np.minimum(fy, 1 - fy) / rows
    )
    mask = smoothstep(0.008, 0.02, edge)
    noise = fractal_noise(size, rng, cells=8)
    shade = rng.random((rows, columns + 2))[row.astype(int), column.astype(int)]
    brick = mix([0.62, 0.22, 0.16], [0.80, 0.36, 0.24], shade * 0.6 + noise * 0.4)
    return mix([0.62, 0.60, 0.55], brick, mask), mask * (0.85 + 0.15 * noise)


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
    color : numpy.ndarray
        Float RGB image of shape ``(size, size, 3)``, with values from 0 to 1.
    height : numpy.ndarray
        Float height field of shape ``(size, size)``, where 1 is highest.
    """
    u, v = uv_grid(size)
    points = rng.random((40, 2))
    distance = np.hypot(
        u[..., None] - points[:, 0], v[..., None] - points[:, 1]
    ).astype(np.float32)
    nearest = distance.argmin(axis=2)
    closest = np.partition(distance, 1, axis=2)
    gap = closest[..., 1] - closest[..., 0]
    mask = smoothstep(0.0, 0.05, gap)
    noise = fractal_noise(size, rng, cells=8)
    shade = rng.random(len(points))[nearest]
    stone = mix([0.42, 0.42, 0.44], [0.72, 0.70, 0.66], shade * 0.7 + noise * 0.3)
    return mix([0.16, 0.14, 0.12], stone, mask), mask * (0.8 + 0.2 * noise)


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
    color : numpy.ndarray
        Float RGB image of shape ``(size, size, 3)``, with values from 0 to 1.
    height : numpy.ndarray
        Float height field of shape ``(size, size)``, where 1 is highest.
    """
    u, v = uv_grid(size)
    count = 4
    fx, fy = u * count % 1.0, v * count % 1.0
    edge = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy)) / count
    mask = smoothstep(0.004, 0.03, edge)
    checker = (np.floor(u * count) + np.floor(v * count)) % 2
    glaze = mix([0.10, 0.48, 0.50], [0.82, 0.86, 0.80], checker)
    return mix([0.30, 0.28, 0.26], glaze, smoothstep(0.0, 0.3, mask)), mask


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
    color : numpy.ndarray
        Float RGB image of shape ``(size, size, 3)``, with values from 0 to 1.
    height : numpy.ndarray
        Float height field of shape ``(size, size)``, where 1 is highest.
    """
    u, v = uv_grid(size)
    planks = 5
    plank = np.floor(u * planks)
    x = u * planks - plank
    offset = rng.random(planks)[plank.astype(int)]
    wobble = fractal_noise(size, rng, cells=3, octaves=4)
    grain = 0.5 + 0.5 * np.sin(38.0 * (x + 0.5 * wobble + offset) + 3.0 * v)
    gap = smoothstep(0.0, 0.03, np.minimum(x, 1 - x))
    color = mix([0.36, 0.20, 0.09], [0.68, 0.45, 0.24], grain * (0.6 + 0.4 * offset))
    return mix([0.08, 0.05, 0.03], color, gap), gap * (0.85 + 0.15 * grain)


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
    color : numpy.ndarray
        Float RGB image of shape ``(size, size, 3)``, with values from 0 to 1.
    height : numpy.ndarray
        Float height field of shape ``(size, size)``, where 1 is highest.
    """
    u, v = uv_grid(size)
    count = 5
    fx, fy = u * count % 1.0 - 0.5, v * count % 1.0 - 0.5
    radius = np.hypot(fx, fy) / 0.16
    dome = np.sqrt(np.clip(1.0 - radius * radius, 0.0, 1.0))
    brushed = np.tile(rng.random((size, 1)), (1, size))
    brushed = 0.5 * brushed + 0.5 * fractal_noise(size, rng, cells=6)
    color = mix([0.42, 0.44, 0.48], [0.62, 0.64, 0.68], brushed)
    return mix(color, [0.74, 0.74, 0.76], dome), 0.8 * dome + 0.04 * brushed


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
    color : numpy.ndarray
        Float RGB image of shape ``(size, size, 3)``, with values from 0 to 1.
    height : numpy.ndarray
        Float height field of shape ``(size, size)``, where 1 is highest.
    """
    u, v = uv_grid(size)
    count = 10
    fx, fy = u * count % 1.0, v * count % 1.0
    over = (np.floor(u * count) + np.floor(v * count)) % 2 == 0
    across = np.sin(np.pi * fy) * (0.55 + 0.45 * np.sin(np.pi * fx))
    along = np.sin(np.pi * fx) * (0.55 + 0.45 * np.sin(np.pi * fy))
    height = np.where(over, across, along)
    color = mix([0.30, 0.22, 0.10], [0.86, 0.72, 0.42], height)
    return color, height


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


def generate_texture_layers():
    """Generate the colour and normal maps for every material.

    Returns
    -------
    albedo : bytes
        RGBA8 colour pixels, one layer per material.
    normals : bytes
        RGBA8 normal map pixels, one layer per material.
    layers : int
        Number of layers.
    """
    rng = np.random.default_rng(config.TEXTURE_SEED)
    generated = [material(config.TEXTURE_SIZE, rng) for material in MATERIALS]
    albedo = to_rgba_bytes([color for color, _ in generated])
    normals = to_rgba_bytes([height_to_normals(height) for _, height in generated])
    return albedo, normals, len(generated)
