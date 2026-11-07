"""Tests for ``gl_utils``.

The ``glsl_header`` branches are reached with a stub in place of
``QOpenGLContext``; everything else runs against the real offscreen context.
"""
import numpy as np
import pytest
from OpenGL import GL
from PyQt6.QtGui import QMatrix4x4, QVector3D

import gl_utils
import shaders

#: Precision statements ``glsl_header`` adds under OpenGL ES.
ES_PRECISION = "precision highp float;\nprecision lowp sampler2DArray;\n"


class _StubFormat:
    def __init__(self, major, minor):
        self._version = (major, minor)

    def majorVersion(self):
        return self._version[0]

    def minorVersion(self):
        return self._version[1]


class _StubContext:
    def __init__(self, major, minor, es):
        self._format = _StubFormat(major, minor)
        self._es = es

    def format(self):
        return self._format

    def isOpenGLES(self):
        return self._es


def _stub_header(monkeypatch, major, minor, es):
    context = _StubContext(major, minor, es)

    class StubQOpenGLContext:
        @staticmethod
        def currentContext():
            return context

    monkeypatch.setattr(gl_utils, "QOpenGLContext", StubQOpenGLContext)
    return gl_utils.glsl_header()


@pytest.mark.parametrize(
    ("major", "minor", "version"),
    [(3, 0, 300), (3, 1, 310), (2, 0, 300)],
)
def test_glsl_header_es(monkeypatch, major, minor, version):
    """OpenGL ES contexts get a ``es`` version line and both precisions.

    **WHY:** This machine never creates an ES context, so a stub stands in for
    it. Before 2026-11-01 this branch produced an ES header that could never
    compile, and nothing caught it.
    """
    header = _stub_header(monkeypatch, major, minor, True)
    assert header == f"#version {version} es\n" + ES_PRECISION


@pytest.mark.parametrize(
    ("major", "minor", "version"),
    [(4, 1, 410), (3, 3, 330), (3, 2, 150), (3, 1, 140), (2, 1, 140)],
)
def test_glsl_header_desktop(monkeypatch, major, minor, version):
    """Desktop contexts map to the matching GLSL version.

    **WHY:** This machine always creates a 4.1 context, so a stub stands in for
    the older versions. Each version must map to a GLSL version the driver
    accepts.
    """
    assert _stub_header(monkeypatch, major, minor, False) == f"#version {version}\n"


def test_glsl_header_real_context(gl_context):
    """The real header names the version the context provides.

    **WHY:** The stubbed tests check the mapping; this one checks that the real
    Qt context reports its version the way the stubs assume.
    """
    fmt = gl_context.format()
    expected = 100 * fmt.majorVersion() + 10 * fmt.minorVersion()
    header = gl_utils.glsl_header()
    assert header.startswith("#version ")
    assert header.split()[1] == str(expected)


def test_compile_shader_success(gl_context):
    """A valid vertex shader compiles to a shader name.

    **WHY:** This is a real compile of a real shader under this machine's
    header, the most direct check that the shader bodies suit this platform.
    """
    source = gl_utils.glsl_header() + shaders.OVERLAY_VERTEX_BODY
    shader = gl_utils.compile_shader(GL.GL_VERTEX_SHADER, source)
    assert GL.glIsShader(shader)


def test_compile_shader_failure(gl_context):
    """Garbage source raises with the info log as the message.

    **WHY:** A failed compile must raise with the driver's log. Otherwise the
    program would carry on with shader 0 and draw nothing, with no explanation.
    """
    with pytest.raises(RuntimeError) as excinfo:
        gl_utils.compile_shader(GL.GL_VERTEX_SHADER, "this is not glsl")
    # The message is the info log; its wording differs between drivers, but
    # every one names either the error or the offending token.
    message = str(excinfo.value).lower()
    assert "error" in message or "this" in message


