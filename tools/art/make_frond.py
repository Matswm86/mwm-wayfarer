#!/usr/bin/env python3
"""Date-palm frond texture (RGBA, 1024x256): rachis plus ~70 leaflet pairs, colour jitter, dry tips.
Own work (Pillow). python3 tools/art/make_frond.py"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / "assets" / "_raw" / "build" / "palm_frond.png"
W, H = 2048, 512
r = random.Random(4)
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
cy = H // 2
for side in (-1, 1):
    n = 80
    for i in range(n):
        t = i / n
        x0 = 60 + t * (W - 140)
        L = (H * 0.47) * (math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.6) * r.uniform(0.85, 1.05)
        ang = math.radians(r.uniform(28, 42) + 20 * t)
        x1 = x0 + math.cos(ang) * L
        y1 = cy + side * math.sin(ang) * L
        g = r.uniform(0.75, 1.1)
        dry = t > 0.85 and r.random() < 0.4
        col = (int(72 * g), int(98 * g), int(48 * g)) if not dry else (int(140 * g), int(118 * g), int(70 * g))
        wid = max(3, int(9 * (1 - 0.5 * t)))
        steps = 14
        pts_a, pts_b = [], []
        for k in range(steps + 1):
            s = k / steps
            px = x0 + (x1 - x0) * s
            py = cy + (y1 - cy) * s + side * 6 * math.sin(math.pi * s)
            ww = wid * math.sin(math.pi * min(1.0, s * 1.05 + 0.05)) ** 0.5
            nx, ny = -(y1 - cy), (x1 - x0)
            ln = math.hypot(nx, ny)
            nx, ny = nx / ln, ny / ln
            pts_a.append((px + nx * ww / 2, py + ny * ww / 2))
            pts_b.append((px - nx * ww / 2, py - ny * ww / 2))
        d.polygon(pts_a + pts_b[::-1], fill=(*col, 255))
        # midrib highlight
        d.line((x0, cy, x0 + (x1 - x0) * 0.9, cy + (y1 - cy) * 0.9), fill=(int(110 * g), int(130 * g), int(70 * g), 255), width=1)
d.line((20, cy, W - 40, cy), fill=(120, 112, 70, 255), width=12)
d.line((20, cy - 3, W - 40, cy - 2), fill=(160, 150, 96, 255), width=3)
img = img.filter(ImageFilter.SMOOTH)
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print("frond", OUT)
