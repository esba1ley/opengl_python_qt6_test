# Architecture

What the repository is now. Rationale lives in `DECISIONS.md`; history in
`JOURNAL.md`. Module structure is described in `src/README.md` and is not
repeated here.

## Module layout
**Status:** Frozen

Plain modules in `src/`, imported by name, with `SceneContext` as the single
runtime-state holder and `config.py` for fixed settings. See `src/README.md`.

`textures.py` is organised for reading: primitives, six shared patterns,
six materials that each return `Material(color, height, steps)`, packing
functions, and `iter_materials`, which replays the materials in order on one
random generator. `generate_texture_layers` consumes it and keeps only colour
and height. `shaders.CUBE_FRAGMENT_BODY` has a `view` uniform (`CUBE_VIEWS`)
that `SceneContext.cube_view` sets through `CubeRenderer`; view 0 is the
normal lit image.

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
Verified under GLSL 1.40 and 4.10, and under the ES header on the Pi.

## Platform coverage
**Status:** Open

Verified on Raspberry Pi (V3D 7.1, Wayland, Mesa GL 3.1 before the switch to
an ES request, and the OpenGL ES request on 2026-11-01, through PyOpenGL's
desktop `GL` module) and macOS (Apple M4, GL 4.1 core). On macOS the axis
line width is clamped to one pixel by the driver. The apt and venv recipe in
`apt-packages.txt`, `apt-packages-docs.txt` and the README was run on the Pi
under Raspberry Pi OS trixie (Debian 13.7) on 2026-11-01: install, venv,
`--check` and the docs build all passed, and passed again with `pytest`
on 2026-11-08 after the teaching refactor. Not yet run on bookworm, vanilla
Debian, another Linux desktop or Windows.

## Testing
**Status:** Frozen

`tests/` at the repository root holds one `test_<module>.py` per `src/`
module, plus `test_conftest.py` for the fixtures. `pytest.ini` is the only
configuration: it sets `testpaths`, `qt_api = pyqt6`, and the coverage
options, including `--cov-fail-under=100`, so a plain `pytest` fails when line
or branch coverage of `src` falls below 100%. Nothing is excluded from
coverage. `tests/conftest.py` puts `src` on `sys.path` and sets the default
`QSurfaceFormat` as `main.py` does in `pytest_configure`, and provides the
fixtures `gl_context` (a shared offscreen `QOpenGLContext` made current per
test), `fbo` (a bound 256 by 256 `QOpenGLFramebufferObject` with depth),
`scene` (a fresh `SceneContext`), `image_to_array` and the autouse
`restore_default_format`.

OpenGL code is tested against a real offscreen context: renderers draw into
the `fbo` and the tests read pixels back. Stubs cover branches this
machine cannot reach (the `glsl_header` ES and older-desktop arms, both arms
of the `overlay.py` ES check around `GL_PROGRAM_POINT_SIZE`), plus
`main.main()` and the `__main__` guard, where only one `QApplication` may
exist per process.
Tests that show a widget, and the real `selftest.check` run, need a display,
like `--check`. Rationale is in `DECISIONS.md`.

Verified on macOS (GL 4.1 core) under Python 3.12 and, on 2026-11-08,
Python 3.11.18 (NumPy 2.4.6, same texture bytes), and on the Pi under its
OpenGL ES 3.1 request with Python 3.13.5 (2026-11-08). Not yet run under
the Pi's desktop GL 3.1.

## Documentation
**Status:** Frozen

