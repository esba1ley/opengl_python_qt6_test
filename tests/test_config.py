"""Tests for the tunable settings in ``config``."""
from PyQt6.QtGui import QVector3D

import config


def test_colors_are_rgb_triples_in_unit_range():
    """Colour settings are three components in [0, 1].

    OpenGL takes colour components in [0, 1]. A colour typed in 0 to 255 would
    saturate to white without any error.
    """
    for color in (config.BACKGROUND_COLOR, config.LIGHT_DOT_COLOR):
        assert len(color) == 3
        assert all(0.0 <= c <= 1.0 for c in color)


def test_default_light_is_unit_length():
    """The default light direction is normalised.

    The cube shader's lighting uses dot products that assume a unit light
    vector. A longer or shorter default would brighten or darken the default
    view.
    """
    assert isinstance(config.DEFAULT_LIGHT, QVector3D)
    assert abs(config.DEFAULT_LIGHT.length() - 1.0) < 1e-6


def test_distance_limits_are_ordered():
    """The default distance lies strictly between the zoom limits.

    If the default lay outside the zoom limits, the first wheel notch would
    jump the camera to a limit. The test guards the relation, not the values,
    so the limits stay free to tune.
    """
    assert config.MIN_DISTANCE < config.DEFAULT_DISTANCE < config.MAX_DISTANCE
