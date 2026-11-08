# Coordinate spaces and the camera

A vertex is stored once, as numbers in the cube's own frame, and drawn at a
different place on screen every time the cube turns. Four matrices take it
there. This page names the frames they connect, shows how
{py:class}`context.SceneContext` builds each matrix from its state, and how
the mouse changes that state.

(guide-spaces-chain)=
## The chain of spaces

A point passes through these frames on its way to the screen:

- **Model space** is the frame the vertex data is written in. The cube spans
  $-1$ to $1$ on each axis, and the sphere grid and axes are centred on the
  same origin ([the geometry](geometry.md)).
- **World space** is the scene's fixed frame. The light direction is given
  in it, and so is the camera position. The model is rotated into it.
- **Camera space** is the frame of the eye. The camera sits at its origin
  and looks along $-z$, with $+x$ to the right and $+y$ up.
- **Clip space** is what the vertex shader writes to `gl_Position`: four
  numbers $(x, y, z, w)$ from which OpenGL decides what is visible.
- **Normalised device coordinates** (NDC) and **window coordinates** follow
  from clip space without any further matrix ({ref}`guide-after-clip`).

### Notation

A transform from frame $a$ to frame $b$ is written $T_{b\leftarrow a}$: the
"to" frame first, the "from" frame second. In prose and code font the same
matrix is `T_b_a`. Points are column vectors and matrices act on the left:

$$
\mathbf{p}_\text{world} = T_{\text{world}\leftarrow\text{model}}\,\mathbf{p}_\text{model} .
$$

So transforms compose with the rightmost applied first, and the inner frame
names cancel:

$$
T_{\text{clip}\leftarrow\text{model}} =
T_{\text{clip}\leftarrow\text{camera}}\,
T_{\text{camera}\leftarrow\text{world}}\,
T_{\text{world}\leftarrow\text{model}} .
$$

A point is extended to four components with $w = 1$, $(x, y, z, 1)$, so
that a $4 \times 4$ matrix can translate it as well as rotate it. A rotation
on its own is written $R_{b\leftarrow a}$, or `R_b_a`.

The code keeps its own names. Each `SceneContext` method returns one of
these matrices as a `QMatrix4x4`:

| Method | Matrix | Code-font name |
|---|---|---|
| `model_matrix()` | $T_{\text{world}\leftarrow\text{model}}$ | `T_world_model` |
| `view_matrix()` | $T_{\text{camera}\leftarrow\text{world}}$ | `T_camera_world` |
| `projection_matrix()` | $T_{\text{clip}\leftarrow\text{camera}}$ | `T_clip_camera` |
| `view_projection_matrix()` | $T_{\text{clip}\leftarrow\text{world}}$ | `T_clip_world` |

The renderers multiply them in the order of the equation above.
{py:meth}`cube.CubeRenderer.paint` sets the `mvp` uniform to
`ctx.view_projection_matrix() * model`, which is
`projection_matrix() * view_matrix() * model_matrix()`, that is
$T_{\text{clip}\leftarrow\text{model}}$. `QMatrix4x4`'s `*` is the ordinary
matrix product, so the code reads in the same order as the maths.

### In the vertex shader

The cube's vertex shader applies two of these matrices:

```{literalinclude} ../../src/shaders.py
:language: glsl
:dedent: 4
:start-at: gl_Position = mvp
:end-at: worldPosition = mat3(model) * position;
```

`mvp * vec4(position, 1.0)` is $T_{\text{clip}\leftarrow\text{model}}$
applied to the model-space point with $w = 1$: the vertex in clip space.
`mat3(model)` is the upper-left $3 \times 3$ block of
$T_{\text{world}\leftarrow\text{model}}$, which is
$R_{\text{world}\leftarrow\text{model}}$; it takes the position and the
face's axes to world space, where the lighting is done.
[The shaders page](shaders.md) explains why the $3 \times 3$ block is enough
here.

(guide-scene-context)=
## The scene state: `SceneContext`

{py:class}`context.SceneContext` holds everything that changes while the
program runs. The widget writes to it, the renderers read from it, and
neither knows about the other ({ref}`guide-mouse`).

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.__init__
:start-at: self.aspect_ratio
:dedent: 8
```

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.reset_view
:start-at: self.rotation =
:dedent: 8
```

`aspect_ratio` and `pixel_ratio` are set by the widget's `resizeGL`
({ref}`guide-gl-overrides`). `cube_view` picks a debug view of the cube
shader. `reset_view` sets the four values the mouse can change, and a
double-click calls it again. The defaults come from {py:mod}`config`:

```{literalinclude} ../../src/config.py
:language: python
:start-at: DEFAULT_DISTANCE = 6.0
:end-at: DEFAULT_LIGHT =
```

- `rotation` is a `QQuaternion`, the cube's orientation.
  `QQuaternion.fromEulerAngles(pitch, yaw, roll)` builds a rotation of
  `roll` degrees about $z$, then `pitch` about $x$, then `yaw` about $y$, in
  that order, as Qt's documentation states. With roll 0 the default is a
  tilt of 25° about $x$, towards the viewer at the top, followed by a turn
  of −35° about $y$, which brings the +X face into view on the right.
- `distance` is 6: the camera is 6 units from the origin.
- `pan` is zero: the origin is in the middle of the window.
- `light` is $(0.4, 0.7, 1.0)$ normalised, a unit vector *towards* the light
  in world space: up, to the right and in front.

`config` gives angles in degrees, with `_DEGREES` in the name, because Qt's
functions take degrees. The maths on this page uses radians only where it
says so.

(guide-matrices)=
## The four matrices

### Model: `model_matrix`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.model_matrix
:start-at: model = QMatrix4x4()
:dedent: 8
```

`QMatrix4x4()` is the identity, and `rotate(quaternion)` multiplies it on
the right by the rotation matrix of the quaternion. Qt's documentation
for `rotate` says the quaternion is assumed to be normalised. The result is a pure rotation,
with no translation and no scaling:

$$
T_{\text{world}\leftarrow\text{model}} =
\begin{bmatrix} R_{\text{world}\leftarrow\text{model}} & \mathbf{0} \\
\mathbf{0}^T & 1 \end{bmatrix} .
$$

The cube, the sphere grid and the axes all use this one matrix, which is
what keeps them together as the cube turns. At the default rotation, the
model's axes land in world space at

| Model axis | In world space |
|---|---|
| $+x$ | $(0.819,\ 0,\ 0.574)$ |
| $+y$ | $(-0.242,\ 0.906,\ 0.346)$ |
| $+z$ | $(-0.520,\ -0.423,\ 0.742)$ |

These are the columns of $R_{\text{world}\leftarrow\text{model}}$.

### View: `view_matrix`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.view_matrix
:start-at: view = QMatrix4x4()
:dedent: 8
```

The view matrix only translates:

$$
T_{\text{camera}\leftarrow\text{world}} =
\begin{bmatrix}
1 & 0 & 0 & p_x \\
0 & 1 & 0 & p_y \\
0 & 0 & 1 & -d \\
0 & 0 & 0 & 1
\end{bmatrix},
$$

with $d$ the distance and $(p_x, p_y)$ the pan. It moves the scene $d$ units
away along $-z$, in front of the camera, and sideways by the pan. **The
camera never rotates.** Its axes are always parallel to the world's: world
$+x$ points right on the screen, $+y$ up and $+z$ out of the screen towards
the viewer. All turning is done by the model matrix, and the light is turned
on its own ({ref}`guide-mouse-motion`).

The camera's own position in world space is where the camera-space origin
comes from. Solving $T_{\text{camera}\leftarrow\text{world}}\,\mathbf{c} =
\mathbf{0}$ undoes the translation:

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.camera_position
:start-at: return
:dedent: 8
```

At the defaults the camera is at $(0, 0, 6)$. The fragment shaders use it
for the specular highlight and to tell the near side of the sphere from the
far side ([the shaders](shaders.md)).

### Projection: `projection_matrix`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.projection_matrix
:start-at: projection = QMatrix4x4()
:dedent: 8
```

`QMatrix4x4.perspective(verticalAngle, aspectRatio, nearPlane, farPlane)`
multiplies the matrix by a perspective projection. Qt's documentation does
not print the matrix, so it was checked in Qt's source (`qmatrix4x4.cpp`,
`QMatrix4x4::perspective`) and numerically against the installed PyQt6. It
is the classic `gluPerspective` matrix. With $\theta$ the vertical field of
view, $f = \cot(\theta/2)$, $a$ the aspect ratio and $n$, $F$ the near and
far distances:

$$
T_{\text{clip}\leftarrow\text{camera}} =
\begin{bmatrix}
f/a & 0 & 0 & 0 \\
0 & f & 0 & 0 \\
0 & 0 & \dfrac{F + n}{n - F} & \dfrac{2Fn}{n - F} \\
0 & 0 & -1 & 0
\end{bmatrix} .
$$

Here $\theta$ = `config.FOV_DEGREES` = 45°, so $f = \cot 22.5° \approx
2.414$; $n$ = `NEAR_PLANE` = 0.1 and $F$ = `FAR_PLANE` = 100. The angle is
vertical, so the window's height always shows the same 45°, and a wider
window shows more to the sides: that is what dividing $x$ by $a$ does.

