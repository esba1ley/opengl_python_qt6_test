# Plan: pytest unit test suite for `src/` at 100% line and branch coverage

## Context

The program has one end-to-end check, `python3 src/main.py --check`, which only
confirms that frames change after each interaction. Nothing tests the modules
individually, so a regression in geometry, textures, the scene mathematics or
the mouse handling is caught only by looking at a frame. This plan adds a
pytest suite covering every module in `src/` to 100% line and branch coverage,
on a new feature branch whose first commit is this plan at `.claude/PLAN.md`.
Subagents execute the tasks, one commit per task, nothing pushed. Work stops
for Erik's review when `pytest` reports 100% with `--cov-branch`.

Decisions already made by Erik (2026-11-02): line and branch coverage; real
offscreen OpenGL context with stubs only for branches this machine cannot
reach; one commit per task; the Python 3.11/3.13 matrix is a later task.

## Verified facts the design rests on

All verified by running on the Mac (PyQt6 6.9.1, PyOpenGL 3.1.10, pytest 9.0.2,
pytest-qt 4.5.0, pytest-cov 7.0.0):

- `QOpenGLContext.create()` + `QOffscreenSurface` gives a 4.1 core context in
  which PyOpenGL works and `glGenVertexArrays` succeeds. A
  `QOpenGLFramebufferObject` (from `PyQt6.QtOpenGL`, not `QtGui`) with a depth
  attachment binds and reads back with `toImage()`. Both renderers initialize
  and paint into it with no GL error, and `selftest.light_dot_is_yellow`
  returns True on the result.
- Setting the default `QSurfaceFormat` after the QApplication exists but
  before `CubeWidget()` still yields a 4.1 core widget, because
  `CubeWidget.__init__` copies `defaultFormat()`. pytest-qt's
  `pytest_configure` creates no QApplication, so conftest can set the format
  there.
- A shown `CubeWidget` under a QApplication returns a correct
  `grabFramebuffer()` after `waitExposed`, with no event loop running.
- `selftest.check(widget)` runs to completion on that widget with
  `selftest.QApplication.exit` monkeypatched to record the code (sip classes
  accept the setattr).
- `setattr(PyQt6.QtWidgets, "QApplication", Fake)` is allowed and a later
  `from PyQt6.QtWidgets import QApplication` sees the fake, so
  `runpy.run_path(".../src/main.py", run_name="__main__")` covers
  `main.py:80-81` with `SystemExit`. pytest-qt's `pytest_runtest_call` calls
  `QApplication.instance()` after the test body and before monkeypatch undo,
  so that patch must live inside `with monkeypatch.context()` and the fake
  must expose `instance = staticmethod(QApplication.instance)`.
- Link failure that is a spec-mandated error everywhere (Apple and Mesa):
  vertex `out vec3 v;` against fragment `in vec4 v;`. Compile failure: any
  garbage body. A vertex shader without `gl_Position` links fine; do not use.
- `textures.mix` line 51: the False arm (both inputs 2-D) is never reached by
  the program; it needs a direct `mix(field, field, t)` test.
- Timing: `generate_texture_layers()` at 512 takes 0.30 s; one renderer
  initialize 0.31 s; materials at size 32 take milliseconds. Whole suite
  expected under 5 s.
- Debian has python3-pytest 7.2.1/8.3.5, python3-pytest-cov 4.0.0/5.0.0,
  python3-pytestqt 4.2.0/4.4.0 (bookworm/trixie); conda-forge has all three.

## Branch and commit workflow

1. `git checkout -b ft/esbailey/pytest-suite develop` (no issue exists; Erik
   may want to file one and rename later).
2. Copy this plan to `.claude/PLAN.md` and commit:
   `docs(plan): add the pytest suite plan` — the first commit on the branch.
3. Each task below ends in one commit on the branch, `test(...)`, `build(...)`
   or `docs(...)` per the repository's commit style, with the co-author
   trailer. Nothing is pushed.
4. Execution uses `superpowers:subagent-driven-development`: one subagent per
   task, in the order below, each told the files it owns and the acceptance
   command. Tasks 2 to 6 are independent once task 1 has landed and may run in
   parallel if their files do not overlap (they do not).
