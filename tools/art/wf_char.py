"""Realistic adult characters for the Wayfarer drafts: Blender Studio Human Base Meshes (CC0) dressed by
inflating body regions into clothes (the Race Riders build_rider.py method), plus own-modelled gear (backpack,
bedroll, scarf, knit cap, boots) and the Poly Haven fishermans_hat. Skin, hair and fabric are PBR.

Kinds: "explorer" (player: waxed olive jacket, charcoal trousers, leather boots, canvas pack, bucket hat)
       "fisher"   (NPC: cream wool sweater, oilskin bib trousers, rubber boots, knit cap, trimmed grey beard)
       "trader"   (NPC: linen shirt, ochre head wrap, sash, sandals; canyon market)

Usage in a scene script:
    import wf_char as C
    rig, objs = C.character("explorer", "stand_look", loc=(x, y, z), yaw_deg=0)
Characters face +Y in rest; their left is -X.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import wf_art as A

SRC = A.RAW / "human" / "human-base-meshes-bundle-v1.4.1" / "human_base_meshes_bundle.blend"
SHOULDER = Vector((0.18, 0.0, 1.40))
WRIST = Vector((0.375, 0.056, 0.875))
TIP = Vector((0.42, 0.12, 0.72))
BONES = {
    "root": ((0, 0, 0), (0, 0.25, 0), None),
    "hips": ((0, 0.0, 0.95), (0, 0.0, 1.10), "root"),
    "spine": ((0, 0.0, 1.10), (0, -0.01, 1.27), "hips"),
    "chest": ((0, -0.01, 1.27), (0, 0.0, 1.44), "spine"),
    "neck": ((0, 0.0, 1.44), (0, 0.02, 1.54), "chest"),
    "head": ((0, 0.02, 1.54), (0, 0.02, 1.76), "neck"),
    "shoulder.L": ((-0.03, 0.0, 1.41), (-0.17, -0.01, 1.40), "chest"),
    "upper_arm.L": ((-0.18, -0.01, 1.40), (-0.27, 0.0, 1.12), "shoulder.L"),
    "forearm.L": ((-0.27, 0.0, 1.12), (-0.375, 0.056, 0.875), "upper_arm.L"),
    "hand.L": ((-0.375, 0.056, 0.875), (-0.42, 0.12, 0.72), "forearm.L"),
    "thigh.L": ((-0.09, 0.0, 0.92), (-0.12, 0.015, 0.49), "hips"),
    "shin.L": ((-0.12, 0.015, 0.49), (-0.16, -0.04, 0.085), "thigh.L"),
    "foot.L": ((-0.16, -0.04, 0.085), (-0.17, 0.14, 0.02), "shin.L"),
}

OUTFIT = {
    "explorer": dict(
        top="jacket", hem=0.80, sleeve=0.955, bottom_lo=0.235, collar=1.49,
        mats=dict(top=("poly_wool_herringbone", "#4A5238", 2.2), bottom=("denim_fabric", "#3A3A3C", 3.0),
                  boots=("brown_leather", "#6B4A32", 3.0)),
        skin="#B98468", hair="#3B2A20", beard=False,
    ),
    "fisher": dict(
        top="sweater", hem=0.86, sleeve=0.94, bottom_lo=0.30, collar=1.50,
        mats=dict(top=("knitted_fleece", "#CFC6B2", 4.0), bottom=("brown_leather", "#2E3B44", 1.5),
                  boots=("brown_leather", "#2B2D2E", 1.0)),
        skin="#C08A72", hair="#9C968E", beard=True,
    ),
    "trader": dict(
        top="shirt", hem=0.70, sleeve=0.80, bottom_lo=0.13, collar=1.47,
        mats=dict(top=("rough_linen", "#E6DCC8", 3.0), bottom=("rough_linen", "#7A5B3E", 3.0),
                  boots=("brown_leather", "#5A3B26", 2.0)),
        skin="#8A5A40", hair="#1E1612", beard=True,
    ),
}


def seg_t(p, a, b):
    ab = b - a
    t = (p - a).dot(ab) / ab.length_squared
    q = a + ab * max(0.0, min(1.0, t))
    return t, (p - q).length


# ---------------------------------------------------------------- materials
def fabric(name, tex, hexcol, tile, rough_add=0.08, wax=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vec = A.mapping(nt, tile, src=tc.outputs["Object"])
    T = A.tex_nodes(nt, tex, vec, box=True)
    # desaturate the scan, then multiply our colour so every fabric keeps its weave but takes the palette
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(T["albedo"], bw.inputs["Color"])
    lv = A.maprange(nt, bw.outputs["Val"], 0.0, 0.6, 0.55, 1.25, clamp=False)
    col = A.math_col_mul(nt, A.rgb(nt, A.hexc(hexcol)[:3]) if hasattr(A, "rgb") else _rgb(nt, A.hexc(hexcol)[:3]), lv)
    # grime toward hems and seams (low-frequency noise)
    g = A.maprange(nt, A.noise(nt, 6.0, tc.outputs["Object"], detail=3), 0.35, 0.75, 0.85, 1.05)
    col = A.math_col_mul(nt, col, g)
    nt.links.new(col, b.inputs["Base Color"])
    r = A.math_node(nt, "ADD", T["rough"], rough_add, clamp=True)
    if wax:
        r = A.math_node(nt, "MULTIPLY", r, 0.62)
    nt.links.new(r, b.inputs["Roughness"])
    # weave normal + large folds
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.8
    nt.links.new(T["normal"], nm.inputs["Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    fold_v = A.mapping(nt, (1.0, 1.0, 3.0), src=tc.outputs["Object"])
    nz = A.noise(nt, 7.0, fold_v, detail=3, rough=0.5)
    bump.inputs["Strength"].default_value = 0.45
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(nz, bump.inputs["Height"])
    nt.links.new(nm.outputs["Normal"], bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = 0.25 if not wax else 0.0
    return m


def _rgb(nt, c):
    n = nt.nodes.new("ShaderNodeRGB")
    n.outputs[0].default_value = (*c, 1.0)
    return n.outputs[0]


A.rgb = _rgb


def skin_mat(name, hexcol, beard_shadow=False):
    """Skin: subsurface, pore bump, colour variation (cheeks/nose/ears redder), painted brows and lips."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    base = A.hexc(hexcol)[:3]
    red = (min(1, base[0] * 1.25), base[1] * 0.78, base[2] * 0.78)
    col = _rgb(nt, base)
    # mottling
    mott = A.maprange(nt, A.noise(nt, 40.0, tc.outputs["Object"], detail=4), 0.35, 0.7, 0.0, 0.35)
    col = A.mixc(nt, mott, col, (*red, 1))
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    X, Y, Z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    ax = A.math_node(nt, "ABSOLUTE", X)

    def blob(cx, cz, cy, rx, rz, ry):
        dx = A.math_node(nt, "DIVIDE", A.math_node(nt, "SUBTRACT", ax, cx), rx)
        dz = A.math_node(nt, "DIVIDE", A.math_node(nt, "SUBTRACT", Z, cz), rz)
        dy = A.math_node(nt, "DIVIDE", A.math_node(nt, "SUBTRACT", Y, cy), ry)
        d = A.math_node(nt, "ADD", A.math_node(nt, "ADD", A.math_node(nt, "MULTIPLY", dx, dx), A.math_node(nt, "MULTIPLY", dz, dz)), A.math_node(nt, "MULTIPLY", dy, dy))
        return A.math_node(nt, "EXPONENT", A.math_node(nt, "MULTIPLY", d, -1.0))

    cheeks = blob(0.035, 1.545, 0.11, 0.025, 0.02, 0.04)
    col = A.mixc(nt, A.math_node(nt, "MULTIPLY", cheeks, 0.35), col, (*red, 1))
    nose = blob(0.0, 1.55, 0.14, 0.012, 0.02, 0.03)
    col = A.mixc(nt, A.math_node(nt, "MULTIPLY", nose, 0.3), col, (*red, 1))
    # brows: two short arcs above the eyes (eyes at |x| 0.033, z 1.574, front y ~0.12)
    brow = blob(0.034, 1.598, 0.125, 0.022, 0.0045, 0.03)
    brow_col = (base[0] * 0.18, base[1] * 0.15, base[2] * 0.13, 1)
    col = A.mixc(nt, A.math_node(nt, "MULTIPLY", brow, 0.85, clamp=True), col, brow_col)
    lips = blob(0.0, 1.515, 0.125, 0.022, 0.006, 0.03)
    col = A.mixc(nt, A.math_node(nt, "MULTIPLY", lips, 0.45, clamp=True), col, (base[0] * 0.8, base[1] * 0.45, base[2] * 0.45, 1))
    if beard_shadow:
        jaw = A.maprange(nt, Z, 1.54, 1.50, 0.0, 0.5)
        front = A.maprange(nt, Y, 0.02, 0.08, 0.0, 1.0)
        bs = A.math_node(nt, "MULTIPLY", jaw, front)
        col = A.mixc(nt, bs, col, (base[0] * 0.45, base[1] * 0.42, base[2] * 0.42, 1))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 0.35
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.012
    rn = A.maprange(nt, A.noise(nt, 90.0, tc.outputs["Object"], detail=2), 0.3, 0.7, 0.42, 0.62)
    nt.links.new(rn, b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.0008
    pores = nt.nodes.new("ShaderNodeTexVoronoi")
    pores.inputs["Scale"].default_value = 900.0
    nt.links.new(tc.outputs["Object"], pores.inputs["Vector"])
    nt.links.new(pores.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def eye_mat(name, iris_hex="#4E6A78"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "NORMALIZE"
    nt.links.new(tc.outputs["Object"], vm.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(vm.outputs[0], sep.inputs["Vector"])
    fwd = A.math_node(nt, "MULTIPLY", sep.outputs["Y"], -1.0)  # base mesh eyes look along -Y (local)
    iris = A.maprange(nt, fwd, 0.86, 0.89)
    pupil = A.maprange(nt, fwd, 0.965, 0.975)
    col = A.mixc(nt, iris, A.hexc("#D9D2C8"), A.hexc(iris_hex))
    col = A.mixc(nt, pupil, col, (0.01, 0.01, 0.01, 1))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    return m


def hair_mat(name, hexcol):
    m = A.flat_mat(name, A.hexc(hexcol), rough=0.45)
    b = A.bsdf(m)
    b.inputs["Specular IOR Level"].default_value = 0.6
    b.inputs["Sheen Weight"].default_value = 0.3
    return m


# ---------------------------------------------------------------- body
def load_body(level=2):
    with bpy.data.libraries.load(str(SRC)) as (_a, b):
        b.objects = ["GEO-body_male_realistic", "GEO-body_male_realistic.eye.L", "GEO-body_male_realistic.eye.R"]
    body, el, er = b.objects
    for o in (body, el, er):
        A.link(o)
    R = Matrix.Rotation(math.pi, 4, "Z")
    for e in (el, er):  # eye world = body.basis @ parent_inverse @ eye.basis; bake into the mesh, origin 0
        ew = body.matrix_basis @ e.matrix_parent_inverse @ e.matrix_basis
        e.parent = None
        e.data = e.data.copy()
        W = Matrix.Translation(-body.location) @ ew
        c = W.translation.copy()
        e.data.transform(Matrix.Translation(-c) @ W)
        e.matrix_basis = R @ Matrix.Translation(c)
    body.location = (0, 0, 0)
    body.rotation_euler = (0, 0, math.pi)
    _upd()
    mr = body.modifiers[0]
    mr.levels = level
    mr.render_levels = level
    activate(body)
    bpy.ops.object.modifier_apply(modifier=mr.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return body, el, er


def activate(o, only=True):
    if only:
        for x in bpy.context.view_layer.objects:
            x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def dress(o, kind):
    cfg = OUTFIT[kind]
    names = ["top", "bottom", "boots", "skin"]
    mats = cfg["mats"]
    o.data.materials.clear()
    o.data.materials.append(fabric(f"{kind}_top", mats["top"][0], mats["top"][1], mats["top"][2], wax=kind == "explorer"))
    o.data.materials.append(fabric(f"{kind}_bottom", mats["bottom"][0], mats["bottom"][1], mats["bottom"][2], wax=kind == "fisher"))
    o.data.materials.append(fabric(f"{kind}_boots", mats["boots"][0], mats["boots"][1], mats["boots"][2], rough_add=-0.1))
    o.data.materials.append(skin_mat(f"{kind}_skin", cfg["skin"], beard_shadow=cfg["beard"]))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    region = {}
    for v in bm.verts:  # narrower trunk (the base mesh is gym-built): x 0.9 below the neck
        k = 0.90 + 0.10 * max(0.0, min(1.0, (v.co.z - 1.47) / 0.05))
        if v.co.z > 0.85:
            v.co.x *= k
    for v in bm.verts:
        p = Vector((abs(v.co.x), v.co.y, v.co.z))
        ta, da = seg_t(p, SHOULDER * Vector((0.9, 1, 1)), WRIST * Vector((0.9, 1, 1)))
        is_arm = (p.x > 0.15 and p.z > 0.70 and da < 0.11 and ta > 0.05) or (p.x > 0.30 and 0.66 < p.z < 1.2)
        if is_arm:
            r = "skin" if ta > cfg["sleeve"] else "top_arm"
            if kind == "trader" and ta > cfg["sleeve"] - 0.02 and ta <= cfg["sleeve"]:
                r = "top_arm"
        elif p.z < cfg["bottom_lo"]:
            r = "boots"
        elif p.z < cfg["hem"]:
            r = "bottom"
        elif p.z > cfg["collar"]:
            r = "skin"
        else:
            r = "top"
        if kind == "trader" and r == "boots" and p.z > 0.035:
            r = "skin"  # sandals: bare feet above the sole
        region[v.index] = (r, ta)
    cloth = [v for v in bm.verts if region[v.index][0] in ("top", "top_arm", "bottom")]
    # slim the gym-built base mesh: pull cloth-covered verts toward the nearest bone segment
    segs = []
    for n, (h, t, _p) in BONES.items():
        if n in ("root", "head", "neck") or n.startswith("hand") or n.startswith("foot"):
            continue
        segs.append((Vector(h), Vector(t)))
        if n.endswith(".L"):
            segs.append((Vector((-h[0], h[1], h[2])), Vector((-t[0], t[1], t[2]))))
    for v in cloth:
        best = None
        for h, t in segs:
            tt, d = seg_t(v.co, h, t)
            if best is None or d < best[0]:
                q = h + (t - h) * max(0.0, min(1.0, tt))
                best = (d, q)
        r = region[v.index][0]
        k = 0.86 if r != "top" else 0.88
        if r == "top" and v.co.y > 0.0:
            k = 0.92  # keep the chest depth, slim the lats and shoulders
        v.co = best[1] + (v.co - best[1]) * k
    for _ in range(12):
        bmesh.ops.smooth_vert(bm, verts=cloth, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    # relaxed hands: curl the fingers about 40 deg (Race Riders grip curl, softer)
    hand_dir = (TIP - WRIST).normalized()
    kn = WRIST + (TIP - WRIST) * 0.45
    for v in bm.verts:
        p = Vector((abs(v.co.x), v.co.y, v.co.z))
        ta, da = seg_t(p, SHOULDER, WRIST)
        if region[v.index][0] != "skin" or p.z > 1.2 or p.x < 0.3:
            continue
        t = (p - kn).dot(hand_dir)
        if t > 0:
            axis = hand_dir.cross(Vector((-1.0, 0.0, 0.0))).normalized()
            ang = min(1.0, t / 0.07) * math.radians(55)
            q = Matrix.Rotation(-ang, 3, axis) @ (p - kn) + kn
            sx = 1.0 if v.co.x >= 0 else -1.0
            v.co = Vector((q.x * sx, q.y, q.z))
    bm.normal_update()
    new = {}
    for v in bm.verts:
        r, ta = region[v.index]
        p = Vector((abs(v.co.x), v.co.y, v.co.z))
        d = 0.0
        if r == "top":
            d = 0.024 if kind == "explorer" else 0.022
            d += 0.012 * max(0.0, min(1.0, (cfg["hem"] + 0.08 - p.z) / 0.08))  # hem flares
            d -= 0.014 * max(0.0, min(1.0, (p.z - (cfg["collar"] - 0.05)) / 0.05))
            if kind == "explorer":  # chest pockets
                pk = math.exp(-(((p.x - 0.085) / 0.04) ** 2 + ((p.z - 1.28) / 0.05) ** 2)) * (v.co.y > 0.05)
                d += 0.012 * pk
        elif r == "top_arm":
            d = 0.021 if kind != "trader" else 0.028
            d += 0.012 * max(0.0, min(1.0, (ta - 0.3) / 0.4)) * (kind == "trader")
            d -= 0.004 * max(0.0, min(1.0, (ta - 0.85) / 0.1))
        elif r == "bottom":
            d = 0.024
            d += 0.010 * max(0.0, min(1.0, (p.z - 0.4) / 0.3)) * (p.z < 0.9)
            d += 0.030 * max(0.0, min(1.0, (0.62 - p.z) / 0.4))  # straight leg, room over the boot
            if kind == "explorer":  # cargo pockets on the thighs
                cp = math.exp(-(((p.z - 0.62) / 0.06) ** 2)) * (p.x > 0.13)
                d += 0.014 * cp
            if kind == "trader":
                d += 0.03 * max(0.0, min(1.0, (0.75 - p.z) / 0.5))  # loose trousers
        elif r == "boots":
            d = 0.016 if kind != "trader" else 0.004
        new[v.index] = v.co + v.normal * d
    for v in bm.verts:
        v.co = new[v.index]
    mid = {"top": 0, "top_arm": 0, "bottom": 1, "boots": 2, "skin": 3}
    for f in bm.faces:
        votes = [mid[region[v.index][0]] for v in f.verts]
        f.material_index = max(set(votes), key=votes.count)
    # boots: replace the toes by a convex hull (sole, round toe)
    foot = [v for v in bm.verts if v.co.z < 0.10]
    hulls = []
    for side in (-1, 1):
        pts = [v.co.copy() for v in foot if v.co.x * side > 0]
        cen = sum(pts, Vector()) / len(pts)
        pts = [Vector((cen.x + (q.x - cen.x) * 1.12, cen.y + (q.y - cen.y) * 1.06, max(q.z, 0.0))) for q in pts]
        pts += [Vector((q.x, q.y, 0.0)) for q in pts if q.z < 0.03]
        hulls.append(pts)
    bmesh.ops.delete(bm, geom=foot, context="VERTS")
    for pts in hulls:
        hv = [bm.verts.new(c) for c in pts]
        res = bmesh.ops.convex_hull(bm, input=hv)
        for g in res["geom_interior"] + res["geom_unused"]:
            if isinstance(g, bmesh.types.BMVert) and g.is_valid and not g.link_faces:
                bm.verts.remove(g)
        for g in res["geom"]:
            if isinstance(g, bmesh.types.BMFace):
                g.material_index = 2
    bm.to_mesh(o.data)
    bm.free()
    for p in o.data.polygons:
        p.use_smooth = True
    return names


# ---------------------------------------------------------------- gear (own modelling)
def rounded_box(name, size, loc, bevel=0.03, mat=None, segs=4):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bv = o.modifiers.new("bev", "BEVEL")
    bv.width = bevel
    bv.segments = segs
    sd = o.modifiers.new("sub", "SUBSURF")
    sd.levels = 1
    sd.render_levels = 2
    if mat:
        o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def tube(name, pts, r, mat, res=10):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    o = A.link(bpy.data.objects.new(name, cu))
    o.data.materials.append(mat)
    return o


def strap(name, pts, w, t, mat):
    """Flat strap along points (ribbon with thickness)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.extrude = w / 2
    cu.bevel_depth = 0
    cu.offset = 0
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    sp.use_endpoint_u = True
    sp.order_u = 3
    o = A.link(bpy.data.objects.new(name, cu))
    o.data.materials.append(mat)
    sol = o.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = t
    return o


def gear_explorer():
    canvas = fabric("pack_canvas", "hessian_230", "#8C7A55", 3.0)
    leather = fabric("pack_leather", "brown_leather", "#5A3A24", 4.0, rough_add=-0.15)
    wool = fabric("bedroll", "knitted_fleece", "#6E6A62", 5.0)
    scarf = fabric("scarf", "knitted_fleece", "#9A4A2A", 6.0)
    parts = []
    # backpack body on the back (back = -Y), main bag + lid + side pocket
    parts.append(rounded_box("pack", (0.33, 0.19, 0.48), (0, -0.20, 1.17), 0.06, canvas))
    parts.append(rounded_box("pack_lid", (0.34, 0.21, 0.10), (0, -0.20, 1.41), 0.04, canvas))
    parts.append(rounded_box("pack_pocket", (0.24, 0.07, 0.20), (0, -0.33, 1.08), 0.03, canvas))
    for sx in (-1, 1):
        parts.append(rounded_box(f"pack_side{sx}", (0.06, 0.13, 0.20), (sx * 0.19, -0.215, 1.07), 0.025, canvas))
        # lid buckle straps
        parts.append(strap(f"lid_strap{sx}", [(sx * 0.08, -0.33, 1.47), (sx * 0.08, -0.335, 1.38), (sx * 0.08, -0.32, 1.20)], 0.03, 0.004, leather))
        # shoulder straps over the shoulders to the front
        parts.append(strap(f"shoulder_strap{sx}", [(sx * 0.10, -0.10, 1.40), (sx * 0.11, -0.04, 1.465), (sx * 0.115, 0.05, 1.45), (sx * 0.11, 0.125, 1.33), (sx * 0.12, 0.125, 1.10)], 0.045, 0.006, leather))
    # bedroll on top of the lid
    bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.46, location=(0, -0.20, 1.525), rotation=(0, math.pi / 2, 0), vertices=24)
    br = bpy.context.active_object
    br.name = "bedroll"
    br.data.materials.append(wool)
    for p in br.data.polygons:
        p.use_smooth = True
    parts.append(br)
    for sx in (-0.13, 0.13):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.079, minor_radius=0.006, location=(sx, -0.20, 1.525), rotation=(0, math.pi / 2, 0))
        t = bpy.context.active_object
        t.data.materials.append(leather)
        parts.append(t)
    # scarf round the neck
    bpy.ops.mesh.primitive_torus_add(major_radius=0.075, minor_radius=0.03, location=(0, 0.01, 1.475), major_segments=32, minor_segments=12)
    sc = bpy.context.active_object
    sc.scale = (1.0, 1.05, 0.85)
    sc.rotation_euler = (math.radians(-10), 0, 0)
    sc.data.materials.append(scarf)
    for p in sc.data.polygons:
        p.use_smooth = True
    parts.append(sc)
    # bucket hat (Poly Haven fishermans_hat)
    c = A.proto("fishermans_hat")
    hat = []
    for src in c.objects:
        o = src.copy()
        o.data = src.data.copy()
        A.link(o)
        hat.append(o)
    lo, hi = A.bounds(hat)
    size = hi - lo
    s = 0.33 / max(size.x, size.y)
    for o in hat:
        o.matrix_world = Matrix.Translation((0, 0.008, 1.585)) @ Matrix.Rotation(math.radians(-5), 4, "X") @ Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + size.z * 0.12))) @ o.matrix_world
    parts += hat
    return parts


def gear_fisher():
    knit = fabric("cap_knit", "knitted_fleece", "#7A2B22", 8.0)
    oil = fabric("apron_oil", "brown_leather", "#2E3B44", 2.0, rough_add=-0.25)
    parts = []
    # knit cap: upper skull shell + folded cuff
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105, location=(0, 0.0, 1.63), segments=32, ring_count=16)
    cap = bpy.context.active_object
    cap.scale = (0.93, 1.05, 0.98)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(cap.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.005 + (0.03 if v.co.y > 0.04 else -0.01)], context="VERTS")
    bm.to_mesh(cap.data)
    bm.free()
    cap.data.materials.append(knit)
    cap.modifiers.new("sol", "SOLIDIFY").thickness = 0.008
    for p in cap.data.polygons:
        p.use_smooth = True
    parts.append(cap)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.022, location=(0, 0.005, 1.632), major_segments=40, minor_segments=10)
    cuff = bpy.context.active_object
    cuff.scale = (0.97, 1.08, 1.0)
    cuff.rotation_euler = (math.radians(-14), 0, 0)
    cuff.data.materials.append(knit)
    parts.append(cuff)
    # oilskin bib front panel (over the sweater)
    parts.append(rounded_box("bib", (0.30, 0.03, 0.30), (0, 0.135, 1.05), 0.01, oil, segs=2))
    for sx in (-1, 1):
        parts.append(strap(f"brace{sx}", [(sx * 0.10, 0.15, 1.19), (sx * 0.12, 0.12, 1.36), (sx * 0.13, 0.0, 1.45), (sx * 0.10, -0.13, 1.30), (sx * 0.08, -0.15, 0.98)], 0.035, 0.004, oil))
    return parts


def gear_trader():
    wrap = fabric("head_wrap", "rough_linen", "#B8863A", 5.0)
    sash = fabric("sash", "fabric_pattern_07", "#8C3B2A", 4.0)
    parts = []
    for i, (z, r) in enumerate(((1.62, 0.108), (1.655, 0.104), (1.69, 0.092), (1.715, 0.07))):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.026, location=(0, 0.0, z), major_segments=40, minor_segments=10)
        t = bpy.context.active_object
        t.scale = (0.92, 1.05, 1.0)
        t.rotation_euler = (math.radians(-8 + i * 3), math.radians(4 * (i % 2) - 2), 0)
        t.data.materials.append(wrap)
        parts.append(t)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, location=(0, -0.005, 1.68), segments=24, ring_count=12)
    t = bpy.context.active_object
    t.scale = (1.0, 1.15, 0.6)
    t.data.materials.append(wrap)
    parts.append(t)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.04, location=(0, 0.0, 0.93), major_segments=40, minor_segments=10)
    s = bpy.context.active_object
    s.scale = (1.0, 0.82, 0.9)
    s.data.materials.append(sash)
    parts.append(s)
    return parts


GEAR = {"explorer": gear_explorer, "fisher": gear_fisher, "trader": gear_trader}


def hair_groups(body, kind):
    """Rest-pose masks (vertex groups) for the scalp crop and the beard; soft edges by distance."""
    cfg = OUTFIT[kind]
    vg_s = body.vertex_groups.new(name="scalp")
    vg_b = body.vertex_groups.new(name="beard")
    for v in body.data.vertices:
        p = v.co
        ax = abs(p.x)
        # hairline: forehead at z 1.655, temples recede, sideburns to z 1.575, nape to z 1.50
        if p.y > 0.085:
            line = 1.66
        elif p.y > 0.03:
            line = 1.66 - (0.085 - p.y) * 1.4
        else:
            line = 1.50 + max(0.0, ax - 0.04) * 0.6
        ear = ax > 0.068 and 1.535 < p.z < 1.605 and -0.03 < p.y < 0.035
        if p.z > line and not ear and p.z > 1.47:
            w = min(1.0, (p.z - line) / 0.012)
            vg_s.add([v.index], w, "REPLACE")
        if cfg["beard"] and 1.462 < p.z < 1.565 and p.y > 0.02:
            top = 1.560 - 0.6 * max(0.0, 0.06 - ax)  # cheek line drops toward the nose
            mouth = ax < 0.026 and 1.503 < p.z < 1.524 and p.y > 0.095
            neck_line = 1.462 + 0.35 * max(0.0, 0.10 - p.y)
            if p.z < top and not mouth and p.z > neck_line:
                w = min(1.0, (top - p.z) / 0.012, (p.z - neck_line) / 0.015)
                vg_b.add([v.index], max(0.05, w), "REPLACE")


def hair_mat_shell(name, hexcol, strand_scale=(260.0, 260.0, 40.0), alpha_cut=0.35):
    """Short hair as a shell (the phone approach): strand-stretched noise for colour and bump, alpha by
    the mask weight x noise so the edge breaks up instead of ending in a line."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = A.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "mask"
    vec = A.mapping(nt, strand_scale, src=tc.outputs["Object"])
    st = A.noise(nt, 1.0, vec, detail=8, rough=0.7)
    base = A.hexc(hexcol)[:3]
    col = A.mixc(nt, A.maprange(nt, st, 0.3, 0.7), (base[0] * 0.55, base[1] * 0.55, base[2] * 0.55, 1), (min(1, base[0] * 1.5), min(1, base[1] * 1.5), min(1, base[2] * 1.5), 1))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Sheen Weight"].default_value = 0.5
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(st, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    fine = A.noise(nt, 1.0, A.mapping(nt, (900.0, 900.0, 120.0), src=tc.outputs["Object"]), detail=2)
    a = A.math_node(nt, "MULTIPLY", attr.outputs["Fac"], A.maprange(nt, fine, 0.3, 0.6, 0.4, 1.3))
    a = A.math_node(nt, "GREATER_THAN", a, alpha_cut)
    nt.links.new(a, b.inputs["Alpha"])
    try:
        m.surface_render_method = "DITHERED"
    except Exception:  # noqa: BLE001
        pass
    return m


def hair_shells(body, kind):
    cfg = OUTFIT[kind]
    out = []
    layers = [("scalp", 0.0035, 1.0)]
    if cfg["beard"]:
        layers += [("beard", 0.0025, 1.0), ("beard", 0.0055, 0.75), ("beard", 0.0085, 0.5)]
    mat_s = hair_mat_shell(f"{kind}_hair", cfg["hair"])
    for gname, off, wmul in layers:
        vg = body.vertex_groups[gname]
        bm = bmesh.new()
        bm.from_mesh(body.data)
        dl = bm.verts.layers.deform.verify()
        wts = {}
        for v in bm.verts:
            w = v[dl].get(vg.index, 0.0)
            wts[v.index] = w
        bm.normal_update()
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if wts[v.index] <= 0.0], context="VERTS")
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            v.co += v.normal * off * (0.6 + 0.4 * v[dl].get(vg.index, 0.0))
        me = bpy.data.meshes.new(f"{kind}_{gname}_{off}")
        bm.to_mesh(me)
        bm.free()
        o = A.link(bpy.data.objects.new(me.name, me))
        o.matrix_world = body.matrix_world
        at = me.attributes.new("mask", "FLOAT", "POINT")
        for i, v in enumerate(me.vertices):
            w = 0.0
            for g in v.groups:
                if g.group == vg.index:
                    w = g.weight
            at.data[i].value = w * wmul
        me.materials.clear()
        me.materials.append(mat_s)
        for p in me.polygons:
            p.use_smooth = True
        out.append(o)
    return out


# ---------------------------------------------------------------- rig and pose
def weights(body, rig):
    """Inverse-distance (power 4) weights to the bone segments a vertex may belong to (arm, leg or trunk
    chain by region). Heat weighting fails on the dressed multires mesh, this never does."""
    bones = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in rig.data.bones}
    groups = {n: body.vertex_groups.get(n) or body.vertex_groups.new(name=n) for n in bones}
    trunk = ["hips", "spine", "chest", "neck", "head"]
    for v in body.data.vertices:
        p = v.co
        s = "L" if p.x < 0 else "R"
        q = Vector((abs(p.x), p.y, p.z))
        ta, da = seg_t(q, SHOULDER, WRIST)
        is_arm = (q.x > 0.165 and q.z > 0.70 and da < 0.13 and ta > 0.05) or (q.x > 0.30 and 0.6 < q.z < 1.2)
        if is_arm:
            cand = [f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}", "chest"]
        elif q.z < 0.98 and q.x > 0.012:
            cand = [f"thigh.{s}", f"shin.{s}", f"foot.{s}", "hips"]
        else:
            cand = trunk + [f"shoulder.{s}"]
        ws = []
        for n in cand:
            h, t = bones[n]
            _tt, d = seg_t(p, h, t)
            ws.append((n, 1.0 / (d + 0.01) ** 4))
        tot = sum(w for _n, w in ws)
        for n, w in ws:
            w /= tot
            if w > 0.01:
                groups[n].add([v.index], w, "REPLACE")



def build_armature(name):
    ad = bpy.data.armatures.new(name)
    ob = A.link(bpy.data.objects.new(name, ad))
    activate(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones
    spec = dict(BONES)
    for n, (h, t, par) in BONES.items():
        if n.endswith(".L"):
            pr = par.replace(".L", ".R") if par and par.endswith(".L") else par
            spec[n[:-2] + ".R"] = ((-h[0], h[1], h[2]), (-t[0], t[1], t[2]), pr)
    for n, (h, t, _p) in spec.items():
        b = eb.new(n)
        b.head, b.tail = h, t
        d = Vector(t) - Vector(h)
        b.align_roll(Vector((0, 0, 1)) if abs(d.normalized().z) < 0.6 else Vector((0, -1, 0)))
    for n, (_h, _t, par) in spec.items():
        if par:
            eb[n].parent = eb[par]
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


def _rest3(pb):
    return pb.bone.matrix_local.to_3x3()


def _cur_rot(pb):
    return pb.matrix.to_3x3() @ _rest3(pb).inverted()


def _head_now(pb):
    if pb.parent is None:
        return pb.bone.head_local.copy()
    par = pb.parent
    return par.matrix @ (par.bone.matrix_local.inverted() @ pb.bone.head_local)


def _upd():
    bpy.context.view_layer.update()


def aim(pb, direction, twist=0.0):
    base = (_cur_rot(pb.parent) if pb.parent else Matrix.Identity(3)) @ _rest3(pb)
    y = base.col[1]
    rd = y.rotation_difference(Vector(direction).normalized()).to_matrix()
    m3 = rd @ base
    if twist:
        m3 = Matrix.Rotation(twist, 3, m3.col[1]) @ m3
    pb.matrix = Matrix.Translation(_head_now(pb)) @ m3.to_4x4()
    _upd()


def rot_local(pb, rx=0.0, ry=0.0, rz=0.0):
    """Rotate a bone about armature X/Y/Z axes (degrees) around its head, keeping its parent's motion."""
    base = (_cur_rot(pb.parent) if pb.parent else Matrix.Identity(3)) @ _rest3(pb)
    R = (Matrix.Rotation(math.radians(rz), 3, "Z") @ Matrix.Rotation(math.radians(ry), 3, "Y") @ Matrix.Rotation(math.radians(rx), 3, "X"))
    pb.matrix = Matrix.Translation(_head_now(pb)) @ (R @ base).to_4x4()
    _upd()


def two_bone(up, lo, target, pole):
    s = _head_now(up)
    l1 = (up.bone.tail_local - up.bone.head_local).length
    l2 = (lo.bone.tail_local - lo.bone.head_local).length
    t = Vector(target)
    d = min((t - s).length, l1 + l2 - 1e-3)
    n = (t - s).normalized()
    pv = Vector(pole) - n * Vector(pole).dot(n)
    pv.normalize()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - a * a))
    j = s + n * a + pv * hh
    aim(up, j - s)
    aim(lo, (s + n * d) - j)


POSES = {
    # stand, weight on the left leg, right hand on the pack strap, head turned to the view
    "stand_look": dict(spine=(2, 0, -4), chest=(0, 0, -4), head=(4, 0, -14), hips_shift=(0.015, 0, 0),
                       wristL=(-0.215, 0.05, 0.86), elbowL=(-0.3, -1, 0), handL=(-0.05, 0.12, -1),
                       wristR=(0.215, 0.07, 0.87), elbowR=(0.3, -1, 0), handR=(0.05, 0.15, -1),
                       ankleL=(-0.11, 0.0, 0.085), ankleR=(0.16, 0.12, 0.09), kneeL=(0, 1, 0), kneeR=(0.3, 1, 0)),
    # walking stride, left foot forward
    "walk": dict(spine=(4, 0, 0), chest=(-2, 0, 6), head=(-2, 0, -6), hips_shift=(0, 0, -0.02),
                 wristL=(-0.2, -0.17, 0.88), elbowL=(-0.4, -1, 0), handL=(0, -0.2, -1),
                 wristR=(0.13, 0.15, 1.12), elbowR=(1, -0.6, -0.3), handR=(-0.4, 0.4, 0.6),
                 ankleL=(-0.11, 0.30, 0.10), ankleR=(0.11, -0.28, 0.16), kneeL=(0, 1, 0), kneeR=(0, 1, 0)),
    # NPC talking: weight back, left hand gestures toward the camera-left, right thumb in the brace
    "talk": dict(spine=(-2, 0, 0), chest=(0, 3, 0), head=(-4, 5, 8), hips_shift=(-0.01, 0, 0),
                 wristL=(-0.30, 0.30, 1.10), elbowL=(-1, -0.6, -0.5), handL=(-0.6, 0.9, 0.3),
                 wristR=(0.19, 0.07, 0.92), elbowR=(1, -0.5, 0), handR=(0.2, 0.2, -1),
                 ankleL=(-0.13, 0.04, 0.085), ankleR=(0.12, -0.04, 0.085), kneeL=(-0.2, 1, 0), kneeR=(0.1, 1, 0)),
    # trader at a stall, both hands resting forward
    "vend": dict(spine=(8, 0, 0), chest=(6, 0, 0), head=(-6, 0, 10), hips_shift=(0, 0, 0),
                 wristL=(-0.18, 0.32, 1.0), elbowL=(-1, -0.4, -0.6), handL=(0, 1, -0.4),
                 wristR=(0.18, 0.32, 1.0), elbowR=(1, -0.4, -0.6), handR=(0, 1, -0.4),
                 ankleL=(-0.12, 0.0, 0.085), ankleR=(0.12, 0.0, 0.085), kneeL=(0, 1, 0), kneeR=(0, 1, 0)),
}


def apply_pose(rig, P):
    activate(rig)
    bpy.ops.object.mode_set(mode="POSE")
    pbs = rig.pose.bones
    for pb in pbs:
        pb.matrix_basis = Matrix.Identity(4)
    _upd()
    h = pbs["hips"]
    h.matrix = Matrix.Translation(Vector(P["hips_shift"])) @ h.matrix
    _upd()
    rot_local(pbs["spine"], *P["spine"])
    rot_local(pbs["chest"], *P["chest"])
    rot_local(pbs["neck"], P["head"][0] * 0.4, P["head"][1] * 0.4, P["head"][2] * 0.4)
    rot_local(pbs["head"], P["head"][0] * 0.6, P["head"][1] * 0.6, P["head"][2] * 0.6)
    for s in ("L", "R"):
        two_bone(pbs[f"upper_arm.{s}"], pbs[f"forearm.{s}"], P[f"wrist{s}"], P[f"elbow{s}"])
        aim(pbs[f"hand.{s}"], P[f"hand{s}"])
        two_bone(pbs[f"thigh.{s}"], pbs[f"shin.{s}"], P[f"ankle{s}"], P[f"knee{s}"])
        aim(pbs[f"foot.{s}"], (0.0, 1.0, -0.42))
    bpy.ops.object.mode_set(mode="OBJECT")


def character(kind, pose_name, loc=(0, 0, 0), yaw_deg=0.0, level=2, scale=1.0):
    """Build, skin, pose and place one character. Returns (rig, [objects])."""
    body, el, er = load_body(level)
    body.name = f"{kind}_body"
    dress(body, kind)
    hair_groups(body, kind)
    em = eye_mat(f"{kind}_eye", "#5B4636" if kind != "explorer" else "#4E6A78")
    for e in (el, er):
        e.data.materials.clear()
        e.data.materials.append(em)
    gear = GEAR[kind]()
    rig = build_armature(f"{kind}_rig")
    # skin the body (heat weights), gear and eyes follow head/chest bones rigidly
    activate(body)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_NAME")
    weights(body, rig)
    for g in gear + [el, er]:
        if g.type not in ("MESH", "CURVE"):
            continue
        lo, hi = A.bounds([g]) if g.type == "MESH" else (Vector((0, 0, 1.5)), Vector((0, 0, 1.5)))
        cz = (lo.z + hi.z) / 2 if g.type == "MESH" else 1.4
        bone = "head" if cz > 1.53 and g.name.find("bedroll") < 0 and "lid" not in g.name else ("hips" if cz < 1.0 else "chest")
        if g.name.startswith("bedroll") or g.name.startswith("Torus") and cz > 1.5 and abs((lo.y + hi.y) / 2 + 0.21) < 0.05:
            bone = "chest"
        mw = g.matrix_world.copy()
        g.parent = rig
        g.parent_type = "BONE"
        g.parent_bone = bone
        g.matrix_world = mw
    apply_pose(rig, POSES[pose_name])
    # bake the pose into the body so particle hair grows on the posed surface
    activate(body)
    for m in list(body.modifiers):
        if m.type == "ARMATURE":
            bpy.ops.object.modifier_apply(modifier=m.name)
    body.parent = None
    shells = hair_shells(body, kind)
    root = bpy.data.objects.new(f"{kind}_root", None)
    A.link(root)
    for o in [body, rig] + shells:
        mw = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = mw
    root.location = loc
    root.rotation_euler = (0, 0, math.radians(yaw_deg))
    root.scale = (scale,) * 3
    _upd()
    return rig, [body, el, er] + gear + shells