The bottom row is what makes the projection perspective. It sets
$w_\text{clip} = -z_\text{camera}$, the distance in front of the camera, and
dividing by $w$ later makes farther things smaller.

### Both at once: `view_projection_matrix`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.view_projection_matrix
:start-at: return
:dedent: 8
```

$T_{\text{clip}\leftarrow\text{world}} = T_{\text{clip}\leftarrow\text{camera}}\,
T_{\text{camera}\leftarrow\text{world}}$. Each renderer multiplies it on the
right by the transform of what it draws: the model matrix for the cube, the
grid and the axes, and a translation for the light dot.

### The light dot: `light_dot_position`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.light_dot_position
:start-at: return
:dedent: 8
```

The light is a direction, not a point, so it is marked where that direction
meets the sphere: the unit vector `light` times `config.SPHERE_RADIUS`
(1.85). The position is in world space, and
{py:meth}`overlay.OverlayRenderer.paint_light_dot` translates the dot there
without the model matrix, so the dot stays put when the cube turns.

### One corner, worked through

Take the cube's corner $(1, 1, 1)$ in model space, at the default view in a
square window.

1. **World.** $R_{\text{world}\leftarrow\text{model}}$ applied to $(1, 1, 1)$
   is the sum of the three columns above: $(0.057,\ 0.484,\ 1.662)$.
2. **Camera.** The view matrix subtracts 6 from $z$: $(0.057,\ 0.484,\
   -4.338)$. The corner is 4.338 units in front of the camera.
3. **Clip.** The projection gives
   $(0.137,\ 1.168,\ 4.146,\ 4.338)$: $x$ and $y$ multiplied by 2.414, and
   $w = 4.338$.
4. **NDC.** Dividing by $w$ gives $(0.032,\ 0.269,\ 0.956)$
   ({ref}`next section <guide-after-clip>`).

The same NDC comes from `mvp.map(QVector3D(1, 1, 1))`, which also divides
by $w$ ({ref}`guide-setting-uniforms`).

(guide-after-clip)=
## After clip space

The rest of the way is fixed-function, done by OpenGL without a matrix
from the program. A clip-space point is visible when $-w \le x, y, z \le w$;
triangles and lines that cross this boundary are cut at it. The **perspective
divide** then divides $x$, $y$ and $z$ by $w$, giving normalised device
coordinates in $[-1, 1]$. Last, the **viewport transform** maps NDC to window
pixels, $x_w = (x_\text{nd} + 1)\,\text{width}/2 + x_0$ and the same for $y$,
measured up from the bottom-left corner, and maps $z_\text{nd}$ from $[-1, 1]$
to a depth in $[0, 1]$ for the depth test. Qt sets the viewport to the whole
framebuffer before each `paintGL` ({ref}`guide-gl-overrides`). The corner
above lands at about pixel $(330, 406)$ of a 640-pixel square, at depth 0.978.

(guide-mouse-motion)=
## From the mouse to the scene

The widget passes each mouse movement, in device-independent pixels, to one
of four methods ({ref}`guide-mouse`). The settings they use:

```{literalinclude} ../../src/config.py
:language: python
:start-at: ROTATE_DEGREES_PER_PIXEL
:end-at: MIN_DISTANCE, MAX_DISTANCE
```

### A drag as a rotation: `screen_rotation`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: screen_rotation
:start-at: axis =
:dedent: 4
```

A drag should move the surface under the cursor along with it. Take the
point of the scene nearest the camera, in the direction $+z$ from the
origin. A rotation about a unit axis $\boldsymbol{\omega}$ moves a point
$\mathbf{p}$ in the direction $\boldsymbol{\omega} \times \mathbf{p}$. Qt's
screen $y$ grows downwards while world $y$ grows upwards, so a drag of
$(\Delta x, \Delta y)$ pixels is the world direction
$(\Delta x, -\Delta y, 0)$. Solving

$$
\boldsymbol{\omega} \times \hat{\mathbf{z}} =
(\omega_y,\ -\omega_x,\ 0) = (\Delta x,\ -\Delta y,\ 0)
$$

gives $\boldsymbol{\omega} = (\Delta y,\ \Delta x,\ 0)$: the drag's
components swapped, which is the `axis` in the code. A drag to the right
turns about $+y$, carrying the front of the scene to the right; a drag
downwards turns about $+x$, carrying the front down. The axis lies in the
screen plane, at right angles to the drag.

The angle is the length of the drag times `ROTATE_DEGREES_PER_PIXEL`, so a
drag of 10 pixels turns 5°. `fromAxisAndAngle` takes degrees and returns a
unit quaternion. A drag of zero length has no axis, so it returns the
identity quaternion instead of normalising a zero vector.

### Turning the cube: `rotate_by`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.rotate_by
:start-at: self.rotation =
:dedent: 8
```

