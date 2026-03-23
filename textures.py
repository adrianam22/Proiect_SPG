from OpenGL.GL import *
import numpy as np


def load_texture(path, repeat=True):
    from PIL import Image as PILImage

    def next_pow2(n):
        p = 1
        while p < n:
            p <<= 1
        return p

    img = PILImage.open(path).convert("RGB")
    max_size = 2048
    new_w = min(max_size, next_pow2(img.width))
    new_h = min(max_size, next_pow2(img.height))
    if (new_w, new_h) != (img.width, img.height):
        img = img.resize((new_w, new_h), PILImage.LANCZOS)

    img = img.transpose(PILImage.FLIP_TOP_BOTTOM)
    data = np.array(img, dtype=np.uint8)

    tid = int(glGenTextures(1))
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
