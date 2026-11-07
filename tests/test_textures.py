"""Tests for the procedural textures in ``textures``."""
import numpy as np
import pytest

import config
import textures

#: Texture side length in pixels, small to keep the tests fast.
SIZE = 32


@pytest.fixture
def rng():
    """A seeded random generator."""
    return np.random.default_rng(1)


def test_smoothstep_endpoints_and_clamping():
    """Values at or beyond the thresholds clamp; the midpoint is 0.5.

    **WHY:** Every material uses ``smoothstep`` for its edges. Without
    clamping, values past the thresholds would overshoot and give colours
    outside [0, 1].
    """
    x = np.array([-1.0, 0.0, 0.5, 1.0, 2.0])
    assert np.allclose(textures.smoothstep(0.0, 1.0, x), [0, 0, 0.5, 1, 1])


def test_mix_colour_with_colour_gives_image():
    """Two colours and a mask give an RGB image.

    **WHY:** Materials blend two constant colours through a mask, which must
    give a full RGB image.
    """
    t = np.array([[0.0, 1.0], [0.5, 0.25]])
    out = textures.mix([0.0, 0.0, 0.0], [1.0, 1.0, 1.0], t)
    assert out.shape == (2, 2, 3)
    assert np.allclose(out[..., 0], t)


def test_mix_colour_with_image_and_image_with_colour():
    """A colour mixes with an image in either argument order.

    **WHY:** Materials also blend a colour into an existing image, in either
    argument order.
    """
    image = np.full((2, 2, 3), 0.5)
    t = np.array([[0.0, 1.0], [0.0, 1.0]])
    left = textures.mix([1.0, 1.0, 1.0], image, t)
    right = textures.mix(image, [1.0, 1.0, 1.0], t)
    assert left.shape == right.shape == (2, 2, 3)
    assert np.allclose(left[:, 0], 1.0) and np.allclose(left[:, 1], 0.5)
    assert np.allclose(right[:, 0], 0.5) and np.allclose(right[:, 1], 1.0)


def test_mix_field_with_field_stays_2d():
    """Two 2-D fields blend to a 2-D field.

    **WHY:** No material calls ``mix`` this way, so this test is the only one
    to reach that branch. It stops a later caller from silently getting a 3-D
    result back.
    """
    a, b = np.zeros((2, 2)), np.ones((2, 2))
    t = np.array([[0.0, 1.0], [0.5, 0.25]])
    out = textures.mix(a, b, t)
    assert out.shape == (2, 2)
    assert np.allclose(out, t)


def test_uv_grid_range_and_orientation():
    """u varies along columns, v along rows, both in [0, 1).

    **WHY:** If u and v were swapped, every texture would turn 90 degrees; if
    they reached 1.0, periodic patterns would repeat their first row at the
    edge.
    """
    u, v = textures.uv_grid(SIZE)
    assert u.shape == v.shape == (SIZE, SIZE)
    assert u.min() == 0.0 and v.min() == 0.0
    assert u.max() < 1.0 and v.max() < 1.0
    assert np.all(u[0] == u[1]) and np.all(v[:, 0] == v[:, 1])
    assert u[0, 1] > u[0, 0] and v[1, 0] > v[0, 0]


def test_value_noise_in_unit_range(rng):
    """Value noise has the requested shape and range.

    **WHY:** Materials use the noise directly as a blend weight, which must
    stay in [0, 1].
    """
    noise = textures.value_noise(SIZE, 4, rng)
    assert noise.shape == (SIZE, SIZE)
    assert noise.min() >= 0.0 and noise.max() <= 1.0


def test_fractal_noise_is_normalised(rng):
    """Fractal noise spans exactly [0, 1].

    **WHY:** Materials rely on the full [0, 1] range for contrast, so the
    octave sum must be renormalised.
    """
    noise = textures.fractal_noise(SIZE, rng)
    assert noise.shape == (SIZE, SIZE)
    assert noise.min() == pytest.approx(0.0)
    assert noise.max() == pytest.approx(1.0)


@pytest.mark.parametrize("material", textures.MATERIALS,
                         ids=[m.__name__ for m in textures.MATERIALS])
def test_material_shapes_and_ranges(material, rng):
    """Every material yields colour (n, n, 3) in [0, 1] and height (n, n).

    **WHY:** Every material feeds the same texture array, so each must return
    the same shapes and a colour range the byte packer can encode. Size 32
    keeps the run fast.
    """
    color, height = material(SIZE, rng)
    assert color.shape == (SIZE, SIZE, 3)
    assert height.shape == (SIZE, SIZE)
    assert color.min() >= 0.0 and color.max() <= 1.0


def test_materials_match_cube_face_count():
    """There is one material per cube face layer.

    **WHY:** The cube has six faces and six texture layers. A seventh material
    would have no face, and a fifth would leave one face without a texture.
    """
    assert len(textures.MATERIALS) == 6


def test_height_to_normals_flat_field():
    """A flat field encodes the straight-up normal (0.5, 0.5, 1.0).

    **WHY:** This is the encoding that the cube shader decodes. A flat surface
    must encode straight up, or every face would look tilted.
    """
    normals = textures.height_to_normals(np.zeros((8, 8)))
    assert normals.shape == (8, 8, 3)
    assert np.allclose(normals, [0.5, 0.5, 1.0])


def test_height_to_normals_slope_tilts_normal():
    """A ramp along u tilts the x component below 0.5 and keeps unit length.

    **WHY:** A sign error here turns bumps into dents. The decoded normal must
    also stay unit length for the lighting to be correct.
    """
    ramp = np.tile(np.linspace(0.0, 1.0, 8), (8, 1))
    normals = textures.height_to_normals(ramp)
    assert np.all(normals[..., 0] < 0.5)
    assert np.allclose(normals[..., 1], 0.5)
    decoded = normals * 2.0 - 1.0
    assert np.allclose(np.linalg.norm(decoded, axis=2), 1.0)


def test_to_rgba_bytes_length_dtype_and_clipping():
    """Output is packed RGBA8, clipped, with opaque alpha.

    **WHY:** Values outside [0, 1] must clip, not wrap, or a slightly negative
    value would turn white. The byte count must match what the texture upload
    expects.
    """
    images = [np.full((2, 2, 3), -1.0), np.full((2, 2, 3), 2.0)]
    packed = textures.to_rgba_bytes(images)
    assert isinstance(packed, bytes)
    assert len(packed) == 2 * 2 * 2 * 4
    array = np.frombuffer(packed, dtype=np.uint8).reshape(2, 2, 2, 4)
    assert np.all(array[0, ..., :3] == 0) and np.all(array[1, ..., :3] == 255)
    assert np.all(array[..., 3] == 255)


def test_generate_texture_layers_sizes(monkeypatch):
    """Both buffers hold one RGBA8 layer per material.

    **WHY:** A buffer of the wrong size makes the texture upload read past its
    end. The texture size is reduced to 32 to keep the run fast.
    """
    monkeypatch.setattr(config, "TEXTURE_SIZE", SIZE)
    albedo, normals, layers = textures.generate_texture_layers()
    expected = SIZE * SIZE * 4 * len(textures.MATERIALS)
    assert len(albedo) == len(normals) == expected
    assert layers == len(textures.MATERIALS)
