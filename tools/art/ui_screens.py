#!/usr/bin/env python3
"""Draw the Wayfarer UI mockups over the Blender renders (Pillow). Prints contrast numbers (my calc).

python3 tools/art/ui_screens.py hud   <raw.png> <out.png>
python3 tools/art/ui_screens.py talk   <raw.png> <out.jpg>   (fjord: Ingrid, GDD 6.4)
python3 tools/art/ui_screens.py trade  <raw.png> <out.jpg>   (Skarvik market, Sell tab; icons = Poly Haven CC0 thumbs)
python3 tools/art/ui_screens.py wonder <raw.png> <out.jpg>   (Singing Cavern; vista built from the same frame)
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
            d.text(
                (x, y0 + ch / 2),
                ["NE", "SE", "SW", "NW"][deg // 90],
                font=f_small,
                fill=U.MUTED_D,
                anchor="mm",
            )
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
        U.panel(
            im,
            (x - tw / 2 - 10, yy - 13, x + tw / 2 + 10, yy + 15),
            radius=14,
            fill=U.INK,
            alpha=0.62,
            drop=False,
        )
        d = ImageDraw.Draw(im)
        d.text(
            (x, yy + 1), label, font=f, fill=U.AMBER if kind == "wonder" else U.TEXT_D, anchor="mm"
        )
    # heading caret
    d.polygon([(W / 2 - 8, y0 - 2), (W / 2 + 8, y0 - 2), (W / 2, y0 + 8)], fill=U.TEXT_D)
    return im


def chip(im, x, y, w, h, draw_fn):
    U.panel(im, (x, y, x + w, y + h), radius=h // 2, fill=U.INK, alpha=0.66, drop=False)
    d = ImageDraw.Draw(im)
    draw_fn(d)


def hud(raw, out):
    im = grade(load(raw))
    im = compass(
        im,
        heading=352,
        markers=[
            ("wonder", 318, "Bluewater Falls  1.2 km"),
            ("rumor", 15, "Blue moss?"),
            ("trade", 40, "Skarvik dock"),
        ],
    )
    d = ImageDraw.Draw(im)
    # top-left: menu disc (48 dp min) + map disc
    for i, fn in enumerate(
        (
            lambda dd, c: U.ic_gear(dd, c, 26, U.TEXT_D, U.INK),
            lambda dd, c: U.ic_map(dd, c, 22, U.TEXT_D),
        )
    ):
        c = (M + 63 + i * 140, M + 63)
        U.panel(
            im,
            (c[0] - 63, c[1] - 63, c[0] + 63, c[1] + 63),
            radius=63,
            fill=U.INK,
            alpha=0.62,
            drop=False,
        )
        d = ImageDraw.Draw(im)
        fn(d, c)
    # top-right: time/weather + pack weight
    f = U.font(24, 600)
    x1 = W - M
    chip(
        im,
        x1 - 300,
        M + 6,
        300,
        54,
        lambda dd: (
            U.ic_moon(dd, (x1 - 270, M + 33), 13, U.TEXT_D, U.over(U.INK, (40, 50, 60), 0.66)),
            dd.text((x1 - 245, M + 33), "21:40  Clear  4°C", font=f, fill=U.TEXT_D, anchor="lm"),
        ),
    )

    def pack(dd):
        U.ic_pack(dd, (x1 - 270, M + 103), 14, U.TEXT_D)
        dd.text((x1 - 245, M + 104), "18.4 / 30 kg", font=f, fill=U.TEXT_D, anchor="lm")
        dd.rounded_rectangle((x1 - 245, M + 124, x1 - 40, M + 130), 3, fill=(255, 255, 255, 60))
        dd.rounded_rectangle(
            (x1 - 245, M + 124, x1 - 245 + int(205 * 18.4 / 30), M + 130), 3, fill=U.TEAL
        )

    chip(im, x1 - 300, M + 72, 300, 64, pack)
    # left move stick (thumb zone), bottom-left
    c = (M + 190, H - M - 190)
    L = U.layer((W, H))
    dl = ImageDraw.Draw(L)
    dl.ellipse(
        (c[0] - 150, c[1] - 150, c[0] + 150, c[1] + 150),
        fill=(17, 21, 26, 70),
        outline=(246, 243, 236, 120),
        width=3,
    )
    dl.ellipse(
        (c[0] - 52 + 20, c[1] - 52 - 34, c[0] + 52 + 20, c[1] + 52 - 34), fill=(246, 243, 236, 205)
    )
    im.alpha_composite(L)
    # right: action button (Gather) + jump
    ca = (W - M - 120, H - M - 150)
    U.shadow(im, (ca[0] - 84, ca[1] - 84, ca[0] + 84, ca[1] + 84), 84, blur=16, alpha=80)
    d = ImageDraw.Draw(im)
    U.disc(d, ca, 84, U.AMBER, ring=U.WHITE, ring_w=4)
    U.ic_leaf(d, (ca[0], ca[1] - 10), 40, U.INK)
    d.text((ca[0], ca[1] + 46), "Gather", font=U.font(22, 700), fill=U.INK, anchor="mm")
    cj = (ca[0] - 200, ca[1] + 70)
    U.panel(
        im,
        (cj[0] - 64, cj[1] - 64, cj[0] + 64, cj[1] + 64),
        radius=64,
        fill=U.INK,
        alpha=0.66,
        drop=False,
    )
    d = ImageDraw.Draw(im)
    U.ic_jump(d, cj, 30, U.TEXT_D)
    cc = (ca[0] - 170, ca[1] - 150)
    U.panel(
        im,
        (cc[0] - 64, cc[1] - 64, cc[0] + 64, cc[1] + 64),
        radius=64,
        fill=U.INK,
        alpha=0.66,
        drop=False,
    )
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
    U.panel(
        im,
        (gx - tw / 2 - 18, gy - 92, gx + tw / 2 + 18, gy - 48),
        radius=22,
        fill=U.INK,
        alpha=0.78,
        drop=False,
    )
    d = ImageDraw.Draw(im)
    d.text((gx, gy - 70), lab, font=f2, fill=U.TEXT_D, anchor="mm")
    im.convert("RGB").save(out, optimize=True)
    U.report(
        [
            ("hud label on ink 66% over dark scene", U.TEXT_D, U.over(U.INK, (40, 50, 60), 0.66)),
            (
                "hud label on ink 66% over bright sky",
                U.TEXT_D,
                U.over(U.INK, (200, 205, 215), 0.66),
            ),
            ("Gather label on amber", U.INK, U.AMBER),
            ("muted tick on ink", U.MUTED_D, U.over(U.INK, (200, 205, 215), 0.62)),
        ]
    )


# ---------------------------------------------------------------- shared for the 10-10 fjord screens
THUMBS = U.ROOT / "assets" / "_raw" / "polyhaven" / "thumbs"
ROCK = (
    U.ROOT
    / "assets"
    / "_raw"
    / "polyhaven"
    / "textures"
    / "rock_face_03"
    / "rock_face_03_diffuse_1k.jpg"
)


def world(raw, blur=0, dim=0.0):
    im = grade(load(raw))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if dim:
        im = Image.alpha_composite(im, Image.new("RGBA", (W, H), (8, 10, 13, int(255 * dim))))
    return im


def round_btn(im, c, r, fill, alpha=0.86, ring=None):
    U.panel(
        im,
        (c[0] - r, c[1] - r, c[0] + r, c[1] + r),
        radius=r,
        fill=fill,
        alpha=alpha,
        outline=ring,
        ow=3,
        drop=False,
    )
    return ImageDraw.Draw(im)


def pill(d, box, fill=None, outline=None, w=3):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, (y1 - y0) // 2, fill=fill, outline=outline, width=w)


def coin_text(d, x, y, s, f, col, anchor="lm", r=None):
    """Coin glyph + number; anchor l = starts at x, r = ends at x."""
    r = r or int(f.size * 0.36)
    wtxt = U.tw(s, f)
    total = 2 * r + 12 + wtxt
    x0 = x if anchor[0] == "l" else x - total
    U.ic_coin(d, (x0 + r, y + 2), r)
    d.text((x0 + 2 * r + 12, y), s, font=f, fill=col, anchor="lm")
    return total


# ---------------------------------------------------------------- talk (NPC dialogue)
def talk(raw, out):
    im = world(raw)
    # bottom scrim so the subtitle panel never sits on bright meadow
    im.alpha_composite(U.vgrad((W, 460), (0, 0, 0, 0), (8, 10, 13, 150)), (0, H - 460))
    d = ImageDraw.Draw(im)
    # camera framing guide: where the NPC stands in the real shot; skipped when the raw frame already shows the NPC
    npc_in_frame = "talk" in Path(raw).name
    gx0, gy0, gx1, gy1 = 560, 150, 1000, 640
    L = U.layer((W, H))
    dl = ImageDraw.Draw(L)
    for x, y, sx, sy in (
        ()
        if npc_in_frame
        else ((gx0, gy0, 1, 1), (gx1, gy0, -1, 1), (gx0, gy1, 1, -1), (gx1, gy1, -1, -1))
    ):
        dl.line((x, y, x + 46 * sx, y), fill=(246, 243, 236, 170), width=4)
        dl.line((x, y, x, y + 46 * sy), fill=(246, 243, 236, 170), width=4)
    im.alpha_composite(L)
    d = ImageDraw.Draw(im)
    # placeholder note: honest about the missing character render, sized to the frame
    nx, ny = (gx0 + gx1) // 2, (gy0 + gy1) // 2
    f1, f2 = U.font(U.T_LABEL, 700), U.font(U.T_CAPTION, 500)
    nw = max(U.tw("Ingrid stands here", f1), U.tw("character not rendered yet", f2))
    if npc_in_frame:
        nw = None
    if nw is not None:
        U.panel(
            im,
            (nx - nw // 2 - 26, ny - 56, nx + nw // 2 + 26, ny + 56),
            radius=28,
            fill=U.INK,
            alpha=0.78,
            drop=False,
        )
    d = ImageDraw.Draw(im)
    if nw is not None:
        d.text((nx, ny - 20), "Ingrid stands here", font=f1, fill=U.TEXT_D, anchor="mm")
        d.text((nx, ny + 24), "character not rendered yet", font=f2, fill=U.MUTED_D, anchor="mm")

    # subtitle panel, bottom-left (left thumb rests below it, reading line stays mid-screen)
    px0, py0, px1, py1 = M, 700, 1130, H - M
    U.panel(im, (px0, py0, px1, py1), radius=28, fill=U.INK, alpha=0.88)
    d = ImageDraw.Draw(im)
    fn = U.font(U.T_TITLE, 700)
    d.text((px0 + 40, py0 + 56), "Ingrid", font=fn, fill=U.AMBER, anchor="lm")
    nx2 = px0 + 40 + U.tw("Ingrid", fn) + 22
    d.text(
        (nx2, py0 + 60), "Fisher, Skarvik", font=U.font(U.T_LABEL, 500), fill=U.MUTED_D, anchor="lm"
    )
    # relationship band chip, right side of the name row
    band = "Trusted"
    fb = U.font(U.T_CAPTION, 700)
    bw = U.tw(band, fb) + 44
    pill(d, (px1 - 40 - bw, py0 + 32, px1 - 40, py0 + 82), outline=U.TEAL_L, w=3)
    d.text((px1 - 40 - bw / 2, py0 + 57), band, font=fb, fill=U.TEAL_L, anchor="mm")
    # the spoken line (pre-voiced; GDD 6.4 Trusted + river flood)
    U.waveform(d, px0 + 40, py0 + 112, 44, 34, U.AMBER, bars=7)
    line = (
        "River's brown as tea. No fish today. If you've any smoked put by, the stall will pay well."
    )
    fl = U.font(U.T_BODY + 2, 500)
    for i, s in enumerate(U.wrap(line, fl, px1 - px0 - 150)):
        d.text((px0 + 110, py0 + 130 + i * 56), s, font=fl, fill=U.TEXT_D, anchor="lm")
    # memory + live fact the line is built from (players see why she says it)
    d.line(
        (px0 + 40, py1 - 92, px1 - 40, py1 - 92), fill=U.over((255, 255, 255), U.INK, 0.16), width=2
    )
    fm = U.font(U.T_CAPTION, 500)
    d.text(
        (px0 + 40, py1 - 44),
        "She remembers: you paid fair for her herring, day 3",
        font=fm,
        fill=U.MUTED_D,
        anchor="lm",
    )

    # replies, right thumb column (130 px tall each, 18 px gaps)
    opts = [
        ("I have smoked fish to sell", "trade"),
        ("How high is the river?", "ask"),
        ("Heard anything about the falls?", "rumor"),
        ("Goodbye", "bye"),
    ]
    fo = U.font(U.T_BODY - 2, 600)
    bx0, bx1 = 1190, W - M
    yy = H - M - len(opts) * U.HIT - (len(opts) - 1) * 18
    for s, kind in opts:
        box = (bx0, yy, bx1, yy + U.HIT)
        if kind == "trade":
            U.shadow(im, box, U.HIT // 2, blur=12, alpha=70)
            d = ImageDraw.Draw(im)
            pill(d, box, fill=U.TEAL_D)
            U.ic_coin(d, (bx0 + 62, yy + U.HIT // 2), 20)
            d.text((bx0 + 104, yy + U.HIT // 2), s, font=fo, fill=U.WHITE, anchor="lm")
        else:
            U.panel(im, box, radius=U.HIT // 2, fill=U.INK, alpha=0.88, drop=False)
            d = ImageDraw.Draw(im)
            if kind == "rumor":
                U.ic_bubble(d, (bx0 + 62, yy + U.HIT // 2 - 2), 20, U.AMBER)
            elif kind == "ask":
                U.ic_bubble(d, (bx0 + 62, yy + U.HIT // 2 - 2), 20, U.TEXT_D)
            else:
                U.ic_cross(d, (bx0 + 62, yy + U.HIT // 2), 30, U.MUTED_D, w=5)
            d.text((bx0 + 104, yy + U.HIT // 2), s, font=fo, fill=U.TEXT_D, anchor="lm")
        yy += U.HIT + 18
    im.convert("RGB").save(out, quality=90, optimize=True)
    sky = (235, 238, 242)
    U.report(
        [
            ("NPC line on ink 88% over bright sky (worst)", U.TEXT_D, U.over(U.INK, sky, 0.88)),
            ("name amber on ink 88% over bright sky", U.AMBER, U.over(U.INK, sky, 0.88)),
            ("role/memory muted on ink 88% over bright sky", U.MUTED_D, U.over(U.INK, sky, 0.88)),
            ("Trusted teal_l on ink 88% over bright sky", U.TEAL_L, U.over(U.INK, sky, 0.88)),
            ("reply text on ink 88% over bright sky", U.TEXT_D, U.over(U.INK, sky, 0.88)),
            ("white on teal_d reply", U.WHITE, U.TEAL_D),
            ("placeholder note on ink 78% over bright sky", U.TEXT_D, U.over(U.INK, sky, 0.78)),
            ("placeholder muted on ink 78% over bright sky", U.MUTED_D, U.over(U.INK, sky, 0.78)),
        ]
    )


# ---------------------------------------------------------------- trade (Skarvik market, Sell tab)
SELL = [
    # name, thumb, have, kg each, price you get, change % vs base, live reason (sim fact). Weights sum to the 18.4 kg pack chip.
    (
        "Smoked fish",
        "wooden_crate_01",
        12,
        0.5,
        "8.7",
        +74,
        "River flood: no fresh fish for 2 days",
    ),
    ("Cloudberries", "wicker_basket_01", 18, 0.1, "9.4", +18, "Stall is low, 6 left"),
    ("Wild honey", "ceramic_pot", 2, 1.0, "12.6", 0, "Normal stock"),
    ("Bog iron ore", "boulder_01", 2, 3.0, "10.8", -10, "Smith is stocked till Friday"),
    ("Firewood bundle", "dead_tree_trunk", 1, 2.6, "3.7", -27, "Woodcutters brought in 80 logs"),
]


def trade(raw, out, icons=None):
    im = world(raw, blur=2, dim=0.18)
    # ledger (light paper, left 2/3)
    lx0, ly0, lx1, ly1 = M, M, 1236, H - M
    U.panel(im, (lx0, ly0, lx1, ly1), radius=28, fill=U.PAPER, alpha=0.98)
    d = ImageDraw.Draw(im)
    d.text(
        (lx0 + 48, ly0 + 66),
        "Skarvik market",
        font=U.font(U.T_DISPLAY - 8, 700, serif=True),
        fill=U.TEXT_L,
        anchor="lm",
    )
    d.text(
        (lx0 + 50, ly0 + 128),
        "Halvard's stall  ·  prices reset each morning",
        font=U.font(U.T_LABEL, 500),
        fill=U.MUTED_L,
        anchor="lm",
    )
    # Buy / Sell segmented control (130 px tall)
    sx1 = lx1 - 40
    sx0 = sx1 - 2 * 170
    sy0 = ly0 + 34
    pill(d, (sx0, sy0, sx1, sy0 + U.HIT), fill=U.PAPER2)
    pill(d, (sx0 + 170, sy0 + 8, sx1 - 8, sy0 + U.HIT - 8), fill=U.TEXT_L)
    d.text(
        (sx0 + 85, sy0 + U.HIT // 2), "Buy", font=U.font(U.T_BODY, 600), fill=U.MUTED_L, anchor="mm"
    )
    d.text(
        (sx0 + 255 - 4, sy0 + U.HIT // 2),
        "Sell",
        font=U.font(U.T_BODY, 700),
        fill=U.PAPER,
        anchor="mm",
    )
    # column heads
    hy = ly0 + 214
    c_icon, c_name, c_have, c_price = lx0 + 40, lx0 + 184, lx0 + 760, lx1 - 48
    U.caps(d, (c_name, hy), "Your goods", U.T_CAPTION - 4, U.MUTED_L, anchor="lm")
    U.caps(d, (c_have, hy), "You have", U.T_CAPTION - 4, U.MUTED_L, anchor="mm")
    U.caps(d, (c_price, hy), "You get each", U.T_CAPTION - 4, U.MUTED_L, anchor="rm")
    ry, rh = hy + 30, 146
    for i, (nm, th, have, kg, price, chg, why) in enumerate(SELL):
        y = ry + i * rh
        box = (lx0 + 22, y + 4, lx1 - 22, y + rh - 6)
        if i == 0:
            d.rounded_rectangle(box, 20, fill=(226, 238, 234), outline=U.TEAL_D, width=4)
        elif i % 2 == 0:
            d.rounded_rectangle(box, 20, fill=U.PAPER2)
        p = THUMBS / f"{th}.png"
        if p.exists():
            ic = U.fit_icon(p, (120, 104))
            im.alpha_composite(ic, (c_icon + (120 - ic.width) // 2, y + (rh - ic.height) // 2))
            d = ImageDraw.Draw(im)
        d.text((c_name, y + 52), nm, font=U.font(U.T_BODY, 600), fill=U.TEXT_L, anchor="lm")
        d.text((c_name, y + 102), why, font=U.font(U.T_CAPTION, 500), fill=U.MUTED_L, anchor="lm")
        d.text((c_have, y + 54), str(have), font=U.font(U.T_NUM, 700), fill=U.TEXT_L, anchor="mm")
        d.text(
            (c_have, y + 102),
            f"{have * kg:g} kg",
            font=U.font(U.T_CAPTION, 500),
            fill=U.MUTED_L,
            anchor="mm",
        )
        coin_text(d, c_price, y + 54, price, U.font(U.T_NUM, 700), U.TEXT_L, anchor="rm")
        fc = U.font(U.T_CAPTION, 700)
        if chg > 0:
            s, col, up = f"{chg}% high", U.TEAL_D, True
        elif chg < 0:
            s, col, up = f"{-chg}% low", U.CLAY_D, False
        else:
            s, col, up = "normal", U.MUTED_L, None
        wv = U.tw(s, fc)
        d.text((c_price, y + 102), s, font=fc, fill=col, anchor="rm")
        if up is not None:
            U.arrow(d, (c_price - wv - 18, y + 102), 9, up, col)

    # right column: wallet chip + close, world visible, then the action card
    rx0, rx1 = 1268, W - M
    U.panel(im, (rx0, M, rx1 - U.HIT - 20, M + 104), radius=52, fill=U.INK, alpha=0.84, drop=False)
    d = ImageDraw.Draw(im)
    coin_text(d, rx0 + 30, M + 52, "1,240", U.font(U.T_NUM - 4, 700), U.TEXT_D)
    U.ic_pack(d, (rx0 + 236, M + 50), 17, U.TEXT_D)
    d.text(
        (rx0 + 264, M + 52), "18.4 / 30 kg", font=U.font(U.T_LABEL, 600), fill=U.TEXT_D, anchor="lm"
    )
    d = round_btn(im, (rx1 - U.HIT // 2, M + U.HIT // 2), U.HIT // 2, U.INK, alpha=0.84)
    U.ic_cross(d, (rx1 - U.HIT // 2, M + U.HIT // 2), 40, U.TEXT_D, w=7)

    cy0 = 392
    U.panel(im, (rx0, cy0, rx1, H - M), radius=28, fill=U.PAPER, alpha=0.98)
    d = ImageDraw.Draw(im)
    ic = U.fit_icon(THUMBS / "wooden_crate_01.png", (150, 110))
    im.alpha_composite(ic, (rx0 + 32, cy0 + 34 + (110 - ic.height) // 2))
    d = ImageDraw.Draw(im)
    d.text(
        (rx0 + 204, cy0 + 70),
        "Smoked fish",
        font=U.font(U.T_TITLE, 700, serif=True),
        fill=U.TEXT_L,
        anchor="lm",
    )
    d.text(
        (rx0 + 206, cy0 + 122),
        "6 kg selected",
        font=U.font(U.T_CAPTION, 500),
        fill=U.MUTED_L,
        anchor="lm",
    )
    # why: the sim fact behind the price, in plain words
    fw = U.font(U.T_LABEL, 500)
    wl = U.wrap(
        "Sells high while the river floods. It drops when the boats go out.", fw, rx1 - rx0 - 72
    )
    for i, s in enumerate(wl):
        d.text((rx0 + 36, cy0 + 196 + i * 46), s, font=fw, fill=U.TEXT_L, anchor="lm")
    # quantity: minus, count, plus, All (each a 130 px target)
    assert len(wl) <= 2, "card note must stay at 2 lines"
    qy = H - M - 36 - 144 - 28 - U.HIT  # stepper sits on top of the Sell button
    r = U.HIT // 2
    cm = (rx0 + 36 + r, qy + r)
    cp = (rx0 + 36 + U.HIT + 116 + r, qy + r)
    for c, sign in ((cm, "−"), (cp, "+")):
        d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=U.TEXT_L, width=4)
        d.text((c[0], c[1] - 3), sign, font=U.font(64, 500), fill=U.TEXT_L, anchor="mm")
    d.text(((cm[0] + cp[0]) / 2, qy + r), "12", font=U.font(64, 700), fill=U.TEXT_L, anchor="mm")
    ab = (cp[0] + r + 24, qy, rx1 - 36, qy + U.HIT)
    pill(d, ab, outline=U.TEXT_L, w=4)
    d.text(
        ((ab[0] + ab[2]) / 2, qy + r), "All", font=U.font(U.T_BODY, 700), fill=U.TEXT_L, anchor="mm"
    )
    # primary action, bottom-right = thumb
    bb = (rx0 + 36, H - M - 36 - 144, rx1 - 36, H - M - 36)
    U.shadow(im, bb, 72, blur=12, alpha=60)
    d = ImageDraw.Draw(im)
    pill(d, bb, fill=U.TEAL_D)
    fbt = U.font(U.T_NUM, 700)
    lab = "Sell 12 for"
    wl_ = U.tw(lab, fbt) + 20 + 2 * 16 + 12 + U.tw("104", fbt)
    bx = (bb[0] + bb[2]) / 2 - wl_ / 2
    d.text((bx, (bb[1] + bb[3]) / 2), lab, font=fbt, fill=U.WHITE, anchor="lm")
    coin_text(d, bx + U.tw(lab, fbt) + 20, (bb[1] + bb[3]) / 2, "104", fbt, U.WHITE, r=16)
    im.convert("RGB").save(out, quality=90, optimize=True)
    sel = (226, 238, 234)
    U.report(
        [
            ("row text on paper", U.TEXT_L, U.PAPER),
            ("row text on stripe", U.TEXT_L, U.PAPER2),
            ("reason muted on paper", U.MUTED_L, U.PAPER),
            ("reason muted on stripe", U.MUTED_L, U.PAPER2),
            ("reason muted on selected row", U.MUTED_L, sel),
            ("over-normal teal_d on selected row", U.TEAL_D, sel),
            ("over-normal teal_d on paper", U.TEAL_D, U.PAPER),
            ("under-normal clay_d on stripe", U.CLAY_D, U.PAPER2),
            ("under-normal clay_d on paper", U.CLAY_D, U.PAPER),
            ("Sell paper on ink segment", U.PAPER, U.TEXT_L),
            ("Buy muted on stripe segment", U.MUTED_L, U.PAPER2),
            ("white on teal_d Sell button", U.WHITE, U.TEAL_D),
            (
                "wallet text on ink 84% over bright sky",
                U.TEXT_D,
                U.over(U.INK, (235, 238, 242), 0.84),
            ),
        ]
    )


# ---------------------------------------------------------------- wonder discovery card (Singing Cavern)
def cave_view(raw, size):
    """The vista from the cavern mouth: the real fjord frame seen through a rock opening, a thin veil of falling water at right."""
    import math
    import random

    import numpy as np

    pw, ph = size
    src = Image.open(raw).convert("RGB")
    sw, sh = src.size
    cw = int(sw * 0.86)
    chh = int(cw * ph / pw)
    ox, oy = int(sw * 0.06), max(0, int(sh * 0.02))
    view = src.crop((ox, oy, ox + cw, oy + chh)).resize(
        (pw, ph), Image.LANCZOS
    )  # crop at native res, no upscale blur
    view = ImageEnhance.Contrast(view).enhance(1.05)
    # opening mask: noisy arch, wider at the bottom
    rnd = random.Random(7)
    mask = Image.new("L", (pw, ph), 0)
    pts = []
    cx, cy = pw * 0.52, ph * 0.72
    for i in range(90):
        a = math.pi * (1 + i / 89)
        j = 1 + rnd.uniform(-0.035, 0.035) + 0.035 * math.sin(i * 0.55)
        pts.append((cx + math.cos(a) * pw * 0.45 * j, cy + math.sin(a) * ph * 0.64 * j))
    pts += [
        (pw * 0.975, ph * 0.84),
        (pw * 0.96, ph + 5),
        (pw * 0.04, ph + 5),
        (pw * 0.055, ph * 0.86),
    ]
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    m = np.asarray(mask, dtype=np.float32) / 255
    # rock: real scan texture, dark, cool, lit from the opening and darker deep inside
    rock = Image.open(ROCK).convert("RGB").resize((pw, pw), Image.LANCZOS).crop((0, 0, pw, ph))
    rock = np.asarray(ImageEnhance.Color(rock).enhance(0.55), dtype=np.float32)
    near = (
        np.asarray(mask.filter(ImageFilter.GaussianBlur(70)), dtype=np.float32) / 255
    )  # 1 near the opening
    lip = (
        np.asarray(
            mask.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(3)),
            dtype=np.float32,
        )
        / 255
        - m
    )
    lip = np.clip(lip, 0, 1)
    shade = 0.16 + 0.55 * near + 0.9 * lip
    rock = rock * shade[..., None]
    rock = rock * 0.88 + np.array([40, 52, 64], np.float32) * 0.12 * shade[..., None]
    # falling-water veil: thin vertical streaks in a soft band at the right of the opening
    v = np.asarray(view, dtype=np.float32)
    # streaks broken along their length (12 rows of noise, stretched), softened sideways, plus spray at the base
    streak = (
        Image.effect_noise((pw // 2, 14), 120)
        .resize((pw, ph), Image.BICUBIC)
        .filter(ImageFilter.GaussianBlur(1.2))
    )
    streak = np.clip((np.asarray(streak, dtype=np.float32) - 135) / 70, 0, 1)
    yy = np.linspace(0, 1, ph, dtype=np.float32)[:, None]
    streak = streak * (0.55 + 0.45 * yy) + 0.55 * np.clip((yy - 0.72) / 0.28, 0, 1) ** 1.5
    band = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(band).polygon([(pw * 0.82, 0), (pw, 0), (pw, ph), (pw * 0.76, ph)], fill=255)
    band = np.asarray(band.filter(ImageFilter.GaussianBlur(45)), dtype=np.float32) / 255
    va = np.clip(band * (0.10 + 0.45 * streak), 0, 0.8)
    v = v * (1 - va[..., None]) + np.array([232, 240, 245], np.float32) * va[..., None]
    out = v * m[..., None] + rock * (1 - m[..., None])
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def wonder(raw, out, photo=None):
    im = world(raw, blur=14, dim=0.5)
    x0, y0, x1, y1 = 120, 72, W - 120, H - 72
    U.panel(im, (x0, y0, x1, y1), radius=30, fill=U.PAPER, alpha=0.99)
    d = ImageDraw.Draw(im)
    # vista (journal illustration) left
    pw, ph = 860, 520
    fx, fy = x0 + 56, y0 + 56
    U.shadow(im, (fx - 12, fy - 12, fx + pw + 12, fy + ph + 12), 6, blur=10, alpha=70, off=(0, 4))
    d = ImageDraw.Draw(im)
    d.rectangle((fx - 12, fy - 12, fx + pw + 12, fy + ph + 12), fill=(252, 250, 245))
    im.paste(cave_view(raw, (pw, ph)), (fx, fy))
    d = ImageDraw.Draw(im)
    d.text(
        (fx, fy + ph + 44),
        "Looking out from behind Bluewater Falls, first light",
        font=U.font(U.T_CAPTION, 450, serif=True, italic=True),
        fill=U.MUTED_L,
        anchor="lm",
    )
    # title block right
    tx = fx + pw + 64
    U.ic_diamond(d, (tx + 20, y0 + 84), 20, U.AMBER, ring=U.AMBER_D)
    U.ic_star(d, (tx + 20, y0 + 84), 9, U.TEXT_L)
    U.caps(d, (tx + 58, y0 + 86), "Wonder found", U.T_CAPTION, U.AMBER_D, anchor="lm")
    d.text(
        (x1 - 56, y0 + 86), "1 of 30", font=U.font(U.T_CAPTION, 600), fill=U.MUTED_L, anchor="rm"
    )
    ft = U.font(U.T_DISPLAY + 4, 700, serif=True)
    d.text((tx, y0 + 166), "The Singing", font=ft, fill=U.TEXT_L, anchor="lm")
    d.text((tx, y0 + 240), "Cavern", font=ft, fill=U.TEXT_L, anchor="lm")
    d.text(
        (tx + 2, y0 + 304),
        "Skarvik Fjord",
        font=U.font(U.T_LABEL, 500),
        fill=U.MUTED_L,
        anchor="lm",
    )
    fj = U.font(U.T_BODY - 2, 450, serif=True, italic=True)
    lore = "Wind through the crystal pipes makes the rock hum at first light. Ingrid's grandmother was right."
    for i, s in enumerate(U.wrap(lore, fj, x1 - 56 - tx)):
        d.text((tx, y0 + 380 + i * 52), s, font=fj, fill=U.TEXT_L, anchor="lm")
    # rewards, full width under the vista
    ry = fy + ph + 96
    d.line((x0 + 56, ry, x1 - 56 - 380 - 40, ry), fill=U.PAPER2, width=3)
    U.caps(d, (x0 + 56, ry + 44), "What you get", U.T_CAPTION - 4, U.MUTED_L, anchor="lm")
    rows = [
        (
            lambda c: U.ic_diamond(d, c, 16, (176, 212, 226), ring=(70, 110, 130)),
            "Resonant crystal  x3",
            U.TEXT_L,
        ),
        (lambda c: U.ic_star(d, c, 18, U.AMBER_D), "Wayfinder reputation  +10", U.TEXT_L),
        (lambda c: U.ic_map(d, c, 16, U.TEXT_L), "Cairn: travel here any time", U.TEXT_L),
        (
            lambda c: U.ic_bubble(d, c, 17, U.AMBER_D, mark=U.PAPER),
            "Rumor: the old observatory",
            U.AMBER_D,
        ),
    ]
    fr = U.font(U.T_LABEL + 2, 600)
    cols = [x0 + 56, x0 + 56 + 560]
    for i, (fn, s, col) in enumerate(rows):
        cx = cols[i % 2]
        cy = ry + 104 + (i // 2) * 62
        fn((cx + 18, cy))
        d.text((cx + 52, cy + 1), s, font=fr, fill=col, anchor="lm")
    # Continue (primary, bottom-right thumb) + Journal (secondary)
    bw, bh = 380, 144
    bb = (x1 - 56 - bw, y1 - 56 - bh, x1 - 56, y1 - 56)
    U.shadow(im, bb, bh // 2, blur=12, alpha=60)
    d = ImageDraw.Draw(im)
    pill(d, bb, fill=U.TEXT_L)
    d.text(
        ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2),
        "Continue",
        font=U.font(U.T_NUM, 700),
        fill=U.PAPER,
        anchor="mm",
    )
    jb = (bb[0], bb[1] - 24 - U.HIT, bb[2], bb[1] - 24)
    pill(d, jb, outline=U.TEXT_L, w=4)
    d.text(
        ((jb[0] + jb[2]) / 2, (jb[1] + jb[3]) / 2),
        "Read in journal",
        font=U.font(U.T_BODY, 600),
        fill=U.TEXT_L,
        anchor="mm",
    )
    im.convert("RGB").save(out, quality=90, optimize=True)
    U.report(
        [
            ("lore/title text on paper", U.TEXT_L, U.PAPER),
            ("WONDER FOUND amber_d on paper", U.AMBER_D, U.PAPER),
            ("caption muted on paper", U.MUTED_L, U.PAPER),
            ("rumor reward amber_d on paper", U.AMBER_D, U.PAPER),
            ("Continue paper on ink", U.PAPER, U.TEXT_L),
        ]
    )


# ---------------------------------------------------------------- build mode
def build(raw, out):
    im = grade(load(raw), vignette=0.15)
    d = ImageDraw.Draw(im)
    # mode banner top-left
    U.panel(im, (M, M, M + 470, M + 96), radius=22, fill=U.INK, alpha=0.8, drop=False)
    d = ImageDraw.Draw(im)
    d.text((M + 28, M + 32), "BUILD", font=U.font(18, 700), fill=U.TEAL, anchor="lm")
    d.text(
        (M + 28, M + 66),
        "Timber house, frame stage",
        font=U.font(27, 700),
        fill=U.TEXT_D,
        anchor="lm",
    )
    d.text(
        (M + 30, M + 128),
        "Flat ground  ·  2 m from the path  ·  Snap on",
        font=U.font(21, 500),
        fill=U.TEXT_D,
        anchor="lm",
    )
    # material cost chips bottom center
    mats = [("Logs", 12, 12), ("Planks", 30, 40), ("Turf", 8, 8), ("Stone", 6, 10)]
    f = U.font(24, 600)
    widths = [U.tw(f"{n}  {have} / {need}", f) + 70 for n, have, need in mats]
    tot = sum(widths) + 16 * (len(mats) - 1)
    x = (W - tot) // 2
    y = H - M - 70
    for (n, have, need), w in zip(mats, widths):
        ok = have >= need
        U.panel(
            im,
            (x, y, x + w, y + 64),
            radius=32,
            fill=U.INK,
            alpha=0.82,
            outline=U.TEAL if ok else U.CLAY,
            ow=3,
            drop=False,
        )
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
    for i, (fn, label) in enumerate(
        (
            (lambda dd, c: U.ic_rotate(dd, c, 26, U.TEXT_D, w=6, flip=True), "Rotate"),
            (lambda dd, c: U.ic_rotate(dd, c, 26, U.TEXT_D, w=6), ""),
        )
    ):
        c = (cx - 150 + i * 150, cy - 170)
        U.panel(
            im,
            (c[0] - 64, c[1] - 64, c[0] + 64, c[1] + 64),
            radius=64,
            fill=U.INK,
            alpha=0.78,
            drop=False,
        )
        d = ImageDraw.Draw(im)
        fn(d, c)
    cc = (cx, cy + 40)
    U.shadow(im, (cc[0] - 80, cc[1] - 80, cc[0] + 80, cc[1] + 80), 80, blur=14, alpha=80)
    d = ImageDraw.Draw(im)
    U.disc(d, cc, 80, U.TEAL, ring=U.WHITE, ring_w=4)
    U.ic_check(d, cc, 44, U.WHITE, w=10)
    cx2 = (cx - 190, cy + 70)
    U.panel(
        im,
        (cx2[0] - 64, cx2[1] - 64, cx2[0] + 64, cx2[1] + 64),
        radius=64,
        fill=U.INK,
        alpha=0.78,
        drop=False,
    )
    d = ImageDraw.Draw(im)
    U.ic_cross(d, cx2, 34, U.TEXT_D, w=7)
    d.text((cc[0], cc[1] + 112), "Place frame", font=U.font(22, 700), fill=U.TEXT_D, anchor="mm")
    # missing material hint
    hint = "Need 10 more planks and 4 stone to finish walls"
    fh = U.font(21, 500)
    tw = U.tw(hint, fh)
    U.panel(
        im,
        ((W - tw) // 2 - 22, H - M - 130, (W + tw) // 2 + 22, H - M - 86),
        radius=22,
        fill=U.INK,
        alpha=0.7,
        drop=False,
    )
    d = ImageDraw.Draw(im)
    d.text((W // 2, H - M - 108), hint, font=fh, fill=U.TEXT_D, anchor="mm")
    im.convert("RGB").save(out, optimize=True)
    U.report(
        [
            ("chip text on ink 82%", U.TEXT_D, U.over(U.INK, (120, 130, 110), 0.82)),
            ("teal check on ink", U.TEAL, U.INK),
            ("clay cross on ink", U.CLAY, U.INK),
            ("white check on teal", U.WHITE, U.TEAL),
            ("BUILD label teal on ink 80%", U.TEAL, U.over(U.INK, (120, 130, 110), 0.8)),
        ]
    )


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "hud":
        hud(sys.argv[2], sys.argv[3])
    elif mode == "talk":
        talk(sys.argv[2], sys.argv[3])
    elif mode == "trade":
        trade(sys.argv[2], sys.argv[3])
    elif mode == "wonder":
        wonder(sys.argv[2], sys.argv[3])
    elif mode == "build":
        build(sys.argv[2], sys.argv[3])
    elif mode == "grade":
        grade(load(sys.argv[2])).convert("RGB").save(sys.argv[3], optimize=True)
