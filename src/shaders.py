"""GLSL source for the cube and the overlay.

Each string is a shader body. `gl_utils.build_program` adds the version header
that matches the current OpenGL context.
"""

#: Cube vertex shader: projects each vertex and carries the face's
#: world-space tangent frame, texture coordinates and texture layer.
CUBE_VERTEX_BODY = """
uniform mat4 mvp;
uniform mat4 model;
in vec3 position;
in vec3 normal;
in vec3 tangent;
in vec3 bitangent;
in vec2 uv;
in float layer;
out vec3 worldPosition;
out vec3 worldNormal;
out vec3 worldTangent;
out vec3 worldBitangent;
out vec2 textureCoords;
flat out float textureLayer;
void main() {
    gl_Position = mvp * vec4(position, 1.0);
    // model is rotation-only, so mat3(model) is safe for directions.
    worldPosition = mat3(model) * position;
    worldNormal = mat3(model) * normal;
    worldTangent = mat3(model) * tangent;
    worldBitangent = mat3(model) * bitangent;
    textureCoords = uv;
    textureLayer = layer;
}
"""

#: Cube fragment shader: normal-mapped Blinn-Phong lighting from the two
#: array textures, gated on the geometric face normal. The ``view`` uniform
#: selects a debug view of one shading stage or of one per-vertex input (see
#: ``CUBE_VIEWS``); 0 is the normal lit image.
CUBE_FRAGMENT_BODY = """
uniform sampler2DArray albedoMap;
uniform sampler2DArray normalMap;
uniform vec3 lightDirection;
uniform vec3 cameraPosition;
uniform int view;
in vec3 worldPosition;
in vec3 worldNormal;
in vec3 worldTangent;
in vec3 worldBitangent;
in vec2 textureCoords;
flat in float textureLayer;
out vec4 fragColor;
void main() {
    vec3 coords = vec3(textureCoords, textureLayer);
    vec3 albedo = texture(albedoMap, coords).rgb;
    vec3 surface = texture(normalMap, coords).xyz * 2.0 - 1.0;

    // Bend the face normal by the normal map, using the face's own axes.
    mat3 tangentToWorld = mat3(
        normalize(worldTangent), normalize(worldBitangent), normalize(worldNormal));
    vec3 n = normalize(tangentToWorld * surface);

    // A face turned away from the light is in the cube's own shadow, so its
    // bumps must not catch light even where they slope towards it. Fade over
    // a small angle so the terminator has no hard seam.
    float facing = smoothstep(0.0, 0.1, dot(normalize(worldNormal), lightDirection));

    float diffuse = facing * max(dot(n, lightDirection), 0.0);
    vec3 toCamera = normalize(cameraPosition - worldPosition);
    vec3 halfway = normalize(lightDirection + toCamera);
    float specular = diffuse > 0.0 ? facing * pow(max(dot(n, halfway), 0.0), 32.0) : 0.0;

    vec3 result = albedo * (0.2 + 0.8 * diffuse) + vec3(0.3 * specular);

    // The view uniform shows one stage on its own, so the manual can picture
    // each step of the lighting (views 1 to 5) and each per-vertex input from
    // the geometry (views 6 to 10). View 0 keeps the final colour.
    if (view == 1) result = albedo;
    else if (view == 2) result = n * 0.5 + 0.5;
    else if (view == 3) result = vec3(diffuse);
    else if (view == 4) result = vec3(facing);
    else if (view == 5) result = vec3(specular);
    else if (view == 6) result = vec3(textureCoords, 0.0);
    // Six faces, layers 0 to 5. The +1 keeps layer 0 off black, which would
    // vanish into the background; the greys run from 1/6 to 1.
    else if (view == 7) result = vec3((textureLayer + 1.0) / 6.0);
    else if (view == 8) result = normalize(worldTangent) * 0.5 + 0.5;
    else if (view == 9) result = normalize(worldBitangent) * 0.5 + 0.5;
    else if (view == 10) result = normalize(worldNormal) * 0.5 + 0.5;
    fragColor = vec4(result, 1.0);
}
"""

#: Names of the cube's debug views; index ``i`` is the value of the ``view``
#: uniform in ``CUBE_FRAGMENT_BODY``.
CUBE_VIEWS = (
    "final",
    "albedo",
    "normal",
    "diffuse",
    "facing",
    "specular",
    "uv",
    "layer",
    "tangent",
    "bitangent",
    "face_normal",
)

#: Overlay vertex shader for the sphere grid, axes and light dot; sets the
#: point size and passes the world position and vertex colour through.
OVERLAY_VERTEX_BODY = """
uniform mat4 mvp;
uniform mat4 model;
uniform float pointSize;
in vec3 position;
in vec3 vertexColor;
out vec3 worldPosition;
out vec3 color;
void main() {
    gl_Position = mvp * vec4(position, 1.0);
    gl_PointSize = pointSize;
    worldPosition = mat3(model) * position;
    color = vertexColor;
}
"""

#: Overlay fragment shader: optional round points and near/far side shading
#: for the sphere grid, with a uniform opacity.
OVERLAY_FRAGMENT_BODY = """
uniform vec3 cameraPosition;
uniform bool sideShading;
uniform bool roundPoint;
uniform float opacity;
in vec3 worldPosition;
in vec3 color;
out vec4 fragColor;
void main() {
    if (roundPoint && length(gl_PointCoord - vec2(0.5)) > 0.5) {
        discard;
    }
    vec3 result = color;
    if (sideShading) {
        // The sphere is centred on the origin, so a point's position is also
        // its outward normal. It faces the camera on the near side.
        bool near = dot(worldPosition, cameraPosition - worldPosition) > 0.0;
        result = near ? vec3(0.82) : vec3(0.32);
    }
    fragColor = vec4(result, opacity);
}
"""
