"""Tests for the procedural textures in ``textures``."""
import numpy as np
import pytest

import config
import textures

SIZE = 32


@pytest.fixture
def rng():
    """A seeded random generator."""
    return np.random.default_rng(1)


def test_smoothstep_endpoints_and_clamping():
    """Values at or beyond the thresholds clamp; the midpoint is 0.5."""
    x = np.array([-1.0, 0.0, 0.5, 1.0, 2.0])
    assert np.allclose(textures.smoothstep(0.0, 1.0, x), [0, 0, 0.5, 1, 1])


def test_mix_colour_with_colour_gives_image():
    """Two colours and a mask give an RGB image."""
    t = np.array([[0.0, 1.0], [0.5, 0.25]])
    out = textures.mix([0.0, 0.0, 0.0], [1.0, 1.0, 1.0], t)
    assert out.shape == (2, 2, 3)
    assert np.allclose(out[..., 0], t)


def test_mix_colour_with_image_and_image_with_colour():
    """A colour mixes with an image in either argument order."""
    image = np.full((2, 2, 3), 0.5)
    t = np.array([[0.0, 1.0], [0.0, 1.0]])
    left = textures.mix([1.0, 1.0, 1.0], image, t)
    right = textures.mix(image, [1.0, 1.0, 1.0], t)
    assert left.shape == right.shape == (2, 2, 3)
    assert np.allclose(left[:, 0], 1.0) and np.allclose(left[:, 1], 0.5)
    assert np.allclose(right[:, 0], 0.5) and np.allclose(right[:, 1], 1.0)


def test_mix_field_with_field_stays_2d():
    """Two 2-D fields blend to a 2-D field."""
    a, b = np.zeros((2, 2)), np.ones((2, 2))
    t = np.array([[0.0, 1.0], [0.5, 0.25]])
    out = textures.mix(a, b, t)
    assert out.shape == (2, 2)
    assert np.allclose(out, t)


def test_uv_grid_range_and_orientation():
    """u varies along columns, v along rows, both in [0, 1)."""
    u, v = textures.uv_grid(SIZE)
    assert u.shape == v.shape == (SIZE, SIZE)
    assert u.min() == 0.0 and v.min() == 0.0
    assert u.max() < 1.0 and v.max() < 1.0
    assert np.all(u[0] == u[1]) and np.all(v[:, 0] == v[:, 1])
    assert u[0, 1] > u[0, 0] and v[1, 0] > v[0, 0]


def test_value_noise_in_unit_range(rng):
    """Value noise has the requested shape and range."""
    noise = textures.value_noise(SIZE, 4, rng)
    assert noise.shape == (SIZE, SIZE)
    assert noise.min() >= 0.0 and noise.max() <= 1.0


def test_fractal_noise_is_normalised(rng):
    """Fractal noise spans exactly [0, 1]."""
    noise = textures.fractal_noise(SIZE, rng)
    assert noise.shape == (SIZE, SIZE)
    assert noise.min() == pytest.approx(0.0)
    assert noise.max() == pytest.approx(1.0)


@pytest.mark.parametrize("material", textures.MATERIALS,
                         ids=[m.__name__ for m in textures.MATERIALS])
def test_material_shapes_and_ranges(material, rng):
    """Every material yields colour (n, n, 3) in [0, 1] and height (n, n)."""
    color, height = material(SIZE, rng)
    assert color.shape == (SIZE, SIZE, 3)
    assert height.shape == (SIZE, SIZE)
    assert color.min() >= 0.0 and color.max() <= 1.0


def test_materials_match_cube_face_count():
    """There is one material per cube face layer."""
    assert len(textures.MATERIALS) == 6


def test_height_to_normals_flat_field():
    """A flat field encodes the straight-up normal (0.5, 0.5, 1.0)."""
    normals = textures.height_to_normals(np.zeros((8, 8)))
    assert normals.shape == (8, 8, 3)
    assert np.allclose(normals, [0.5, 0.5, 1.0])


def test_height_to_normals_slope_tilts_normal():
    """A ramp along u tilts the x component below 0.5 and keeps unit length."""
    ramp = np.tile(np.linspace(0.0, 1.0, 8), (8, 1))
    normals = textures.height_to_normals(ramp)
    assert np.all(normals[..., 0] < 0.5)
    assert np.allclose(normals[..., 1], 0.5)
    decoded = normals * 2.0 - 1.0
    assert np.allclose(np.linalg.norm(decoded, axis=2), 1.0)


def test_to_rgba_bytes_length_dtype_and_clipping():
    """Output is packed RGBA8, clipped, with opaque alpha."""
    images = [np.full((2, 2, 3), -1.0), np.full((2, 2, 3), 2.0)]
    packed = textures.to_rgba_bytes(images)
    assert isinstance(packed, bytes)
    assert len(packed) == 2 * 2 * 2 * 4
    array = np.frombuffer(packed, dtype=np.uint8).reshape(2, 2, 2, 4)
    assert np.all(array[0, ..., :3] == 0) and np.all(array[1, ..., :3] == 255)
    assert np.all(array[..., 3] == 255)


def test_generate_texture_layers_sizes(monkeypatch):
    """Both buffers hold one RGBA8 layer per material."""
    monkeypatch.setattr(config, "TEXTURE_SIZE", SIZE)
    albedo, normals, layers = textures.generate_texture_layers()
    expected = SIZE * SIZE * 4 * len(textures.MATERIALS)
    assert len(albedo) == len(normals) == expected
    assert layers == len(textures.MATERIALS)
