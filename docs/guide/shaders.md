# The shaders

A **shader** is a small program the GPU runs in parallel, written in GLSL.
Two kinds are used here. A **vertex shader** runs once per vertex and says
where it lands on screen. The GPU then fills each triangle with
**fragments**, roughly one per covered pixel, interpolating the vertex
shader's outputs across the triangle. A **fragment shader** runs once per
fragment and returns its colour.

The shader sources are Python strings in {py:mod}`shaders`, without a
`#version` line. {py:func}`gl_utils.build_program` prepends the header that
{py:func}`gl_utils.glsl_header` chooses for the OpenGL context Qt actually
created: GLSL 1.40 or 1.50 on desktop OpenGL 3.1 or 3.2, a matching version
from 3.3 on (4.10 on macOS), and GLSL ES 3.x0 with precision statements on
OpenGL ES. The bodies therefore use only what GLSL 1.40 and GLSL ES 3.00
have in common.

## The cube's vertex shader

```{literalinclude} ../../src/shaders.py
:language: glsl
:start-after: CUBE_VERTEX_BODY = """
:end-before: '"""'
```

**Uniforms** are values set once per draw call and shared by every vertex.
{py:meth}`cube.CubeRenderer.paint` sets them from the
{py:class}`context.SceneContext`:

- `mvp` is projection × view × model, `ctx.view_projection_matrix() * model`:
  model space to clip space in one matrix.
- `model` is `ctx.model_matrix()`, the cube's rotation.

The `in` variables are the vertex attributes from
`geometry.VERTEX_ATTRIBUTES` ({ref}`guide-layers`), one set per vertex.

- `gl_Position = mvp * vec4(position, 1.0)` is the one output OpenGL
  requires: the vertex in clip space. The 1.0 makes the position a point, so
  translations in the matrix apply to it.
- The next four lines rotate the position and the face's three axes into
  world space, where the light and camera are given. `mat3(model)` is the
  upper-left 3 × 3 of the model matrix. The model matrix is a pure rotation,
  so that is enough: there is no translation for positions to miss, and a
  rotation turns normals correctly. (A matrix with non-uniform scaling would
  need its inverse transpose for normals.)
- `textureCoords` and `textureLayer` pass the texture coordinates and layer
  through unchanged.

Every `out` is interpolated across the triangle for the fragment shader,
except `textureLayer`, which is `flat`: each fragment gets the value of one
vertex unchanged. For the cube, the three axes are the same at every vertex
of a face, so they arrive unchanged too, up to rounding; `textureCoords` varies, and each
fragment gets its own $(u, v)$ on the face.

## The cube's fragment shader

```{literalinclude} ../../src/shaders.py
:language: glsl
:start-after: CUBE_FRAGMENT_BODY = """
:end-before: '"""'
```

The new uniforms come from the same `paint` call:

- `albedoMap` and `normalMap` are **samplers**, handles to the textures on
  units 0 and 1 ({ref}`guide-texture-arrays`).
- `lightDirection` is `ctx.light`, a unit vector pointing *towards* the light
  in world space. The light is directional, like the sun: the same direction
  at every point.
- `cameraPosition` is `ctx.camera_position()`, the camera in world space.
- `view` is `ctx.cube_view`, which picks a debug view (below).

The pictures in this section are the cube through each debug view. They show
the cube alone, without the grid, under one light chosen by
`specular_light` in `tools/make_guide_images.py`: the direction that mirrors
the camera in the front (+Z) face, so the specular highlight is centred on
that face. Under the window's default light the highlight is nearly
invisible, so it could not be pictured. `view-final.png` therefore differs
from the screenshot in the README.

### Albedo

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: vec3 coords = vec3(textureCoords, textureLayer);
:end-at: vec3 albedo = texture(albedoMap, coords).rgb;
```

`texture` reads a sampler at a coordinate, applying the filters set at upload
({ref}`guide-mipmaps`). For an array texture the coordinate has three
components, $(u, v, \text{layer})$. **Albedo** is the surface's own colour
before any lighting: the material's colour image.

```{figure} ../images/guide/view-albedo.png
:alt: The cube in plain texture colours: rivets in front, bricks on the right, tiles on top, all equally bright

View 1, `albedo`. The faces are unlit, so all three are equally bright.
```

### The bent normal

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: vec3 surface = texture(normalMap, coords)
:end-at: vec3 n = normalize(tangentToWorld * surface);
```

