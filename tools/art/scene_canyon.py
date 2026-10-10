"""Key frame 3: desert canyon trade oasis. Red sandstone walls in strata, a spring pool with date palms, market
stalls with striped awnings, traders and cargo, warm haze, a carved facade far up the canyon.

BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user \
blender -b --factory-startup -P tools/art/scene_canyon.py -- <variant key> <out.png> [scale] [samples]
"""

from __future__ import annotations

import math
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
R = A.rng(23)
P0 = (-6.0, -22.0)
POOL = (16.0, 40.0, 11.0)


def cx(y):
    return 8 * math.sin(y / 60) + (0.0025 * (y - 150) ** 2 if y > 150 else 0.0)


def hw(y):
    return 36 - 16 * B.smoothstep(90, 220, y) + 10 * B.smoothstep(-40, -120, y)


def h(x, y):
    e = abs(x - cx(y)) - hw(y) + 7 * B.fbm(y / 45, x / 45)
    fl = 0.35 * B.fbm(x / 14, y / 14) + 0.6 * B.fbm(x / 40, y / 40)
    if e <= 0:
        z = fl + 0.03 * max(0, -e - 10) * 0  # flat floor
        z += 1.2 * B.smoothstep(-6, 0, e)  # talus toe
    else:
        r = e * 2.8 + 4 * B.fbm(x / 20, y / 20)
        step = 8.5
        k = r / step
        fr = k - math.floor(k)
        z = fl + 1.2 + step * (math.floor(k) + min(1.0, fr / 0.72))
        z = min(z, 150 + 25 * B.fbm(x / 120, y / 120)) + 3 * B.ridged(x / 12, y / 30, 3)
    # pool hollow
    dx, dy = x - POOL[0], y - POOL[1]
    d = math.hypot(dx, dy * 1.3)
    z -= 1.6 * math.exp(-((d / POOL[2]) ** 4))
    return z


def terrain():
    layers = dict(
        flat=("red_sand", 4.0, (1.0, 0.92, 0.85)),
        steep=("red_sandstone_wall", 9.0, (1.05, 0.82, 0.68)),
        high=("sandstone_cracks", 12.0, (1.0, 0.8, 0.66)),
    )
    m = A.terrain_mat("canyon_terrain", layers, slope=(0.55, 0.8), height=(9000, 9100), macro=0.02, macro_amp=(0.8, 1.12))
    A.grid_mesh("terrain_mid", h, -260, 260, -150, 700, 380, 560, m)
    A.grid_mesh("terrain_far", lambda x, y: h(x, y) - 1.0, -2500, 2500, -1500, 4000, 200, 220, m)


def pool():
    m = A.water_mat("oasis", A.hexc("#0F4A44"), A.hexc("#3E8C78"), rough=0.03, wave_scale=0.4, wave_strength=0.06)
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=POOL[2] * 1.15, fill_type="NGON", location=(POOL[0], POOL[1], h(POOL[0], POOL[1]) + 1.15))
    o = bpy.context.active_object
    o.scale = (1.0, 1 / 1.3, 1)
    o.data.materials.append(m)
    reeds = A.proto("grass_medium_01", tint_rgb=(0.85, 1.0, 0.7))
    for i in range(160):
        a = R.uniform(0, 6.28)
        rr = POOL[2] * R.uniform(0.95, 1.25)
        x, y = POOL[0] + math.cos(a) * rr, POOL[1] + math.sin(a) * rr / 1.3
        A.inst(reeds, (x, y, h(x, y)), yaw=R.uniform(0, 6.3), scale=R.uniform(1.0, 1.8))


def palms():
    spots = []
    for i in range(14):
        a = 2 * math.pi * i / 14 + R.uniform(-0.2, 0.2)
        rr = POOL[2] * R.uniform(1.3, 2.2)
        spots.append((POOL[0] + math.cos(a) * rr, POOL[1] + math.sin(a) * rr / 1.2))
    spots += [(-26, 70), (-20, 95), (30, 110), (22, 140), (-30, 10), (34, -5), (28, 20)]
    for i, (x, y) in enumerate(spots):
        B.palm((x, y, h(x, y) - 0.1), height=R.uniform(8, 15), lean=(R.uniform(-0.12, 0.12), R.uniform(-0.12, 0.12)), seed=i)


