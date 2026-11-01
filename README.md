# Qt6 OpenGL Test

A small Python program for testing OpenGL inside a Qt6 window. It draws a
textured, bump-mapped cube inside a latitude/longitude sphere grid, and you can
rotate, zoom and pan the scene and move the light with the mouse.

All the textures are generated in code, so there are no image files.

## What it draws

- **Cube:** a 2x2x2 cube centred on the origin, with a different material on
  each side.

  | Side | Direction | Material |
  |---|---|---|
  | Right | +X | Brick |
  | Left | −X | Cobblestone |
  | Top | +Y | Glazed teal and cream tiles |
  | Bottom | −Y | Woven straw |
  | Front | +Z | Riveted brushed metal |
  | Back | −Z | Wooden planks |

- **Sphere grid:** lines every 15° of longitude and 10° of latitude, drawn at
  30% opacity and fixed to the cube. Near-side lines are light gray and far-side
  lines are dark gray.
- **Axes:** the +X, +Y and +Z axes are red, green and blue lines running from
  the origin to the sphere. The cube hides the parts inside it.
- **Light dot:** a yellow dot on the sphere marks the direction to the light. It
  appears faintly when it is behind the cube.

### Sphere coordinates

| Direction | Latitude | Longitude |
|---|---|---|
| +X | 0° | 0° |
| +Y | 0° | +90° |
| +Z | +90° (pole) | Any |
| −Z | −90° (pole) | Any |

## Requirements

- Python 3.10 or later
- PyQt6, including the `QtOpenGLWidgets` module
- PyOpenGL
- NumPy
- OpenGL 3.1 or OpenGL ES 3.0

On Debian and Raspberry Pi OS, install the dependencies with:

```
sudo apt install python3-pyqt6 python3-opengl python3-numpy
```

The program has been run on a Raspberry Pi with a V3D 7.1 GPU, under Wayland,
using OpenGL 3.1 from Mesa.

## Running

Run these commands from this directory:

```
python3 src/main.py           # open the window
python3 src/main.py --check   # run the self-test, then exit
```

The self-test opens the window for a few seconds, so it needs a display. It
simulates mouse input, prints `PASS` or `FAIL` for each check, and exits with
status 0 only if everything passed.

## Mouse controls

| Input | Action |
|---|---|
| Left-drag | Rotate the cube and sphere |
| Right-drag | Move the light |
| Middle-drag | Pan |
| Wheel | Zoom |
| Double-click | Reset the view and the light |

The light stays fixed in the scene, so its dot doesn't move when you rotate the
cube.

## Configuration

Settings such as colours, opacity, grid spacing, bump depth and mouse sensitivity
are in [`src/config.py`](src/config.py).

## Code layout

The code is in [`src/`](src/). See [`src/README.md`](src/README.md) for how the
modules fit together.
