import math
import ctypes
import numpy as np
from OpenGL.GL import *

ROAD_TEX_NAME = "road1.jpg"
CIRCUIT_CX = 18.0
CIRCUIT_CZ = -18.0
CIRCUIT_W = 48.0
CIRCUIT_H = 30.0
CORNER_R = 7.0
ROAD_WIDTH = 6.5
CORNER_SEGS = 18
ROAD_LIFT = 0.05
TEX_SCALE = 1
#construieste forma circuitului
def _build_centerline(cx, cz, W, H, R, segs):
    # cx, cz = centrul circuitului
    # W, H = latime si inaltime
    # R = raza colturilor rotunjite
    # segs = cate segmente are fiecare colt
    hw, hh = W / 2, H / 2
    arcs = [
        ((cx + hw - R, cz - hh + R), -math.pi / 2, 0.0),
        ((cx + hw - R, cz + hh - R), 0.0, math.pi / 2),
        ((cx - hw + R, cz + hh - R), math.pi / 2, math.pi),
        ((cx - hw + R, cz - hh + R), math.pi, 3 * math.pi / 2),
    ]
    pts = []
    for (acx, acz), a_start, a_end in arcs:
        for s in range(segs):
            t = s / segs
            a = a_start + t * (a_end - a_start)
            pts.append((acx + R * math.cos(a), acz + R * math.sin(a)))
    return pts
# calculeaza directia drumului
def _smooth_normals(pts):
    N = len(pts)
    normals = []
    for i in range(N):
        prev = pts[(i - 1) % N]
        curr = pts[i]
        nxt = pts[(i + 1) % N]

        tx1 = curr[0] - prev[0]
        tz1 = curr[1] - prev[1]
        l1 = math.sqrt(tx1 * tx1 + tz1 * tz1) + 1e-12
        tx1, tz1 = tx1 / l1, tz1 / l1

        tx2 = nxt[0] - curr[0]
        tz2 = nxt[1] - curr[1]
        l2 = math.sqrt(tx2 * tx2 + tz2 * tz2) + 1e-12
        tx2, tz2 = tx2 / l2, tz2 / l2

        tx = (tx1 + tx2) * 0.5
        tz = (tz1 + tz2) * 0.5
        lt = math.sqrt(tx * tx + tz * tz) + 1e-12
        tx, tz = tx / lt, tz / lt
        normals.append((-tz, tx))
    return normals

#construieste modelul 3d pt circuitului (vertexi + indecsi)
def build_circuit(circuit_y, cx=CIRCUIT_CX, cz=CIRCUIT_CZ, W=CIRCUIT_W,
                  H=CIRCUIT_H, R=CORNER_R, road_width=ROAD_WIDTH,
                  segs=CORNER_SEGS):
    pts = _build_centerline(cx, cz, W, H, R, segs)
    normals = _smooth_normals(pts)
    N = len(pts)

    arc_len = [0.0]
    for i in range(1, N):
        dx = pts[i][0] - pts[i - 1][0]
        dz = pts[i][1] - pts[i - 1][1]
        arc_len.append(arc_len[-1] + math.sqrt(dx * dx + dz * dz))
    dx = pts[0][0] - pts[-1][0]
    dz = pts[0][1] - pts[-1][1]
    total = arc_len[-1] + math.sqrt(dx * dx + dz * dz)

    half = road_width / 2
    verts = []
    indices = []

    for i in range(N):
        px, pz = pts[i]
        nx, nz = normals[i]
        u = arc_len[i] / road_width * TEX_SCALE
        ix = px - nx * half
        iz = pz - nz * half
        ox = px + nx * half
        oz = pz + nz * half
        uf = -u
        verts += [ix, circuit_y, iz, 0, 1, 0, uf, 0.0]
        verts += [ox, circuit_y, oz, 0, 1, 0, uf, 1.0]

    for i in range(N):
        a = i * 2
        b = a + 1
        c = ((i + 1) % N) * 2
        d = c + 1
        indices += [a, c, b, b, c, d]

    v = np.array(verts, dtype=np.float32)
    idx = np.array(indices, dtype=np.uint32)

    vao = int(glGenVertexArrays(1))
    glBindVertexArray(vao)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, v.nbytes, v, GL_STATIC_DRAW)

    ibo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, idx.nbytes, idx, GL_STATIC_DRAW)

    stride = 8 * 4
    glVertexPointer(3, GL_FLOAT, stride, ctypes.c_void_p(0))
    glNormalPointer(GL_FLOAT, stride, ctypes.c_void_p(12))
    glTexCoordPointer(2, GL_FLOAT, stride, ctypes.c_void_p(24))
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    glBindVertexArray(0)
    return vao, ibo, len(indices)
#deseneaza circuitul
def draw_circuit(vao, ibo, cnt, tex_road):
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    glBindVertexArray(vao)
    glBindTexture(GL_TEXTURE_2D, tex_road)
    glColor3f(1.0, 1.0, 1.0)
    glDrawElements(GL_TRIANGLES, cnt, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)

#circuitul este pus pe teren
def compute_circuit_y(hmap, grid, terrain_scale, cx=CIRCUIT_CX, cz=CIRCUIT_CZ,
                      W=CIRCUIT_W, H=CIRCUIT_H, R=CORNER_R,
                      segs=CORNER_SEGS, lift=ROAD_LIFT):
    half_t = terrain_scale / 2.0
    step = terrain_scale / grid
    pts = _build_centerline(cx, cz, W, H, R, segs)
    heights = []
    for (px, pz) in pts:
        gi = int((px + half_t) / step)
        gj = int((pz + half_t) / step)
        gi = max(0, min(grid, gi))
        gj = max(0, min(grid, gj))
        heights.append(float(hmap[gi, gj]))
    return float(np.mean(heights)) + lift
