import math
import ctypes
import numpy as np
from OpenGL.GL import *


# teren cu un singur "munte" mic in colt si restul plat
# cu cat un punct e mai departe de varf, cu atat inaltimea scade exponential
def generate_heightmap_fbm(grid, max_height=14.0, seed=42):
    size = grid + 1
    h = np.zeros((size, size), dtype=np.float32)

    def gaussian_peak(cx, cy, height, radius):
        for y in range(size):
            for x in range(size):
                dx = (x - cx) / radius
                dy = (y - cy) / radius
                d = dx * dx + dy * dy
                h[y, x] += height * math.exp(-d * 2.5)

    gaussian_peak(
        cx=int(size * 0.85),
        cy=int(size * 0.15),
        height=0.25,
        radius=size * 0.18
    )
    rng = np.random.default_rng(seed)
    noise = rng.random((size, size)).astype(np.float32) - 0.5
    h += noise * 0.0

    h = np.clip(h, 0, 1)

    return (h * max_height).astype(np.float32)


def build_terrain(grid, size, hmap):
    step = size / grid
    half = size / 2.0
    verts = []
    for i in range(grid + 1):
        for j in range(grid + 1):
            x = -half + i * step
            z = -half + j * step
            y = float(hmap[i, j])
            hpx = hmap[min(i + 1, grid), j]
            hmx = hmap[max(i - 1, 0), j]
            hpz = hmap[i, min(j + 1, grid)]
            hmz = hmap[i, max(j - 1, 0)]
            nx_ = (hmx - hpx) / (2 * step)
            nz_ = (hmz - hpz) / (2 * step)
            ny_ = 1.0
            ln = math.sqrt(nx_ * nx_ + ny_ * ny_ + nz_ * nz_)
            verts.extend([x, y, z, nx_ / ln, ny_ / ln, nz_ / ln, i / grid * 1.0, j / grid * 1.0])
    indices = []
    for i in range(grid):
        for j in range(grid):
            a = i * (grid + 1) + j
            b = a + 1
            c = a + (grid + 1)
            d = c + 1
            indices.extend([a, c, b, b, c, d])
    v_arr = np.array(verts, dtype=np.float32)
    i_arr = np.array(indices, dtype=np.uint32)
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, v_arr.nbytes, v_arr, GL_STATIC_DRAW)
    ibo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, i_arr.nbytes, i_arr, GL_STATIC_DRAW)
    stride = 8 * 4
    glVertexPointer(3, GL_FLOAT, stride, ctypes.c_void_p(0))
    glNormalPointer(GL_FLOAT, stride, ctypes.c_void_p(12))
    glTexCoordPointer(2, GL_FLOAT, stride, ctypes.c_void_p(24))
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glBindVertexArray(0)
    return int(vao), int(ibo), len(indices), float(np.max(np.abs(hmap)))


def draw_terrain(vao, ibo, cnt, tex_grass):
    glEnable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glBindVertexArray(vao)
    glBindTexture(GL_TEXTURE_2D, tex_grass)
    glColor3f(1, 1, 1)
    glDrawElements(GL_TRIANGLES, cnt, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)
    glEnable(GL_LIGHTING)
