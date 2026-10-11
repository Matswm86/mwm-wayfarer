"""Pass 3: append two wildflower cards (dandelion, pink flower) from the graphic designer's meadow
atlas (assets/incoming/ground_cover/meadow_atlas_albedo.png, Poly Haven plant renders, CC0) to the
ground-cover strip (assets/models/ground/ground_cards.png, 6 -> 8 cards) and its json.

Run once: python3 tools/spike/add_meadow_flowers.py   (Pillow, numpy, scipy)
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "incoming" / "ground_cover" / "meadow_atlas_albedo.png"
OUT = ROOT / "assets" / "models" / "ground"
# designer tile index -> (name, card height in m)
TILES = {4: ("dandelion", 0.35), 12: ("pink_flower", 0.32)}

info = json.loads((OUT / "ground_cards.json").read_text())
assert len(info["cards"]) == 6, "already extended"
px = info["px"]
strip = np.asarray(Image.open(OUT / "ground_cards.png").convert("RGBA"))
atlas = np.asarray(Image.open(SRC).convert("RGBA"))
tile = atlas.shape[0] // 4
add = []
for idx, (name, size) in TILES.items():
    r, c = divmod(idx, 4)
    im = np.asarray(
        Image.fromarray(atlas[r * tile : (r + 1) * tile, c * tile : (c + 1) * tile]).resize(
            (px, px), Image.LANCZOS
        )
    )
    cov = im[..., 3] > 8
    rgb = im[..., :3]
    if cov.any():
        _, ind = ndimage.distance_transform_edt(~cov, return_indices=True)
        rgb = rgb[ind[0], ind[1]]
    add.append(np.dstack([rgb, im[..., 3]]))
    info["cards"].append({"model": f"designer meadow atlas tile {idx} ({name})", "size_m": size})
strip = np.concatenate([strip, *add], axis=1)
Image.fromarray(strip.astype(np.uint8), "RGBA").save(OUT / "ground_cards.png", optimize=True)
(OUT / "ground_cards.json").write_text(json.dumps(info, indent=1))
print("ground_cards.png", strip.shape)
