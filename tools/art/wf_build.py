"""Procedural set pieces for the Wayfarer drafts, all textured with Poly Haven CC0 scans:
turf-roof timber houses, clinker boats, waterfall ribbon, mist cards, market stalls with awnings, ruined
colonnade, palms, a sky with an aurora band. Blender metres, Z up."""

from __future__ import annotations

import math
import random

import bpy
import wf_art as A
from mathutils import Vector, noise


def _obj(name, verts, faces, mat=None, smooth=False, uv_fn=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if uv_fn is not None:
        uvl = me.uv_layers.new(name="UVMap")
        for p in me.polygons:
            for li in p.loop_indices:
                uvl.data[li].uv = uv_fn(me.vertices[me.loops[li].vertex_index].co, p.normal)
    o = A.link(bpy.data.objects.new(name, me))
    if mat:
        o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    return o


def box_uv(co, n):
    """World-metre box mapping for building parts."""
    ax = max(range(3), key=lambda i: abs(n[i]))
    if ax == 0:
        return (co.y, co.z)
    if ax == 1:
        return (co.x, co.z)
    return (co.x, co.y)


def cube(name, size, loc, mat, rot_z=0.0, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=(0, 0, rot_z))
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL")
        bv.width = bevel
        bv.segments = 2
    uvl = o.data.uv_layers[0]
    for p in o.data.polygons:
        for li in p.loop_indices:
            co = o.data.vertices[o.data.loops[li].vertex_index].co
            uvl.data[li].uv = box_uv(co, p.normal)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------- Nordic turf-roof house
_MATS: dict[str, bpy.types.Material] = {}


def mats_nordic():
    if _MATS:
        return _MATS
    _MATS["red"] = A.pbr(
        "wall_red",
        "weathered_plank_siding",
        0.45,
        tint_rgb=(0.62, 0.20, 0.13),
        hue=(0.5, 0.35, 1.0),
    )
    _MATS["ochre"] = A.pbr(
        "wall_ochre",
        "weathered_plank_siding",
        0.45,
        tint_rgb=(0.85, 0.55, 0.22),
        hue=(0.5, 0.4, 1.0),
    )
    _MATS["white"] = A.pbr(
        "wall_white",
        "weathered_plank_siding",
        0.45,
        tint_rgb=(1.0, 0.97, 0.9),
        hue=(0.5, 0.15, 1.15),
    )
    _MATS["tar"] = A.pbr("wall_tar", "wood_trunk_wall", 0.7, tint_rgb=(0.55, 0.42, 0.33))
    _MATS["turf"] = A.pbr("turf", "leafy_grass", 0.35, tint_rgb=(0.85, 0.95, 0.6), nstrength=1.4)
    _MATS["stone"] = A.pbr("found_stone", "stone_wall", 0.5)
    _MATS["trim"] = A.flat_mat("trim", A.hexc("#E8E2D4"), rough=0.6)
    _MATS["bark"] = A.pbr("roof_edge", "weathered_brown_planks", 0.5, tint_rgb=(0.6, 0.5, 0.42))
    win = bpy.data.materials.new("window_lit")
    win.use_nodes = True
    b = A.bsdf(win)
    b.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Emission Color"].default_value = A.hexc("#FFB35C")
    b.inputs["Emission Strength"].default_value = 6.0
    _MATS["win_lit"] = win
    _MATS["win_dark"] = A.flat_mat("window_dark", (0.015, 0.018, 0.022, 1), rough=0.05)
    return _MATS


def nordic_house(
    loc, yaw, w=6.0, d=8.0, h=3.0, pitch=27.0, wall="red", lit=0.6, seed=0, chimney=True
):
    """Timber house with stone footing, gable turf roof (overhang, birch-bark edge boards), windows, door."""
    M = mats_nordic()
    r = random.Random(seed)
    objs = []
    cx, cy, cz = loc
    objs.append(cube("found", (w + 0.3, d + 0.3, 0.6), (0, 0, 0.1), M["stone"]))
    objs.append(cube("walls", (w, d, h), (0, 0, 0.4 + h / 2), M[wall]))
    # gable ends
    rh = (w / 2) * math.tan(math.radians(pitch))
    for sy in (-1, 1):
        y = sy * d / 2
        v = [(-w / 2, y, 0.4 + h), (w / 2, y, 0.4 + h), (0, y, 0.4 + h + rh)]
        g = _obj("gable", v, [(0, 1, 2)], M[wall], uv_fn=box_uv)
        sol = g.modifiers.new("s", "SOLIDIFY")
        sol.thickness = 0.12
        objs.append(g)
    # roof slabs with overhang and thickness (turf ~0.25 m)
    ov = 0.45
    for sx in (-1, 1):
        x0, z0 = sx * (w / 2 + ov), 0.4 + h - ov * math.tan(math.radians(pitch))
        x1, z1 = 0.0, 0.4 + h + rh
        v = [
            (x0, -d / 2 - ov, z0),
            (x1, -d / 2 - ov, z1),
            (x1, d / 2 + ov, z1),
            (x0, d / 2 + ov, z0),
        ]
        sl = _obj(
            "roof", v, [(0, 1, 2, 3)], M["turf"], uv_fn=lambda co, n: (co.x * 1.2 + co.z, co.y)
        )
        sl.data.polygons[0].use_smooth = True
        sub = sl.modifiers.new("sub", "SUBSURF")
        sub.subdivision_type = "SIMPLE"
        sub.levels = sub.render_levels = 5
        dp = sl.modifiers.new("disp", "DISPLACE")
        tx = bpy.data.textures.new(f"turfn{seed}{sx}", "CLOUDS")
        tx.noise_scale = 0.35
        dp.texture = tx
        dp.strength = 0.12
        dp.direction = "Z"
        so = sl.modifiers.new("sol", "SOLIDIFY")
        so.thickness = 0.28
        so.offset = 1.0
        so.material_offset = 0
        objs.append(sl)
        # edge board under the turf
        eb = cube("eave", (0.06, d + 2 * ov, 0.3), (x0 * 0.995, 0, z0 - 0.08), M["bark"])
        objs.append(eb)
    # windows and door on the long sides and gable
    for sx in (-1, 1):
        n = max(2, int(d / 2.6))
        for i in range(n):
            y = -d / 2 + (i + 0.5) * d / n
            if sx == 1 and i == n // 2:
                objs.append(
                    cube("door", (0.08, 1.0, 2.0), (sx * (w / 2 + 0.02), y, 0.4 + 1.0), M["tar"])
                )
                continue
            m = M["win_lit"] if r.random() < lit else M["win_dark"]
            objs.append(cube("win", (0.06, 0.8, 1.0), (sx * (w / 2 + 0.03), y, 0.4 + h * 0.55), m))
            objs.append(
                cube("frame", (0.07, 1.0, 1.2), (sx * (w / 2 + 0.01), y, 0.4 + h * 0.55), M["trim"])
            )
    for sy in (-1, 1):
        m = M["win_lit"] if r.random() < lit else M["win_dark"]
        objs.append(
            cube("gwin", (0.7, 0.06, 0.8), (0, sy * (d / 2 + 0.06), 0.4 + h + rh * 0.35), m)
        )
        objs.append(
            cube(
                "gframe", (0.9, 0.07, 1.0), (0, sy * (d / 2 + 0.04), 0.4 + h + rh * 0.35), M["trim"]
            )
        )
    if chimney:
        objs.append(
            cube("chim", (0.6, 0.6, 1.4), (w * 0.15, d * 0.25, 0.4 + h + rh * 0.7), M["stone"])
        )
    root = bpy.data.objects.new("house", None)
    A.link(root)
    for o in objs:
        o.parent = root
    root.location = (cx, cy, cz)
    root.rotation_euler = (0, 0, yaw)
    return root, objs


# ---------------------------------------------------------------- clinker boat
def boat(loc, yaw, L=6.0, B=1.8, D=0.75, color="#E9E4DA", seed=0, cabin=False):
    """Clinker-built wooden boat (faering / snekke): lofted U sections with plank steps, sheer rising at the ends."""
    planks = A.pbr(
        f"hull{seed}",
        "wood_planks_dirt",
        0.6,
        tint_rgb=A.hexc(color)[:3],
        hue=(0.5, 0.3, 1.1),
        rough_add=0.05,
    )
    inner = A.pbr(f"hull_in{seed}", "weathered_brown_planks", 0.5, tint_rgb=(0.75, 0.62, 0.48))
    nu, nv = 40, 12
    verts, faces = [], []
    for i in range(nu + 1):
        t = i / nu
        hw = B / 2 * (math.sin(math.pi * t) ** 0.65)
        sheer = D + 0.22 * ((2 * t - 1) ** 4)
        keel = -0.02 * math.sin(math.pi * t)
        x = (t - 0.5) * L
        for j in range(nv + 1):
            a = j / nv  # 0 = keel, 1 = gunwale
            step = math.floor(a * 6) / 6
            a2 = a * 0.6 + step * 0.4  # clinker steps
            yy = hw * math.sin(a2 * math.pi / 2) ** 0.9
            zz = keel + sheer * (1 - math.cos(a2 * math.pi / 2)) ** 1.0
            verts.append((x, yy, zz))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            faces.append((a, a + nv + 1, a + nv + 2, a + 1))
    # mirror other side
    n0 = len(verts)
    verts += [(x, -y, z) for (x, y, z) in verts]
    faces += [tuple(reversed([v + n0 for v in f])) for f in faces]
    o = _obj(
        "hull",
        verts,
        faces,
        planks,
        smooth=True,
        uv_fn=lambda co, n: (co.x * 0.5, co.z * 2.5 + abs(co.y)),
    )
    o.data.materials.append(inner)
    sol = o.modifiers.new("s", "SOLIDIFY")
    sol.thickness = 0.04
    sol.material_offset = 1
    objs = [o]
    # thwarts
    for tx in (-0.2, 0.15, 0.32):
        objs.append(
            cube(
                "thwart",
                (0.22, B * 0.85 * math.sin(math.pi * (tx + 0.5)) ** 0.6, 0.04),
                (tx * L, 0, D * 0.62),
                inner,
            )
        )
    if cabin:
        wh = A.pbr(f"cabin{seed}", "weathered_plank_siding", 0.4, tint_rgb=(0.9, 0.9, 0.86))
        objs.append(cube("wheelhouse", (1.3, B * 0.7, 1.3), (-0.12 * L, 0, D + 0.55), wh))
        objs.append(
            cube(
                "cabroof",
                (1.45, B * 0.78, 0.08),
                (-0.12 * L, 0, D + 1.24),
                A.flat_mat("cabroof", A.hexc("#2B2F33"), 0.5),
            )
        )
        objs.append(
            cube(
                "cabwin",
                (0.05, B * 0.5, 0.4),
                (-0.12 * L + 0.66, 0, D + 0.85),
                mats_nordic()["win_dark"],
            )
        )
    root = bpy.data.objects.new("boat", None)
    A.link(root)
    for b in objs:
        b.parent = root
    root.location = loc
    root.rotation_euler = (0.0, 0.0, yaw)
    return root


# ---------------------------------------------------------------- waterfall
def waterfall(path_pts, width, name="falls", strength=3.0):
    """A ribbon down a cliff (list of 3D points top->bottom) with streaking white water, alpha-broken edges.
    Godot/Unity: one scrolling-UV card strip + a mist sprite pool at the foot."""
    verts, faces = [], []
    n = len(path_pts)
    for i, p in enumerate(path_pts):
        p = Vector(p)
        t = Vector(path_pts[min(i + 1, n - 1)]) - Vector(path_pts[max(i - 1, 0)])
        side = t.cross(Vector((0, 0, 1)))
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        wv = width * (0.7 + 0.6 * i / n)
        verts += [tuple(p - side * wv / 2), tuple(p + side * wv / 2)]
    for i in range(n - 1):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    o = _obj(name, verts, faces, smooth=True)
    uvl = o.data.uv_layers.new(name="UVMap")
    for p in o.data.polygons:
        for li in p.loop_indices:
            vi = o.data.loops[li].vertex_index
            uvl.data[li].uv = (vi % 2, (vi // 2) / (n - 1))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = A.mapping(nt, (40.0, 1.5, 1.0), src=tc.outputs["UV"])
    nz = A.noise(nt, 1.0, mp, detail=6, rough=0.6)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs["Vector"])
    edge = A.math_node(
        nt,
        "MULTIPLY",
        A.maprange(nt, sep.outputs["X"], 0.0, 0.25),
        A.maprange(nt, sep.outputs["X"], 1.0, 0.75),
    )
    a = A.math_node(nt, "MULTIPLY", edge, A.maprange(nt, nz, 0.35, 0.65, 0.15, 1.0))
    a = A.math_node(nt, "MULTIPLY", a, A.maprange(nt, sep.outputs["Y"], 0.0, 0.08))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.85, 0.9, 0.95, 1)
    em.inputs["Strength"].default_value = strength
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.9, 0.93, 0.96, 1)
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], ad.inputs[0])
    nt.links.new(df.outputs[0], ad.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(ad.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def mist(loc, size, alpha=0.35, color=(0.85, 0.88, 0.92), name="mist", face=None, seed=0):
    """Soft camera-facing mist card (noise alpha). face: point to face toward."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], 1)
    if face is not None:
        d = Vector(face) - Vector(loc)
        d.z = 0
        o.rotation_euler = (math.pi / 2, 0, math.atan2(d.y, d.x) + math.pi / 2)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "DISTANCE"
    nt.links.new(tc.outputs["UV"], vm.inputs[0])
    vm.inputs[1].default_value = (0.5, 0.5, 0)
    rad = A.maprange(nt, vm.outputs["Value"], 0.5, 0.15)
    off = nt.nodes.new("ShaderNodeMapping")
    off.inputs["Location"].default_value = (seed * 3.1, seed * 1.7, 0)
    off.inputs["Scale"].default_value = (3.0, 3.0, 3.0)
    nt.links.new(tc.outputs["UV"], off.inputs["Vector"])
    nz = A.noise(nt, 1.0, off.outputs[0], detail=5, rough=0.6)
    a = A.math_node(nt, "MULTIPLY", rad, A.maprange(nt, nz, 0.35, 0.7, 0.0, alpha))
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = 1.0
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def aurora(
    world_nt,
    bg_node,
    strength=1.2,
    az_center=120.0,
    az_width=70.0,
    elev=(22.0, 50.0),
    color=(0.25, 1.0, 0.55),
):
    """Aurora band added to the sky shader by view direction: curtain folds (noise on azimuth), bright lower
    edge, fades up. Sky-only, so the depth fog never touches it. Godot: a few lines in the sky shader."""
    nt = world_nt
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    az = A.math_node(
        nt,
        "MULTIPLY",
        A.math_node(nt, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"]),
        180.0 / math.pi,
    )
    el = A.math_node(nt, "MULTIPLY", A.math_node(nt, "ARCSINE", sep.outputs["Z"]), 180.0 / math.pi)
    # curtain base elevation wanders with azimuth
    wv = A.math_node(
        nt, "MULTIPLY", A.math_node(nt, "SINE", A.math_node(nt, "MULTIPLY", az, 0.09)), 6.0
    )
    base = A.math_node(nt, "ADD", wv, elev[0])
    rel = A.math_node(nt, "SUBTRACT", el, base)
    lower = A.maprange(nt, rel, -1.0, 1.5)
    upper = A.maprange(nt, rel, elev[1] - elev[0], 2.0)
    vert = A.math_node(nt, "MULTIPLY", lower, upper)
    vert = A.math_node(nt, "MULTIPLY", vert, A.maprange(nt, rel, 18.0, 0.0, 0.25, 1.0))
    azm = A.math_node(
        nt,
        "MULTIPLY",
        A.maprange(
            nt,
            A.math_node(nt, "ABSOLUTE", A.math_node(nt, "SUBTRACT", az, az_center)),
            az_width,
            az_width * 0.4,
        ),
        1.0,
    )
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(A.math_node(nt, "MULTIPLY", az, 0.6), cmb.inputs["X"])
    nt.links.new(A.math_node(nt, "MULTIPLY", el, 0.02), cmb.inputs["Y"])
    streak = A.noise(nt, 0.35, cmb.outputs[0], detail=4, rough=0.6)
    fold = A.maprange(nt, streak, 0.38, 0.75, 0.1, 1.0)
    i = A.math_node(nt, "MULTIPLY", A.math_node(nt, "MULTIPLY", vert, azm), fold)
    em = nt.nodes.new("ShaderNodeEmission")
    col = A.mixc(nt, A.maprange(nt, rel, 2.0, 22.0), (*color, 1), (0.2, 0.75, 0.75, 1))
    nt.links.new(col, em.inputs["Color"])
    nt.links.new(A.math_node(nt, "MULTIPLY", i, strength), em.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    nt.links.new(bg_node.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])


def fbm(x, y, octaves=5, basis="PERLIN_ORIGINAL"):
    return noise.fractal((x, y, 0.0), 1.0, 2.0, octaves, noise_basis=basis)


def ridged(x, y, octaves=5):
    return noise.ridged_multi_fractal(
        (x, y, 0.0), 1.0, 2.0, octaves, 1.0, 2.0, noise_basis="PERLIN_ORIGINAL"
    )


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- date palm
_PALM = {}


def palm_mats():
    if _PALM:
        return _PALM
    _PALM["bark"] = A.pbr("palm_bark", "palm_tree_bark", 1.0, coords="UV")
    m = bpy.data.materials.new("frond")
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = A.load_image(A.BUILD / "palm_frond.png")
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Subsurface Weight"].default_value = 0.0
    try:
        b.inputs["Transmission Weight"].default_value = 0.0
    except Exception:  # noqa: BLE001
        pass
    m.surface_render_method = "DITHERED"
    m.use_backface_culling = False
    _PALM["frond"] = m
    return _PALM


def palm(loc, height=11.0, lean=(0.0, 0.0), seed=0, nfr=16, frond_w=1.1):
    M = palm_mats()
    r = random.Random(seed)
    seg, rings = 14, 30
    verts, faces = [], []
    top = Vector(loc)
    for j in range(rings + 1):
        t = j / rings
        z = height * t
        off = Vector((lean[0], lean[1], 0)) * (t**1.6) * height
        rad = 0.24 * (1.0 - 0.25 * t) * (1 + 0.06 * math.sin(j * 2.2))
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((off.x + rad * math.cos(a), off.y + rad * math.sin(a), z))
        top = Vector(loc) + Vector((off.x, off.y, z))
    for j in range(rings):
        for i in range(seg):
            a = j * seg + i
            b2 = j * seg + (i + 1) % seg
            faces.append((a, b2, b2 + seg, a + seg))
    tr = _obj(
        "palm_trunk",
        verts,
        faces,
        M["bark"],
        smooth=True,
        uv_fn=lambda co, n: (math.atan2(co.y, co.x) / math.pi, co.z / 1.2),
    )
    tr.location = loc
    objs = [tr]
    # fronds: curved strips, UV u along the frond
    for k in range(nfr):
        az = 2 * math.pi * k / nfr + r.uniform(-0.2, 0.2)
        up = r.uniform(-0.15, 0.75) if k % 3 else r.uniform(0.6, 1.0)
        L = r.uniform(3.6, 4.6)
        n = 12
        vv, ff, uvs = [], [], []
        dirv = Vector((math.cos(az), math.sin(az), 0))
        side = Vector((-math.sin(az), math.cos(az), 0))
        for i in range(n + 1):
            s = i / n
            ang = math.radians(55 * up) - s * s * math.radians(80)
            p = dirv * (L * s * math.cos(ang * 0.6)) + Vector((0, 0, L * s * math.sin(ang) * 0.6))
            wv = frond_w * math.sin(math.pi * min(1, s * 0.95 + 0.08)) ** 0.5
            droop = Vector((0, 0, -0.25 * wv))
            vv += [tuple(top + p - side * wv / 2 + droop), tuple(top + p + side * wv / 2 + droop)]
            uvs += [(s, 0.0), (s, 1.0)]
        for i in range(n):
            a = i * 2
            ff.append((a, a + 2, a + 3, a + 1))
        fo = _obj("frond", vv, ff, M["frond"], smooth=True)
        uvl = fo.data.uv_layers.new(name="UVMap")
        for p in fo.data.polygons:
            for li in p.loop_indices:
                uvl.data[li].uv = uvs[fo.data.loops[li].vertex_index]
        objs.append(fo)
    return objs


# ---------------------------------------------------------------- market stall with striped awning
def stripe_mat(name, c1, c2, stripes=8.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_profile = "SAW"
    wv.inputs["Scale"].default_value = stripes
    wv.inputs["Distortion"].default_value = 0.0
    nt.links.new(tc.outputs["UV"], wv.inputs["Vector"])
    st = A.maprange(nt, wv.outputs["Fac"], 0.48, 0.52)
    vec = A.mapping(nt, 3.0, "UV")
    T = A.tex_nodes(nt, "rough_linen", vec)
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(T["albedo"], bw.inputs["Color"])
    lv = A.maprange(nt, bw.outputs["Val"], 0.2, 0.8, 0.75, 1.15)
    col = A.math_col_mul(nt, A.mixc(nt, st, c1, c2), lv)
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = 0.4
    m.use_backface_culling = False
    try:
        b.inputs["Subsurface Weight"].default_value = 0.0
    except Exception:  # noqa: BLE001
        pass
    return m


def stall(loc, yaw, w=4.0, d=3.0, hgt=2.6, cloth=None, seed=0):
    wood = A.pbr("stall_wood", "weathered_brown_planks", 0.6, tint_rgb=(0.8, 0.65, 0.5))
    objs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            hh = hgt + (0.4 if sy < 0 else 0.0)
            objs.append(cube("post", (0.12, 0.12, hh), (sx * w / 2, sy * d / 2, hh / 2), wood))
    objs.append(cube("table", (w * 0.95, d * 0.45, 0.08), (0, d * 0.22, 0.85), wood))
    objs.append(cube("table_front", (w * 0.95, 0.05, 0.8), (0, d * 0.45, 0.45), wood))
    # sagging awning, sloped toward the front
    nx, ny = 16, 10
    vv, ff = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x = (u - 0.5) * (w + 0.6)
            y = (v - 0.5) * (d + 0.8)
            z = (
                hgt
                + 0.4
                - 0.55 * v
                - 0.18 * math.sin(math.pi * u) * math.sin(math.pi * v)
                + (0.06 * math.sin(u * 30 + seed) if j == ny else 0)
            )
            vv.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            ff.append((a, a + 1, a + nx + 2, a + nx + 1))
    aw = _obj(
        "awning",
        vv,
        ff,
        cloth,
        smooth=True,
        uv_fn=lambda co, n: ((co.x + w) / (w + 0.6), (co.y + d) / (d + 0.8)),
    )
    objs.append(aw)
    # valance flap at the front
    vv2 = [
        (-(w + 0.6) / 2, (d + 0.8) / 2, hgt - 0.15),
        ((w + 0.6) / 2, (d + 0.8) / 2, hgt - 0.15),
        ((w + 0.6) / 2, (d + 0.8) / 2, hgt - 0.5),
        (-(w + 0.6) / 2, (d + 0.8) / 2, hgt - 0.5),
    ]
    fl = _obj(
        "valance", vv2, [(0, 1, 2, 3)], cloth, uv_fn=lambda co, n: ((co.x + w) / (w + 0.6), co.z)
    )
    objs.append(fl)
    root = bpy.data.objects.new("stall", None)
    A.link(root)
    for o in objs:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, yaw)
    return root
