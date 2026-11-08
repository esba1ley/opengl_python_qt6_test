# Plan: a "How the textures and shaders work" chapter, with `textures.py` restructured to teach

## Context

Erik wants the manual to explain, step by step, how every part of
`src/textures.py` and `src/shaders.py` builds the cube's textured faces, with
images of each step. He judged (2026-11-07) that the repository's purpose is
to teach how procedural textures and shaders work in OpenGL, so the code
itself should be restructured to read as a lesson, not merely documented.

Decisions already made by Erik:
- Restructure `textures.py` into shared, documented pattern functions, with
  every material recording its named intermediate steps.
- Show the cube fragment shader's stages both as rendered images (through a
  debug `view` uniform in the real shader) and as equations and prose.
- Restate the repository's purpose as teaching in the README and `CLAUDE.md`.
- Execute with subagents on a feature branch; this plan is the first commit
  as `.claude/PLAN.md` (replacing the pytest plan; git keeps it); one commit
  per task; stop for Erik's review before merging.

## Hard constraints

- **Texture bytes are unchanged.** On this Mac (NumPy 2.3.5),
  `hashlib.sha256(albedo + normals).hexdigest()` of
  `textures.generate_texture_layers()` starts `70bf2f00d9547795` and must
  still do so after every textures task. Verified by the controller after each
  task. It is not made a permanent test: NumPy's `sin`/`hypot` may differ by
  platform and build, so a golden hash would fail on the Pi for no fault.
- **View 0 renders unchanged.** `tools/make_face_images.py`,
  `tools/make_icon.py` and `tools/make_control_animations.py` regenerate
  byte-identical files on this Mac after the shader change. If not, the GLSL
  is reworked so the final colour expression is untouched (FMA contraction
  can change with surrounding code) before anything else happens.
- **Random draw order and shapes are preserved**: bricks draws fractal noise,
  then `random((8, 6))` (keep `columns + 2`); cobbles draws `(40, 2)` points,
  then fractal noise, then `random(40)`; rivets `random((size, 1))`, then
  fractal noise; wood `random(5)`, then fractal noise. Recording a step never
  moves a draw.
- 100% line and branch coverage (`pytest.ini`), Ruff clean, `--check` passes,
  `make -C docs html` clean with `-W`. Every new test has a summary line and a
  `**WHY:**` paragraph. No new dependency beyond the existing set (Pillow
  stays tools-only).

## Design

### `textures.py`
- Six shared patterns, each a public, NumPy-docstring'd function used by at
  least one material without distortion:
  - `seam(f)`: `np.minimum(f, 1 - f)`, the 1-D distance to the nearest cell
    edge (bricks, tiles, wood).
  - `cell_lattice(u, v, columns, rows, stagger=0.0)` returns
    `(column, row, fx, fy)`, with odd rows shifted by `stagger` (bricks 8×4
    with stagger 0.5; tiles 4×4; rivets 5×5, centred via `fx - 0.5`; weave
    10×10). Compute `v * rows` once and reuse it for `floor` and the fraction.
  - `edge_distance(fx, fy, columns, rows)`:
    `np.minimum(seam(fx) / columns, seam(fy) / rows)` (bricks, tiles; exact
    for the tiles form too, since division by a positive constant keeps order).
  - `checker(column, row)` returns float parity (tiles; weave compares `== 0`
    at the call site). Keep it float so `mix` does not cast a bool.
  - `voronoi(u, v, points)` returns `(nearest, gap)`, casting the distance
    volume to `float32` exactly where cobbles does now and returning `gap` as
    float32. No `asarray(float)`, no squared distances.
  - `dome(fx, fy, radius)`, the rivet hemisphere.
- Wood stays a 1-D lattice inline (`plank = floor(u * 5)`, `x = u * 5 - plank`)
  using `seam(x)`; weave keeps `across`/`along` inline, since they are the
  lesson.
- Each material returns `Material(color, height, steps)`, a `NamedTuple` whose
  `steps` is an ordered dict from a readable step name to a 2-D field or RGB
  image, filled as the material builds. Never record the `(size, size, 40)`
  distance volume, and never update a recorded array in place (rivets'
  `brushed` is reassigned, not mutated).
- `iter_materials(size, seed=config.TEXTURE_SEED)` yields
  `(function, Material)` in `MATERIALS` order on one shared generator, so the
  docs tool sees exactly the real layers. `generate_texture_layers()` consumes
  it and keeps only colour and height, so steps (about 150 MB at 512 px) are
  never all held at once.
- Expression text that sets bits stays verbatim: `mix` as
  `a*(1-t) + b*t`, weights such as `shade*0.6 + noise*0.4`, the order of terms
  in each sum.

### `shaders.py`, `config.py`, `context.py`, `cube.py`
- `CUBE_FRAGMENT_BODY`: compute every term as now, assign the current final
  expression to `vec3 result`, then
  `if (view == 1) result = albedo; else if (view == 2) result = n * 0.5 + 0.5;`
  and so on for diffuse, facing and specular (as grey); `fragColor =
  vec4(result, 1.0)`. `uniform int view` needs no header change (GLSL ES 3.00
  fragment shaders default `int` to mediump).
- `#: CUBE_VIEWS` in `shaders.py`: the names in index order
  (`"final", "albedo", "normal", "diffuse", "facing", "specular"`).
