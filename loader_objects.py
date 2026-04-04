import os
import math
import struct
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

def load_colormap(path: str) -> int:
    from PIL import Image as PILImage

    def next_pow2(n):
        p = 1
        while p < n:
            p <<= 1
        return p

    img = PILImage.open(path).convert("RGBA")
    new_w = min(2048, next_pow2(img.width))
    new_h = min(2048, next_pow2(img.height))
    if (new_w, new_h) != (img.width, img.height):
        img = img.resize((new_w, new_h), PILImage.LANCZOS)
    img = img.transpose(PILImage.FLIP_TOP_BOTTOM)
    data = img.tobytes()

    tid = int(glGenTextures(1))
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, data)
    glGenerateMipmap(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return tid

def _parse_obj(path: str):
    positions = []
    uvs = []
    normals = []
    faces = []

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            tok = parts[0]

            if tok == 'v' and len(parts) >= 4:
                positions.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif tok == 'vt' and len(parts) >= 3:
                uvs.append((float(parts[1]), float(parts[2])))
            elif tok == 'vn' and len(parts) >= 4:
                normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif tok == 'f' and len(parts) >= 4:
                verts_in_face = []
                for token in parts[1:]:
                    idx = token.split('/')
                    vi = int(idx[0]) - 1
                    uvi = int(idx[1]) - 1 if len(idx) > 1 and idx[1] else 0
                    ni = int(idx[2]) - 1 if len(idx) > 2 and idx[2] else 0
                    verts_in_face.append((vi, uvi, ni))
                for i in range(1, len(verts_in_face) - 1):
                    faces.append([verts_in_face[0], verts_in_face[i], verts_in_face[i + 1]])

    if not faces:
        return None, 0

    if not uvs:
        uvs = [(0.0, 0.0)]
    if not normals:
        normals = [(0.0, 1.0, 0.0)]

    buf = []
    for tri in faces:
        for (vi, uvi, ni) in tri:
            px, py, pz = positions[vi]
            nx, ny, nz = normals[min(ni, len(normals) - 1)]
            u, v = uvs[min(uvi, len(uvs) - 1)]
            buf.extend([px, py, pz, nx, ny, nz, u, v])

    arr = np.array(buf, dtype=np.float32)
    n_verts = len(faces) * 3

    vao = int(glGenVertexArrays(1))
    glBindVertexArray(vao)

    vbo = int(glGenBuffers(1))
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, arr.nbytes, arr, GL_STATIC_DRAW)

    stride = 8 * 4
    glVertexPointer(3, GL_FLOAT, stride, ctypes.c_void_p(0))
    glNormalPointer(GL_FLOAT, stride, ctypes.c_void_p(12))
    glTexCoordPointer(2, GL_FLOAT, stride, ctypes.c_void_p(24))
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    glBindVertexArray(0)
    return vao, n_verts

class KenneyModel:
    def __init__(self, obj_path: str):
        self.name = os.path.splitext(os.path.basename(obj_path))[0]
        self.vao, self.n = _parse_obj(obj_path)
        self._bbox = self._compute_bbox(obj_path)

    def _compute_bbox(self, path):
        mn = [1e9, 1e9, 1e9]
        mx = [-1e9, -1e9, -1e9]
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('v '):
                    p = line.split()
                    for i, val in enumerate([float(p[1]), float(p[2]), float(p[3])]):
                        mn[i] = min(mn[i], val)
                        mx[i] = max(mx[i], val)
        return mn, mx

    @property
    def height(self):
        return self._bbox[1][1] - self._bbox[0][1]

    @property
    def width(self):
        return self._bbox[1][0] - self._bbox[0][0]

    def draw(self, x, y, z, scale=1.0, rot_y=0.0, tex_id=None):
        if self.vao is None:
            return

        glPushMatrix()
        glTranslatef(x, y - self._bbox[0][1] * scale, z)
        if rot_y:
            glRotatef(rot_y, 0, 1, 0)
        glScalef(scale, scale, scale)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        if tex_id:
            glBindTexture(GL_TEXTURE_2D, tex_id)
        glColor3f(1, 1, 1)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.n)
        glBindVertexArray(0)

        glPopMatrix()

