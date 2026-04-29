import math
from OpenGL.GL import *
from OpenGL.GLU import *

LAMP_POLE_H = 5.5
LAMP_ARM_LEN = 0.0
LAMP_HEAD_BASE_Y = 0.18
LAMP_HOUSING_HALF_W = 0.15
LAMP_HOUSING_H = 0.50
LAMP_ROOF_H = 0.10
LAMP_EFFECT_OFFSET_X = 0.0
LAMP_EFFECT_OFFSET_Y = 0.02
LAMP_FRAME_OFFSET_Y = -0.22
LAMP_EFFECT_OFFSET_Z = 0.0
LAMP_BENCH_SHADOW_OFFSET_INWARD = 0.06
LAMP_BENCH_SHADOW_OFFSET_ALONG_BENCH = 0.0
LAMP_BENCH_SHADOW_START_FORWARD = -0.06
LAMP_BENCH_SHADOW_WORLD_OFFSET_X = 0.0
LAMP_BENCH_SHADOW_WORLD_OFFSET_Z = 0.0


def draw_tree(x, y, z, trunk_h=3.0, trunk_r=0.22, crown_h=4.5, crown_r=1.8,
              tex_bark=None, tex_leaves=None, shadow_pass=False):
    if shadow_pass:
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
    else:
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)

    q = gluNewQuadric()
    gluQuadricTexture(q, GL_FALSE if shadow_pass else GL_TRUE)
    gluQuadricNormals(q, GLU_SMOOTH)

    if tex_bark and not shadow_pass:
        glBindTexture(GL_TEXTURE_2D, tex_bark)
    glColor4f(0.0, 0.0, 0.0, 0.22) if shadow_pass else glColor3f(0.55, 0.38, 0.18)
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, trunk_r, trunk_r * 0.6, trunk_h, 8, 2)
    glPopMatrix()

    if tex_leaves and not shadow_pass:
        glBindTexture(GL_TEXTURE_2D, tex_leaves)
    elif not shadow_pass:
        glDisable(GL_TEXTURE_2D)
    glColor4f(0.0, 0.0, 0.0, 0.22) if shadow_pass else glColor3f(0.18, 0.52, 0.15)
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
    if not shadow_pass:
        glEnable(GL_TEXTURE_2D)

