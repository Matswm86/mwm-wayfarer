"""Pack the 16 rendered twig tiles into the leaf atlas (called by cardify_tree.py, system Python + Pillow).
usage: python3 pack_leaf_atlas.py <tmp_dir> <out_dir> <species> <tiles> <tile_px>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def pack_atlas(TMP, OUT, species, TILES, TILE_PX):

    n = TILES * TILE_PX
    yy, xx = np.mgrid[0:TILE_PX, 0:TILE_PX]
    r = np.hypot(xx - TILE_PX / 2 + 0.5, yy - TILE_PX / 2 + 0.5) / (TILE_PX / 2)
    soft = np.ones_like(r)  # tiles hold only whole sprays (island-selected), no fade needed
    alb = np.zeros((n, n, 4), np.uint8)
    nor = np.zeros((n, n, 3), np.uint8)
    orm = np.zeros((n, n, 3), np.uint8)
    for i in range(TILES * TILES):
        ty, tx = divmod(i, TILES)
        sl = (slice(ty * TILE_PX, (ty + 1) * TILE_PX), slice(tx * TILE_PX, (tx + 1) * TILE_PX))
        a = np.asarray(Image.open(TMP / f"{species}_albedo_{i:02d}.png").convert("RGBA")).astype(np.float32)
        nm = np.asarray(Image.open(TMP / f"{species}_normal_{i:02d}.png").convert("RGBA")).astype(np.float32)
        ao = np.asarray(Image.open(TMP / f"{species}_ao_{i:02d}.png").convert("RGBA")).astype(np.float32)
        alpha = a[..., 3] / 255.0 * soft
        # bleed colour into the cut-away area so mips never fringe dark
        rgb = a[..., :3]
        filled = Image.fromarray(rgb.astype(np.uint8))
        m = Image.fromarray((alpha > 0.02).astype(np.uint8) * 255)
        for _ in range(6):
            bl = filled.filter(ImageFilter.BoxBlur(6))
            mb = m.filter(ImageFilter.BoxBlur(6))
            fa = np.asarray(filled).astype(np.float32)
            ba = np.asarray(bl).astype(np.float32)
            mm = np.asarray(m)[..., None] > 0
            mba = np.asarray(mb).astype(np.float32)[..., None] / 255.0
            est = np.where(mba > 0.01, ba / np.maximum(mba, 1e-3), fa)
            fa = np.where(mm, fa, est)
            filled = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8))
            m = Image.fromarray(np.maximum(np.asarray(m), (np.asarray(mb) > 0) * 255).astype(np.uint8))
        # fold 60 % of the tile's own needle AO into the colour: flat cards otherwise read too pale in sun
        aof = ao[..., 0:1] / 255.0
        aof[ao[..., 3] < 10] = 1.0
        col = np.asarray(filled).astype(np.float32) * (0.4 + 0.6 * aof) * 0.85
        alb[sl] = np.dstack([np.clip(col, 0, 255).astype(np.uint8), (alpha * 255).astype(np.uint8)])
        nn = nm[..., :3]
        nn[nm[..., 3] < 10] = (128, 128, 255)
        nor[sl] = nn.astype(np.uint8)
        o = ao[..., 0]
        o[ao[..., 3] < 10] = 255
        orm[sl] = np.dstack([o, np.full_like(o, 0.80 * 255), np.zeros_like(o)]).astype(np.uint8)
    Image.fromarray(alb, "RGBA").save(OUT / f"{species}_leaves_albedo.png", optimize=True)
    Image.fromarray(nor).save(OUT / f"{species}_leaves_normal.png", optimize=True)
    Image.fromarray(orm).save(OUT / f"{species}_leaves_orm.png", optimize=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    pack_atlas(Path(a[0]), Path(a[1]), a[2], int(a[3]), int(a[4]))
