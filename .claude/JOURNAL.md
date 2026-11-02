# Journal

Newest first.

## 2026-11-01 — Pi confirms the apt recipe

- Erik ran both apt lists, the `--system-site-packages` venv with Ruff and
  `docs/requirements.txt`, `--check` inside it and `make -C docs html` on
  the Raspberry Pi. All passed, so Debian's PlantUML 1.2020.2, Graphviz 2.42
  and Java render the diagrams, and apt's PyQt6 and PyOpenGL run under the
  ES context. The Pi runs Raspberry Pi OS on Debian 13.7 (trixie), so the
  packages exercised were the trixie versions (PyQt6 6.9.0, PyOpenGL 3.1.9,
  NumPy 2.2); the bookworm floors in `environment.yml` remain untested on
  bookworm itself. Platform coverage in `ARCHITECTURE.md` updated.

**Next:** Merge `ft/esbailey/top-gl-version-per-platform` into `develop`.
Vanilla Debian remains untested.


## 2026-11-01 — Pi confirms the OpenGL ES context

- Erik ran the program on the Pi under the OpenGL ES request from commit
  `31e7f37`; it runs, which also confirms PyOpenGL's desktop `GL` module
  works under an ES context. Updated `ARCHITECTURE.md` (shader targets,
  platform coverage), `CLAUDE.md` and the README accordingly.
- Committed the environment and apt work as `ef7bcc4`.

**Next:** On the Pi, run both apt lines, the venv recipe, `--check` and
`make -C docs html` to check the recipe in `apt-packages.txt`. Then merge
`ft/esbailey/top-gl-version-per-platform` into `develop`. Done in the entry
above.


## 2026-11-01 — apt lists for Debian and Raspberry Pi OS

- Added `apt-packages.txt` and `apt-packages-docs.txt`, checked package
  names and bookworm/trixie versions against the Debian archive, and lowered
  the `environment.yml` floors to the bookworm versions. See `DECISIONS.md`.
- README "Python environment" now points at the lists and a venv recipe for
  Ruff and Sphinx; new "Raspberry Pi OS versus Debian" subsection.
- Not run on a Pi or Debian in this session; the macOS docs build and lint
  still pass.

**Next:** On the Pi, run both apt lines, the venv recipe, `--check` (also
settling the pending OpenGL ES context question) and `make -C docs html`.
Done for the ES context in the entry above; the apt recipe remains.


## 2026-11-01 — Reproducible environment

- Inventoried every import and its installed origin: PyQt6 6.9.1 via pip,
  PyOpenGL 3.1.10 and NumPy 2.3.5 via conda-forge, Sphinx tooling split
  across both, PlantUML and Graphviz from MacPorts, Oracle JDK 25 by hand.
- Added `environment.yml` and `environment-docs.yml`, rewrote
  `docs/requirements.txt` to mirror the latter, and replaced the README's
  Requirements section with Requirements, Setting up (Python environment,
  System prerequisites table, OpenGL versions). See `DECISIONS.md`.
- Verification: a fresh `opengl_qt6_test` environment created from the two
  files resolved to Python 3.12.16, pyqt6 6.11.0 on one qt6-main 6.11.2,
  PyOpenGL 3.1.10, NumPy 2.5.4, Sphinx 9.1.1, with nothing from pip. From
  inside it `--check` passes (GL 4.1, GLSL 4.10) and `make -C docs html`
  builds all five diagrams using the MacPorts `dot`, `plantuml` and the
  Oracle JDK.
- Its Ruff 0.17.3 flagged three things Ruff 0.14.10 did not, because the
  default rule set changed. Added `ruff.toml` pinning the classic selection;
  both versions now report 61 rules and a clean tree.

**Next:** Nothing queued beyond the pending Pi run of the ES context.


## 2026-11-01 — PlantUML diagrams in the manual

- Added `docs/diagrams/` with `classes`, `startup`, `frame`, `mouse` and
  `calls` sources, `docs/diagrams.rst` to show them, and the
  sphinxcontrib-plantuml extension in `docs/conf.py`. See `DECISIONS.md`.
- Updated `README.md`, `.claude/CLAUDE.md`, `ARCHITECTURE.md` and
  `docs/requirements.txt` for the PlantUML and Java prerequisites.
- A JDK 25 was installed for PlantUML. The class and call-graph diagrams
  then failed under the conda Graphviz 13.1 (`plantuml -testdot`: "dot
  generates unreadable SVG file"); `conf.py` now passes the MacPorts `dot`.
- `make -C docs html` builds with no warnings. All five diagrams were
  rendered to PNG and checked against `src/` by eye.

**Next:** Nothing queued beyond the pending Pi run of the ES context.


## 2026-11-01 — Sphinx documentation

- Added `docs/` with `conf.py`, `index.md`, `src/README.md`, `api/` pages for
  all eleven modules, a `Makefile` and `requirements.txt`. See `DECISIONS.md`.
- Added `#:` doc-comments to the four constants in `src/shaders.py`, unlinked
  two README references that had no docs page, and added a Documentation
  section to `README.md`. `docs/_build/` is ignored by git.
- `make -C docs html` builds with no warnings; `--check` still passes.

**Next:** Nothing queued beyond the pending Pi run of the ES context.


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
