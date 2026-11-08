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


def test_seam_values_and_symmetry():
    """``seam`` is 0 at the edges, 0.5 at the centre and mirrors about 0.5.

    **WHY:** Every edge mask measures its distance with ``seam``. A wrong
    peak or a lopsided shape would give mortar lines or borders of unequal
    thickness on the two sides of a cell.
    """
    f = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    assert np.allclose(textures.seam(f), [0.0, 0.25, 0.5, 0.25, 0.0])
    g = np.linspace(0.0, 1.0, 11)
    assert np.allclose(textures.seam(g), textures.seam(1 - g))


def test_cell_lattice_plain_grid():
    """Without stagger, indices count cells and fractions lie in [0, 1).

    **WHY:** Tiles, weave and rivets rely on the plain lattice matching
    ``u * n % 1.0`` exactly; the fractions must also stay below 1 so a pixel
    never falls into the next cell.
    """
    u, v = textures.uv_grid(16)
    column, row, fx, fy = textures.cell_lattice(u, v, 4, 2)
    assert column.min() == 0 and column.max() == 3
    assert row.min() == 0 and row.max() == 1
    assert fx.min() >= 0.0 and fx.max() < 1.0
    assert fy.min() >= 0.0 and fy.max() < 1.0
    assert np.array_equal(fx, u * 4 % 1.0)
    assert np.array_equal(fy, v * 2 % 1.0)


def test_cell_lattice_stagger_shifts_odd_rows():
    """Stagger shifts only odd rows, by the given fraction of a cell.

    **WHY:** Bricks need every other course offset by half a brick. Even
    rows must be untouched, and the fractions must still lie in [0, 1) after
    the shift.
    """
    u, v = textures.uv_grid(16)
    plain = textures.cell_lattice(u, v, 4, 4)
    column, row, fx, fy = textures.cell_lattice(u, v, 4, 4, stagger=0.5)
    even = row % 2 == 0
    assert np.array_equal(fx[even], plain[2][even])
    assert np.array_equal(column[even], plain[0][even])
    x = u * 4 + 0.5
    assert np.array_equal(column[~even] + fx[~even], x[~even])
    assert column.max() == 4
    assert fx.min() >= 0.0 and fx.max() < 1.0
    assert np.array_equal(fy, plain[3])


def test_edge_distance_zero_on_edges_and_scaled():
    """Edge distance is 0 on an edge and peaks at the cell centre, scaled.

    **WHY:** The mortar width is set in texture units; the division by the
    column and row counts is what keeps it the same on all four sides of a
    non-square brick.
    """
    fx = np.array([0.0, 0.5, 0.5, 0.5])
    fy = np.array([0.5, 0.5, 0.0, 0.25])
    out = textures.edge_distance(fx, fy, 4, 8)
    assert np.allclose(out, [0.0, 0.5 / 8, 0.0, 0.25 / 8])


def test_checker_alternates_and_is_float():
    """Neighbouring cells get opposite values, as floats.

    **WHY:** The tile pattern mixes two colours by this value. A boolean
    result would make ``mix`` cast it, so the float type is part of the
    contract.
    """
    column = np.array([0.0, 1.0, 0.0, 1.0])
    row = np.array([0.0, 0.0, 1.0, 1.0])
    out = textures.checker(column, row)
    assert out.dtype == np.float64
    assert np.array_equal(out, [0.0, 1.0, 1.0, 0.0])


def test_voronoi_nearest_gap_dtype_and_bisector():
    """Nearest index is right, the gap is float32 and ~0 on the bisector.

    **WHY:** Cobbles take their shade from the nearest point and their
    mortar from the gap. The gap must be non-negative, and small where two
    points are equally near, or the stones would have no borders.
    """
    points = np.array([[0.25, 0.5], [0.75, 0.5]])
    u = np.array([[0.1, 0.5, 0.9]])
    v = np.full_like(u, 0.5)
    nearest, gap = textures.voronoi(u, v, points)
    assert nearest.tolist() == [[0, 0, 1]]
    assert gap.dtype == np.float32
    assert (gap >= 0.0).all()
    assert gap[0, 1] == pytest.approx(0.0, abs=1e-6)
    assert gap[0, 0] == pytest.approx(0.5, abs=1e-6)