def market():
    cloths = [
        B.stripe_mat("aw_red", A.hexc("#A8322A"), A.hexc("#E8DCC4"), 9),
        B.stripe_mat("aw_saffron", A.hexc("#D9932B"), A.hexc("#F0E6D2"), 7),
        B.stripe_mat("aw_indigo", A.hexc("#24476E"), A.hexc("#E6DCC8"), 10),
        B.stripe_mat("aw_madder", A.hexc("#7E2F24"), A.hexc("#C9A27A"), 6),
    ]
    stalls = [(-14, 10, 80), (-15, 18, 85), (-16, 26.5, 95), (-14, 35, 92), (-11, 44, 100), (-6, 54, 120), (2, 60, 160)]
    for i, (x, y, yaw) in enumerate(stalls):
        B.stall((x, y, h(x, y) - 0.05), math.radians(yaw - 180), w=4.2, d=3.0, hgt=2.5, cloth=cloths[i % 4], seed=i)
    goods = [A.proto(n) for n in ("ceramic_vase_01", "ceramic_vase_03", "antique_ceramic_vase_01", "brass_pot_01", "brass_vase_02", "wicker_basket_01", "wicker_basket_02")]
    heavy = [A.proto(n) for n in ("wooden_crate_01", "wooden_crate_02", "Barrel_01")]
    for i, (x, y, yaw) in enumerate(stalls):
        for k in range(5):
            gx, gy = x + R.uniform(1.6, 3.2), y + R.uniform(-1.8, 1.8)
            A.inst(R.choice(goods), (gx, gy, h(gx, gy)), yaw=R.uniform(0, 6.3), scale=R.uniform(0.9, 1.4))
        for k in range(2):
            gx, gy = x - R.uniform(0.5, 2.0), y + R.uniform(-2.0, 2.0)
            A.inst(R.choice(heavy), (gx, gy, h(gx, gy)), yaw=R.uniform(0, 6.3), scale=1.0)
    # caravan cargo stacked at the canyon floor (crates, barrels, sacks)
    sack = B.stripe_mat("sack", A.hexc("#B89A6E"), A.hexc("#A88C62"), 2)
    for k in range(18):
        gx, gy = 6 + R.uniform(-3, 4), 4 + R.uniform(-3, 5)
        z = h(gx, gy) + (1.0 if k > 12 else 0)
        A.inst(R.choice(heavy), (gx, gy, z), yaw=R.uniform(-0.3, 0.3), scale=1.0)
    for k in range(10):
        gx, gy = 2 + R.uniform(-2, 2), 9 + R.uniform(-2, 2)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(gx, gy, h(gx, gy) + 0.3))
        sk = bpy.context.active_object
        sk.scale = (1.0, 0.75, 0.6)
        sk.data.materials.append(sack)
        for p in sk.data.polygons:
            p.use_smooth = True


def facade():
    """Carved temple front cut into the far wall (lost-age wonder hint)."""
    stone = A.pbr("facade", "red_sandstone_wall", 0.25, coords="Object", box=True, tint_rgb=(1.08, 0.86, 0.72))
    y = 250
    x = cx(y) - hw(y) - 2
    zb = h(x + 8, y) + 6
    objs = []
    for i in range(6):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.4, depth=22, location=(x + 10, y - 15 + i * 6, zb + 11))
        c = bpy.context.active_object
        c.data.materials.append(stone)
        objs.append(c)
    objs.append(B.cube("ent", (4, 36, 4), (x + 10, y, zb + 24), stone, bevel=0.2))
    v = [(x + 10, y - 19, zb + 26), (x + 10, y + 19, zb + 26), (x + 10, y, zb + 34)]
    pd = B._obj("ped", v, [(0, 1, 2)], stone, uv_fn=B.box_uv)
    pd.modifiers.new("s", "SOLIDIFY").thickness = 3
    objs.append(B.cube("door", (1.0, 7, 12), (x + 11.5, y, zb + 6), A.flat_mat("dark", (0.02, 0.015, 0.012, 1), 0.9)))
    objs.append(B.cube("base", (8, 40, 3), (x + 10, y, zb - 1), stone))


def people():
    import wf_mh as M

    M.character("trader", "vend", loc=(-12.6, 18.5, h(-12.6, 18.5)), yaw_deg=-90)
    M.character("trader", "talk", loc=(-9.0, 35.5, h(-9.0, 35.5)), yaw_deg=-120)
    M.character("fisher", "walk", loc=(3.0, 30.0, h(3.0, 30.0)), yaw_deg=170, gear=False)


def player_and_camera():
    import wf_mh as M

    P = Vector((P0[0], P0[1], h(*P0)))
    view = Vector((0.12, 1.0, 0)).normalized()
    yaw = math.degrees(math.atan2(-view.x, view.y))
    M.character("explorer", "walk", loc=tuple(P), yaw_deg=yaw)
    right = Vector((view.y, -view.x, 0))
    cam = P - view * 4.2 + right * 1.4 + Vector((0, 0, 2.0))
    tgt = P + view * 50 + Vector((0, 0, 4.0)) + right * 3
    return A.camera(cam, tgt, lens=24, dof=((P - cam).length, 4.0))


def main():
    import time

    t0 = time.time()
    A.reset()
    A.eevee(samples=SAMPLES, res=(int(1920 * SCALE), int(1080 * SCALE)), exposure=-0.5)
    w, nt, env = A.world_hdri("syferfontein_18d_clear_puresky_4k.hdr", -56, strength=1.0)
    for attr, val in (("sun_threshold", 10.0), ("sun_angle", math.radians(1.0)), ("use_sun_shadow", True), ("sun_shadow_maximum_resolution", 0.002)):
        if hasattr(w, attr):
            setattr(w, attr, val)
    terrain()
    pool()
    palms()
    market()
    facade()
    people()
    player_and_camera()
    A.compositor_fog((0.86, 0.68, 0.52), 25, 900, 0.62, sky_haze=0.18, vignette=0.18, haze_power=2.0)
    print("BUILD", round(time.time() - t0, 1))
    bpy.ops.wm.save_as_mainfile(filepath=str(A.BUILD / f"canyon_{VARIANT}.blend"))
    if "--norender" not in argv:
        A.render(OUT)


main()
