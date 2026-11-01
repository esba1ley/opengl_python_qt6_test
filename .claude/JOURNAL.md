# Journal

Newest first.

## 2026-11-01 — Newest OpenGL per platform

- `src/main.py` now requests a 4.1 core profile on macOS and OpenGL ES 3.1
  elsewhere. `src/gl_utils.py` derives the GLSL `#version` line from the
  created context and adds `float` and `sampler2DArray` precision on ES,
  fixing an ES header that would never have compiled. See `DECISIONS.md`.
- Shader bodies untouched. Verified on macOS: context reports GL 4.1 Metal,
  header `#version 410`, `--check` passes, saved frame unchanged. Every header
  branch checked with stub contexts.
- Updated `README.md`, `.claude/CLAUDE.md` and `ARCHITECTURE.md`.

**Next:** Run `--check` on the Pi and confirm the version line reads
"OpenGL ES 3.1 Mesa". If PyOpenGL fails under the ES context, route GL
imports through `OpenGL.GLES3`.

## 2026-11-01 — Release v0.1.0

- Added `.bumpversion.cfg` and `__version__` in `src/main.py` so bump2version
  owns the version number. Merged `develop` into `main` and tagged `v0.1.0`.

**Next:** Nothing queued.

## 2026-11-01 — Application icon from a screenshot

- Added `tools/make_icon.py`, which locates the black client area below the
  title bar, finds the sphere's bounding box, crops a padded square, masks it
  to a soft-edged disc and scales it to 512 px. PyQt6 and NumPy only.
- Generated `icon.png` from `ScreenGrab.png` and set it with
  `QApplication.setWindowIcon` in `src/main.py`.
- `--check` passes. The source screenshot is kept as `tools/ScreenGrab.png`.

**Next:** Nothing queued.

## 2026-11-01 — Stop shadowed faces catching light

- Confirmed the light is directional, so all rays are parallel and the cube
  cannot cast shadows on itself except by face orientation.
- Added a geometric-normal gate to `CUBE_FRAGMENT_BODY` in `src/shaders.py`.
  See the matching entry in `DECISIONS.md`.
- Verified with before/after frames lit from behind the visible faces, plus
  `--check` passing. Default view is visually unchanged.

**Next:** Nothing queued.

## 2026-11-01 — First run on macOS

- Ran `python3 src/main.py --check` on an Apple M4 Mac from the `esb312`
  conda environment. It failed with `version '140' is not supported` because
  macOS handed out an OpenGL 2.1 context.
- Added a macOS-only 3.2 core profile request in `src/main.py` and changed
  `src/widget.py` to extend the default format rather than replace it. See
  the 2026-11-01 entry in `DECISIONS.md`.
- Self-test passes all six checks; a saved frame shows the cube, grid, axes
  and light dot correctly. Axes are one pixel wide on macOS.
- Documented the macOS requirement in `README.md` and `.claude/CLAUDE.md`, and
  created `ARCHITECTURE.md`, `DECISIONS.md` and this journal.

**Next:** Nothing queued. The Pi path should be re-run to confirm the
`defaultFormat()` change is neutral there.