def draw_lamppost(x, y, z, pole_h=LAMP_POLE_H, pole_r=0.09, shadow_pass=False):
    glDisable(GL_TEXTURE_2D)
    if shadow_pass:
        glDisable(GL_LIGHTING)
    else:
        glEnable(GL_LIGHTING)

    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)

    glColor4f(0.0, 0.0, 0.0, 0.22) if shadow_pass else glColor3f(0.08, 0.08, 0.10)
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, pole_r * 1.35, pole_r * 1.1, 0.16, 10, 1)
    glTranslatef(0.0, 0.0, 0.16)
    gluCylinder(q, pole_r, pole_r * 0.82, pole_h - 0.42, 10, 3)
    glTranslatef(0.0, 0.0, pole_h - 0.42)
    gluCylinder(q, pole_r * 0.82, pole_r * 0.66, 0.26, 10, 1)
    glPopMatrix()

    glColor4f(0.0, 0.0, 0.0, 0.22) if shadow_pass else glColor3f(0.10, 0.10, 0.12)
    head_x = x
    head_y = y + pole_h + LAMP_HEAD_BASE_Y
    head_z = z

    glPushMatrix()
    glTranslatef(head_x, y + pole_h - 0.16, head_z)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(q, pole_r * 0.28, pole_r * 0.22, LAMP_HEAD_BASE_Y + 0.04, 8, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(head_x, head_y + LAMP_FRAME_OFFSET_Y, head_z)
    glColor4f(0.0, 0.0, 0.0, 0.22) if shadow_pass else glColor3f(0.08, 0.08, 0.10)

    frame_w = LAMP_HOUSING_HALF_W
    frame_h = LAMP_HOUSING_H
    frame_d = LAMP_HOUSING_HALF_W
    bar = 0.024

    for sx in (-frame_w, frame_w):
        for sz in (-frame_d, frame_d):
            glPushMatrix()
            glTranslatef(sx, -frame_h * 0.5, sz)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(q, bar, bar, frame_h, 8, 1)
            glPopMatrix()

    glBegin(GL_QUADS)
    glVertex3f(-frame_w, frame_h * 0.5, -frame_d)
    glVertex3f(frame_w, frame_h * 0.5, -frame_d)
    glVertex3f(frame_w, frame_h * 0.5, frame_d)
    glVertex3f(-frame_w, frame_h * 0.5, frame_d)

    glVertex3f(-frame_w * 0.82, -frame_h * 0.5, -frame_d * 0.82)
    glVertex3f(-frame_w * 0.82, -frame_h * 0.5, frame_d * 0.82)
    glVertex3f(frame_w * 0.82, -frame_h * 0.5, frame_d * 0.82)
    glVertex3f(frame_w * 0.82, -frame_h * 0.5, -frame_d * 0.82)
    glEnd()

    glBegin(GL_TRIANGLES)
    glVertex3f(-frame_w * 1.05, frame_h * 0.5, frame_d * 1.05)
    glVertex3f(frame_w * 1.05, frame_h * 0.5, frame_d * 1.05)
    glVertex3f(0.0, frame_h * 0.5 + LAMP_ROOF_H, 0.0)

    glVertex3f(frame_w * 1.05, frame_h * 0.5, -frame_d * 1.05)
    glVertex3f(-frame_w * 1.05, frame_h * 0.5, -frame_d * 1.05)
    glVertex3f(0.0, frame_h * 0.5 + LAMP_ROOF_H, 0.0)

    glVertex3f(frame_w * 1.05, frame_h * 0.5, frame_d * 1.05)
    glVertex3f(frame_w * 1.05, frame_h * 0.5, -frame_d * 1.05)
    glVertex3f(0.0, frame_h * 0.5 + LAMP_ROOF_H, 0.0)

    glVertex3f(-frame_w * 1.05, frame_h * 0.5, -frame_d * 1.05)
    glVertex3f(-frame_w * 1.05, frame_h * 0.5, frame_d * 1.05)
    glVertex3f(0.0, frame_h * 0.5 + LAMP_ROOF_H, 0.0)
    glEnd()
    glPopMatrix()

    gluDeleteQuadric(q)
    glColor3f(1, 1, 1)
    glEnable(GL_TEXTURE_2D)

def draw_bench(x, y, z, length=2.2, angle_y=0.0, shadow_pass=False):
    glDisable(GL_TEXTURE_2D)
    if shadow_pass:
        glDisable(GL_LIGHTING)
        glColor4f(0.0, 0.0, 0.0, 0.22)
    else:
        glEnable(GL_LIGHTING)
        glColor3f(0.34, 0.24, 0.14)

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

    glColor4f(0.0, 0.0, 0.0, 0.22) if shadow_pass else glColor3f(0.40, 0.28, 0.17)
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

    glColor4f(0.0, 0.0, 0.0, 0.22) if shadow_pass else glColor3f(0.30, 0.21, 0.13)
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


def draw_bench_shadow_proxy(x, y, z, angle_y=0.0, length=2.2, width=0.46, seat_h=0.42, back_h=0.72):
    hl = length / 2.0
    hw = width / 2.0
    seat_thickness = 0.08
    back_thickness = 0.08

    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle_y, 0, 1, 0)

    glBegin(GL_QUADS)
    # Seat proxy.
    glVertex3f(-hl, seat_h, -hw)
    glVertex3f(hl, seat_h, -hw)
    glVertex3f(hl, seat_h, hw)
    glVertex3f(-hl, seat_h, hw)

    glVertex3f(-hl, seat_h - seat_thickness, -hw)
    glVertex3f(-hl, seat_h, -hw)
    glVertex3f(hl, seat_h, -hw)
    glVertex3f(hl, seat_h - seat_thickness, -hw)

    glVertex3f(-hl, seat_h - seat_thickness, hw)
    glVertex3f(hl, seat_h - seat_thickness, hw)
    glVertex3f(hl, seat_h, hw)
    glVertex3f(-hl, seat_h, hw)

    # Backrest proxy.
    glVertex3f(-hl, back_h, hw)
    glVertex3f(hl, back_h, hw)
    glVertex3f(hl, seat_h + 0.04, hw)
    glVertex3f(-hl, seat_h + 0.04, hw)

    glVertex3f(-hl, back_h, hw + back_thickness)
    glVertex3f(-hl, back_h, hw)
    glVertex3f(hl, back_h, hw)
    glVertex3f(hl, back_h, hw + back_thickness)
    glEnd()

    glPopMatrix()


