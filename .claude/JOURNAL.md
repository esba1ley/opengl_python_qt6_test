# Journal

Newest first.

## 2026-11-08 — References and further reading

- `docs/references.md`: new top-level page after the guide, linking the
  documentation and the authors' tutorials for Python, the runtime,
  development and documentation packages, Qt 6 (by the classes the program
  uses), OpenGL, OpenGL ES and GLSL (a table of the specifications per
  platform), platform notes and the two quaternion-convention papers.
- `docs/guide/*.md`: a "Further reading" list at the end of each page;
  `index.md` points at the references page.
- `README.md`, `src/README.md`, `docs/diagrams.rst` and the guide pages:
  the first prose mention of each package on a page (PyQt6, PyOpenGL,
  NumPy, Qt, ctypes, the test, docs and environment tools) links to its
  documentation. Headings, code and existing links are left alone.
- Every link checked on 2026-11-08 with `curl` and Sphinx's linkcheck;
  the Khronos wiki and SourceForge refuse automated requests, so those were
  confirmed through redirects and search instead.
- `README.md`, `.claude/CLAUDE.md` and `.claude/ARCHITECTURE.md` mention the
  page; reason in `DECISIONS.md`.

## 2026-11-08 — Guide from the window to the frame

- `docs/guide/`: new pages `window`, `context`, `spaces`, `geometry`,
  `buffers` and `frame`; `index` rewritten around three captioned parts; the
  vertex-layout section moved from `gpu.md` to `geometry.md`. The depth-mask
  and line-width explanations were corrected after measuring the grid's
  depth write (its own far-side lines, then gaps in the axes and dot).
- `src/geometry.py`: `CUBE_FACES` names the faces. `src/main.py`:
  `request_surface_format` is the one platform-gated format request, used by
  `main()`, `tools/offscreen.py` and `tests/conftest.py`.
- `src/shaders.py`: five geometry debug views (`CUBE_VIEWS` now has 11);
  the layer view is grey = (layer + 1) / 6 so layer 0 is visible.
  `src/widget.py`: `resizeGL`'s docstring corrected to device-independent
  pixels (Qt 6 passes `width()` and `height()`).
- `tools/make_guide_images.py`: hyphenated view file names and the four
  frame build-up images; the guide has 69 images.
- Project documents updated: `README.md`, `src/README.md`,
  `.claude/CLAUDE.md` (the rerun rule, the depth rule),
  `.claude/ARCHITECTURE.md`; reasons in the five `DECISIONS.md` entries of
  this date. Reflowed one long line in `src/README.md`; the long
  `ARCHITECTURE.md` lines (the Documentation paragraph and two in the
  Teaching guide) were rewrapped to 80 columns in the final fix wave.

**Next:** Run `pytest` and `--check` on the Pi under OpenGL ES for the new
views; the deferred minors the final review leaves.

## 2026-11-08 — Python 3.11 run

- Ran `pytest -W error` (118 passed, 100% coverage) and `--check` (6 PASS)
  on macOS under Python 3.11.18 in `opengl_qt6_test_311`; texture hash
  unchanged under NumPy 2.4.6. Recorded in `ARCHITECTURE.md` (Testing).
- The `environment.yml` recipe for another Python version passed
  `python=3.11` to `conda env create`, which rejects it; replaced with a
  `sed` copy.

**Next:** Pi face-image comparison of view 0; the surface-format factoring.

## 2026-11-08 — Release v0.4.0

- Cut `rc/esbailey/v0.4.0` from `develop` and ran `bump2version minor`
  without tagging. Merged into `main`, tagged `v0.4.0`, and merged `main`
  back into `develop`.
- Adds the teaching restructure of `textures.py`, the cube shader's `view`
  uniform, `tools/make_guide_images.py` and the "How it works" chapter. Texture
  bytes and the lit image are unchanged.

**Next:** Pi face-image comparison of view 0, Python 3.11, and the
surface-format factoring.

## 2026-11-08 — Pi run of the teaching branch

