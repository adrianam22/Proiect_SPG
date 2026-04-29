import ctypes
import math

from OpenGL.GL import *

from config import CUBE_S


def draw_skybox(tex_top, tex_front, tex_back, tex_left, tex_right, s=CUBE_S, tint=(0.34, 0.38, 0.52)):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glColor3f(*tint)

    def face(tex, verts_uv):
        glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_QUADS)
        for (u, v), (x, y, z) in verts_uv:
            glTexCoord2f(u, v)
            glVertex3f(x, y, z)
        glEnd()

    face(tex_top, [
        ((0, 0), (-s, s, -s)), ((1, 0), (s, s, -s)),
        ((1, 1), (s, s, s)), ((0, 1), (-s, s, s))
    ])

    face(tex_front, [
        ((0, 0), (-s, -s, -s)), ((1, 0), (s, -s, -s)),
        ((1, 1), (s, s, -s)), ((0, 1), (-s, s, -s))
    ])

    face(tex_back, [
        ((0, 0), (s, -s, s)), ((1, 0), (-s, -s, s)),
        ((1, 1), (-s, s, s)), ((0, 1), (s, s, s))
    ])

    face(tex_left, [
        ((0, 0), (-s, -s, s)), ((1, 0), (-s, -s, -s)),
        ((1, 1), (-s, s, -s)), ((0, 1), (-s, s, s))
    ])

    face(tex_right, [
        ((0, 0), (s, -s, -s)), ((1, 0), (s, -s, s)),
        ((1, 1), (s, s, s)), ((0, 1), (s, s, -s))
    ])

    glEnable(GL_DEPTH_TEST)


def draw_ground(tex, s=CUBE_S, rep=1.0, tint=(0.50, 0.52, 0.54)):
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    glBindTexture(GL_TEXTURE_2D, tex)
    glColor3f(*tint)
    y = -CUBE_S + 0.02
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glTexCoord2f(0, 0)
    glVertex3f(-s, y, -s)
    glTexCoord2f(rep, 0)
    glVertex3f(s, y, -s)
    glTexCoord2f(rep, rep)
    glVertex3f(s, y, s)
    glTexCoord2f(0, rep)
    glVertex3f(-s, y, s)
    glEnd()


def draw_moon(direction, distance=CUBE_S * 0.72, radius=3.3):
    dx, dy, dz = direction
    ln = (dx * dx + dy * dy + dz * dz) ** 0.5 or 1.0
    dx, dy, dz = dx / ln, dy / ln, dz / ln
    x = -dx * distance
    y = dy * distance * 0.85
    z = -dz * distance

    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)

    glPushMatrix()
    glTranslatef(x, y, z)

    # Soft halo behind the moon so the global light source reads clearly.
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.72, 0.78, 0.96, 0.10)
    glVertex3f(0.0, 0.0, 0.0)
    for i in range(33):
        ang = 2.0 * math.pi * i / 32.0
        glColor4f(0.72, 0.78, 0.96, 0.0)
        glVertex3f(radius * 2.3 * math.cos(ang), radius * 2.3 * math.sin(ang), 0.0)
    glEnd()

    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.95, 0.96, 1.0, 0.92)
    glVertex3f(0.0, 0.0, 0.0)
    for i in range(33):
        ang = 2.0 * math.pi * i / 32.0
        glColor4f(0.95, 0.96, 1.0, 0.92)
        glVertex3f(radius * math.cos(ang), radius * math.sin(ang), 0.0)
    glEnd()

    glPopMatrix()
    glPopAttrib()


