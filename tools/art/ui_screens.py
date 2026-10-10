#!/usr/bin/env python3
"""Draw the Wayfarer UI mockups over the Blender renders (Pillow). Prints contrast numbers (my calc).

python3 tools/art/ui_screens.py hud   <raw.png> <out.png>
python3 tools/art/ui_screens.py talk  <raw.png> <out.png>
python3 tools/art/ui_screens.py trade <raw.png> <out.png> <icons_dir>
python3 tools/art/ui_screens.py wonder <raw_bg.png> <photo.png> <out.png>
python3 tools/art/ui_screens.py build <raw.png> <out.png>
python3 tools/art/ui_screens.py grade <raw.png> <out.png>      (vignette + gentle grade only, for key frames)
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import wf_ui as U  # noqa: E402

W, H = 1920, 1080
M = 48  # safe margin px


def load(p):
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return im


def grade(im, vignette=0.22, contrast=1.04, sat=1.03):
    """Final look: gentle contrast, a soft vignette (moved out of the Blender compositor)."""
    rgb = im.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Color(rgb).enhance(sat)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((-W * 0.18, -H * 0.3, W * 1.18, H * 1.3), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    v = Image.composite(rgb, Image.blend(rgb, dark, vignette), mask)
    return v.convert("RGBA")


# ---------------------------------------------------------------- HUD
def compass(im, heading=352, markers=()):
    d = ImageDraw.Draw(im)
    cw, ch = 760, 50
    x0, y0 = (W - cw) // 2, 34
    U.panel(im, (x0, y0, x0 + cw, y0 + ch), radius=25, fill=U.INK, alpha=0.62, drop=False)
    d = ImageDraw.Draw(im)
    fov = 150.0
    f_card = U.font(22, 700)
    f_small = U.font(15, 600)
    for deg in range(0, 360, 15):
        rel = ((deg - heading + 540) % 360) - 180
        if abs(rel) > fov / 2:
            continue
        x = x0 + cw / 2 + rel / (fov / 2) * (cw / 2 - 30)
        if deg % 90 == 0:
            d.text((x, y0 + ch / 2), "NESW"[deg // 90], font=f_card, fill=U.TEXT_D, anchor="mm")
        elif deg % 45 == 0:
            d.text((x, y0 + ch / 2), ["NE", "SE", "SW", "NW"][deg // 90], font=f_small, fill=U.MUTED_D, anchor="mm")
        else:
            d.line((x, y0 + 18, x, y0 + ch - 18), fill=(*U.MUTED_D, 255), width=2)
    for kind, deg, label in markers:
        rel = ((deg - heading + 540) % 360) - 180
        x = x0 + cw / 2 + rel / (fov / 2) * (cw / 2 - 30)
        yy = y0 + ch + 22
        if kind == "wonder":
            U.ic_diamond(d, (x, y0 + ch / 2), 11, U.AMBER, ring=U.INK)
            U.ic_star(d, (x, y0 + ch / 2), 5, U.INK)
        elif kind == "rumor":
            U.ic_bubble(d, (x, y0 + ch / 2 - 2), 11, U.TEXT_D)
        elif kind == "trade":
            U.ic_anchor(d, (x, y0 + ch / 2), 13, U.TEAL, w=3)
        f = U.font(17, 600)
        tw = U.tw(label, f)
        U.panel(im, (x - tw / 2 - 10, yy - 13, x + tw / 2 + 10, yy + 15), radius=14, fill=U.INK, alpha=0.62, drop=False)
        d = ImageDraw.Draw(im)
        d.text((x, yy + 1), label, font=f, fill=U.AMBER if kind == "wonder" else U.TEXT_D, anchor="mm")
    # heading caret
    d.polygon([(W / 2 - 8, y0 - 2), (W / 2 + 8, y0 - 2), (W / 2, y0 + 8)], fill=U.TEXT_D)
    return im


def chip(im, x, y, w, h, draw_fn):
    U.panel(im, (x, y, x + w, y + h), radius=h // 2, fill=U.INK, alpha=0.66, drop=False)
    d = ImageDraw.Draw(im)
    draw_fn(d)


def hud(raw, out):
    im = grade(load(raw))
    im = compass(im, heading=352, markers=[("wonder", 318, "Bluewater Falls  1.2 km"), ("rumor", 15, "Blue moss?"), ("trade", 40, "Skarvik dock")])
    d = ImageDraw.Draw(im)
    # top-left: menu disc (48 dp min) + map disc
    for i, fn in enumerate((lambda dd, c: U.ic_gear(dd, c, 26, U.TEXT_D, U.INK), lambda dd, c: U.ic_map(dd, c, 22, U.TEXT_D))):
        c = (M + 63 + i * 140, M + 63)
        U.panel(im, (c[0] - 63, c[1] - 63, c[0] + 63, c[1] + 63), radius=63, fill=U.INK, alpha=0.62, drop=False)
        d = ImageDraw.Draw(im)
        fn(d, c)
    # top-right: time/weather + pack weight
    f = U.font(24, 600)
    fs = U.font(18, 500)
    x1 = W - M
    chip(im, x1 - 300, M + 6, 300, 54, lambda dd: (U.ic_moon(dd, (x1 - 270, M + 33), 13, U.TEXT_D, U.over(U.INK, (40, 50, 60), 0.66)), dd.text((x1 - 245, M + 33), "21:40  Clear  4°C", font=f, fill=U.TEXT_D, anchor="lm")))
    def pack(dd):
        U.ic_pack(dd, (x1 - 270, M + 103), 14, U.TEXT_D)
        dd.text((x1 - 245, M + 104), "18.4 / 30 kg", font=f, fill=U.TEXT_D, anchor="lm")
        dd.rounded_rectangle((x1 - 245, M + 124, x1 - 40, M + 130), 3, fill=(255, 255, 255, 60))
        dd.rounded_rectangle((x1 - 245, M + 124, x1 - 245 + int(205 * 18.4 / 30), M + 130), 3, fill=U.TEAL)
    chip(im, x1 - 300, M + 72, 300, 64, pack)
    # left move stick (thumb zone), bottom-left
    c = (M + 190, H - M - 190)
    L = U.layer((W, H))
    dl = ImageDraw.Draw(L)
    dl.ellipse((c[0] - 150, c[1] - 150, c[0] + 150, c[1] + 150), fill=(17, 21, 26, 70), outline=(246, 243, 236, 120), width=3)
    dl.ellipse((c[0] - 52 + 20, c[1] - 52 - 34, c[0] + 52 + 20, c[1] + 52 - 34), fill=(246, 243, 236, 205))
    im.alpha_composite(L)
    # right: action button (Gather) + jump
    ca = (W - M - 120, H - M - 150)
    U.shadow(im, (ca[0] - 84, ca[1] - 84, ca[0] + 84, ca[1] + 84), 84, blur=16, alpha=80)
    d = ImageDraw.Draw(im)
    U.disc(d, ca, 84, U.AMBER, ring=U.WHITE, ring_w=4)
    U.ic_leaf(d, (ca[0], ca[1] - 10), 40, U.INK)
    d.text((ca[0], ca[1] + 46), "Gather", font=U.font(22, 700), fill=U.INK, anchor="mm")
    cj = (ca[0] - 200, ca[1] + 70)
    U.panel(im, (cj[0] - 64, cj[1] - 64, cj[0] + 64, cj[1] + 64), radius=64, fill=U.INK, alpha=0.66, drop=False)
    d = ImageDraw.Draw(im)
    U.ic_jump(d, cj, 30, U.TEXT_D)
    cc = (ca[0] - 170, ca[1] - 150)
    U.panel(im, (cc[0] - 64, cc[1] - 64, cc[0] + 64, cc[1] + 64), radius=64, fill=U.INK, alpha=0.66, drop=False)
    d = ImageDraw.Draw(im)
    U.ic_hand(d, (cc[0], cc[1] + 4), 30, U.TEXT_D)
    # world-space gather prompt pinned to a plant
    gx, gy = 1180, 760
    U.panel(im, (gx - 6, gy - 6, gx + 6, gy + 6), radius=6, fill=U.AMBER, alpha=1.0, drop=False)
    d = ImageDraw.Draw(im)
    d.line((gx, gy - 8, gx, gy - 46), fill=U.AMBER, width=3)
    lab = "Cloudberries  x6"
    f2 = U.font(22, 600)
    tw = U.tw(lab, f2)
    U.panel(im, (gx - tw / 2 - 18, gy - 92, gx + tw / 2 + 18, gy - 48), radius=22, fill=U.INK, alpha=0.78, drop=False)
    d = ImageDraw.Draw(im)
    d.text((gx, gy - 70), lab, font=f2, fill=U.TEXT_D, anchor="mm")
    im.convert("RGB").save(out, optimize=True)
    U.report([("hud label on ink 66% over dark scene", U.TEXT_D, U.over(U.INK, (40, 50, 60), 0.66)),
              ("hud label on ink 66% over bright sky", U.TEXT_D, U.over(U.INK, (200, 205, 215), 0.66)),
              ("Gather label on amber", U.INK, U.AMBER), ("muted tick on ink", U.MUTED_D, U.over(U.INK, (200, 205, 215), 0.62))])


# ---------------------------------------------------------------- dialogue
def talk(raw, out, name="Ivar", role="Net mender, Skarvik", line="Blue moss? Try the northern ravine after rain. Old Marta buys it too."):
    im = grade(load(raw))
    g = U.vgrad((W, 340), (0, 0, 0, 0), (10, 13, 17, 215))
    im.alpha_composite(g, (0, H - 340))
    d = ImageDraw.Draw(im)
    x0 = 300
    yb = H - 210
    U.waveform(d, x0, yb - 2, 52, 30, U.AMBER, bars=9)
    fn = U.font(30, 700)
    d.text((x0 + 70, yb + 13), name, font=fn, fill=U.AMBER, anchor="lm")
    d.text((x0 + 70 + U.tw(name, fn) + 18, yb + 15), role, font=U.font(22, 500), fill=U.MUTED_D, anchor="lm")
    fl = U.font(40, 500)
    d.text((x0, yb + 50), line, font=fl, fill=U.TEXT_D, anchor="la")
    # replies (48 dp tall pills) on the right, above the subtitle
    opts = [("1", "Where is the northern ravine?"), ("2", "Who is Old Marta?"), ("3", "Trade")]
    fo = U.font(24, 600)
    yy = H - 470
    for k, s in opts:
        tw = U.tw(s, fo)
        bx1 = W - M
        bx0 = bx1 - tw - 110
        U.panel(im, (bx0, yy, bx1, yy + 74), radius=37, fill=U.INK, alpha=0.8, drop=False)
        d = ImageDraw.Draw(im)
        U.disc(d, (bx0 + 38, yy + 37), 19, None, ring=U.MUTED_D, ring_w=2)
        d.text((bx0 + 38, yy + 38), k, font=U.font(18, 700), fill=U.MUTED_D, anchor="mm")
        d.text((bx0 + 72, yy + 37), s, font=fo, fill=U.TEXT_D, anchor="lm")
        yy += 90
    # relationship chip under the name area (top-left of subtitle)
    rel = "Knows you  ·  Helped with nets"
    fr = U.font(18, 600)
    U.panel(im, (x0, yb - 52, x0 + U.tw(rel, fr) + 28, yb - 18), radius=17, fill=U.INK, alpha=0.7, drop=False)
    d = ImageDraw.Draw(im)
    d.text((x0 + 14, yb - 35), rel, font=fr, fill=U.TEAL, anchor="lm")
    im.convert("RGB").save(out, optimize=True)
    U.report([("subtitle line on gradient (darkest)", U.TEXT_D, (14, 17, 22)), ("speaker name amber on gradient", U.AMBER, (20, 24, 30)),
              ("role muted on gradient", U.MUTED_D, (20, 24, 30)), ("relationship teal on ink 70%", U.TEAL, U.over(U.INK, (60, 70, 80), 0.7)),
              ("reply text on ink 80%", U.TEXT_D, U.over(U.INK, (120, 120, 120), 0.8))])


# ---------------------------------------------------------------- trade
ITEMS = [
    # name, icon, origin tag (kind, text), price, delta %, stock/qty, weight
    ("Olive oil, amphora", "ceramic_vase_01", ("import", "Import · Lantia isles"), 46, +12, 8, 6.0),
    ("Salt cod, barrel", "Barrel_01", ("import", "Import · Skarvik fjord"), 88, -6, 3, 22.0),
    ("Pomegranates", "food_pomegranate_01", ("local", "Local · oasis gardens"), 4, -18, 40, 0.3),
    ("Lemons", "lemon", ("import", "Import · Lantia isles"), 3, +4, 55, 0.2),
    ("Copper pot", "brass_pot_01", ("local", "Local · Qasr smiths"), 31, 0, 6, 2.5),
    ("Dates, basket", "wicker_basket_01", ("export", "Export · sells well north"), 12, +22, 14, 4.0),
]


def trade(raw, out, icons):
    bg = load(raw)
    bg = bg.filter(ImageFilter.GaussianBlur(10))
    im = Image.alpha_composite(bg, Image.new("RGBA", (W, H), (0, 0, 0, 90)))
    d = ImageDraw.Draw(im)
    px0, py0, px1, py1 = 150, 70, W - 150, H - 70
    U.panel(im, (px0, py0, px1, py1), radius=28, fill=U.PAPER, alpha=0.97)
    d = ImageDraw.Draw(im)
    # header
    d.text((px0 + 48, py0 + 42), "Qasr Oasis market", font=U.font(40, 700, serif=True), fill=U.TEXT_L, anchor="lm")
    d.text((px0 + 50, py0 + 86), "Trader Samir  ·  Caravan from the north arrived 2 days ago", font=U.font(22, 500), fill=U.MUTED_L, anchor="lm")
    # coins + cart
    cx = px1 - 48
    U.ic_coin(d, (cx - 330, py0 + 50), 17)
    d.text((cx - 304, py0 + 51), "1,240", font=U.font(32, 700), fill=U.TEXT_L, anchor="lm")
    d.text((cx - 304, py0 + 86), "coins", font=U.font(18, 500), fill=U.MUTED_L, anchor="lm")
    U.ic_pack(d, (cx - 150, py0 + 50), 16, U.TEXT_L)
    d.text((cx - 125, py0 + 51), "21.8 / 30 kg", font=U.font(26, 700), fill=U.TEXT_L, anchor="lm")
    d.rounded_rectangle((cx - 125, py0 + 76, cx, py0 + 84), 4, fill=U.PAPER2)
    d.rounded_rectangle((cx - 125, py0 + 76, cx - 125 + int(125 * 21.8 / 30), py0 + 84), 4, fill=U.TEAL_D)
    # tabs
    ty = py0 + 132
    tabs = [("Buy", True), ("Sell", False), ("Orders", False)]
    tx = px0 + 48
    for s, on in tabs:
        f = U.font(26, 700 if on else 600)
        tw = U.tw(s, f)
        if on:
            d.rounded_rectangle((tx - 22, ty - 4, tx + tw + 22, ty + 54), 27, fill=U.TEXT_L)
        d.text((tx, ty + 25), s, font=f, fill=U.PAPER if on else U.MUTED_L, anchor="lm")
        tx += tw + 70
    # column heads
    hy = ty + 92
    cols = dict(icon=px0 + 48, name=px0 + 160, origin=px0 + 640, price=px0 + 1060, trend=px0 + 1200, stock=px0 + 1340, qty=px0 + 1450)
    fh = U.font(18, 700)
    for k, lab in (("name", "ITEM"), ("origin", "ORIGIN"), ("price", "PRICE"), ("trend", "7-DAY"), ("stock", "STOCK"), ("qty", "CART")):
        d.text((cols[k], hy), lab, font=fh, fill=U.MUTED_L, anchor="lm")
    ry = hy + 30
    rh = 92
    for i, (nm, ic, (kind, otxt), price, delta, stock, wt) in enumerate(ITEMS):
        y = ry + i * rh
        if i % 2 == 0:
            d.rounded_rectangle((px0 + 28, y, px1 - 28, y + rh - 6), 16, fill=U.PAPER2)
        icp = Path(icons) / f"{ic}.png"
        if icp.exists():
            ico = Image.open(icp).convert("RGBA").resize((76, 76), Image.LANCZOS)
            im.alpha_composite(ico, (cols["icon"], y + 5))
        d.text((cols["name"], y + 30), nm, font=U.font(26, 600), fill=U.TEXT_L, anchor="lm")
        d.text((cols["name"], y + 62), f"{wt:g} kg each", font=U.font(19, 500), fill=U.MUTED_L, anchor="lm")
        tagc = {"import": U.TEAL_D, "export": U.AMBER_D, "local": U.MUTED_L}[kind]
        ft = U.font(20, 600)
        tw = U.tw(otxt, ft)
        d.rounded_rectangle((cols["origin"], y + 25, cols["origin"] + tw + 28, y + 63), 19, outline=tagc, width=2)
        d.text((cols["origin"] + 14, y + 44), otxt, font=ft, fill=tagc, anchor="lm")
        U.ic_coin(d, (cols["price"] - 18, y + 43), 11)
        d.text((cols["price"], y + 44), f"{price}", font=U.font(28, 700), fill=U.TEXT_L, anchor="lm")
        if delta > 0:
            U.arrow(d, (cols["trend"], y + 44), 9, True, U.TEAL_D)
            d.text((cols["trend"] + 16, y + 44), f"+{delta}%", font=U.font(22, 700), fill=U.TEAL_D, anchor="lm")
        elif delta < 0:
            U.arrow(d, (cols["trend"], y + 44), 9, False, U.CLAY_D)
            d.text((cols["trend"] + 16, y + 44), f"{delta}%", font=U.font(22, 700), fill=U.CLAY_D, anchor="lm")
        else:
            d.text((cols["trend"] - 6, y + 44), "–  0%", font=U.font(22, 700), fill=U.MUTED_L, anchor="lm")
        d.text((cols["stock"], y + 44), f"{stock}", font=U.font(24, 600), fill=U.TEXT_L, anchor="lm")
        q = [0, 1, 4, 0, 0, 2][i]
        sx = cols["qty"]
        for j, (s, xx) in enumerate((("−", sx), ("+", sx + 150))):
            d.ellipse((xx, y + 17, xx + 54, y + 71), outline=U.TEXT_L if j or q else (190, 182, 170), width=2)
            d.text((xx + 27, y + 43), s, font=U.font(30, 600), fill=U.TEXT_L if j or q else (170, 162, 150), anchor="mm")
        d.text((sx + 102, y + 44), str(q), font=U.font(28, 700), fill=U.TEXT_L, anchor="mm")
    # footer
    fy = py1 - 96
    d.line((px0 + 28, fy - 18, px1 - 28, fy - 18), fill=U.PAPER2, width=2)
    d.text((px0 + 48, fy + 30), "Cart  7 items  ·  6.8 kg  ·  ", font=U.font(26, 600), fill=U.TEXT_L, anchor="lm")
    U.ic_coin(d, (px0 + 412, fy + 30), 13)
    d.text((px0 + 432, fy + 31), "41", font=U.font(28, 700), fill=U.TEXT_L, anchor="lm")
    d.text((px0 + 490, fy + 31), "Lemons are cheaper on the isles. Dates sell high in the north.", font=U.font(21, 500, serif=True, italic=True), fill=U.MUTED_L, anchor="lm")
    bw = 260
    d.rounded_rectangle((px1 - 48 - bw, fy - 2, px1 - 48, fy + 64), 33, fill=U.TEAL_D)
    d.text((px1 - 48 - bw / 2, fy + 31), "Buy for 41", font=U.font(28, 700), fill=U.WHITE, anchor="mm")
    d.rounded_rectangle((px1 - 48 - bw - 200, fy - 2, px1 - 48 - bw - 24, fy + 64), 33, outline=U.TEXT_L, width=2)
    d.text((px1 - 48 - bw - 112, fy + 31), "Close", font=U.font(26, 600), fill=U.TEXT_L, anchor="mm")
    im.convert("RGB").save(out, optimize=True)
    U.report([("ledger text on paper", U.TEXT_L, U.PAPER), ("ledger text on stripe", U.TEXT_L, U.PAPER2), ("muted on paper", U.MUTED_L, U.PAPER),
              ("muted on stripe", U.MUTED_L, U.PAPER2), ("price up teal_d on stripe", U.TEAL_D, U.PAPER2), ("price down clay_d on stripe", U.CLAY_D, U.PAPER2),
              ("export amber_d on paper", U.AMBER_D, U.PAPER), ("white on teal_d button", U.WHITE, U.TEAL_D)])


# ---------------------------------------------------------------- wonder card
def wonder(raw, photo, out):
    bg = load(raw).filter(ImageFilter.GaussianBlur(8))
    im = Image.alpha_composite(bg, Image.new("RGBA", (W, H), (8, 10, 12, 120)))
    cw, chh = 1180, 820
    x0, y0 = (W - cw) // 2, (H - chh) // 2
    U.panel(im, (x0, y0, x0 + cw, y0 + chh), radius=26, fill=U.PAPER, alpha=0.98)
    d = ImageDraw.Draw(im)
    # photo frame
    pw, ph = 600, 400
    ph_im = Image.open(photo).convert("RGB")
    r = max(pw / ph_im.width, ph / ph_im.height)
    ph_im = ph_im.resize((int(ph_im.width * r), int(ph_im.height * r)), Image.LANCZOS)
    ox = (ph_im.width - pw) // 2
    oy = (ph_im.height - ph) // 2
    ph_im = ph_im.crop((ox, oy, ox + pw, oy + ph))
    fx, fy = x0 + 56, y0 + 150
    d.rectangle((fx - 14, fy - 14, fx + pw + 14, fy + ph + 52), fill=(252, 250, 245))
    U.shadow(im, (fx - 14, fy - 14, fx + pw + 14, fy + ph + 52), 4, blur=10, alpha=70, off=(0, 4))
    d = ImageDraw.Draw(im)
    d.rectangle((fx - 14, fy - 14, fx + pw + 14, fy + ph + 52), fill=(252, 250, 245))
    im.paste(ph_im, (fx, fy))
    d.text((fx + 2, fy + ph + 26), "Sketched from Cape Lantia, day 14", font=U.font(19, 500, serif=True, italic=True), fill=U.MUTED_L, anchor="lm")
    # header
    U.ic_diamond(d, (x0 + 72, y0 + 74), 20, U.AMBER, ring=U.AMBER_D)
    U.ic_star(d, (x0 + 72, y0 + 74), 9, U.TEXT_L)
    d.text((x0 + 110, y0 + 56), "WONDER DISCOVERED", font=U.font(20, 700), fill=U.AMBER_D, anchor="lm")
    d.text((x0 + 110, y0 + 96), "The Drowned Colonnade", font=U.font(46, 700, serif=True), fill=U.TEXT_L, anchor="lm")
    d.text((x0 + cw - 56, y0 + 62), "Wonder 3 of 24", font=U.font(20, 600), fill=U.MUTED_L, anchor="rm")
    # journal text
    jx = fx + pw + 56
    jy = fy - 6
    fj = U.font(27, 450, serif=True, italic=True)
    lines = [
        "The fishermen were right. Forty",
        "columns once held a roof over",
        "the headland, and the sea took",
        "half of them. A stone face the",
        "size of a house watches the bay",
        "from the shallows.",
        "",
        "Nobody in Lantia agrees on who",
        "built it. The tide pools below",
        "glitter with blue shells.",
    ]
    for i, s in enumerate(lines):
        d.text((jx, jy + i * 40), s, font=fj, fill=U.TEXT_L, anchor="la")
    # rewards line
    ry = y0 + chh - 150
    d.line((x0 + 56, ry - 20, x0 + cw - 56, ry - 20), fill=U.PAPER2, width=2)
    d.text((x0 + 56, ry + 6), "REWARDS", font=U.font(18, 700), fill=U.MUTED_L, anchor="lm")
    rw = [("Explorer reputation +120", U.TEAL_D), ("New rumour: the Glass Forest", U.AMBER_D), ("Map: Cape Lantia charted", U.TEXT_L)]
    rx = x0 + 56
    for s, c in rw:
        f = U.font(23, 600)
        tw = U.tw(s, f)
        d.rounded_rectangle((rx, ry + 30, rx + tw + 32, ry + 76), 23, outline=c, width=2)
        d.text((rx + 16, ry + 53), s, font=f, fill=c, anchor="lm")
        rx += tw + 52
    bw = 220
    d.rounded_rectangle((x0 + cw - 56 - bw, ry + 22, x0 + cw - 56, ry + 84), 31, fill=U.TEXT_L)
    d.text((x0 + cw - 56 - bw / 2, ry + 53), "Continue", font=U.font(26, 700), fill=U.PAPER, anchor="mm")
    im.convert("RGB").save(out, optimize=True)
    U.report([("journal text on paper", U.TEXT_L, U.PAPER), ("WONDER label amber_d on paper", U.AMBER_D, U.PAPER), ("rewards teal_d on paper", U.TEAL_D, U.PAPER),
              ("caption muted on photo mat", U.MUTED_L, (252, 250, 245)), ("Continue paper on ink", U.PAPER, U.TEXT_L)])


# ---------------------------------------------------------------- build mode
def build(raw, out):
    im = grade(load(raw), vignette=0.15)
    d = ImageDraw.Draw(im)
    # mode banner top-left
    U.panel(im, (M, M, M + 470, M + 96), radius=22, fill=U.INK, alpha=0.8, drop=False)
    d = ImageDraw.Draw(im)
    d.text((M + 28, M + 32), "BUILD", font=U.font(18, 700), fill=U.TEAL, anchor="lm")
    d.text((M + 28, M + 66), "Timber house, frame stage", font=U.font(27, 700), fill=U.TEXT_D, anchor="lm")
    d.text((M + 30, M + 128), "Flat ground  ·  2 m from the path  ·  Snap on", font=U.font(21, 500), fill=U.TEXT_D, anchor="lm")
    # material cost chips bottom center
    mats = [("Logs", 12, 12), ("Planks", 30, 40), ("Turf", 8, 8), ("Stone", 6, 10)]
    f = U.font(24, 600)
    widths = [U.tw(f"{n}  {have} / {need}", f) + 70 for n, have, need in mats]
    tot = sum(widths) + 16 * (len(mats) - 1)
    x = (W - tot) // 2
    y = H - M - 70
    for (n, have, need), w in zip(mats, widths):
        ok = have >= need
        U.panel(im, (x, y, x + w, y + 64), radius=32, fill=U.INK, alpha=0.82, outline=U.TEAL if ok else U.CLAY, ow=3, drop=False)
        d = ImageDraw.Draw(im)
        if ok:
            U.ic_check(d, (x + 30, y + 32), 22, U.TEAL, w=5)
        else:
            U.ic_cross(d, (x + 30, y + 32), 22, U.CLAY, w=5)
        d.text((x + 54, y + 33), f"{n}  {have} / {need}", font=f, fill=U.TEXT_D, anchor="lm")
        x += w + 16
    # right-side controls: rotate L / R, confirm, cancel (all >= 48 dp)
    cx = W - M - 90
    cy = H // 2 + 40
    for i, (fn, label) in enumerate(((lambda dd, c: U.ic_rotate(dd, c, 26, U.TEXT_D, w=6, flip=True), "Rotate"), (lambda dd, c: U.ic_rotate(dd, c, 26, U.TEXT_D, w=6), ""))):
        c = (cx - 150 + i * 150, cy - 170)
        U.panel(im, (c[0] - 64, c[1] - 64, c[0] + 64, c[1] + 64), radius=64, fill=U.INK, alpha=0.78, drop=False)
        d = ImageDraw.Draw(im)
        fn(d, c)
    cc = (cx, cy + 40)
    U.shadow(im, (cc[0] - 80, cc[1] - 80, cc[0] + 80, cc[1] + 80), 80, blur=14, alpha=80)
    d = ImageDraw.Draw(im)
    U.disc(d, cc, 80, U.TEAL, ring=U.WHITE, ring_w=4)
    U.ic_check(d, cc, 44, U.WHITE, w=10)
    cx2 = (cx - 190, cy + 70)
    U.panel(im, (cx2[0] - 64, cx2[1] - 64, cx2[0] + 64, cx2[1] + 64), radius=64, fill=U.INK, alpha=0.78, drop=False)
    d = ImageDraw.Draw(im)
    U.ic_cross(d, cx2, 34, U.TEXT_D, w=7)
    d.text((cc[0], cc[1] + 112), "Place frame", font=U.font(22, 700), fill=U.TEXT_D, anchor="mm")
    # missing material hint
    hint = "Need 10 more planks and 4 stone to finish walls"
    fh = U.font(21, 500)
    tw = U.tw(hint, fh)
    U.panel(im, ((W - tw) // 2 - 22, H - M - 130, (W + tw) // 2 + 22, H - M - 86), radius=22, fill=U.INK, alpha=0.7, drop=False)
    d = ImageDraw.Draw(im)
    d.text((W // 2, H - M - 108), hint, font=fh, fill=U.TEXT_D, anchor="mm")
    im.convert("RGB").save(out, optimize=True)
    U.report([("chip text on ink 82%", U.TEXT_D, U.over(U.INK, (120, 130, 110), 0.82)), ("teal check on ink", U.TEAL, U.INK), ("clay cross on ink", U.CLAY, U.INK),
              ("white check on teal", U.WHITE, U.TEAL), ("BUILD label teal on ink 80%", U.TEAL, U.over(U.INK, (120, 130, 110), 0.8))])


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "hud":
        hud(sys.argv[2], sys.argv[3])
    elif mode == "talk":
        talk(sys.argv[2], sys.argv[3])
    elif mode == "trade":
        trade(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "wonder":
        wonder(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "build":
        build(sys.argv[2], sys.argv[3])
    elif mode == "grade":
        grade(load(sys.argv[2])).convert("RGB").save(sys.argv[3], optimize=True)
