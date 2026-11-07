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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from OpenGL import GL  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtGui import (  # noqa: E402
    QGuiApplication,
    QOffscreenSurface,
    QOpenGLContext,
    QQuaternion,
    QSurfaceFormat,
    QVector3D,
)
from PyQt6.QtOpenGL import (  # noqa: E402
    QOpenGLFramebufferObject,
    QOpenGLFramebufferObjectFormat,
)

import config  # noqa: E402
import textures  # noqa: E402
from context import SceneContext  # noqa: E402
from cube import CubeRenderer  # noqa: E402

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


def request_format():
    """Set the default surface format the program itself requests.

    These lines repeat ``main.main``, which sets the format inline.
    """
    surface = QSurfaceFormat()
    if sys.platform == "darwin":
        surface.setVersion(4, 1)
        surface.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    else:
        surface.setRenderableType(QSurfaceFormat.RenderableType.OpenGLES)
        surface.setVersion(3, 1)
    QSurfaceFormat.setDefaultFormat(surface)


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
    surface = QOffscreenSurface()
    surface.create()
    context = QOpenGLContext()
    if not context.create() or not context.makeCurrent(surface):
        sys.exit("make_face_images: no OpenGL context")

    fmt = QOpenGLFramebufferObjectFormat()
    fmt.setAttachment(QOpenGLFramebufferObject.Attachment.Depth)
    target = QOpenGLFramebufferObject(RENDER_SIZE, RENDER_SIZE, fmt)
    target.bind()
    GL.glViewport(0, 0, RENDER_SIZE, RENDER_SIZE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    renderer = CubeRenderer()
    renderer.initialize()
    ctx = SceneContext()
    tangent = math.tan(math.radians(config.FOV_DEGREES / 2.0))
    ctx.distance = 1.0 + 1.0 / (FILL * tangent)
    half = int(face_half_width(ctx.distance)) - 2  # stay inside the edge pixels
    centre = RENDER_SIZE // 2

    images = []
    for rotation, normal in zip(FACE_ROTATIONS, FACE_NORMALS):
        facing = rotation.rotatedVector(normal)
        assert (facing - QVector3D(0, 0, 1)).length() < 1e-5, facing
        ctx.rotation = rotation
        GL.glClearColor(*config.BACKGROUND_COLOR, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        renderer.paint(ctx)
        frame = target.toImage()
        face = frame.copy(centre - half, centre - half, 2 * half, 2 * half)
        images.append(
            face.scaled(
                size,
                size,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    target.release()
    context.doneCurrent()
    return images


def main():
    """Parse the arguments, render the faces and save them as PNG files."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="where to write the images")
    parser.add_argument(
        "--size", type=int, default=128, help="output side length in pixels"
    )
    args = parser.parse_args()

    request_format()
    app = QGuiApplication(sys.argv[:1])  # noqa: F841 - needed for the surface
    args.directory.mkdir(parents=True, exist_ok=True)
    for material, image in zip(textures.MATERIALS, render_faces(args.size)):
        path = args.directory / f"face-{material.__name__}.png"
        if not image.save(str(path)):
            sys.exit(f"make_face_images: could not write {path}")
        print(path)


if __name__ == "__main__":
    main()