The first line undoes the encoding of {py:func}`textures.height_to_normals`:
$\mathbf{s} = 2\,\mathrm{rgb} - 1$ maps $[0, 1]$ back to $[-1, 1]$, a normal
in tangent space.

`mat3(a, b, c)` builds a matrix whose columns are `a`, `b` and `c`. With the
face's world-space tangent $\mathbf{T}$, bitangent $\mathbf{B}$ and normal
$\mathbf{N}$ as columns,

$$
\mathbf{n} = \operatorname{normalize}\bigl(
  [\mathbf{T}\ \mathbf{B}\ \mathbf{N}]\,\mathbf{s}\bigr)
= \operatorname{normalize}\bigl(
  s_x \mathbf{T} + s_y \mathbf{B} + s_z \mathbf{N}\bigr) .
$$

That is the change of frame: the map's $x$ goes along the direction in which
$u$ grows, $y$ along $v$, $z$ out of the face. The three axes are normalised
because interpolation does not preserve length in general, and the result is
normalised because filtering shortens the stored normals
({ref}`guide-mipmaps`).

```{figure} ../images/guide/view-normal.png
:alt: The cube coloured by its normals: blue front, pink right, green top, with the bumps visible as colour shifts

View 2, `normal`: $\tfrac{1}{2}\mathbf{n} + \tfrac{1}{2}$ as a colour. Unlike
the normal maps, these are world-space normals, so each face has its own base
colour, and the rivets, bricks and tiles show as shifts in it.
```

### The facing gate

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: float facing = smoothstep
:end-at: float facing = smoothstep
```

A normal map can tilt $\mathbf{n}$ towards the light on a face that points
away from it. Without a check, the slopes of bumps on a face in the cube's
own shadow would catch light that has to pass through the cube to reach them.
So `facing` asks the real face normal $\mathbf{N}$, not the bent one, whether
the face is lit at all:

$$
\mathrm{facing} = \operatorname{smoothstep}(0,\ 0.1,\ \mathbf{N} \cdot \mathbf{L}) .
$$

It is 0 on faces turned away from the light, 1 once $\mathbf{N}\cdot\mathbf{L}
\ge 0.1$, and fades between, over the last $5.7°$ or so before the light
grazes the face ($\arcsin 0.1 \approx 5.7°$). The fade means a face does not
switch on with a jump as the cube turns. `smoothstep` here is GLSL's
built-in, with the same formula as {py:func}`textures.smoothstep`.

```{figure} ../images/guide/view-facing.png
:alt: Only the front face of the cube, in white, on black

View 4, `facing`. Under this light only the front face is lit; the others are
gated to 0.
```

### Diffuse light

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: float diffuse = facing
:end-at: float diffuse = facing
```

