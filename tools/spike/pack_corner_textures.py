"""Beauty corner ground layers (pass 3): Poly Haven scans (CC0) fetched at 2K and packed.

Output in assets/terrain/tex/:
  path.png        2048 RGBA  grass_path_2 albedo + height (worn dirt path through the village)
  path_nrm.png    2048 RGBA  grass_path_2 OpenGL normal xy + roughness in B
  gravel.png      2048 RGBA  gravel_ground_01 albedo + height (path edges, yard gravel)
  pebbles.png     2048 RGBA  ganges_river_pebbles albedo + height (fjord shore)
  pebbles_nrm.png 2048 RGBA  ganges_river_pebbles normal xy + roughness in B
  sand.png        2048 RGBA  damp_beach_sand_02 albedo + height (wet sand at the water line)

Downloads go to assets/_raw/polyhaven/textures/<name>/ (gitignored).
Run: python3 tools/spike/pack_corner_textures.py   (Pillow, numpy, network)
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "assets" / "_raw" / "polyhaven" / "textures"
OUT = ROOT / "assets" / "terrain" / "tex"
SETS = {
    "path": "grass_path_2",
    "gravel": "gravel_ground_01",
    "pebbles": "ganges_river_pebbles",
    "sand": "damp_beach_sand_02",
}
NORMALS = ("path", "pebbles")
SIZE = 2048
UA = {"User-Agent": "mwm-wayfarer-tools/1.0"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        return r.read()


def fetch(name: str) -> dict[str, Path]:
    files = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
    out = {}
    for key, kind, fmt in (
        ("diff", "Diffuse", "jpg"),
        ("disp", "Displacement", "png"),
        ("nor", "nor_gl", "jpg"),
        ("rough", "Rough", "jpg"),
    ):
        entry = files.get(kind) or files.get(key)
        if entry is None:
            continue
        url = entry["2k"][fmt]["url"]
        dst = RAW / name / url.rsplit("/", 1)[1]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            dst.write_bytes(get(url))
        out[key] = dst
    return out


def load(p: Path, mode: str) -> np.ndarray:
    im = Image.open(p)
    if im.mode in ("I;16", "I"):
        a = np.asarray(im, dtype=np.float32)
        a = (a - a.min()) / max(a.max() - a.min(), 1.0)
        im = Image.fromarray((a * 255).astype(np.uint8))
    im = im.convert(mode)
    if im.size != (SIZE, SIZE):
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
    return np.asarray(im, dtype=np.uint8)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, name in SETS.items():
        f = fetch(name)
        alb = load(f["diff"], "RGB")
        hgt = load(f["disp"], "L")
        Image.fromarray(np.dstack([alb, hgt])).save(OUT / f"{key}.png")
        if key in NORMALS:
            nrm = load(f["nor"], "RGB")
            rough = load(f["rough"], "L")
            Image.fromarray(np.dstack([nrm[..., 0], nrm[..., 1], rough, hgt])).save(
                OUT / f"{key}_nrm.png"
            )
        print("packed", key, "from", name)


if __name__ == "__main__":
    main()
