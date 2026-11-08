# One frame

The earlier pages built everything a frame needs: the programs, the
textures, the vertex buffers and the matrices. This page follows one call to
`paintGL` from the clear to the last point drawn. It draws four things, in a
fixed order: the cube, the sphere grid, the axes and the light dot. The
pictures below show the frame after each of them.

```{uml} ../diagrams/frame.puml
---
caption: >-
  One call to paintGL(). The cube renderer draws first, then the overlay
  renderer draws the grid, the axes and the light dot.
---
```

(guide-frame-clear)=
## Starting the frame: `paintGL`

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.paintGL
:start-at: GL.glEnable
:dedent: 8
```

Qt binds the widget's framebuffer and sets the viewport before calling
`paintGL`, and sets nothing else ({ref}`guide-gl-overrides`). Its
documentation also warns that state set in `initializeGL` may not persist.
So the frame sets what it needs itself.

- `glEnable(GL_DEPTH_TEST)` turns on the depth test. Every capability except
  dithering and multisampling starts off. With the test on, a fragment is
  kept only if it is nearer than what the depth buffer holds at its pixel
  (the comparison is `GL_LESS`, the initial one, which the program never
  changes), and its depth is then written there.
- `glClear` clears **both** buffers. Qt does no clearing, so without the
  colour clear the frame would be drawn over whatever the framebuffer held.
  The depth clear matters as much: it sets every pixel's depth to 1.0, the
  far end of the range, so the first fragment at each pixel passes the test.
  Depths left from the previous frame would hide parts of this one.
- The clear colour is `config.BACKGROUND_COLOR`, black, with alpha 1. The
  frame starts opaque, and the overlay keeps it that way (below).

Then the two renderers draw, each from the same
{py:class}`~context.SceneContext`.

(guide-frame-cube)=
## The cube: `CubeRenderer.paint`

```{literalinclude} ../../src/cube.py
:language: python
:pyobject: CubeRenderer.paint
:start-at: model = ctx.model_matrix()
:dedent: 8
```

`glUseProgram` makes the cube's program current, and the next five calls set
its uniforms ({ref}`guide-setting-uniforms`):

- `mvp` is `ctx.view_projection_matrix() * model`, model space to clip space,
  and `model` the model matrix alone ({ref}`guide-matrices`).
- `lightDirection` is `ctx.light`, the unit vector towards the light in world
  space, and `cameraPosition` is the camera in world space
  ({ref}`guide-scene-context`, {ref}`guide-matrices`).
- `view` is `ctx.cube_view`, the debug view to draw; 0 is the lit colour
  ([the debug views](shaders.md#the-debug-views)).

Next come the textures. `glActiveTexture(GL_TEXTURE0)` selects texture unit
0, and `glBindTexture` puts the albedo array on it; unit 1 gets the normal
maps. The samplers `albedoMap` and `normalMap` were told once, in
`init_textures`, to read units 0 and 1 ({ref}`guide-texture-arrays`), so
only the bindings are made here. The last `glActiveTexture` makes unit 0
active again, its initial setting.

Last, binding the VAO restores the vertex layout, and
`glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)` draws the 36 vertices as
12 triangles ({ref}`guide-cube-buffer`). The vertex shader places them, and
the fragment shader lights every pixel they cover ([the shaders](shaders.md)).
Blending is off, so each fragment that passes the depth test replaces the
colour under it, with the alpha of 1 that the shader writes.

```{figure} ../images/guide/frame-1-cube.png
:alt: The lit cube alone on black: rivets in front, bricks on the right, tiles on top

