# Architecture

What the repository is now. Rationale lives in `DECISIONS.md`; history in
`JOURNAL.md`. Module structure is described in `src/README.md` and is not
repeated here.

## Module layout
**Status:** Frozen

Plain modules in `src/`, imported by name, with `SceneContext` as the single
runtime-state holder and `config.py` for fixed settings. See `src/README.md`.

## OpenGL context selection
**Status:** Frozen

`main.py` sets the default `QSurfaceFormat` before creating the application
and asks for the newest OpenGL each platform offers: a 4.1 core profile on
macOS, OpenGL ES 3.1 elsewhere. `widget.py` builds its own format from
`QSurfaceFormat.defaultFormat()` and only adds depth and multisampling, so
the request survives. Nothing else in the program tests the platform.

## Shader language targets
**Status:** Frozen

Shader bodies carry no version line and use only features common to GLSL 1.40
and GLSL ES 3.00. `gl_utils.glsl_header` prepends a `#version` line derived
from the version of the current context (GLSL 1.40, 1.50, 3.30 and up, or
GLSL ES 3.x0), plus `float` and `sampler2DArray` precision statements on ES.
Verified under GLSL 1.40 and 4.10; the ES header has not yet been run.

## Platform coverage
**Status:** Open

Verified on Raspberry Pi (V3D 7.1, Wayland, Mesa GL 3.1, before the switch to
an ES request) and macOS (Apple M4, GL 4.1 core). On macOS the axis line width
is clamped to one pixel by the driver. The OpenGL ES 3.1 request on the Pi,
and PyOpenGL's desktop `GL` module under an ES context, are unverified. No
Linux desktop or Windows run yet.

## Application icon
**Status:** Frozen

`icon.png` at the repository root, set with `QApplication.setWindowIcon` in
`main.py`. Derived, not hand-drawn: `tools/make_icon.py` crops a window
screenshot to a disc around the sphere grid. There is no `.icns` or app
bundle, so the icon only appears while the program runs.
