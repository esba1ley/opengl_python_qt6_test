# From arrays to vertex buffers

[The geometry](geometry.md) ends with lists of numbers in Python. The vertex
shaders read their `in` variables, the **attributes**, from memory the GPU
can reach, so the numbers have to be copied there once, and OpenGL has to be
told how to find each attribute among them. This page does that for the cube
and then for the overlay.

Three kinds of OpenGL object are involved:

- a **buffer object** holds bytes in GPU-accessible memory. Used for vertex
  data, it is often called a **VBO**, a vertex buffer object;
- a **vertex array object** (**VAO**) records how the attributes are laid out
  in buffers: for each attribute, whether it is used, where it starts, how
  many numbers it has, and which buffer it comes from;
- the **program** built on [the context page](context.md), whose attributes
  have numbered **locations**.

(guide-cube-buffer)=
## The cube: `init_vertices`

{py:meth}`cube.CubeRenderer.init_vertices` runs once, from `initialize`,
with the context current:

```{literalinclude} ../../src/cube.py
:language: python
:pyobject: CubeRenderer.init_vertices
:start-at: vertices = geometry.cube_vertices()
:dedent: 8
```

### From a Python list to C floats

`geometry.cube_vertices()` returns a Python list of 540 floats, 36 vertices
of 15. `vertex_count` is $540 / 15 = 36$, the number of vertices to draw.

