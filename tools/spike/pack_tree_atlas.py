"""Pack the impostor frames from tools/spike/bake_tree_impostors.py into two atlases.

Run: python3 tools/spike/pack_tree_atlas.py
Writes assets/models/trees/trees_albedo.png and trees_normal.png: one row per variant, 16 frames
per row (8 azimuths at the low elevation, then 8 at the high one). Transparent texels get the
colour of the nearest covered texel (dilation) so mipmaps do not bleed a dark halo.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / "assets" / "_raw" / "build" / "impostors"
OUT = ROOT / "assets" / "models" / "trees"
meta = json.loads((OUT / "trees.json").read_text())
fw, fh = meta["frame_px"]
naz = meta["azimuths"]
nel = len(meta["elevations_deg"])
nv = len(meta["variants"])

for mode in ("albedo", "normal"):
    atlas = np.zeros((nv * fh, naz * nel * fw, 4), np.uint8)
    for v in range(nv):
        for e in range(nel):
            for a in range(naz):
                im = np.asarray(Image.open(TMP / f"v{v}_{mode}_{e}_{a}.png").convert("RGBA"))
                if mode == "normal":
                    alpha = np.asarray(
                        Image.open(TMP / f"v{v}_albedo_{e}_{a}.png").convert("RGBA")
                    )[..., 3]
                    im = np.dstack([im[..., :3], alpha])
                rgb = im[..., :3].astype(np.float32)
                cov = im[..., 3] > 8
                if cov.any():
                    _, idx = ndimage.distance_transform_edt(~cov, return_indices=True)
                    rgb = rgb[idx[0], idx[1]]
                x0 = (e * naz + a) * fw
                atlas[v * fh : (v + 1) * fh, x0 : x0 + fw, :3] = rgb.astype(np.uint8)
                atlas[v * fh : (v + 1) * fh, x0 : x0 + fw, 3] = im[..., 3]
    Image.fromarray(atlas, "RGBA").save(OUT / f"trees_{mode}.png", optimize=True)
    print("wrote", f"trees_{mode}.png", atlas.shape)
