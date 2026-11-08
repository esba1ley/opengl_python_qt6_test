# Project Context

A PyQt6 and OpenGL test program that draws a textured cube inside a sphere grid,
and a teaching example of the whole program, from the window and the OpenGL
context through the geometry to procedural textures and shaders: the code is
meant to be read, and the "How it works" chapter (`docs/guide/`) explains
it. See `README.md` for what it does and `src/README.md` for how the modules
fit together. Update both when behaviour or module structure changes.

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

`.github/workflows/docs.yml` runs the same docs build on every push to
`develop`, `main`, `ft/**` and `rc/**` and publishes the manual to GitHub Pages
from `main`.
A docs change that builds locally can still fail there, since the runner
uses Ubuntu's PlantUML and Graphviz; check the run after pushing.

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
- Avoid dependencies beyond PyQt6, PyOpenGL and NumPy. Pillow is the one
  exception, a development dependency used only by
  `tools/make_control_animations.py`; nothing in `src/` or `tests/` may
  import it. Any new Python
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
  fails the build. Images are fine: the include in `docs/index.md` uses
  `:relative-images:`, so image paths stay relative to the README.
- Module-level constants get a `#:` doc-comment so autodoc lists them.
- `docs/diagrams/*.puml` are hand-maintained PlantUML diagrams of the class
  structure, startup, a frame, mouse handling and the call graph, plus
  `textures.puml`, the texture pipeline. When a call is added or removed, a
  method is renamed, or the draw order changes, update the matching diagram in
  the same change. A change to the texture pipeline or to the cube shader's
  stages updates `textures.puml`. Rendering them needs
  `plantuml`, Java and Graphviz from MacPorts; `docs/conf.py` points
  PlantUML at `/opt/local/bin/dot` because the conda Graphviz 13 produces
  SVG that PlantUML rejects.
- Put runtime state in `SceneContext` and fixed settings in `config.py`. Don't
  hard-code tunable values in other modules.
- Renderers read from the `SceneContext` passed to `paint(ctx)`. They must not
  touch the widget or each other.
- `widget.py` should only translate mouse input into `SceneContext` calls.
- `textures.py` and `geometry.py` must stay free of OpenGL calls.
- Materials in `textures.py` are built from the shared patterns (`seam`,
  `cell_lattice`, `edge_distance`, `checker`, `voronoi`, `dome`) and return
  `Material(color, height, steps)`, recording each intermediate array in
  `steps` as it is built. Never record the distance volume, and never change
  a recorded array in place. A recorded step must not move a random draw: the
  texture bytes must stay the same unless a material is meant to change.
- The cube shader's `view` uniform must keep view 0
  identical to the lit image, and every view in `shaders.CUBE_VIEWS` must
  render. After a shader change, regenerate `tools/make_face_images.py`,
  `tools/make_icon.py` and `tools/make_control_animations.py` output and
  check that git shows no change.
- After changing a material, a pattern, the geometry, the cube shader, the
  overlay's drawing or anything visible in the default frame (the build-up
  images show it), rerun
  `python3 tools/make_guide_images.py docs/images/guide` and look at the
  images; commit them with the change.
- Each guide page ends with "Further reading", and `docs/references.md`
  lists the documentation for every dependency, Qt class and OpenGL
  version. A new dependency, Qt class or GL topic gets its link there,
  checked with `python3 -m sphinx -b linkcheck docs docs/_build/linkcheck`
  (Khronos's wiki and SourceForge refuse the checker; open those by hand).
  In the READMEs and the manual's pages, link the first prose mention of
  a package on each page to the same URL the references page uses.
- The chapter quotes code with `literalinclude` (`:pyobject:` for functions,
  `:start-after:` the constant's assignment line, such as
  `CUBE_VERTEX_BODY = """`, with `:end-before:` the closing quotes, for
  shader strings), so renaming a quoted
  function or constant needs a `make -C docs html`.
- Generate textures in code rather than adding image files. The one image
  file the program loads is `icon.png`, the application icon. Every image in
  the repository is rendered by a tool in `tools/`, never drawn or captured
  by hand; the tools share `tools/offscreen.py`.
- `icon.png` and `docs/images/screenshot.png` come from one render of the
  default view: rerun `tools/make_icon.py icon.png docs/images/screenshot.png`
  after any visible change, and look at both.
- `docs/images/face-*.png` illustrate the README's material table. They are
  rendered, not drawn: rerun `tools/make_face_images.py docs/images` after
  changing a material, the cube shader or the default light, and look at
  them.
- `docs/images/control-*.webp` animate the README's mouse controls table.
  Rerun `tools/make_control_animations.py docs/images` after changing the
  mouse handling, `config` interaction settings or anything visible, and
  play them before committing; every regeneration adds about 1 MB to the
  repository's history, so do not regenerate them for unrelated changes.
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
- The sphere grid must not write depth, or its near lines hide its own far-side
  lines and it cuts gaps in the axes and dot.
- The cube, sphere and axes share `ctx.model_matrix()`, which keeps them anchored.
- The light is fixed in the scene, so the light dot ignores the model matrix.
- The sphere's longitude runs from +X towards +Y, with its poles on the Z axis.