A matte surface scatters light equally in all directions, so how bright it
looks depends only on how much light falls on it. Light arriving at an angle
$\theta$ from the normal spreads over $1/\cos\theta$ times the area, so the
brightness goes as $\cos\theta = \mathbf{n}\cdot\mathbf{L}$ for unit vectors
(Lambert's law). Negative values mean the light is behind the surface, so
they are clamped to 0:

$$
\mathrm{diffuse} = \mathrm{facing} \cdot \max(\mathbf{n} \cdot \mathbf{L},\ 0) .
$$

This uses the bent normal, so each bump is brighter on the side facing the
light.

```{figure} ../images/guide/view-diffuse.png
:alt: The front face in grey, with each rivet bright on one side and shaded on the other

View 3, `diffuse`, as grey. The rivets are lit on the side towards the light.
```

### Specular highlight

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: vec3 toCamera = normalize
:end-at: float specular = diffuse
```

A glossy surface also reflects light like a mirror, so you see a highlight
where the surface reflects the light into the camera. With $\mathbf{V}$ the
unit vector towards the camera, that happens when the normal bisects
$\mathbf{L}$ and $\mathbf{V}$, that is, when $\mathbf{n}$ equals the
**halfway vector**

$$
\mathbf{H} = \operatorname{normalize}(\mathbf{L} + \mathbf{V}) .
$$

The Blinn-Phong model measures how close the normal is to $\mathbf{H}$ and
narrows the result with an exponent:

$$
\mathrm{specular} =
\begin{cases}
\mathrm{facing} \cdot \max(\mathbf{n} \cdot \mathbf{H},\ 0)^{32} & \text{if diffuse} > 0, \\
0 & \text{otherwise.}
\end{cases}
$$

The larger the exponent, the smaller and sharper the highlight. With 32,
it falls to half when $\mathbf{n}\cdot\mathbf{H} = 0.5^{1/32} \approx 0.979$,
about $12°$ between $\mathbf{n}$ and $\mathbf{H}$. The `diffuse > 0` test
stops a highlight on a point the light does not reach.

Unlike the diffuse term, the specular term depends on where the camera is.
`toCamera` is computed per fragment from `worldPosition`, so it differs
slightly across a face.

```{figure} ../images/guide/view-specular.png
:alt: The front face nearly white, with a dark ring around each rivet

View 5, `specular`, as grey. Under this light the flat plate reflects almost
straight into the camera, so it is close to white; the sides of each rivet
lean away from $\mathbf{H}$ and go dark.
```

### The final colour

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: vec3 result = albedo
:end-at: vec3 result = albedo
```

$$
\mathrm{result} = \mathrm{albedo} \cdot (0.2 + 0.8\,\mathrm{diffuse}) + 0.3\,\mathrm{specular} .
$$

- **0.2** is ambient light, a stand-in for light bounced from the
  surroundings, so faces turned away from the light are dim rather than
  black.
- **0.8 × diffuse** is the direct light; fully lit, ambient plus diffuse
  is 1, the albedo itself.
- **0.3 × specular** is added as grey, the same in all three channels,
  rather than multiplied by the albedo, so highlights take the light's
  colour (white) instead of the surface's. Where the sum exceeds 1, the
  framebuffer clamps it.

Nothing in the pipeline converts between sRGB and linear light. The textures
are stored as `GL_RGBA8`, not an sRGB format, and the shader writes `result`
to `fragColor` unchanged, so the colours in {py:mod}`textures` are display
values that the lighting multiplies as if they were linear. Physically based
shading would decode them to linear light, light them, and encode the result
for display; skipping that, a common simplification, makes partly lit areas
look darker than the formulas above suggest, since the display treats the
output as sRGB.

```{figure} ../images/guide/view-final.png
:alt: The lit cube: a bright riveted front face with a highlight, dim brick and tile faces

View 0, `final`: the colour the program draws. The brick and tile faces get
only the ambient term, because the facing gate turns their direct light off.
```

### The debug views

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: if (view == 1)
:end-at: fragColor = vec4(result, 1.0);
```

Every term is computed for every view, and `view` only chooses which one is
written; view 0 keeps the final colour. The names, in index order, are in
`shaders.CUBE_VIEWS`:

```{literalinclude} ../../src/shaders.py
:language: python
:start-at: CUBE_VIEWS = (
:end-at: CUBE_VIEWS = (
```

The value comes from {py:attr}`context.SceneContext.cube_view`, which starts
at `config.DEFAULT_CUBE_VIEW` (0). No mouse control changes it; to see a
stage in the running program, set `DEFAULT_CUBE_VIEW` to its index. The view
survives a double-click reset, which restores only the rotation, zoom, pan
and light.

## The overlay shaders

The sphere grid, the axes and the light dot share one simpler program.

```{literalinclude} ../../src/shaders.py
:language: glsl
:start-after: OVERLAY_VERTEX_BODY = """
:end-before: '"""'
```

The vertex shader projects each vertex as the cube's does, and passes on its
colour and rotated position. `gl_PointSize` sets the size in pixels of a
point drawn with `GL_POINTS`; only the light dot is drawn that way, at
`config.LIGHT_DOT_SIZE` (14) times the screen's pixel ratio.

```{literalinclude} ../../src/shaders.py
:language: glsl
:start-after: OVERLAY_FRAGMENT_BODY = """
:end-before: '"""'
```

- **Round points.** A point is drawn as a square. `gl_PointCoord` runs from
  0 to 1 across that square, so `length(gl_PointCoord - vec2(0.5))` is the
  distance from its centre. `discard` drops every fragment farther than 0.5,
  which leaves a disc. `roundPoint` is on only for the light dot.
- **Near and far sides.** The grid lines lie on a sphere centred on the
  origin, so a point's position $\mathbf{P}$ is also the direction of the
  sphere's outward normal there. The point is on the near side when that
  normal faces the camera $\mathbf{C}$:
  $\mathbf{P} \cdot (\mathbf{C} - \mathbf{P}) > 0$. Near-side lines are drawn
  light grey (0.82) and far-side lines dark grey (0.32); the vertex colour is
  ignored. `sideShading` is on only for the grid.
- **Opacity.** `opacity` becomes the alpha, and blending mixes the fragment
  over what is already drawn: `config.SPHERE_OPACITY` (0.30) for the grid,
  1 for the axes, and for the light dot first `config.HIDDEN_OPACITY` (0.35)
  without depth testing, so it shows faintly through the cube, then 1 with
  depth testing.

The overlay is drawn after the cube, and the grid does not write depth; the
[diagrams](../diagrams.rst) page shows the whole frame.

## One pixel, start to finish

Follow one fragment on the brick face, at the model-space point
$(1,\ 0.2,\ -0.475)$ on the +X face. The numbers that depend only on the
formulas are exact; those that depend on the noise are given for a noise value
of 0.5, the middle of its range.

1. **Vertices.** The point lies on the +X face, layer 0, whose tangent is +Y
   and bitangent +Z. Its corners have $u = (y + 1)/2$ and $v = (z + 1)/2$,
   and both are linear across the face, so the interpolated coordinates
   are $u = 0.6$, $v = 0.2625$, layer 0.
2. **Cell.** In the brick lattice, $v \cdot 8 = 2.1$: row 2, an even row, so
   no stagger; $f_y = 0.1$. And $u \cdot 4 = 2.4$: column 2, $f_x = 0.4$. In
   the 512 px texture this is near row 134 and column 307; the filters blend
   the texels around it, so the shader sees a slightly smoothed version of
   the values below.
3. **Distance and mask.** $\operatorname{seam}(0.4)/4 = 0.1$ and
   $\operatorname{seam}(0.1)/8 = 0.0125$, so $d = 0.0125$: the long edge of
   the brick is the nearer. That is on the bevel, between 0.008 and 0.02:
   $t = (0.0125 - 0.008)/0.012 = 0.375$ and
   $m = 0.375^2 (3 - 2 \times 0.375) \approx 0.316$.
4. **Colour.** The colour is $\operatorname{mix}(\text{mortar},
   \text{brick}, 0.316)$, about two-thirds mortar grey and one-third this
   brick's red.
5. **Height and normal.** Across the bevel $d = v - 0.25$, so
   $\partial d / \partial v = 1$, and the slope of the smoothstep is
   $6t(1 - t)/0.012 \approx 117$. With the noise at 0.5 and its own slope
   ignored, $\partial h/\partial v \approx 117 \times 0.925 \approx 108$,
   and $\partial h/\partial u \approx 0$.
   The tangent-space normal is
   $\operatorname{normalize}(0,\ -0.03 \times 108,\ 1) \approx
   (0,\ -0.96,\ 0.29)$: the bevel faces steeply towards $-v$, down into the
   joint, about $73°$ from the face normal.
6. **Upload.** That normal is stored as $\tfrac{1}{2}\mathbf{n} +
   \tfrac{1}{2} \approx (0.5,\ 0.02,\ 0.65)$, bytes (128, 6, 165), in
   layer 0 of the normal map, and the colour in layer 0 of the albedo.
7. **Back to world space.** The shader decodes $\mathbf{s} \approx
   (0, -0.96, 0.29)$ and forms $0 \cdot \mathbf{T} - 0.96\,\mathbf{B} +
   0.29\,\mathbf{N}$. In model space $\mathbf{T} = +Y$, $\mathbf{B} = +Z$ and
   $\mathbf{N} = +X$, so $\mathbf{n} \approx (0.29,\ 0,\ -0.96)$ before the
   cube's rotation: the bevel faces mostly towards −Z.
8. **Lighting.** If the light is on the +X side of the cube far enough that
   $\mathbf{N}\cdot\mathbf{L} \ge 0.1$, `facing` is 1. The diffuse term is
   then $\max(\mathbf{n}\cdot\mathbf{L}, 0)$: bright when the light also
   comes from the −Z side, black when it comes from +Z. This is why each
   joint shows one bright and one dark edge. If the face is turned away from
   the light, `facing` is 0 and the fragment gets only
   $0.2 \times \mathrm{albedo}$, whatever its normal.
9. **Output.** `fragColor` is $\mathrm{albedo}\,(0.2 + 0.8\,\mathrm{diffuse}) +
   0.3\,\mathrm{specular}$ with alpha 1, written to the framebuffer if the
   depth test passes.
