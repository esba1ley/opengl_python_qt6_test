# Project Context

A PyQt6 and OpenGL test program that draws a textured cube inside a sphere grid.
See `README.md` for what it does and `src/README.md` for how the modules fit
together. Update both when behaviour or module structure changes.

## Commands

Run these from the repository root:

```
python3 src/main.py           # open the window
python3 src/main.py --check   # run the self-test, then exit
make -C docs html             # build the HTML manual into docs/_build/html
```

`--check` needs a display and exits with status 0 only if everything passed.
Run it after every code change. It only confirms that frames change, so also save
a frame with `grabFramebuffer()` and look at it after any visual change.

The `Qt6CTPlatformTheme` lines and the `GLib-GObject-CRITICAL` warning in the
output are harmless.

## Platform constraints

- The development machine is a Raspberry Pi with a V3D 7.1 GPU, under Wayland.
  Its desktop OpenGL stops at 3.1 with GLSL 1.40; its OpenGL ES reaches 3.1.
- `main.py` requests OpenGL ES 3.1 on Linux and a 4.1 core profile on macOS
  (Apple M4), which otherwise gives OpenGL 2.1. Keep that choice gated on
  `sys.platform`: macOS has no OpenGL ES, and the Pi has no 3.2 core context.
- `gl_utils.glsl_header` derives the `#version` line from the context Qt
  actually created, so shader bodies in `shaders.py` must not include one.
- Shader bodies are shared by every header, so they must stay within the
  features common to GLSL 1.40 and GLSL ES 3.00. Do not use anything newer
  than GLSL 1.40, even though macOS compiles them as GLSL 4.10. The ES
  request has not yet been run on the Pi.
- Use PyQt6, not PySide6. `PySide6.QtOpenGLWidgets` isn't installed here.
- Avoid dependencies beyond PyQt6, PyOpenGL and NumPy.

## Code conventions

- Use NumPy-style docstrings on every module, class, function and method.
  Sphinx renders them with napoleon, and the docs build treats warnings as
  errors, so run `make -C docs html` after changing a docstring or a README.
- The Sphinx pages under `docs/` include `README.md` and `src/README.md`
  rather than copying them. Relative links in those files must point at
  `src/README.md` or at nothing; a link to a file that is not a docs page
  fails the build.
- Module-level constants get a `#:` doc-comment so autodoc lists them.

## Rendering rules

- Draw order matters: cube, sphere grid, axes, then light dot.
- The sphere grid must not write depth, or it cuts gaps in the axes and dot.
- The cube, sphere and axes share `ctx.model_matrix()`, which keeps them anchored.
- The light is fixed in the scene, so the light dot ignores the model matrix.
- The sphere's longitude runs from +X towards +Y, with its poles on the Z axis.