The frame after `CubeRenderer.paint`, at the default view and light. Each
frame image on this page is a 240-pixel render of the whole window.
```

(guide-frame-overlay)=
## The overlay: `OverlayRenderer.paint`

```{literalinclude} ../../src/overlay.py
:language: python
:pyobject: OverlayRenderer.paint
:start-at: locs = self.locs
:dedent: 8
```

The grid, the axes and the light dot share one program and one VAO, so both
are bound once ({ref}`guide-overlay-buffer`). Two uniforms are the same for
all three parts and are set here: `cameraPosition`, which the fragment shader
uses to tell the near side of the sphere from the far side, and `pointSize`,
the dot's size in physical pixels ([the overlay shaders](shaders.md#the-overlay-shaders)).
Each `paint_` method then sets the rest.

(guide-frame-blend)=
### Blending: `glBlendFuncSeparate`

With `GL_BLEND` on, a fragment's colour is not written as it is: it is
combined with the colour already in the framebuffer. Write $C_s$, $a_s$ for
the fragment's colour and alpha (the shader's `opacity`), and $C_d$, $a_d$
for what the framebuffer holds. `glBlendFuncSeparate` takes four factors,
two for the colour and two for the alpha:

$$
C = a_s\,C_s + (1 - a_s)\,C_d , \qquad a = 0 \cdot a_s + 1 \cdot a_d = a_d .
$$

The colour is the usual "over" mix: a grid line at opacity 0.3 is 30% grey
and 70% of what was there; at opacity 1 the fragment replaces it. The alpha
in the framebuffer is kept as it was, 1 everywhere.

The more common `glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)` uses the
colour factors for the alpha too, and a grid line would then leave
$a = 0.3^2 + 0.7 = 0.79$. The widget's framebuffer has an alpha channel (a
`QOpenGLFramebufferObject` is `GL_RGBA8` by default, `GL_RGBA` on OpenGL ES),
so the frame would become partly transparent wherever the overlay is drawn.

That alpha does not stay inside OpenGL. The images in this manual are read
from a `QOpenGLFramebufferObject` with `toImage()`, which returns a
premultiplied ARGB image, alpha included, and `tools/` saves it as PNG.
Rendered with `glBlendFunc` instead, 13,113 pixels of a 480 × 480 frame had
alpha below 1, the lowest about 0.42; with `glBlendFuncSeparate` none did.
In the window, Qt draws the widget's texture into the window without
blending, alpha and all (`QBackingStoreDefaultCompositor::flush` in
`qbackingstoredefaultcompositor.cpp`, Qt 6.11.2); what then shows depends on
the window system. Keeping the destination alpha keeps the frame opaque in
both.

(guide-frame-grid)=
### The grid: `paint_grid`

```{literalinclude} ../../src/overlay.py
:language: python
:pyobject: OverlayRenderer.paint_grid
:start-at: locs = self.locs
:dedent: 8
```

The grid uses the model matrix, the same as the cube, so it turns with it
({ref}`guide-matrices`); `model` also gives the fragment shader the world
position it needs for the near-and-far test. `sideShading` on picks the
grey, `roundPoint` off leaves lines alone, and `opacity` is
`config.SPHERE_OPACITY`, 0.30.

The depth test is still on, so the cube hides the far-side lines behind it.
`glDepthMask(GL_FALSE)` stops the grid **writing** depth; it does not turn
the test off. Without it, every grid line would write its depth, and the
axes and the dot, drawn after it, would fail the depth test wherever a
near-side line crosses in front of them: small gaps cut out of the axes and
the dot, even though the line is 70% transparent. Drawn with the mask left
on, 253 pixels of a 480 × 480 frame changed, all of them on the axes and the
dot, the only things drawn after the grid.

`glDepthMask(GL_TRUE)` turns writing back on. The axes and the dot need it,
and so does the next frame's clear, since `glClear` obeys the write masks.

```{figure} ../images/guide/frame-2-grid.png
:alt: The cube inside a faint wire sphere, with the lines brighter in front of the cube

