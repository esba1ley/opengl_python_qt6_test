"""Renderer for the textured, bump-mapped cube."""
from OpenGL import GL

import config
import geometry
import gl_utils
import shaders
import textures

FLOAT_SIZE = 4


class CubeRenderer:
    """Draws the cube using the state in a `context.SceneContext`.

    Call `initialize` once and `paint` for each frame, both with an OpenGL
    context current.
    """

    def initialize(self):
        """Create the shader program, textures and vertex buffer."""
        self.program = gl_utils.build_program(
            shaders.CUBE_VERTEX_BODY, shaders.CUBE_FRAGMENT_BODY
        )
        self.mvp_loc = GL.glGetUniformLocation(self.program, "mvp")
        self.model_loc = GL.glGetUniformLocation(self.program, "model")
        self.light_loc = GL.glGetUniformLocation(self.program, "lightDirection")
        self.camera_loc = GL.glGetUniformLocation(self.program, "cameraPosition")
        self.init_textures()
        self.init_vertices()

    def init_textures(self):
        """Upload the colour and normal maps and connect them to the shader."""
        albedo, normals, layers = textures.generate_texture_layers()
        size = config.TEXTURE_SIZE
        self.albedo_texture = gl_utils.upload_texture_array(0, albedo, size, layers)
        self.normal_texture = gl_utils.upload_texture_array(1, normals, size, layers)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glUseProgram(self.program)
        GL.glUniform1i(GL.glGetUniformLocation(self.program, "albedoMap"), 0)
        GL.glUniform1i(GL.glGetUniformLocation(self.program, "normalMap"), 1)

    def init_vertices(self):
        """Upload the cube's vertices and describe their layout."""
        vertices = geometry.cube_vertices()
        self.vertex_count = len(vertices) // geometry.FLOATS_PER_VERTEX
        buffer_data = (GL.GLfloat * len(vertices))(*vertices)

        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)
        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(vertices) * FLOAT_SIZE,
            buffer_data,
            GL.GL_STATIC_DRAW,
        )
        stride = geometry.FLOATS_PER_VERTEX * FLOAT_SIZE
        offset = 0
        for name, size in geometry.VERTEX_ATTRIBUTES:
            location = GL.glGetAttribLocation(self.program, name)
            GL.glEnableVertexAttribArray(location)
            GL.glVertexAttribPointer(
                location,
                size,
                GL.GL_FLOAT,
                GL.GL_FALSE,
                stride,
                GL.GLvoidp(offset * FLOAT_SIZE),
            )
            offset += size
        GL.glBindVertexArray(0)

    def paint(self, ctx):
        """Draw the cube.

        Parameters
        ----------
        ctx : context.SceneContext
            The scene to draw.
        """
        model = ctx.model_matrix()
        GL.glUseProgram(self.program)
        gl_utils.set_matrix(self.mvp_loc, ctx.view_projection_matrix() * model)
        gl_utils.set_matrix(self.model_loc, model)
        gl_utils.set_vector(self.light_loc, ctx.light)
        gl_utils.set_vector(self.camera_loc, ctx.camera_position())
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.albedo_texture)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.normal_texture)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertex_count)
        GL.glBindVertexArray(0)
