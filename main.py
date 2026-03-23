import os
import sys
import math

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config import WINDOW_W, WINDOW_H, CUBE_S, TERRAIN_GRID, TERRAIN_SCALE, SENSITIVITY, TEXTURE_DIR
from textures import load_texture
from terrain import generate_heightmap_fbm, build_terrain, draw_terrain
from render import draw_skybox, draw_ground, draw_interior_markers, setup_lighting
from track import find_track_center, sample_height
from circuit import build_circuit, draw_circuit, compute_circuit_y, ROAD_TEX_NAME, ROAD_WIDTH
from object import draw_all_objects, load_billboard_texture
from loader_objects import load_colormap, KenneyScene, load_glb_model, draw_glb_model


def main():
    pygame.init()
    pygame.display.set_mode((WINDOW_W, WINDOW_H), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.05, 0.05, 0.08, 1.0)

    def set_proj(w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov, w / h, 0.1, CUBE_S * 5)
        glMatrixMode(GL_MODELVIEW)

    fov = 70.0
    set_proj(WINDOW_W, WINDOW_H)
    setup_lighting()

    def tp(n):
        return os.path.join(TEXTURE_DIR, n)

    tex_grass = load_texture(tp("grass.jpg"), repeat=True)
    tex_sky = load_texture(tp("sky.png"), repeat=False)
    tex_front = load_texture(tp("wall.png"), repeat=False)
    tex_back = load_texture(tp("wall.png"), repeat=False)
    tex_left = load_texture(tp("wall.png"), repeat=False)
    tex_right = load_texture(tp("wall.png"), repeat=False)
    tex_road = load_texture(tp(ROAD_TEX_NAME), repeat=True)

    def load_safe(name, fallback):
        path = tp(name)
        return load_texture(path, repeat=True) if os.path.exists(path) else fallback

    tree_billboard_textures = []
    for i in range(1, 5):
        path = tp(f"tree{i}.png")
        if os.path.exists(path):
            tree_billboard_textures.append(load_billboard_texture(path))

    obj_textures = {}

    kenney_scene = None
    kenney_dir = os.path.join(os.path.dirname(__file__), "kenney", "Models", "OBJ format")
    kenney_tex = os.path.join(kenney_dir, "Textures", "colormap.png")
    if os.path.exists(kenney_dir) and os.path.exists(kenney_tex):
        tex_colormap = load_colormap(kenney_tex)
        kenney_scene = KenneyScene(kenney_dir, tex_colormap)

    glb_lamp = None
    glb_bench = None
    glb_lamp_path = os.path.join(os.path.dirname(__file__), "kenney", "Models", "streetlamp.glb")
    glb_bench_path = os.path.join(os.path.dirname(__file__), "kenney", "Models", "bench.glb")
    if os.path.exists(glb_lamp_path):
        glb_lamp = load_glb_model(glb_lamp_path)
    if os.path.exists(glb_bench_path):
        glb_bench = load_glb_model(glb_bench_path)

    hmap = generate_heightmap_fbm(TERRAIN_GRID, 10.0, seed=42)
    vao, ibo, cnt, _ = build_terrain(TERRAIN_GRID, TERRAIN_SCALE, hmap)
    track_outer_x = 30.0
    track_outer_z = 18.0
    track_cx, track_cz, _ = find_track_center(hmap, TERRAIN_SCALE, track_outer_x, track_outer_z)
    track_road_w = ROAD_WIDTH
    track_straight_half = max(0.0, track_outer_x - track_outer_z)

    circuit_y = -CUBE_S + compute_circuit_y(hmap, TERRAIN_GRID, TERRAIN_SCALE)
    road_vao, road_ibo, road_cnt = build_circuit(circuit_y)

    view_mode = "ground"
    ground_cam = {
        "x": track_cx + track_straight_half,
        "z": track_cz - (track_outer_z - track_road_w * 0.5),
        "yaw": 180.0,
        "pitch": -2.5,
    }
    top_cam = {
        "x": track_cx,
        "z": track_cz,
        "yaw": 0.0,
        "pitch": -55.0,
    }
    cam_x = ground_cam["x"]
    cam_z = ground_cam["z"]
    cam_y = -CUBE_S + 1.85
    yaw = ground_cam["yaw"]
    pitch = ground_cam["pitch"]
    dragging = False

    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            elif ev.type == KEYDOWN:
                if ev.key in (K_ESCAPE, K_q):
                    running = False
                elif ev.key == K_SPACE:
                    view_mode = "top" if view_mode == "ground" else "ground"
                    if view_mode == "top":
                        cam_x = top_cam["x"]
                        cam_z = top_cam["z"]
                        yaw = top_cam["yaw"]
                        pitch = top_cam["pitch"]
                    else:
                        cam_x = ground_cam["x"]
                        cam_z = ground_cam["z"]
                        yaw = ground_cam["yaw"]
                        pitch = ground_cam["pitch"]
                elif ev.key == K_r:
                    view_mode = "ground"
                    cam_x = ground_cam["x"]
                    cam_z = ground_cam["z"]
                    yaw, pitch = ground_cam["yaw"], ground_cam["pitch"]
                    fov = 70.0
            elif ev.type == MOUSEBUTTONDOWN:
                if ev.button == 1:
                    dragging = True
            elif ev.type == MOUSEBUTTONUP:
                if ev.button == 1:
                    dragging = False
            elif ev.type == MOUSEMOTION:
                if dragging:
                    yaw = (yaw + ev.rel[0] * SENSITIVITY) % 360
                    pitch = max(-89, min(89, pitch + ev.rel[1] * SENSITIVITY))
            elif ev.type == MOUSEWHEEL:
                fov = max(20.0, min(120.0, fov - ev.y * 2.0))
                set_proj(*pygame.display.get_surface().get_size())
            elif ev.type == VIDEORESIZE:
                glViewport(0, 0, ev.w, ev.h)
                set_proj(ev.w, ev.h)

        keys = pygame.key.get_pressed()
        move = 12.0 * dt
        rad = math.radians(yaw)
        fwd_x = math.sin(rad)
        fwd_z = -math.cos(rad)
        right_x = math.cos(rad)
        right_z = math.sin(rad)
        if view_mode == "ground":
            if keys[K_w]:
                cam_x += fwd_x * move
                cam_z += fwd_z * move
            if keys[K_s]:
                cam_x -= fwd_x * move
                cam_z -= fwd_z * move
            if keys[K_a]:
                cam_x -= right_x * move
                cam_z -= right_z * move
            if keys[K_d]:
                cam_x += right_x * move
                cam_z += right_z * move
            cam_y = -CUBE_S + sample_height(hmap, TERRAIN_SCALE, cam_x, cam_z) + 1.85
            ground_cam["x"] = cam_x
            ground_cam["z"] = cam_z
            ground_cam["yaw"] = yaw
            ground_cam["pitch"] = pitch
        else:
            cam_y = -CUBE_S + CUBE_S * 1.35

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glRotatef(-pitch, 1, 0, 0)
        glRotatef(-yaw, 0, 1, 0)
        glTranslatef(-cam_x, -cam_y, -cam_z)

        draw_skybox(tex_sky, tex_front, tex_back, tex_left, tex_right)

        glPushMatrix()
        glTranslatef(0.0, -CUBE_S, 0.0)
        draw_terrain(vao, ibo, cnt, tex_grass)
        glPopMatrix()
        draw_circuit(road_vao, road_ibo, road_cnt, tex_road)
        draw_ground(tex_grass)
        draw_interior_markers()

        if kenney_scene:
            kenney_scene.draw_all(circuit_y)
            draw_all_objects(circuit_y, {
                'wall': None, 'roof': None,
                'bark': None, 'leaves': None,
                'tree_billboard': None,
                '_only_lamps_benches': True,
                'glb_lamp': glb_lamp,
                'glb_bench': glb_bench,
                'draw_glb_model': draw_glb_model,
            })
        else:
            obj_textures['glb_lamp'] = glb_lamp
            obj_textures['glb_bench'] = glb_bench
            obj_textures['draw_glb_model'] = draw_glb_model
            draw_all_objects(circuit_y, obj_textures)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