5. After task 7, run the full acceptance command. If coverage is below 100%,
   dispatch a fix-up subagent with the `term-missing` report. When it reads
   100%, stop and report to Erik for review. Do not merge, push or delete
   anything.

## Layout and configuration

- `tests/` at the repository root, flat, one `test_<module>.py` per `src/`
  module plus `conftest.py`.
- `pytest.ini` (single standalone file, matching `ruff.toml` and
  `.bumpversion.cfg`):
  ```
  [pytest]
  testpaths = tests
  qt_api = pyqt6
  addopts = --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=100
  ```
  No `.coveragerc`: nothing is excluded, the `__main__` guard included.
- `tests/conftest.py`:
  - `pytest_configure(config)`: insert `<repo>/src` on `sys.path` (the same
    pattern as `docs/conf.py:11`), then set the default `QSurfaceFormat`
    exactly as `main.py:59-70` does (4.1 core on darwin, OpenGL ES 3.1 else).
    Those seven lines are duplicated from `main.py` on purpose; this plan does
    not change `src/`. A follow-up may factor them into a `main` function.
  - session fixture `gl_context`: `QOpenGLContext` + `QOffscreenSurface`,
    `makeCurrent`; yields the context; `doneCurrent` at teardown.
  - function fixture `fbo(gl_context)`: 256×256
    `QOpenGLFramebufferObject` with `Attachment.Depth`, bound, viewport set,
    cleared; yields it; `release()` at teardown.
  - helper `image_to_array(QImage) -> ndarray` (reuse the idea from
    `tools/make_icon.py:24` but keep tests self-contained; do not import
    `tools`).
  - function fixture `scene`: a fresh `SceneContext()` with
    `aspect_ratio = 1.0`.
  - autouse fixture `restore_default_format`: saves
    `QSurfaceFormat.defaultFormat()` and restores it after each test (the
    `main.main()` linux arm sets ES 3.1 and would break later widget tests).
- `.gitignore`: add `.coverage`, `.pytest_cache/`, `htmlcov/`.

## Tasks

