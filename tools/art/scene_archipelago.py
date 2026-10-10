"""Key frame 2: Mediterranean lost-age archipelago. A colossal ruined temple on a white limestone headland (the
wonder), a giant marble head sunk in the shallows, turquoise bay, olive trees, player over-the-shoulder.

BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user \
blender -b --factory-startup -P tools/art/scene_archipelago.py -- <variant key|card> <out.png> [scale] [samples]
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import wf_art as A  # noqa: E402
import wf_build as B  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
VARIANT = argv[0]
OUT = argv[1]
SCALE = float(argv[2]) if len(argv) > 2 else 1.0
SAMPLES = int(argv[3]) if len(argv) > 3 else 64
R = A.rng(11)

P0 = (0.0, 0.0, 38.0)  # player
HEAD = (-60.0, 330.0)  # headland with the temple (top ~52 m)
VIEW = (-0.17, 0.985)


def land(x, y):
    """Signed land height before cliffs: sum of island blobs."""
    def blob(cx, cy, rx, ry, hh, rot=0.0):
        dx, dy = x - cx, y - cy
        c, s = math.cos(rot), math.sin(rot)
        u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
        return hh * math.exp(-(u * u + v * v) ** 1.2)

    z = -30.0
    z = max(z, blob(30, -40, 170, 140, 70))  # player's hill
    z = max(z, blob(HEAD[0], HEAD[1], 120, 70, 82, 0.5))  # temple headland
    z = max(z, blob(-260, 420, 160, 120, 60))  # ridge behind the headland
    z = max(z, blob(380, 520, 120, 90, 48))  # island right
    z = max(z, blob(-700, 1400, 380, 220, 140))  # far island left
    z = max(z, blob(600, 1900, 420, 200, 120))  # far island right
    z = max(z, blob(-50, 2600, 600, 260, 160))  # far horizon island
    z = max(z, blob(250, 1100, 90, 60, 30))  # islet
    return z


def h(x, y):
    z = land(x, y)
    n = B.fbm(x / 120, y / 120)
    # limestone: steepen the shore into cliffs (terrace curve) and add karst noise
    if z > -2:
        t = min(1.0, (z + 2) / 18.0)
        z = z + 14 * (t ** 0.35 - t) + n * 6 * t + 4 * B.ridged(x / 35, y / 35, 3) * t
    else:
        z = z + n * 3
    # flat top for the temple platform
    dx, dy = x - HEAD[0], y - HEAD[1]
    k = math.exp(-((dx * dx / (55.0**2)) + (dy * dy / (40.0**2))) ** 2)
    z = z * (1 - k) + 54.0 * k
    # player knoll
    dx, dy = x - P0[0], y - P0[1]
    k = math.exp(-((dx * dx + dy * dy) / (40.0**2)))
    along = dx * VIEW[0] + dy * VIEW[1]
    zk = P0[2] - 0.12 * max(0.0, along) + 0.05 * (dx * VIEW[1] - dy * VIEW[0])
    return z * (1 - k) + zk * k


def terrain():
    layers = dict(
        flat=("dry_ground_rocks", 6.0, (1.05, 1.0, 0.9)),
        steep=("marble_cliff_02", 22.0, (1.08, 1.05, 0.98)),
        high=("aerial_rocks_02", 30.0, (1.0, 0.98, 0.92)),
        low=("coast_sand_01", 5.0, (1.1, 1.05, 0.95)),
    )
    m = A.terrain_mat("arch_terrain", layers, slope=(0.55, 0.8), height=(9000, 9100), macro=0.01, macro_amp=(0.82, 1.1), extra=(0.5, 3.5, 2.0))
    A.grid_mesh("terrain_mid", h, -900, 900, -200, 1200, 420, 330, m)
    A.grid_mesh("terrain_far", lambda x, y: h(x, y) - 1.5, -5000, 5000, -3000, 9000, 250, 300, m)
    return m


def water():
    """Grid water: vertex colour = depth under the surface (shallow turquoise over sand, deep blue)."""
    mat = bpy.data.materials.new("sea")
    mat.use_nodes = True
    nt = mat.node_tree
    b = A.bsdf(mat)
    va = nt.nodes.new("ShaderNodeVertexColor")
    va.layer_name = "depth"
    dep = va.outputs["Color"]
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(dep, sep.inputs["Color"])
    d = sep.outputs["Red"]
    c1 = A.mixc(nt, A.maprange(nt, d, 0.0, 0.18), A.hexc("#7FE0D2"), A.hexc("#1FB3B0"))
    c2 = A.mixc(nt, A.maprange(nt, d, 0.18, 0.6), c1, A.hexc("#0B6E8C"))
    c3 = A.mixc(nt, A.maprange(nt, d, 0.6, 1.0), c2, A.hexc("#06395E"))
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.2
    col = A.mixc(nt, A.math_node(nt, "MULTIPLY", lw.outputs["Facing"], 0.35), c3, A.hexc("#0A3150"))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.06
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n2 = A.noise(nt, 0.35, tc.outputs["Object"], detail=8, rough=0.6)
    w1 = nt.nodes.new("ShaderNodeTexWave")
    w1.inputs["Scale"].default_value = 0.05
    w1.inputs["Distortion"].default_value = 6
    nt.links.new(tc.outputs["Object"], w1.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.3
    nt.links.new(A.math_node(nt, "ADD", n2, A.math_node(nt, "MULTIPLY", w1.outputs["Fac"], 0.3)), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # foam line where depth ~0
    foam = A.maprange(nt, d, 0.012, 0.0)
    fn = A.maprange(nt, A.noise(nt, 1.2, tc.outputs["Object"], detail=4), 0.45, 0.65)
    fm = A.math_node(nt, "MULTIPLY", foam, fn)
    col2 = A.mixc(nt, fm, col, (0.92, 0.95, 0.95, 1))
    nt.links.new(col2, b.inputs["Base Color"])
    o = A.grid_mesh("sea", lambda x, y: 0.0, -1500, 1500, -300, 3200, 300, 350, mat)
    ca = o.data.color_attributes.new("depth", "FLOAT_COLOR", "POINT")
    for i, v in enumerate(o.data.vertices):
        dd = max(0.0, -h(v.co.x, v.co.y)) / 30.0
        dd = min(1.0, dd)
        ca.data[i].color = (dd, dd, dd, 1)
    far = A.grid_mesh("sea_far", lambda x, y: -0.05, -9000, 9000, -6000, 14000, 10, 10, A.water_mat("sea_far_m", A.hexc("#06395E"), A.hexc("#0B5A7C"), rough=0.06, wave_scale=0.02, wave_strength=0.15))
    return o


# ---------------------------------------------------------------- temple
def column(name, base, height, radius, mat, broken=None, seed=0):
    """Fluted Doric column with entasis; broken=None or the height of the break (jagged top)."""
    seg, rings = 40, 24
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
                jag = (0.6 * math.sin(a * 3 + seed) + 0.4 * math.sin(a * 7 + seed * 2)) * radius * 0.5
            verts.append((r * fl * math.cos(a), r * fl * math.sin(a), z + jag))
    for j in range(rings):
        for i in range(seg):
            a = j * seg + i
            b2 = j * seg + (i + 1) % seg
            faces.append((a, b2, b2 + seg, a + seg))
    top = list(range(rings * seg, rings * seg + seg))
    faces.append(tuple(top))
    o = B._obj(name, verts, faces, mat, smooth=True, uv_fn=lambda co, n: (math.atan2(co.y, co.x) * radius, co.z))
    objs = [o]
    if broken is None:
        # echinus + abacus capital
        bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=radius * 1.12, depth=radius * 0.45, location=(0, 0, height + radius * 0.2))
        e = bpy.context.active_object
        e.data.materials.append(mat)
        objs.append(e)
        objs.append(B.cube("abacus", (radius * 2.6, radius * 2.6, radius * 0.4), (0, 0, height + radius * 0.62), mat))
    root = bpy.data.objects.new(name, None)
    A.link(root)
    for x in objs:
        x.parent = root
    root.location = base
    return root


def temple():
    marble = A.pbr("temple_marble", "marble_cliff_04", 0.25, coords="Object", box=True, tint_rgb=(1.12, 1.07, 0.98))
    stone = A.pbr("temple_blocks", "white_sandstone_blocks_02", 0.35, coords="Object", box=True, tint_rgb=(1.05, 1.0, 0.92))
    cx, cy = HEAD
    rot = math.radians(-22)
    zc = 54.0
    ncol_x, ncol_y = 8, 15
    sp = 7.2
    rad = 1.45
    colh = 21.0
    W = (ncol_x - 1) * sp
    L = (ncol_y - 1) * sp
    objs = []
    for k, (gx, gy, gz) in enumerate(((W + 10, L + 10, 1.2), (W + 7, L + 7, 1.2), (W + 4, L + 4, 1.2))):
        objs.append(B.cube(f"step{k}", (gx, gy, gz), (0, 0, k * 1.2 + 0.6 - 1.0), stone, bevel=0.15))
    base_z = 3 * 1.2 - 1.0
    r = A.rng(5)
    cols = []
    for i in range(ncol_x):
        for j in range(ncol_y):
            if 0 < i < ncol_x - 1 and 0 < j < ncol_y - 1:
                continue
            x = -W / 2 + i * sp
            y = -L / 2 + j * sp
            # collapse pattern: the seaward (low j) end and one long side mostly fallen
            keep = r.random()
            standing = (j >= 5 and (i == 0 or j >= 8)) or (i == 0 and j >= 3)
            if standing and keep > 0.15:
                c = column(f"col{i}_{j}", (x, y, base_z), colh, rad, marble)
            elif keep > 0.35:
                c = column(f"col{i}_{j}", (x, y, base_z), colh, rad, marble, broken=r.uniform(2.0, 12.0), seed=i + j)
            else:
                continue
            cols.append((i, j, c))
            objs.append(c)
    # architrave + frieze on runs of standing full columns
    full = {(i, j) for i, j, c in cols if c.children and len(c.children) > 1}
    for i in (0, ncol_x - 1):
        for j in range(ncol_y - 1):
            if (i, j) in full and (i, j + 1) in full:
                x = -W / 2 + i * sp
                y = -L / 2 + (j + 0.5) * sp
                objs.append(B.cube("arch", (rad * 2.4, sp + 0.2, 2.0), (x, y, base_z + colh + rad * 0.82 + 1.0), stone, bevel=0.06))
                objs.append(B.cube("frieze", (rad * 2.2, sp + 0.2, 1.8), (x, y, base_z + colh + rad * 0.82 + 2.9), marble, bevel=0.05))
    for j in (ncol_y - 1,):
        for i in range(ncol_x - 1):
            if (i, j) in full and (i + 1, j) in full:
                x = -W / 2 + (i + 0.5) * sp
                y = -L / 2 + j * sp
                objs.append(B.cube("arch", (sp + 0.2, rad * 2.4, 2.0), (x, y, base_z + colh + rad * 0.82 + 1.0), stone, bevel=0.06))
                objs.append(B.cube("frieze", (sp + 0.2, rad * 2.2, 1.8), (x, y, base_z + colh + rad * 0.82 + 2.9), marble, bevel=0.05))
    # pediment remnant on the landward end
    yb = -L / 2 + (ncol_y - 1) * sp
    v = [(-W / 2 - 1.5, yb, 0), (W / 2 + 1.5, yb, 0), (0, yb, 6.5)]
    pd = B._obj("pediment", v, [(0, 1, 2)], marble, uv_fn=B.box_uv)
    pd.location = (0, 0, base_z + colh + rad * 0.82 + 3.8)
    pd.modifiers.new("s", "SOLIDIFY").thickness = 2.0
    objs.append(pd)
    # fallen drums on the platform and down the slope
    for k in range(26):
        a = r.uniform(0, 6.28)
        rr = r.uniform(0.0, 1.0)
        x = r.uniform(-W / 2 - 6, W / 2 + 6)
        y = r.uniform(-L / 2 - 14, -L / 2 + 20)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=rad * r.uniform(0.9, 1.05), depth=r.uniform(1.6, 2.4), location=(x, y, base_z + rad * 0.9), rotation=(math.pi / 2, 0, a))
        d = bpy.context.active_object
        d.data.materials.append(marble)
        objs.append(d)
    root = bpy.data.objects.new("temple", None)
    A.link(root)
    for o in objs:
        o.parent = root
    root.location = (cx, cy, zc)
    root.rotation_euler = (0, 0, rot)
    return root


def colossus():
    """Giant marble head (Poly Haven marble_bust_01 at ~45x) half sunk in the shallows below the headland."""
    c = A.proto("marble_bust_01", tint_rgb=(1.05, 1.02, 0.96))
    sz = A.proto_size(c)
    s = 22.0 / sz.z
    e = A.inst(c, (HEAD[0] + 105, HEAD[1] - 95, -9.0), yaw=math.radians(205), scale=s, tilt=(math.radians(-14), math.radians(18)))
    return e


def vegetation():
    olive = A.proto("tree_small_02", hue=(0.5, 0.55, 0.95), tint_rgb=(0.85, 0.92, 0.82))
    shrubs = [A.proto("shrub_04"), A.proto("searsia_lucida")]
    olive_imp = A.impostor(olive, 512, name="imp_olive")
    pine_imp = A.impostor(A.proto_variants("pine_tree_01")[0], 512, name="imp_pine_med", tint=(0.85, 0.95, 0.8))
    grass = [A.proto("grass_medium_02", tint_rgb=(1.1, 0.95, 0.6))]
    rocks = A.proto("boulder_01", tint_rgb=(1.1, 1.08, 1.0))
    n = 0
    for _ in range(3500):
        x = R.uniform(-700, 700)
        y = R.uniform(-150, 900)
        z = h(x, y)
        if z < 4 or z > 140:
            continue
        nx = (h(x + 2, y) - h(x - 2, y)) / 4
        ny = (h(x, y + 2) - h(x, y - 2)) / 4
        if math.hypot(nx, ny) > 0.7:
            continue
        dx, dy = x - HEAD[0], y - HEAD[1]
        if (dx * dx / 70**2 + dy * dy / 60**2) < 1.0:
            continue
        d = math.hypot(x - P0[0], y - P0[1])
        if d < 6:
            continue
        rr = R.random()
        if d < 45:
            c = olive if rr < 0.3 else R.choice(shrubs)
        else:
            c = olive_imp if rr < 0.45 else (pine_imp if rr < 0.6 else R.choice(shrubs))
        A.inst(c, (x, y, z - 0.2), yaw=R.uniform(0, 6.3), scale=R.uniform(0.7, 1.2) * (1.0 if c not in shrubs else 1.4))
        n += 1
    for _ in range(1300):
        x = P0[0] + R.uniform(-30, 30)
        y = P0[1] + R.uniform(-5, 60)
        if abs(x - (P0[0] + 0.8 - 0.1 * (y - P0[1]))) < 1.1:
            continue
        A.inst(grass[0], (x, y, h(x, y) - 0.03), yaw=R.uniform(0, 6.3), scale=R.uniform(0.6, 1.1))
    for _ in range(24):
        x = P0[0] + R.uniform(-30, 30)
        y = P0[1] + R.uniform(-5, 50)
        A.inst(rocks, (x, y, h(x, y) - 0.4), yaw=R.uniform(0, 6.3), scale=R.uniform(0.15, 0.5))
    print("VEG", n)


def player_and_camera():
    import wf_mh as M

    P = Vector((P0[0], P0[1], h(P0[0], P0[1])))
    yaw = math.degrees(math.atan2(-VIEW[0], VIEW[1]))
    M.character("explorer", "stand_look", loc=tuple(P), yaw_deg=yaw)
    fwd = Vector((VIEW[0], VIEW[1], 0))
    right = Vector((fwd.y, -fwd.x, 0))
    cam = P - fwd * 4.0 + right * 1.3 + Vector((0, 0, 2.1))
    tgt = Vector((HEAD[0], HEAD[1], 50.0)) + right * 40
    return A.camera(cam, tgt, lens=27, dof=((P - cam).length, 5.6))


def main():
    import time

    t0 = time.time()
    A.reset()
    A.eevee(samples=SAMPLES, res=(int(1920 * SCALE), int(1080 * SCALE)), exposure=-0.35)
    w, nt, env = A.world_hdri("kloofendal_48d_partly_cloudy_puresky_4k.hdr", 95, strength=1.0)
    for attr, val in (("sun_threshold", 10.0), ("sun_angle", math.radians(1.0)), ("use_sun_shadow", True), ("sun_shadow_maximum_resolution", 0.002)):
        if hasattr(w, attr):
            setattr(w, attr, val)
    terrain()
    water()
    temple()
    colossus()
    vegetation()
    player_and_camera()
    A.compositor_fog((0.72, 0.80, 0.86), 120, 3500, 0.55, sky_haze=0.05, vignette=0.15, haze_power=2.0)
    print("BUILD", round(time.time() - t0, 1))
    bpy.ops.wm.save_as_mainfile(filepath=str(A.BUILD / f"arch_{VARIANT}.blend"))
    if "--norender" not in argv:
        A.render(OUT)


main()
