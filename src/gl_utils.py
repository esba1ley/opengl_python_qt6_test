"""Small helpers around raw OpenGL calls."""
from OpenGL import GL
from PyQt6.QtGui import QOpenGLContext


def compile_shader(kind, source):
    """Compile a single shader.

    Parameters
    ----------
    kind : int
        Shader type, such as ``GL_VERTEX_SHADER``.
    source : str
        Complete GLSL source.

    Returns
    -------
    int
        The OpenGL shader name.

    Raises
    ------
    RuntimeError
        If compilation fails. The message is the shader info log.
    """
    shader = GL.glCreateShader(kind)
    GL.glShaderSource(shader, source)
    GL.glCompileShader(shader)
    if not GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS):
        raise RuntimeError(GL.glGetShaderInfoLog(shader))
    return shader


def glsl_header():
    """Choose the GLSL header for the current OpenGL context.

    The version line follows the version the context actually provides, so
    the same shader bodies compile under the newest GLSL each platform offers
    and still work if a platform returns less than was requested.

    Returns
    -------
    str
        Version line and any precision statements. Desktop OpenGL and OpenGL
        ES need different headers, and Qt may provide either.

    Notes
    -----
    Desktop OpenGL 3.1 and 3.2 pair with GLSL 1.40 and 1.50. From 3.3 on, the
    GLSL version number matches the OpenGL version. OpenGL ES 3.x pairs with
    GLSL ES 3.x0. Versions below those are not supported and get the lowest
    header, so the compiler reports the problem.

    GLSL ES fragment shaders have no default precision for ``float`` or for
    ``sampler2DArray``, so the ES header declares both. Desktop GLSL accepts
    and ignores precision statements.
    """
    context = QOpenGLContext.currentContext()
    major, minor = context.format().majorVersion(), context.format().minorVersion()
    if context.isOpenGLES():
        version = 300 + 10 * minor if major == 3 else 300
        return (
            f"#version {version} es\n"
            "precision highp float;\n"
            "precision lowp sampler2DArray;\n"
        )
    if (major, minor) >= (3, 3):
        version = 100 * major + 10 * minor
    elif (major, minor) == (3, 2):
        version = 150
    else:
        version = 140
    return f"#version {version}\n"


def build_program(vertex_body, fragment_body):
    """Compile and link a shader program for the current context.

    Parameters
    ----------
    vertex_body : str
        GLSL source of the vertex shader, without a version header.
    fragment_body : str
        GLSL source of the fragment shader, without a version header.

    Returns
    -------
    int
        The OpenGL program name.

    Raises
    ------
    RuntimeError
        If a shader fails to compile or the program fails to link.
    """
    header = glsl_header()
    program = GL.glCreateProgram()
    for kind, body in (
        (GL.GL_VERTEX_SHADER, vertex_body),
        (GL.GL_FRAGMENT_SHADER, fragment_body),
    ):
        GL.glAttachShader(program, compile_shader(kind, header + body))
    GL.glLinkProgram(program)
    if not GL.glGetProgramiv(program, GL.GL_LINK_STATUS):
        raise RuntimeError(GL.glGetProgramInfoLog(program))
    return program


def set_matrix(location, matrix):
    """Upload a matrix to a uniform of the current program.

    Parameters
    ----------
    location : int
        Uniform location.
    matrix : PyQt6.QtGui.QMatrix4x4
        Matrix to upload.
    """
    # copyDataTo() is row-major, so ask GL to transpose it.
    values = (GL.GLfloat * 16)(*matrix.copyDataTo())
    GL.glUniformMatrix4fv(location, 1, GL.GL_TRUE, values)


def set_vector(location, vector):
    """Upload a 3D vector to a uniform of the current program.

    Parameters
    ----------
    location : int
        Uniform location.
    vector : PyQt6.QtGui.QVector3D
        Vector to upload.
    """
    GL.glUniform3f(location, vector.x(), vector.y(), vector.z())


def upload_texture_array(unit, pixels, size, layers):
    """Create a mipmapped 2D array texture from pixel data.

    The new texture stays bound to `unit`, and that unit stays active. A current
    OpenGL context is required.

    Parameters
    ----------
    unit : int
        Texture unit to bind to, where 0 means ``GL_TEXTURE0``.
    pixels : bytes
        RGBA8 pixels for every layer, as produced by `to_rgba_bytes`.
    size : int
        Width and height of each layer, in pixels.
    layers : int
        Number of layers.

    Returns
    -------
    int
        The OpenGL texture name.
    """
    GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
    texture = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, texture)
    GL.glTexImage3D(
        GL.GL_TEXTURE_2D_ARRAY,
        0,
        GL.GL_RGBA8,
        size,
        size,
        layers,
        0,
        GL.GL_RGBA,
        GL.GL_UNSIGNED_BYTE,
        pixels,
    )
    GL.glGenerateMipmap(GL.GL_TEXTURE_2D_ARRAY)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
    return texture