class KenneyScene:
    BUILDINGS = [
        "building-type-a",
        "building-type-b",
        "building-type-c",
        "building-type-d",
        "building-type-e",
        "building-type-f",
    ]
    TREES = ["tree-large", "tree-small"]
    EXTRAS = ["planter", "fence"]

    def __init__(self, obj_folder: str, tex_colormap: int):
        self.folder = obj_folder
        self.tex = tex_colormap
        self.models = {}
        for name in self.BUILDINGS + self.TREES + self.EXTRAS:
            path = os.path.join(obj_folder, f"{name}.obj")
            if os.path.exists(path):
                self.models[name] = KenneyModel(path)

    def _circuit_positions(self, n, dist_from_center, phase=0.0):
        from circuit import (CIRCUIT_CX as CX, CIRCUIT_CZ as CZ,
                             CIRCUIT_W as CW, CIRCUIT_H as CH,
                             CORNER_R as CR, ROAD_WIDTH as RW,
                             CORNER_SEGS as CSEGS,
                             _build_centerline, _smooth_normals)

        pts = _build_centerline(CX, CZ, CW, CH, CR, CSEGS)
        nrms = _smooth_normals(pts)
        N = len(pts)

        arc = [0.0]
        for i in range(1, N):
            dx = pts[i][0] - pts[i - 1][0]
            dz = pts[i][1] - pts[i - 1][1]
            arc.append(arc[-1] + math.sqrt(dx * dx + dz * dz))
        dx = pts[0][0] - pts[-1][0]
        dz = pts[0][1] - pts[-1][1]
        total = arc[-1] + math.sqrt(dx * dx + dz * dz)

        result = []
        for k in range(n):
            target = (total * k / n + phase) % total
            for i in range(N):
                j = (i + 1) % N
                l0 = arc[i]
                l1 = arc[j] if j != 0 else total
                if l1 < l0:
                    l1 = total
                if l0 <= target <= l1:
                    t = (target - l0) / max(l1 - l0, 1e-9)
                    px = pts[i][0] + t * (pts[j][0] - pts[i][0])
                    pz = pts[i][1] + t * (pts[j][1] - pts[i][1])
                    nx = nrms[i][0] + t * (nrms[j][0] - nrms[i][0])
                    nz = nrms[i][1] + t * (nrms[j][1] - nrms[i][1])
                    ln = math.sqrt(nx * nx + nz * nz) + 1e-9
                    nx, nz = nx / ln, nz / ln
                    rot = math.degrees(math.atan2(nx, nz))
                    result.append((px + nx * dist_from_center, pz + nz * dist_from_center, rot))
                    break
        return result

    def draw_all(self, base_y: float):
        from circuit import (CIRCUIT_CX as CX, CIRCUIT_CZ as CZ,
                             CIRCUIT_W as CW, CIRCUIT_H as CH,
                             ROAD_WIDTH as RW)

        y = base_y
        t_names = [m for m in self.TREES if m in self.models]
        if not t_names:
            return

        b_names = [m for m in self.BUILDINGS if m in self.models]
        if b_names:
            inner_hw = max(6.0, CW / 2.0 - (RW / 2.0 + 6.0))
            inner_hh = max(6.0, CH / 2.0 - (RW / 2.0 + 6.0))
            b_positions = [
                (CX - inner_hw * 0.6, CZ - inner_hh * 0.5),
                (CX + inner_hw * 0.6, CZ - inner_hh * 0.5),
                (CX - inner_hw * 0.6, CZ + inner_hh * 0.5),
                (CX + inner_hw * 0.6, CZ + inner_hh * 0.5),
            ]
            for i, (bx, bz) in enumerate(b_positions):
                name = b_names[i % len(b_names)]
                m = self.models[name]
                scale = 6.0 / max(m.height, 0.1)
                rot = (i * 90) % 360
                m.draw(bx, y, bz, scale=scale, rot_y=float(rot), tex_id=self.tex)

        tree_pts = self._circuit_positions(16, dist_from_center=-(RW / 2 + 1.6), phase=0.0)
        for i, (px, pz, rot) in enumerate(tree_pts):
            name = t_names[i % len(t_names)]
            m = self.models[name]
            scale = 5.5 / max(m.height, 0.1)
            rot_var = (i * 73) % 360
            m.draw(px, y, pz, scale=scale, rot_y=float(rot_var), tex_id=self.tex)


