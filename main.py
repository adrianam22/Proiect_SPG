import sys, os, math, ctypes
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL  import *
from OpenGL.GLU import *

WINDOW_W, WINDOW_H = 1280, 720
CUBE_S   = 50.0
TERRAIN_GRID  = 80
TERRAIN_SIZE  = CUBE_S * 1.8
SENSITIVITY   = 0.18
TEXTURE_DIR   = os.path.join(os.path.dirname(__file__), "textures")

def load_texture(path, repeat=True):
    from PIL import Image as PILImage

    def next_pow2(n):
        p = 1
        while p < n:
            p <<= 1
        return p

    img = PILImage.open(path).convert("RGB")
    MAX_SIZE = 2048
    new_w = min(MAX_SIZE, next_pow2(img.width))
    new_h = min(MAX_SIZE, next_pow2(img.height))
    if (new_w, new_h) != (img.width, img.height):
        img = img.resize((new_w, new_h), PILImage.LANCZOS)

    img  = img.transpose(PILImage.FLIP_TOP_BOTTOM)
    data = np.array(img, dtype=np.uint8)

    tid  = int(glGenTextures(1))
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, data)
    glGenerateMipmap(GL_TEXTURE_2D)
    wrap = GL_REPEAT if repeat else GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return tid

#teren cu munti folosind functii gaussiene
#cu cat un punct e mai departe de varf, cu atat inaltimea scade exponential
def generate_heightmap_fbm(grid, max_height=14.0, seed=42):
    size = grid + 1
    h = np.zeros((size, size), dtype=np.float32)
    def gaussian_peak(cx, cy, height, radius):
        for y in range(size):
            for x in range(size):
                dx = (x - cx) / radius
                dy = (y - cy) / radius
                d = dx*dx + dy*dy
                h[y, x] += height * math.exp(-d * 2.5)
    gaussian_peak(
        cx=int(size*0.75),
        cy=int(size*0.55),
        height=1.0,
        radius=size*0.35
    )
    gaussian_peak(
        cx=int(size*0.25),
        cy=int(size*0.50),
        height=0.45,
        radius=size*0.28
    )
    rng = np.random.default_rng(seed)
    noise = rng.random((size, size)).astype(np.float32) - 0.5
    h += noise * 0.03

    h = np.clip(h, 0, 1)

    return (h * max_height).astype(np.float32)

def build_terrain(grid, size, hmap):
    step=size/grid; half=size/2.
    verts=[]
    for i in range(grid+1):
        for j in range(grid+1):
            x=-half+i*step; z=-half+j*step; y=float(hmap[i,j])
            hpx=hmap[min(i+1,grid),j]; hmx=hmap[max(i-1,0),j]
            hpz=hmap[i,min(j+1,grid)]; hmz=hmap[i,max(j-1,0)]
            nx_=(hmx-hpx)/(2*step); nz_=(hmz-hpz)/(2*step); ny_=1.
            ln=math.sqrt(nx_*nx_+ny_*ny_+nz_*nz_)
            verts.extend([x,y,z,nx_/ln,ny_/ln,nz_/ln,i/grid*1.,j/grid*1.])
    indices=[]
    for i in range(grid):
        for j in range(grid):
            a=i*(grid+1)+j; b=a+1; c=a+(grid+1); d=c+1
            indices.extend([a,c,b,b,c,d])
    v_arr=np.array(verts,dtype=np.float32)
    i_arr=np.array(indices,dtype=np.uint32)
    vao=glGenVertexArrays(1); glBindVertexArray(vao)
    vbo=glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER,vbo)
    glBufferData(GL_ARRAY_BUFFER,v_arr.nbytes,v_arr,GL_STATIC_DRAW)
    ibo=glGenBuffers(1); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER,i_arr.nbytes,i_arr,GL_STATIC_DRAW)
    stride=8*4
    glVertexPointer(3,GL_FLOAT,stride,ctypes.c_void_p(0))
    glNormalPointer(GL_FLOAT,stride,ctypes.c_void_p(12))
    glTexCoordPointer(2,GL_FLOAT,stride,ctypes.c_void_p(24))
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glBindVertexArray(0)
    return int(vao),int(ibo),len(indices),float(np.max(np.abs(hmap)))

