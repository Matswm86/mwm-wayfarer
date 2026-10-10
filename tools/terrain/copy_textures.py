"""Copy the Poly Haven (CC0) terrain textures the spike uses into assets/textures/ at 1k.

Run with any Python that has Pillow: python3 tools/terrain/copy_textures.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "_raw" / "polyhaven" / "textures"
OUT = ROOT / "assets" / "textures"
SETS = {
    "leafy_grass": "grass",
    "aerial_rocks_02": "rock",
    "aerial_grass_rock": "alpine",
    "cliff_side": "cliff",
    "gray_rocks": "scree",
}
NORMALS = {"aerial_rocks_02": "rock", "cliff_side": "cliff"}

OUT.mkdir(parents=True, exist_ok=True)
for name, short in SETS.items():
    src = next((SRC / name).glob(f"{name}_diffuse_*.jpg"))
    im = Image.open(src).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    dst = OUT / f"{short}_albedo.jpg"
    im.save(dst, quality=88)
    print(src.name, "->", dst.name, dst.stat().st_size)
for name, short in NORMALS.items():
    src = next((SRC / name).glob(f"{name}_nor_gl_*.jpg"))
    im = Image.open(src).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    dst = OUT / f"{short}_normal.jpg"
    im.save(dst, quality=92)
    print(src.name, "->", dst.name, dst.stat().st_size)