def draw_bench_leg_shadow_proxy(x, y, z, angle_y=0.0, length=2.2):
    hl = length / 2.0
    front_back_half = 0.19
    leg_half = 0.045
    front_h = 0.42
    back_h = 0.72

    def draw_leg_box(cx, cz, h):
        x0 = cx - leg_half
        x1 = cx + leg_half
        z0 = cz - leg_half
        z1 = cz + leg_half
        y0 = 0.0
        y1 = h

        glBegin(GL_QUADS)
        glVertex3f(x0, y0, z0)
        glVertex3f(x1, y0, z0)
        glVertex3f(x1, y1, z0)
        glVertex3f(x0, y1, z0)

        glVertex3f(x1, y0, z1)
        glVertex3f(x0, y0, z1)
        glVertex3f(x0, y1, z1)
        glVertex3f(x1, y1, z1)

        glVertex3f(x0, y0, z1)
        glVertex3f(x0, y0, z0)
        glVertex3f(x0, y1, z0)
        glVertex3f(x0, y1, z1)

        glVertex3f(x1, y0, z0)
        glVertex3f(x1, y0, z1)
        glVertex3f(x1, y1, z1)
        glVertex3f(x1, y1, z0)
        glEnd()

    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle_y, 0, 1, 0)

    for sx in (-hl + 0.18, hl - 0.18):
        draw_leg_box(sx, -front_back_half, front_h)
        draw_leg_box(sx, front_back_half, back_h)

    glPopMatrix()


