# Decisions

Newest first.

## 2026-11-07 — Render the icon and README screenshot instead of capturing them
**Status:** Accepted
**Context:** `icon.png` was cropped by `tools/make_icon.py` from
`tools/ScreenGrab.png`, a hand-taken screenshot that was also the README's
top image. Every other image had become tool-rendered, and Erik asked
whether the capture should be automated so the icon follows the program.
**Decision:** `tools/make_icon.py` renders the default view offscreen at
1280 pixels and writes both the icon (cropped to the sphere, whose projected
radius it computes, then disc-masked) and `docs/images/screenshot.png`
(scaled to 640). `ScreenGrab.png` is deleted. The offscreen setup moves into
`tools/offscreen.py`, shared by all three image tools.
**Consequences:** The icon changed from a hand-rotated view lit from behind
to the default view, and the README image lost the macOS title bar. The
screenshot detection code (title bar, brightness bounding box) is gone. The
face images and animations came out byte-identical after the refactor.
Rejected: grabbing a shown window with `grabFramebuffer()` (needs a display
and adds nothing over 2x supersampling); keeping `ScreenGrab.png` for the
README only (the README image and the icon could drift apart).

## 2026-11-07 — Animate the mouse controls as WebP rendered through the real input path
**Status:** Accepted
**Context:** Erik asked for an animation of each mouse control in the
README. Frames had to come from the app, play on GitHub and in the Sphinx
manual, and not swell the repository, since git keeps every regenerated
version.
**Decision:** `tools/make_control_animations.py` drives a hidden
`CubeWidget` with synthetic events and records its own `paintGL` offscreen,
2x supersampled, with a painted cursor and label. Output is lossy animated
WebP at 240 pixels and quality 70, written with Pillow, which becomes a
development dependency (`pillow>=9.4`, Debian `python3-pil`) for this tool
only. Erik chose WebP after a comparison of formats.
**Consequences:** About 1.1 MB for all five, against roughly 5 MB as
animated PNG; quality 60 looked the same but 70 was kept as margin. Sphinx
9.1 copies `.webp` images although its HTML builder does not list the type.
Rejected: animated PNG (no dependency, but lossless and about five times
larger); GIF (256 colours band the textures); MP4 (GitHub will not play a
video from a repository path); calling `SceneContext` methods directly
(would not show that the mouse mapping works); screen recordings (not
reproducible).

## 2026-11-07 — Publish the manual to GitHub Pages from main
**Status:** Accepted
**Context:** Erik asked to publish the manual. It had been a local build
only, with hosting rejected on 2026-11-01 for lack of an audience. The
build imports every `src/` module and renders PlantUML, so whatever builds
it needs PyQt6, PyOpenGL, NumPy, PlantUML, Java and Graphviz.
**Decision:** A GitHub Actions workflow, `.github/workflows/docs.yml`,
builds with `make -C docs html` on pushes to `develop`, `main`, `ft/**` and
`rc/**` and
deploys with `actions/deploy-pages` from `main` only. Python packages come
from the two conda files through `setup-miniconda` with miniforge; PlantUML
and Graphviz from Ubuntu's apt, which the Pi showed renders the diagrams.
**Consequences:** The site at https://esba1ley.github.io/opengl_python_qt6_test/
always matches the latest release, and a broken build is seen on the branch
that broke it, before a release. Pages must be set to deploy from GitHub Actions in the
repository settings. Rejected: a hand-maintained `gh-pages` branch
(generated HTML in git and a manual step per release); Read the Docs (a
second service, with PlantUML and Graphviz to install through its own
configuration); publishing from `develop` (it would show unreleased work).

## 2026-11-07 — Render the README's material images with the program's renderer
**Status:** Accepted
**Context:** Erik asked for a small image of each material in the README's
"What it draws" table, captured from the app. The project had kept to one
image file, the icon, and the textures change whenever `textures.py` does.
**Decision:** `tools/make_face_images.py` turns each face to the camera,
draws it with `CubeRenderer` alone into an offscreen framebuffer under the
default light, crops to the face and writes 128-pixel PNGs to `docs/images/`.
The "one image file" rule now covers files the program loads; README
illustrations are allowed when a tool regenerates them.
**Consequences:** Six committed PNGs of 8 to 31 kB each, that go stale if a
material or the shader changes until the tool is rerun. Rejected: cropping
faces from window screenshots (the grid and axes cross every face, and the
faces are foreshortened); writing the raw albedo layers (not what the app
shows, with no bump lighting); HTML `<img>` tags to set a display width
(Sphinx would not copy the files).

