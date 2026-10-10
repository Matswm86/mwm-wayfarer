"""Key frame 3: R3 Redwall Oasis (desert canyon trade oasis).

Real relief: a valley in Wadi Rum, Jordan, Copernicus GLO-30 elevation (see assets/_raw/dem/cop30/SOURCE.md for
licence and the required notice), resampled by tools/terrain/cop_to_game.py wadirum. Frame: metres, +X east,
+Y north, heights relative to the valley floor at the player.
A spring pool with date palms at the foot of the sunlit east wall, market stalls with striped awnings, traders and
cargo on the sand floor, a carved temple front cut into the wall further up the valley.

BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user \
flock ~/MWM/scratch/wayfarer/render.lock blender -b --factory-startup -P tools/art/scene_canyon.py -- key <out.png> [scale] [samples]
Env for look-dev: WF_YAW (view bearing, deg from north), WF_PITCH, WF_EXPOSURE, WF_SUN_AZ.
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
R = A.rng(23)

DEM = A.dem_sampler(A.RAW / "dem" / "wadirum_game.npz")
P0 = (42.0, 604.0)  # player on the valley floor, in front of the amphitheatre in the east wall
Z0 = DEM(*P0)
POOL = (92.0, 690.0, 13.0)  # spring pool at the foot of the east wall
FACADE_Y = 930.0
YAW = float(os.environ.get("WF_YAW", 40.0))
PITCH = float(os.environ.get("WF_PITCH", 7.0))
VIEW = (math.sin(math.radians(YAW)), math.cos(math.radians(YAW)))


def dz(x, y):
    return DEM(x, y) - Z0


def grad(x, y, e=10.0):
    return math.hypot(DEM(x + e, y) - DEM(x - e, y), DEM(x, y + e) - DEM(x, y - e)) / (2 * e)


def h_base(x, y):
    z = dz(x, y)
    s = grad(x, y)
    rock = B.smoothstep(0.35, 0.8, s)
    # sandstone strata: the real 30 m relief gets 6 m ledges where it is steep (cross-bedded benches)
    if rock > 0:
        st = 9.0 + 3.0 * B.fbm(x / 300, y / 300, 2)
        zw = z + 4.0 * B.fbm(
            x / 60, y / 60, 3
        )  # warp the bedding so ledges wander instead of ringing the hill
        k = zw / st
        fr = k - math.floor(k)
        zs = st * (math.floor(k) + B.smoothstep(0.1, 0.9, fr) ** 0.7) - (zw - z)
        z = z * (1 - 0.35 * rock) + zs * 0.35 * rock
        z += rock * (1.6 * B.fbm(x / 22, y / 22, 4) + 0.8 * B.ridged(x / 7, y / 9, 3))
    # sand floor: soft drifts, rippled near the walls
    z += (1 - rock) * (0.9 * B.fbm(x / 70, y / 28, 3) + 0.25 * B.fbm(x / 9, y / 9, 3))
    # pool hollow
    d = math.hypot(x - POOL[0], (y - POOL[1]) * 1.3)
    z -= 1.8 * math.exp(-((d / POOL[2]) ** 4))
    # level stand for the player
    dd = math.hypot(x - P0[0], y - P0[1])
    k = math.exp(-((dd / 12.0) ** 2))
    return z * (1 - k) + 0.2 * k


def _toe(y, rise, x):
    lo = h_base(x, y)
    while x < P0[0] + 900:
        z = h_base(x, y)
        lo = min(lo, z)
        if z - lo >= rise:
            break
        x += 2.0
    return x, lo


X_FACE, Z_FACE = _toe(FACADE_Y, 8.0, P0[0])
X_FACE -= 3.0
FACE_H = 52.0


def h(x, y):
    """Terrain plus a rock spur whose west side is cut vertical: the cliff the temple front is carved into."""
    z = h_base(x, y)
    dy = abs(y - FACADE_Y)
    if dy < 80 and x > X_FACE - 4:
        w = 1.0 - B.smoothstep(42, 80, dy)
        top = (
            Z_FACE
            + FACE_H * w * (1 + 0.08 * B.fbm(x / 25, y / 25, 3))
            + 3.0 * B.ridged(x / 9, y / 9, 3) * w
        )
        cut = B.smoothstep(X_FACE - 2.5, X_FACE, x)
        z = max(z, Z_FACE + (top - Z_FACE) * cut)
    return z


def terrain():
    layers = dict(
        flat=("red_sand", 4.0, (1.3, 0.98, 0.78)),
        patch=("aerial_sand", 9.0, (1.12, 0.84, 0.62)),
        steep=("cliff_side", 42.0, (1.05, 0.9, 0.82)),
        high=("rock_boulder_cracked", 14.0, (1.0, 0.86, 0.76)),
    )
    m = A.terrain_mat(
        "canyon_terrain",
        layers,
        slope=(0.68, 0.86),
        height=(90, 140),
        macro=0.01,
        macro_amp=(0.82, 1.12),
        box_all=True,
        patch=(0.025, 0.4, 0.62),
    )
    A.grid_mesh("terrain_near", h, -200, 700, 450, 1250, 450, 400, m)  # 2 m cells round the oasis

    def hmid(x, y):
        d = max(-200 - x, x - 700, 450 - y, y - 1250)
        return h(x, y) - 1.5 * (1 - B.smoothstep(-8, 0, d))

    A.grid_mesh("terrain_mid", hmid, -1700, 1700, -300, 3600, 567, 650, m)
    A.grid_mesh("terrain_far", lambda x, y: dz(x, y) - 2.0, -5000, 5000, -4000, 8000, 333, 400, m)


def pool():
    m = A.water_mat(
        "oasis",
        A.hexc("#123F3A"),
        A.hexc("#4E9A86"),
        rough=0.02,
        wave_scale=0.4,
        wave_strength=0.05,
    )
    zc = h(POOL[0], POOL[1]) + 1.5
    bpy.ops.mesh.primitive_circle_add(
        vertices=96, radius=POOL[2] * 1.15, fill_type="NGON", location=(POOL[0], POOL[1], zc)
    )
    o = bpy.context.active_object
    o.scale = (1.0, 1 / 1.3, 1)
    o.data.materials.append(m)
    reeds = A.proto("grass_medium_01", tint_rgb=(0.85, 1.0, 0.7))
    for _ in range(260):
        a = R.uniform(0, 6.28)
        rr = POOL[2] * R.uniform(0.95, 1.3)
        x, y = POOL[0] + math.cos(a) * rr, POOL[1] + math.sin(a) * rr / 1.3
        A.inst(reeds, (x, y, h(x, y)), yaw=R.uniform(0, 6.3), scale=R.uniform(1.0, 1.9))
    return zc


def palms():
    spots = []
    for i in range(18):
        a = 2 * math.pi * i / 18 + R.uniform(-0.15, 0.15)
        rr = POOL[2] * R.uniform(1.35, 2.6)
        spots.append((POOL[0] + math.cos(a) * rr, POOL[1] + math.sin(a) * rr / 1.2))
    # a ribbon of palms along the wall toe, where the spring water seeps out
    for k in range(26):
        y = POOL[1] + R.uniform(-120, 330)
        x = POOL[0] + 15 + R.uniform(-30, 40) + 0.25 * (y - POOL[1])
        if grad(x, y) < 0.35:
            spots.append((x, y))
    # three palms framing the left foreground
    for fx, fy in ((-14.0, 26.0), (-20.0, 40.0), (-11.0, 52.0)):
        spots.append(
            (P0[0] + VIEW[1] * fx + VIEW[0] * fy, P0[1] - VIEW[0] * fx + VIEW[1] * fy)
        )  # P0 + right*fx + fwd*fy
    for i, (x, y) in enumerate(spots):
        B.palm(
            (x, y, h(x, y) - 0.1),
            height=R.uniform(8, 16),
            lean=(R.uniform(-0.12, 0.12), R.uniform(-0.12, 0.12)),
            seed=i,
            nfr=26,
            frond_w=1.7,
        )
    # date-palm trunks are warm grey-brown, the shared bark scan is pale
    m = bpy.data.materials.get("palm_bark")
    if m is not None:
        b = A.bsdf(m)
        if b.inputs["Base Color"].is_linked:
            src = b.inputs["Base Color"].links[0].from_socket
            m.node_tree.links.new(
                A.tint(m.node_tree, src, (0.72, 0.58, 0.46)), b.inputs["Base Color"]
            )
    print("PALMS", len(spots))


def market():
    cloths = [
        B.stripe_mat("aw_red", A.hexc("#A8322A"), A.hexc("#E8DCC4"), 9),
        B.stripe_mat("aw_saffron", A.hexc("#D9932B"), A.hexc("#F0E6D2"), 7),
        B.stripe_mat("aw_indigo", A.hexc("#24476E"), A.hexc("#E6DCC8"), 10),
        B.stripe_mat("aw_madder", A.hexc("#7E2F24"), A.hexc("#C9A27A"), 6),
    ]
    # two rows of stalls lining the path from the player toward the pool
    fwd = Vector((POOL[0] - P0[0], POOL[1] - P0[1], 0)).normalized()
    side = Vector((fwd.y, -fwd.x, 0))
    yaw_path = math.atan2(-fwd.x, fwd.y)
    stalls = []
    for k in range(5):
        for sgn in (-1, 1):
            if sgn == 1 and k in (0, 3):
                continue
            c = (
                Vector((P0[0], P0[1], 0))
                + fwd * (16 + k * 11 + (4 if sgn > 0 else 0))
                + side * sgn * 9.0
            )
            stalls.append(
                (c.x, c.y, yaw_path + (math.pi / 2 if sgn < 0 else -math.pi / 2) * 0.45 + math.pi)
            )  # half-turned to the arriving player
    for i, (x, y, yaw) in enumerate(stalls):
        B.stall((x, y, h(x, y) - 0.05), yaw, w=4.2, d=3.0, hgt=2.5, cloth=cloths[i % 4], seed=i)
    goods = [
        A.proto(n)
        for n in (
            "ceramic_vase_01",
            "ceramic_vase_03",
            "antique_ceramic_vase_01",
            "brass_pot_01",
            "brass_vase_02",
            "wicker_basket_01",
            "wicker_basket_02",
        )
    ]
    heavy = [A.proto(n) for n in ("wooden_crate_01", "wooden_crate_02", "Barrel_01")]
    for x, y, yaw in stalls:
        f = Vector((math.sin(-yaw), math.cos(yaw), 0))
        for _ in range(6):
            g = (
                Vector((x, y, 0))
                + f * R.uniform(1.6, 2.8)
                + Vector((f.y, -f.x, 0)) * R.uniform(-1.8, 1.8)
            )
            A.inst(
                R.choice(goods),
                (g.x, g.y, h(g.x, g.y)),
                yaw=R.uniform(0, 6.3),
                scale=R.uniform(0.9, 1.4),
            )
        for _ in range(2):
            g = (
                Vector((x, y, 0))
                - f * R.uniform(0.5, 2.0)
                + Vector((f.y, -f.x, 0)) * R.uniform(-2.0, 2.0)
            )
            A.inst(R.choice(heavy), (g.x, g.y, h(g.x, g.y)), yaw=R.uniform(0, 6.3))
    # caravan cargo by the path: crates and barrels
    cx, cy = (
        P0[0] + VIEW[1] * 15 + VIEW[0] * 24,
        P0[1] - VIEW[0] * 15 + VIEW[1] * 24,
    )  # right of the path
    for k in range(18):
        gx, gy = cx + R.uniform(-3, 4), cy + R.uniform(-3, 4)
        A.inst(
            R.choice(heavy), (gx, gy, h(gx, gy) + (1.0 if k > 12 else 0)), yaw=R.uniform(-0.3, 0.3)
        )
    return stalls


def wall_toe(y, rise=18.0, x=None):
    """First x east of x (default the player) where the ground has risen `rise` metres above the lowest floor so far."""
    x = P0[0] if x is None else x
    lo = h(x, y)
    while x < P0[0] + 900:
        z = h(x, y)
        lo = min(lo, z)
        if z - lo >= rise:
            break
        x += 2.0
    return x


def facade(F=1.7):
    """Carved temple front cut into the east wall (lost-age wonder hint), ~45 m tall like the Treasury at Petra,
    on a rock buttress (terrain material) so it stands vertical against the sloping wall."""
    stone = A.pbr(
        "facade", "cliff_side", 0.05, coords="Object", box=True, tint_rgb=(1.12, 0.94, 0.84)
    )
    y = FACADE_Y
    x = X_FACE - 2.6
    zb = Z_FACE - 0.5
    objs = []
    for i in range(6):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24,
            radius=1.3 * F,
            depth=16 * F,
            location=(x - 1.5 * F, y + (-14 + i * 5.6) * F, zb + 9 * F),
        )
        c = bpy.context.active_object
        c.data.materials.append(stone)
        objs.append(c)
    objs.append(
        B.cube(
            "entab", (3.4 * F, 36 * F, 3.2 * F), (x - 1.5 * F, y, zb + 18.6 * F), stone, bevel=0.2
        )
    )
    pd = B._obj(
        "ped",
        [
            (x - 1.5 * F, y - 18 * F, zb + 20.2 * F),
            (x - 1.5 * F, y + 18 * F, zb + 20.2 * F),
            (x - 1.5 * F, y, zb + 26.5 * F),
        ],
        [(0, 1, 2)],
        stone,
        uv_fn=B.box_uv,
    )
    pd.modifiers.new("s", "SOLIDIFY").thickness = 2.4 * F
    objs.append(pd)
    dark = A.flat_mat("dark", (0.025, 0.015, 0.01, 1), 0.95)
    objs.append(B.cube("door", (1.6, 5.5 * F, 9 * F), (x + 2.2, y, zb + 5.5 * F), dark))
    objs.append(B.cube("base", (6 * F, 40 * F, 1.6 * F), (x - 1.0 * F, y, zb + 0.3 * F), stone))
    # cliff dwellings: small dark doorways and ledges cut into the wall on either side
    for k in range(9):
        yy = y + R.choice((-1, 1)) * R.uniform(60, 190)
        zz = R.uniform(6, 30)
        xx = wall_toe(yy, zz, x - 40)
        zc = h(xx, yy)
        objs.append(B.cube("cave", (2.0, 1.6, 2.2), (xx - 0.4, yy, zc + 1.1), dark))
        objs.append(B.cube("sill", (2.0, 3.4, 0.4), (xx - 1.0, yy, zc - 0.1), stone))
    return objs


def people(stalls):
    import wf_mh as M

    x, y, yaw = stalls[1]
    M.character("trader", "vend", loc=(x, y, h(x, y)), yaw_deg=math.degrees(yaw))
    x, y, yaw = stalls[4]
    M.character("trader", "talk", loc=(x + 1.0, y, h(x + 1.0, y)), yaw_deg=math.degrees(yaw) + 30)
    fx, fy = P0[0] + 6, P0[1] + 62
    M.character("fisher", "walk", loc=(fx, fy, h(fx, fy)), yaw_deg=170, gear=False)


def player_and_camera():
    import wf_mh as M

    P = Vector((P0[0], P0[1], h(*P0)))
    yaw = math.degrees(math.atan2(-VIEW[0], VIEW[1]))
    M.character("explorer", "walk", loc=tuple(P), yaw_deg=yaw)
    fwd = Vector((VIEW[0], VIEW[1], 0))
    right = Vector((fwd.y, -fwd.x, 0))
    cam = P - fwd * 4.2 + right * 1.4 + Vector((0, 0, 2.0))
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
    # clear midday-afternoon sky, sun 43 deg from the west-south-west: lights the west-facing east wall and the floor
    w, nt, env, el = A.world_hdri_sun(
        "kloofendal_43d_clear_puresky_4k.hdr",
        float(os.environ.get("WF_SUN_AZ", 245.0)),
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
    pool()
    palms()
    stalls = market()
    facade()
    people(stalls)
    player_and_camera()
    A.compositor_fog(
        (0.86, 0.74, 0.62), 200, 3000, 0.28, sky_haze=0.06, vignette=0.12, haze_power=2.0
    )
    print("BUILD", round(time.time() - t0, 1))
    bpy.ops.wm.save_as_mainfile(filepath=str(A.BUILD / f"canyon_{VARIANT}.blend"))
    if "--norender" not in argv:
        A.render(OUT)


main()
