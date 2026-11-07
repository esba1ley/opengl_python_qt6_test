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
| `textures.py` | Procedural materials and normal maps, using only NumPy | No |
| `shaders.py` | GLSL source for both renderers | No |
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
| Add or replace a material | Add a function to `textures.py`, then update `MATERIALS` |
| Add a new mouse control | Add a method to `SceneContext`, then call it from `widget.py` |
| Draw something new | Add a renderer, then call it from `CubeWidget.paintGL` |
| Add a self-test check | Extend `check` in `selftest.py` |
| Add a unit test | Add to `tests/test_<module>.py`, with a docstring saying what it checks and why; `pytest` fails below 100% coverage |

Material functions take `(size, rng)` and return a colour image and a height map
as float arrays from 0 to 1. `MATERIALS` needs one entry per cube face, in the
order used by `cube_vertices` in `geometry.py`.