## 2026-11-07 — Document each test's purpose in its docstring and the manual
**Status:** Accepted
**Context:** The suite's tests said what they checked but not why they
existed, so the case for each one lived only in a review conversation. Erik
asked whether that rationale was in the documentation; it was not.
**Decision:** Each test docstring gains a second paragraph on the bug it
would catch or the convention it pins, and `docs/tests/` renders the test
files with autodoc, one page per file, as `docs/api/` does for `src/`.
`docs/conf.py` puts the repository root on `sys.path` and mocks `pytest`.
**Consequences:** The rationale sits next to the test and is updated in the
same edit; changing a test docstring now needs a docs build. Rejected: a
hand-written page in `docs/` (a second copy that drifts the first time a
test changes); rationale in `ARCHITECTURE.md` (it describes structure, not
individual tests, and is outside the manual); requiring real `pytest` in
the docs build (the pip-only `docs/requirements.txt` route lacks it).

## 2026-11-02 — Configure pytest in pytest.ini
**Status:** Accepted
**Context:** pytest and coverage need configuration, and there are three
places to put it. The repository keeps one standalone file per tool.
**Decision:** A single `pytest.ini`, next to `ruff.toml` and
`.bumpversion.cfg`, holding the test path, the Qt binding and the coverage
options. No `.coveragerc`, because nothing is excluded from coverage.
**Consequences:** One more root file, and tool settings stay greppable by
tool. Rejected: `pyproject.toml` (the repo has none and adding one invites
packaging questions it does not need); `.coveragerc` to exclude the
`__main__` guard (`runpy` covers it, so excluding it would hide a branch).

## 2026-11-02 — Gate the suite on 100% line and branch coverage
**Status:** Accepted
**Context:** The program is small (542 statements, 56 branches), so complete
coverage is reachable, and a threshold only protects anything if it fails the
run.
**Decision:** `--cov-branch` and `--cov-fail-under=100` in `pytest.ini`, so
`pytest` exits non-zero below 100%.
**Consequences:** Every `src/` change needs tests that cover its new
branches, and a platform-specific arm needs a stub if this machine cannot
reach it. Rejected: line-only coverage (an untaken else-arm still counts as
covered); a lower threshold (it drifts down).

## 2026-11-02 — Test OpenGL code against a real offscreen context
**Status:** Accepted
**Context:** Most of `src/` issues GL calls. The suite had to say whether
they render correctly, and run as a normal `pytest` call.
**Decision:** Create a real offscreen `QOpenGLContext` with a
`QOffscreenSurface`, draw into a `QOpenGLFramebufferObject` and read pixels
back. Stub only branches this machine cannot reach, plus `main.main()` and the
`__main__` guard (listed under Testing in `ARCHITECTURE.md`).
**Consequences:** Tests need a display and take a few seconds.
Results depend on the local GL driver; the suite has run only on the Mac so
far. Rejected: mocking all of `OpenGL.GL` (headless and fast, but it verifies
call sequences, not rendering).

## 2026-11-01 — Give Debian and Raspberry Pi OS commented apt lists
**Status:** Accepted
**Context:** The conda files cover macOS and 64-bit Linux with miniforge, but
Raspberry Pi developers use apt, and the README had one bare install line.
The question was also whether Pi OS needs anything Debian does not.
**Decision:** Two commented lists, `apt-packages.txt` for runtime and
development and `apt-packages-docs.txt` for the manual's system tools, each
installable with `sudo apt install $(sed 's/#.*//' file)`. One list serves
both distributions, since Pi OS Bookworm and Trixie are Debian 12 and 13
with the same package names; the README explains the real differences
(preinstalled graphics stack and session, firmware, 32-bit image, Pi
archive overlay). Ruff and the Sphinx packages are taken from pip in a
`--system-site-packages` venv rather than apt. The conda floors were
lowered to the Bookworm versions (pyqt6 6.4, PyOpenGL 3.1.6, NumPy 1.24),
the oldest set the program is known to run on.
**Consequences:** A Pi developer needs two apt lines and one venv. Package
names and versions were checked against the Debian archive, not installed
on a Pi in this session. Rejected: apt for Sphinx too (Bookworm ships
Sphinx 5.3, myst-parser 0.18 and sphinx-rtd-theme 1.2, and both releases
ship sphinxcontrib-plantuml at upstream 0.5 from 2014, which predates the
`svg_img` output format `conf.py` uses); a shell script instead of lists
(hides what is installed and adds a thing to maintain); separate Pi OS and
Debian lists (identical content).