- Erik ran `pytest`, `python3 src/main.py --check` and `make -C docs html` on
  the Pi (OpenGL ES 3.1, Python 3.13.5) at `ft/esbailey/textures-guide`; all passed, the
  test suite for the first time there. Recorded in `ARCHITECTURE.md`
  (Testing, Platform coverage).

**Next:** On the Pi, compare `tools/make_face_images.py` output from
`develop` and this branch to confirm view 0 is byte-identical under GLES;
the suite does not check that.

## 2026-11-07 — Teaching example: patterns, steps, debug view and guide chapter

- Factored six shared patterns out of `src/textures.py`; materials now return
  `Material(color, height, steps)` and `iter_materials` replays them. Texture
  bytes unchanged (sha256 prefix `70bf2f00d9547795`).
- Added the `view` uniform to the cube fragment shader, `CUBE_VIEWS`,
  `config.DEFAULT_CUBE_VIEW` and `SceneContext.cube_view`; view 0 renders
  unchanged.
- Added `tools/make_guide_images.py` (60 images in `docs/images/guide/`) and
  the chapter in `docs/guide/` with `docs/diagrams/textures.puml`.
- Restated the README, `src/README.md` and these documents; corrected the
  `uv_grid` and `generate_texture_layers` docstrings and three chapter
  sentences. See `DECISIONS.md`.

**Next:** Run `pytest` and `--check` on the Pi, where view-0 identity under
GLES and GL 3.1 is still unverified.

## 2026-11-07 — Rendered icon and screenshot, shared offscreen module

- Added `tools/offscreen.py` and moved the face-image and animation tools
  onto it; both regenerated byte-identical files.
- Rewrote `tools/make_icon.py` to render the default view and write
  `icon.png` and `docs/images/screenshot.png`; deleted `tools/ScreenGrab.png`.
  See `DECISIONS.md`. Compared old and new icons by eye.

**Next:** The surface-format lines now live in `main.py`, `tests/conftest.py`
and `tools/offscreen.py`.

## 2026-11-07 — Animations of the mouse controls

- Added `tools/make_control_animations.py` and five looping WebP animations
  in `docs/images/`, shown in a new column of the README's mouse controls
  table. See `DECISIONS.md`. Checked by contact sheet: each control does what
  its label says, and each loop ends where it began.
- Added Pillow as a development dependency to `environment.yml` and
  `apt-packages.txt` (Debian bookworm 9.4.0, trixie 11.1.0, checked against
  sources.debian.org).

**Next:** Check the animations play on the GitHub README and the Pages site
after release.

## 2026-11-07 — Release v0.3.2

- Cut `rc/esbailey/v0.3.2` from `develop` and ran `bump2version patch`
  without tagging. Merged into `main`, tagged `v0.3.2`, and merged `main`
  back into `develop`.
- Adds the GitHub Pages workflow; pushing `main` publishes the manual. The
  program is unchanged apart from the version.

**Next:** As before: Pi run of the suite, Python 3.11 and 3.13, and the
surface-format factoring.

## 2026-11-07 — Publish the manual to GitHub Pages

- Added `.github/workflows/docs.yml`: builds the manual on pushes to
  `develop`, `main`, `ft/**` and `rc/**`, deploys to https://esba1ley.github.io/opengl_python_qt6_test/ from `main`. See
  `DECISIONS.md`. Updated the README's Documentation section,
  `ARCHITECTURE.md` and `CLAUDE.md`.
- GitHub cannot dispatch a workflow by hand until it is on the default
  branch, so the build also runs on `ft/**` and `rc/**` pushes. Its first run
  on the feature branch built cleanly with Ubuntu's PlantUML 1.2020.2 and
  Graphviz 2.42, all five diagrams rendered; a second run, restricted to
  conda-forge, removed the implicit `defaults` channel warning. Pages was
  already set to deploy from GitHub Actions.

**Next:** Release so `main` deploys. Done in the entry above.

## 2026-11-07 — Release v0.3.1

- Cut `rc/esbailey/v0.3.1` from `develop` and ran `bump2version patch`
  without tagging. Merged into `main`, tagged `v0.3.1`, and merged `main`
  back into `develop`.
