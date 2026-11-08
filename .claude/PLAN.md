# Plan: extend "How it works" from the window to the frame

## Context

The "How it works" chapter (`docs/guide/`, v0.4.0) explains how
`textures.py` and `shaders.py` build the cube's textured faces. Erik now
wants the same depth for everything that comes before and around it: the Qt
application, window, widget and event loop; the OpenGL context and shader
programs; the scene's coordinate spaces and matrices; and the geometry of
the cube, sphere grid, axes and light dot, up to the point where textures
are applied. The reader should understand every part of setting up the GUI,
the OpenGL scene and the geometry inside it.

Decisions already made by Erik (2026-11-08):
- **One guide, in order.** "How it works" grows into a single walk-through:
  new pages for the window, the context and programs, the coordinate spaces,
  the geometry and buffers, then the existing texture pages, ending with one
  frame put together.
- **Light-touch code changes.** Docs first; change code only where it fights
  the explanation, with the vertex data provably unchanged.
- **Images:** a rendered build-up of one frame, plus new geometry debug
  views in the cube shader (texture coordinates, face layer, tangent frame).
- **Notation:** Erik's frame notation in the docs (`T_world_model`, composed
  rightmost first), with Qt's quaternion convention stated against his.
  Code names stay as they are.
- Execution as before: subagents on `ft/esbailey/scene-guide` from
  `develop`, this plan committed first as `.claude/PLAN.md` (replacing the
  textures plan; git keeps it), one commit per task, stop for Erik's review
  before merging. Commit types from Erik's list only; never `feat`.

## Hard constraints

- **Texture bytes unchanged**: `generate_texture_layers()` hash prefix
  `70bf2f00d9547795` (command under Verification).
- **Vertex data unchanged**: on this Mac,
  `sha256(np.array(cube_vertices(), float64).tobytes() +
  grid_vertices().tobytes() + axis_vertices().tobytes())` starts
  `44f48b500c33c716`, before and after Task 1.
- **View 0 renders unchanged** after the shader task: `make_face_images.py`,
  `make_icon.py` and `make_control_animations.py` regenerate byte-identical
  files. If not, rework the GLSL so the final-colour expression is untouched.
- 100% line and branch coverage, Ruff clean, `--check` 6 PASS,
  `make -C docs html` clean under `-W`. Every new test has a summary line and
  a `**WHY:**` paragraph. No new dependency.
- Every factual claim about Qt is checked against the Qt 6 documentation
  (QOpenGLWidget, QSurfaceFormat, QCoreApplication::exec, QWidget::update,
  QQuaternion); the writer cites the class and section in the task report.

## Design

### Code (light touch)

- **`geometry.cube_vertices`**: replace the anonymous
  `faces = ((0, 1), (0, -1), ...)` and the `u, v = [...]` comprehension with
  a named, `#:`-documented module constant listing each face as
  `(name, axis, sign)` in `MATERIALS` order (`"+X"` … `"-Z"`), and short
  comments on the corner order and the two triangles. Output identical
  (fingerprint above). No change to `VERTEX_ATTRIBUTES`.
- **Surface format, queued since 2026-11-01**: move the seven
  platform-gated lines out of `main.main()` into
  `main.request_surface_format()`, called by `main()`,
  `tools/offscreen.request_format` (removed; the tools call the new
  function) and `tests/conftest.pytest_configure`. One copy, so the window
  page can quote one function. "Nothing else in the program tests the
  platform" stays true. Update `startup.puml` and `calls.puml`.
- **Geometry debug views** in `CUBE_FRAGMENT_BODY`, appended after view 5 in
  the existing `else if` chain, computed from inputs the shader already has:
  6 `uv` = `vec3(textureCoords, 0.0)`; 7 `layer` = `vec3(textureLayer / 5.0)`
  (six faces, layers 0 to 5); 8 `tangent`, 9 `bitangent`, 10 `face_normal` =
  the normalised world-space vector `* 0.5 + 0.5`. Extend `CUBE_VIEWS` to
  match. Update the debug-view line in `docs/diagrams/textures.puml`.

### Images (`tools/make_guide_images.py`)