## 2026-11-01 — Pin the environment in conda files, system tools in the README
**Status:** Accepted
**Context:** The repository recorded its dependencies only as README prose,
and the working environment had grown mixed: PyQt6 from pip with its own
bundled Qt beside an unused conda-forge `qt6-main`, Graphviz from both
conda-forge and MacPorts with PlantUML rejecting the conda one, and the JDK
installed by hand. A fresh clone could not reproduce it.
**Decision:** Two conda-forge environment files: `environment.yml` for the
runtime plus `ruff` and `bump2version`, and `environment-docs.yml` layered on
with `conda env update` for the Sphinx packages, mirrored by
`docs/requirements.txt` for pip. PyQt6 comes from conda-forge's `pyqt6` so
Qt is installed once. Version floors only. Everything that is not a Python
package is documented in a README table with the MacPorts and apt commands,
and Graphviz is deliberately excluded from the conda files.
**Consequences:** A clone is reproducible on macOS and Linux with miniforge;
Raspberry Pi OS keeps the apt path, which the files cannot express.
Verifying in a fresh environment showed Ruff 0.17's default rule set (409
rules) flagging code that Ruff 0.14's (61 rules) accepted, so `ruff.toml`
pins the classic `E4, E7, E9, F` selection the code was written against;
widening it is left as a separate decision. The
existing `esb312` environment is unchanged; its pip PyQt6 and conda Graphviz
remain a local inconsistency that the new environment avoids. Rejected:
`pyproject.toml` with extras (pip cannot install Qt once and share it; the
project has no package to install); a single environment file (forces the
docs toolchain on every runtime clone); exact pins or `conda env export`
(platform-specific builds would not resolve on the Pi).


## 2026-11-01 — Hand-drawn PlantUML diagrams of execution and mouse handling
**Status:** Accepted
**Context:** The manual needed to show how the program executes and what it
does on mouse events. PlantUML was the required notation, and PlantUML has no
generator for Python call graphs.
**Decision:** Five hand-written sources in `docs/diagrams/`, rendered at
build time by sphinxcontrib-plantuml: a class diagram with function-only
modules drawn as `<<module>>` boxes; sequence diagrams for startup to first
frame, one `paintGL()` call, and mouse input with the three drag buttons as
`alt` branches plus wheel and double-click; and a call graph of every
function reachable from `main()`, grouped by module, with `selftest` and the
small texture helpers omitted. A CLAUDE.md rule makes updating the diagrams
part of any change to the call structure.
**Consequences:** The diagrams can drift from the code, which the rule
mitigates but does not prevent. Rendering adds `plantuml`, a Java runtime
and Graphviz as build prerequisites; conda-forge's Graphviz 13.1 emits SVG
that PlantUML 1.2026.6 cannot parse, so `conf.py` passes `-graphvizdot
/opt/local/bin/dot` when that MacPorts binary exists. Rejected: generated call graphs via pyan3 or
code2flow (Graphviz output, not PlantUML, and noisy at this size); one
sequence diagram per mouse button (identical shape five times); including
`selftest` in the call graph (it drives the widget from outside and would
double the mouse edges).


