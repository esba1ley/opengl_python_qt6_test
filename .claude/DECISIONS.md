# Decisions

Newest first.

## 2026-11-01 — Gate bump lighting on the geometric face normal
**Status:** Accepted
**Context:** The cube fragment shader lit each pixel from the normal-mapped
normal alone. On a face turned away from the directional light, bumps sloping
towards the light still received diffuse and specular light, so rivet rims and
mortar edges glowed inside the cube's own shadow.
**Decision:** Multiply diffuse and specular by
`smoothstep(0.0, 0.1, dot(faceNormal, lightDirection))` in
`CUBE_FRAGMENT_BODY`. A convex cube cannot shadow itself any other way under
parallel light, so the face normal alone decides whether a face is lit.
**Consequences:** Shadowed faces show only the ambient term. The 0.1 fade
width avoids a hard seam at the terminator and follows the shader's existing
hard-coded lighting constants. Rejected: shadow mapping (no occluder other
than the cube itself, so pointless); horizon mapping to self-shadow bumps
within a lit face (large change, needs per-material horizon textures).

## 2026-11-01 — Request the newest OpenGL per platform, derive GLSL version at run time
**Status:** Accepted
**Context:** The goal was the most advanced OpenGL on both the Raspberry Pi 5
and macOS with minimal code differences. The platforms share no context
version: macOS offers desktop GL up to 4.1 core and no OpenGL ES; Mesa's V3D
stops at desktop GL 3.1 but reaches OpenGL ES 3.1. A single `#version 300 es`
shader set was ruled out because macOS cannot compile it.
**Decision:** `main.py` requests 4.1 core on macOS and OpenGL ES 3.1
elsewhere, the only platform test in the program. `gl_utils.glsl_header`
builds the `#version` line from the created context's major and minor version
instead of fixed strings, and on ES declares `highp float` and
`lowp sampler2DArray` precision, since GLSL ES gives neither a default in
fragment shaders. Shader bodies stay unchanged and limited to GLSL 1.40
features so one source serves every header.
**Consequences:** macOS now compiles the shaders as GLSL 4.10 and `--check`
passes. The Pi will compile them as GLSL ES 3.10 once verified; if Qt refuses
the ES request the header falls back to whatever desktop version is granted.
Risk: PyOpenGL's desktop `GL` module may not dispatch under an EGL ES context;
the fallback is routing imports through PyOpenGL's `GLES3` module. Rejected:
GLSL 1.40 everywhere (already the state, but not the newest driver path on
the Pi); ES 3.00 on both (impossible on macOS); hard-coded per-platform
headers (fail instead of degrade when a platform grants less).

## 2026-11-01 — Request a core profile only on macOS
**Status:** Superseded by 2026-11-01 — Request the newest OpenGL per platform
**Context:** On macOS, Qt's default surface format yields a legacy OpenGL 2.1
context, which rejects `#version 140` shaders. The Raspberry Pi target offers
OpenGL 3.1 and no 3.2 core context, so an unconditional 3.2 core request could
break it.
**Decision:** In `main.py`, when `sys.platform == "darwin"`, set a default
`QSurfaceFormat` with version 3.2 and `CoreProfile` before constructing
`QApplication`. Make `widget.py` start from `QSurfaceFormat.defaultFormat()`
instead of a blank format so the request is not overwritten.
**Consequences:** Shaders stay at GLSL 1.40, so the Pi path is unchanged.
macOS reports GL 4.1 core and all `--check` tests pass. Wider axis lines are
ignored by Apple's core profile. Rejected: raising the shader version to 1.50
(breaks the Pi); setting the profile in the widget only (Qt's shared context
on macOS is created from the default format, so the two must match).
