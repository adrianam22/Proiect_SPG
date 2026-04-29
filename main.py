import os
import sys
import math
import random

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config import WINDOW_W, WINDOW_H, CUBE_S, TERRAIN_GRID, TERRAIN_SCALE, SENSITIVITY, TEXTURE_DIR
from textures import load_texture
from terrain import generate_heightmap_fbm, build_terrain, draw_terrain
from render import (
    configure_lighting,
    draw_projected_shadow,
    draw_ground,
    draw_moon,
    draw_skybox,
    select_active_lamps,
    setup_lighting,
)
from track import find_track_center, sample_height
from circuit import build_circuit, draw_circuit, compute_circuit_y, ROAD_TEX_NAME, ROAD_WIDTH
from object import (
    draw_all_objects,
    draw_bench_lamp_shadow,
    get_lamp_lights,
    get_scene_layout,
    load_billboard_texture,
)
from loader_objects import (
    load_colormap,
    KenneyScene,
    load_glb_model,
    draw_glb_model,
)


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_angle_deg(a, b, t):
    delta = (b - a + 180.0) % 360.0 - 180.0
    return (a + delta * t) % 360.0


def rotate_xz(x, z, yaw_deg):
    yaw_rad = math.radians(yaw_deg)
    cos_yaw = math.cos(yaw_rad)
    sin_yaw = math.sin(yaw_rad)
    return (
        x * cos_yaw + z * sin_yaw,
        -x * sin_yaw + z * cos_yaw,
    )


def build_footprint_collider(x, z, yaw, scale, bbox_min, bbox_max, shrink_x=1.0, shrink_z=1.0):
    local_center_x = (bbox_min[0] + bbox_max[0]) * 0.5 * scale
    local_center_z = (bbox_min[2] + bbox_max[2]) * 0.5 * scale
    offset_x, offset_z = rotate_xz(local_center_x, local_center_z, yaw)
    half_x = max(0.05, (bbox_max[0] - bbox_min[0]) * 0.5 * scale * shrink_x)
    half_z = max(0.05, (bbox_max[2] - bbox_min[2]) * 0.5 * scale * shrink_z)
    return {
        "center": (x + offset_x, z + offset_z),
        "yaw": yaw,
        "half_x": half_x,
        "half_z": half_z,
    }


def get_obb_axes(yaw_deg):
    yaw_rad = math.radians(yaw_deg)
    return (
        (math.cos(yaw_rad), -math.sin(yaw_rad)),
        (math.sin(yaw_rad), math.cos(yaw_rad)),
    )


def obb_intersects(a, b):
    axes = get_obb_axes(a["yaw"]) + get_obb_axes(b["yaw"])
    dx = b["center"][0] - a["center"][0]
    dz = b["center"][1] - a["center"][1]

    for axis_x, axis_z in axes:
        dist = abs(dx * axis_x + dz * axis_z)

        a_axis_x, a_axis_z = get_obb_axes(a["yaw"])
        a_proj = (
            abs(a_axis_x[0] * axis_x + a_axis_x[1] * axis_z) * a["half_x"] +
            abs(a_axis_z[0] * axis_x + a_axis_z[1] * axis_z) * a["half_z"]
        )
        b_axis_x, b_axis_z = get_obb_axes(b["yaw"])
        b_proj = (
            abs(b_axis_x[0] * axis_x + b_axis_x[1] * axis_z) * b["half_x"] +
            abs(b_axis_z[0] * axis_x + b_axis_z[1] * axis_z) * b["half_z"]
        )
        if dist > a_proj + b_proj:
            return False
    return True


def collides_with_any(collider, colliders):
    return any(obb_intersects(collider, other) for other in colliders)


