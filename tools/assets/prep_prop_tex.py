"""Texture prep for a Sketchfab prop: author's source maps -> 2K albedo / normal(GL) / ORM (R AO, G rough, B metal).
Orientation is matched to the GLB's embedded base colour automatically (Sketchfab sources are often V-flipped).
usage: python3 prep_prop_tex.py <glb> <out_prefix> albedo=<f> normal=<f> [ao=<f>] [rough=<f>] [metal=<f>] [size=2048]
"""
import io
import json
import struct
import sys

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None
glb, pre = sys.argv[1], sys.argv[2]
kw = dict(a.split("=", 1) for a in sys.argv[3:])
N = int(kw.get("size", 2048))
f = open(glb, "rb").read()
ln = struct.unpack("<I", f[12:16])[0]
g = json.loads(f[20:20 + ln])
b0 = 20 + ln + 8
bc = g["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"]["index"]
bv = g["bufferViews"][g["images"][g["textures"][bc]["source"]]["bufferView"]]
ref = Image.open(io.BytesIO(f[b0 + bv.get("byteOffset", 0): b0 + bv.get("byteOffset", 0) + bv["byteLength"]])).convert("L").resize((256, 256))


def corr(a, b):
    a = np.asarray(a, float) - np.asarray(a, float).mean()
    b = np.asarray(b, float) - np.asarray(b, float).mean()
    return (a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum())


alb = Image.open(kw["albedo"]).convert("RGB")
small = alb.convert("L").resize((256, 256))
flip = corr(ref, ImageOps.flip(small)) > corr(ref, small)
print("flip", flip, round(corr(ref, small), 3), round(corr(ref, ImageOps.flip(small)), 3))


def prep(path, mode):
    im = Image.open(path).convert(mode)
    if flip:
        im = ImageOps.flip(im)
    return im.resize((N, N), Image.LANCZOS)


prep(kw["albedo"], "RGB").save(pre + "_albedo.png")
prep(kw["normal"], "RGB").save(pre + "_normal.png")
ao = np.asarray(prep(kw["ao"], "L")) if "ao" in kw else np.full((N, N), 255, np.uint8)
ro = np.asarray(prep(kw["rough"], "L")) if "rough" in kw else np.full((N, N), 210, np.uint8)
me = np.asarray(prep(kw["metal"], "L")) if "metal" in kw else np.zeros((N, N), np.uint8)
Image.fromarray(np.dstack([ao, ro, me])).save(pre + "_orm.png")
print("wrote", pre)
