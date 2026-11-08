#!/usr/bin/env python3
"""Render the default view, and make the icon and README screenshot from it.

The program's default view is drawn offscreen by the window's own
``paintGL``, at twice the screenshot's size, and scaled down for the
screenshot. For the icon, the same frame is cropped to a square around the
sphere grid, whose projected radius follows from the camera settings in
``config``, masked to a soft-edged disc so the corners are transparent, and
scaled to the requested size. Both therefore follow any change to the scene.

Examples
--------
Regenerate ``icon.png`` and the README screenshot::

    python3 tools/make_icon.py icon.png docs/images/screenshot.png
"""
import argparse
import math
import sys

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage

from offscreen import OffscreenScene

# src/ is on the import path once offscreen is imported.
import config

#: Side length of the README screenshot, in pixels: the window's size.
SCREENSHOT_SIZE = 640

#: Side length of the render, twice the screenshot's, to smooth the lines.
RENDER_SIZE = 2 * SCREENSHOT_SIZE


def image_to_array(image):
    """Copy a QImage into an ``(h, w, 4)`` BGRA uint8 array.

    Parameters
    ----------
    image : PyQt6.QtGui.QImage
        Source image, in any format.

    Returns
    -------
    numpy.ndarray
        A writable copy of the pixels, channel order B, G, R, A.
    """
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = image.width(), image.height()
    buffer = image.constBits()
    buffer.setsize(height * image.bytesPerLine())
    rows = np.frombuffer(buffer, np.uint8).reshape(height, image.bytesPerLine())
    return rows[:, : width * 4].reshape(height, width, 4).copy()


def array_to_image(pixels):
    """Build a QImage from an ``(h, w, 4)`` BGRA uint8 array.

    Parameters
    ----------
    pixels : numpy.ndarray
        Pixel data, channel order B, G, R, A.

    Returns
    -------
    PyQt6.QtGui.QImage
        An independent copy of the pixels.
    """
    pixels = np.ascontiguousarray(pixels)
    height, width = pixels.shape[:2]
    image = QImage(pixels.data, width, height, width * 4, QImage.Format.Format_ARGB32)
    return image.copy()


def sphere_radius(size, distance):
    """Return the projected radius of the sphere grid, in pixels.

    The sphere is centred on the origin and the camera looks at it from
    ``distance``, so its outline is a circle centred in the frame.

    Parameters
    ----------
    size : int
        Side length of the square frame, in pixels.
    distance : float
        Camera distance from the origin.

    Returns
    -------
    float
        Radius of the outline, in pixels.
    """
    half_angle = math.asin(config.SPHERE_RADIUS / distance)
    tangent = math.tan(math.radians(config.FOV_DEGREES / 2.0))
    return math.tan(half_angle) / tangent * size / 2.0


def make_icon(frame, distance, size, padding):
    """Crop, mask and scale a rendered frame into an icon.

    Parameters
    ----------
    frame : PyQt6.QtGui.QImage
        Square render of the scene, with the sphere centred.
    distance : float
        Camera distance the frame was rendered at.
    size : int
        Width and height of the icon, in pixels.
    padding : float
        Extra space around the sphere, as a fraction of its radius.

    Returns
    -------
    PyQt6.QtGui.QImage
        The icon, with transparent corners outside the disc.
    """
    pixels = image_to_array(frame)
    centre = frame.width() // 2
    half = int(sphere_radius(frame.width(), distance) * (1.0 + padding))
    crop = pixels[centre - half : centre + half, centre - half : centre + half].copy()

    # Soft-edged disc: fully opaque inside, fading over the last few pixels.
    h, w = crop.shape[:2]
    yy, xx = np.mgrid[:h, :w]
    radius = np.hypot(xx - (w - 1) / 2.0, yy - (h - 1) / 2.0)
    edge = min(h, w) / 2.0
    alpha = np.clip((edge - radius) / 6.0, 0.0, 1.0)
    crop[..., 3] = (alpha * 255).astype(np.uint8)
    crop[..., :3] = (crop[..., :3] * alpha[..., None]).astype(np.uint8)

    return array_to_image(crop).scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def main(argv):
    """Parse arguments, render the default view and write both images.

    Parameters
    ----------
    argv : list of str
        Command-line arguments, without the program name.

    Returns
    -------
    int
        Exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("icon", help="PNG icon to write")
    parser.add_argument("screenshot", help="PNG screenshot to write")
    parser.add_argument("--size", type=int, default=512, help="icon size in pixels")
    parser.add_argument("--padding", type=float, default=0.06, help="space around the sphere")
    args = parser.parse_args(argv)

    scene = OffscreenScene(RENDER_SIZE)
    frame = scene.render()
    distance = scene.widget.ctx.distance
    scene.close()

    screenshot = frame.convertToFormat(QImage.Format.Format_RGB32).scaled(
        SCREENSHOT_SIZE,
        SCREENSHOT_SIZE,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    icon = make_icon(frame, distance, args.size, args.padding)
    for image, path in ((icon, args.icon), (screenshot, args.screenshot)):
        if not image.save(path):
            print(f"cannot write {path}", file=sys.stderr)
            return 1
        print(f"wrote {path} ({image.width()}x{image.height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