def apply_camera_controls(target, basis, keys, dt):
    move = (28.0 if keys[K_LSHIFT] or keys[K_RSHIFT] else 14.0) * dt
    rot_speed = 75.0 * dt
    yaw_rad = math.radians(basis["yaw"])
    pitch_rad = math.radians(basis["pitch"])
    roll_rad = math.radians(basis["roll"])
    forward = (
        math.sin(yaw_rad) * math.cos(pitch_rad),
        -math.sin(pitch_rad),
        -math.cos(yaw_rad) * math.cos(pitch_rad),
    )
    right = (
        math.cos(yaw_rad),
        0.0,
        math.sin(yaw_rad),
    )
    up = (
        math.sin(roll_rad) * right[0],
        math.cos(roll_rad),
        math.sin(roll_rad) * right[2],
    )

    if keys[K_w]:
        target["x"] += forward[0] * move
        target["y"] += forward[1] * move
        target["z"] += forward[2] * move
    if keys[K_s]:
        target["x"] -= forward[0] * move
        target["y"] -= forward[1] * move
        target["z"] -= forward[2] * move
    if keys[K_a]:
        target["x"] -= right[0] * move
        target["z"] -= right[2] * move
    if keys[K_d]:
        target["x"] += right[0] * move
        target["z"] += right[2] * move
    if keys[K_e]:
        target["x"] += up[0] * move
        target["y"] += up[1] * move
        target["z"] += up[2] * move
    if keys[K_q]:
        target["x"] -= up[0] * move
        target["y"] -= up[1] * move
        target["z"] -= up[2] * move
    if keys[K_j]:
        target["yaw"] = (target["yaw"] - rot_speed) % 360.0
    if keys[K_l]:
        target["yaw"] = (target["yaw"] + rot_speed) % 360.0
    if keys[K_i]:
        target["pitch"] = clamp(target["pitch"] - rot_speed, -89.0, 89.0)
    if keys[K_k]:
        target["pitch"] = clamp(target["pitch"] + rot_speed, -89.0, 89.0)
    if keys[K_u]:
        target["roll"] = clamp(target["roll"] - rot_speed, -60.0, 60.0)
    if keys[K_o]:
        target["roll"] = clamp(target["roll"] + rot_speed, -60.0, 60.0)


def build_chase_camera(car_pos, car_yaw, car_length=3.6, car_height=1.4):
    distance = max(12.0, car_length * 3.35)
    height = max(4.6, car_height * 3.3)
    forward_x, forward_z = rotate_xz(0.0, 1.0, car_yaw)

    return {
        "x": car_pos["x"] - forward_x * distance,
        "y": car_pos["y"] + height,
        "z": car_pos["z"] - forward_z * distance,
        "yaw": (180.0 - car_yaw) % 360.0,
        "pitch": -17.0,
        "roll": 0.0,
    }


def update_bounded_random_mover(mover, dt, half_extent, margin, min_height, max_height):
    mover["turn_timer"] -= dt
    if mover["turn_timer"] <= 0.0:
        ang = random.uniform(-70.0, 70.0)
        mover["yaw"] = (mover["yaw"] + ang) % 360.0
        mover["speed"] = clamp(mover["speed"] + random.uniform(-1.2, 1.4), 4.8, 8.2)
        mover["vertical_speed"] = clamp(
            mover["vertical_speed"] + random.uniform(-1.6, 1.2),
            -2.8,
            1.8,
        )
        mover["turn_timer"] = random.uniform(0.28, 0.82)

    dir_x, dir_z = rotate_xz(0.0, 1.0, mover["yaw"])
    next_x = mover["x"] + dir_x * mover["speed"] * dt
    next_z = mover["z"] + dir_z * mover["speed"] * dt
    low = -half_extent + margin
    high = half_extent - margin
    bounced = False

    if next_x < low or next_x > high:
        mover["yaw"] = (180.0 - mover["yaw"]) % 360.0
        next_x = clamp(next_x, low, high)
        bounced = True
    if next_z < low or next_z > high:
        mover["yaw"] = (-mover["yaw"]) % 360.0
        next_z = clamp(next_z, low, high)
        bounced = True
    if bounced:
        mover["vertical_speed"] = clamp(mover["vertical_speed"] + random.uniform(-0.8, 0.4), -3.0, 1.8)
        mover["turn_timer"] = random.uniform(0.2, 0.6)

    mover["x"] = next_x
    mover["z"] = next_z
    mover["bob_phase"] += dt * mover["bob_speed"]
    mover["base_y"] = clamp(mover["base_y"] + mover["vertical_speed"] * dt, min_height, max_height)
    if mover["base_y"] <= min_height + 0.05:
        mover["vertical_speed"] = abs(mover["vertical_speed"]) * 0.65 + 0.35
    elif mover["base_y"] >= max_height - 0.05:
        mover["vertical_speed"] = -abs(mover["vertical_speed"]) * 0.65

    mover["vertical_speed"] = clamp(
        mover["vertical_speed"] + random.uniform(-0.45, 0.25) * dt,
        -3.0,
        1.8,
    )
    mover["y"] = clamp(
        mover["base_y"] + math.sin(mover["bob_phase"]) * mover["bob_amp"],
        min_height,
        max_height,
    )


