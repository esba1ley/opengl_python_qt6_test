"""Tests for the tunable settings in ``config``."""
from PyQt6.QtGui import QVector3D

import config


def test_scalar_settings_are_numbers():
    """Numeric settings are floats or ints as the renderers expect."""
    for name in (
        "ROTATE_DEGREES_PER_PIXEL", "ZOOM_FACTOR_PER_NOTCH", "MIN_DISTANCE",
        "MAX_DISTANCE", "DEFAULT_DISTANCE", "FOV_DEGREES", "NEAR_PLANE",
        "FAR_PLANE", "BUMP_STRENGTH", "SPHERE_RADIUS", "SPHERE_OPACITY",
        "CURVE_STEP_DEGREES", "AXIS_LINE_WIDTH", "HIDDEN_OPACITY",
        "LIGHT_DOT_SIZE",
    ):
        assert isinstance(getattr(config, name), float), name
    for name in ("TEXTURE_SIZE", "TEXTURE_SEED", "LONGITUDE_STEP", "LATITUDE_STEP"):
        assert isinstance(getattr(config, name), int), name


def test_colors_are_rgb_triples_in_unit_range():
    """Colour settings are three components in [0, 1]."""
    for color in (config.BACKGROUND_COLOR, config.LIGHT_DOT_COLOR):
        assert len(color) == 3
        assert all(0.0 <= c <= 1.0 for c in color)


def test_default_light_is_unit_length():
    """The default light direction is normalised."""
    assert isinstance(config.DEFAULT_LIGHT, QVector3D)
    assert abs(config.DEFAULT_LIGHT.length() - 1.0) < 1e-6


def test_distance_limits_are_ordered():
    """The default distance lies strictly between the zoom limits."""
    assert config.MIN_DISTANCE < config.DEFAULT_DISTANCE < config.MAX_DISTANCE