def draw_bench_lamp_shadow(lamp_x, lamp_z, bench_x, y, bench_z, angle_y=0.0, length=2.2, alpha=0.22):
    angle_rad = math.radians(angle_y)
    along_x = math.cos(angle_rad)
    along_z = math.sin(angle_rad)
    side_x = -math.sin(angle_rad)
    side_z = math.cos(angle_rad)

    leg_along = length * 0.5 - 0.18
    leg_side = 0.19
    lamp_side = (lamp_x - bench_x) * side_x + (lamp_z - bench_z) * side_z
    side_sign = 1.0 if lamp_side >= 0.0 else -1.0

    leg_positions = []
    for sx in (-leg_along, leg_along):
        leg_positions.append((
            bench_x + along_x * sx + side_x * leg_side * side_sign,
            bench_z + along_z * sx + side_z * leg_side * side_sign,
            -1.0 if sx < 0.0 else 1.0,
        ))

    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_POLYGON_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(-1.0, -1.0)

    base_y = y + 0.028
    start_mid_x = (leg_positions[0][0] + leg_positions[1][0]) * 0.5
    start_mid_z = (leg_positions[0][1] + leg_positions[1][1]) * 0.5

    dir_x = start_mid_x - lamp_x
    dir_z = start_mid_z - lamp_z
    dir_len = math.sqrt(dir_x * dir_x + dir_z * dir_z) + 1e-9
    dir_x /= dir_len
    dir_z /= dir_len
    inward_x = -side_x * side_sign
    inward_z = -side_z * side_sign
    shadow_shift_x = (
        inward_x * LAMP_BENCH_SHADOW_OFFSET_INWARD
        + along_x * LAMP_BENCH_SHADOW_OFFSET_ALONG_BENCH
        + LAMP_BENCH_SHADOW_WORLD_OFFSET_X
    )
    shadow_shift_z = (
        inward_z * LAMP_BENCH_SHADOW_OFFSET_INWARD
        + along_z * LAMP_BENCH_SHADOW_OFFSET_ALONG_BENCH
        + LAMP_BENCH_SHADOW_WORLD_OFFSET_Z
    )

    layers = (
        (0.00, 0.00, 0.75, 0.12, 1.00),
        (0.06, -0.03, 0.95, 0.18, 0.55),
        (-0.05, 0.04, 1.08, 0.22, 0.34),
    )

    for dir_side_offset, near_push, length_scale, spread_scale, alpha_scale in layers:
        layer_dir_x = dir_x + side_x * dir_side_offset
        layer_dir_z = dir_z + side_z * dir_side_offset
        layer_dir_len = math.sqrt(layer_dir_x * layer_dir_x + layer_dir_z * layer_dir_z) + 1e-9
        layer_dir_x /= layer_dir_len
        layer_dir_z /= layer_dir_len

        near0_x = (
            leg_positions[0][0]
            + shadow_shift_x
            + layer_dir_x * (LAMP_BENCH_SHADOW_START_FORWARD + near_push)
        )
        near0_z = (
            leg_positions[0][1]
            + shadow_shift_z
            + layer_dir_z * (LAMP_BENCH_SHADOW_START_FORWARD + near_push)
        )
        near1_x = (
            leg_positions[1][0]
            + shadow_shift_x
            + layer_dir_x * (LAMP_BENCH_SHADOW_START_FORWARD + near_push)
        )
        near1_z = (
            leg_positions[1][1]
            + shadow_shift_z
            + layer_dir_z * (LAMP_BENCH_SHADOW_START_FORWARD + near_push)
        )

        far0_x = near0_x + layer_dir_x * length_scale - along_x * spread_scale
        far0_z = near0_z + layer_dir_z * length_scale - along_z * spread_scale
        far1_x = near1_x + layer_dir_x * length_scale + along_x * spread_scale
        far1_z = near1_z + layer_dir_z * length_scale + along_z * spread_scale

        glBegin(GL_QUADS)
        glColor4f(0.0, 0.0, 0.0, alpha * alpha_scale)
        glVertex3f(near0_x, base_y, near0_z)
        glVertex3f(near1_x, base_y, near1_z)
        glColor4f(0.0, 0.0, 0.0, 0.0)
        glVertex3f(far1_x, base_y, far1_z)
        glVertex3f(far0_x, base_y, far0_z)
        glEnd()

    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.0, 0.0, 0.0, alpha * 0.72)
    glVertex3f(
        start_mid_x + shadow_shift_x,
        base_y + 0.002,
        start_mid_z + shadow_shift_z,
    )
    for i in range(25):
        ang = 2.0 * math.pi * i / 24.0
        local_u = math.cos(ang) * 0.24
        local_v = math.sin(ang) * 0.10
        glColor4f(0.0, 0.0, 0.0, 0.0)
        glVertex3f(
            start_mid_x + inward_x * 0.05 + along_x * local_u + dir_x * abs(local_v) * 0.45,
            base_y + 0.002,
            start_mid_z + inward_z * 0.05 + along_z * local_u + dir_z * abs(local_v) * 0.45,
        )
    glEnd()

    glPopAttrib()


def _build_circuit_frame():
    from circuit import (CIRCUIT_CX as CX, CIRCUIT_CZ as CZ,
                         CIRCUIT_W as CW, CIRCUIT_H as CH,
                         CORNER_R as CR, CORNER_SEGS as CSEGS,
                         _build_centerline, _smooth_normals)

    pts = _build_centerline(CX, CZ, CW, CH, CR, CSEGS)
    normals = _smooth_normals(pts)
    arc = [0.0]
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i - 1][0]
        dz = pts[i][1] - pts[i - 1][1]
        arc.append(arc[-1] + math.sqrt(dx * dx + dz * dz))
    dx = pts[0][0] - pts[-1][0]
    dz = pts[0][1] - pts[-1][1]
    total = arc[-1] + math.sqrt(dx * dx + dz * dz)
    return pts, normals, arc, total


