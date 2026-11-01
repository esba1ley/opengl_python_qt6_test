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

`main.py` sets the default `QSurfaceFormat` before creating the application.
On macOS it requests an OpenGL 3.2 core profile; elsewhere it leaves the Qt
default so the Raspberry Pi gets its OpenGL 3.1 context. `widget.py` builds its
own format from `QSurfaceFormat.defaultFormat()` and only adds depth and
multisampling, so the profile request survives.

## Shader language targets
**Status:** Open

Shader bodies carry no version line; `gl_utils.glsl_header` prepends
`#version 140` or `#version 300 es`. The ES path has never been run.

## Platform coverage
**Status:** Open

Verified on Raspberry Pi (V3D 7.1, Wayland, Mesa GL 3.1) and macOS (Apple M4,
GL 4.1 core). On macOS the axis line width is clamped to one pixel by the
driver. No Linux desktop or Windows run yet.

## Application icon
**Status:** Frozen

`icon.png` at the repository root, set with `QApplication.setWindowIcon` in
`main.py`. Derived, not hand-drawn: `tools/make_icon.py` crops a window
screenshot to a disc around the sphere grid. There is no `.icns` or app
bundle, so the icon only appears while the program runs.