def draw_skybox(tex_top, tex_front, tex_back, tex_left, tex_right, s=CUBE_S):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glColor3f(1,1,1)

    def face(tex, verts_uv):
        glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_QUADS)
        for (u,v),(x,y,z) in verts_uv:
            glTexCoord2f(u,v); glVertex3f(x,y,z)
        glEnd()

    face(tex_top,[
        ((0,0),(-s, s,-s)), ((1,0),( s, s,-s)),
        ((1,1),( s, s, s)), ((0,1),(-s, s, s))])

    face(tex_front,[
        ((0,0),(-s,-s,-s)), ((1,0),( s,-s,-s)),
        ((1,1),( s, s,-s)), ((0,1),(-s, s,-s))])

    face(tex_back,[
        ((0,0),( s,-s, s)), ((1,0),(-s,-s, s)),
        ((1,1),(-s, s, s)), ((0,1),( s, s, s))])

    face(tex_left,[
        ((0,0),(-s,-s, s)), ((1,0),(-s,-s,-s)),
        ((1,1),(-s, s,-s)), ((0,1),(-s, s, s))])

    face(tex_right,[
        ((0,0),( s,-s,-s)), ((1,0),( s,-s, s)),
        ((1,1),( s, s, s)), ((0,1),( s, s,-s))])

    glEnable(GL_DEPTH_TEST)

def draw_ground(tex, s=CUBE_S, rep=1.):
    glEnable(GL_TEXTURE_2D); glEnable(GL_LIGHTING)
    glBindTexture(GL_TEXTURE_2D, tex)
    glColor3f(1,1,1)
    y=-CUBE_S+0.02
    glBegin(GL_QUADS)
    glNormal3f(0,1,0)
    glTexCoord2f(0,0);     glVertex3f(-s,y,-s)
    glTexCoord2f(rep,0);   glVertex3f( s,y,-s)
    glTexCoord2f(rep,rep); glVertex3f( s,y, s)
    glTexCoord2f(0,rep);   glVertex3f(-s,y, s)
    glEnd()

def draw_terrain(vao, ibo, cnt, tex_grass):
    glEnable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glBindVertexArray(vao)
    glBindTexture(GL_TEXTURE_2D, tex_grass)
    glColor3f(1, 1, 1)
    glDrawElements(GL_TRIANGLES, cnt, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)
    glEnable(GL_LIGHTING)

def draw_interior_markers(s=CUBE_S):
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_LIGHTING)
    glLineWidth(1.2)

    glColor3f(1.0, 1.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0, 1.0, 1.0, 0.18)

    edges = [

        ((-s,-s,-s),( s,-s,-s)), (( s,-s,-s),( s,-s, s)),
        (( s,-s, s),(-s,-s, s)), ((-s,-s, s),(-s,-s,-s)),

        ((-s, s,-s),( s, s,-s)), (( s, s,-s),( s, s, s)),
        (( s, s, s),(-s, s, s)), ((-s, s, s),(-s, s,-s)),

        ((-s,-s,-s),(-s, s,-s)), (( s,-s,-s),( s, s,-s)),
        (( s,-s, s),( s, s, s)), ((-s,-s, s),(-s, s, s)),
    ]
    glBegin(GL_LINES)
    for (a,b) in edges:
        glVertex3fv(a); glVertex3fv(b)
    glEnd()

    glLineWidth(2.5)
    axis_len = s * 0.35

    glBegin(GL_LINES)
    glColor4f(1.0, 0.25, 0.25, 0.85)
    glVertex3f(-axis_len, 0, 0); glVertex3f(axis_len, 0, 0)
    glColor4f(0.25, 1.0, 0.35, 0.85)
    glVertex3f(0, -axis_len, 0); glVertex3f(0, axis_len, 0)
    glColor4f(0.25, 0.55, 1.0, 0.85)
    glVertex3f(0, 0, -axis_len); glVertex3f(0, 0, axis_len)
    glEnd()

    glPointSize(8.0)
    glBegin(GL_POINTS)
    glColor4f(1.0, 1.0, 0.0, 0.9)   # galben
    glVertex3f(0, 0, 0)
    glEnd()

    glDisable(GL_BLEND)
    glLineWidth(1.0)
    glPointSize(1.0)
    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)