def _points_on_circuit(n, dist_from_center, phase=0.0):
    pts, normals, arc, total = _build_circuit_frame()
    result = []
    count = len(pts)
    for k in range(n):
        target = (total * k / n + phase) % total
        for i in range(count):
            i_next = (i + 1) % count
            l0 = arc[i]
            l1 = arc[i_next] if i_next != 0 else total
            if l1 < l0:
                l1 = total
            if l0 <= target <= l1:
                t = (target - l0) / max(l1 - l0, 1e-9)
                px = pts[i][0] + t * (pts[i_next][0] - pts[i][0])
                pz = pts[i][1] + t * (pts[i_next][1] - pts[i][1])
                nx = normals[i][0] + t * (normals[i_next][0] - normals[i][0])
                nz = normals[i][1] + t * (normals[i_next][1] - normals[i][1])
                ln = math.sqrt(nx * nx + nz * nz) + 1e-9
                nx, nz = nx / ln, nz / ln
                result.append((px + nx * dist_from_center, pz + nz * dist_from_center, nx, nz))
                break
    return result, total


def get_scene_layout(base_y):
    from circuit import ROAD_WIDTH as RW

    items = {"trees": [], "benches": [], "lamps": []}
    tree_pts, total = _points_on_circuit(16, dist_from_center=-(RW / 2 + 1.6), phase=0.0)
    for px, pz, nx, nz in tree_pts:
        items["trees"].append({
            "x": px,
            "y": base_y,
            "z": pz,
            "nx": nx,
            "nz": nz,
        })

    phase_bench = total / 32.0
    bench_pts, _ = _points_on_circuit(8, dist_from_center=-(RW / 2 + 0.9), phase=phase_bench)
    for px, pz, nx, nz in bench_pts:
        bx = px - nx * 1.2
        bz = pz - nz * 1.2
        angle_deg = math.degrees(math.atan2(-nx, -nz))
        tx = -nz
        tz = nx
        lamp_x = bx + tx * 2.8
        lamp_z = bz + tz * 2.8
        items["benches"].append({
            "x": bx,
            "y": base_y,
            "z": bz,
            "angle_y": angle_deg,
        })
        items["lamps"].append({
            "x": lamp_x,
            "y": base_y,
            "z": lamp_z,
            "angle_y": angle_deg,
            "light_x": lamp_x + LAMP_ARM_LEN,
            "light_y": base_y + LAMP_POLE_H - 0.1,
            "light_z": lamp_z,
        })
    return items


def get_lamp_lights(base_y):
    layout = get_scene_layout(base_y)
    return [
        {"x": lamp["light_x"], "y": lamp["light_y"], "z": lamp["light_z"]}
        for lamp in layout["lamps"]
    ]


def get_lamp_effect_anchor(lamp):
    return (
        lamp["light_x"] + LAMP_EFFECT_OFFSET_X,
        lamp["light_y"] + LAMP_EFFECT_OFFSET_Y,
        lamp["light_z"] + LAMP_EFFECT_OFFSET_Z,
    )


def draw_lamp_bulb(x, y, z, inner_radius=0.055, outer_radius=0.095):
    q = gluNewQuadric()

    glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)

    glColor4f(1.0, 0.95, 0.72, 1.0)
    glPushMatrix()
    glTranslatef(x, y, z)
    gluSphere(q, inner_radius, 14, 14)
    glPopMatrix()

    glColor4f(1.0, 0.72, 0.24, 0.32)
    glPushMatrix()
    glTranslatef(x, y, z)
    gluSphere(q, outer_radius, 14, 14)
    glPopMatrix()

    glPopAttrib()
    gluDeleteQuadric(q)


