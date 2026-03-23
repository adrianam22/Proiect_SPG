import math
import numpy as np


def sample_height(hmap, size, x, z):
    grid = hmap.shape[0] - 1
    half = size / 2.0
    u = (x + half) / size
    v = (z + half) / size
    u = max(0.0, min(1.0, u))
    v = max(0.0, min(1.0, v))
    fx = u * grid
    fz = v * grid
    x0 = int(math.floor(fx))
    z0 = int(math.floor(fz))
    x1 = min(x0 + 1, grid)
    z1 = min(z0 + 1, grid)
    tx = fx - x0
    tz = fz - z0
    h00 = float(hmap[x0, z0])
    h10 = float(hmap[x1, z0])
    h01 = float(hmap[x0, z1])
    h11 = float(hmap[x1, z1])
    h0 = h00 * (1.0 - tx) + h10 * tx
    h1 = h01 * (1.0 - tx) + h11 * tx
    return h0 * (1.0 - tz) + h1 * tz


def find_track_center(hmap, size, outer_half_x, outer_half_z):
    grid = hmap.shape[0] - 1
    step = size / grid
    hx = max(1, int(outer_half_x / step))
    hz = max(1, int(outer_half_z / step))
    best = (grid // 2, grid // 2)
    best_max = 1e9
    for i in range(hx, grid - hx, 3):
        for j in range(hz, grid - hz, 3):
            region = hmap[i - hx:i + hx + 1, j - hz:j + hz + 1]
            local_max = float(np.max(region))
            if local_max < best_max:
                best_max = local_max
                best = (i, j)
    cx = -size / 2.0 + best[0] * step
    cz = -size / 2.0 + best[1] * step
    return cx, cz, best_max