def test_dome_centre_and_outside_radius():
    """The dome is 1 at the centre, 0 at and beyond its radius.

    **WHY:** Rivets are hemispheres on a flat plate. Without the clip, the
    square root of a negative number would give NaN outside the radius.
    """
    fx = np.array([0.0, 0.16, 0.4])
    fy = np.zeros(3)
    out = textures.dome(fx, fy, 0.16)
    assert np.allclose(out, [1.0, 0.0, 0.0])
    assert not np.isnan(out).any()


@pytest.mark.parametrize("material", textures.MATERIALS,
                         ids=[m.__name__ for m in textures.MATERIALS])
def test_material_shapes_and_ranges(material, rng):
    """Every material yields colour (n, n, 3) in [0, 1] and height (n, n).

    **WHY:** Every material feeds the same texture array, so each must return
    the same shapes and a colour range the byte packer can encode. Size 32
    keeps the run fast.
    """
    color, height, _ = material(SIZE, rng)
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


@pytest.mark.parametrize("material", textures.MATERIALS,
                         ids=[m.__name__ for m in textures.MATERIALS])
def test_material_steps_are_recorded(material, rng):
    """Every material records finite 2D or RGB steps ending in its layers.

    **WHY:** The documentation draws each step as an image, so every step
    must be a (n, n) field or (n, n, 3) image with no NaN or infinity. The
    "colour" and "height" steps must be the very arrays returned, or the
    pictures would not show the layers that reach the GPU.
    """
    result = material(SIZE, rng)
    assert isinstance(result, textures.Material)
    assert result.steps
    assert result.steps["colour"] is result.color
    assert result.steps["height"] is result.height
    for name, step in result.steps.items():
        assert step.shape in ((SIZE, SIZE), (SIZE, SIZE, 3)), name
        assert np.isfinite(step).all(), name


def test_iter_materials_follows_materials_order():
    """`iter_materials` yields each material function, in layer order.

    **WHY:** The layer index is the cube face index. Out of order, every face
    would show another face's material.
    """
    pairs = list(textures.iter_materials(SIZE, seed=1))
    assert [function for function, _ in pairs] == list(textures.MATERIALS)
    assert all(isinstance(material, textures.Material) for _, material in pairs)


def test_iter_materials_is_repeatable_and_defaults_to_config_seed(monkeypatch):
    """The same seed gives the same colours; no seed uses `config.TEXTURE_SEED`.

    **WHY:** The documentation images must show the layers the program really
    builds, which needs the same seed to give the same pixels, and the default
    to follow the configured seed when it is read, not when the module loads.
    """
    first = [m.color for _, m in textures.iter_materials(SIZE, seed=5)]
    second = [m.color for _, m in textures.iter_materials(SIZE, seed=5)]
    assert all(np.array_equal(a, b) for a, b in zip(first, second))
    monkeypatch.setattr(config, "TEXTURE_SEED", 5)
    default = [m.color for _, m in textures.iter_materials(SIZE)]
    assert all(np.array_equal(a, b) for a, b in zip(first, default))


def test_generate_texture_layers_packs_iter_materials(monkeypatch):
    """The packed layers equal `iter_materials` colours and normals.

    **WHY:** `generate_texture_layers` is a thin consumer of `iter_materials`.
    If the two drifted apart, the documentation would describe textures the
    program does not use.
    """
    monkeypatch.setattr(config, "TEXTURE_SIZE", SIZE)
    materials = [m for _, m in textures.iter_materials(SIZE)]
    albedo, normals, layers = textures.generate_texture_layers()
    assert albedo == textures.to_rgba_bytes([m.color for m in materials])
    assert normals == textures.to_rgba_bytes(
        [textures.height_to_normals(m.height) for m in materials]
    )
    assert layers == len(materials)
