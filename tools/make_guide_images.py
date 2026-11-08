#!/usr/bin/env python3
"""Render every image the "How it works" manual chapter needs.

Four groups of PNG files are written:

* the texture primitives (one octave of noise, fractal noise, a smoothstep
  ramp and a mix), at 160 pixels;
* the shared patterns (lattice, edge distance, seam, checker, Voronoi gap and
  dome), at 160 pixels;
* every step each material records while it builds, plus its normal map, at
  160 pixels, taken from :func:`textures.iter_materials` so they show the
  real layers;
* the cube alone, drawn once per entry of ``shaders.CUBE_VIEWS`` under a light
  that puts the specular highlight on the front face, at 240 pixels.

Everything is generated at a larger size and smooth-scaled down. Regenerate
the images only when a material or the cube shader changes.

Examples
--------
Regenerate the images in ``docs/images/guide``::

    python3 tools/make_guide_images.py docs/images/guide
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from OpenGL import GL
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QVector3D

from offscreen import OffscreenScene
from make_icon import array_to_image

# src/ is on the import path once offscreen is imported.
import config
import shaders
import textures

#: Side length at which the fields are generated, in pixels.
FIELD_SIZE = 512

#: Side length of the field images as written, in pixels.
FIELD_OUTPUT = 160

#: Side length of the cube render, in pixels, before scaling down.
VIEW_RENDER = 480

#: Side length of the cube images as written, in pixels.
VIEW_OUTPUT = 240

#: Seed for the primitive and pattern images, so they are stable.
SEED = 1

#: Lattice of the brick pattern images, as ``(columns, rows)``.
BRICK_LATTICE = (4, 8)

#: Number of seed points in the Voronoi image.
VORONOI_POINTS = 40


def to_image(array, size):
    """Turn a field or an RGB image into a smooth-scaled ``QImage``.

    The array is copied first, so a step recorded by a material is never
    changed. A 2-D field is drawn as greyscale by this rule: if its maximum is
    below 0.5 (distances, which are small), or if any value lies outside
    [0, 1], it is stretched from its minimum (black) to its maximum (white);
    otherwise, when its maximum is 0.5 or more and every value lies in [0, 1],
    it is drawn unstretched, 0 black and 1 white, which keeps masks
    meaningful. An ``(h, w, 3)`` array is read as RGB and clipped to [0, 1].

    Parameters
    ----------
    array : numpy.ndarray
        A 2-D field or an ``(h, w, 3)`` RGB image.
    size : int
        Side length of the result, in pixels.

    Returns
    -------
    PyQt6.QtGui.QImage
        The image, scaled to `size` by `size` with smoothing.
    """
    data = np.array(array, dtype=float)
    if data.ndim == 2:
        low, high = data.min(), data.max()
        if high < 0.5 or low < 0.0 or high > 1.0:
            data = (data - low) / (high - low) if high > low else np.zeros_like(data)
        data = np.repeat(data[..., None], 3, axis=2)
    data = np.clip(data, 0.0, 1.0)
    bgra = np.full(data.shape[:2] + (4,), 255, np.uint8)
    bgra[..., :3] = np.round(data[..., ::-1] * 255.0).astype(np.uint8)
    return array_to_image(bgra).scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def specular_light(ctx):
    """Find the light that centres the specular highlight on the front face.

    The front face is the model's +Z face. Its normal in world space is
    ``n = rotation * (0, 0, 1)`` and its centre is at the same point, since
    the cube has half-width 1. With ``v`` the unit vector from that centre to
    the camera, the mirror direction is ``2 (n . v) n - v``: a light there
    reflects straight into the camera, so the highlight sits on the face's
    middle.

    Parameters
    ----------
    ctx : context.SceneContext
        Scene state; its rotation and camera give the geometry.

    Returns
    -------
    PyQt6.QtGui.QVector3D
        Unit vector towards the light, in world space.
    """
    normal = ctx.rotation.rotatedVector(QVector3D(0, 0, 1))
    to_camera = (ctx.camera_position() - normal).normalized()
    mirror = 2.0 * QVector3D.dotProduct(normal, to_camera) * normal - to_camera
    return mirror.normalized()


def primitive_images():
    """Build the primitive images.

    Returns
    -------
    dict of str to numpy.ndarray
        Field or RGB array by file name, at ``FIELD_SIZE``.
    """
    rng = np.random.default_rng(SEED)
    u, _ = textures.uv_grid(FIELD_SIZE)
    ramp = textures.smoothstep(0.3, 0.7, u)
    return {
        "noise-octave.png": textures.value_noise(FIELD_SIZE, 4, rng),
        "noise-fractal.png": textures.fractal_noise(FIELD_SIZE, rng),
        "smoothstep.png": ramp,
        "mix.png": textures.mix([0.62, 0.22, 0.16], [0.80, 0.36, 0.24], ramp),
    }


def pattern_images():
    """Build the shared-pattern images.

    Returns
    -------
    dict of str to numpy.ndarray
        Field or RGB array by file name, at ``FIELD_SIZE``.
    """
    rng = np.random.default_rng(SEED)
    u, v = textures.uv_grid(FIELD_SIZE)
    columns, rows = BRICK_LATTICE
    _, _, fx, fy = textures.cell_lattice(u, v, columns, rows, stagger=0.5)
    scaled = u * 5
    _, gap = textures.voronoi(u, v, rng.random((VORONOI_POINTS, 2)))
    column, row, tx, ty = textures.cell_lattice(u, v, 5, 5)
    return {
        "pattern-cell-lattice.png": fx,
        "pattern-edge-distance.png": textures.edge_distance(fx, fy, columns, rows),
        "pattern-seam.png": textures.seam(scaled - np.floor(scaled)),
        "pattern-checker.png": textures.checker(
            *textures.cell_lattice(u, v, 4, 4)[:2]
        ),
        "pattern-voronoi.png": gap,
        "pattern-dome.png": textures.dome(tx - 0.5, ty - 0.5, 0.16),
    }


def slug(name):
    """Return a step name as a file-name fragment.

    Parameters
    ----------
    name : str
        Step name, such as ``"distance to edge"``.

    Returns
    -------
    str
        Lower case with spaces turned into hyphens.
    """
    return name.lower().replace(" ", "-")


def write(image, path):
    """Save an image and print its path.

    Parameters
    ----------
    image : PyQt6.QtGui.QImage
        Image to save as PNG.
    path : pathlib.Path
        Destination file.

    Returns
    -------
    int
        Size of the written file, in bytes.
    """
    if not image.save(str(path)):
        sys.exit(f"make_guide_images: could not write {path}")
    print(path)
    return path.stat().st_size


def main():
    """Parse the arguments, render every image and report the totals."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="where to write the images")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)

    count = total = 0

    def save(image, name):
        nonlocal count, total
        total += write(image, args.directory / name)
        count += 1

    for fields in (primitive_images(), pattern_images()):
        for name, array in fields.items():
            save(to_image(array, FIELD_OUTPUT), name)

    for function, material in textures.iter_materials(FIELD_SIZE):
        stem = function.__name__
        for step, array in material.steps.items():
            save(to_image(array, FIELD_OUTPUT), f"{stem}-{slug(step)}.png")
        normals = textures.height_to_normals(material.height)
        save(to_image(normals, FIELD_OUTPUT), f"{stem}-normal-map.png")

    scene = OffscreenScene(VIEW_RENDER)
    ctx = scene.widget.ctx
    cube = scene.widget.cube

    def paint_cube():
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClearColor(*config.BACKGROUND_COLOR, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        cube.paint(ctx)

    default_light = ctx.light
    ctx.light = specular_light(ctx)
    for index, name in enumerate(shaders.CUBE_VIEWS):
        ctx.cube_view = index
        image = scene.render(paint_cube).scaled(
            VIEW_OUTPUT,
            VIEW_OUTPUT,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        save(image, f"view-{name}.png")
    ctx.cube_view = config.DEFAULT_CUBE_VIEW
    ctx.light = default_light
    scene.close()

    print(f"{count} images, {total / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
