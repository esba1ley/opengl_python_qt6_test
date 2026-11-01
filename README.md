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
- OpenGL 3.1 or later, or OpenGL ES 3.0 or later

On Debian and Raspberry Pi OS, install the dependencies with:

```
sudo apt install python3-pyqt6 python3-opengl python3-numpy
```

`main.py` asks each platform for the newest OpenGL it offers, and the shaders
are compiled under the matching GLSL version. On Linux it requests OpenGL ES
3.1, which on a Raspberry Pi 5 is the native path of Mesa's V3D driver. On
macOS it requests an OpenGL 4.1 core profile, because macOS has no OpenGL ES
and offers only OpenGL 2.1 otherwise. The shader source is the same on both;
only the `#version` line differs, and it is chosen at run time from the
context that was actually created, so a platform that grants less than was
requested still works.

The program has been run on a Raspberry Pi with a V3D 7.1 GPU, under Wayland,
using OpenGL 3.1 from Mesa, and on an Apple M4 using OpenGL 4.1 core. The
OpenGL ES request has not yet been run on the Pi. Apple's core profile ignores
line widths above one pixel, so the axes draw thinner there than on the Pi.
In a conda environment, install the dependencies with:

```
conda install pyopengl numpy
pip install PyQt6
```

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

## Icon

`icon.png` is the application icon, which Qt shows in the Dock or taskbar
while the program runs. It is cropped from a screenshot of the window by
`tools/make_icon.py`, which finds the sphere, masks it to a disc and scales it
to 512 pixels. To regenerate it from a new screenshot:

```
python3 tools/make_icon.py tools/ScreenGrab.png icon.png
```

## Configuration

Settings such as colours, opacity, grid spacing, bump depth and mouse sensitivity
are in `src/config.py`.

## Documentation

A local HTML manual, built with Sphinx in the Read the Docs style, combines this
file, `src/README.md`, PlantUML diagrams of how the program executes and an API
reference generated from the docstrings. Rendering the diagrams needs
`plantuml`, a Java runtime and Graphviz, all from MacPorts on this machine.
Build it from the environment that runs the program:

```
pip install -r docs/requirements.txt
make -C docs html
open docs/_build/html/index.html
```

## Code layout

The code is in `src/`. See [`src/README.md`](src/README.md) for how the
modules fit together.
