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

## Documentation
**Status:** Frozen

`docs/` holds a Sphinx project for a local HTML build only; there is no
hosted configuration. `docs/index.md` and `docs/src/README.md` pull in the
repository's `README.md` and `src/README.md` with MyST's include directive,
so the READMEs remain the single source and the Sphinx page names mirror the
file paths so the README's relative link resolves. `docs/api/` has one
automodule page per module in `src/`, rendered by napoleon from the
NumPy-style docstrings with the Read the Docs theme. `docs/diagrams.rst`
renders five hand-maintained PlantUML sources from `docs/diagrams/` through
sphinxcontrib-plantuml: a class diagram, sequence diagrams for startup, one
frame and mouse input, and a call graph of everything reachable from
`main()`. Build dependencies are listed in `docs/requirements.txt`, separate
from the program's three; the diagrams also need `plantuml`, a Java
runtime and Graphviz, with `conf.py` preferring the MacPorts `dot`.

## Environment
**Status:** Frozen

`environment.yml` is the minimum conda-forge environment to run and develop
the program (Python 3.12, pyqt6, pyopengl, numpy, ruff, bump2version);
`environment-docs.yml` layers the Sphinx packages onto it with
`conda env update`, and `docs/requirements.txt` mirrors that second file for
pip. Version floors only, no exact builds, so the same files resolve on
arm64 macOS and Linux. `ruff.toml` pins the lint rule selection, since
Ruff's defaults differ between versions. Non-Python prerequisites (OpenGL driver, PlantUML,
Java, Graphviz, make) are documented in the README's system prerequisites
table with MacPorts and apt commands, and Graphviz is kept out of the conda
environment on purpose. Debian and Raspberry Pi OS are covered by
`apt-packages.txt` (runtime and development) and `apt-packages-docs.txt`
(system tools for the manual), with Ruff and the Sphinx packages from pip in
a `--system-site-packages` venv because Debian's are missing or too old.

## Application icon
**Status:** Frozen

`icon.png` at the repository root, set with `QApplication.setWindowIcon` in
`main.py`. Derived, not hand-drawn: `tools/make_icon.py` crops a window
screenshot to a disc around the sphere grid. There is no `.icns` or app
bundle, so the icon only appears while the program runs.
