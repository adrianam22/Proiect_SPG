import math
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_tree(x, y, z, trunk_h=3.0, trunk_r=0.22, crown_h=4.5, crown_r=1.8,
              tex_bark=None, tex_leaves=None):
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)

    q = gluNewQuadric()
    gluQuadricTexture(q, GL_TRUE)
    gluQuadricNormals(q, GLU_SMOOTH)

    if tex_bark:
        glBindTexture(GL_TEXTURE_2D, tex_bark)
    glColor3f(0.55, 0.38, 0.18)
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, trunk_r, trunk_r * 0.6, trunk_h, 8, 2)
    glPopMatrix()

    if tex_leaves:
        glBindTexture(GL_TEXTURE_2D, tex_leaves)
    else:
        glDisable(GL_TEXTURE_2D)
    glColor3f(0.18, 0.52, 0.15)
    glPushMatrix()
    glTranslatef(x, y + trunk_h * 0.75, z)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, crown_r, 0.0, crown_h, 10, 3)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(x, y + trunk_h * 0.75 + crown_h * 0.45, z)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, crown_r * 0.65, 0.0, crown_h * 0.6, 10, 2)
    glPopMatrix()

    gluDeleteQuadric(q)
    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)

def draw_lamppost(x, y, z, pole_h=5.5, pole_r=0.09, globe_r=0.28):
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)

    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)

    glColor3f(0.30, 0.30, 0.32)
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, pole_r, pole_r * 0.7, pole_h, 7, 1)
    gluDisk(q, 0, pole_r * 1.6, 7, 1)
    glPopMatrix()

    glColor3f(0.28, 0.28, 0.30)
    arm_len = 0.7
    arm_y = y + pole_h - 0.1
    glPushMatrix()
    glTranslatef(x, arm_y, z)
    glRotatef(90, 0, 1, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, pole_r * 0.6, pole_r * 0.6, arm_len, 6, 1)
    glPopMatrix()

    glColor3f(1.0, 0.92, 0.60)
    glPushMatrix()
    glTranslatef(x + arm_len, arm_y - globe_r * 0.2, z)
    gluSphere(q, globe_r, 10, 10)
    glPopMatrix()

    glColor3f(0.28, 0.28, 0.30)
    glPushMatrix()
    glTranslatef(x + arm_len, arm_y - globe_r * 0.2 + globe_r, z)
    gluDisk(q, 0, globe_r * 1.1, 10, 1)
    glPopMatrix()

    gluDeleteQuadric(q)
    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)

def draw_bench(x, y, z, length=2.2, angle_y=0.0):
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    glColor3f(0.55, 0.38, 0.22)

    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle_y, 0, 1, 0)

    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)

    hl = length / 2
    sw = 0.06
    lh = 0.42
    bh = 0.72
    lw = 0.38

    for sx in [-hl + 0.18, hl - 0.18]:
        glPushMatrix()
        glTranslatef(sx, 0, -lw / 2)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(q, sw, sw, lh, 5, 1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(sx, 0, lw / 2)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(q, sw, sw, bh, 5, 1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(sx, 0.10, -lw / 2)
        glRotatef(90, 1, 0, 0)
        gluCylinder(q, sw * 0.8, sw * 0.8, lw, 5, 1)
        glPopMatrix()

    glColor3f(0.62, 0.43, 0.25)
    plank_w = lw / 3.2
    for pz in [-lw / 2 + plank_w * 0.3, 0, lw / 2 - plank_w * 0.3]:
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-hl, lh, pz - sw / 2)
        glVertex3f(hl, lh, pz - sw / 2)
        glVertex3f(hl, lh, pz + sw / 2)
        glVertex3f(-hl, lh, pz + sw / 2)
        glNormal3f(0, 0, -1)
        glVertex3f(-hl, lh - sw, pz - sw / 2)
        glVertex3f(hl, lh - sw, pz - sw / 2)
        glVertex3f(hl, lh, pz - sw / 2)
        glVertex3f(-hl, lh, pz - sw / 2)
        glEnd()

    glColor3f(0.58, 0.40, 0.22)
    back_z = lw / 2 - sw
    for bk_h in [bh - 0.22, bh - 0.08]:
        glBegin(GL_QUADS)
        glNormal3f(0, 0, -1)
        glVertex3f(-hl, bk_h - sw, back_z)
        glVertex3f(hl, bk_h - sw, back_z)
        glVertex3f(hl, bk_h, back_z)
        glVertex3f(-hl, bk_h, back_z)
        glNormal3f(0, 1, 0)
        glVertex3f(-hl, bk_h, back_z)
        glVertex3f(hl, bk_h, back_z)
        glVertex3f(hl, bk_h, back_z + sw)
        glVertex3f(-hl, bk_h, back_z + sw)
        glEnd()

    gluDeleteQuadric(q)
    glPopMatrix()

    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)


def draw_billboard(x, y, z, tex, width=5.0, height=7.0):
    mv = glGetFloatv(GL_MODELVIEW_MATRIX)
    rx, ry, rz = float(mv[0][0]), float(mv[0][1]), float(mv[0][2])
    ux, uy, uz = float(mv[1][0]), float(mv[1][1]), float(mv[1][2])

    hw = width / 2.0
    x0 = x - rx * hw
    y0 = y
    z0 = z - rz * hw
    x1 = x + rx * hw
    y1 = y
    z1 = z + rz * hw
    x2 = x + rx * hw + ux * height
    y2 = y + uy * height
    z2 = z + rz * hw + uz * height
    x3 = x - rx * hw + ux * height
    y3 = y + uy * height
    z3 = z - rz * hw + uz * height

    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.05)
    glDepthMask(GL_FALSE)

    glBindTexture(GL_TEXTURE_2D, tex)
    glColor4f(1.0, 1.0, 1.0, 1.0)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(x0, y0, z0)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(x1, y1, z1)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(x2, y2, z2)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(x3, y3, z3)
    glEnd()

    glPopAttrib()

