#!/usr/bin/env python3
"""Region palette strips (6 swatches + hex each). Fjord, archipelago and canyon are measured from the rendered
key frames (median-cut on the frame, then picked by role); rainforest delta and glacier highlands are designed.
python3 tools/art/palettes.py <key_fjord.png> <key_archipelago.png> <key_canyon.png> <out.png>"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import wf_ui as U  # noqa: E402

DESIGNED = {
    "fjord": ["#1C2B2E", "#3F4C4A", "#5E7044", "#8A2E22", "#E3B27A", "#7FD6A6"],
    "archipelago": ["#F1ECE0", "#CFC3A8", "#7E8A5A", "#1FB3B0", "#0B6E8C", "#E8A85C"],
    "canyon": ["#7A3A24", "#B5653E", "#D9A273", "#4F6B3A", "#24476E", "#E9DCC6"],
    "rainforest delta": ["#13261C", "#2F5530", "#6E8C3A", "#6B5A3A", "#3E7F86", "#E7C45A"],
    "glacier highlands": ["#E9EEF2", "#A9C4D6", "#4F7A99", "#3A3F44", "#8C8F86", "#D97B4A"],
}
ROLES = {
    "fjord": "shadow water, wet rock, turf, falu red, lamp light, aurora",
    "archipelago": "limestone, dry grass, olive, shallows, deep sea, late sun",
    "canyon": "deep strata, sandstone, sand, palm, indigo awning, linen",
    "rainforest delta": "canopy shadow, leaf, moss light, mud bank, river, flower gold",
    "glacier highlands": "snow, ice, crevasse blue, basalt, moraine, hut red",
}


def measured(path, n=6):
    im = Image.open(path).convert("RGB").resize((480, 270))
    q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[: n * 3]
    cols = [tuple(pal[i * 3 : i * 3 + 3]) for i in range(n)]
    return sorted(cols, key=U.lum)


def main():
    keys = dict(zip(["fjord", "archipelago", "canyon"], sys.argv[1:4]))
    out = sys.argv[4]
    W, rowh = 1920, 196
    img = Image.new("RGB", (W, 120 + rowh * 5 + 30), U.PAPER)
    d = ImageDraw.Draw(img)
    d.text((60, 58), "MWM Wayfarer  ·  region palettes (60 / 30 / 10: first two swatches = 60, next two = 30, last two = accents)", font=U.font(30, 700), fill=U.TEXT_L, anchor="lm")
    for r, (name, hexes) in enumerate(DESIGNED.items()):
        y = 110 + r * rowh
        d.text((60, y + 30), name.title(), font=U.font(32, 700, serif=True), fill=U.TEXT_L, anchor="lm")
        src = "measured from the key frame, then rounded to roles" if name in keys else "designed (no render yet)"
        d.text((60, y + 70), src, font=U.font(19, 500), fill=U.MUTED_L, anchor="lm")
        d.text((60, y + 100), ROLES[name], font=U.font(18, 500, serif=True, italic=True), fill=U.MUTED_L, anchor="lm")
        x = 520
        for hx in hexes:
            c = tuple(int(hx[i : i + 2], 16) for i in (1, 3, 5))
            d.rounded_rectangle((x, y + 8, x + 200, y + 128), 14, fill=c)
            tc = U.TEXT_L if U.contrast(U.TEXT_L, c) > U.contrast(U.WHITE, c) else U.WHITE
            d.text((x + 14, y + 112), hx, font=U.font(20, 600), fill=tc, anchor="lm")
            x += 214
        if name in keys and Path(keys[name]).exists():
            mc = measured(keys[name])
            mx = 520
            for c in mc:
                d.rectangle((mx, y + 140, mx + 200, y + 158), fill=c)
                mx += 214
            d.text((mx + 4, y + 149), "raw frame", font=U.font(16, 500), fill=U.MUTED_L, anchor="lm")
    img.save(out, optimize=True)
    print("saved", out)


if __name__ == "__main__":
    main()