### Task 1 — scaffold and dependencies (`build(test)`)
Files: `pytest.ini`, `tests/conftest.py`, `tests/__init__.py` (empty, so
pytest's rootdir import mode is unambiguous), `.gitignore`, `environment.yml`
(Development: `pytest>=7.2`, `pytest-cov>=4.0`, `pytest-qt>=4.2`),
`apt-packages.txt` (Development: `python3-pytest`, `python3-pytest-cov`,
`python3-pytestqt`), `README.md` (one "Testing" subsection: the `pytest`
command, that it needs a display like `--check`, and the dependency note).
Also one smoke test `tests/test_conftest.py` that asserts the `gl_context` is
valid and current and the `fbo` reads back as all background colour.
Acceptance: `pytest tests/test_conftest.py --no-cov` passes;
`ruff check src tools docs/conf.py tests` clean; `make -C docs html` clean
(README changed).

### Task 2 — pure modules (`test(pure)`)
Files: `tests/test_config.py`, `tests/test_shaders.py`,
`tests/test_geometry.py`, `tests/test_context.py`, `tests/test_textures.py`.
- config: constants have the expected types; `DEFAULT_LIGHT` is unit length;
  `MIN_DISTANCE < DEFAULT_DISTANCE < MAX_DISTANCE`.
- shaders: the four bodies contain no `#version`, each has `main(`, the
  vertex bodies write `gl_Position`, both fragment bodies declare the out
  variable the program expects.
- geometry: `cube_vertices()` is 36 × `FLOATS_PER_VERTEX`; six layer indices;
  `sphere_points` at poles and equator; `curve_to_segments` doubles interior
  points; `with_color` shapes and broadcasting; `grid_vertices` and
  `axis_vertices` counts and that every point lies on the sphere / axis.
- context: `screen_rotation` zero-delta identity branch (`context.py:25`) and
  non-zero; `reset_view` defaults; `rotate_by`, `move_light_by` keep the
  light unit length; `pan_by` with `viewport_height` 0 (the `max(...,1)`
  clamp); `zoom_by` clamps at both `MIN_DISTANCE` and `MAX_DISTANCE`;
  `model/view/projection/view_projection` consistency (`vp == p * v`);
  `camera_position` distance equals `distance`; `light_dot_position` length
  equals `SPHERE_RADIUS`.
- textures: `smoothstep` endpoints and clamping; `mix` with all four shape
  combinations including 2-D/2-D (`textures.py:51` False arm); `uv_grid`
  range; `value_noise` and `fractal_noise` in [0, 1] at size 32 with a seeded
  rng; every material in `MATERIALS` at size 32 returns colour `(32,32,3)` in
  [0,1] and height `(32,32)`; `height_to_normals` of a flat field is
  `(0.5,0.5,1.0)` everywhere; `to_rgba_bytes` length and dtype;
  `generate_texture_layers()` with `config.TEXTURE_SIZE` monkeypatched to 32
  returns two byte buffers of `32*32*4*len(MATERIALS)` bytes.
Acceptance: these files pass; `pytest --cov=src --cov-branch
--cov-report=term-missing --cov-fail-under=0` shows 100% for `config`,
`shaders`, `geometry`, `context`, `textures`.

### Task 3 — `gl_utils` (`test(gl_utils)`)
File: `tests/test_gl_utils.py`, using `gl_context`.
- `glsl_header()` with `gl_utils.QOpenGLContext` monkeypatched to a stub
  (`currentContext()` → object with `format().majorVersion()`,
  `format().minorVersion()`, `isOpenGLES()`): ES (3,0) → `#version 300 es`
  plus both precision lines, ES (3,1) → `310 es`, ES (2,0) → `300 es`;
  desktop (4,1) → `410`, (3,3) → `330`, (3,2) → `150`, (3,1) → `140`,
  (2,1) → `140`. Also the real context: header starts with `#version` and
  matches the context's version.
- `compile_shader` success on the overlay vertex body with the real header;
  failure on garbage raises `RuntimeError` containing the log.
- `build_program` success on the overlay pair and on the cube pair; link
  failure with the `out vec3 v` / `in vec4 v` pair raises `RuntimeError`.
- `set_matrix`: upload a known `QMatrix4x4`, read back with
  `glGetUniformfv`, compare column-major; `set_vector` likewise with
  `glGetUniformfv`.
- `upload_texture_array`: size 4, two layers, then `glGetTexLevelParameteriv`
  width/height/depth and no GL error.
Acceptance: 100% for `gl_utils`.

### Task 4 — renderers (`test(renderers)`)
Files: `tests/test_cube.py`, `tests/test_overlay.py`, using `gl_context`,
`fbo`, `scene`.
- cube: `initialize()` then `paint(scene)`; the image has non-background
  pixels near the centre; uniform locations are all ≥ 0; a second `paint`
  after `scene.rotate_by` differs from the first.
- overlay: `initialize()` then `paint(scene)`; `axis_width <=
  config.AXIS_LINE_WIDTH`; light dot pixel is yellow per
  `selftest.light_dot_is_yellow` on an object with `.ctx = scene`; grid lines
  present. Both arms of `overlay.py:69`, deterministic on either platform:
  one test patches `overlay.QOpenGLContext` to report ES and asserts
  `GL.glEnable` was not called with `GL_PROGRAM_POINT_SIZE` (record calls by
  monkeypatching `overlay.GL.glEnable` with a wrapper that forwards other
  enums); the other patches it to report desktop and asserts it was called,
  with the wrapper swallowing `GL_PROGRAM_POINT_SIZE` so the test also runs
  under an ES context on the Pi. Both `paint_light_dot` arms
  (`overlay.py:158-161`) fall out of one `paint`.
Acceptance: 100% for `cube` and `overlay`.

### Task 5 — widget and selftest (`test(widget)`)
Files: `tests/test_widget.py`, `tests/test_selftest.py`, using `qtbot`.
- widget, unshown instance: `__init__` sets title, size, `ctx`, renderers;
  `resizeGL(640, 0)` gives `aspect_ratio 640.0` (height clamp) and
  `resizeGL(400, 200)` gives 2.0; hand-built `QMouseEvent`/`QWheelEvent`
  (constructor forms as in `selftest.py:31-33, 45-56`) drive
  `mousePressEvent` (sets `last_pos`), `mouseMoveEvent` with Left (rotation
  changes), Right (light changes), Middle (pan changes) and NoButton (nothing
  changes, `update()` still called — spy with `monkeypatch`), precedence Left
  over Right; `wheelEvent` with ±120 changes `distance`;
  `mouseDoubleClickEvent` restores defaults. Do not assert a specific
  `pixel_ratio`.
- widget, shown: `qtbot.addWidget(w)`, `w.show()`, `qtbot.waitExposed(w)`,
  `w.grabFramebuffer()` is 640×640-ish (compare to `w.size() *
  devicePixelRatio`), `initializeGL` printed three lines (`capsys`), light
  dot yellow.
- selftest: real `check(widget)` on the shown widget with
  `selftest.QApplication.exit` monkeypatched to record; assert code 0 and the
  six `PASS` lines via `capsys`. FAIL path: a stub widget with `.ctx`,
  `width()/height()`, `grabFramebuffer()` returning one constant `QImage`
  filled black, and `QApplication.sendEvent` tolerated (stub is a `QObject`
  subclass so `sendEvent` works); assert exit code 1 and `FAIL` lines.
  `send_drag`/`send_wheel` are covered by `check`; add one direct test each
  asserting the events reach a recording `QObject`.
Acceptance: 100% for `widget` and `selftest`.

### Task 6 — main (`test(main)`)
File: `tests/test_main.py`.
- `main.main()` with `main.QApplication` replaced by a fake class (records
  `setWindowIcon`, `exec()` returns 7, `instance` static), `main.CubeWidget`
  by a stub with `show()`, `main.QTimer.singleShot` recorded; `sys.argv`
  monkeypatched. Four runs: darwin without `--check` (default format is 4.1
  core, no timer), darwin with `--check` (timer registered with 1000 ms;
  call the recorded callable and assert it invoked a monkeypatched
  `main.selftest.check` with the widget), non-darwin (`main.sys.platform =
  "linux"`; default format renderable type is OpenGLES, version 3.1).
  Returns 7 each time. `restore_default_format` autouse fixture handles
  cleanup.
- `__main__` guard: inside `with monkeypatch.context() as m:` patch
  `PyQt6.QtWidgets.QApplication` with the fake (with `instance`),
  `sys.modules["widget"].CubeWidget` with the stub, `sys.argv`; then
  `runpy.run_path(str(repo/"src"/"main.py"), run_name="__main__")` inside
  `pytest.raises(SystemExit) as e`; `e.value.code == 7`.
- `__version__` matches `.bumpversion.cfg`'s `current_version` (read the
  file with `configparser`), so a bump cannot drift.
