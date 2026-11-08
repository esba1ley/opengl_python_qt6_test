# How it works

Every surface on the cube is computed from numbers. No image file is loaded:
{py:mod}`textures` builds six materials with NumPy when the program starts,
{py:mod}`gl_utils` hands them to the GPU as textures, and the two shaders in
{py:mod}`shaders` turn them into lit pixels every frame. This chapter follows
that path from the first random number to the colour of one pixel. It
starts with the window and the OpenGL context the cube is drawn in.

It assumes you know Python and a little linear algebra (vectors, dot
products, a matrix acting on a vector), but nothing about GPU texturing.

## The pipeline

```{uml} ../diagrams/textures.puml
---
caption: >-
  From the seeded generator to a shaded pixel. The first two parts run once,
  when the cube renderer is initialised; the last runs on the GPU for every
  frame.
---
```

The work splits into two halves that never run at the same time.

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

| Stage | Where it lives | Page |
|---|---|---|
| Building blocks: coordinates, `smoothstep`, `mix`, noise, patterns | `src/textures.py` | [Primitives and patterns](primitives.md) |
| The six materials | `src/textures.py` | [The materials](materials.md) |
| Shared randomness, normal maps, packing | `src/textures.py` | [From arrays to GPU textures](gpu.md) |
| Texture arrays, mipmaps, filters | `src/gl_utils.py`, `src/cube.py` | [From arrays to GPU textures](gpu.md) |
| Each face's axes and texture layer | `src/geometry.py` | [Primitives](primitives.md), [The geometry](geometry.md) |
| Vertex and fragment shaders | `src/shaders.py` | [The shaders](shaders.md) |
| Fixed settings (`TEXTURE_SIZE`, `TEXTURE_SEED`, `BUMP_STRENGTH`) | `src/config.py` | wherever they are used |

## How to read the images

The pictures in this chapter are made by `tools/make_guide_images.py`. The
pattern and material images are generated at 512 pixels, the size the program
uses, and scaled down to 160 pixels; the views of the cube are 240 pixels.

They are drawn in **texture space**: $u$ runs to the right and $v$ runs down
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
