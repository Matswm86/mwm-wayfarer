"""Key frame 1: Nordic fjord coast at golden hour with an aurora hint, player over-the-shoulder.
Variants: key (key_fjord), talk (fisher NPC on the jetty), build (ghost house frame), hud (same as key).

BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user \
blender -b --factory-startup -P tools/art/scene_fjord.py -- <variant> <out.png> [scale] [samples]
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import wf_art as A  # noqa: E402
import wf_build as B  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
VARIANT = argv[0]
OUT = argv[1]
SCALE = float(argv[2]) if len(argv) > 2 else 1.0
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
# Lighting overrides for A/B renders; unset = the original key-frame values.
LIT = {k: float(os.environ.get(f"WF_{k}", d)) for k, d in (("SUN_ELEV", 7.0), ("SUN_ENERGY", 4.5), ("FOG_START", 80), ("FOG_MAX", 0.7), ("MIST_ALPHA", 0.4), ("EXPOSURE", -0.2))}
SCREEN_RT = os.environ.get("WF_SCREEN_RT") == "1"
# Mountain relief: spurs, bays, gullies, uneven crests and a scree apron instead of one smooth wall.
RELIEF = os.environ.get("WF_RELIEF") == "1"
R = A.rng(7)


# Real terrain: Naeroyfjord, Kartverket DTM 10 (© Kartverket, CC BY 4.0), resampled by tools/terrain/dem_to_game.py.
DEM = None
if os.environ.get("WF_DEM") == "1":
    import numpy as np

    DEM = np.load(Path(__file__).resolve().parents[2] / "assets" / "_raw" / "dem" / "naeroy_game.npz")
    DEM = {k: DEM[k] for k in DEM.files}


def xs(y):
    if DEM is not None:
        return float(np.interp(y, DEM["ty"], DEM["xs"]))
    bend = 0.00035 * (y - 1800) ** 2 if y > 1800 else 0.0
    return -30 + 25 * math.sin(y / 170) + bend


def W(y):
    if DEM is not None:
        return float(np.interp(y, DEM["ty"], DEM["w"]))
    return 380 + 0.08 * max(y, 0)


def dem_h(x, y):
    """Bilinear height from the resampled DTM grid; clamps at the grid edge."""
    g, st = DEM["grid"], float(DEM["step"])
    fx = min(max((x - float(DEM["x0"])) / st, 0.0), g.shape[1] - 1.001)
    fy = min(max((y - float(DEM["y0"])) / st, 0.0), g.shape[0] - 1.001)
    i, j = int(fy), int(fx)
    ty, tx = fy - i, fx - j
    top = g[i, j] * (1 - tx) + g[i, j + 1] * tx
    bot = g[i + 1, j] * (1 - tx) + g[i + 1, j + 1] * tx
    return float(top * (1 - ty) + bot * ty)


P0 = (xs(25.0) + 16.0, 25.0, 5.5) if DEM is not None else (-10.0, 25.0, 5.5)
VIEW = (-0.07, 0.997)  # view heading of the key frame (4 deg left of +Y)


def h(x, y):
    z = h_raw(x, y)
    # a calm knoll for the player: blend to a plane that falls away toward the view
    dx, dy = x - P0[0], y - P0[1]
    k = math.exp(-((dx * dx + dy * dy) / (22.0**2)))
    along = dx * VIEW[0] + dy * VIEW[1]
    side = dx * VIEW[1] - dy * VIEW[0]
    zk = P0[2] - 0.10 * max(0.0, along) + 0.03 * max(0.0, -along) + 0.12 * side
    return z * (1 - k) + zk * k


def h_raw(x, y):
    if DEM is not None:
        z = dem_h(x, y)
        e = x - xs(y)
        # village shelf on the east shore: ease the real 15-25 % slope toward a gentle bench
        m = 0.75 * (1 - B.smoothstep(90, 170, e)) * B.smoothstep(-5, 15, e) * B.smoothstep(-150, -50, y) * (1 - B.smoothstep(380, 480, y))
        if m > 0:
            z = z * (1 - m) + (1.0 + 0.045 * min(e, 95) + 0.5 * B.fbm(x / 30, y / 30)) * m
        return z
    e = x - xs(y)
    n1 = B.fbm(x / 260, y / 260)
    if e >= 0:
        shelf = B.smoothstep(40, 100, y) * (1 - B.smoothstep(270, 340, y))
        z0 = 0.30 * min(e, 110) + 620 * (1 - math.exp(-((max(0.0, e - 110)) / 220) ** 1.6))
        z1 = 1.0 + 0.045 * min(e, 95) + 0.5 * B.fbm(x / 30, y / 30) + 650 * (1 - math.exp(-((max(0.0, e - 95)) / 200) ** 1.6))
        z = z0 * (1 - shelf) + z1 * shelf
        steep = B.smoothstep(100, 160, e)
        z += n1 * 22 * B.smoothstep(0, 60, e) + steep * 40 * B.ridged(x / 45, y / 170, 4)
        if RELIEF:
            z += steep * (110 * B.fbm(y / 300, 8.2, 3) - gullies(x, y) * B.smoothstep(140, 400, e))
        return z
    e2 = xo = xs(y) - W(y)
    e2 = xo - x
    if RELIEF:
        e2 += 110 * B.fbm(y / 420, 1.7, 3) + 45 * B.fbm(y / 140, 5.1, 3)
    if e2 >= 0 and RELIEF:
        return wall(x, y, e2, n1, crest=720 + 380 * B.fbm(y / 520, 3.3, 4), notch=True)
    if e2 >= 0:
        hl = 780 + 220 * B.fbm(y / 900, 3.3, 3)
        z = hl * (1 - math.exp(-(e2 / 70) ** 1.45))
        z += n1 * 30 * B.smoothstep(0, 40, e2) + B.smoothstep(15, 80, e2) * 55 * B.ridged(x / 50, y / 140, 4)
        # hanging valley notch where the waterfall leaves the plateau
        z -= 120 * math.exp(-(((y - 1150) / 90) ** 2)) * B.smoothstep(40, 200, e2)
        return z
    return -10.0 - 30 * min(1.0, min(-e, -(xo - x)) / 120)


def gullies(x, y):
    """Couloirs: narrow cuts that run down the slope (noise varies fast along the valley, slow across it)."""
    g = 1.0 - abs(B.fbm(y / 85 + 0.3 * B.fbm(x / 200, y / 200, 2), x / 420, 3))
    return 140 * g**4


def wall(x, y, e2, n1, crest, notch):
    """Fjord wall profile: scree apron, steep face, then a rounded shoulder to an uneven crest."""
    apron = 28 * B.smoothstep(0, 45, e2)
    face = crest * (1 - math.exp(-(max(0.0, e2 - 25) / 85) ** 1.6))
    z = apron + face
    up = B.smoothstep(40, 160, e2)
    z += n1 * 30 * B.smoothstep(0, 40, e2) + up * 95 * B.ridged(x / 70, y / 110, 5)
    z -= gullies(x, y) * B.smoothstep(60, 260, e2) * (1 - B.smoothstep(500, 900, e2))
    z += up * 60 * B.fbm(x / 90, y / 60, 4)
    if notch:
        z -= 120 * math.exp(-(((y - 1150) / 90) ** 2)) * B.smoothstep(40, 200, e2)
    return z


def terrain():
    layers = dict(
        flat=("leafy_grass", 7.0, (0.62, 0.78, 0.5)),
        steep=("rock_face_03", 26.0, (0.36, 0.40, 0.42)),
        high=("aerial_grass_rock", 40.0, (0.7, 0.8, 0.62)),
    )
    m = A.terrain_mat("fjord_terrain", layers, slope=(0.5, 0.72) if (RELIEF or DEM is not None) else (0.32, 0.58), box_all=RELIEF or DEM is not None, height=(560, 760), macro=0.004, macro_amp=(0.6, 1.2))
    def hmid(x, y):
        d = max(abs(x - P0[0]) - 40, abs(y - P0[1] - 30) - 55)
        return h(x, y) - 0.9 * (1 - B.smoothstep(-5, 5, d))

    mid = A.grid_mesh("terrain_mid", hmid, -1500, 1500, -300, 3600, 420, 520, m)
    far = A.grid_mesh("terrain_far", lambda x, y: h(x, y) - 3.0, -7000, 7000, -4000, 11000, 280, 300, m)
    return mid, far


def near_patch(P):
    """High-res ground round the player: grass and moss, a worn foot path, micro relief."""
    mat = bpy.data.materials.new("near")
    mat.use_nodes = True
    nt = mat.node_tree
    b = A.bsdf(mat)
    uv = A.mapping(nt, 1 / 2.5, "UV")
    G = A.tex_nodes(nt, "leafy_grass", uv)
    uv2 = A.mapping(nt, 1 / 2.0, "UV", rot=0.7)
    T = A.tex_nodes(nt, "forest_ground_04", uv2)
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "path"
    nz = A.noise(nt, 0.6, detail=4)
    pm = A.maprange(nt, A.math_node(nt, "ADD", attr.outputs["Color"], A.math_node(nt, "MULTIPLY", A.math_node(nt, "SUBTRACT", nz, 0.5), 0.25)), 0.45, 0.7)
    gcol = A.tint(nt, G["albedo"], (0.9, 1.0, 0.75))
    col = A.mixc(nt, pm, gcol, T["albedo"])
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(A.mixf(nt, pm, G["rough"], T["rough"]), b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(A.mixc(nt, pm, G["normal"], T["normal"]), nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])

    def hn(x, y):
        return h(x, y) + 0.35 * B.fbm(x / 3, y / 3, 3) + 0.08 * B.fbm(x / 0.7, y / 0.7, 2) + 0.06

    o = A.grid_mesh("near", hn, P.x - 45, P.x + 45, P.y - 25, P.y + 90, 240, 300, mat)
    ca = o.data.color_attributes.new("path", "FLOAT_COLOR", "POINT")
    for i, v in enumerate(o.data.vertices):
        px = P.x + 0.3 + 1.6 * math.sin((v.co.y - P.y) / 14.0) - 0.08 * (v.co.y - P.y)
        d = abs(v.co.x - px)
        w = max(0.0, 1.0 - d / 0.9)
        ca.data[i].color = (w, w, w, 1)
    return o, hn


def scatter_near(P, hn):
    grass = [A.proto("grass_medium_01"), A.proto("grass_medium_02")]
    fern = A.proto("fern_02")
    rocks = A.proto_variants("rock_moss_set_01") + [A.proto("rock_face_02")]
    for i in range(4500):
        x = P.x + R.uniform(-30, 30)
        y = P.y + R.uniform(-6, 70)
        px = P.x + 0.3 + 1.6 * math.sin((y - P.y) / 14.0) - 0.08 * (y - P.y)
        if abs(x - px) < 0.9 + R.random() * 0.4:
            continue
        dist = (Vector((x, y)) - Vector((P.x, P.y - 3.5))).length
        if dist > 18 and R.random() < 0.55:
            continue
        if hn(x, y) < 0.8:
            continue
        g = grass[0] if R.random() < 0.35 else grass[1]
        A.inst(g, (x, y, hn(x, y) - 0.03), yaw=R.uniform(0, 6.3), scale=R.uniform(0.9, 1.7))
    for i in range(70):
        x = P.x + R.uniform(-22, 22)
        y = P.y + R.uniform(-4, 50)
        px = P.x + 0.3 + 1.6 * math.sin((y - P.y) / 14.0) - 0.08 * (y - P.y)
        if abs(x - px) < 1.4:
            continue
        A.inst(fern, (x, y, hn(x, y) - 0.05), yaw=R.uniform(0, 6.3), scale=R.uniform(0.8, 1.5))
    for i in range(18):
        x = P.x + R.uniform(-26, 26)
        y = P.y + R.uniform(6, 70)
        px = P.x + 0.3 + 1.6 * math.sin((y - P.y) / 14.0) - 0.08 * (y - P.y)
        if abs(x - px) < 2.5 or abs(x - P.x) < 6 and y < P.y + 20:
            continue
        A.inst(R.choice(rocks), (x, y, hn(x, y) - 0.25), yaw=R.uniform(0, 6.3), scale=R.uniform(0.35, 0.9))


def shore_rocks():
    rocks = A.proto_variants("rock_moss_set_01") + [A.proto("coast_rocks_01", tint_rgb=(0.7, 0.72, 0.7)), A.proto("boulder_01", tint_rgb=(0.75, 0.78, 0.76))]
    for i in range(70):
        y = R.uniform(-60, 90)
        x = xs(y) + R.uniform(-4, 5)
        if abs(x - P0[0]) < 4 and abs(y - P0[1]) < 6:
            continue
        A.inst(R.choice(rocks), (x, y, h(x, y) - 0.6), yaw=R.uniform(0, 6.3), scale=R.uniform(0.5, 1.6))


def trees():
    firs = A.proto_variants("fir_tree_01")
    pines = A.proto_variants("pine_tree_01")
    imps = [A.impostor(c, 512, tint=(0.9, 0.95, 0.85)) for c in firs] + [A.impostor(c, 512, tint=(0.9, 0.95, 0.85)) for c in pines[:2]]
    n = 0
    nfull = 0
    for _ in range(2600):
        y = R.uniform(-80, 1400)
        x = xs(y) + R.uniform(12, 520)
        z = h(x, y)
        if z > 360 or z < 2.5:
            continue
        if 90 < y < 300 and x < xs(y) + 85:
            continue
        dpl = (Vector((x, y)) - Vector((P0[0], P0[1]))).length
        if dpl < 16:
            continue
        nx = (h(x + 3, y) - h(x - 3, y)) / 6
        if abs(nx) > 1.0 and R.random() < 0.8:
            continue
        if dpl < 70 and nfull < 4:
            c = R.choice(firs)
            nfull += 1
        else:
            c = R.choice(imps)
        A.inst(c, (x, y, z - 0.3), yaw=R.uniform(0, 6.3), scale=R.uniform(0.7, 1.25))
        n += 1
    for _ in range(900):
        y = R.uniform(150, 3000)
        x = xs(y) - W(y) - R.uniform(4, 160)
        z = h(x, y)
        if z > 300 or z < 2.5:
            continue
        nx = (h(x + 3, y) - h(x - 3, y)) / 6
        if abs(nx) > 1.3 and R.random() < 0.85:
            continue
        A.inst(R.choice(imps), (x, y, z - 0.3), yaw=R.uniform(0, 6.3), scale=R.uniform(0.8, 1.3))
        n += 1
    # village garden trees
    for y in (110, 150, 196, 236, 280):
        x = xs(y) + R.uniform(40, 80)
        A.inst(R.choice(imps), (x, y, h(x, y) - 0.2), yaw=R.uniform(0, 6.3), scale=R.uniform(0.6, 0.9))
    print("TREES", n)


def cliffs():
    """Scaled rock-face scans (Poly Haven mountainside, rock_face_01) dress the steep walls with real relief."""
    faces = [A.proto("mountainside", tint_rgb=(0.78, 0.86, 0.88), hue=(0.5, 0.35, 0.8)), A.proto("rock_face_01", tint_rgb=(0.78, 0.86, 0.86), hue=(0.5, 0.35, 0.8))]
    y = 260.0
    while y < 3200:
        xo = xs(y) - W(y)
        s = R.uniform(26, 40)
        c = faces[0] if R.random() < 0.75 else faces[1]
        sz = A.proto_size(c)
        sc = s if c is faces[0] else s * 2.0
        e2 = R.uniform(6, 30)
        A.inst(c, (xo - e2, y, h(xo - e2, y) - 25), yaw=math.radians(90 + R.uniform(-12, 12)), scale=sc)
        if R.random() < 0.7:
            e3 = e2 + R.uniform(60, 120)
            A.inst(faces[0], (xo - e3, y + R.uniform(-60, 60), h(xo - e3, y) - 40), yaw=math.radians(90 + R.uniform(-15, 15)), scale=s * 1.1)
        y += sz.x * sc * R.uniform(0.4, 0.6)
    y = 420.0
    while y < 2600:
        xr = xs(y)
        s = R.uniform(24, 38)
        e2 = R.uniform(140, 220)
        A.inst(faces[0], (xr + e2, y, h(xr + e2, y) - 30), yaw=math.radians(-90 + R.uniform(-12, 12)), scale=s)
        y += 10.2 * s * R.uniform(0.6, 0.85)


def village():
    houses = [
        # x offset from shore, y, yaw(deg), w, d, wall, lit
        (28, 118, 12, 6.0, 9.0, "red", 0.7),
        (46, 140, 98, 5.5, 8.0, "ochre", 0.6),
        (22, 160, 8, 5.0, 7.0, "white", 0.8),
        (55, 178, 95, 6.5, 10.0, "red", 0.5),
        (30, 205, 15, 5.0, 7.0, "red", 0.9),
        (62, 222, 100, 5.0, 7.5, "white", 0.5),
        (36, 246, 20, 6.0, 8.0, "ochre", 0.6),
        (70, 262, 90, 5.0, 6.5, "red", 0.4),
        (14, 270, 5, 4.5, 6.0, "tar", 0.3),
    ]
    for i, (dx, y, yaw, w, d, wall, lit) in enumerate(houses):
        x = xs(y) + dx
        B.nordic_house((x, y, h(x, y) - 0.15), math.radians(yaw), w=w, d=d, h=2.8 + 0.4 * (i % 2), wall=wall, lit=lit, seed=i)
    # boathouses (naust) at the shore, gable to the water
    for i, y in enumerate((150, 192)):
        x = xs(y) + 5
        B.nordic_house((x, y, max(0.2, h(x, y)) - 0.1), math.radians(90), w=5.0, d=9.0, h=2.4, pitch=32, wall="tar", lit=0.0, seed=20 + i, chimney=False)
    # jetty and boats
    pier = A.proto("modular_wooden_pier")
    sz = A.proto_size(pier)
    print("PIER", sz)
    yj = 172
    A.inst(pier, (xs(yj) - 6, yj, -0.6), yaw=math.radians(90), scale=1.0)
    A.inst(pier, (xs(yj) - 22, yj, -0.6), yaw=math.radians(90), scale=1.0)
    boats = [(-10, yj + 3.0, 4, "#E9E4DA", False), (-18, yj - 3.2, -6, "#2F5A4A", True), (-26, yj + 3.4, 2, "#8E2B22", False), (-60, 240, 40, "#DCD6C8", True)]
    for i, (dx, y, yaw, col, cab) in enumerate(boats):
        B.boat((xs(yj) + dx, y, -0.28), math.radians(90 + yaw), L=6.5 if not cab else 8.0, B=2.0 if not cab else 2.5, color=col, seed=i, cabin=cab)
    # barrels and crates on the shore
    bar = A.proto("wooden_barrels_01")
    A.inst(bar, (xs(yj) + 3, yj - 6, h(xs(yj) + 3, yj - 6)), yaw=0.3)


def water():
    m = A.water_mat("fjord_water", A.hexc("#061A1E"), A.hexc("#16383A"), rough=0.02, wave_scale=0.05, wave_strength=0.08)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-200, 3000, 0))
    o = bpy.context.active_object
    o.scale = (6000, 8000, 1)
    o.data.materials.append(m)
    pr = bpy.data.lightprobes.new("planar", "PLANE")
    po = A.link(bpy.data.objects.new("planar", pr))
    po.location = (-200, 2000, 0.02)
    po.scale = (3000, 4000, 1)
    return o


def falls():
    y0 = 1150
    pts = []
    xo = xs(y0) - W(y0)
    for k in range(40):
        t = k / 39
        e2 = 120 * (1 - t) ** 1.5 + 1.5
        x = xo - e2
        z = h(x, y0)
        pts.append((x + 2.0, y0 + 6 * math.sin(t * 5), z + 2.5))
    B.waterfall(pts, 34.0, strength=2.6)
    xb = xo + 10
    for i in range(5):
        B.mist((xb - 15 + i * 6, y0 + R.uniform(-15, 15), 18 + i * 7), (90, 55), alpha=LIT["MIST_ALPHA"], face=(P0[0], P0[1], 10), seed=i)


def player_and_camera(P, variant):
    import wf_mh as M

    yaw = float(os.environ.get("WF_YAW", 6.0))  # degrees left of +Y
    M.character("explorer", "stand_look", loc=(P.x, P.y, P.z), yaw_deg=yaw)
    fwd = Vector((-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0))
    right = Vector((fwd.y, -fwd.x, 0))
    cam = P - fwd * 3.8 + right * 1.2 + Vector((0, 0, 2.05))
    tgt = P + fwd * 80 + Vector((0, 0, 8.0)) + right * 6
    return A.camera(cam, tgt, lens=26, dof=((P - cam).length, 5.6))


def ghost_frame(c, yaw):
    """Build-mode ghost: timber frame (sills, posts, plates, rafters) in a translucent teal-white material."""
    m = bpy.data.materials.new("ghost")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = A.hexc("#BFF3EA")
    em.inputs["Strength"].default_value = 1.6
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.5
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    w, d, hh = 6.0, 8.0, 2.8
    parts = []
    t = 0.22
    for sy in (-1, 1):
        parts.append(B.cube("sill", (w, t, t), (0, sy * d / 2, 0.15), m))
        parts.append(B.cube("plate", (w, t, t), (0, sy * d / 2, hh), m))
    for sx in (-1, 1):
        parts.append(B.cube("sill", (t, d, t), (sx * w / 2, 0, 0.15), m))
        parts.append(B.cube("plate", (t, d, t), (sx * w / 2, 0, hh), m))
        for k in range(5):
            parts.append(B.cube("post", (t, t, hh), (sx * w / 2, -d / 2 + k * d / 4, hh / 2), m))
    for k in range(5):
        y = -d / 2 + k * d / 4
        for sx in (-1, 1):
            r = B.cube("rafter", (t * 0.8, t * 0.8, 3.9), (sx * w / 4, y, hh + 0.75), m)
            r.rotation_euler = (0, sx * math.radians(-62), 0)
            parts.append(r)
    parts.append(B.cube("ridge", (t, d, t), (0, 0, hh + 1.6), m))
    # footprint
    fm = A.flat_mat("footprint", (0.2, 0.75, 0.65, 1), emit=A.hexc("#2FA396"), emit_strength=2.0)
    for sy in (-1, 1):
        parts.append(B.cube("fp", (w + 1.0, 0.08, 0.04), (0, sy * (d / 2 + 0.5), 0.03), fm))
    for sx in (-1, 1):
        parts.append(B.cube("fp", (0.08, d + 1.0, 0.04), (sx * (w / 2 + 0.5), 0, 0.03), fm))
    root = bpy.data.objects.new("ghost", None)
    A.link(root)
    for p in parts:
        p.parent = root
    root.location = c
    root.rotation_euler = (0, 0, yaw)


def talk_setup():
    import wf_mh as M

    y = 128.0
    x = xs(y) + 11.0
    P = Vector((x, y, h(x, y)))
    F = Vector((x - 1.2, y + 4.6, 0))
    F.z = h(F.x, F.y)
    M.character("explorer", "stand_look", loc=tuple(P), yaw_deg=8)
    M.character("fisher", "talk", loc=tuple(F), yaw_deg=180 + 10)
    right = Vector((1, 0, 0))
    cam = P + Vector((0, -3.0, 0)) + right * 0.95 + Vector((0, 0, 1.95))
    tgt = F + Vector((0, 0, 1.45)) + right * -0.4
    A.camera(cam, tgt, lens=40, dof=((F - cam).length, 2.8))


def main():
    A.reset()
    t0 = __import__("time").time()
    A.eevee(samples=SAMPLES, res=(int(1920 * SCALE), int(1080 * SCALE)), exposure=LIT["EXPOSURE"])
    if SCREEN_RT and hasattr(bpy.context.scene.eevee, "ray_tracing_method"):
        bpy.context.scene.eevee.ray_tracing_method = "SCREEN"
    w, nt, env = A.world_hdri(os.environ.get("WF_HDRI", "qwantani_dusk_2_puresky_4k.hdr"), 25, strength=0.9)
    if os.environ.get("WF_AURORA", "1") == "1":
        B.aurora(nt, nt.nodes["Background"], strength=2.2, az_center=112.0, az_width=40.0, elev=(16.0, 46.0))
    A.sun(LIT["SUN_ELEV"], 152, color=(1.0, 0.66, 0.36), energy=LIT["SUN_ENERGY"], angle=1.5)
    terrain()
    water()
    falls()
    village()
    if not (RELIEF or DEM is not None) or os.environ.get("WF_CLIFF_SCANS") == "1":
        cliffs()
    shore_rocks()
    trees()
    P = Vector((P0[0], P0[1], h(P0[0], P0[1])))
    near, hn = near_patch(P)
    P.z = hn(P.x, P.y)
    if VARIANT != "talk":
        scatter_near(P, hn)
    if VARIANT == "talk":
        talk_setup()
    else:
        player_and_camera(P, VARIANT)
    if VARIANT == "build":
        gx, gy = P.x + 4.0, P.y + 14.0
        ghost_frame((gx, gy, hn(gx, gy) + 0.05), math.radians(-12))
    A.compositor_fog((0.56, 0.62, 0.72), LIT["FOG_START"], 3200, LIT["FOG_MAX"], sky_haze=0.05, haze_power=2.0)
    print("BUILD", round(__import__("time").time() - t0, 1))
    bpy.ops.wm.save_as_mainfile(filepath=str(A.BUILD / f"fjord_{VARIANT}.blend"))
    if "--norender" not in argv:
        A.render(OUT)


main()