def main():
    pygame.init()
    pygame.display.set_mode((WINDOW_W, WINDOW_H), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption("Laborator SPG - Free Camera")
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.12, 0.14, 0.20, 1.0)

    def set_proj(w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov, w / h, 0.1, CUBE_S * 5)
        glMatrixMode(GL_MODELVIEW)

    fov = 70.0
    set_proj(WINDOW_W, WINDOW_H)
    setup_lighting()

    def tp(name):
        return os.path.join(TEXTURE_DIR, name)

    tex_grass = load_texture(tp("grass.jpg"), repeat=True)
    tex_sky = load_texture(tp("sky.png"), repeat=False)
    tex_front = load_texture(tp("wall.png"), repeat=False)
    tex_back = load_texture(tp("wall.png"), repeat=False)
    tex_left = load_texture(tp("wall.png"), repeat=False)
    tex_right = load_texture(tp("wall.png"), repeat=False)
    tex_road = load_texture(tp(ROAD_TEX_NAME), repeat=True)

    tree_billboard_textures = []
    for i in range(1, 5):
        path = tp(f"tree{i}.png")
        if os.path.exists(path):
            tree_billboard_textures.append(load_billboard_texture(path))

    kenney_scene = None
    kenney_dir = os.path.join(os.path.dirname(__file__), "kenney", "Models", "OBJ format")
    kenney_tex = os.path.join(kenney_dir, "Textures", "colormap.png")
    if os.path.exists(kenney_dir) and os.path.exists(kenney_tex):
        tex_colormap = load_colormap(kenney_tex)
        kenney_scene = KenneyScene(kenney_dir, tex_colormap)

    glb_bench = None
    glb_bench_path = os.path.join(os.path.dirname(__file__), "kenney", "Models", "bench.glb")
    if os.path.exists(glb_bench_path):
        glb_bench = load_glb_model(glb_bench_path)

    glb_car = None
    glb_car_path = os.path.join(os.path.dirname(__file__), "kenney", "Models", "ergoninane-fast-74.glb")
    if os.path.exists(glb_car_path):
        glb_car = load_glb_model(glb_car_path)

    glb_balloon = None
    glb_balloon_path = os.path.join(os.path.dirname(__file__), "kenney", "Models", "balloon.glb")
    if os.path.exists(glb_balloon_path):
        glb_balloon = load_glb_model(glb_balloon_path)

    glb_airplane = None
    glb_airplane_path = os.path.join(os.path.dirname(__file__), "kenney", "Models", "airplane.glb")
    if os.path.exists(glb_airplane_path):
        glb_airplane = load_glb_model(glb_airplane_path)

    hmap = generate_heightmap_fbm(TERRAIN_GRID, 10.0, seed=42)
    vao, ibo, cnt, _ = build_terrain(TERRAIN_GRID, TERRAIN_SCALE, hmap)
    track_outer_x = 30.0
    track_outer_z = 18.0
    track_cx, track_cz, _ = find_track_center(hmap, TERRAIN_SCALE, track_outer_x, track_outer_z)
    track_road_w = ROAD_WIDTH
    track_straight_half = max(0.0, track_outer_x - track_outer_z)

    circuit_y = -CUBE_S + compute_circuit_y(hmap, TERRAIN_GRID, TERRAIN_SCALE)
    road_vao, road_ibo, road_cnt = build_circuit(circuit_y)
    scene_layout = get_scene_layout(circuit_y)
    lamp_lights = get_lamp_lights(circuit_y)
    max_lamp_shadows = 4
    fill_direction = (-0.35, 0.95, -0.2)

    ground_preset = {
        "x": track_cx + track_straight_half,
        "y": -CUBE_S + sample_height(
            hmap,
            TERRAIN_SCALE,
            track_cx + track_straight_half,
            track_cz - (track_outer_z - track_road_w * 0.5),
        ) + 1.85,
        "z": track_cz - (track_outer_z - track_road_w * 0.5),
        "yaw": 180.0,
        "pitch": -2.5,
        "roll": 0.0,
    }
    top_preset = {
        "x": track_cx,
        "y": -CUBE_S + CUBE_S * 1.35,
        "z": track_cz,
        "yaw": 0.0,
        "pitch": -55.0,
        "roll": 0.0,
    }
    camera = dict(ground_preset)
    camera_mode = "follow" if glb_car else "free"

    car_spawn = {
        "x": track_cx + track_straight_half - 2.0,
        "y": circuit_y,
        "z": track_cz - (track_outer_z - track_road_w * 0.5),
        "yaw": 0.0,
    }
    car_scale = 1.3 / max(glb_car.get("height", 1.0), 0.1) if glb_car else 1.0
    car = {
        **car_spawn,
        "speed": 0.0,
        "scale": car_scale,
        "steer": 0.0,
    }

    car_bbox_min = (
        glb_car["x_min"] - glb_car.get("x_center", 0.0),
        glb_car["y_min"],
        glb_car["z_min"] - glb_car.get("z_center", 0.0),
    ) if glb_car else (-0.5, 0.0, -0.5)
    car_bbox_max = (
        glb_car["x_max"] - glb_car.get("x_center", 0.0),
        glb_car["y_min"] + glb_car["height"],
        glb_car["z_max"] - glb_car.get("z_center", 0.0),
    ) if glb_car else (0.5, 1.0, 0.5)
    car_length = (car_bbox_max[2] - car_bbox_min[2]) * car_scale
    car_height_world = (car_bbox_max[1] - car_bbox_min[1]) * car_scale
    follow_camera = build_chase_camera(
        car,
        car["yaw"],
        car_length=car_length,
        car_height=car_height_world,
    ) if glb_car else None
    follow_manual = {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "yaw": 0.0,
        "pitch": 0.0,
        "roll": 0.0,
    }
    balloon = None
    if glb_balloon:
        balloon_scale = 5.2 / max(glb_balloon.get("height", 1.0), 0.1)
        balloon = {
            "x": -12.0,
            "y": 7.2,
            "z": 8.0,
            "base_y": 7.2,
            "yaw": 35.0,
            "speed": 6.0,
            "vertical_speed": -0.55,
            "bob_phase": 0.0,
            "bob_speed": 2.4,
            "bob_amp": 1.1,
            "turn_timer": 0.55,
            "scale": balloon_scale,
        }

    airplane = None
    if glb_airplane:
        airplane_scale = 4.2 / max(glb_airplane.get("height", 1.0), 0.1)
        airplane = {
            "angle": 0.0,
            "radius_x": 22.0,
            "radius_z": 15.0,
            "center_x": 0.0,
            "center_z": 0.0,
            "y": 8.4,
            "angular_speed": 22.0,
            "scale": airplane_scale,
        }

    building_colliders = []
    if kenney_scene:
        for instance in kenney_scene.get_building_instances(circuit_y):
            building_colliders.append(build_footprint_collider(
                instance["x"],
                instance["z"],
                instance["rot_y"],
                instance["scale"],
                instance["bbox_min"],
                instance["bbox_max"],
                shrink_x=0.92,
                shrink_z=0.92,
            ))

    object_draw_args = {
        "wall": None,
        "roof": None,
        "bark": None,
        "leaves": None,
        "tree_billboard": tree_billboard_textures,
        "glb_bench": glb_bench,
        "draw_glb_model": draw_glb_model,
    }

    clock = pygame.time.Clock()
    dragging = False
    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            elif ev.type == KEYDOWN:
                if ev.key == K_ESCAPE:
                    running = False
                elif ev.key == K_1:
                    camera_mode = "top"
                elif ev.key == K_2:
                    camera.update(ground_preset)
                    camera_mode = "free"
                elif ev.key == K_3 and glb_car:
                    camera_mode = "follow"
                    follow_camera = build_chase_camera(
                        car,
                        car["yaw"],
                        car_length=car_length,
                        car_height=car_height_world,
                    )
                    follow_manual = {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0,
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0,
                    }
                elif ev.key == K_r:
                    camera.update(ground_preset)
                    fov = 70.0
                    if glb_car:
                        car.update(car_spawn)
                        car["speed"] = 0.0
                        car["steer"] = 0.0
                        camera_mode = "follow"
                        follow_camera = build_chase_camera(
                            car,
                            car["yaw"],
                            car_length=car_length,
                            car_height=car_height_world,
                        )
                        follow_manual = {
                            "x": 0.0,
                            "y": 0.0,
                            "z": 0.0,
                            "yaw": 0.0,
                            "pitch": 0.0,
                            "roll": 0.0,
                        }
                    set_proj(*pygame.display.get_surface().get_size())
            elif ev.type == MOUSEBUTTONDOWN:
                if ev.button == 1:
                    dragging = True
            elif ev.type == MOUSEBUTTONUP:
                if ev.button == 1:
                    dragging = False
            elif ev.type == MOUSEMOTION and dragging:
                if camera_mode == "free":
                    camera["yaw"] = (camera["yaw"] + ev.rel[0] * SENSITIVITY) % 360.0
                    camera["pitch"] = clamp(camera["pitch"] + ev.rel[1] * SENSITIVITY, -89.0, 89.0)
                elif camera_mode == "follow" and glb_car:
                    follow_manual["yaw"] = (follow_manual["yaw"] + ev.rel[0] * SENSITIVITY) % 360.0
                    follow_manual["pitch"] = clamp(
                        follow_manual["pitch"] + ev.rel[1] * SENSITIVITY,
                        -50.0,
                        50.0,
                    )
            elif ev.type == MOUSEWHEEL:
                fov = clamp(fov - ev.y * 2.0, 20.0, 120.0)
                set_proj(*pygame.display.get_surface().get_size())
            elif ev.type == VIDEORESIZE:
                glViewport(0, 0, ev.w, ev.h)
                set_proj(ev.w, ev.h)

        keys = pygame.key.get_pressed()
        if glb_car:
            accel = 0.0
            if keys[K_UP]:
                accel += 9.0
            if keys[K_DOWN]:
                accel -= 7.0

            if accel == 0.0:
                drag = 8.0 * dt
                if abs(car["speed"]) <= drag:
                    car["speed"] = 0.0
                else:
                    car["speed"] -= math.copysign(drag, car["speed"])
            else:
                car["speed"] += accel * dt

            car["speed"] = clamp(car["speed"], -4.0, 10.0)

            steer_input = 0
            if keys[K_LEFT]:
                steer_input += 1
            if keys[K_RIGHT]:
                steer_input -= 1

            max_steer = 36.0
            steer_speed = 150.0
            steer_return = 180.0
            steer_target = steer_input * max_steer
            steer_delta = steer_target - car["steer"]
            if steer_input:
                max_step = steer_speed * dt
            else:
                max_step = steer_return * dt
            if abs(steer_delta) <= max_step:
                car["steer"] = steer_target
            else:
                car["steer"] += math.copysign(max_step, steer_delta)

            candidate_yaw = car["yaw"]
            if abs(car["speed"]) > 0.35 and abs(car["steer"]) > 0.05:
                wheelbase = 2.2
                yaw_delta = math.degrees(
                    (car["speed"] / wheelbase) * math.tan(math.radians(car["steer"])) * dt
                )
                candidate_yaw = (car["yaw"] + yaw_delta) % 360.0
            elif steer_input:
                candidate_yaw = (car["yaw"] + steer_input * 38.0 * dt) % 360.0

            forward_x, forward_z = rotate_xz(0.0, 1.0, candidate_yaw)
            next_x = car["x"] + forward_x * car["speed"] * dt
            next_z = car["z"] + forward_z * car["speed"] * dt
            next_collider = build_footprint_collider(
                next_x,
                next_z,
                candidate_yaw,
                car["scale"],
                car_bbox_min,
                car_bbox_max,
                shrink_x=0.72,
                shrink_z=0.82,
            )

            if collides_with_any(next_collider, building_colliders):
                car["speed"] = 0.0
            else:
                car["x"] = next_x
                car["z"] = next_z
                car["yaw"] = candidate_yaw

        if balloon:
            update_bounded_random_mover(
                balloon,
                dt,
                half_extent=CUBE_S,
                margin=3.5,
                min_height=4.4,
                max_height=10.5,
            )

        if airplane:
            airplane["angle"] = (airplane["angle"] + airplane["angular_speed"] * dt) % 360.0
            plane_rad = math.radians(airplane["angle"])
            airplane["x"] = airplane["center_x"] + math.cos(plane_rad) * airplane["radius_x"]
            airplane["z"] = airplane["center_z"] + math.sin(plane_rad) * airplane["radius_z"]
            tangent_x = -math.sin(plane_rad) * airplane["radius_x"]
            tangent_z = math.cos(plane_rad) * airplane["radius_z"]
            airplane["yaw"] = math.degrees(math.atan2(tangent_x, tangent_z)) % 360.0

        if camera_mode == "free":
            apply_camera_controls(camera, camera, keys, dt)

        if camera_mode == "top":
            render_camera = dict(top_preset)
        elif camera_mode == "follow" and glb_car:
            target_follow_camera = build_chase_camera(
                car,
                car["yaw"],
                car_length=car_length,
                car_height=car_height_world,
            )
            pos_blend = clamp(1.8 * dt, 0.0, 1.0)
            rot_blend = clamp(1.0 * dt, 0.0, 1.0)
            follow_camera["x"] = lerp(follow_camera["x"], target_follow_camera["x"], pos_blend)
            follow_camera["y"] = lerp(follow_camera["y"], target_follow_camera["y"], pos_blend)
            follow_camera["z"] = lerp(follow_camera["z"], target_follow_camera["z"], pos_blend)
            follow_camera["yaw"] = lerp_angle_deg(follow_camera["yaw"], target_follow_camera["yaw"], rot_blend)
            follow_camera["pitch"] = lerp(follow_camera["pitch"], target_follow_camera["pitch"], rot_blend)
            follow_camera["roll"] = 0.0
            apply_camera_controls(follow_manual, follow_camera, keys, dt)
            render_camera = {
                "x": follow_camera["x"] + follow_manual["x"],
                "y": follow_camera["y"] + follow_manual["y"],
                "z": follow_camera["z"] + follow_manual["z"],
                "yaw": (follow_camera["yaw"] + follow_manual["yaw"]) % 360.0,
                "pitch": clamp(follow_camera["pitch"] + follow_manual["pitch"], -89.0, 89.0),
                "roll": clamp(follow_camera["roll"] + follow_manual["roll"], -60.0, 60.0),
            }
        else:
            render_camera = dict(camera)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glRotatef(-render_camera["roll"], 0, 0, 1)
        glRotatef(-render_camera["pitch"], 1, 0, 0)
        glRotatef(-render_camera["yaw"], 0, 1, 0)
        glTranslatef(-render_camera["x"], -render_camera["y"], -render_camera["z"])

        draw_skybox(tex_sky, tex_front, tex_back, tex_left, tex_right, tint=(0.30, 0.34, 0.50))
        draw_moon(fill_direction)
        active_lamps = select_active_lamps(
            lamp_lights,
            camera_pos=(render_camera["x"], render_camera["y"], render_camera["z"]),
            max_lamp_lights=6,
        )
        configure_lighting(
            fill_direction,
            active_lamps,
            camera_pos=(render_camera["x"], render_camera["y"], render_camera["z"]),
            max_lamp_lights=6,
        )

        glPushMatrix()
        glTranslatef(0.0, -CUBE_S, 0.0)
        draw_terrain(vao, ibo, cnt, tex_grass, tint=(0.44, 0.47, 0.42))
        glPopMatrix()
        draw_circuit(road_vao, road_ibo, road_cnt, tex_road)
        draw_ground(tex_grass, tint=(0.46, 0.48, 0.50))

        shadow_y = circuit_y + 0.03
        draw_projected_shadow(
            (fill_direction[0], fill_direction[1], fill_direction[2], 0.0),
            shadow_y,
            lambda: (
                kenney_scene.draw_all(circuit_y, shadow_pass=True) if kenney_scene else None,
                draw_all_objects(circuit_y, {
                    **object_draw_args,
                    "_only_lamps_benches": True,
                } if kenney_scene else object_draw_args, shadow_pass=True),
                draw_glb_model(
                    glb_car,
                    car["x"],
                    car["y"],
                    car["z"],
                    scale=car["scale"],
                    rot_y=car["yaw"],
                    shadow_pass=True,
                    center_xz=True,
                ) if glb_car else None,
                draw_glb_model(
                    glb_balloon,
                    balloon["x"],
                    balloon["y"],
                    balloon["z"],
                    scale=balloon["scale"],
                    rot_y=balloon["yaw"],
                    shadow_pass=True,
                    center_xz=True,
                ) if balloon else None,
                draw_glb_model(
                    glb_airplane,
                    airplane["x"],
                    airplane["y"],
                    airplane["z"],
                    scale=airplane["scale"],
                    rot_y=airplane["yaw"],
                    shadow_pass=True,
                    center_xz=True,
                ) if airplane else None
            ),
            alpha=0.008,
        )
        if kenney_scene:
            kenney_scene.draw_all(circuit_y)
            draw_all_objects(circuit_y, {
                **object_draw_args,
                "_only_lamps_benches": True,
            })
        else:
            draw_all_objects(circuit_y, object_draw_args)

        if glb_car:
            draw_glb_model(
                glb_car,
                car["x"],
                car["y"],
                car["z"],
                scale=car["scale"],
                rot_y=car["yaw"],
                center_xz=True,
            )
        if balloon:
            draw_glb_model(
                glb_balloon,
                balloon["x"],
                balloon["y"],
                balloon["z"],
                scale=balloon["scale"],
                rot_y=balloon["yaw"],
                center_xz=True,
                force_unlit=True,
            )
        if airplane:
            draw_glb_model(
                glb_airplane,
                airplane["x"],
                airplane["y"],
                airplane["z"],
                scale=airplane["scale"],
                rot_y=airplane["yaw"],
                center_xz=True,
                force_unlit=True,
            )

        lamp_bench_pairs = list(zip(scene_layout["lamps"], scene_layout["benches"]))
        lamp_bench_pairs.sort(
            key=lambda pair: (
                (pair[0]["light_x"] - render_camera["x"]) ** 2 +
                (pair[0]["light_y"] - render_camera["y"]) ** 2 +
                (pair[0]["light_z"] - render_camera["z"]) ** 2
            )
        )
        for lamp, bench in lamp_bench_pairs[:max_lamp_shadows]:
            draw_bench_lamp_shadow(
                lamp["light_x"],
                lamp["light_z"],
                bench["x"],
                shadow_y,
                bench["z"],
                angle_y=bench["angle_y"],
                alpha=0.20,
            )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
