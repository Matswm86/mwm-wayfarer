"""Cliff material set (ambientCG CC0 4K scans) -> assets/incoming/cliff_materials/<name>_{albedo,normal,orm,height}.png
albedo: graded towards fjord gneiss (DESIGN 7.1: dark grey, never beige): saturation x SAT, mean sRGB luminance -> LUM
orm: R = AO, G = roughness, B = 0. normal: OpenGL. height: 16-bit displacement as given.
Also writes <name>_tile3x3.jpg (1536 px, the albedo tiled 3x3 at 1/6 scale) to judge repetition.
usage: python3 make_cliff_materials.py <acg_dir>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
SRC = Path(sys.argv[1])
OUT = (Path.home() / "MWM/projects/mwm-wayfarer/assets/incoming/cliff_materials")
OUT.mkdir(parents=True, exist_ok=True)
SETS = {  # name: (ambientCG id, saturation, target mean luminance sRGB 0-1)
    "gneiss_banded": ("Rock030", 0.55, 0.36),
    "gneiss_dark": ("Rock028", 0.55, 0.32),
    "granite_lichen": ("Rock048", 0.75, 0.40),
}
W = np.array([0.2126, 0.7152, 0.0722])
for name, (aid, sat, lum) in SETS.items():
    d = SRC / aid
    col = np.asarray(Image.open(d / f"{aid}_4K-PNG_Color.png").convert("RGB")).astype(np.float32) / 255
    L = (col * W).sum(-1, keepdims=True)
    g = L + (col - L) * sat
    g *= np.array([0.98, 1.0, 1.03])
    g *= lum / float((g * W).sum(-1).mean())
    Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).save(OUT / f"{name}_albedo.png")
    Image.open(d / f"{aid}_4K-PNG_NormalGL.png").convert("RGB").save(OUT / f"{name}_normal.png")
    ao = np.asarray(Image.open(d / f"{aid}_4K-PNG_AmbientOcclusion.png").convert("L"))
    ro = np.asarray(Image.open(d / f"{aid}_4K-PNG_Roughness.png").convert("L"))
    Image.fromarray(np.dstack([ao, ro, np.zeros_like(ao)])).save(OUT / f"{name}_orm.png")
    Image.open(d / f"{aid}_4K-PNG_Displacement.png").save(OUT / f"{name}_height.png")
    t = Image.open(OUT / f"{name}_albedo.png").resize((512, 512))
    tile = Image.new("RGB", (1536, 1536))
    for i in range(3):
        for j in range(3):
            tile.paste(t, (i * 512, j * 512))
    tile.save(OUT / f"{name}_tile3x3.jpg", quality=85)
    print(name, aid, "albedo mean", g.reshape(-1, 3).mean(0).round(3))