- The new views are written automatically by the existing view loop as
  `view-uv.png` … `view-face-normal.png` (5 images).
- New group: the frame built up at the default view and light, 240 px from
  a 480 px render: `frame-1-cube.png`, `frame-2-grid.png`,
  `frame-3-axes.png`, `frame-4-light-dot.png`. Drawn through
  `OffscreenScene.render(paint=...)` with the real `CubeRenderer.paint` and
  `OverlayRenderer.paint`, disabling later overlay steps by overriding
  `paint_axes` / `paint_light_dot` on the instance (no change to `src/`), so
  the setup in `OverlayRenderer.paint` is not duplicated. The last image is
  the default view, as in the screenshot.
- 60 → 69 images.

### Chapter pages (`docs/guide/`)

Toctree, in reading order, with captions for three parts:

1. **The window and the scene**
   - `window.md` — `main()`: `request_surface_format` and why the default
     format must be set before `QApplication`; the application object, the
     icon, `CubeWidget` as a `QOpenGLWidget`, `show()`, `app.exec()` and
     what the event loop does. The widget's life cycle: when Qt calls
     `initializeGL`, `resizeGL` and `paintGL`, with the context current, and
     that the widget renders into a framebuffer Qt composites. Mouse events
     to `SceneContext` calls to `update()`, which schedules (and merges)
     repaints. The self-test: `QTimer.singleShot` and
     `QApplication.sendEvent`. Embeds `startup.puml` and `mouse.puml`.
   - `context.md` — the OpenGL context and shader programs: what
     `QSurfaceFormat` asks for (version, profile or ES, depth buffer, 4×
     samples) and why each; the printed renderer strings; `glsl_header`;
     `compile_shader` and `build_program`, with their error paths; uniform
     and attribute locations; `set_matrix` (row-major copy, transposed
     upload) and `set_vector`.
   - `spaces.md` — coordinate spaces and the camera, in Erik's notation:
     model, world, camera, clip, normalised device and window coordinates;
     $T_{\text{world}\leftarrow\text{model}}$ etc. written `T_world_model`,
     with `mvp = T_clip_camera · T_camera_world · T_world_model` mapped to
     `projection_matrix() * view_matrix() * model_matrix()`. The perspective
     matrix from `FOV_DEGREES`, aspect, near and far. `screen_rotation`
     (drag to axis and angle), why it pre-multiplies (rotation about world
     axes, which are screen axes because the camera does not rotate),
     renormalising, zoom clamping, pan scaling, `camera_position` as the
     inverse of the view translation, the light as a world-space direction.
     **Convention box:** Qt's `QQuaternion` is Hamilton, scalar-first and
     rotates vectors actively; the stored `rotation` takes model coordinates
     to world, i.e. `R_world_model`. State the equivalent in Erik's JPL,
     scalar-last, passive convention (expected: the conjugate, components
     reordered) only after the controller has checked it numerically.
   - `geometry.md` — the cube: the face table, each face's tangent frame,
     corners, $(u, v)$ and the two triangles; the vertex layout (moved here
     from `gpu.md`, which keeps a two-line pointer); the new views
     `uv`, `layer`, `tangent`, `bitangent`, `face_normal` with images. The
     sphere grid: `sphere_points`, meridians and parallels, `CURVE_STEP_DEGREES`,
     `curve_to_segments` for `GL_LINES`, `with_color`; the axes; the light
     dot as one point.
   - `buffers.md` — from arrays to vertex buffers: VAO, VBO,
     `glBufferData`, `glVertexAttribPointer` with stride and offsets, the
     cube's six attributes against the overlay's two, and the overlay's one
     buffer split into grid, axes and dot ranges by `glDrawArrays` first and
     count.
2. **Textures and shaders** — the existing `primitives`, `materials`,
   `gpu`, `shaders` pages, with links into the new pages where they now
   assume them (vertex layout, uniforms, spaces).
3. **A frame**
   - `frame.md` — one `paintGL`: depth test and clear, the cube draw, the
     overlay's blend function (why alpha is kept), the grid without depth
     writes, the clamped axis width, the light dot's two passes; draw order
     and what breaks if it changes. Embeds `frame.puml` and the four
     build-up images. Ends by linking to "One pixel, start to finish".
