# Project Context

A PyQt6 and OpenGL test program that draws a textured cube inside a sphere grid.
See `README.md` for what it does and `src/README.md` for how the modules fit
together. Update both when behaviour or module structure changes.

## Commands

Run these from the repository root, inside the conda environment from
`environment.yml` (plus `environment-docs.yml` for the manual):

```
conda env create -f environment.yml && conda activate opengl_qt6_test
conda env update -n opengl_qt6_test -f environment-docs.yml
python3 src/main.py           # open the window
python3 src/main.py --check   # run the self-test, then exit
pytest                        # run tests/, fail below 100% branch coverage
pytest --no-cov tests/test_<module>.py   # run a subset (the gate needs the full run)
make -C docs html             # build the HTML manual into docs/_build/html
```

`--check` needs a display and exits with status 0 only if everything passed.
Run it after every code change. It only confirms that frames change, so also save
a frame with `grabFramebuffer()` and look at it after any visual change.

`pytest` needs a display too. Run it after every change to `src/`, together
with `--check`.

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
  than GLSL 1.40, even though macOS compiles them as GLSL 4.10. All three
  headers have been run: GLSL 1.40 and ES on the Pi, 4.10 on macOS.
- Use PyQt6, not PySide6. `PySide6.QtOpenGLWidgets` isn't installed here.
- Avoid dependencies beyond PyQt6, PyOpenGL and NumPy. Any new Python
  dependency goes in `environment.yml` and `apt-packages.txt` (runtime or
  development) or in both `environment-docs.yml` and `docs/requirements.txt`
  (documentation), with the version floor and a matching README note. The
  conda floors track the Debian bookworm versions in `apt-packages.txt`.
- Lint with `ruff check src tools docs/conf.py tests`. The rule set is pinned in
  `ruff.toml`; change it there, not with per-run flags.
- Anything that is not a Python package (PlantUML, Java, Graphviz, the GL
  driver) belongs in the README's system prerequisites table, with the
  MacPorts and apt commands, and in `apt-packages-docs.txt` for Debian,
  never in an environment file. In particular do not add Graphviz to the
  conda files; see the README for why.

## Code conventions

- Use NumPy-style docstrings on every module, class, function and method.
  Sphinx renders them with napoleon, and the docs build treats warnings as
  errors, so run `make -C docs html` after changing a docstring or a README.
- The Sphinx pages under `docs/` include `README.md` and `src/README.md`
  rather than copying them. Relative links in those files must point at
  `src/README.md` or at nothing; a link to a file that is not a docs page
  fails the build.
- Module-level constants get a `#:` doc-comment so autodoc lists them.
- `docs/diagrams/*.puml` are hand-maintained PlantUML diagrams of the class
  structure, startup, a frame, mouse handling and the call graph. When a
  call is added or removed, a method is renamed, or the draw order changes,
  update the matching diagram in the same change. Rendering them needs
  `plantuml`, Java and Graphviz from MacPorts; `docs/conf.py` points
  PlantUML at `/opt/local/bin/dot` because the conda Graphviz 13 produces
  SVG that PlantUML rejects.
- Put runtime state in `SceneContext` and fixed settings in `config.py`. Don't
  hard-code tunable values in other modules.
- Renderers read from the `SceneContext` passed to `paint(ctx)`. They must not
  touch the widget or each other.
- `widget.py` should only translate mouse input into `SceneContext` calls.
- `textures.py` and `geometry.py` must stay free of OpenGL calls.
- Generate textures in code rather than adding image files. The one image
  file is `icon.png`, the application icon; regenerate it with
  `tools/make_icon.py` from a window screenshot rather than editing it.
- Every change to `src/` comes with tests in `tests/test_<module>.py` that keep
  line and branch coverage at 100%. `pytest.ini` owns the thresholds; change
  them there, not with per-run flags. See `ARCHITECTURE.md` (Testing) for the
  layout and `DECISIONS.md` for why.
- GL tests use the `gl_context`, `fbo`, `scene` and `image_to_array` fixtures
  from `tests/conftest.py` and draw into a real offscreen context. Stubs
  cover branches this machine cannot reach, plus `main.main()` and the
  `__main__` guard, where only one `QApplication` may exist; say which in the
  test's docstring.
- Every test docstring has two parts: a one-line summary of what it checks,
  then a paragraph starting with `**WHY:**` on why the suite needs it (the
  bug it would catch, or the convention it pins). `docs/tests/` renders them, so run
  `make -C docs html` after changing a test docstring, and add a page there
  for a new test file.
- A new Python test dependency follows the dependency rule above: it goes in
  `environment.yml` and `apt-packages.txt` with a version floor.
- Modules live directly in `src/` and import each other by name, such as
  `import config`. There is no package or install step.

## Rendering rules

- Draw order matters: cube, sphere grid, axes, then light dot.
- The sphere grid must not write depth, or it cuts gaps in the axes and dot.
- The cube, sphere and axes share `ctx.model_matrix()`, which keeps them anchored.
- The light is fixed in the scene, so the light dot ignores the model matrix.
- The sphere's longitude runs from +X towards +Y, with its poles on the Z axis.
