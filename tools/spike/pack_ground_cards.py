"""Pack the ground-cover cards (tools/spike/bake_ground_cards.py) into one strip atlas.

Run: python3 tools/spike/pack_ground_cards.py -> assets/models/ground/ground_cards.png
Transparent texels take the nearest covered colour so mipmaps keep no dark fringe.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / "assets" / "_raw" / "build" / "ground_cards"
OUT = ROOT / "assets" / "models" / "ground"
info = json.loads((OUT / "ground_cards.json").read_text())
px = info["px"]
n = len(info["cards"])
strip = np.zeros((px, px * n, 4), np.uint8)
for i in range(n):
    im = np.asarray(Image.open(TMP / f"card{i}.png").convert("RGBA"))
    cov = im[..., 3] > 8
    rgb = im[..., :3]
    if cov.any():
        _, idx = ndimage.distance_transform_edt(~cov, return_indices=True)
        rgb = rgb[idx[0], idx[1]]
    strip[:, i * px : (i + 1) * px, :3] = rgb
    strip[:, i * px : (i + 1) * px, 3] = im[..., 3]
Image.fromarray(strip, "RGBA").save(OUT / "ground_cards.png", optimize=True)
print("wrote ground_cards.png", strip.shape)