def load_billboard_texture(path):
    from PIL import Image as PILImage

    def next_pow2(n):
        p = 1
        while p < n:
            p <<= 1
        return p

    img = PILImage.open(path).convert("RGBA")
    max_size = 2048
    new_w = min(max_size, next_pow2(img.width))
    new_h = min(max_size, next_pow2(img.height))
    if (new_w, new_h) != (img.width, img.height):
        img = img.resize((new_w, new_h), PILImage.LANCZOS)
    img = img.transpose(PILImage.FLIP_TOP_BOTTOM)
    data = img.tobytes()

    tid = int(glGenTextures(1))
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, data)
    glGenerateMipmap(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    return tid


def draw_all_objects(base_y, textures):
    from circuit import (CIRCUIT_CX as CX, CIRCUIT_CZ as CZ,
                         CIRCUIT_W as CW, CIRCUIT_H as CH,
                         CORNER_R as CR, ROAD_WIDTH as RW,
                         CORNER_SEGS as CSEGS,
                         _build_centerline, _smooth_normals)

    tb = textures.get('bark')
    tl = textures.get('leaves')
    tree_billboards = textures.get('tree_billboard') or []
    only_extras = textures.get('_only_lamps_benches', False)
    glb_lamp = textures.get('glb_lamp')
    glb_bench = textures.get('glb_bench')
    _draw_glb = textures.get('draw_glb_model')
    y = base_y

    _pts = _build_centerline(CX, CZ, CW, CH, CR, CSEGS)
    _nrm = _smooth_normals(_pts)
    _N = len(_pts)
    _arc = [0.0]
    for i in range(1, _N):
        dx = _pts[i][0] - _pts[i - 1][0]
        dz = _pts[i][1] - _pts[i - 1][1]
        _arc.append(_arc[-1] + math.sqrt(dx * dx + dz * dz))
    dx = _pts[0][0] - _pts[-1][0]
    dz = _pts[0][1] - _pts[-1][1]
    _total = _arc[-1] + math.sqrt(dx * dx + dz * dz)

    def _pts_on_circuit(n, dist_from_center, phase=0.0):
        result = []
        for k in range(n):
            target = (_total * k / n + phase) % _total
            for i in range(_N):
                i_next = (i + 1) % _N
                l0 = _arc[i]
                l1 = _arc[i_next] if i_next != 0 else _total
                if l1 < l0:
                    l1 = _total
                if l0 <= target <= l1:
                    t = (target - l0) / max(l1 - l0, 1e-9)
                    px = _pts[i][0] + t * (_pts[i_next][0] - _pts[i][0])
                    pz = _pts[i][1] + t * (_pts[i_next][1] - _pts[i][1])
                    nx = _nrm[i][0] + t * (_nrm[i_next][0] - _nrm[i][0])
                    nz = _nrm[i][1] + t * (_nrm[i_next][1] - _nrm[i][1])
                    ln = math.sqrt(nx * nx + nz * nz) + 1e-9
                    nx, nz = nx / ln, nz / ln
                    result.append((px + nx * dist_from_center, pz + nz * dist_from_center, nx, nz))
                    break
        return result

    n_trees = 16
    if not only_extras:
        tree_pts = _pts_on_circuit(n_trees, dist_from_center=-(RW / 2 + 1.6), phase=0.0)
        if tree_billboards:
            n_tex = len(tree_billboards)
            for i, (px, pz, nx, nz) in enumerate(tree_pts):
                draw_billboard(px, y, pz, tree_billboards[i % n_tex], width=4.5, height=7.0)
        else:
            for px, pz, nx, nz in tree_pts:
                draw_tree(px, y, pz, trunk_h=2.8, trunk_r=0.20, crown_h=4.2, crown_r=1.7,
                          tex_bark=tb, tex_leaves=tl)

    n_benches = 8
    phase_bench = _total / (n_trees * 2)
    bench_pts = _pts_on_circuit(n_benches, dist_from_center=-(RW / 2 + 0.9), phase=phase_bench)
    for px, pz, nx, nz in bench_pts:
        bx = px - nx * 1.2
        bz = pz - nz * 1.2
        angle_deg = math.degrees(math.atan2(-nx, -nz))
        tx = -nz
        tz = nx
        lamp_gap = 2.8
        lamp_pos = (bx + tx * lamp_gap, bz + tz * lamp_gap)
        if glb_lamp and _draw_glb:
            lamp_scale = 5.0 / max(glb_lamp.get('height', 1.1), 0.1)
            _draw_glb(glb_lamp, lamp_pos[0], y, lamp_pos[1], scale=lamp_scale, rot_y=angle_deg)
        else:
            draw_lamppost(lamp_pos[0], y, lamp_pos[1], pole_h=5.5)

        if glb_bench and _draw_glb:
            bench_scale = 0.8 / max(glb_bench.get('height', 1.0), 0.1)
            _draw_glb(glb_bench, bx, y, bz, scale=bench_scale, rot_y=angle_deg)
        else:
            draw_bench(bx, y, bz, angle_y=angle_deg)