- A documentation release: the README screenshot, the rendered face images
  and `tools/make_face_images.py`. The program is unchanged apart from the
  version.

**Next:** As in the entries below: Pi run of the suite, Python 3.11 and 3.13,
and the surface-format factoring.

## 2026-11-07 — README screenshot and material images

- Embedded `tools/ScreenGrab.png` at the top of the README, with
  `:relative-images:` on the include in `docs/index.md` so the manual resolves
  it too.
- Added `tools/make_face_images.py` and the six `docs/images/face-*.png`
  images it renders, shown in a new column of the README's material table.
  See `DECISIONS.md`. Checked by eye against the screenshot.
- `make -C docs html` clean, Ruff clean, `--check` passes; `src/` unchanged.

**Next:** The surface-format lines now exist in three places (`main.py`,
`tests/conftest.py`, `tools/make_face_images.py`); factoring them into a
`main` function is the open question from 2026-11-02.

## 2026-11-07 — Release v0.3.0

- Cut `rc/esbailey/v0.3.0` from `develop` and ran `bump2version minor`
  without tagging, as for `v0.2.0`. Merged into `main`, tagged `v0.3.0`, and
  merged `main` back into `develop`.
- The release adds the pytest suite (98 tests, 100% line and branch
  coverage) and the test-suite pages in the manual. No module in `src/`
  changed apart from the version number, so the program's platform coverage
  is as for `v0.2.0`. The suite itself has run only on macOS.

**Next:** Run the suite on the Pi under the ES 3.1 context, and under Python
3.11 and 3.13.

## 2026-11-07 — Test review: weak tests fixed, rationale in the manual

- Walked Erik through every test. Removed the config type check and the two
  shader text matches (the compile and link tests already cover them),
  dropped the `vp == p * v` restatement from `test_context.py`, replaced the
  overlay's 500-lit-pixel threshold with projected grid intersections that
  must land on lit pixels (axes and dot switched off), and made the
  double-click test change pan and light before resetting.
- Added a rationale paragraph to all 82 test function docstrings and the
  `docs/tests/` pages that render them. See `DECISIONS.md`.
- `pytest`: 98 passed, 100% line and branch coverage. Ruff clean,
  `--check` passes, `make -C docs html` clean with every test rendered.

**Next:** Unchanged from the 2026-11-02 entry: Pi run, Python 3.11 and 3.13
environments, surface-format factoring, shader log decoding.

## 2026-11-02 — pytest suite at 100% branch coverage

- Committed the plan first at `.claude/PLAN.md`, then executed it by
  subagent, one commit per task, on `ft/esbailey/pytest-suite`.
- Added `pytest.ini`, `tests/conftest.py` and one `tests/test_<module>.py`
  per module in `src/`. `pytest -W error`: 103 passed in 2.3 s, 100% line and
  branch coverage (542 statements, 56 branches).
- Added `pytest`, `pytest-cov` and `pytest-qt` to `environment.yml` and
  `apt-packages.txt`, and a Testing subsection to the README.
- Recorded the design in `ARCHITECTURE.md` (Testing) and three entries in
  `DECISIONS.md`.

**Next:** Run the suite on the Pi under the ES 3.1 context. Create Python
3.11 and 3.13 environments and run it there. Decide whether to factor the
seven surface-format lines out of `main.py` into a function shared with
`tests/conftest.py`. Make `gl_utils` decode the shader and program log
instead of raising `RuntimeError` with its bytes repr (a small `src` change).

## 2026-11-01 — Release v0.2.0

- Cut `rc/esbailey/v0.2.0` from `develop` and ran `bump2version minor`
  without tagging, since the release tag belongs on the merge commit on
  `main`, as for `v0.1.0`. Merged into `main`, tagged `v0.2.0`, and merged
  `main` back into `develop`.
- The release carries the per-platform OpenGL request with the derived GLSL
  header, the Sphinx manual with PlantUML diagrams, and the conda and apt
  environment files, all verified on macOS and Raspberry Pi OS trixie.

**Next:** Nothing queued. Bookworm and vanilla Debian remain untested.

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