- `index.md` is rewritten to cover the whole path (window → context → spaces
  → geometry → buffers → textures → shaders → frame), with the stage table
  extended; `textures.puml` stays as the textures part's diagram.
- Code is quoted with `literalinclude` (`:pyobject:` for functions and
  methods), maths with `dollarmath`, as before.

## Tasks (one commit each, on `ft/esbailey/scene-guide` from `develop`)

0. `docs(plan): add the scene guide plan` — this file as `.claude/PLAN.md`.
1. `refactor(geometry): name the cube's faces` — the face table and
   comments; tests unchanged or extended; controller checks the vertex
   fingerprint. Model: sonnet.
2. `refactor(main): factor the surface-format request into one function` —
   `main.request_surface_format`, callers in `offscreen.py` and
   `conftest.py`, `test_main.py` coverage, `startup.puml`, `calls.puml`,
   README and ARCHITECTURE wording that names where the request lives.
   Model: sonnet.
3. `refactor(shaders): add geometry debug views to the cube shader` — five
   views, `CUBE_VIEWS`, `textures.puml`; tests: a parametrised test with the
   identity rotation so +Z faces the camera, checking the centre pixel of
   each new view against its expected colour (uv ≈ (0.5, 0.5, 0), layer
   0.8 grey, tangent ≈ (1, 0.5, 0.5), bitangent ≈ (0.5, 1, 0.5), face normal
   ≈ (0.5, 0.5, 1)). Controller reruns the three image tools for byte
   identity. Model: sonnet.
4. `build(tools): render the frame build-up and geometry view images` —
   tool and 9 new images, checked by contact sheet. Model: sonnet.
5. `docs(guide): explain the window, the context and the shader programs` —
   `window.md`, `context.md`, toctree with part captions. Model: opus.
6. `docs(guide): explain the coordinate spaces, the geometry and the vertex
   buffers` — `spaces.md`, `geometry.md`, `buffers.md`, the `gpu.md`
   pointer. Controller checks the quaternion statement numerically before
   review. Model: opus.
7. `docs(guide): explain one frame and tie the guide together` — `frame.md`,
   the rewritten `index.md`, cross-links from the existing four pages.
   Model: opus.
8. `docs(project): describe the extended guide` — README (chapter
   description, image count), `src/README.md`, `CLAUDE.md` (view-0 rule now
   covers 11 views; guide image list), `ARCHITECTURE.md` (Teaching guide
   pages and images; OpenGL context selection names
   `request_surface_format`), `DECISIONS.md` (extend the guide; light-touch
   code; geometry views; the build-up drawn through the real renderers),
   `JOURNAL.md`. Model: sonnet.

Each task gets a task review; a final whole-branch review on opus; one fix
wave if needed.

## Verification

```
python3 -c "import sys,hashlib; sys.path.insert(0,'src'); import textures; \
a,n,l=textures.generate_texture_layers(); print(hashlib.sha256(a+n).hexdigest()[:16])"
# 70bf2f00d9547795
python3 -c "import sys,hashlib,numpy as np; sys.path.insert(0,'src'); import geometry as g; \
print(hashlib.sha256(np.array(g.cube_vertices(),np.float64).tobytes()+g.grid_vertices().tobytes()+g.axis_vertices().tobytes()).hexdigest()[:16])"
# 44f48b500c33c716
pytest -W error                          # 100% line and branch
ruff check src tools docs/conf.py tests
python3 src/main.py --check              # 6 PASS
python3 tools/make_face_images.py docs/images        # no git diff
python3 tools/make_icon.py icon.png docs/images/screenshot.png   # no git diff
python3 tools/make_control_animations.py docs/images # no git diff
python3 tools/make_guide_images.py docs/images/guide # only the 9 new files
make -C docs html                        # clean, every image present
```

Look at the new images and the built pages by eye before stopping.

## Stop condition

All tasks committed and reviewed, every verification line passing. Do not
merge, push or delete. Report to Erik: commits, the two hashes and the
byte-identity results, image count, the page list, every ruling made, and
the open question of re-running `pytest` and `--check` on the Pi for the
new views under OpenGL ES.