def _get_accessor_data(gltf, binary, acc_idx):
    acc = gltf.accessors[acc_idx]
    bv = gltf.bufferViews[acc.bufferView]
    start = bv.byteOffset + (acc.byteOffset or 0)

    comp_map = {
        5126: ('f', 4),
        5123: ('H', 2),
        5125: ('I', 4),
        5121: ('B', 1),
    }
    fmt, sz = comp_map[acc.componentType]
    type_counts = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    n = type_counts[acc.type]
    stride = bv.byteStride or (n * sz)
    data = []
    for i in range(acc.count):
        chunk = binary[start + i * stride: start + i * stride + n * sz]
        data.append(struct.unpack(f'{n}{fmt}', chunk))
    return data


def load_glb_model(path: str):
    try:
        import pygltflib
    except ImportError:
        return None

    gltf = pygltflib.GLTF2().load(path)
    binary = gltf.binary_blob()
    primitives_out = []

    for mesh in gltf.meshes:
        for prim in mesh.primitives:
            mat = gltf.materials[prim.material] if prim.material is not None else None
            color = (0.7, 0.7, 0.7)
            is_emissive = False
            if mat and mat.pbrMetallicRoughness:
                cf = mat.pbrMetallicRoughness.baseColorFactor
                if cf:
                    color = (float(cf[0]), float(cf[1]), float(cf[2]))
            if mat and mat.name and 'light' in mat.name.lower():
                is_emissive = True

            pos_idx = prim.attributes.POSITION
            if pos_idx is None:
                continue
            positions = _get_accessor_data(gltf, binary, pos_idx)

            nrm_idx = prim.attributes.NORMAL
            if nrm_idx is not None:
                normals = _get_accessor_data(gltf, binary, nrm_idx)
            else:
                normals = [(0.0, 1.0, 0.0)] * len(positions)

            if prim.indices is not None:
                raw_idx = _get_accessor_data(gltf, binary, prim.indices)
                indices = [x[0] for x in raw_idx]
            else:
                indices = list(range(len(positions)))

            buf = []
            for idx in indices:
                px, py, pz = positions[idx]
                nx, ny, nz = normals[idx]
                buf.extend([px, py, pz, nx, ny, nz])

            arr = np.array(buf, dtype=np.float32)
            n_vert = len(indices)

            vao = int(glGenVertexArrays(1))
            glBindVertexArray(vao)

            vbo = int(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, arr.nbytes, arr, GL_STATIC_DRAW)

            stride = 6 * 4
            glVertexPointer(3, GL_FLOAT, stride, ctypes.c_void_p(0))
            glNormalPointer(GL_FLOAT, stride, ctypes.c_void_p(12))
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_NORMAL_ARRAY)

            glBindVertexArray(0)

            primitives_out.append({
                'vao': vao,
                'count': n_vert,
                'color': color,
                'emissive': is_emissive,
            })

    all_pos = []
    for mesh in gltf.meshes:
        for prim in mesh.primitives:
            if prim.attributes.POSITION is not None:
                all_pos.extend(_get_accessor_data(gltf, binary, prim.attributes.POSITION))

    if all_pos:
        ys = [p[1] for p in all_pos]
        height = max(ys) - min(ys)
        y_min = min(ys)
    else:
        height = 1.0
        y_min = 0.0

    return {
        'primitives': primitives_out,
        'height': height,
        'y_min': y_min,
    }


def draw_glb_model(model: dict, x: float, y: float, z: float, scale: float = 1.0, rot_y: float = 0.0):
    if not model or not model.get('primitives'):
        return

    glPushMatrix()
    glTranslatef(x, y - model['y_min'] * scale, z)
    if rot_y:
        glRotatef(rot_y, 0, 1, 0)
    glScalef(scale, scale, scale)

    glDisable(GL_TEXTURE_2D)
    for prim in model['primitives']:
        r, g, b = prim['color']
        if prim['emissive']:
            glDisable(GL_LIGHTING)
            glColor3f(min(r * 2.5, 1.0), min(g * 2.5, 1.0), min(b * 2.5, 1.0))
        else:
            glEnable(GL_LIGHTING)
            glColor3f(r, g, b)
        glBindVertexArray(prim['vao'])
        glDrawArrays(GL_TRIANGLES, 0, prim['count'])
        glBindVertexArray(0)

    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glPopMatrix()
