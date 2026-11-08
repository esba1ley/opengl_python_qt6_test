# How it works

This chapter follows the program from `main()` to the colour of one pixel.
It starts with the window and its event loop, then the OpenGL context and
the shader programs, the coordinate spaces and the camera, the geometry, and
the vertex buffers that carry it to the GPU. The second part builds the
textures, since every surface on the cube is computed from numbers and no
image file is loaded, and ends with the shaders that light them. The last
page follows one whole frame, from the clear to the last point drawn.

It assumes you know Python and a little linear algebra (vectors, dot
products, a matrix acting on a vector), but nothing about OpenGL or GPU
texturing.

## The path through the program

The work splits into what runs once and what runs every frame.

1. **Starting up, once.** {py:func}`main.main` asks for an OpenGL version,
   creates the application and the widget, and starts the event loop. When
   Qt has created the OpenGL context, `initializeGL` lets each renderer
   compile its shaders, build its textures and upload its vertices.
2. **Every frame.** Qt calls `paintGL` whenever the widget needs painting:
   for example when it is first shown or resized, and after a mouse event
   changes the {py:class}`~context.SceneContext` and asks for a repaint.
   `paintGL` clears the framebuffer and draws the cube, the sphere grid,
   the axes and the light dot from the scene state, through the matrices
   of the coordinate-spaces page.

| Stage | Where it lives | Page |
|---|---|---|
| Window, event loop, mouse input, self-test | `src/main.py`, `src/widget.py`, `src/selftest.py` | [The window and the event loop](window.md) |
| OpenGL context, GLSL version, shader programs, uniforms | `src/gl_utils.py` | [The OpenGL context and shader programs](context.md) |
| Scene state, matrices, mouse motion | `src/context.py` | [Coordinate spaces and the camera](spaces.md) |
| Cube vertices, sphere grid, axes | `src/geometry.py` | [The geometry](geometry.md) |
| Vertex buffers and vertex arrays | `src/cube.py`, `src/overlay.py` | [From arrays to vertex buffers](buffers.md) |
| Building blocks: coordinates, `smoothstep`, `mix`, noise, patterns | `src/textures.py` | [Primitives and patterns](primitives.md) |
| The six materials | `src/textures.py` | [The materials](materials.md) |
| Shared randomness, normal maps, packing | `src/textures.py` | [From arrays to GPU textures](gpu.md) |
| Texture arrays, mipmaps, filters | `src/gl_utils.py`, `src/cube.py` | [From arrays to GPU textures](gpu.md) |
| Vertex and fragment shaders | `src/shaders.py` | [The shaders](shaders.md) |
| One frame: draw order, blending, depth | `src/widget.py`, `src/cube.py`, `src/overlay.py` | [One frame](frame.md) |
| Fixed settings | `src/config.py` | wherever they are used |

## The textures part: from a seed to a pixel

```{uml} ../diagrams/textures.puml
---
caption: >-
  From the seeded generator to a shaded pixel. The first two parts run once,
  when the cube renderer is initialised; the last runs on the GPU for every
  frame.
---
```

The textures part has three steps:

1. **On the CPU, once.** {py:func}`textures.iter_materials` creates one
   random generator from `config.TEXTURE_SEED` and calls each material
   function in turn. A material combines a few small building blocks
   (coordinates, noise, soft thresholds, cell patterns) into two arrays: a
   colour image and a height field. {py:func}`textures.height_to_normals`
   turns each height field into a normal map, and
   {py:func}`textures.to_rgba_bytes` packs the images into bytes.
2. **Upload, once.** {py:func}`gl_utils.upload_texture_array` copies the
   colour images into one 2D array texture and the normal maps into
   another, and builds their mipmaps.
3. **On the GPU, every frame.** The vertex shader places each corner of the
   cube on screen and carries its face's axes along. The fragment shader then
   runs once per covered pixel: it reads the colour and the normal from the
   two textures, bends the face's normal by the normal map, and lights the
   result.

## How to read the images

The pictures in this chapter are made by `tools/make_guide_images.py`, and
are of three kinds:

- the pattern and material images, generated at 512 pixels, the size the
  program uses, and scaled down to 160 pixels;
- the views of the cube alone, one per debug view of the cube shader
  (the shading views on the shaders page, the geometry views on the geometry
  page), at 240 pixels;
- the frame build-up on the last page, 240-pixel renders of the whole window
  with the overlay's parts added one at a time.

The pattern and material images are drawn in **texture space**: $u$ runs to the right and $v$ runs down
the rows of the image, both from 0 to just under 1 (at most $(\text{size}-1)/\text{size}$). That is not how they appear on the
cube; [the primitives page](primitives.md) explains the difference.

A single-channel field is drawn as greyscale by one rule:

- a field whose values all lie in $[0, 1]$ and whose maximum is at least 0.5,
  such as a mask, is drawn as it is: 0 is black and 1 is white;
- a field whose maximum is below 0.5, such as a distance, is stretched so its
  minimum is black and its maximum is white (so is any field with values
  outside $[0, 1]$, though none of the images here has any). Captions say **stretched** when
  this happened, because the grey levels then show shape, not value;
- a colour image is drawn as RGB, with values clipped to $[0, 1]$.

To regenerate the images after changing a material or the cube shader, run
this from the repository root:

```
python3 tools/make_guide_images.py docs/images/guide
```

```{toctree}
:caption: The window and the scene
:maxdepth: 2

window
context
spaces
geometry
buffers
```

```{toctree}
:caption: Textures and shaders
:maxdepth: 2

primitives
materials
gpu
shaders
```

```{toctree}
:caption: A frame
:maxdepth: 2

frame
```
