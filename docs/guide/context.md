# The OpenGL context and shader programs

The previous page ended with Qt calling `initializeGL` with the widget's
OpenGL context current. This page explains what that context is, how the
program finds out which version of OpenGL it got, and how it turns the GLSL
source strings in {py:mod}`shaders` into programs the GPU can run. It ends
with how Python values reach the variables in those programs.

The OpenGL context is not the same thing as {py:class}`context.SceneContext`,
the program's own object holding the camera and the light. On this page
"context" means the OpenGL one.

(guide-what-is-a-context)=
## What a context is

OpenGL is a long list of functions, such as `glClear` or `glDrawArrays`, and
almost all of them act on hidden state: which shader program is in use,
which textures are bound, whether depth testing is on, and the objects
themselves (shaders, textures, buffers). A **context** holds one complete set
of that state. The window system creates it, at Qt's request, for use with
a window or an off-screen surface, and an OpenGL call always acts on the
context that is **current**. A context can be current in only one thread, and against one
surface, at a time.

This is why nothing in the program calls OpenGL before `initializeGL`. The
widget's context does not exist until Qt creates it, after the window is
shown, and Qt makes it current before calling `initializeGL`, `resizeGL` and
`paintGL` ({ref}`guide-gl-overrides`). The names OpenGL returns, such as the
program and texture numbers below, mean something only in that context.

(guide-requested-format)=
## What was asked for, and what was granted

{py:func}`main.request_surface_format` ({ref}`guide-surface-format`) asks for
OpenGL 4.1 core on macOS and OpenGL ES 3.1 elsewhere. A `QSurfaceFormat` is a
set of requests, not a guarantee: the context Qt creates may differ. Its
actual format can be read back from the context, and on some systems it is a
newer version than the one requested.

The widget adds two requests of its own to the default format
({ref}`guide-widget`): a 24-bit depth buffer and 4 samples per pixel. These
describe the framebuffer the widget draws into rather than the version of
OpenGL, so they belong with the widget. Qt's documentation for
`QOpenGLWidget` says it is up to the application to ask for a depth buffer,
and that multisampling is enabled by setting the number of samples on the
format passed to `setFormat()`. The tests and `tools/offscreen.py` use the
same default format but draw into framebuffer objects they create
themselves, and give those a depth buffer when they create them.

The widget's requests are no more binding than the version: where
multisampling is not supported, the request for samples may be ignored, and
the program still runs.

(guide-glsl-header)=
## Choosing the GLSL version: `glsl_header`

Every GLSL shader starts with a `#version` line, and it must come before
anything else in the source except comments and blank space. Without one,
desktop GLSL assumes version 1.10. Each OpenGL version supports particular
GLSL versions, so the right line depends on the context. The shader bodies in {py:mod}`shaders`
therefore have no `#version` line, and {py:func}`gl_utils.glsl_header`
writes one for the context that is current:

```{literalinclude} ../../src/gl_utils.py
:language: python
:pyobject: glsl_header
:start-at: context = QOpenGLContext.currentContext()
:dedent: 4
```

`QOpenGLContext.currentContext()` returns the context that is current in
this thread, the widget's, and `format()` returns the format it was actually
created with, so `major` and `minor` are the version that was granted, not
the one requested.

**OpenGL ES.** `isOpenGLES()` is true for an OpenGL ES context. OpenGL ES 3.0
pairs with GLSL ES 3.00 and OpenGL ES 3.1 with GLSL ES 3.10, so
`300 + 10 * minor` gives 300 or 310, written `#version 310 es` on the
Raspberry Pi. Anything other than ES 3.x falls back to 300, and the compiler
reports the problem if the context cannot compile it.

The two precision lines are needed by GLSL ES only. GLSL ES lets a shader
declare how precise a type must be, `lowp`, `mediump` or `highp`, and gives
some types a default. The fragment shader language has no default precision
for `float`, and neither shader language has one for `sampler2DArray`, the
type of the cube's two textures ({ref}`guide-texture-arrays`). Without the
lines, every `float` declaration in a fragment shader would need its own
qualifier.