The drag's rotation multiplies the old one **on the left**. In matrices,

$$
R_{\text{world}\leftarrow\text{model}}^\text{new} =
R_\text{drag}\,R_{\text{world}\leftarrow\text{model}}^\text{old} ,
$$

so a model point is first rotated as before, into world space, and then
turned by the drag about an axis given in world coordinates. The camera does
not rotate, so world axes are screen axes, and the drag turns the scene
about the screen's axes whatever the cube's orientation. Multiplying on the
right instead would turn about the cube's own axes, and a drag would follow
the cursor only while the cube was unturned.

`normalized()` scales the result back to length 1. A product of unit
quaternions is a unit quaternion in exact arithmetic, but each product
rounds, and the error builds up slowly over many drags. `rotate()` in
`model_matrix` assumes a unit quaternion; given a longer one, it would build
a matrix that is no longer a pure rotation.

### Moving the light: `move_light_by`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.move_light_by
:start-at: self.light =
:dedent: 8
```

The same drag rotation is applied to the light vector instead of to the
cube. `rotatedVector` rotates a vector by the quaternion, $q\,v\,q^{*}$ in
Qt's documentation. The light is in world space, so it turns about the same
screen axes and follows the cursor across the sphere, while the cube stays
still. `normalized()` keeps it a unit vector, as the shader expects.

### Panning: `pan_by`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.pan_by
:start-at: scale =
:dedent: 8
```

The pan moves the scene in camera $x$ and $y$; $y$ is negated because screen
$y$ grows downwards. The scale converts pixels to world units. At distance
$d$ the window's height covers $2d\tan(\theta/2) \approx 0.828\,d$ world
units in the plane through the origin facing the camera, so one pixel there
is $0.828\,d/\text{height}$. The code's $0.8\,d/\text{height}$ is just under
that: points in that plane move with the cursor, about 3% short of it.
Nearer points move farther on screen than the cursor, and farther ones less,
since every point moves by the same world distance.
The scale grows with `distance`, so panning feels the same at any zoom.

### Zooming: `zoom_by`

```{literalinclude} ../../src/context.py
:language: python
:pyobject: SceneContext.zoom_by
:start-at: distance =
:dedent: 8
```

Each notch towards the screen multiplies the distance by
`ZOOM_FACTOR_PER_NOTCH` (0.9), and each notch back divides it by 0.9. A
factor per notch makes zooming feel even: the same number of notches always
changes the apparent size by the same ratio. The result is clamped to
$[2, 20]$. At 2 the camera is still outside the sphere of radius 1.85, so
everything drawn is at least 0.15 units in front of it, beyond the near plane
at 0.1; at 20 the cube is small.
From the default of 6, about 10.4 notches reach the near limit and 11.4 the
far one.

(guide-quaternion-convention)=
```{admonition} Quaternion conventions: Qt and JPL
:class: note

Qt's `QQuaternion` is **Hamilton** ($ij = k$), **scalar-first**
$(w, x, y, z)$, and `rotatedVector` rotates vectors **actively**.
`SceneContext.rotation` takes model coordinates to world coordinates: its
matrix is `R_world_model`.

In the JPL convention (scalar-last, $ij = -k$, passive), the same attitude
is the quaternion

$$
\bar q_{\text{world}\leftarrow\text{model}} = [-x,\ -y,\ -z,\ w] ,
$$

the conjugate, with the scalar moved last. With $\mathbf{q}$ its vector part,
$q_4$ its scalar and $\lfloor\mathbf{q}\times\rfloor$ the matrix that takes
the cross product with $\mathbf{q}$, its direction-cosine matrix

$$
C(\bar q) = (2q_4^2 - 1)\,I - 2q_4\lfloor\mathbf{q}\times\rfloor +
2\,\mathbf{q}\mathbf{q}^T
$$

equals `R_world_model`. The update in `rotate_by`, `new = drag * old` in Qt,
keeps the same order under the JPL product:

$$
\bar q_\text{new} = \bar q_\text{drag} \otimes \bar q_\text{old} .
$$

Both statements were checked numerically over 200 random rotations, to
float32 precision (largest error $3 \times 10^{-7}$). Taking Qt's components
in scalar-last order without conjugating gives the wrong matrix: in the same
check, its largest error was 1.6.
```
