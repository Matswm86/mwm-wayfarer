"""Key frame 3b: R3 Redwall Oasis, inside the siq (slot canyon) that leads into the oasis.

Why a separate scene: the 30 m Copernicus relief in scene_canyon.py cannot hold a slot canyon (real siqs are
3-15 m wide), so the canyon key read as an ordinary valley. Here the two walls are authored meshes, not a
heightfield: each wall is a vertical grid pushed sideways by rounded sandstone strata, flowing erosion and grain,
so a 70 m wall has real horizontal ledges instead of stretched cells (DESIGN 7.1, 10-10 lesson).
Look: narrow meandering slot, strong warm sun striking one wall high up, cool sky fill + warm bounce in the
shadow, layered sandstone colour (deep red, rose, ochre, cream bands), bright exit to the oasis ahead.

BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user \
blender -b --factory-startup -P tools/art/scene_siq.py -- key <out.png> [scale] [samples]
Env: WF_SUN_ELEV (58), WF_SUN_AZ (100: light from the east, slightly ahead), WF_EXPOSURE (0).
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
R = A.rng(31)
HWALL = 60.0
Y0, Y1 = -30.0, 300.0
EXIT = 215.0  # the slot opens into the oasis from here


def xc(y):
    """Slot centre line: a meander, so the walls overlap ahead and hide the exit until the last bend."""
    return 7.0 * math.sin(y / 48.0) + 2.5 * math.sin(y / 19.0 + 1.3)


def half_w(y, z, side):
    w0 = 3.4 + 1.4 * B.fbm(y / 40.0 + 3 * side, 0.5, 2)  # 5-10 m floor
    open_top = 0.07 * z + 0.0016 * z * z  # walls lean apart towards the sky, so the sun reaches the upper west wall
    flow = 2.2 * B.fbm(y / 26.0 + 11 * side, z / 22.0, 3)  # big water-carved swells
    st = 2.4 + 0.6 * B.fbm(y / 90.0, z / 30.0 + side, 2)
    zw = z + 1.4 * B.fbm(y / 35.0, side * 5.0, 2)  # bedding planes wander a little
    f = (zw / st) % 1.0
    ledge = 0.65 * (1.0 - math.sin(math.pi * f) ** 0.5)  # soft layers erode back between harder beds
    grain = 0.10 * B.fbm(y / 1.6 + side * 7, z / 1.6, 3)
    ex = B.smoothstep(EXIT - 25.0, EXIT + 50.0, y)
    return w0 + open_top + flow + ledge + grain + ex * (45.0 + 0.5 * z)


def wall(side, mat, dy=0.5, dz=0.5):
    ny = int((Y1 - Y0) / dy)
    nz = int(HWALL / dz)
    verts, faces = [], []
    for j in range(nz + 2):
        z = min(j * dz, HWALL)
        for i in range(ny + 1):
            y = Y0 + i * dy
            x = xc(y) + side * half_w(y, z, side)
            if j == nz + 1:  # rim: run the top outward as a plateau so the sky strip has a clean edge
                x += side * 60.0
            verts.append((x, y, z if j <= nz else HWALL + 0.6 * B.fbm(y / 15, side, 2)))
    for j in range(nz + 1):
        for i in range(ny):
            a = j * (ny + 1) + i
            q = (a, a + 1, a + ny + 2, a + ny + 1)
            faces.append(q if side > 0 else q[::-1])
    me = bpy.data.meshes.new(f"siq_wall{side}")
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    o = A.link(bpy.data.objects.new(f"siq_wall{side}", me))
    o.data.materials.append(mat)
    return o


def sandstone_mat():
    """Layered sandstone: colour bands from a 1D noise of height (non-repeating strata), triplanar scan grain."""
    m = bpy.data.materials.new("siq_sandstone")
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    T = A.tex_nodes(nt, "sandstone_cracks", A.mapping(nt, 1 / 3.0, "Object", src=tc.outputs["Object"]), box=True)
    T2 = A.tex_nodes(nt, "sandstone_cracks", A.mapping(nt, 1 / 13.0, "Object", rot=0.9, src=tc.outputs["Object"]), box=True)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    warp = A.math_node(nt, "MULTIPLY", A.noise(nt, 0.03, tc.outputs["Object"], detail=2), 6.0)
    zv = A.math_node(nt, "ADD", sep.outputs["Z"], warp)
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(A.math_node(nt, "MULTIPLY", zv, 0.22), comb.inputs["Z"])
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(n1, "noise_dimensions"):
        n1.noise_dimensions = "1D"
    n1.inputs["Scale"].default_value = 1.0
    n1.inputs["Detail"].default_value = 3.0
    if "W" in n1.inputs:
        nt.links.new(A.math_node(nt, "MULTIPLY", zv, 0.22), n1.inputs["W"])
    else:
        nt.links.new(comb.outputs[0], n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    stops = [
        (0.30, "#6E3020"),
        (0.38, "#8E3E26"),
        (0.45, "#B5653E"),
        (0.52, "#C47A50"),
        (0.58, "#D9A273"),
        (0.64, "#E6C9A2"),
        (0.70, "#B0604A"),
    ]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], A.hexc(stops[0][1])
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], A.hexc(stops[-1][1])
    for pos, hx in stops[1:-1]:
        e = cr.elements.new(pos)
        e.color = A.hexc(hx)
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    lum = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(A.mixc(nt, 0.4, T["albedo"], T2["albedo"]), lum.inputs[0])
    detail = A.maprange(nt, lum.outputs[0], 0.1, 0.6, 0.75, 1.15)
    col = A.math_col_mul(nt, ramp.outputs["Color"], detail)
    # desert varnish: darker streaks down from the rim
    st_vec = A.mapping(nt, (0.12, 0.12, 0.006), "Object", src=tc.outputs["Object"])
    st = nt.nodes.new("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 4.0
    st.inputs["Detail"].default_value = 5.0
    nt.links.new(st_vec, st.inputs["Vector"])
    varnish = A.math_node(nt, "MULTIPLY", A.maprange(nt, st.outputs["Fac"], 0.55, 0.7), A.maprange(nt, sep.outputs["Z"], 20, 60))
    col = A.mixc(nt, A.math_node(nt, "MULTIPLY", varnish, 0.35), col, A.math_col_mul(nt, col, A.maprange(nt, st.outputs["Fac"], 0, 1, 0.35, 0.35)))
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(A.maprange(nt, T["rough"], 0, 1, 0.75, 0.95), b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.3
    nt.links.new(A.mixc(nt, 0.4, T["normal"], T2["normal"]), nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def floor_z(x, y):
    return 0.25 * B.fbm(x / 6, y / 9, 3) + 0.08 * B.fbm(x / 1.2, y / 1.2, 2) - 0.15 * B.smoothstep(EXIT, EXIT + 60, y)


def floor():
    m = A.pbr("siq_sand", "red_sand", 1 / 3.0, tint_rgb=(1.25, 0.95, 0.78))
    return A.grid_mesh("siq_floor", floor_z, -120, 120, Y0, Y1 + 200, 240, 520, m)


def boulders():
    protos = [A.proto("namaqualand_boulder_02", tint_rgb=(1.1, 0.75, 0.6)), A.proto("namaqualand_boulder_05", tint_rgb=(1.1, 0.75, 0.6))]
    for k in range(14):
        y = R.uniform(8, EXIT - 10)
        side = R.choice((-1, 1))
        x = xc(y) + side * (half_w(y, 0.3, side) - R.uniform(0.3, 1.0))
        A.inst(R.choice(protos), (x, y, floor_z(x, y) - 0.1), yaw=R.uniform(0, 6.3), scale=R.uniform(0.25, 0.7))


def oasis_glimpse():
    """What waits beyond the exit: palms and a sunlit far wall, enough to pull the eye down the slot."""
    far = A.pbr("far_wall", "sandstone_cracks", 1 / 18.0, coords="Object", box=True, tint_rgb=(1.35, 0.85, 0.6))
    A.grid_mesh(
        "far_wall",
        lambda x, y: 0.0,
        -200,
        200,
        0,
        120,
        40,
        12,
        far,
    )
    o = bpy.data.objects["far_wall"]
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = (xc(EXIT + 140) - 10, EXIT + 160, -1)
    for k in range(10):
        y = EXIT + R.uniform(45, 130)
        x = xc(y) + R.uniform(-45, 45)
        B.palm((x, y, floor_z(x, y) - 0.1), height=R.uniform(9, 16), lean=(R.uniform(-0.1, 0.1), R.uniform(-0.1, 0.1)), seed=k, nfr=22, frond_w=1.6)


def player_and_camera():
    import wf_mh as M

    y = 18.0
    P = Vector((xc(y) + 0.4, y, floor_z(xc(y), y)))
    d = Vector((xc(y + 6) - xc(y - 6), 12.0, 0)).normalized()
    yaw = math.degrees(math.atan2(-d.x, d.y))
    M.character("explorer", "walk", loc=tuple(P), yaw_deg=yaw)
    right = Vector((d.y, -d.x, 0))
    cam = P - d * 4.0 + right * 1.1 + Vector((0, 0, 1.75))
    tgt = P + d * 60 + Vector((0, 0, 17.0))
    return A.camera(cam, tgt, lens=22, dof=((P - cam).length, 8.0))


def main():
    import time

    t0 = time.time()
    A.reset()
    A.eevee(samples=SAMPLES, res=(int(1920 * SCALE), int(1080 * SCALE)), exposure=float(os.environ.get("WF_EXPOSURE", 0.0)))
    if hasattr(bpy.context.scene.eevee, "ray_tracing_method"):
        bpy.context.scene.eevee.ray_tracing_method = "SCREEN"
    A.world_hdri("kloofendal_43d_clear_puresky_4k.hdr", 0, strength=float(os.environ.get("WF_SKY", 0.45)))
    A.sun(
        float(os.environ.get("WF_SUN_ELEV", 74.0)),
        float(os.environ.get("WF_SUN_AZ", 82.0)),
        color=(1.0, 0.80, 0.58),
        energy=float(os.environ.get("WF_SUN_ENERGY", 7.5)),
        angle=0.6,
    )
    m = sandstone_mat()
    wall(-1, m)
    wall(1, m)
    floor()
    boulders()
    oasis_glimpse()
    player_and_camera()
    A.compositor_fog((0.92, 0.78, 0.62), 70, 1500, 0.16, sky_haze=0.04, vignette=0.12, haze_power=2.0)
    print("BUILD", round(time.time() - t0, 1))
    bpy.ops.wm.save_as_mainfile(filepath=str(A.BUILD / f"siq_{VARIANT}.blend"))
    if "--norender" not in argv:
        A.render(OUT)


main()
