"""Convert a .cube 3D LUT (tools/refmatch/fit_lut.py) into a PNG strip Godot can load.

The strip is N slices of N x N side by side (width N*N, height N): slice b holds blue index b,
x = red, y = green, which is the .cube order (red fastest). scripts/Main.gd builds an
ImageTexture3D from it for Environment.adjustment_color_correction.

Run: python3 tools/spike/cube_to_png.py assets/luts/grade.cube assets/luts/grade.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    size = 0
    rows = []
    for line in src.read_text().splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "LUT_3D_SIZE":
            size = int(parts[1])
        elif len(parts) == 3 and parts[0][0] in "0123456789.-":
            rows.append([float(v) for v in parts])
    lut = np.array(rows, dtype=np.float32).reshape(size, size, size, 3)  # [b][g][r]
    strip = np.concatenate([lut[b] for b in range(size)], axis=1)  # (g, b*size + r)
    img = np.clip(strip * 255.0 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(img, "RGB").save(dst)
    print("wrote", dst, img.shape)


if __name__ == "__main__":
    main()