`docs/` holds a Sphinx project for an HTML build. `.github/workflows/docs.yml`
builds it on GitHub Actions for every push to `develop`, `main`, `ft/**` and
`rc/**` and
publishes it to GitHub Pages (https://esba1ley.github.io/opengl_python_qt6_test/) from `main`
only. The runner takes the Python packages from `environment.yml` and
`environment-docs.yml` through miniforge and PlantUML, Java and Graphviz from
apt. The Miniforge installer is pinned (`MINIFORGE_VERSION` in the
workflow) and kept in the Actions cache, downloaded with retries only on a
cache miss. `docs/guide/` is the teaching chapter (see Teaching guide).
`docs/index.md` and `docs/src/README.md` pull in the
repository's `README.md` and `src/README.md` with MyST's include directive,
so the READMEs remain the single source and the Sphinx page names mirror the
file paths so the README's relative link resolves. `docs/api/` has one
automodule page per module in `src/`, rendered by napoleon from the
NumPy-style docstrings with the Read the Docs theme. `docs/tests/` does the
same for each file in `tests/`, `conftest.py` included, so the reason for
each test is rendered from its docstring; `conf.py` mocks `pytest` so the
pages build without it. `docs/diagrams.rst`
renders five of the six hand-maintained PlantUML sources in `docs/diagrams/` through
sphinxcontrib-plantuml: a class diagram, sequence diagrams for startup, one
frame and mouse input, and a call graph of everything reachable from
`main()`. Build dependencies are listed in `docs/requirements.txt`, separate
from the program's three; the diagrams also need `plantuml`, a Java
runtime and Graphviz, with `conf.py` preferring the MacPorts `dot`.

## Environment
**Status:** Frozen

`environment.yml` is the minimum conda-forge environment to run and develop
the program (Python 3.12, pyqt6, pyopengl, numpy; for development ruff,
bump2version, pytest, pytest-cov, pytest-qt and Pillow, the last only for
`tools/make_control_animations.py`);
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

## Teaching guide
**Status:** Frozen

The repository doubles as a teaching example. `docs/guide/` holds the "How it
works" chapter in five pages (`index`, `primitives`, `materials`, `gpu`,
`shaders`), reached from `docs/index.md`. It quotes `src/` with
`literalinclude`, so a rename fails the build, and sets its maths with MyST
`dollarmath` (enabled in `docs/conf.py`; MathJax loads from a CDN when a page
is viewed). `docs/diagrams/textures.puml` is its PlantUML activity diagram.
Its 60 images are in `docs/images/guide/`, written by
`tools/make_guide_images.py` in four groups: the primitives
(`primitive_images`), the shared patterns (`pattern_images`), every recorded
step and normal map of each material from `textures.iter_materials`, and the
cube drawn through each `CUBE_VIEWS` entry; they are committed and
regenerated only when a material, a pattern or the cube shader changes.

## Application icon
**Status:** Frozen

`icon.png` at the repository root, set with `QApplication.setWindowIcon` in
`main.py`. Rendered, not drawn: `tools/make_icon.py` draws the default view
offscreen at 1280 pixels through the window's own `paintGL`, crops a square
around the sphere grid, whose projected radius it computes from `config`,
masks it to a soft-edged disc and scales it to 512 pixels. There is no
`.icns` or app bundle, so the icon only appears while the program runs.

## README illustrations
**Status:** Frozen

Every image in `docs/images/` is rendered by a tool in `tools/`; the chapter's
images in `docs/images/guide/` are described under Teaching guide. The tools
share `tools/offscreen.py`, which requests the program's surface format,
makes an offscreen context current, binds a framebuffer and initialises a
hidden `CubeWidget`'s renderers on it.

`docs/images/screenshot.png`, the default view at 640 pixels, is shown at
the top of the README; `tools/make_icon.py` writes it from the same render
as the icon. Six `docs/images/face-<material>.png` images, 128 pixels
square, sit in its material table. `tools/make_face_images.py` renders them
with the program's own `CubeRenderer` alone, each face
turned to the camera under `config.DEFAULT_LIGHT`, without the overlay.

Five `docs/images/control-<gesture>.webp` animations, 240 pixels square and
looping, sit in the mouse controls table. `tools/make_control_animations.py`
sends synthetic events through `QApplication.sendEvent` to a hidden
`CubeWidget`, draws each frame with the widget's own `paintGL` into an
offscreen framebuffer at twice the size, scales it down, paints a cursor and
a gesture label with `QPainter`, and writes lossy WebP at quality 70 with
Pillow. Each sequence returns to its first view. The
include in `docs/index.md` uses `:relative-images:` so the same paths work on
GitHub and in the manual.
