"""Pack the terrain material set (visual pass 2) from Poly Haven scans (CC0) in assets/_raw.

Output in assets/terrain/tex/:
  rock_mask.png  4096 RGBA  R = cliff_side brightness, G = rock_face_03 brightness,
                            B = cliff_side height, A = rock_face_03 height.
                            Gneiss colour comes from the shader palette; the scans give the
                            foliation, cracks and the heights for height-blended triplanar.
  rock_nrm.png   4096 RGB   cliff_side OpenGL normal
  grass.png      2048 RGBA  leafy_grass albedo + height (valley meadow)
  turf.png       2048 RGBA  sparse_grass albedo + height (alpine turf, heather tint in shader)
  soil.png       2048 RGBA  forest_ground_04 albedo + height (forest floor, paths)
  scree.png      2048 RGBA  rock_ground_02 albedo + height (scree aprons, outcrop rubble)

Run: python3 tools/spike/pack_terrain_textures.py   (Pillow, numpy)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "assets" / "_raw" / "polyhaven" / "textures"
OUT = ROOT / "assets" / "terrain" / "tex"


def img(path: str, size: int, mode: str = "RGB") -> np.ndarray:
    im = Image.open(RAW / path).convert(mode)
    if im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def lum(a: np.ndarray) -> np.ndarray:
    v = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    # stretch to the full range so the shader can map it to a gneiss tone curve
    lo, hi = np.percentile(v, 1.0), np.percentile(v, 99.0)
    return np.clip((v - lo) / (hi - lo), 0.0, 1.0)


def stretch(v: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(v, 0.5), np.percentile(v, 99.5)
    return np.clip((v - lo) / (hi - lo), 0.0, 1.0)


def save(name: str, a: np.ndarray) -> None:
    mode = "RGBA" if a.shape[-1] == 4 else "RGB"
    Image.fromarray(np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8), mode).save(
        OUT / name, optimize=True
    )
    print("wrote", name, a.shape)


def albedo_height(
    stem: str, res: str, size: int, diff: str = "diff", disp: str = "disp"
) -> np.ndarray:
    a = img(f"{stem}/{stem}_{diff}_{res}.jpg", size)
    h = stretch(img(f"{stem}/{stem}_{disp}_{res}.jpg", size, "L"))
    return np.dstack([a, h])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 4096
    cliff = img("cliff_side/cliff_side_diff_4k.jpg", n)
    face = img("rock_face_03/rock_face_03_diff_2k.jpg", n)
    cliff_h = stretch(img("cliff_side/cliff_side_disp_4k.jpg", n, "L"))
    face_h = stretch(img("rock_face_03/rock_face_03_disp_2k.jpg", n, "L"))
    save("rock_mask.png", np.dstack([lum(cliff), lum(face), cliff_h, face_h]))
    save("rock_nrm.png", img("cliff_side/cliff_side_nor_gl_4k.jpg", n))
    save("grass.png", albedo_height("leafy_grass", "2k", 2048, "diffuse", "displacement"))
    save("turf.png", albedo_height("sparse_grass", "2k", 2048))
    save("soil.png", albedo_height("forest_ground_04", "2k", 2048))
    save("scree.png", albedo_height("rock_ground_02", "2k", 2048, "diffuse", "displacement"))


if __name__ == "__main__":
    main()