def draw_lamp_glass(x, y, z, angle_y, width=LAMP_HOUSING_HALF_W * 0.74, height=LAMP_HOUSING_H * 0.74):
    glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)

    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle_y, 0, 1, 0)

    glass_alpha = 0.22
    glow_alpha = 0.10
    inset = width * 0.82
    top = height * 0.5
    bottom = -height * 0.5

    glBegin(GL_QUADS)
    glColor4f(1.0, 0.78, 0.28, glass_alpha)
    glVertex3f(-width, bottom, inset)
    glVertex3f(width, bottom, inset)
    glColor4f(1.0, 0.86, 0.48, glow_alpha)
    glVertex3f(width, top, inset)
    glVertex3f(-width, top, inset)

    glColor4f(1.0, 0.78, 0.28, glass_alpha)
    glVertex3f(width, bottom, -inset)
    glVertex3f(-width, bottom, -inset)
    glColor4f(1.0, 0.86, 0.48, glow_alpha)
    glVertex3f(-width, top, -inset)
    glVertex3f(width, top, -inset)

    glColor4f(1.0, 0.78, 0.28, glass_alpha)
    glVertex3f(inset, bottom, width)
    glVertex3f(inset, bottom, -width)
    glColor4f(1.0, 0.86, 0.48, glow_alpha)
    glVertex3f(inset, top, -width)
    glVertex3f(inset, top, width)

    glColor4f(1.0, 0.78, 0.28, glass_alpha)
    glVertex3f(-inset, bottom, -width)
    glVertex3f(-inset, bottom, width)
    glColor4f(1.0, 0.86, 0.48, glow_alpha)
    glVertex3f(-inset, top, width)
    glVertex3f(-inset, top, -width)
    glEnd()

    glPopMatrix()
    glPopAttrib()


def draw_lamp_glow(x, y, z, radius=0.18):
    mv = glGetFloatv(GL_MODELVIEW_MATRIX)
    right = (float(mv[0][0]), float(mv[0][1]), float(mv[0][2]))
    up = (float(mv[1][0]), float(mv[1][1]), float(mv[1][2]))

    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)

    for scale, alpha in ((1.0, 0.12), (0.70, 0.20), (0.42, 0.30)):
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(1.0, 0.84, 0.38, alpha)
        glVertex3f(x, y, z)
        for i in range(25):
            ang = 2.0 * math.pi * i / 24.0
            dx = math.cos(ang) * radius * scale
            dy = math.sin(ang) * radius * scale
            glColor4f(1.0, 0.64, 0.16, 0.0)
            glVertex3f(
                x + right[0] * dx + up[0] * dy,
                y + right[1] * dx + up[1] * dy,
                z + right[2] * dx + up[2] * dy,
            )
        glEnd()

    glPopAttrib()


def draw_light_pool(x, y, z, angle_y, radius_x=3.6, radius_z=2.0, forward_shift=0.75):
    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)

    angle_rad = math.radians(angle_y)
    dir_x = math.sin(angle_rad)
    dir_z = -math.cos(angle_rad)
    center_x = x + dir_x * forward_shift
    center_z = z + dir_z * forward_shift

    for scale, alpha in ((1.0, 0.30), (0.58, 0.42)):
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(1.0, 0.82, 0.34, alpha)
        glVertex3f(center_x, y, center_z)
        for i in range(33):
            ang = 2.0 * math.pi * i / 32.0
            local_x = math.cos(ang) * radius_x * scale
            local_z = math.sin(ang) * radius_z * scale
            world_x = center_x + local_x * math.cos(angle_rad) - local_z * math.sin(angle_rad)
            world_z = center_z + local_x * math.sin(angle_rad) + local_z * math.cos(angle_rad)
            glColor4f(1.0, 0.68, 0.16, 0.0)
            glVertex3f(world_x, y, world_z)
        glEnd()

    glPopAttrib()


def draw_lamp_shadow(x, y, z, moon_dir=(-0.35, -0.2), length=3.1, width=0.62):
    dx, dz = moon_dir
    ln = math.sqrt(dx * dx + dz * dz) + 1e-9
    dx /= ln
    dz /= ln
    tip_x = x - dx * length
    tip_z = z - dz * length
    side_x = -dz * width
    side_z = dx * width

    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)

    glBegin(GL_TRIANGLES)
    glColor4f(0.0, 0.0, 0.0, 0.22)
    glVertex3f(x, y, z)
    glColor4f(0.0, 0.0, 0.0, 0.02)
    glVertex3f(tip_x + side_x, y, tip_z + side_z)
    glVertex3f(tip_x - side_x, y, tip_z - side_z)
    glEnd()

    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.0, 0.0, 0.0, 0.16)
    glVertex3f(x, y, z)
    for i in range(25):
        ang = 2.0 * math.pi * i / 24.0
        glColor4f(0.0, 0.0, 0.0, 0.0)
        glVertex3f(
            x + math.cos(ang) * 0.85,
            y,
            z + math.sin(ang) * 0.85,
        )
    glEnd()

    glPopAttrib()