- `precision highp float;` makes every `float`, and every float vector and
  matrix, `highp`, the highest of the three.
- `precision lowp sampler2DArray;` gives the array sampler the same
  precision GLSL ES gives `sampler2D` by default.

The same header goes on the vertex shader too, where `highp float` is the
default already.

**Desktop OpenGL.** The version numbers do not line up before 3.3:

| Context | GLSL | `#version` |
|---|---|---|
| OpenGL 3.1 | 1.40 | `140` |
| OpenGL 3.2 | 1.50 | `150` |
| OpenGL 3.3 | 3.30 | `330` |
| OpenGL 4.1 (macOS) | 4.10 | `410` |

From 3.3 on, the GLSL version equals the OpenGL version, written without the
point, hence `100 * major + 10 * minor`. 3.2 gets 150, and anything older
gets 140, the lowest the shader bodies are written for. A driver that does
not support the version in the line reports an error when compiling. No
precision lines are added: desktop GLSL accepts precision qualifiers only for
portability with OpenGL ES and gives them no meaning.

The shader bodies are written once for all of these headers, so they use only
what GLSL 1.40 and GLSL ES 3.00 have in common, even on macOS, where they are
compiled as GLSL 4.10. [The shaders page](shaders.md) explains the bodies
themselves.

(guide-compile)=
## Compiling a shader: `compile_shader`

```{literalinclude} ../../src/gl_utils.py
:language: python
:pyobject: compile_shader
:start-at: shader = GL.glCreateShader(kind)
:dedent: 4
```

A **shader object** holds the source of one shader and, after compiling,
the result.

- `glCreateShader(kind)` creates an empty shader object and returns its
  **name**, a non-zero integer that stands for it in later calls. `kind` is
  `GL_VERTEX_SHADER` or `GL_FRAGMENT_SHADER`.
- `glShaderSource` copies the source string into the object. Nothing is
  checked yet.
- `glCompileShader` compiles it. Compilation can fail, for example on a typing
  mistake in the GLSL, and the call itself does not say so: the result is
  stored in the shader object.
- `glGetShaderiv(shader, GL_COMPILE_STATUS)` reads that result back, true
  if the shader compiled without errors.
- On failure, `glGetShaderInfoLog` returns the compiler's messages, as
  written by the driver. The function raises them as a `RuntimeError`, so a
  shader error stops the program with the driver's own explanation.

(guide-link)=
## Linking a program: `build_program`

Shaders run as part of a **program object**, which here joins one vertex
shader and one fragment shader:

```{literalinclude} ../../src/gl_utils.py
:language: python
:pyobject: build_program
:start-at: header = glsl_header()
:dedent: 4
```

- `glsl_header()` is called once, and the header is put in front of both
  bodies.
- `glCreateProgram()` creates an empty program object.
- The loop compiles each shader with `compile_shader` and attaches it with
  `glAttachShader`, which marks it to be included when the program is linked.
- `glLinkProgram` links the attached shaders into one program the GPU can
  run. Linking can fail even when both shaders compiled: for example, when
  the fragment shader uses an input that the vertex shader does not declare
  in the same way. As with compiling, the result is stored in the object,
  not returned.
- `glGetProgramiv(program, GL_LINK_STATUS)` reads the result, and
  `glGetProgramInfoLog` gives the linker's messages, again raised as a
  `RuntimeError`.

The function returns the program's name. Each renderer builds one program in
its `initialize` and keeps the name; before drawing, `glUseProgram` makes it
the current program, and the next draw call runs it.

(guide-uniform-locations)=
## Finding the uniforms: locations

A shader reads values from the program in two ways. **Attributes** (`in`
variables of the vertex shader) are read per vertex from a buffer;
[from arrays to vertex buffers](buffers.md) describes them and
`glGetAttribLocation`. **Uniforms** are
single values, the same for every vertex and fragment of one draw call: a
matrix, a light direction, a texture unit.