A Python list holds pointers to Python objects, not numbers laid side by
side, so OpenGL cannot read it. `GL.GLfloat * len(vertices)` is a [ctypes](https://docs.python.org/3/library/ctypes.html)
type, an array of 540 C `float`s, and calling it with `*vertices` creates one
filled with the values. A C `float` is 4 bytes, `FLOAT_SIZE`, so the array
is 2160 bytes.

### The vertex array object

`glGenVertexArrays(1)` creates one VAO name, and `glBindVertexArray` makes it
the current one. From here on, every call that enables or describes an
attribute is recorded in this VAO. At the end, `glBindVertexArray(0)` breaks
the binding, so that no later call can change the recorded layout by
accident.

The VAO is what makes drawing short: binding it again restores the whole
layout in one call. It is also required. In a core-profile context, which is
what macOS gives this program, VAO 0 means no vertex array at all, and a call
that changes, draws from or reads vertex array state with none bound fails
with `GL_INVALID_OPERATION`. OpenGL ES 3 still has a default VAO, but the
program creates its own on every platform.

### The buffer: `glGenBuffers`, `glBindBuffer`, `glBufferData`

- `glGenBuffers(1)` creates a buffer name.
- `glBindBuffer(GL_ARRAY_BUFFER, vbo)` binds it to the `GL_ARRAY_BUFFER`
  target, the one vertex attributes are read from. Calls that name that
  target now act on this buffer.
- `glBufferData(GL_ARRAY_BUFFER, size, data, usage)` creates the buffer's
  **data store**, `size` bytes, here $540 \times 4 = 2160$, and copies
  `data` into it. Once the call returns, the Python and ctypes copies are no
  longer needed.
- `GL_STATIC_DRAW` is the usage hint. *Static* means the contents are set
  once and used many times; *draw* means the application writes them and
  OpenGL reads them for drawing. A hint lets the driver choose where to keep
  the data. It does not restrict what the program may do with the buffer.

### Describing the attributes

The loop walks `geometry.VERTEX_ATTRIBUTES` ({ref}`guide-layers`) and
connects each attribute to the shader input of the same name.

- `glGetAttribLocation(program, name)` returns the location the linker gave
  the attribute. The locations are not in the order the shader declares the
  attributes: on a Mac with an M4 chip, `position` is 5 and `bitangent` is
  0. Looking each up by name is what keeps the Python table and the shader
  in step. A name that is not an active attribute returns −1.
- `glEnableVertexAttribArray(location)` turns the attribute on in the bound
  VAO. Attributes are off by default, and an attribute that is off is not
  read from a buffer.
- `glVertexAttribPointer` describes where the attribute's values are.

The arguments of `glVertexAttribPointer`:

- `location`, the attribute.
- `size`, the number of components: 3 for the position, normal, tangent and
  bitangent, 2 for `uv`, 1 for `layer`. It matches the GLSL type, `vec3`,
  `vec2` or `float`.
- `GL_FLOAT`, the type of each component in the buffer: 32-bit floats.
- `GL_FALSE`, *normalised*. Normalising maps integer data into
  $[0, 1]$ or $[-1, 1]$; the data here is already floating point, so it is
  passed through.
- `stride`, the number of bytes from one vertex to the next:
  $15 \times 4 = 60$. Every attribute has the same stride, because the
  attributes are **interleaved**: all 15 numbers of a vertex sit together,
  then the next vertex's.
- `GL.GLvoidp(offset * FLOAT_SIZE)`, the offset in bytes of the attribute's
  first value from the start of the buffer. The C parameter is a pointer, a
  leftover from when vertex data was read from the application's memory, so
  [PyOpenGL](https://pyopengl.sourceforge.net/documentation/) wants the offset wrapped as a `void *`.

`offset` counts floats and grows by each attribute's size, so the offsets
follow from the order and sizes in `VERTEX_ATTRIBUTES`:

| Attribute | Size | Offset (floats) | Offset (bytes) |
|---|---|---|---|
| `position` | 3 | 0 | 0 |
| `normal` | 3 | 3 | 12 |
| `tangent` | 3 | 6 | 24 |
| `bitangent` | 3 | 9 | 36 |
| `uv` | 2 | 12 | 48 |
| `layer` | 1 | 14 | 56 |

The last attribute ends at byte $56 + 4 = 60$, the stride. Vertex $i$'s
`uv`, for example, is the two floats at bytes $60\,i + 48$ and $60\,i + 52$.

`glVertexAttribPointer` also stores, for that attribute, the buffer bound to
`GL_ARRAY_BUFFER` when it is called. That is how the VAO knows which buffer
to read, and why `glBindBuffer` comes before the loop. The `GL_ARRAY_BUFFER`
binding itself is not part of the VAO: with the cube's VAO bound again
later, `GL_ARRAY_BUFFER_BINDING` reads 0, while each attribute's
`GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING` reads the cube's buffer.

### Drawing

```{literalinclude} ../../src/cube.py
:language: python
:pyobject: CubeRenderer.paint
:start-at: GL.glBindVertexArray(self.vao)
:dedent: 8
```

Binding the VAO brings back the layout. `glDrawArrays(mode, first, count)`
then takes `count` consecutive vertices from every enabled attribute,
starting at vertex `first`, and builds primitives of kind `mode` from them.
`GL_TRIANGLES` takes the vertices three at a time: 36 vertices, 12
triangles, two per face, in the order `cube_vertices` wrote them.

(guide-overlay-buffer)=
## The overlay: one buffer, three ranges

{py:meth}`overlay.OverlayRenderer.initialize` puts the sphere grid, the axes
and the light dot into one buffer:

```{literalinclude} ../../src/overlay.py
:language: python
:pyobject: OverlayRenderer.initialize
:start-at: grid = geometry.grid_vertices()
:end-at: GL.glBindVertexArray(0)
:dedent: 8
```

The three arrays all have six columns, a position and a colour
({ref}`guide-sphere-grid`), so `np.vstack` stacks them into one array of
$10{,}440 + 6 + 1 = 10{,}447$ rows. `astype(np.float32)` matters: [NumPy](https://numpy.org/doc/stable/)'s
default is 64-bit floats, and `GL_FLOAT` is 32 bits. `tobytes()` writes the
rows one after another, each row's six numbers together, which is again an
interleaved layout. `data.nbytes` is $10{,}447 \times 6 \times 4 =
250{,}728$ bytes.

The rest follows the cube's pattern with two attributes instead of six.
The stride is $6 \times 4 = 24$ bytes; `position` starts at byte 0 and
`vertexColor` at byte 12, and both have three components. The offsets are
written out in the loop instead of coming from a table.

The three parts are told apart by where they sit in the buffer. The counts
are kept from `len(grid)` and `len(axes)` and passed to `glDrawArrays` as
`first` and `count`:

| Part | Drawn in | Mode | `first` | `count` |
|---|---|---|---|---|
| Sphere grid | `paint_grid` | `GL_LINES` | 0 | 10,440 (`grid_count`) |
| Axes | `paint_axes` | `GL_LINES` | 10,440 | 6 (`axis_count`) |
| Light dot | `paint_light_dot` | `GL_POINTS` | 10,446 (`dot_first`) | 1 |

The grid's 10,440 vertices are 5220 segments, the axes' 6 are three
segments, and the dot is one point. All three use the same VAO, bound once
in `paint`; only the range, the mode and the uniforms change between them.

## Nothing moves in the buffers

Neither buffer is written again after `initialize`. The vertices stay in
model space, as {py:mod}`geometry` made them, for the life of the program.
(The light dot is the exception: its vertex is at the origin and its own
transform moves it, not the model matrix.)
Turning the cube, panning, zooming and moving the light change only the
{py:class}`~context.SceneContext`, and each frame turns that into uniforms:
the `mvp` and `model` matrices, the light direction and the camera position
([coordinate spaces and the camera](spaces.md)). The vertex shader applies
them to every vertex as it is drawn. Sending a few matrices per frame is far
cheaper than rewriting 10,000 vertices, and it is why the buffers can be
`GL_STATIC_DRAW`.

## Further reading

- The OpenGL Wiki on [vertex specification](https://wikis.khronos.org/opengl/Vertex_Specification): vertex array objects, buffers and attribute formats.
- Reference pages: [`glGenVertexArrays`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glGenVertexArrays.xhtml), [`glBindVertexArray`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glBindVertexArray.xhtml), [`glBufferData`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glBufferData.xhtml), [`glVertexAttribPointer`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml) and [`glDrawArrays`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glDrawArrays.xhtml).
- Python's [`ctypes`](https://docs.python.org/3/library/ctypes.html), and [PyOpenGL for OpenGL programmers](https://pyopengl.sourceforge.net/documentation/opengl_diffs.html) on how PyOpenGL accepts arrays.

The {ref}`references page <references>` lists the rest, with the
authors' tutorials for each part of the program.