The grid added. Near-side lines cross in front of the cube, light grey;
far-side lines show only beside the cube, darker, and the lines converge at
the +Z pole, lower left.
```

(guide-frame-axes)=
### The axes: `paint_axes`

```{literalinclude} ../../src/overlay.py
:language: python
:pyobject: OverlayRenderer.paint_axes
:start-at: locs = self.locs
:dedent: 8
```

The axes use the model matrix too, so they stay fixed to the cube. `opacity`
is 1, so blending gives the fragment's colour unchanged. The depth test and
depth writes are both on: the axes run from the origin, and the part inside
the cube is hidden by the cube's faces, so each axis shows from the centre
of a face out to the sphere ({ref}`guide-axes-dot`).

The line width was fixed in `initialize`:

```{literalinclude} ../../src/overlay.py
:language: python
:pyobject: OverlayRenderer.initialize
:start-at: widest_line =
:dedent: 8
```

How wide a line can be is up to the implementation, which reports the
range in `GL_ALIASED_LINE_WIDTH_RANGE`. On a Mac with an M4 chip the 4.1 core
profile reports $[1, 1]$, and there `glLineWidth(2.0)` fails with
`GL_INVALID_VALUE`, which PyOpenGL raises as an exception. So the width is
`config.AXIS_LINE_WIDTH` (2) where the driver allows it, and 1 on that Mac. `glLineWidth(1.0)` afterwards puts back the initial width.

```{figure} ../images/guide/frame-3-axes.png
:alt: The same scene with a red, a green and a blue line leaving the cube's faces

The axes added: red $+x$ to the right, green $+y$ up, blue $+z$ towards the
lower left. Each starts at a face, not at the centre.
```

(guide-frame-light-dot)=
### The light dot: `paint_light_dot`

```{literalinclude} ../../src/overlay.py
:language: python
:pyobject: OverlayRenderer.paint_light_dot
:start-at: locs = self.locs
:dedent: 8
```

The dot's vertex is at the origin. Its transform is a translation to
`ctx.light_dot_position()`, where the direction to the light meets the
sphere, and `mvp` is the view-projection matrix times that translation,
with **no** model matrix ({ref}`guide-matrices`). The light is fixed in
world space, so turning the cube leaves the dot where it is; only a drag
with the right button, or a double-click reset, moves it
({ref}`guide-mouse-motion`). `roundPoint`
turns the square point into a disc.

The dot is drawn twice:

1. **Depth test off, opacity `config.HIDDEN_OPACITY` (0.35).** The dot is
   drawn over everything, 35% yellow. With the test off, the depth buffer is
   not written either. Where the dot is behind the cube, this faint disc is
   all that shows, so the light can be found even when it is behind.
2. **Depth test on, opacity 1.** Where nothing nearer is in the depth buffer,
   the solid dot replaces the faint one. Where the cube is in front, the test
   fails and the faint dot stays.

The second pass leaves the depth test on. `paint` then turns blending off and
unbinds the VAO.

```{figure} ../images/guide/frame-4-light-dot.png
:alt: The finished frame, with a yellow dot on the sphere above the cube's top right corner

The finished frame. Under the default light the dot is in front of the cube,
so the solid pass covers the faint one.
```

(guide-draw-order)=
## Why the order is fixed

The depth test sorts opaque surfaces by itself, whatever order they come
in. What it cannot sort is anything drawn without writing depth: the grid
and the dot's faint pass. Those blend with what is already in the
framebuffer, and anything drawn later may cover them. Hence:

- **The cube first.** Drawn after the grid, the cube covers the near-side
  lines in front of it, since they left no depth to stop it: about 3,200
  pixels of a 480 × 480 frame change.
- **The grid writes no depth**, or it cuts gaps in the axes and the dot
  drawn after it (above).
- **The light dot last**, at least after the cube. Drawn before the cube,
  the faint pass is painted over wherever the cube is in front, and a light
  behind the cube can no longer be found.
- **The axes after the grid.** This one changes little: drawn after the axes,
  the translucent near-side lines would lie over them where they cross,
  about 20 pixels of a 480 × 480 frame.

The transforms follow the same rule as the rest of the program: the cube,
the grid and the axes share `ctx.model_matrix()`, which keeps them together,
and the light dot ignores it.

When `paintGL` returns, Qt resolves the multisampled framebuffer
({ref}`guide-widget`) and composites the result into the window. Nothing
else is drawn until the next `update()` ({ref}`guide-mouse`).

## The same frame, one pixel at a time

This page followed the frame draw call by draw call. The shaders page
follows a single fragment of the same frame, from its texture coordinates to
the colour written here: {ref}`guide-one-pixel`.
