#!/usr/bin/env python3
"""Render each face of the cube head-on, for the README's material table.

Each face is turned towards the camera, drawn by the program's own
``CubeRenderer`` into an offscreen framebuffer under the default light, cropped
to the face and scaled down. The sphere grid, axes and light dot are not drawn,
so nothing covers the material. Images are named after the material functions
in ``textures.MATERIALS``.

Examples
--------
Regenerate the images in ``docs/images``::

    python3 tools/make_face_images.py docs/images
"""
import argparse
import math
import sys
from pathlib import Path

from OpenGL import GL
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QQuaternion, QVector3D

from offscreen import OffscreenScene

# src/ is on the import path once offscreen is imported.
import config
import textures

#: Side length of the offscreen render, in pixels, before scaling down.
RENDER_SIZE = 512

#: Fraction of the render's width that the face fills.
FILL = 0.95

#: Rotation turning each face towards the camera, in ``MATERIALS`` order
#: (+X, -X, +Y, -Y, +Z, -Z). The side faces keep +Y up, as in the window.
FACE_ROTATIONS = (
    QQuaternion.fromAxisAndAngle(0.0, 1.0, 0.0, -90.0),
    QQuaternion.fromAxisAndAngle(0.0, 1.0, 0.0, 90.0),
    QQuaternion.fromAxisAndAngle(1.0, 0.0, 0.0, 90.0),
    QQuaternion.fromAxisAndAngle(1.0, 0.0, 0.0, -90.0),
    QQuaternion(),
    QQuaternion.fromAxisAndAngle(0.0, 1.0, 0.0, 180.0),
)

#: Outward normal of each face, in ``MATERIALS`` order.
FACE_NORMALS = (
    QVector3D(1, 0, 0), QVector3D(-1, 0, 0), QVector3D(0, 1, 0),
    QVector3D(0, -1, 0), QVector3D(0, 0, 1), QVector3D(0, 0, -1),
)


def face_half_width(distance):
    """Return half the projected width of the facing side, in pixels.

    Parameters
    ----------
    distance : float
        Camera distance from the cube's centre. The facing side is one unit
        nearer.

    Returns
    -------
    float
        Half the side's width in the render.
    """
    tangent = math.tan(math.radians(config.FOV_DEGREES / 2.0))
    return RENDER_SIZE / 2.0 / ((distance - 1.0) * tangent)


def render_faces(size):
    """Render every face and return the scaled images.

    Parameters
    ----------
    size : int
        Side length of each output image, in pixels.

    Returns
    -------
    list of PyQt6.QtGui.QImage
        One image per face, in ``MATERIALS`` order.
    """
    scene = OffscreenScene(RENDER_SIZE)
    ctx = scene.widget.ctx
    cube = scene.widget.cube
    tangent = math.tan(math.radians(config.FOV_DEGREES / 2.0))
    ctx.distance = 1.0 + 1.0 / (FILL * tangent)
    half = int(face_half_width(ctx.distance)) - 2  # stay inside the edge pixels
    centre = RENDER_SIZE // 2

    def paint_cube():
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClearColor(*config.BACKGROUND_COLOR, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        cube.paint(ctx)

    images = []
    for rotation, normal in zip(FACE_ROTATIONS, FACE_NORMALS):
        facing = rotation.rotatedVector(normal)
        assert (facing - QVector3D(0, 0, 1)).length() < 1e-5, facing
        ctx.rotation = rotation
        frame = scene.render(paint_cube)
        face = frame.copy(centre - half, centre - half, 2 * half, 2 * half)
        images.append(
            face.scaled(
                size,
                size,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    scene.close()
    return images


def main():
    """Parse the arguments, render the faces and save them as PNG files."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="where to write the images")
    parser.add_argument(
        "--size", type=int, default=128, help="output side length in pixels"
    )
    args = parser.parse_args()

    args.directory.mkdir(parents=True, exist_ok=True)
    for material, image in zip(textures.MATERIALS, render_faces(args.size)):
        path = args.directory / f"face-{material.__name__}.png"
        if not image.save(str(path)):
            sys.exit(f"make_face_images: could not write {path}")
        print(path)


if __name__ == "__main__":
    main()