def setup_lighting():
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0,GL_POSITION, [0.6, 1.0, 0.4, 0.0])
    glLightfv(GL_LIGHT0,GL_AMBIENT,  [0.35,0.35,0.35,1.0])
    glLightfv(GL_LIGHT0,GL_DIFFUSE,  [0.9, 0.85,0.70,1.0])
    glLightfv(GL_LIGHT0,GL_SPECULAR, [0.15,0.15,0.15,1.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK,GL_AMBIENT_AND_DIFFUSE)

def main():
    pygame.init()
    pygame.display.set_mode((WINDOW_W,WINDOW_H), DOUBLEBUF|OPENGL|RESIZABLE)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.05,0.05,0.08,1.0)

    def set_proj(w,h):
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(fov, w/h, 0.1, CUBE_S*5)
        glMatrixMode(GL_MODELVIEW)

    fov = 70.0
    set_proj(WINDOW_W, WINDOW_H)
    setup_lighting()

    def tp(n): return os.path.join(TEXTURE_DIR, n)
    tex_grass  = load_texture(tp("grass.jpg"),          repeat=True)
    tex_sky    = load_texture(tp("sky_top.jpg"),         repeat=False)
    tex_front  = load_texture(tp("mountain_front.jpg"),  repeat=False)
    tex_back   = load_texture(tp("mountain_back.jpg"),   repeat=False)
    tex_left   = load_texture(tp("mountain_left.jpg"),   repeat=False)
    tex_right  = load_texture(tp("mountain_right.jpg"),  repeat=False)

    TERRAIN_SCALE  = CUBE_S * 2.0
    TERRAIN_GRID   = 80
    MAX_HEIGHT     = 22.0
    hmap = generate_heightmap_fbm(TERRAIN_GRID, MAX_HEIGHT, seed=42)
    vao, ibo, cnt, _ = build_terrain(TERRAIN_GRID, TERRAIN_SCALE, hmap)

    yaw   = 0.0
    pitch = -12.0
    dragging = False

    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(60)

        for ev in pygame.event.get():
            if ev.type == QUIT: running = False
            elif ev.type == KEYDOWN:
                if ev.key in (K_ESCAPE, K_q): running = False
                elif ev.key == K_r: yaw, pitch = 0.0, -12.0; fov = 70.0
            elif ev.type == MOUSEBUTTONDOWN:
                if ev.button == 1: dragging = True
            elif ev.type == MOUSEBUTTONUP:
                if ev.button == 1: dragging = False
            elif ev.type == MOUSEMOTION:
                if dragging:
                    yaw   = (yaw   + ev.rel[0] * SENSITIVITY) % 360
                    pitch = max(-89, min(89, pitch + ev.rel[1] * SENSITIVITY))
            elif ev.type == MOUSEWHEEL:
                fov = max(20., min(120., fov - ev.y * 2.0))
                set_proj(*pygame.display.get_surface().get_size())
            elif ev.type == VIDEORESIZE:
                glViewport(0,0,ev.w,ev.h)
                set_proj(ev.w,ev.h)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glRotatef(-pitch, 1, 0, 0)
        glRotatef(-yaw,   0, 1, 0)

        draw_skybox(tex_sky, tex_front, tex_back, tex_left, tex_right)

        glPushMatrix()
        glTranslatef(0.0, -CUBE_S, 0.0)
        draw_terrain(vao, ibo, cnt, tex_grass)
        glPopMatrix()
        draw_ground(tex_grass)
        draw_interior_markers()
        fps = clock.get_fps()
        pygame.display.flip()

    pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()