## 2026-11-01 — Document with Sphinx, including the READMEs in place
**Status:** Accepted; its rejection of hosting is superseded by 2026-11-07 —
Publish the manual to GitHub Pages from main
**Context:** A browsable manual was wanted, built locally and opened by hand,
without duplicating the prose that already lives in `README.md` and
`src/README.md` or exposing the working notes under `.claude/`.
**Decision:** A `docs/` Sphinx project with the Read the Docs theme. Prose
pages use MyST's include directive to read the two READMEs from their real
locations; the including pages are named `index` and `src/README` so the
README's own link to `src/README.md` becomes a page cross-reference. API
pages are one `automodule` per module, rendered by Sphinx's built-in
napoleon in NumPy mode. The build runs with warnings as errors.
`.claude/` is not included.
**Consequences:** Two README links that pointed at a directory and a source
file were reduced to inline code, since a link that is not a docs page fails
the build. Shader constants gained `#:` doc-comments so autodoc lists them.
Sphinx 9.1 builds cleanly with sphinx-rtd-theme 3.0.2 despite the theme's
declared upper bound of Sphinx 8. Rejected: numpydoc (an extra dependency
for no gain at this size); copying the READMEs into `docs/` (two sources to
drift); a hosted Read the Docs configuration (no audience for it).


## 2026-11-01 — Gate bump lighting on the geometric face normal
**Status:** Accepted
**Context:** The cube fragment shader lit each pixel from the normal-mapped
normal alone. On a face turned away from the directional light, bumps sloping
towards the light still received diffuse and specular light, so rivet rims and
mortar edges glowed inside the cube's own shadow.
**Decision:** Multiply diffuse and specular by
`smoothstep(0.0, 0.1, dot(faceNormal, lightDirection))` in
`CUBE_FRAGMENT_BODY`. A convex cube cannot shadow itself any other way under
parallel light, so the face normal alone decides whether a face is lit.
**Consequences:** Shadowed faces show only the ambient term. The 0.1 fade
width avoids a hard seam at the terminator and follows the shader's existing
hard-coded lighting constants. Rejected: shadow mapping (no occluder other
than the cube itself, so pointless); horizon mapping to self-shadow bumps
within a lit face (large change, needs per-material horizon textures).

## 2026-11-01 — Request the newest OpenGL per platform, derive GLSL version at run time
**Status:** Accepted
**Context:** The goal was the most advanced OpenGL on both the Raspberry Pi 5
and macOS with minimal code differences. The platforms share no context
version: macOS offers desktop GL up to 4.1 core and no OpenGL ES; Mesa's V3D
stops at desktop GL 3.1 but reaches OpenGL ES 3.1. A single `#version 300 es`
shader set was ruled out because macOS cannot compile it.
**Decision:** `main.py` requests 4.1 core on macOS and OpenGL ES 3.1
elsewhere, the only platform test in the program. `gl_utils.glsl_header`
builds the `#version` line from the created context's major and minor version
instead of fixed strings, and on ES declares `highp float` and
`lowp sampler2DArray` precision, since GLSL ES gives neither a default in
fragment shaders. Shader bodies stay unchanged and limited to GLSL 1.40
features so one source serves every header.
**Consequences:** macOS now compiles the shaders as GLSL 4.10 and `--check`
passes. The Pi will compile them as GLSL ES 3.10 once verified; if Qt refuses
the ES request the header falls back to whatever desktop version is granted.
Risk: PyOpenGL's desktop `GL` module may not dispatch under an EGL ES context;
the fallback is routing imports through PyOpenGL's `GLES3` module. Rejected:
GLSL 1.40 everywhere (already the state, but not the newest driver path on
the Pi); ES 3.00 on both (impossible on macOS); hard-coded per-platform
headers (fail instead of degrade when a platform grants less).

## 2026-11-01 — Request a core profile only on macOS
**Status:** Superseded by 2026-11-01 — Request the newest OpenGL per platform
**Context:** On macOS, Qt's default surface format yields a legacy OpenGL 2.1
context, which rejects `#version 140` shaders. The Raspberry Pi target offers
OpenGL 3.1 and no 3.2 core context, so an unconditional 3.2 core request could
break it.
**Decision:** In `main.py`, when `sys.platform == "darwin"`, set a default
`QSurfaceFormat` with version 3.2 and `CoreProfile` before constructing
`QApplication`. Make `widget.py` start from `QSurfaceFormat.defaultFormat()`
instead of a blank format so the request is not overwritten.
**Consequences:** Shaders stay at GLSL 1.40, so the Pi path is unchanged.
macOS reports GL 4.1 core and all `--check` tests pass. Wider axis lines are
ignored by Apple's core profile. Rejected: raising the shader version to 1.50
(breaks the Pi); setting the profile in the widget only (Qt's shared context
on macOS is created from the default format, so the two must match).
