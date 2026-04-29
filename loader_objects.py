import os
import io
import math
import struct
import ctypes
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

    def draw(self, x, y, z, scale=1.0, rot_y=0.0, tex_id=None, shadow_pass=False):
        if self.vao is None:
            return

        glPushMatrix()
        glTranslatef(x, y - self._bbox[0][1] * scale, z)
        if rot_y:
            glRotatef(rot_y, 0, 1, 0)
        glScalef(scale, scale, scale)

        if shadow_pass:
            glDisable(GL_TEXTURE_2D)
            glDisable(GL_LIGHTING)
            glColor4f(0.0, 0.0, 0.0, 0.22)
        else:
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_LIGHTING)
            glColor3f(1, 1, 1)
        if tex_id and not shadow_pass:
            glBindTexture(GL_TEXTURE_2D, tex_id)

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

    def get_building_instances(self, base_y: float):
        from circuit import (CIRCUIT_CX as CX, CIRCUIT_CZ as CZ,
                             CIRCUIT_W as CW, CIRCUIT_H as CH,
                             ROAD_WIDTH as RW)

        b_names = [m for m in self.BUILDINGS if m in self.models]
        if not b_names:
            return []

        inner_hw = max(6.0, CW / 2.0 - (RW / 2.0 + 6.0))
        inner_hh = max(6.0, CH / 2.0 - (RW / 2.0 + 6.0))
        b_positions = [
            (CX - inner_hw * 0.6, CZ - inner_hh * 0.5),
            (CX + inner_hw * 0.6, CZ - inner_hh * 0.5),
            (CX - inner_hw * 0.6, CZ + inner_hh * 0.5),
            (CX + inner_hw * 0.6, CZ + inner_hh * 0.5),
        ]

        instances = []
        for i, (bx, bz) in enumerate(b_positions):
            name = b_names[i % len(b_names)]
            model = self.models[name]
            scale = 6.0 / max(model.height, 0.1)
            rot = float((i * 90) % 360)
            instances.append({
                "name": name,
                "x": bx,
                "y": base_y,
                "z": bz,
                "scale": scale,
                "rot_y": rot,
                "bbox_min": tuple(model._bbox[0]),
                "bbox_max": tuple(model._bbox[1]),
            })
        return instances

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

    def draw_all(self, base_y: float, shadow_pass=False):
        from circuit import ROAD_WIDTH as RW

        y = base_y
        t_names = [m for m in self.TREES if m in self.models]

        for instance in self.get_building_instances(base_y):
            self.models[instance["name"]].draw(
                instance["x"],
                y,
                instance["z"],
                scale=instance["scale"],
                rot_y=instance["rot_y"],
                tex_id=self.tex,
                shadow_pass=shadow_pass,
            )

        if not t_names:
            return

        tree_pts = self._circuit_positions(16, dist_from_center=-(RW / 2 + 1.6), phase=0.0)
        for i, (px, pz, rot) in enumerate(tree_pts):
            name = t_names[i % len(t_names)]
            m = self.models[name]
            scale = 5.5 / max(m.height, 0.1)
            rot_var = (i * 73) % 360
            m.draw(px, y, pz, scale=scale, rot_y=float(rot_var), tex_id=self.tex, shadow_pass=shadow_pass)


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


def _quat_to_matrix(quat):
    x, y, z, w = quat
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy), 0.0],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx), 0.0],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float32)


def _node_matrix(node):
    if getattr(node, "matrix", None):
        return np.array(node.matrix, dtype=np.float32).reshape((4, 4)).T

    translation = getattr(node, "translation", None) or [0.0, 0.0, 0.0]
    rotation = getattr(node, "rotation", None) or [0.0, 0.0, 0.0, 1.0]
    scale = getattr(node, "scale", None) or [1.0, 1.0, 1.0]

    t = np.identity(4, dtype=np.float32)
    t[:3, 3] = np.array(translation, dtype=np.float32)

    r = _quat_to_matrix(rotation)

    s = np.identity(4, dtype=np.float32)
    s[0, 0] = scale[0]
    s[1, 1] = scale[1]
    s[2, 2] = scale[2]

    return t @ r @ s


