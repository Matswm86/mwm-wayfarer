#!/usr/bin/env python3
"""UI kit for the Wayfarer mockups (Pillow), drawn over the Blender renders like Race Riders hud_overlay.py.
Tokens are the ones written into docs/DESIGN.md section 6; contrast numbers printed by `contrast()` are my calc.
Scale: mock 1920x1080 landscape = 2.625 px per dp (a 411 dp tall phone), so 48 dp = 126 px.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "assets" / "fonts"
DP = 2.625

# ---------------------------------------------------------------- tokens
INK = (17, 21, 26)  # #11151A  dark chrome (panels over the world, 84% alpha)
INK2 = (30, 36, 43)  # #1E242B  raised dark surface
PAPER = (245, 240, 230)  # #F5F0E6  light card / ledger surface
PAPER2 = (232, 224, 210)  # #E8E0D2  row stripe on paper
TEXT_D = (246, 243, 236)  # #F6F3EC  text on dark
MUTED_D = (184, 191, 199)  # #B8BFC7  secondary text on dark
TEXT_L = (27, 31, 36)  # #1B1F24  text on paper
MUTED_L = (92, 86, 78)  # #5C564E  secondary text on paper
AMBER = (240, 168, 60)  # #F0A83C  wonders, rumours, discovery
AMBER_D = (150, 96, 20)  # #966014  amber text on paper
TEAL = (47, 163, 150)  # #2FA396  confirm, price up, valid placement
TEAL_D = (20, 110, 100)  # #146E64  teal text on paper
CLAY = (210, 85, 63)  # #D2553F  price down, missing material
CLAY_D = (168, 52, 34)  # #A83422  clay text on paper
WHITE = (255, 255, 255)


def hexs(c):
    return "#%02X%02X%02X" % c[:3]


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = c[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def over(fg, bg, a):
    return tuple(int(fg[i] * a + bg[i] * (1 - a)) for i in range(3))


# ---------------------------------------------------------------- fonts
_FC: dict = {}


def font(size, weight=500, serif=False, italic=False):
    key = (size, weight, serif, italic)
    if key in _FC:
        return _FC[key]
    if serif:
        p = FONTS / ("SourceSerif4-Italic[opsz,wght].ttf" if italic else "SourceSerif4[opsz,wght].ttf")
    else:
        p = FONTS / "Inter[opsz,wght].ttf"
    f = ImageFont.truetype(str(p), size)
    try:
        axes = f.get_variation_axes()
        vals = []
        for ax in axes:
            nm = ax.get("name", b"")
            nm = nm.decode() if isinstance(nm, bytes) else str(nm)
            if "eight" in nm or nm.lower().startswith("wght"):
                vals.append(weight)
            elif "ptical" in nm or nm.lower().startswith("opsz"):
                vals.append(max(ax["minimum"], min(ax["maximum"], size * 0.75)))
            else:
                vals.append(ax.get("default", ax["minimum"]))
        f.set_variation_by_axes(vals)
    except Exception as e:  # noqa: BLE001
        print("font variation failed", e)
    _FC[key] = f
    return f


# ---------------------------------------------------------------- drawing helpers
def layer(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def shadow(base, box, radius, blur=18, alpha=90, off=(0, 6)):
    sh = Image.new("L", base.size, 0)
    d = ImageDraw.Draw(sh)
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]), radius, fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    blk = Image.new("RGBA", base.size, (0, 0, 0, 0))
    blk.putalpha(sh)
    base.alpha_composite(blk)


def panel(base, box, radius=18, fill=INK, alpha=0.84, outline=None, ow=2, drop=True):
    if drop:
        shadow(base, box, radius)
    L = layer(base.size)
    d = ImageDraw.Draw(L)
    d.rounded_rectangle(box, radius, fill=(*fill, int(255 * alpha)), outline=(*outline, 255) if outline else None, width=ow)
    base.alpha_composite(L)


def text(d, xy, s, f, fill, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def tw(s, f):
    b = f.getbbox(s)
    return b[2] - b[0]


def disc(d, c, r, fill, ring=None, ring_w=4):
    x, y = c
    d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=ring, width=ring_w if ring else 0)


def blur_region(img, box, radius=14, darken=0.0):
    reg = img.crop(box).filter(ImageFilter.GaussianBlur(radius))
    if darken:
        blk = Image.new("RGBA", reg.size, (0, 0, 0, int(255 * darken)))
        reg = Image.alpha_composite(reg.convert("RGBA"), blk)
    img.paste(reg, box[:2])


def vgrad(size, top_rgba, bot_rgba):
    w, h = size
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top_rgba[i] * (1 - t) + bot_rgba[i] * t) for i in range(4)))
    return g.resize((w, h))


# ---------------------------------------------------------------- icons (white vector glyphs)
def ic_leaf(d, c, s, col):
    x, y = c
    pts = []
    for i in range(40):
        t = i / 39 * math.pi
        pts.append((x + math.cos(t) * s * 0.9 * 0.5 - s * 0.0, y - math.sin(t) * s * 0.42))
    d.polygon([(x - s * 0.55, y + s * 0.35), (x + s * 0.55, y - s * 0.45), (x + s * 0.2, y + s * 0.25)], fill=col)
    d.ellipse((x - s * 0.55, y - s * 0.45, x + s * 0.55, y + s * 0.35), fill=col)
    d.line((x - s * 0.7, y + s * 0.55, x + s * 0.35, y - s * 0.25), fill=INK, width=max(2, int(s * 0.09)))


def ic_hand(d, c, s, col):
    x, y = c
    d.rounded_rectangle((x - s * 0.42, y - s * 0.05, x + s * 0.38, y + s * 0.6), int(s * 0.18), fill=col)
    for i, (dx, hh) in enumerate(((-0.32, 0.55), (-0.11, 0.7), (0.1, 0.66), (0.29, 0.5))):
        d.rounded_rectangle((x + s * dx - s * 0.085, y - s * hh, x + s * dx + s * 0.085, y + s * 0.1), max(1, int(s * 0.05)), fill=col)
    d.rounded_rectangle((x - s * 0.62, y + s * 0.0, x - s * 0.36, y + s * 0.38), int(s * 0.1), fill=col)


def ic_jump(d, c, s, col):
    x, y = c
    d.polygon([(x, y - s * 0.6), (x - s * 0.5, y), (x - s * 0.18, y), (x - s * 0.18, y + s * 0.55), (x + s * 0.18, y + s * 0.55), (x + s * 0.18, y), (x + s * 0.5, y)], fill=col)


def ic_star(d, c, s, col):
    x, y = c
    pts = []
    for i in range(10):
        r = s if i % 2 == 0 else s * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    d.polygon(pts, fill=col)


def ic_diamond(d, c, s, fill, ring=None):
    x, y = c
    d.polygon([(x, y - s), (x + s, y), (x, y + s), (x - s, y)], fill=fill, outline=ring)


def ic_bubble(d, c, s, fill, mark=INK):
    x, y = c
    d.rounded_rectangle((x - s, y - s * 0.75, x + s, y + s * 0.55), int(s * 0.45), fill=fill)
    d.polygon([(x - s * 0.35, y + s * 0.4), (x - s * 0.55, y + s * 1.0), (x + s * 0.05, y + s * 0.45)], fill=fill)
    f = font(int(s * 1.25), 800)
    d.text((x, y - s * 0.1), "?", font=f, fill=mark, anchor="mm")


def ic_anchor(d, c, s, col, w=4):
    x, y = c
    d.ellipse((x - s * 0.18, y - s * 0.9, x + s * 0.18, y - s * 0.54), outline=col, width=w)
    d.line((x, y - s * 0.54, x, y + s * 0.75), fill=col, width=w)
    d.line((x - s * 0.4, y - s * 0.3, x + s * 0.4, y - s * 0.3), fill=col, width=w)
    d.arc((x - s * 0.75, y - s * 0.2, x + s * 0.75, y + s * 0.8), 20, 160, fill=col, width=w)


def ic_sun(d, c, s, col):
    x, y = c
    d.ellipse((x - s * 0.45, y - s * 0.45, x + s * 0.45, y + s * 0.45), fill=col)
    for i in range(8):
        a = i * math.pi / 4
        d.line((x + math.cos(a) * s * 0.65, y + math.sin(a) * s * 0.65, x + math.cos(a) * s * 0.95, y + math.sin(a) * s * 0.95), fill=col, width=max(2, int(s * 0.14)))


def ic_moon(d, c, s, col, bg):
    x, y = c
    d.ellipse((x - s * 0.7, y - s * 0.7, x + s * 0.7, y + s * 0.7), fill=col)
    d.ellipse((x - s * 0.35, y - s * 0.9, x + s * 0.95, y + s * 0.4), fill=bg)


def ic_pack(d, c, s, col):
    x, y = c
    d.rounded_rectangle((x - s * 0.55, y - s * 0.55, x + s * 0.55, y + s * 0.8), int(s * 0.25), fill=col)
    d.rounded_rectangle((x - s * 0.3, y - s * 0.85, x + s * 0.3, y - s * 0.45), int(s * 0.12), outline=col, width=max(2, int(s * 0.14)))
    d.rectangle((x - s * 0.55, y - s * 0.05, x + s * 0.55, y + s * 0.05), fill=INK)


def ic_coin(d, c, s):
    x, y = c
    d.ellipse((x - s, y - s, x + s, y + s), fill=(214, 160, 52))
    d.ellipse((x - s * 0.72, y - s * 0.72, x + s * 0.72, y + s * 0.72), outline=(250, 214, 120), width=max(2, int(s * 0.14)))


def ic_gear(d, c, r, col, hole):
    x, y = c
    pts = []
    for i in range(16):
        a = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.78
        for da in (-0.17, 0.17):
            pts.append((x + math.cos(a + da) * rr, y + math.sin(a + da) * rr))
    d.polygon(pts, fill=col)
    d.ellipse((x - r * 0.36, y - r * 0.36, x + r * 0.36, y + r * 0.36), fill=hole)


def ic_map(d, c, s, col):
    x, y = c
    d.polygon([(x - s, y - s * 0.7), (x - s * 0.33, y - s * 0.9), (x + s * 0.33, y - s * 0.7), (x + s, y - s * 0.9), (x + s, y + s * 0.7), (x + s * 0.33, y + s * 0.9), (x - s * 0.33, y + s * 0.7), (x - s, y + s * 0.9)], fill=col)
    for xx in (-0.33, 0.33):
        d.line((x + s * xx, y - s * 0.8 + (0.2 * s if xx > 0 else 0), x + s * xx, y + s * 0.8), fill=INK, width=max(2, int(s * 0.1)))


def ic_rotate(d, c, s, col, w=6, flip=False):
    x, y = c
    a0, a1 = (200, 470) if not flip else (70, 340)
    d.arc((x - s, y - s, x + s, y + s), a0, a1, fill=col, width=w)
    a = math.radians(a1 if not flip else a0)
    tip = (x + math.cos(a) * s, y + math.sin(a) * s)
    dirv = (-math.sin(a), math.cos(a)) if not flip else (math.sin(a), -math.cos(a))
    p1 = (tip[0] + dirv[0] * s * 0.45, tip[1] + dirv[1] * s * 0.45)
    nrm = (math.cos(a), math.sin(a))
    d.polygon([p1, (tip[0] + nrm[0] * s * 0.32, tip[1] + nrm[1] * s * 0.32), (tip[0] - nrm[0] * s * 0.32, tip[1] - nrm[1] * s * 0.32)], fill=col)


def ic_check(d, c, s, col, w=10):
    x, y = c
    d.line((x - s * 0.55, y, x - s * 0.15, y + s * 0.4, x + s * 0.6, y - s * 0.45), fill=col, width=w, joint="curve")


def ic_cross(d, c, s, col, w=8):
    x, y = c
    d.line((x - s * 0.45, y - s * 0.45, x + s * 0.45, y + s * 0.45), fill=col, width=w)
    d.line((x - s * 0.45, y + s * 0.45, x + s * 0.45, y - s * 0.45), fill=col, width=w)


def arrow(d, c, s, up, col):
    x, y = c
    if up:
        d.polygon([(x, y - s), (x + s * 0.85, y + s * 0.6), (x - s * 0.85, y + s * 0.6)], fill=col)
    else:
        d.polygon([(x, y + s), (x + s * 0.85, y - s * 0.6), (x - s * 0.85, y - s * 0.6)], fill=col)


def waveform(d, x, y, w, h, col, seed=3, bars=14):
    import random

    r = random.Random(seed)
    bw = w / (bars * 1.7)
    for i in range(bars):
        a = 0.25 + 0.75 * abs(math.sin(i * 0.9 + 0.4)) * r.uniform(0.6, 1.0)
        bh = h * a
        bx = x + i * bw * 1.7
        d.rounded_rectangle((bx, y + (h - bh) / 2, bx + bw, y + (h + bh) / 2), int(bw / 2), fill=col)


def report(pairs):
    """pairs: list of (label, fg, bg). Prints WCAG contrast (my calc)."""
    for lab, fg, bg in pairs:
        print(f"CONTRAST {lab}: {hexs(fg)} on {hexs(bg)} = {contrast(fg, bg):.2f}:1 (my calc)")


# This Pillow build rejects a corner radius that leaves no straight edge; clamp it for small icons.
_rr = ImageDraw.ImageDraw.rounded_rectangle


def _safe_rr(self, xy, radius=0, *a, **k):
    (x0, y0), (x1, y1) = (xy[0], xy[1]) if len(xy) == 2 else ((xy[0], xy[1]), (xy[2], xy[3]))
    radius = max(0, min(int(radius), int((min(x1 - x0, y1 - y0) - 3) // 2)))
    return _rr(self, (x0, y0, x1, y1), radius, *a, **k)


ImageDraw.ImageDraw.rounded_rectangle = _safe_rr