Acceptance: 100% for `main`; the full suite now reports 100% overall.

### Task 7 — project documentation (`docs(testing)`)
Files: `.claude/CLAUDE.md` (Commands: `pytest`; conventions: new code needs
tests keeping 100% branch coverage, `pytest.ini` owns the thresholds, tests
need a display, GL tests use the `gl_context`/`fbo` fixtures),
`.claude/ARCHITECTURE.md` (new "Testing" section, Frozen),
`.claude/DECISIONS.md` (entry: real offscreen context over mocked GL, with
the alternatives rejected; entry: 100% branch coverage as the gate; entry:
`pytest.ini` over `pyproject.toml`), `.claude/JOURNAL.md` (session entry
dated 2026-11-02, Next: Python 3.11/3.13 matrix, Pi run of the suite),
`src/README.md` only if it describes how to verify changes (check; add one
line pointing at `tests/` if so). Keep `.claude/` out of Sphinx.
Acceptance: `make -C docs html` clean.

## Verification (end-to-end)

From the repository root inside the `esb312` or `opengl_qt6_test` env:

```
pytest                                   # must print TOTAL 100% and exit 0
ruff check src tools docs/conf.py tests  # clean
python3 src/main.py --check              # still passes
make -C docs html                        # clean
git log --oneline develop..HEAD          # plan commit first, one per task
```

Stop condition: `pytest` exits 0 with `--cov-fail-under=100` on this Mac.
Report the coverage table, suite duration, the commit list, and these review
questions: whether to factor the surface-format lines out of `main.py` into a
function shared with `conftest.py`; whether to file an issue for the branch
name; and when to run the suite on the Pi under the ES context (the
`overlay.py:69` tests are written to pass there, `glsl_header` stubs are
platform-free, but nothing in this plan is executed on the Pi).