def _iter_scene_nodes(gltf):
    scene_index = gltf.scene if gltf.scene is not None else 0
    scene = gltf.scenes[scene_index]
    roots = list(getattr(scene, "nodes", None) or [])
    stack = [(node_index, np.identity(4, dtype=np.float32)) for node_index in roots]

    while stack:
        node_index, parent_matrix = stack.pop()
        node = gltf.nodes[node_index]
        world_matrix = parent_matrix @ _node_matrix(node)
        yield node, world_matrix
        for child_index in reversed(list(getattr(node, "children", None) or [])):
            stack.append((child_index, world_matrix))


def _load_glb_texture(gltf, binary, texture_idx, cache):
    if texture_idx is None:
        return None
    if texture_idx in cache:
        return cache[texture_idx]

    try:
        from PIL import Image as PILImage
    except ImportError:
        cache[texture_idx] = None
        return None

    texture = gltf.textures[texture_idx]
    source_index = texture.source
    if source_index is None:
        cache[texture_idx] = None
        return None

    image = gltf.images[source_index]
    if image.bufferView is None:
        cache[texture_idx] = None
        return None

    buffer_view = gltf.bufferViews[image.bufferView]
    start = buffer_view.byteOffset or 0
    raw = binary[start:start + buffer_view.byteLength]
    img = PILImage.open(io.BytesIO(raw)).convert("RGBA")
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
    cache[texture_idx] = tid
    return tid


def load_glb_model(path: str):
    try:
        import pygltflib
    except ImportError:
        return None

    gltf = pygltflib.GLTF2().load(path)
    binary = gltf.binary_blob()
    primitives_out = []
    texture_cache = {}
    all_pos = []

    for node, world_matrix in _iter_scene_nodes(gltf):
        if node.mesh is None:
            continue

        normal_matrix = np.linalg.inv(world_matrix[:3, :3]).T
        mesh = gltf.meshes[node.mesh]
        for prim in mesh.primitives:
            mat = gltf.materials[prim.material] if prim.material is not None else None
            color = (0.7, 0.7, 0.7)
            is_emissive = False
            texture_id = None
            if mat and mat.pbrMetallicRoughness:
                cf = mat.pbrMetallicRoughness.baseColorFactor
                if cf:
                    color = (float(cf[0]), float(cf[1]), float(cf[2]))
                base_color_tex = mat.pbrMetallicRoughness.baseColorTexture
                if base_color_tex and base_color_tex.index is not None:
                    texture_id = _load_glb_texture(gltf, binary, base_color_tex.index, texture_cache)
            if mat and mat.name and 'light' in mat.name.lower():
                is_emissive = True

            pos_idx = prim.attributes.POSITION
            if pos_idx is None:
                continue
            raw_positions = _get_accessor_data(gltf, binary, pos_idx)

            nrm_idx = prim.attributes.NORMAL
            if nrm_idx is not None:
                raw_normals = _get_accessor_data(gltf, binary, nrm_idx)
            else:
                raw_normals = [(0.0, 1.0, 0.0)] * len(raw_positions)

            uv_idx = prim.attributes.TEXCOORD_0
            if uv_idx is not None:
                uvs = _get_accessor_data(gltf, binary, uv_idx)
            else:
                uvs = [(0.0, 0.0)] * len(raw_positions)

            positions = []
            normals = []
            for (px, py, pz), (nx, ny, nz) in zip(raw_positions, raw_normals):
                world_pos = world_matrix @ np.array([px, py, pz, 1.0], dtype=np.float32)
                positions.append((float(world_pos[0]), float(world_pos[1]), float(world_pos[2])))

                world_nrm = normal_matrix @ np.array([nx, ny, nz], dtype=np.float32)
                nrm_len = float(np.linalg.norm(world_nrm))
                if nrm_len > 1e-9:
                    world_nrm = world_nrm / nrm_len
                else:
                    world_nrm = np.array([0.0, 1.0, 0.0], dtype=np.float32)
                normals.append((float(world_nrm[0]), float(world_nrm[1]), float(world_nrm[2])))

            if prim.indices is not None:
                raw_idx = _get_accessor_data(gltf, binary, prim.indices)
                indices = [x[0] for x in raw_idx]
            else:
                indices = list(range(len(positions)))

            buf = []
            for idx in indices:
                px, py, pz = positions[idx]
                nx, ny, nz = normals[idx]
                u, v = uvs[idx]
                buf.extend([px, py, pz, nx, ny, nz, u, v])

            arr = np.array(buf, dtype=np.float32)
            n_vert = len(indices)

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

            primitives_out.append({
                'vao': vao,
                'count': n_vert,
                'color': color,
                'emissive': is_emissive,
                'texture_id': texture_id,
            })
            all_pos.extend(positions)

    if all_pos:
        xs = [p[0] for p in all_pos]
        ys = [p[1] for p in all_pos]
        zs = [p[2] for p in all_pos]
        x_min = min(xs)
        x_max = max(xs)
        x_center = (x_min + x_max) * 0.5
        height = max(ys) - min(ys)
        y_min = min(ys)
        z_min = min(zs)
        z_max = max(zs)
        z_center = (z_min + z_max) * 0.5
    else:
        x_min = -0.5
        x_max = 0.5
        x_center = 0.0
        height = 1.0
        y_min = 0.0
        z_min = -0.5
        z_max = 0.5
        z_center = 0.0

    return {
        'primitives': primitives_out,
        'height': height,
        'y_min': y_min,
        'x_min': x_min,
        'x_max': x_max,
        'x_center': x_center,
        'z_min': z_min,
        'z_max': z_max,
        'z_center': z_center,
    }


