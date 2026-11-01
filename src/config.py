"""Tunable settings shared by the other modules."""
from PyQt6.QtGui import QVector3D

# Interaction
ROTATE_DEGREES_PER_PIXEL = 0.5
ZOOM_FACTOR_PER_NOTCH = 0.9
MIN_DISTANCE, MAX_DISTANCE = 2.0, 20.0

# Camera and light
DEFAULT_DISTANCE = 6.0
FOV_DEGREES = 45.0
NEAR_PLANE, FAR_PLANE = 0.1, 100.0
DEFAULT_PITCH_DEGREES, DEFAULT_YAW_DEGREES = 25.0, -35.0
DEFAULT_LIGHT = QVector3D(0.4, 0.7, 1.0).normalized()

# Cube materials
TEXTURE_SIZE = 512
TEXTURE_SEED = 7
BUMP_STRENGTH = 0.03  # higher makes the surface relief look deeper

# Sphere grid
SPHERE_RADIUS = 1.85  # just outside the cube's corners, which are at sqrt(3)
SPHERE_OPACITY = 0.30
LONGITUDE_STEP = 15
LATITUDE_STEP = 10
CURVE_STEP_DEGREES = 2.0  # length of the straight segments that form each curve

# Axes and light dot
AXIS_LINE_WIDTH = 2.0
HIDDEN_OPACITY = 0.35  # light dot when seen through the cube
LIGHT_DOT_COLOR = (1.00, 0.90, 0.10)
LIGHT_DOT_SIZE = 14.0  # pixels