def draw_interior_markers(s=CUBE_S):
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glLineWidth(1.2)

    glColor3f(1.0, 1.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0, 1.0, 1.0, 0.18)

    edges = [
        ((-s, -s, -s), (s, -s, -s)), ((s, -s, -s), (s, -s, s)),
        ((s, -s, s), (-s, -s, s)), ((-s, -s, s), (-s, -s, -s)),
        ((-s, s, -s), (s, s, -s)), ((s, s, -s), (s, s, s)),
        ((s, s, s), (-s, s, s)), ((-s, s, s), (-s, s, -s)),
        ((-s, -s, -s), (-s, s, -s)), ((s, -s, -s), (s, s, -s)),
        ((s, -s, s), (s, s, s)), ((-s, -s, s), (-s, s, s)),
    ]
    glBegin(GL_LINES)
    for a, b in edges:
        glVertex3fv(a)
        glVertex3fv(b)
    glEnd()

    glLineWidth(2.5)
    axis_len = s * 0.35

    glBegin(GL_LINES)
    glColor4f(1.0, 0.25, 0.25, 0.85)
    glVertex3f(-axis_len, 0, 0)
    glVertex3f(axis_len, 0, 0)
    glColor4f(0.25, 1.0, 0.35, 0.85)
    glVertex3f(0, -axis_len, 0)
    glVertex3f(0, axis_len, 0)
    glColor4f(0.25, 0.55, 1.0, 0.85)
    glVertex3f(0, 0, -axis_len)
    glVertex3f(0, 0, axis_len)
    glEnd()

    glPointSize(8.0)
    glBegin(GL_POINTS)
    glColor4f(1.0, 1.0, 0.0, 0.9)
    glVertex3f(0, 0, 0)
    glEnd()

    glDisable(GL_BLEND)
    glLineWidth(1.0)
    glPointSize(1.0)
    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)


def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.08, 0.08, 0.10, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.12, 0.12, 0.12, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 24.0)


def select_active_lamps(lamp_lights=None, camera_pos=None, max_lamp_lights=6):
    if not lamp_lights:
        return []

    active_lamps = list(lamp_lights)
    if camera_pos is not None:
        cam_x, cam_y, cam_z = camera_pos
        active_lamps.sort(
            key=lambda lamp: (
                (lamp["x"] - cam_x) ** 2 +
                (lamp["y"] - cam_y) ** 2 +
                (lamp["z"] - cam_z) ** 2
            )
        )
    return active_lamps[:max(0, min(max_lamp_lights, 7))]


def configure_lighting(fill_direction, lamp_lights=None, camera_pos=None, max_lamp_lights=6):
    glEnable(GL_LIGHTING)

    for light_id in range(GL_LIGHT0, GL_LIGHT7 + 1):
        glDisable(light_id)

    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [fill_direction[0], fill_direction[1], fill_direction[2], 0.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.10, 0.11, 0.14, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.32, 0.34, 0.40, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.14, 0.16, 0.20, 1.0])

    for idx, lamp in enumerate(select_active_lamps(lamp_lights, camera_pos, max_lamp_lights), start=1):
        light_id = GL_LIGHT0 + idx
        glEnable(light_id)
        glLightfv(light_id, GL_POSITION, [lamp["x"], lamp["y"], lamp["z"], 1.0])
        glLightfv(light_id, GL_AMBIENT, [0.05, 0.04, 0.025, 1.0])
        glLightfv(light_id, GL_DIFFUSE, [0.92, 0.78, 0.48, 1.0])
        glLightfv(light_id, GL_SPECULAR, [0.28, 0.22, 0.12, 1.0])
        glLightf(light_id, GL_CONSTANT_ATTENUATION, 0.35)
        glLightf(light_id, GL_LINEAR_ATTENUATION, 0.08)
        glLightf(light_id, GL_QUADRATIC_ATTENUATION, 0.012)


def _shadow_matrix(light_pos, plane):
    lx, ly, lz, lw = light_pos
    a, b, c, d = plane
    dot = a * lx + b * ly + c * lz + d * lw
    mat = [
        [dot - lx * a, -lx * b, -lx * c, -lx * d],
        [-ly * a, dot - ly * b, -ly * c, -ly * d],
        [-lz * a, -lz * b, dot - lz * c, -lz * d],
        [-lw * a, -lw * b, -lw * c, dot - lw * d],
    ]
    flat = []
    for col in range(4):
        for row in range(4):
            flat.append(mat[row][col])
    return (ctypes.c_float * 16)(*flat)


def draw_projected_shadow(light_pos, shadow_y, draw_fn, alpha=0.04):
    plane = (0.0, 1.0, 0.0, -shadow_y)
    shadow_mat = _shadow_matrix(light_pos, plane)

    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_POLYGON_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(-1.0, -1.0)

    glPushMatrix()
    glMultMatrixf(shadow_mat)
    glColor4f(0.0, 0.0, 0.0, alpha)
    draw_fn()
    glPopMatrix()

    glPopAttrib()
