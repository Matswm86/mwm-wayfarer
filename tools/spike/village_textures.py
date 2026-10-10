"""Copy the Poly Haven (CC0) texture sets the exported village uses into assets/models/village/tex/.

Run after tools/spike/export_village.py: python3 tools/spike/village_textures.py
Per set: albedo (desaturated to the set's saturation from materials.json; the tint is in the
vertex colours), OpenGL normal and ARM (AO, roughness, metal), all 1024 px JPEG.
"""

import json
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "_raw" / "polyhaven" / "textures"
OUT = ROOT / "assets" / "models" / "village" / "tex"
SIZE = 1024

OUT.mkdir(parents=True, exist_ok=True)
mats = json.loads((OUT.parent / "materials.json").read_text())
for info in mats.values():
    name = info["set"]
    if name == "flat":
        continue
    for kind, key in (("albedo", "diffuse"), ("normal", "nor_gl"), ("arm", "arm")):
        src = next((SRC / name).glob(f"{name}_{key}_*.jpg"))
        im = Image.open(src).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
        if kind == "albedo" and info["sat"] < 0.99:
            im = ImageEnhance.Color(im).enhance(info["sat"])
        dst = OUT / f"{name}_{kind}.jpg"
        im.save(dst, quality=88)
        print(src.name, "->", dst.name, dst.stat().st_size)