def draw_glb_model(model: dict, x: float, y: float, z: float, scale: float = 1.0, rot_y: float = 0.0,
                   shadow_pass: bool = False, center_xz: bool = False, force_unlit: bool = False):
    if not model or not model.get('primitives'):
        return

    pivot_x = model.get('x_center', 0.0) if center_xz else 0.0
    pivot_z = model.get('z_center', 0.0) if center_xz else 0.0

    glPushMatrix()
    glTranslatef(x, y, z)
    if rot_y:
        glRotatef(rot_y, 0, 1, 0)
    glScalef(scale, scale, scale)
    glTranslatef(-pivot_x, -model['y_min'], -pivot_z)

    for prim in model['primitives']:
        r, g, b = prim['color']
        if shadow_pass:
            glDisable(GL_TEXTURE_2D)
            glDisable(GL_LIGHTING)
            glColor4f(0.0, 0.0, 0.0, 0.22)
        elif prim.get('texture_id'):
            glEnable(GL_TEXTURE_2D)
            if force_unlit:
                glDisable(GL_LIGHTING)
            else:
                glEnable(GL_LIGHTING)
            glBindTexture(GL_TEXTURE_2D, prim['texture_id'])
            glColor3f(1.0, 1.0, 1.0)
        elif prim['emissive']:
            glDisable(GL_TEXTURE_2D)
            glDisable(GL_LIGHTING)
            glColor3f(min(r * 2.5, 1.0), min(g * 2.5, 1.0), min(b * 2.5, 1.0))
        else:
            glDisable(GL_TEXTURE_2D)
            glEnable(GL_LIGHTING)
            glColor3f(r, g, b)
        glBindVertexArray(prim['vao'])
        glDrawArrays(GL_TRIANGLES, 0, prim['count'])
        glBindVertexArray(0)

    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glPopMatrix()
