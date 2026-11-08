# Source Overview

The modules in this directory are plain Python files, not an installed package.
Running `python3 src/main.py` puts this directory on the import path, so modules
import each other by name, such as `import config`.

## The shared context

`SceneContext` in `context.py` is the single place that describes the scene. The
rest of the program works through it:

- **`widget.py` writes to it.** Mouse handlers call methods such as
  `ctx.rotate_by(delta)`, and do no scene calculations themselves.
- **The renderers read from it.** Each one receives it in `paint(ctx)`, so the
  renderers never touch the widget or each other.
- **`selftest.py` reads from it.** It uses the same matrices as the renderers to
  work out where the light dot should appear.

```
mouse input ──> CubeWidget ──> SceneContext ──> CubeRenderer
                                            └─> OverlayRenderer
```

The cube, sphere and axes stay anchored to each other because they all use
`ctx.model_matrix()`.

### What it holds

| Attribute | Meaning |
|---|---|
| `rotation` | Orientation of the cube, sphere and axes |
| `distance` | Distance from the camera to the origin |
| `pan` | Sideways and vertical camera offset |
| `light` | Unit vector towards the light, in world space |
| `aspect_ratio` | Viewport width divided by height |
| `pixel_ratio` | Device pixels per logical pixel |
| `cube_view` | Which shading stage the cube shader shows (index into `shaders.CUBE_VIEWS`) |

### What it provides

| Purpose | Methods |
|---|---|
| Change the scene | `rotate_by`, `move_light_by`, `pan_by`, `zoom_by`, `reset_view` |
| Read matrices | `model_matrix`, `view_matrix`, `projection_matrix`, `view_projection_matrix` |
| Read positions | `camera_position`, `light_dot_position` |

Runtime state belongs in `SceneContext`. Fixed settings belong in `config.py`.
OpenGL objects, such as buffers and programs, belong to the renderer that uses
them.

## Modules

| Module | Scope | OpenGL context needed? |
|---|---|---|
| `main.py` | Starts the Qt application and handles `--check` | No |
| `context.py` | `SceneContext`, the shared state and its matrices | No |
| `widget.py` | `CubeWidget`, which handles mouse input and paints frames | Yes |
| `cube.py` | `CubeRenderer`, which draws the textured cube | Yes |
| `overlay.py` | `OverlayRenderer`, which draws the sphere grid, axes and light dot | Yes |
| `geometry.py` | Vertex data for the cube, sphere grid and axes | No |
| `textures.py` | Shared patterns, procedural materials that record their steps, and normal maps, using only NumPy | No |
| `shaders.py` | GLSL source for both renderers, including the cube's debug views | No |
| `gl_utils.py` | Helpers for shaders, uniforms and textures | Yes |
| `config.py` | Settings shared by the other modules | No |
| `selftest.py` | Simulated mouse input and the `--check` tests | Yes |

## Dependencies between modules

Each module imports only the modules listed on its row:

| Module | Imports |
|---|---|
| `main.py` | `selftest`, `widget` |
| `widget.py` | `config`, `context`, `cube`, `overlay` |
| `cube.py` | `config`, `geometry`, `gl_utils`, `shaders`, `textures` |
| `overlay.py` | `config`, `geometry`, `gl_utils`, `shaders` |
| `context.py` | `config` |
| `geometry.py` | `config` |
| `textures.py` | `config` |
| `gl_utils.py`, `shaders.py`, `selftest.py`, `config.py` | None |

The renderers accept a `SceneContext` as an argument without importing
`context.py`, and `selftest.py` reaches it through `widget.ctx`.

## Frame order

`CubeWidget.paintGL` clears the frame and then draws in this order:

1. **Cube:** `CubeRenderer.paint` draws the solid cube and writes depth.
2. **Sphere grid:** `OverlayRenderer.paint_grid` draws translucent lines without
   writing depth, so the lines don't cut gaps in what comes next.
3. **Axes:** `OverlayRenderer.paint_axes` uses depth testing, so the cube hides
   the parts inside it.
4. **Light dot:** `OverlayRenderer.paint_light_dot` draws a faint pass without
   depth testing, then a solid pass with it.

## Common changes

| To do this | Change this |
|---|---|
| Adjust colours, opacity, spacing or sensitivity | `config.py` |
| Add or replace a material | Follow the recipe below |
| Look at one stage of the cube's shading | Set `ctx.cube_view` or `config.DEFAULT_CUBE_VIEW` to an index into `shaders.CUBE_VIEWS` |
| Add a new mouse control | Add a method to `SceneContext`, then call it from `widget.py` |
| Draw something new | Add a renderer, then call it from `CubeWidget.paintGL` |
| Add a self-test check | Extend `check` in `selftest.py` |
| Add a unit test | Add to `tests/test_<module>.py`, with a docstring saying what it checks and why; `pytest` fails below 100% coverage |

## Textures

`textures.py` is written to be read. Its pieces, in file order:

- **Primitives:** `smoothstep`, `mix`, `uv_grid`, `value_noise` and
  `fractal_noise`.
- **Shared patterns:** `seam`, `cell_lattice`, `edge_distance`, `checker`,
  `voronoi` and `dome`. Materials combine these rather than repeating the
  geometry.
- **Materials:** `bricks`, `cobbles`, `tiles`, `wood`, `rivets` and `weave`,
  collected in `MATERIALS`.
- **Packing:** `height_to_normals` and `to_rgba_bytes`.
- **Drivers:** `iter_materials` and `generate_texture_layers`.

A material function takes `(size, rng)` and returns a `Material`, a named
tuple of `color`, `height` and `steps`. `color` is a float RGB image and
`height` a height map, both with values from 0 to 1. `steps` is an ordered
dict from a readable step name to the 2D field or RGB image at that point in
the build; the last two entries are `"colour"` and `"height"`. Nothing
recorded in `steps` is changed afterwards.

To add a material:

1. Write `def name(size, rng)` that builds the material from the patterns,
   records each intermediate array in a `steps` dict, and returns
   `Material(color, height, steps)`.
2. Append it to `MATERIALS`.
3. Add a face layer: `MATERIALS` needs one entry per cube face, in the order
   used by `cube_vertices` in `geometry.py`, so the geometry and the texture
   array's layer count must change together.
4. Add tests, and rerun `tools/make_guide_images.py docs/images/guide`.

All the materials share one random generator, in `MATERIALS` order, so each
draws from where the previous one stopped. Adding a material in the middle, or
changing how many numbers one draws, changes every material after it.
`iter_materials(size, seed=None)` replays them in that order and yields each
`Material`; `generate_texture_layers` uses it and keeps only the colour and
height, so the steps of all materials are never held at once. The documentation
tool uses the same function, so its images show exactly the layers the program
draws.

## Shader views

`CUBE_FRAGMENT_BODY` has a `uniform int view` that selects what the cube shows:
the index into `shaders.CUBE_VIEWS` (`final`, `albedo`, `normal`, `diffuse`,
`facing`, `specular`). `SceneContext.cube_view` holds it, starting at
`config.DEFAULT_CUBE_VIEW` (0, the lit image), and `CubeRenderer.paint` sends it
to the shader. Double-clicking resets the view and light but keeps `cube_view`.
The program has no control for changing it; the guide's images set it from code.
