"""Renderer for the sphere grid, the axes and the light dot."""
import numpy as np
from OpenGL import GL
from PyQt6.QtGui import QMatrix4x4, QOpenGLContext

import config
import geometry
import gl_utils
import shaders

FLOAT_SIZE = 4


class OverlayRenderer:
    """Draws everything except the cube, on top of the cube.

    It reads the same `context.SceneContext` as the cube renderer, which is
    what keeps the sphere and axes anchored to the cube. Call `initialize`
    once and `paint` for each frame, both with an OpenGL context current.
    """

    def initialize(self):
        """Create the shader program and vertex buffer."""
        self.program = gl_utils.build_program(
            shaders.OVERLAY_VERTEX_BODY, shaders.OVERLAY_FRAGMENT_BODY
        )
        self.locs = {
            name: GL.glGetUniformLocation(self.program, name)
            for name in (
                "mvp",
                "model",
                "pointSize",
                "cameraPosition",
                "sideShading",
                "roundPoint",
                "opacity",
            )
        }

        grid = geometry.grid_vertices()
        axes = geometry.axis_vertices()
        dot = geometry.with_color(np.zeros((1, 3)), config.LIGHT_DOT_COLOR)
        self.grid_count = len(grid)
        self.axis_count = len(axes)
        self.dot_first = self.grid_count + self.axis_count
        data = np.vstack((grid, axes, dot)).astype(np.float32)

        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)
        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data.tobytes(), GL.GL_STATIC_DRAW)
        stride = data.shape[1] * FLOAT_SIZE
        for name, offset in (("position", 0), ("vertexColor", 3)):
            location = GL.glGetAttribLocation(self.program, name)
            GL.glEnableVertexAttribArray(location)
            GL.glVertexAttribPointer(
                location,
                3,
                GL.GL_FLOAT,
                GL.GL_FALSE,
                stride,
                GL.GLvoidp(offset * FLOAT_SIZE),
            )
        GL.glBindVertexArray(0)

        # Desktop GL ignores gl_PointSize unless told otherwise; GLES always
        # uses it and rejects this setting.
        if not QOpenGLContext.currentContext().isOpenGLES():
            GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        widest_line = GL.glGetFloatv(GL.GL_ALIASED_LINE_WIDTH_RANGE)[1]
        self.axis_width = min(config.AXIS_LINE_WIDTH, float(widest_line))

    def paint(self, ctx):
        """Draw the sphere grid, the axes and the light dot.

        The grid is translucent and does not write depth. The axes are depth
        tested, so the cube hides the parts inside it. The dot also has a faint
        pass without depth testing, so it stays visible behind the cube.

        Parameters
        ----------
        ctx : context.SceneContext
            The scene to draw.
        """
        locs = self.locs
        GL.glUseProgram(self.program)
        GL.glBindVertexArray(self.vao)
        gl_utils.set_vector(locs["cameraPosition"], ctx.camera_position())
        GL.glUniform1f(locs["pointSize"], config.LIGHT_DOT_SIZE * ctx.pixel_ratio)

        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFuncSeparate(
            GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ZERO, GL.GL_ONE
        )
        self.paint_grid(ctx)
        self.paint_axes(ctx)
        self.paint_light_dot(ctx)
        GL.glDisable(GL.GL_BLEND)
        GL.glBindVertexArray(0)

    def paint_grid(self, ctx):
        """Draw the latitude and longitude lines.

        Parameters
        ----------
        ctx : context.SceneContext
            The scene to draw.
        """
        locs = self.locs
        model = ctx.model_matrix()
        gl_utils.set_matrix(locs["mvp"], ctx.view_projection_matrix() * model)
        gl_utils.set_matrix(locs["model"], model)
        GL.glUniform1i(locs["sideShading"], 1)
        GL.glUniform1i(locs["roundPoint"], 0)
        GL.glUniform1f(locs["opacity"], config.SPHERE_OPACITY)
        # Translucent lines must not write depth, or they would punch small
        # gaps in the axes and light dot drawn after them.
        GL.glDepthMask(GL.GL_FALSE)
        GL.glDrawArrays(GL.GL_LINES, 0, self.grid_count)
        GL.glDepthMask(GL.GL_TRUE)
        GL.glUniform1i(locs["sideShading"], 0)

    def paint_axes(self, ctx):
        """Draw the axes. Depth testing hides the parts inside the cube.

        Parameters
        ----------
        ctx : context.SceneContext
            The scene to draw.
        """
        locs = self.locs
        mvp = ctx.view_projection_matrix() * ctx.model_matrix()
        gl_utils.set_matrix(locs["mvp"], mvp)
        GL.glUniform1f(locs["opacity"], 1.0)
        GL.glLineWidth(self.axis_width)
        GL.glDrawArrays(GL.GL_LINES, self.grid_count, self.axis_count)
        GL.glLineWidth(1.0)

    def paint_light_dot(self, ctx):
        """Draw the dot marking the direction to the light.

        The light is fixed in the scene, so the dot ignores the model matrix.

        Parameters
        ----------
        ctx : context.SceneContext
            The scene to draw.
        """
        locs = self.locs
        transform = QMatrix4x4()
        transform.translate(ctx.light_dot_position())
        gl_utils.set_matrix(locs["mvp"], ctx.view_projection_matrix() * transform)
        GL.glUniform1i(locs["roundPoint"], 1)
        # The dot is drawn faintly without depth first, so the light can still
        # be found behind the cube, then solid wherever it is really visible.
        for depth_test, opacity in ((False, config.HIDDEN_OPACITY), (True, 1.0)):
            if depth_test:
                GL.glEnable(GL.GL_DEPTH_TEST)
            else:
                GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glUniform1f(locs["opacity"], opacity)
            GL.glDrawArrays(GL.GL_POINTS, self.dot_first, 1)
