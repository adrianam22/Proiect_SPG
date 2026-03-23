from OpenGL.GL import *

from config import CUBE_S


def draw_skybox(tex_top, tex_front, tex_back, tex_left, tex_right, s=CUBE_S):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glColor3f(1, 1, 1)

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


def draw_ground(tex, s=CUBE_S, rep=1.0):
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    glBindTexture(GL_TEXTURE_2D, tex)
    glColor3f(1, 1, 1)
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
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.6, 1.0, 0.4, 0.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.35, 0.35, 0.35, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.85, 0.70, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.15, 0.15, 0.15, 1.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
