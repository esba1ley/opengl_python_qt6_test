(references)=
# References and further reading

This page lists the documentation behind everything the program uses:
Python, the Python packages, Qt 6, and OpenGL in its desktop and embedded
forms. For each one, it gives the learning material the authors maintain or
recommend, followed by the reference material. Each page of
[How it works](guide/index.md) ends with a shorter list for its own topic.

The links were checked on 2026-11-08. Where a project keeps documentation for
several versions, the link points at the version the program targets, or at
the current version when the part the program uses has not changed.

## Where to start

If one of these is new to you, start with the authors' own introduction:

- **Python:** [The Python Tutorial](https://docs.python.org/3/tutorial/index.html),
  maintained with the language. The Python wiki's
  [Beginner's Guide](https://wiki.python.org/moin/BeginnersGuide) points
  to more introductions, for programmers and non-programmers.
- **NumPy:** [NumPy: the absolute basics for beginners](https://numpy.org/doc/stable/user/absolute_beginners.html),
  then the [quickstart](https://numpy.org/doc/stable/user/quickstart.html).
  The project's [Learn](https://numpy.org/learn/) page lists further
  tutorials and books.
- **Qt 6:** [Getting Started with Qt](https://doc.qt.io/qt-6/gettingstarted.html),
  then [Qt Examples and Tutorials](https://doc.qt.io/qt-6/qtexamplesandtutorials.html).
  [Qt Academy](https://www.qt.io/academy) has free courses from The Qt
  Company (it needs an account).
- **OpenGL:** the OpenGL Wiki's
  [Getting Started](https://wikis.khronos.org/opengl/Getting_Started) page,
  maintained by the Khronos community, and the
  [Rendering Pipeline Overview](https://wikis.khronos.org/opengl/Rendering_Pipeline_Overview).
  [LearnOpenGL](https://learnopengl.com/) is a free online tutorial in the
  same core-profile style as this program, with no fixed-function calls.
- **pytest:** [Get Started](https://docs.pytest.org/en/stable/getting-started.html).
- **Sphinx:** the [Sphinx tutorial](https://www.sphinx-doc.org/en/master/tutorial/index.html).

## Python

The program targets Python 3.12 and is tested on 3.11 and 3.13 as well.

- [Python documentation](https://docs.python.org/3/): the language and
  library reference.
- [The Python Standard Library](https://docs.python.org/3/library/index.html).
  The modules the program and its tools lean on are
  [`ctypes`](https://docs.python.org/3/library/ctypes.html) (C arrays handed
  to OpenGL), [`sys.platform`](https://docs.python.org/3/library/sys.html#sys.platform)
  (the one platform test),
  [`argparse`](https://docs.python.org/3/library/argparse.html) and
  [`contextlib`](https://docs.python.org/3/library/contextlib.html) (in the
  tools).
- [Status of Python versions](https://devguide.python.org/versions/): which
  versions receive bug fixes and which receive only security fixes.
- [PEP 8](https://peps.python.org/pep-0008/), the style guide the code
  follows, and the
  [numpydoc docstring guide](https://numpydoc.readthedocs.io/en/latest/format.html),
  the format of every docstring.

## Python packages

### Run time

- **PyQt6**, the Python bindings for Qt 6, by Riverbank Computing:
  [project page](https://www.riverbankcomputing.com/software/pyqt/) and
  [reference guide](https://www.riverbankcomputing.com/static/Docs/PyQt6/).
  The guide covers what differs from Qt's C++ interface, such as
  [signals and slots](https://www.riverbankcomputing.com/static/Docs/PyQt6/signals_slots.html)
  and the [module index](https://www.riverbankcomputing.com/static/Docs/PyQt6/module_index.html);
  for what a class does, read {ref}`Qt's own documentation <qt-6>`.
  PySide6, Qt's official binding, is a different package and is not used
  here.
- **PyOpenGL**, the Python binding for OpenGL:
  [project page](https://pyopengl.sourceforge.net/),
  [documentation index](https://pyopengl.sourceforge.net/documentation/),
  and [PyOpenGL for OpenGL programmers](https://pyopengl.sourceforge.net/documentation/opengl_diffs.html),
  how its calls differ from the C API. The source is on
  [GitHub](https://github.com/mcfletch/pyopengl). Its tutorial links are
  old, and many teach pre-shader OpenGL, so learn the API itself from the
  OpenGL section below.
- **NumPy**: [documentation](https://numpy.org/doc/stable/). The texture
  and geometry code relies most on
  [broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html),
  [indexing](https://numpy.org/doc/stable/user/basics.indexing.html),
  the [random `Generator`](https://numpy.org/doc/stable/reference/random/generator.html)
  and [data types](https://numpy.org/doc/stable/reference/arrays.dtypes.html).

### Development

- **pytest**: [documentation](https://docs.pytest.org/en/stable/), and
  [fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), which
  `tests/conftest.py` uses for its OpenGL context.
- **pytest-qt**: [documentation](https://pytest-qt.readthedocs.io/en/latest/).
- **pytest-cov**: [documentation](https://pytest-cov.readthedocs.io/en/latest/);
  it runs coverage.py, whose page on
  [branch coverage](https://coverage.readthedocs.io/en/latest/branch.html)
  explains the branch half of the 100% gate.
- **Pillow**: [documentation](https://pillow.readthedocs.io/en/stable/);
  used only by `tools/make_control_animations.py`.
- **Ruff**: [documentation](https://docs.astral.sh/ruff/).
- **bump2version**: [repository and documentation](https://github.com/c4urself/bump2version).

### Documentation

- **Sphinx**: [documentation](https://www.sphinx-doc.org/en/master/), with
  [autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
  and [napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html),
  which build the API pages from the docstrings.
- **MyST-Parser**, the Markdown reader:
  [documentation](https://myst-parser.readthedocs.io/en/latest/) and its
  [maths syntax](https://myst-parser.readthedocs.io/en/latest/syntax/math.html).
- **Read the Docs Sphinx theme**: [documentation](https://sphinx-rtd-theme.readthedocs.io/en/stable/).
- **sphinxcontrib-plantuml**: [repository](https://github.com/sphinx-contrib/plantuml).
  It runs [PlantUML](https://plantuml.com/) (see its
  [sequence](https://plantuml.com/sequence-diagram) and
  [activity](https://plantuml.com/activity-diagram-beta) diagram pages),
  which uses [Graphviz](https://graphviz.org/) to lay out some diagrams.

### Environment

- [Miniforge](https://github.com/conda-forge/miniforge), the conda installer,
  and the [conda-forge documentation](https://conda-forge.org/docs/), the
  channel every package comes from.
- [MacPorts](https://www.macports.org/), for PlantUML, Java and Graphviz on
  macOS.

(qt-6)=
## Qt 6

- [Qt 6 documentation](https://doc.qt.io/qt-6/), and the module overviews
  for [Qt GUI](https://doc.qt.io/qt-6/qtgui-index.html),
  [Qt Widgets](https://doc.qt.io/qt-6/qtwidgets-index.html) and
  [Qt OpenGL](https://doc.qt.io/qt-6/qtopengl-index.html).
- Concepts: [the event system](https://doc.qt.io/qt-6/eventsandfilters.html),
  [signals and slots](https://doc.qt.io/qt-6/signalsandslots.html) and
  [high DPI](https://doc.qt.io/qt-6/highdpi.html) (device-independent
  pixels).
- Examples close to this program, in C++:
  [Cube OpenGL ES 2.0](https://doc.qt.io/qt-6/qtopengl-cube-example.html), a
  textured cube turned with the mouse, and
  [Hello GL2](https://doc.qt.io/qt-6/qtopengl-hellogl2-example.html), a
  `QOpenGLWidget` with its own shaders and vertex buffers.

The classes the program uses, by job:

- **The application and the window:**
  [`QApplication`](https://doc.qt.io/qt-6/qapplication.html),
  [`QCoreApplication::exec`](https://doc.qt.io/qt-6/qcoreapplication.html#exec),
  [`QWidget`](https://doc.qt.io/qt-6/qwidget.html) and
  [`QWidget::update`](https://doc.qt.io/qt-6/qwidget.html#update).
- **OpenGL:** [`QOpenGLWidget`](https://doc.qt.io/qt-6/qopenglwidget.html),
  [`QSurfaceFormat`](https://doc.qt.io/qt-6/qsurfaceformat.html),
  [`QOpenGLContext`](https://doc.qt.io/qt-6/qopenglcontext.html), and for
  the tests and tools
  [`QOffscreenSurface`](https://doc.qt.io/qt-6/qoffscreensurface.html) and
  [`QOpenGLFramebufferObject`](https://doc.qt.io/qt-6/qopenglframebufferobject.html).
- **Input and timing:** [`QMouseEvent`](https://doc.qt.io/qt-6/qmouseevent.html),
  [`QWheelEvent`](https://doc.qt.io/qt-6/qwheelevent.html) and
  [`QTimer`](https://doc.qt.io/qt-6/qtimer.html).
- **Maths:** [`QVector3D`](https://doc.qt.io/qt-6/qvector3d.html),
  [`QMatrix4x4`](https://doc.qt.io/qt-6/qmatrix4x4.html) and
  [`QQuaternion`](https://doc.qt.io/qt-6/qquaternion.html).
- **Images and drawing (the tools):** [`QImage`](https://doc.qt.io/qt-6/qimage.html)
  and [`QPainter`](https://doc.qt.io/qt-6/qpainter.html).

## OpenGL, OpenGL ES and GLSL

OpenGL is maintained by the [Khronos Group](https://www.khronos.org/opengl/),
as is [OpenGL ES](https://www.khronos.org/opengles/), its version for
embedded systems. The specifications are the final word; the reference pages
are easier to read for one function at a time.

### Specifications

The program asks for a different context on each platform, so three
specifications and three shading-language versions apply:

| Platform | Context | API specification | Shading language |
|---|---|---|---|
| macOS | OpenGL 4.1 core | [OpenGL 4.1 core profile](https://registry.khronos.org/OpenGL/specs/gl/glspec41.core.pdf) | [GLSL 4.10](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.4.10.pdf) |
| Linux (Raspberry Pi) | OpenGL ES 3.1 | [OpenGL ES 3.1](https://registry.khronos.org/OpenGL/specs/es/3.1/es_spec_3.1.pdf) | [GLSL ES 3.00](https://registry.khronos.org/OpenGL/specs/es/3.0/GLSL_ES_Specification_3.00.pdf) |
| Linux, if desktop OpenGL is granted instead | OpenGL 3.1 | [OpenGL 3.1](https://registry.khronos.org/OpenGL/specs/gl/glspec31.pdf) | [GLSL 1.40](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.1.40.pdf) |

The shader bodies keep to what GLSL 1.40 and GLSL ES 3.00 share, so they
compile under all three headers ({doc}`guide/context`). Every version is
in the [OpenGL registry](https://registry.khronos.org/OpenGL/index_gl.php)
and the [OpenGL ES registry](https://registry.khronos.org/OpenGL/index_es.php).

### Reference pages and quick reference

- [Reference pages](https://registry.khronos.org/OpenGL-Refpages/), one per
  function, for [OpenGL 4](https://registry.khronos.org/OpenGL-Refpages/gl4/)
  and [OpenGL ES 3](https://registry.khronos.org/OpenGL-Refpages/es3/).
  They cover the GLSL built-in functions too, such as
  [`smoothstep`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/smoothstep.xhtml),
  [`mix`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/mix.xhtml) and
  [`texture`](https://registry.khronos.org/OpenGL-Refpages/gl4/html/texture.xhtml).
- [Quick reference cards](https://www.khronos.org/developers/reference-cards/),
  the whole API and shading language on a few pages.

### Learning

- The [OpenGL Wiki](https://wikis.khronos.org/opengl/Getting_Started),
  maintained by the Khronos community. Its pages on
  [vertex specification](https://wikis.khronos.org/opengl/Vertex_Specification),
  [vertex post-processing](https://wikis.khronos.org/opengl/Vertex_Post-Processing),
  [array textures](https://wikis.khronos.org/opengl/Array_Texture),
  [the depth test](https://wikis.khronos.org/opengl/Depth_Test),
  [blending](https://wikis.khronos.org/opengl/Blending),
  [the OpenGL context](https://wikis.khronos.org/opengl/OpenGL_Context) and
  [the GLSL language](https://wikis.khronos.org/opengl/Core_Language_(GLSL))
  match pages of the guide.
- [LearnOpenGL](https://learnopengl.com/), by Joey de Vries: in particular
  [coordinate systems](https://learnopengl.com/Getting-started/Coordinate-Systems),
  [Blinn-Phong lighting](https://learnopengl.com/Advanced-Lighting/Advanced-Lighting)
  and [normal mapping](https://learnopengl.com/Advanced-Lighting/Normal-Mapping).
- Books, listed with the reference pages above: the
  [*OpenGL SuperBible*](https://www.openglsuperbible.com/) (Sellers, Wright
  and Haemel; 7th edition, OpenGL 4.5), and the *OpenGL Programming Guide*
  (Kessenich, Sellers and Shreiner; 9th edition, OpenGL 4.5), known as the
  Red Book.
- For procedural textures: [*The Book of Shaders*](https://thebookofshaders.com/)
  by Patricio Gonzalez Vivo and Jen Lowe, on
  [shaping functions](https://thebookofshaders.com/05/),
  [noise](https://thebookofshaders.com/11/) and
  [cellular noise](https://thebookofshaders.com/12/); and Inigo Quilez's
  [articles](https://iquilezles.org/articles/), such as
  [Voronoi edges](https://iquilezles.org/articles/voronoilines/).

### Platforms

- **macOS:** Apple deprecated OpenGL in macOS 10.14 and stops at 4.1. Its
  archived [OpenGL Programming Guide for Mac](https://developer.apple.com/library/archive/documentation/GraphicsImaging/Conceptual/OpenGL-MacProgGuide/)
  still describes how contexts and profiles are chosen.
- **Raspberry Pi:** the [Raspberry Pi documentation](https://www.raspberrypi.com/documentation/),
  and Mesa's page on the [V3D driver](https://docs.mesa3d.org/drivers/v3d.html)
  for the Pi's GPU.

## Rotations and quaternions

Qt's `QQuaternion` uses the Hamilton convention, scalar first; the guide
writes rotations in the JPL convention, scalar last (see
{ref}`Quaternion conventions: Qt and JPL <guide-quaternion-convention>`).
Two papers set the conventions side by side:

- Joan Solà, [*Quaternion kinematics for the error-state Kalman filter*](https://arxiv.org/abs/1711.02508)
  (2017), section 3, "Quaternion conventions", compares the Hamilton and JPL conventions term by term.
- Nikolas Trawny and Stergios I. Roumeliotis,
  [*Indirect Kalman Filter for 3D Attitude Estimation*](https://mars.cs.umn.edu/tr/reports/Trawny05b.pdf)
  (University of Minnesota MARS Lab, TR-2005-002, March 2005), section 1,
  defines quaternion algebra in the JPL convention and notes where it differs
  from Hamilton's.