def draw_local_lamp_shadow(x, y, z, angle_y, length=1.1, width=0.42, alpha=0.08):
    angle_rad = math.radians(angle_y)
    dir_x = math.sin(angle_rad)
    dir_z = -math.cos(angle_rad)
    center_x = x + dir_x * 0.55
    center_z = z + dir_z * 0.55

    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)

    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.0, 0.0, 0.0, alpha)
    glVertex3f(center_x, y, center_z)
    for i in range(25):
        ang = 2.0 * math.pi * i / 24.0
        local_x = math.cos(ang) * length
        local_z = math.sin(ang) * width
        world_x = center_x + local_x * math.cos(angle_rad) - local_z * math.sin(angle_rad)
        world_z = center_z + local_x * math.sin(angle_rad) + local_z * math.cos(angle_rad)
        glColor4f(0.0, 0.0, 0.0, 0.0)
        glVertex3f(world_x, y, world_z)
    glEnd()

    glPopAttrib()


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


def draw_all_objects(base_y, textures, shadow_pass=False):
    tb = textures.get('bark')
    tl = textures.get('leaves')
    tree_billboards = textures.get('tree_billboard') or []
    only_extras = textures.get('_only_lamps_benches', False)
    shadow_center = textures.get('_shadow_center')
    shadow_radius = textures.get('_shadow_radius')
    skip_lamps = textures.get('_skip_lamps', False)
    glb_bench = textures.get('glb_bench')
    _draw_glb = textures.get('draw_glb_model')
    layout = get_scene_layout(base_y)

    def in_shadow_range(x, z):
        if shadow_center is None or shadow_radius is None:
            return True
        dx = x - shadow_center[0]
        dz = z - shadow_center[1]
        return dx * dx + dz * dz <= shadow_radius * shadow_radius

    if not only_extras:
        if tree_billboards and not shadow_pass:
            n_tex = len(tree_billboards)
            for i, tree in enumerate(layout["trees"]):
                draw_billboard(tree["x"], tree["y"], tree["z"], tree_billboards[i % n_tex], width=4.5, height=7.0)
        else:
            for tree in layout["trees"]:
                if shadow_pass and not in_shadow_range(tree["x"], tree["z"]):
                    continue
                draw_tree(tree["x"], tree["y"], tree["z"], trunk_h=2.8, trunk_r=0.20, crown_h=4.2, crown_r=1.7,
                          tex_bark=tb, tex_leaves=tl, shadow_pass=shadow_pass)

    for lamp in layout["lamps"]:
        if shadow_pass and (skip_lamps or not in_shadow_range(lamp["x"], lamp["z"])):
            continue
        draw_lamppost(lamp["x"], lamp["y"], lamp["z"], pole_h=LAMP_POLE_H, shadow_pass=shadow_pass)

        if not shadow_pass:
            anchor_x, anchor_y, anchor_z = get_lamp_effect_anchor(lamp)
            draw_light_pool(lamp["light_x"], base_y + 0.04, lamp["light_z"], lamp["angle_y"])
            draw_local_lamp_shadow(lamp["x"], base_y + 0.031, lamp["z"], lamp["angle_y"])
            draw_lamp_glass(anchor_x, anchor_y, anchor_z, lamp["angle_y"])
            draw_lamp_bulb(anchor_x, anchor_y, anchor_z)
            draw_lamp_glow(anchor_x, anchor_y, anchor_z)

    for bench in layout["benches"]:
        if shadow_pass and not in_shadow_range(bench["x"], bench["z"]):
            continue
        if glb_bench and _draw_glb:
            bench_scale = 0.8 / max(glb_bench.get('height', 1.0), 0.1)
            _draw_glb(glb_bench, bench["x"], bench["y"], bench["z"], scale=bench_scale,
                      rot_y=bench["angle_y"], shadow_pass=shadow_pass)
        else:
            draw_bench(bench["x"], bench["y"], bench["z"], angle_y=bench["angle_y"], shadow_pass=shadow_pass)