- `#: DEFAULT_CUBE_VIEW = 0` in `config.py`; `SceneContext.__init__` sets
  `self.cube_view` from it (not `reset_view`, so a double-click keeps it);
  `CubeRenderer` looks up `view_loc` and `paint` sets it from `ctx.cube_view`,
  which keeps the rule that renderers read only `SceneContext`.
- Update `docs/diagrams/frame.puml`, `calls.puml` and `classes.puml` for the
  new uniform and the new texture functions.

### Images: `tools/make_guide_images.py`
- Uses `tools/offscreen.py` and Qt to write PNGs to `docs/images/guide/`:
  - primitives: one octave of value noise, the five-octave sum, a smoothstep
    ramp, a `mix` of two colours by a mask;
  - for each material, every recorded step, then its normal map
    (`height_to_normals`), taken from `iter_materials` at 512 px and scaled to
    160 px; fields drawn as greyscale, normals as RGB;
  - the cube at the default view through each `CUBE_VIEWS` entry, 240 px.
- Copies arrays before normalising for display. Expect roughly 50 images and
  about 1 MB; regenerate only when a material or the shader changes.

### Documentation chapter
- A "How it works" toctree in `docs/` with pages:
  `guide/index` (purpose, the pipeline end to end, a new PlantUML activity
  diagram `docs/diagrams/textures.puml`), `guide/primitives` (`uv_grid`,
  `smoothstep`, `mix`, `value_noise`, `fractal_noise`, the six patterns),
  `guide/materials` (one section per material: idea, steps with maths, quoted
  code, image row), `guide/gpu` (randomness and draw order, height to
  normals, packing, the texture array, mipmaps and filters), `guide/shaders`
  (both cube shaders line by line with the stage images, both overlay
  shaders, one pixel traced from texture coordinate to colour).
- Code is quoted with `literalinclude` from `src/` (`:pyobject:` for
  functions; `:start-after:`/`:end-before:` the `#:` comments for shader
  strings), so a rename fails the build instead of showing stale code.
- Maths with MyST `dollarmath` (`myst_enable_extensions` in `docs/conf.py`);
  rendered by MathJax, which loads from a CDN when the page is viewed.

## Tasks (one commit each, on `ft/esbailey/textures-guide` from `develop`)

0. `docs(plan): add the textures and shaders guide plan` — this file as
   `.claude/PLAN.md`.
1. `refactor(textures): add shared pattern functions` — the six patterns with
   unit tests (each branch, dtype of `voronoi`'s gap, float `checker`); no
   callers yet. Model: sonnet.
2. `refactor(textures): build the materials from the shared patterns` —
   tiles, weave, rivets, bricks, then wood (`seam` only), then cobbles;
   controller checks the hash after the commit. Model: sonnet; escalate to
   opus if the hash moves.
3. `refactor(textures): record each material's steps` — `Material`,
   `iter_materials`, slimmer `generate_texture_layers`; tests for step names,
   shapes, ranges, and that `iter_materials` matches
   `generate_texture_layers`. Hash checked again. Model: sonnet.
4. `refactor(shaders): add a debug view to the cube fragment shader` —
   shader, `CUBE_VIEWS`, config, context, cube, the three diagrams, tests
   (`view_loc` found; every view renders and differs from view 0; each index
   appears as `view == i`). Controller reruns the three image tools and
   compares bytes. Model: sonnet.
5. `build(tools): render the guide's step and shader images` — the tool and
   its images, checked by contact sheet. Model: sonnet.
6. `docs(guide): explain how the textures and shaders work` — conf.py,
   diagram, five pages, toctree. Model: opus (the writing is the product).
7. `docs(project): restate the repository as a teaching example` — README
   intro and a pointer to the chapter, `src/README.md` (material recipe,
   `Material` contract, patterns), `CLAUDE.md` (purpose, the steps and view
   rules, regeneration rule for guide images), `ARCHITECTURE.md` (new
   Teaching guide section; Module layout and Documentation updates; Frozen
   changes covered by the decision), `DECISIONS.md` (purpose; refactor for
   teaching; debug view in the real shader; images from replayed materials),
   `JOURNAL.md`. Model: sonnet.

Each task gets a task review; a final whole-branch review on opus; one fix
wave if needed.

## Verification

```
python3 -c "import sys,hashlib; sys.path.insert(0,'src'); import textures; \
a,n,l=textures.generate_texture_layers(); print(hashlib.sha256(a+n).hexdigest()[:16])"
# must print 70bf2f00d9547795
pytest                                   # 100% line and branch
ruff check src tools docs/conf.py tests
python3 src/main.py --check              # 6 PASS
python3 tools/make_face_images.py docs/images        # no git diff
python3 tools/make_icon.py icon.png docs/images/screenshot.png   # no git diff
python3 tools/make_control_animations.py docs/images # no git diff
make -C docs html                        # clean, every guide image present
```

Look at the guide images and the built chapter by eye before stopping.

## Stop condition

All tasks committed and reviewed, every verification line passing. Do not
merge, push or delete. Report to Erik: the commit list, the hash and
byte-identity results, image count and size, the chapter's page list, rulings
made, and these open questions: whether to run the suite and `--check` on the
Pi (the view-0 identity under GLES and GL 3.1 is unverified there), and
whether the guide images should also appear in the README.
