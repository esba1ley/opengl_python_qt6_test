# The window and the event loop

Before anything is drawn, the program has to open a window, get an OpenGL
context from the operating system and wait for the user to do something.
Qt does most of that work. This page follows the program from `main()` to
the first frame, then shows what happens when the mouse moves, and how the
self-test drives the same code without a user.

Three modules are involved: {py:mod}`main` starts the program,
{py:mod}`widget` holds the window, and {py:mod}`selftest` replaces the user
when `--check` is given.

```{uml} ../diagrams/startup.puml
---
caption: >-
  From main() to the first frame. Everything above the divider runs in
  main(); everything below it runs inside the event loop, after Qt has
  created the OpenGL context.
---
```

(guide-surface-format)=
## Asking for an OpenGL version: `request_surface_format`

The first thing {py:func}`main.main` does is call
{py:func}`main.request_surface_format`:

```{literalinclude} ../../src/main.py
:language: python
:pyobject: request_surface_format
:start-at: surface = QSurfaceFormat()
:dedent: 4
```

A `QSurfaceFormat` is a list of requests for the surface OpenGL will draw on: which OpenGL version, which profile, how many
bits of depth, and so on. A default-constructed one asks for OpenGL 2.0.

- On macOS (`sys.platform == "darwin"`) it asks for OpenGL 4.1 with the
  **core profile**. The core profile leaves out the functions OpenGL 3.0
  marked as deprecated. As the comment says, macOS gives only OpenGL 2.1
  unless a core profile is requested.