OpenGL does not set a uniform by its name. After linking, each uniform has
a **location**, an integer, and `glGetUniformLocation(program, name)`
returns it. {py:meth}`cube.CubeRenderer.initialize` looks up the cube's
uniforms once, straight after building the program:

```{literalinclude} ../../src/cube.py
:language: python
:pyobject: CubeRenderer.initialize
:start-at: self.program = gl_utils.build_program
:end-at: self.view_loc
:dedent: 8
```

{py:meth}`overlay.OverlayRenderer.initialize` does the same with a
dictionary, so its paint methods can write `locs["opacity"]`:

```{literalinclude} ../../src/overlay.py
:language: python
:pyobject: OverlayRenderer.initialize
:start-at: self.locs = {
:end-at: '        }'
:dedent: 8
```

Locations stay the same until the program is linked again, which never
happens here, so looking them up once is enough.

`glGetUniformLocation` returns -1 for a name that is not an **active**
uniform of the program. A uniform is active only if the linker found that the
program may read it, so a uniform that is declared but never used need not be
active, and its location is then -1 too. Setting a value at location -1 is
silently ignored. A misspelt name, or a uniform the shader stopped using, therefore
gives no error, only a scene that does not change.
`test_uniform_locations_are_all_found` in `tests/test_cube.py` checks that
each of the five locations `initialize` stores is 0 or more.

(guide-setting-uniforms)=
## Setting uniforms: `set_matrix`, `set_vector`, `glUniform1i`

A uniform is set with one of the `glUniform` functions, whose name says the
type: `glUniform3f` for three floats, `glUniformMatrix4fv` for 4 × 4 float
matrices, `glUniform1i` for one integer. They act on the current program, so
each `paint` method calls `glUseProgram` first. The values stay in the program
until they are set again.

```{literalinclude} ../../src/gl_utils.py
:language: python
:pyobject: set_matrix
:start-at: values =
:dedent: 4
```

The matrices are `QMatrix4x4` objects. `copyDataTo()` returns their 16
entries in **row-major** order, row by row. `glUniformMatrix4fv` expects
**column-major** order, column by column, unless its third argument,
`transpose`, is `GL_TRUE`; then it reads the values as rows. Passing
`GL_TRUE` therefore gives the shader the matrix as Qt holds it, so that
`mvp * vec4(position, 1.0)` in GLSL is the same homogeneous product Qt
computes in `mvp.map(position)`. The two results differ only in that
`map()` also divides by $w$, while `gl_Position` is kept before the divide. `(GL.GLfloat * 16)(...)` packs the values
into a ctypes array of 16 C floats for PyOpenGL to pass on. The `1` is the
number of matrices.

```{literalinclude} ../../src/gl_utils.py
:language: python
:pyobject: set_vector
:start-at: GL.glUniform3f
:dedent: 4
```

`set_vector` passes the three components of a `QVector3D` to `glUniform3f`.

Integer uniforms are set directly with `glUniform1i`:

- **Samplers.** A sampler uniform holds the number of a texture unit, and
  `glUniform1i` (or `glUniform1iv`) is the only way to set one.
  {py:meth}`cube.CubeRenderer.init_textures` sets `albedoMap` to 0 and
  `normalMap` to 1 ({ref}`guide-texture-arrays`).
- **Integers.** `view` in the cube's fragment shader is an `int`, set each
  frame to `ctx.cube_view`.
- **Booleans.** `sideShading` and `roundPoint` in the overlay's fragment
  shader are `bool`. They are set with `glUniform1i` too: 0 sets false and
  any other value true.

`glUniform1f` sets a single float, such as the overlay's `opacity` and
`pointSize`. If a call's type and size do not match the uniform's
declaration in the shader, OpenGL records the error `GL_INVALID_OPERATION`
and leaves the uniform unchanged.
