"""Own-modelled gear for the MakeHuman characters (backpack, bedroll, straps) plus the Poly Haven
fishermans_hat. Built in the rig's REST space (MakeHuman: front -Y, left +X) and parented to bones, so the
pose carries it."""

from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

import wf_art as A
import wf_char as C


def _ray_back(z, x=0.0):
    """Distance of the clothed back surface at height z (rest pose): cast from +Y toward the body."""
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, 1.5, z)), Vector((0, -1, 0)))
    return loc.y if hit else 0.13


def _top(objs):
    return max(A.bounds([o])[1].z for o in objs if o.type == "MESH")


def explorer(rig, kids):
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()
    canvas = C.fabric("pack_canvas", "hessian_230", "#7E6E4E", 3.0)
    leather = C.fabric("pack_leather", "brown_leather", "#4E3220", 4.0, rough_add=-0.15)
    wool = C.fabric("bedroll", "knitted_fleece", "#5E5B55", 5.0)
    top = _top([k for k in kids if k.name.endswith(".body")])
    sh = top - 0.33  # shoulder line
    yb = max(_ray_back(sh - 0.20), _ray_back(sh - 0.10))
    d = 0.20
    yc = yb + d / 2 + 0.01
    parts = []
    parts.append(C.rounded_box("pack", (0.32, d, 0.50), (0, yc, sh - 0.25), 0.06, canvas))
    parts.append(C.rounded_box("pack_lid", (0.33, d + 0.02, 0.10), (0, yc + 0.005, sh + 0.01), 0.04, canvas))
    parts.append(C.rounded_box("pack_pocket", (0.23, 0.07, 0.20), (0, yc + d / 2 + 0.02, sh - 0.33), 0.03, canvas))
    for sx in (-1, 1):
        parts.append(C.rounded_box(f"pack_side{sx}", (0.06, 0.12, 0.20), (sx * 0.18, yc, sh - 0.34), 0.025, canvas))
        parts.append(C.strap(f"lid_strap{sx}", [(sx * 0.08, yc + d / 2 + 0.02, sh + 0.05), (sx * 0.08, yc + d / 2 + 0.025, sh - 0.04), (sx * 0.08, yc + d / 2 + 0.015, sh - 0.2)], 0.03, 0.004, leather))
        parts.append(C.strap(f"shoulder_strap{sx}", [(sx * 0.10, yb + 0.02, sh - 0.02), (sx * 0.115, yb - 0.06, sh + 0.035), (sx * 0.12, yb - 0.16, sh + 0.02), (sx * 0.12, yb - 0.24, sh - 0.12), (sx * 0.13, yb - 0.24, sh - 0.32)], 0.045, 0.006, leather))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.46, location=(0, yc, sh + 0.13), rotation=(0, math.pi / 2, 0), vertices=32)
    br = bpy.context.active_object
    br.name = "bedroll"
    br.data.materials.append(wool)
    for p in br.data.polygons:
        p.use_smooth = True
    parts.append(br)
    for sx in (-0.14, 0.14):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.079, minor_radius=0.006, location=(sx, yc, sh + 0.13), rotation=(0, math.pi / 2, 0))
        t = bpy.context.active_object
        t.data.materials.append(leather)
        parts.append(t)
    for p in parts:
        C.activate(p)
        bpy.ops.object.convert(target="MESH")
    parts = [bpy.context.view_layer.objects.get(p.name) or p for p in parts]
    for p in parts:
        mw = p.matrix_world.copy()
        p.parent = rig
        p.parent_type = "BONE"
        p.parent_bone = "spine02"
        p.matrix_world = mw
    rig.data.pose_position = "POSE"
    return parts


def hat(rig, kids, width=0.35, sink=0.115, tilt=-4.0):
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()
    top = _top([k for k in kids if k.name.endswith(".body")])
    c = A.proto("fishermans_hat")
    out = []
    for src in c.objects:
        o = src.copy()
        o.data = src.data.copy()
        A.link(o)
        out.append(o)
    lo, hi = A.bounds(out)
    size = hi - lo
    s = width / max(size.x, size.y)
    hb = rig.data.bones["head"].head_local
    T = Matrix.Translation((0, hb.y + 0.01, top - sink)) @ Matrix.Rotation(math.radians(tilt), 4, "X") @ Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)))
    for o in out:
        o.matrix_world = T @ o.matrix_world
        mw = o.matrix_world.copy()
        o.parent = rig
        o.parent_type = "BONE"
        o.parent_bone = "head"
        o.matrix_world = mw
    rig.data.pose_position = "POSE"
    return out


GEAR = {
    "explorer": explorer,
    "fisher": lambda rig, kids: hat(rig, kids),
    "ingrid": lambda rig, kids: [],
    "trader": lambda rig, kids: [],
}