- Elsewhere it asks for **OpenGL ES** 3.1. OpenGL ES ("OpenGL for Embedded
  Systems") is a separate, smaller variant of OpenGL. The development
  machine, a Raspberry Pi, reaches OpenGL ES 3.1 but desktop OpenGL only
  3.1, whose shading language stops at GLSL 1.40.

`QSurfaceFormat.setDefaultFormat` makes this the format every OpenGL
context and widget uses unless it is given another one. The widget below
starts from it.

This call comes before the `QApplication` exists, and the order matters.
Qt's documentation for `QOpenGLWidget` says that setting the default format
before the application is constructed is mandatory on some platforms, macOS
among them, when a core profile is requested. Qt creates contexts of its own,
and setting the format first means they are all created with the same version
and profile, which keeps the sharing of resources between them working.

The request is only a request. The context Qt creates may have a different
version, and the program reads the version it actually got when it builds its
shaders; [the next page](context.md) explains how.

`tools/offscreen.py` and `tests/conftest.py` call the same function, so the
images in this manual and the tests draw with the same kind of context as
the window.

(guide-main)=
## Starting the application: `main`

```{literalinclude} ../../src/main.py
:language: python
:pyobject: main
:start-at: request_surface_format()
:dedent: 4
```

Line by line:

- `QApplication(sys.argv)` creates the application object. A Qt GUI program
  has exactly one. Its constructor sets up the connection to the window
  system and receives the command-line arguments, from which Qt removes the
  options it recognises, such as `-platform`. `--check` is not one of them.
- `app.setWindowIcon(...)` sets the default icon for every window of the
  application, from `icon.png` at the top of the repository
  (`main.ICON_PATH`).
- `CubeWidget()` builds the widget, described in the next section. It has
  no parent widget, and a widget without a parent is a window of its own.
- `widget.show()` shows it. Nothing is drawn yet: drawing needs the event
  loop, which has not started.
- With `--check` on the command line, `QTimer.singleShot(1000, ...)` asks Qt
  to call {py:func}`selftest.check` once, 1000 milliseconds later. Timers
  need a running event loop, so the call happens inside `app.exec()`, about
  a second after the window was shown.
- `app.exec()` runs the **event loop** and only returns when the program is
  about to end.

The event loop is what a GUI program does most of the time. It waits for
something to happen: a key or mouse event from the window system, a timer
running out, a request to repaint a widget. Each one becomes an event object,
and Qt delivers it to the widget it concerns by calling one of that widget's
methods. Then the loop waits again. It stops when `exit()` is called, or, by
default, when the last window is closed. `exec()` then returns the status
passed to `exit()`; closing the last window quits with status 0, which means
success.

The last lines of `main.py` hand that status to the operating system:

```{literalinclude} ../../src/main.py
:language: python
:start-at: if __name__ == "__main__":
```

`sys.exit(main())` makes the program's exit status the event loop's, which
is how `python3 src/main.py --check` reports success or failure to the shell.

(guide-widget)=
## The widget: `CubeWidget`

{py:class}`widget.CubeWidget` is a subclass of `QOpenGLWidget`, Qt's widget
for drawing with OpenGL. A `QOpenGLWidget` does not draw into the window
directly. It renders into a **framebuffer object**, an off-screen image
that OpenGL draws into like a window, and the window then composites that
image with the rest of its contents. The self-test reads its frames back
from this framebuffer ({ref}`guide-selftest`).

### The constructor

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.__init__
:start-at: super().__init__()
:dedent: 8
```

- `setWindowTitle` and `resize(640, 640)` set the title bar and the size of
  the window's contents, 640 by 640 pixels.
- `QSurfaceFormat.defaultFormat()` returns a copy of the format set by
  `request_surface_format`, so the version and profile carry over. Two
  requests are added to it:
  - `setDepthBufferSize(24)` asks for a **depth buffer** of at least 24 bits
    per pixel. The depth buffer stores, for each pixel, how far away the
    surface drawn there is, so that a nearer triangle hides a farther one
    whatever order they are drawn in. Qt's documentation says that without a
    non-zero request there is no guarantee of a depth buffer; without one,
    each face of the cube would simply cover the ones drawn before it, as the
    comment in the code says. 24 bits is the common choice.
  - `setSamples(4)` asks for **multisampling** with 4 samples per pixel.
    OpenGL then samples every triangle and line at 4 points in each pixel
    instead of one, and resolves the 4 samples into the pixel's colour. This
    is antialiasing: it smooths the jagged edges of the cube and of the
    grid's thin lines. Where multisampling is not supported the request may
    be ignored.
- `setFormat(surface)` gives the widget this format, which Qt uses when it
  creates the widget's context. It has to be called before the widget is
  shown.
- The last four lines create the program's own objects: the scene state
  ({py:class}`context.SceneContext`), the two renderers
  ({py:class}`cube.CubeRenderer`, {py:class}`overlay.OverlayRenderer`), and
  the last mouse position. None of them touches OpenGL yet, because there is
  no context yet.

(guide-gl-overrides)=
### The three OpenGL methods

A `QOpenGLWidget` subclass overrides three methods, and Qt calls each of them
with the widget's context **current**, meaning that OpenGL calls made inside
them act on this widget's context. Outside these three methods the widget
would have to call `makeCurrent()` first, which this program never needs to.

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.initializeGL
:start-at: print(
:dedent: 8
```

`initializeGL` is called once, before the first `resizeGL` or `paintGL`. It
is the first call with the context current, so this is where the renderers
build their shader programs, textures and vertex buffers
({py:meth}`cube.CubeRenderer.initialize`,
{py:meth}`overlay.OverlayRenderer.initialize`; the part of the startup
diagram below the divider). The framebuffer is not ready yet, so nothing is
drawn here.

The three `print` lines report what the program got. `glGetString` returns
a string from the OpenGL implementation: `GL_RENDERER` names the renderer,
typically the GPU; `GL_VERSION` is the OpenGL version, here followed by the
driver's own; `GL_SHADING_LANGUAGE_VERSION` is the version of GLSL, the
language the shaders are written in. On a Mac with an M4 chip they read:

```
Renderer: Apple M4
Version:  4.1 Metal - 90.5
GLSL:     4.10
```

PyOpenGL returns them as bytes, hence `.decode()`. They are the first thing
to look at when the program fails on a new machine.

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.resizeGL
:start-at: self.ctx.aspect_ratio
:dedent: 8
```

`resizeGL(width, height)` is called whenever the widget changes size,
including once when it first appears. The two numbers are the widget's
`width()` and `height()`, which Qt gives in **device-independent pixels**.
On a high-density screen one of those covers several physical pixels: a
640-pixel-wide widget at a device pixel ratio of 2 is 1280 physical pixels
wide. The widget records two things for the renderers:

- `aspect_ratio`, width divided by height, which the projection matrix needs
  so the cube is not stretched. `max(height, 1)` avoids dividing by zero for
  a window shrunk to no height. The ratio is the same in either kind of
  pixel.
- `pixel_ratio`, the device pixel ratio, which the overlay uses to make the
  light dot the same apparent size on any screen.

There is no `glViewport` call here. Qt calls `glViewport` itself before every
`paintGL`, with the widget's size multiplied by the device pixel ratio, so the
viewport covers the whole framebuffer in physical pixels.

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.paintGL
:start-at: GL.glEnable
:dedent: 8
```

`paintGL` is called whenever the widget needs painting. By the time it runs,
Qt has made the context current, bound the widget's framebuffer object and
set the viewport, and done nothing else: no clearing, no other state. So the
method turns on depth testing, clears the colour buffer to
`config.BACKGROUND_COLOR` and clears the depth buffer, and asks the two renderers
to draw, cube first. The renderers read everything they need from
`self.ctx`. A later page follows one frame through both renderers.

(guide-mouse)=
## Mouse input

```{uml} ../diagrams/mouse.puml
---
caption: >-
  Mouse input. Each handler changes the SceneContext and calls update();
  Qt calls paintGL() later, from the event loop.
---
```

Qt delivers mouse events by calling methods on the widget under the
pointer. `CubeWidget` overrides four of them. The press handler is one line,
`self.last_pos = event.position()`. The other three:

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.mouseMoveEvent
:start-at: delta = event.position()
:dedent: 8
```

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.wheelEvent
:start-at: self.ctx.zoom_by
:dedent: 8
```

```{literalinclude} ../../src/widget.py
:language: python
:pyobject: CubeWidget.mouseDoubleClickEvent
:start-at: self.ctx.reset_view()
:dedent: 8
```

- `mousePressEvent` only remembers where the pointer was.
  `event.position()` is the position relative to the widget, in
  device-independent pixels, as a `QPointF`.
- `mouseMoveEvent` is called when the pointer moves while a button is held
  (the widget does not turn on mouse tracking, so it gets no moves without a
  button). It measures the movement since the last event, stores the new
  position, and passes the movement to one {py:class}`~context.SceneContext`
  method chosen by the button held: `rotate_by` for the left button,
  `move_light_by` for the right, `pan_by` for the middle. `event.buttons()`
  is the set of buttons held during the move, tested with `&`.
- `wheelEvent` zooms. `angleDelta().y()` is the wheel's turn in eighths of
  a degree; most mice turn in steps of 15 degrees, which is 120, so dividing
  by 120 gives notches.
- `mouseDoubleClickEvent` resets the view and the light. The widget also
  receives the press and release events of both clicks; the presses only set
  `last_pos`.

Every handler that changes the scene ends with `self.update()`. `update()`
does not paint. It schedules a paint event, which Qt processes when control
returns to the event loop, and that paint event calls `paintGL`. Calling
`update()` several times before then normally gives a single paint. So if
several move events arrive before the next paint, each one changes the
`SceneContext` and asks for a repaint, and one frame draws the result of all
of them.

The widget keeps no scene state of its own. It translates input into
`SceneContext` calls and the renderers draw from the `SceneContext`, so the
widget, the renderers and the self-test only meet through that one object;
the next pages describe what it holds.

(guide-selftest)=
## The self-test: `selftest.check`

`python3 src/main.py --check` runs {py:func}`selftest.check` from the timer
set in `main`. It plays the part of the user:

```{literalinclude} ../../src/selftest.py
:language: python
:pyobject: send_drag
:start-at: no_modifier =
:dedent: 4
```

`send_drag` builds the three events a real drag produces, a press, a move
and a release, as `QMouseEvent` objects, and hands each one to
`QApplication.sendEvent`. `sendEvent` delivers an event directly to the
widget, without going through the event loop's queue, so the widget's
handler has run when it returns. For a move event the `button` argument is
`NoButton`, as Qt expects, and the held button goes in `buttons`.
{py:func}`selftest.send_wheel` does the same with one `QWheelEvent`.

`check` then compares frames:

```{literalinclude} ../../src/selftest.py
:language: python
:pyobject: check
:start-at: frames = [
:end-at: frames.append(("pan"
:dedent: 4
```

`widget.grabFramebuffer()` renders a frame and returns it as a `QImage`. It
reads the pixels back from the GPU with `glReadPixels`, which can be slow,
but it means the test
sees exactly what `paintGL` drew, without waiting for the event loop to
repaint. The test checks that the light dot is yellow where it should be,
that each of the four controls changes the image, and that a double-click
restores the first image exactly.

```{literalinclude} ../../src/selftest.py
:language: python
:pyobject: check
:start-at: restored =
:dedent: 4
```

`QApplication.exit(status)` tells the event loop to stop. `app.exec()` in
`main` then returns `status`, and `sys.exit` passes it on: 0 if every check
passed, 1 otherwise.
