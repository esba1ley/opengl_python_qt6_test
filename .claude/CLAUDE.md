# Project Context

A PyQt6 and OpenGL test program that draws a textured cube inside a sphere grid.
See `README.md` for what it does and `src/README.md` for how the modules fit
together. Update both when behaviour or module structure changes.

## Commands

Run these from the repository root:

```
python3 src/main.py           # open the window
python3 src/main.py --check   # run the self-test, then exit
```

`--check` needs a display and exits with status 0 only if everything passed.
Run it after every code change. It only confirms that frames change, so also save
a frame with `grabFramebuffer()` and look at it after any visual change.

The `Qt6CTPlatformTheme` lines and the `GLib-GObject-CRITICAL` warning in the
output are harmless.

## Platform constraints

- The development machine is a Raspberry Pi with a V3D 7.1 GPU, under Wayland.
- It provides OpenGL 3.1 and GLSL 1.40, so shaders must not use `#version 330`
  or later features. `gl_utils.glsl_header` adds the version line, so shader
  bodies in `shaders.py` must not include one.
- Keep shaders valid for both GLSL 1.40 and GLSL ES 3.00. The ES path has never
  been run.
- It also runs on macOS (Apple M4). `main.py` requests a 3.2 core profile
  there, since macOS otherwise gives OpenGL 2.1. Keep that request gated on
  `sys.platform`, because the Pi has no 3.2 core context.
- Use PyQt6, not PySide6. `PySide6.QtOpenGLWidgets` isn't installed here.
- Avoid dependencies beyond PyQt6, PyOpenGL and NumPy.

## Code conventions

- Use NumPy-style docstrings on every module, class, function and method.
- Put runtime state in `SceneContext` and fixed settings in `config.py`. Don't
  hard-code tunable values in other modules.
- Renderers read from the `SceneContext` passed to `paint(ctx)`. They must not
  touch the widget or each other.
- `widget.py` should only translate mouse input into `SceneContext` calls.
- `textures.py` and `geometry.py` must stay free of OpenGL calls.
- Generate textures in code rather than adding image files. The one image
  file is `icon.png`, the application icon; regenerate it with
  `tools/make_icon.py` from a window screenshot rather than editing it.
- Modules live directly in `src/` and import each other by name, such as
  `import config`. There is no package or install step.

## Rendering rules

- Draw order matters: cube, sphere grid, axes, then light dot.
- The sphere grid must not write depth, or it cuts gaps in the axes and dot.
- The cube, sphere and axes share `ctx.model_matrix()`, which keeps them anchored.
- The light is fixed in the scene, so the light dot ignores the model matrix.
- The sphere's longitude runs from +X towards +Y, with its poles on the Z axis.
