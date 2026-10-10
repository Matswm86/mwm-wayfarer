"""Key frame 2: R2 Amberline Isles (lost-age Mediterranean archipelago).

Real coast: Kefalonia west coast, Myrtos bay to the Assos peninsula, Copernicus GLO-30 elevation
(see assets/_raw/dem/cop30/SOURCE.md for licence and the required notice), resampled by
tools/terrain/cop_to_game.py kefalonia. Frame: metres, +X east, +Y north.
The player stands on olive terraces above a ruined temple on the south headland of the bay, looking north over
turquoise shallows and white limestone cliffs toward the peninsula; a giant marble head lies in the shallows.

BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user \
flock ~/MWM/scratch/wayfarer/render.lock blender -b --factory-startup -P tools/art/scene_archipelago.py -- key <out.png> [scale] [samples]
Env for look-dev: WF_YAW (view bearing, deg from north), WF_PITCH, WF_EXPOSURE, WF_FAST=1 (skip far vegetation),
WF_P0="x,y" (player), WF_FOG_START / WF_FOG_MAX / WF_FOG_POW (aerial perspective).
10-10 b terrace view (docs/mockups/key_archipelago_terraces.jpg): WF_P0="-900,-430" WF_YAW=14 WF_PITCH=-4 WF_FOG_MAX=0.36.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
import wf_art as A  # noqa: E402
import wf_build as B  # noqa: E402
from mathutils import Vector  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
VARIANT = argv[0]
OUT = argv[1]
SCALE = float(argv[2]) if len(argv) > 2 else 1.0
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
FAST = os.environ.get("WF_FAST") == "1"
R = A.rng(11)

DEM = A.dem_sampler(A.RAW / "dem" / "kefalonia_game.npz")
# player: default on the headland's west shoulder; WF_P0="x,y" moves the look-dev camera (10-10 b uses the slope above)
P0 = tuple(float(v) for v in os.environ.get("WF_P0", "-1057,12").split(","))
T = (-760.0, 8.0)  # temple centre, on a podium on the shoulder above the beach
T_ROT = math.radians(84.0)
YAW = float(os.environ.get("WF_YAW", 62.0))  # view bearing, degrees east of north
PITCH = float(os.environ.get("WF_PITCH", -4.0))
VIEW = (math.sin(math.radians(YAW)), math.cos(math.radians(YAW)))
TZ = DEM(*T) + 5.0  # temple platform height: cut into the slope uphill, podium wall downhill


def _rot(dx, dy, a):
    c, s = math.cos(a), math.sin(a)
    return dx * c + dy * s, -dx * s + dy * c


def h_land(x, y):
    """Real elevation plus small-scale karst relief (the 30 m data has no rock detail)."""
    z = DEM(x, y)
    if z > 0.0:
        k = B.smoothstep(0.0, 6.0, z)
        z += k * (2.2 * B.fbm(x / 38, y / 38, 4) + 0.9 * B.ridged(x / 11, y / 11, 3) - 0.6)
    return z


TC = (-830.0, 70.0)  # terrace field: the slope from the headland down to the bay
TR = (190.0, 85.0)
TSTEP = 3.0


# second terrace field (10-10 b): the slope right in front of the player, so terraces read in the foreground too
TC2 = (P0[0] + VIEW[0] * 165, P0[1] + VIEW[1] * 165)
TR2 = (150.0, 150.0)


def terr_mask(x, y):
    d = math.hypot((x - TC[0]) / TR[0], (y - TC[1]) / TR[1])
    d2 = math.hypot((x - TC2[0]) / TR2[0], (y - TC2[1]) / TR2[1])
    return 1.0 - B.smoothstep(0.7, 1.0, min(d, d2))


def terraces(x, y, z):
    """Olive terraces: 3 m steps with short dry-stone risers on the slope down to the bay."""
    m = terr_mask(x, y)
    if m <= 0 or z < 6:
        return z
    k = z / TSTEP
    fr = k - math.floor(k)
    zt = TSTEP * (math.floor(k) + B.smoothstep(0.86, 1.0, fr))  # steep 0.4 m-wide risers = dry-stone walls
    return z * (1 - m) + zt * m


def h(x, y):
    z = h_land(x, y)
    z = terraces(x, y, z)
    # temple platform: ease the headland top to a level bench
    u, v = _rot(x - T[0], y - T[1], T_ROT)
    k = math.exp(-((u * u / (34.0**2) + v * v / (58.0**2)) ** 2))
    z = z * (1 - k) + TZ * k
    # a calm stand for the player
    dx, dy = x - P0[0], y - P0[1]
    k = math.exp(-((dx * dx + dy * dy) / (14.0**2)))
    return z * (1 - k) + (DEM(*P0) + 0.4) * k


def terrain():
    layers = dict(
        flat=("rock_ground_02", 5.0, (1.2, 1.12, 0.98)),
        patch=("aerial_rocks_04", 24.0, (0.78, 0.86, 0.6)),
        steep=("marble_cliff_05", 20.0, (1.12, 1.12, 1.1)),
        high=("aerial_rocks_02", 40.0, (1.0, 1.0, 0.94)),
        low=("coast_sand_01", 6.0, (1.12, 1.08, 1.0)),
    )
    m = A.terrain_mat(
        "arch_terrain",
        layers,
        slope=(0.62, 0.8),
        height=(420, 520),
        macro=0.006,
        macro_amp=(0.78, 1.12),
        extra=(0.4, 3.0, 1.5),
        box_all=True,
        patch=(0.02, 0.44, 0.58),
    )
    nb = (P0[0] - 70, P0[0] + 70, P0[1] - 30, P0[1] + 110)

    def hmid(x, y):
        dd = max(nb[0] - x, x - nb[1], nb[2] - y, y - nb[3])
        return h(x, y) - 0.9 * (1 - B.smoothstep(-6, 2, dd))

    A.grid_mesh("terrain_near", h, nb[0], nb[1], nb[2], nb[3], 140, 140, m)
    # terrace fields at 0.6 m so the risers become real walls; their own material: dry-stone risers, soil treads
    tm = A.terrain_mat(
        "terrace_mat",
        dict(
            flat=("rock_ground_02", 4.0, (1.12, 1.02, 0.84)),
            patch=("aerial_rocks_04", 14.0, (0.8, 0.86, 0.6)),
            steep=("stone_wall", 2.2, (1.05, 1.0, 0.92)),
        ),
        slope=(0.5, 0.66),
        macro=0.02,
        macro_amp=(0.85, 1.1),
        box_all=True,
        patch=(0.05, 0.45, 0.6),
    )
    fields = []
    for c, r in ((TC, TR), (TC2, TR2)):
        box = (c[0] - r[0], c[0] + r[0], c[1] - r[1], c[1] + r[1])
        fields.append(box)
        A.grid_mesh(
            "terraces", lambda x, y: h(x, y) + 0.02, box[0], box[1], box[2], box[3], int(2 * r[0] / 0.6), int(2 * r[1] / 0.6), tm
        )

    def hmid(x, y, _h=hmid):
        z = _h(x, y)
        if terr_mask(x, y) > 0.72:  # under a terrace field: sink the coarse mesh out of sight
            z -= 1.5
        return z

    A.grid_mesh("terrain_mid", hmid, -2600, 900, -700, 2600, 560, 528, m)
    A.grid_mesh("terrain_far", lambda x, y: DEM(x, y) - 2.0, -6000, 6000, -5000, 9000, 400, 467, m)
    return m


def sea():
    """Grid sea: vertex colour = depth under the surface (turquoise over the sand shelf, deep blue beyond)."""
    mat = bpy.data.materials.new("sea")
    mat.use_nodes = True
    nt = mat.node_tree
    b = A.bsdf(mat)
    va = nt.nodes.new("ShaderNodeVertexColor")
    va.layer_name = "depth"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(va.outputs["Color"], sep.inputs["Color"])
    d = sep.outputs["Red"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    c1 = A.mixc(nt, A.maprange(nt, d, 0.0, 0.14), A.hexc("#7FD6C8"), A.hexc("#22AFB2"))
    c2 = A.mixc(nt, A.maprange(nt, d, 0.14, 0.5), c1, A.hexc("#0C7E9C"))
    c3 = A.mixc(nt, A.maprange(nt, d, 0.5, 1.0), c2, A.hexc("#083F6C"))
    # seagrass (Posidonia) meadows: dark patches on the sandy shelf, from 3 m down
    sg = A.maprange(nt, A.noise(nt, 0.012, tc.outputs["Object"], detail=6, rough=0.65), 0.5, 0.58)
    sg = A.math_node(nt, "MULTIPLY", sg, A.maprange(nt, d, 0.08, 0.16))
    sg = A.math_node(nt, "MULTIPLY", sg, A.maprange(nt, d, 0.7, 0.5))
    c3 = A.mixc(nt, A.math_node(nt, "MULTIPLY", sg, 0.75), c3, A.hexc("#14404A"))
    # foam where the water is a few cm deep, broken by noise
    foam = A.maprange(nt, d, 0.03, 0.0)
    fn = A.maprange(nt, A.noise(nt, 0.9, tc.outputs["Object"], detail=4), 0.42, 0.62)
    col = A.mixc(nt, A.math_node(nt, "MULTIPLY", foam, fn), c3, (0.9, 0.95, 0.95, 1))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["IOR"].default_value = 1.33
    n2 = A.noise(nt, 0.25, tc.outputs["Object"], detail=8, rough=0.6)
    w1 = nt.nodes.new("ShaderNodeTexWave")
    w1.inputs["Scale"].default_value = 0.035
    w1.inputs["Distortion"].default_value = 6
    nt.links.new(tc.outputs["Object"], w1.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.3
    nt.links.new(
        A.math_node(nt, "ADD", n2, A.math_node(nt, "MULTIPLY", w1.outputs["Fac"], 0.3)),
        bump.inputs["Height"],
    )
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    o = A.grid_mesh("sea", lambda x, y: 0.0, -3200, 1200, -900, 7000, 440, 790, mat)
    ca = o.data.color_attributes.new("depth", "FLOAT_COLOR", "POINT")
    for i, v in enumerate(o.data.vertices):
        dd = min(1.0, max(0.0, -DEM(v.co.x, v.co.y)) / 28.0)
        ca.data[i].color = (dd, dd, dd, 1)
    A.grid_mesh(
        "sea_far",
        lambda x, y: -0.05,
        -30000,
        30000,
        -20000,
        40000,
        10,
        10,
        A.water_mat(
            "sea_far_m",
            A.hexc("#083E66"),
            A.hexc("#0C5E86"),
            rough=0.05,
            wave_scale=0.02,
            wave_strength=0.12,
        ),
    )
    return o


# ---------------------------------------------------------------- temple
def column(name, base, height, radius, mat, broken=None, seed=0):
    """Fluted Doric column with entasis; broken=None or the height of the break (jagged top)."""
    seg, rings = 40, 20
    hh = height if broken is None else broken
    verts, faces = [], []
    for j in range(rings + 1):
        t = j / rings
        z = hh * t
        tt = z / height
        r = radius * (1.0 - 0.18 * tt + 0.05 * math.sin(math.pi * tt))
        for i in range(seg):
            a = 2 * math.pi * i / seg
            fl = 1.0 - 0.045 * abs(math.sin(10 * a))
            jag = 0.0
            if broken is not None and j == rings:
                jag = (
                    (0.6 * math.sin(a * 3 + seed) + 0.4 * math.sin(a * 7 + seed * 2)) * radius * 0.5
                )
            verts.append((r * fl * math.cos(a), r * fl * math.sin(a), z + jag))
    for j in range(rings):
        for i in range(seg):
            a = j * seg + i
            b2 = j * seg + (i + 1) % seg
            faces.append((a, b2, b2 + seg, a + seg))
    faces.append(tuple(range(rings * seg, rings * seg + seg)))
    o = B._obj(
        name,
        verts,
        faces,
        mat,
        smooth=True,
        uv_fn=lambda co, n: (math.atan2(co.y, co.x) * radius, co.z),
    )
    objs = [o]
    if broken is None:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=40,
            radius=radius * 1.12,
            depth=radius * 0.45,
            location=(0, 0, height + radius * 0.2),
        )
        e = bpy.context.active_object
        e.data.materials.append(mat)
        objs.append(e)
        objs.append(
            B.cube(
                "abacus",
                (radius * 2.6, radius * 2.6, radius * 0.4),
                (0, 0, height + radius * 0.62),
                mat,
            )
        )
    root = bpy.data.objects.new(name, None)
    A.link(root)
    for x in objs:
        x.parent = root
    root.location = base
    return root


def temple():
    """Peripteral Doric temple, 6 x 13 columns (Sounion/Aphaia proportions, scaled up for a lost age), half fallen."""
    marble = A.pbr(
        "temple_marble",
        "marble_cliff_04",
        0.25,
        coords="Object",
        box=True,
        tint_rgb=(1.1, 1.06, 0.98),
    )
    stone = A.pbr(
        "temple_blocks",
        "white_sandstone_blocks_02",
        0.35,
        coords="Object",
        box=True,
        tint_rgb=(1.04, 1.0, 0.93),
    )
    ncol_x, ncol_y, sp, rad, colh = 6, 13, 5.6, 1.25, 15.0
    W = (ncol_x - 1) * sp
    L = (ncol_y - 1) * sp
    objs = []
    for k, (gx, gy) in enumerate(((W + 7, L + 7), (W + 5, L + 5), (W + 3, L + 3))):
        objs.append(
            B.cube(f"step{k}", (gx, gy, 0.9), (0, 0, k * 0.9 + 0.45 - 0.9), stone, bevel=0.1)
        )
    base_z = 3 * 0.9 - 0.9
    # podium / retaining terrace (Delphi-style) that carries the platform over the falling slope
    objs.append(B.cube("podium", (W + 11, L + 11, 18.0), (0, 0, -0.9 - 9.0), stone, bevel=0.2))
    r = A.rng(5)
    cols = []
    for i in range(ncol_x):
        for j in range(ncol_y):
            if 0 < i < ncol_x - 1 and 0 < j < ncol_y - 1:
                continue
            x = -W / 2 + i * sp
            y = -L / 2 + j * sp
            keep = r.random()
            standing = (j >= 4 and (i == 0 or j >= 9)) or (i == ncol_x - 1 and j >= 10)
            if standing and keep > 0.12:
                c = column(f"col{i}_{j}", (x, y, base_z), colh, rad, marble)
            elif keep > 0.3:
                c = column(
                    f"col{i}_{j}",
                    (x, y, base_z),
                    colh,
                    rad,
                    marble,
                    broken=r.uniform(1.5, 7.0),
                    seed=i + j,
                )
            else:
                continue
            cols.append((i, j, c))
            objs.append(c)
    full = {(i, j) for i, j, c in cols if len(c.children) > 1}
    top = base_z + colh + rad * 0.82
    for i in (0, ncol_x - 1):
        for j in range(ncol_y - 1):
            if (i, j) in full and (i, j + 1) in full:
                y = -L / 2 + (j + 0.5) * sp
                x = -W / 2 + i * sp
                objs.append(
                    B.cube("arch", (rad * 2.4, sp + 0.2, 1.4), (x, y, top + 0.7), stone, bevel=0.05)
                )
                objs.append(
                    B.cube(
                        "frieze", (rad * 2.2, sp + 0.2, 1.3), (x, y, top + 2.05), marble, bevel=0.04
                    )
                )
    j = ncol_y - 1
    for i in range(ncol_x - 1):
        if (i, j) in full and (i + 1, j) in full:
            x = -W / 2 + (i + 0.5) * sp
            y = -L / 2 + j * sp
            objs.append(
                B.cube("arch", (sp + 0.2, rad * 2.4, 1.4), (x, y, top + 0.7), stone, bevel=0.05)
            )
            objs.append(
                B.cube("frieze", (sp + 0.2, rad * 2.2, 1.3), (x, y, top + 2.05), marble, bevel=0.04)
            )
    yb = L / 2
    pd = B._obj(
        "pediment",
        [(-W / 2 - 1.2, yb, 0), (W / 2 + 1.2, yb, 0), (0, yb, 4.2)],
        [(0, 1, 2)],
        marble,
        uv_fn=B.box_uv,
    )
    pd.location = (0, 0, top + 2.7)
    pd.modifiers.new("s", "SOLIDIFY").thickness = 1.4
    objs.append(pd)
    # cella wall stubs
    for k in range(7):
        yy = -L / 2 + 10 + k * 5.2
        hgt = r.uniform(0.8, 3.6)
        for sx in (-1, 1):
            objs.append(
                B.cube(
                    "cella",
                    (0.9, 5.0, hgt),
                    (sx * (W / 2 - 4.2), yy, base_z + hgt / 2),
                    stone,
                    bevel=0.05,
                )
            )
    # fallen drums on the platform and down the slope
    for k in range(30):
        x = r.uniform(-W / 2 - 8, W / 2 + 8)
        y = r.uniform(-L / 2 - 6, L / 2 - 10)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32,
            radius=rad * r.uniform(0.9, 1.05),
            depth=r.uniform(1.2, 1.8),
            location=(x, y, base_z + rad * 0.9 - (0 if abs(x) < W / 2 + 2 else 1.6)),
            rotation=(math.pi / 2, 0, r.uniform(0, 6.28)),
        )
        d = bpy.context.active_object
        d.data.materials.append(marble)
        objs.append(d)
    root = bpy.data.objects.new("temple", None)
    A.link(root)
    for o in objs:
        o.parent = root
    root.location = (T[0], T[1], TZ)
    root.rotation_euler = (0, 0, T_ROT)
    return root


def colossus():
    """Giant marble head (Poly Haven marble_bust_01) half sunk in the shallows east of the headland."""
    c = A.proto("marble_bust_01", tint_rgb=(1.05, 1.02, 0.96))
    sz = A.proto_size(c)
    x, y = -715.0, 190.0
    return A.inst(
        c,
        (x, y, DEM(x, y) - 1.5),
        yaw=math.radians(250),
        scale=15.0 / sz.z,
        tilt=(math.radians(-16), math.radians(14)),
    )


def in_view(x, y, margin=40.0, far=2600.0):
    dx, dy = x - P0[0], y - P0[1]
    along = dx * VIEW[0] + dy * VIEW[1]
    side = dx * VIEW[1] - dy * VIEW[0]
    return -20 < along < far and abs(side) < along * 0.72 + margin


def slope(x, y, e=2.0):
    return math.hypot(h(x + e, y) - h(x - e, y), h(x, y + e) - h(x, y - e)) / (2 * e)


def lod(c, ratio, name):
    """Decimated copy of a prototype collection (scanned plants are 0.4-2 M triangles; a phone LOD is a few k)."""
    out = bpy.data.collections.new(name)
    A.lib_root().children.link(out)
    for o in c.objects:
        o2 = o.copy()
        out.objects.link(o2)
        o2.modifiers.new("dec", "DECIMATE").ratio = ratio
    return out


def cypress_proto():
    """Italian cypress: a lumpy dark-green spindle (reads right from 30 m out; no scan needed)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=24, radius=1.0, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = "cypress"
    for v in o.data.vertices:
        t = (v.co.z + 1) / 2
        v.co.x *= 1.15 * (1 - 0.55 * t**1.6)
        v.co.y *= 1.15 * (1 - 0.55 * t**1.6)
        v.co.z = (v.co.z + 1) * 5.5
    tx = bpy.data.textures.new("cyp_lumps", "CLOUDS")
    tx.noise_scale = 0.6
    d = o.modifiers.new("lumps", "DISPLACE")
    d.texture = tx
    d.strength = 0.45
    for p in o.data.polygons:
        p.use_smooth = True
    m = bpy.data.materials.new("cypress")
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = A.noise(nt, 2.5, tc.outputs["Object"], detail=6, rough=0.7)
    nt.links.new(A.mixc(nt, nz, A.hexc("#1E2A17"), A.hexc("#3F5230")), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    nt.links.new(A.noise(nt, 9.0, tc.outputs["Object"], detail=4), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    o.data.materials.append(m)
    c = bpy.data.collections.new("cypress")
    A.lib_root().children.link(c)
    for uc in list(o.users_collection):
        uc.objects.unlink(o)
    c.objects.link(o)
    return c


def maquis_proto():
    """Distant maquis clump (mastic, kermes oak, juniper): a lumpy flattened blob. 1-3 px at 1 km, so shape > detail."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = "maquis"
    o.scale = (1.0, 1.0, 0.62)
    bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new("maq_lumps", "CLOUDS")
    tx.noise_scale = 0.5
    d = o.modifiers.new("lumps", "DISPLACE")
    d.texture = tx
    d.strength = 0.5
    for p in o.data.polygons:
        p.use_smooth = True
    m = bpy.data.materials.new("maquis")
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = A.noise(nt, 1.5, tc.outputs["Object"], detail=5, rough=0.7)
    nt.links.new(A.mixc(nt, nz, A.hexc("#2E3820"), A.hexc("#59633A")), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    o.data.materials.append(m)
    c = bpy.data.collections.new("maquis")
    A.lib_root().children.link(c)
    for uc in list(o.users_collection):
        uc.objects.unlink(o)
    c.objects.link(o)
    return c


def vegetation():
    olive_hi = A.proto("tree_small_02", hue=(0.5, 0.5, 0.95), tint_rgb=(0.86, 0.92, 0.8))
    olive = A.impostor(olive_hi, 512, name="imp_arch_olive2", tint=(1.0, 0.93, 0.78))
    shrub4 = A.proto("shrub_04", tint_rgb=(0.8, 0.9, 0.7))
    sears = lod(A.proto("searsia_lucida", tint_rgb=(0.85, 0.92, 0.75)), 0.1, "searsia_lod")
    shrubs = [shrub4, sears]
    warm = (1.0, 0.93, 0.78)
    olive_imp = olive
    shrub_imp = A.impostor(shrub4, 256, name="imp_arch_shrub2", tint=warm)
    cyp = cypress_proto()
    maq = maquis_proto()
    grass = A.proto("grass_medium_02", tint_rgb=(1.1, 0.98, 0.65))
    rocks = A.proto("boulder_01", tint_rgb=(1.2, 1.18, 1.1))
    n = 0
    # olives in rows on the terraces (trees stand mid-tread), cypresses here and there
    for i in range(22000):
        c, r = (TC, TR) if i % 3 else (TC2, TR2)
        x = c[0] + R.uniform(-r[0], r[0])
        y = c[1] + R.uniform(-r[1], r[1])
        if not in_view(x, y, 60) or terr_mask(x, y) < 0.7:
            continue
        z = h(x, y)
        if z < 6:
            continue
        u, v = _rot(x - T[0], y - T[1], T_ROT)
        if (abs(u) < 30 and abs(v) < 48) or math.hypot(x - P0[0], y - P0[1]) < 7:
            continue
        k = (h_land(x, y) / TSTEP) % 1.0
        if not (0.25 < k < 0.6):
            continue
        rr = R.random()
        in2 = math.hypot((x - TC2[0]) / TR2[0], (y - TC2[1]) / TR2[1]) < 1.0
        if in2 and (math.hypot(x - P0[0], y - P0[1]) < 38 or R.random() < 0.45):
            continue  # foreground field: keep the first 38 m open and the grove thinner so the walls show
        if rr < 0.08 and not in2:
            A.inst(cyp, (x, y, z - 0.3), yaw=R.uniform(0, 6.3), scale=R.uniform(0.8, 1.25))
        elif rr < 0.75:
            A.inst(olive, (x, y, z - 0.15), yaw=R.uniform(0, 6.3), scale=R.uniform(0.8, 1.15))
        else:
            continue
        n += 1
    # maquis over the wider coast: real (decimated) shrubs to 400 m, cards beyond
    for _ in range(0 if FAST else 110000):
        along = 50 + 2500 * R.random() ** 1.8
        side = along * 0.74 * (2 * R.random() - 1)
        x = P0[0] + VIEW[0] * along + VIEW[1] * side
        y = P0[1] + VIEW[1] * along - VIEW[0] * side
        z = DEM(x, y)
        if z < 4 or z > 700 or terr_mask(x, y) > 0.3:
            continue
        sl = math.hypot(DEM(x + 10, y) - DEM(x - 10, y), DEM(x, y + 10) - DEM(x, y - 10)) / 20
        if sl > 1.0 or R.random() < sl * 0.8 or B.fbm(x / 140, y / 140, 3) < -0.1:
            continue
        u, v = _rot(x - T[0], y - T[1], T_ROT)
        if abs(u) < 34 and abs(v) < 52:
            continue
        rr = R.random()
        if rr < 0.05:
            c, s = cyp, R.uniform(0.8, 1.2)
        elif along < 400:
            c, s = (
                (olive, R.uniform(0.7, 1.0))
                if rr < 0.25
                else (R.choice(shrubs), R.uniform(0.9, 1.6))
            )
        else:
            c, s = (olive_imp, R.uniform(0.8, 1.2)) if rr < 0.12 else (maq, R.uniform(1.4, 3.2))
        A.inst(c, (x, y, h(x, y) - 0.3), yaw=R.uniform(0, 6.3), scale=s)
        n += 1
    # foreground: two full-resolution olives, fallen drums and a ruined wall run on the player's terrace
    marble = bpy.data.materials.get("temple_marble")
    stone = bpy.data.materials.get("temple_blocks")
    fwd = Vector((VIEW[0], VIEW[1], 0))
    right = Vector((fwd.y, -fwd.x, 0))
    P = Vector((P0[0], P0[1], 0))
    tb = Vector((T[0] - P0[0], T[1] - P0[1], 0)).normalized()

    def clear(q):  # keep the sight line to the temple open
        v = (q - P).normalized()
        return v.dot(tb) < math.cos(math.radians(14))

    for off, sc in ((fwd * 60 - right * 30, 1.0),):
        q = P + off
        A.inst(olive_hi, (q.x, q.y, h(q.x, q.y) - 0.2), yaw=R.uniform(0, 6.3), scale=sc)
    for k in range(2):
        q = P + fwd * R.uniform(9, 14) + right * R.uniform(-9, -6)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32,
            radius=1.2,
            depth=R.uniform(1.2, 1.7),
            location=(q.x, q.y, h(q.x, q.y) + 0.8),
            rotation=(math.pi / 2, 0, R.uniform(0, 6.28)),
        )
        bpy.context.active_object.data.materials.append(marble)
    for k in range(12):
        q = P + fwd * (6 + k * 2.3) - right * (4.5 + 0.12 * k + R.uniform(-0.15, 0.15))
        hh = R.uniform(0.5, 1.5) if k not in (4, 5, 9) else 0.25
        B.cube(
            "wall",
            (1.1, 2.25, hh),
            (q.x, q.y, h(q.x, q.y) + hh / 2 - 0.15),
            stone,
            rot_z=math.atan2(-fwd.x, fwd.y),
            bevel=0.06,
        )
    # dry grass and rocks round the player
    for _ in range(9000):
        q = P + fwd * R.uniform(-3, 45) + right * R.uniform(-28, 28)
        if (q - P).length < 1.2:
            continue
        A.inst(
            grass, (q.x, q.y, h(q.x, q.y) - 0.03), yaw=R.uniform(0, 6.3), scale=R.uniform(0.5, 1.1)
        )
    for _ in range(420):
        q = P + fwd * R.uniform(6, 90) + right * R.uniform(-45, 45)
        if (q - P).dot(right) < -8 or not clear(q):  # far left stays open over the bay
            continue
        A.inst(
            R.choice(shrubs),
            (q.x, q.y, h(q.x, q.y) - 0.1),
            yaw=R.uniform(0, 6.3),
            scale=R.uniform(0.7, 1.4),
        )
    for _ in range(40):
        q = P + fwd * R.uniform(3, 60) + right * R.uniform(-35, 35)
        A.inst(
            rocks, (q.x, q.y, h(q.x, q.y) - 0.3), yaw=R.uniform(0, 6.3), scale=R.uniform(0.15, 0.6)
        )
    print("VEG", n)


def player_and_camera():
    import wf_mh as M

    P = Vector((P0[0], P0[1], h(*P0)))
    yaw = math.degrees(math.atan2(-VIEW[0], VIEW[1]))
    M.character("explorer", "stand_look", loc=tuple(P), yaw_deg=yaw)
    fwd = Vector((VIEW[0], VIEW[1], 0))
    right = Vector((fwd.y, -fwd.x, 0))
    cam = P - fwd * 4.2 + right * 2.5 + Vector((0, 0, 2.0))
    tgt = cam + fwd * 100 + Vector((0, 0, 100 * math.tan(math.radians(PITCH))))
    return A.camera(cam, tgt, lens=24, dof=((P - cam).length, 5.6))


def main():
    import time

    t0 = time.time()
    A.reset()
    A.eevee(
        samples=SAMPLES,
        res=(int(1920 * SCALE), int(1080 * SCALE)),
        exposure=float(os.environ.get("WF_EXPOSURE", 0.0)),
    )
    if hasattr(bpy.context.scene.eevee, "ray_tracing_method"):
        bpy.context.scene.eevee.ray_tracing_method = "SCREEN"
    # afternoon sun from the south-west: side light across the bay, sun behind the camera's left shoulder
    w, nt, env, el = A.world_hdri_sun(
        "kloofendal_48d_partly_cloudy_puresky_4k.hdr",
        float(os.environ.get("WF_SUN_AZ", 205.0)),
        strength=1.0,
    )
    for attr, val in (
        ("sun_threshold", 10.0),
        ("sun_angle", math.radians(1.0)),
        ("use_sun_shadow", True),
        ("sun_shadow_maximum_resolution", 0.002),
    ):
        if hasattr(w, attr):
            setattr(w, attr, val)
    terrain()
    sea()
    temple()
    colossus()
    vegetation()
    player_and_camera()
    # aerial perspective (10-10 b): stronger blue-grey with distance so headlands separate into layers
    A.compositor_fog(
        (0.62, 0.74, 0.90),
        float(os.environ.get("WF_FOG_START", 250)),
        5200,
        float(os.environ.get("WF_FOG_MAX", 0.36)),
        sky_haze=0.04,
        vignette=0.12,
        haze_power=float(os.environ.get("WF_FOG_POW", 1.4)),
    )
    print("BUILD", round(time.time() - t0, 1))
    bpy.ops.wm.save_as_mainfile(filepath=str(A.BUILD / f"arch_{VARIANT}.blend"))
    if "--norender" not in argv:
        A.render(OUT)


main()
