#!/usr/bin/env python3
"""Turn a screenshot of the program into a square, disc-masked icon.

The sphere grid is found as the bounding box of pixels brighter than a
threshold, ignoring the window frame and any title bar above the black client
area. A square slightly larger than that box
is cropped, masked to a soft-edged disc so the corners are transparent, and
scaled to the requested size.

Examples
--------
Regenerate ``icon.png`` from a screenshot of the window::

    python3 tools/make_icon.py tools/ScreenGrab.png icon.png
"""
import argparse
import sys

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage


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


def client_top(pixels, run=8, black=8):
    """Find the first row of the black client area below any title bar.

    A title bar is gray, not black, so the client area starts at the first
    row that begins a run of near-black rows down the centre column.

    Parameters
    ----------
    pixels : numpy.ndarray
        BGRA pixels of the screenshot.
    run : int
        Number of consecutive near-black rows required.
    black : int
        Maximum channel value for a pixel to count as near-black.

    Returns
    -------
    int
        Index of the first row of the client area, or 0 if none is found.
    """
    column = pixels[:, pixels.shape[1] // 2, :3].max(axis=1)
    dark = column <= black
    for row in range(len(dark) - run):
        if dark[row : row + run].all():
            return row
    return 0


def find_sphere(pixels, frame, threshold):
    """Locate the sphere grid as the bounding box of bright pixels.

    Parameters
    ----------
    pixels : numpy.ndarray
        BGRA pixels of the screenshot.
    frame : int
        Border width to ignore, in pixels, so window chrome is skipped.
    threshold : int
        Minimum channel value for a pixel to count as content.

    Returns
    -------
    tuple of int
        Centre x, centre y and radius, in pixels.
    """
    top = client_top(pixels) + frame
    bright = pixels[top:-frame, frame:-frame, :3].max(axis=2)
    ys, xs = np.nonzero(bright > threshold)
    if xs.size == 0:
        raise ValueError("no content found above the threshold")
    cx = (xs.min() + xs.max()) // 2 + frame
    cy = (ys.min() + ys.max()) // 2 + top
    radius = max(xs.max() - xs.min(), ys.max() - ys.min()) // 2
    return cx, cy, radius


def make_icon(screenshot, size, padding, frame, threshold):
    """Crop, mask and scale a screenshot into an icon.

    Parameters
    ----------
    screenshot : PyQt6.QtGui.QImage
        Screenshot of the running program.
    size : int
        Width and height of the icon, in pixels.
    padding : float
        Extra space around the sphere, as a fraction of its radius.
    frame : int
        Border width of the screenshot to ignore, in pixels.
    threshold : int
        Brightness threshold for detecting the sphere.

    Returns
    -------
    PyQt6.QtGui.QImage
        The icon, with transparent corners outside the disc.
    """
    pixels = image_to_array(screenshot)
    cx, cy, radius = find_sphere(pixels, frame, threshold)
    half = int(radius * (1.0 + padding))
    height, width = pixels.shape[:2]
    x0, y0 = max(cx - half, 0), max(cy - half, 0)
    x1, y1 = min(cx + half, width), min(cy + half, height)
    crop = pixels[y0:y1, x0:x1].copy()

    # Soft-edged disc: fully opaque inside, fading over the last few pixels.
    h, w = crop.shape[:2]
    yy, xx = np.mgrid[:h, :w]
    distance = np.hypot(xx - (w - 1) / 2.0, yy - (h - 1) / 2.0)
    edge = min(h, w) / 2.0
    alpha = np.clip((edge - distance) / 3.0, 0.0, 1.0)
    crop[..., 3] = (alpha * 255).astype(np.uint8)
    crop[..., :3] = (crop[..., :3] * alpha[..., None]).astype(np.uint8)

    image = array_to_image(crop)
    return image.scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def main(argv):
    """Parse arguments, build the icon and write it out.

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
    parser.add_argument("screenshot", help="PNG screenshot of the window")
    parser.add_argument("output", help="PNG icon to write")
    parser.add_argument("--size", type=int, default=512, help="icon size in pixels")
    parser.add_argument("--padding", type=float, default=0.06, help="space around the sphere")
    parser.add_argument("--frame", type=int, default=12, help="screenshot border to ignore")
    parser.add_argument("--threshold", type=int, default=60, help="brightness threshold")
    args = parser.parse_args(argv)

    screenshot = QImage(args.screenshot)
    if screenshot.isNull():
        print(f"cannot read {args.screenshot}", file=sys.stderr)
        return 1
    icon = make_icon(screenshot, args.size, args.padding, args.frame, args.threshold)
    if not icon.save(args.output):
        print(f"cannot write {args.output}", file=sys.stderr)
        return 1
    print(f"wrote {args.output} ({icon.width()}x{icon.height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