@pytest.mark.parametrize(
    ("vertex", "fragment"),
    [
        (shaders.OVERLAY_VERTEX_BODY, shaders.OVERLAY_FRAGMENT_BODY),
        (shaders.CUBE_VERTEX_BODY, shaders.CUBE_FRAGMENT_BODY),
    ],
    ids=["overlay", "cube"],
)
def test_build_program_success(gl_context, vertex, fragment):
    """The program pairs link.

    **WHY:** Linking checks that each vertex shader's outputs match the
    fragment shader's inputs, which compiling each shader alone does not.
    """
    program = gl_utils.build_program(vertex, fragment)
    assert GL.glIsProgram(program)


def test_build_program_link_failure(gl_context):
    """Mismatched varying types fail to link and raise.

    **WHY:** The GLSL specification requires every driver to reject this type
    mismatch at link time. Both shaders are compiled first, so the error must
    come from linking.
    """
    vertex = "out vec3 v;\nvoid main() { v = vec3(0.0); gl_Position = vec4(0.0); }\n"
    fragment = "in vec4 v;\nout vec4 color;\nvoid main() { color = v; }\n"
    header = gl_utils.glsl_header()
    # Both shaders compile on their own, so the failure comes from linking.
    gl_utils.compile_shader(GL.GL_VERTEX_SHADER, header + vertex)
    gl_utils.compile_shader(GL.GL_FRAGMENT_SHADER, header + fragment)
    with pytest.raises(RuntimeError):
        gl_utils.build_program(vertex, fragment)


@pytest.fixture
def cube_program(gl_context):
    """Build and bind the cube program."""
    program = gl_utils.build_program(
        shaders.CUBE_VERTEX_BODY, shaders.CUBE_FRAGMENT_BODY
    )
    GL.glUseProgram(program)
    yield program
    GL.glUseProgram(0)


def test_set_matrix(cube_program):
    """Uploaded values read back column-major, i.e. transposed.

    **WHY:** Matrix uploads are where transposition bugs live. A transposed
    projection still draws something, just wrongly, so the bug would show only
    in a frame.
    """
    values = np.arange(1.0, 17.0, dtype=np.float32)
    matrix = QMatrix4x4(*values.tolist())  # row-major constructor
    location = GL.glGetUniformLocation(cube_program, "mvp")
    gl_utils.set_matrix(location, matrix)
    buffer = (GL.GLfloat * 16)()
    GL.glGetUniformfv(cube_program, location, buffer)
    expected = values.reshape(4, 4).T.reshape(-1)
    np.testing.assert_array_equal(np.array(buffer[:]), expected)


def test_set_vector(cube_program):
    """Uploaded components read back in order.

    **WHY:** A component-order mistake would move the light or the camera
    without any error.
    """
    location = GL.glGetUniformLocation(cube_program, "lightDirection")
    gl_utils.set_vector(location, QVector3D(1.0, 2.0, 3.0))
    buffer = (GL.GLfloat * 3)()
    GL.glGetUniformfv(cube_program, location, buffer)
    assert list(buffer) == [1.0, 2.0, 3.0]


def test_upload_texture_array(gl_context):
    """Width, height and depth match and no GL error is raised.

    **WHY:** The texture array's dimensions are what the cube shader samples by
    layer. A wrong depth would sample the wrong material for some faces.
    """
    size, layers = 4, 2
    pixels = bytes(size * size * layers * 4)
    texture = gl_utils.upload_texture_array(0, pixels, size, layers)
    assert GL.glIsTexture(texture)
    target = GL.GL_TEXTURE_2D_ARRAY
    dims = [
        GL.glGetTexLevelParameteriv(target, 0, name)
        for name in (GL.GL_TEXTURE_WIDTH, GL.GL_TEXTURE_HEIGHT, GL.GL_TEXTURE_DEPTH)
    ]
    assert dims == [size, size, layers]
    assert GL.glGetError() == GL.GL_NO_ERROR
