"""MakeHuman-based characters (MPFB 2 + MakeHuman system assets, both CC0 assets) for the Wayfarer drafts.

Run Blender with BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user so the MPFB extension and its asset
library load from inside the workspace (installed there by tools/art/setup_mpfb.sh).
Characters face -Y in MakeHuman; human(...) turns them to face +Y like the rest of the kit.
"""

from __future__ import annotations

import math

import addon_utils
import bpy
from mathutils import Euler, Matrix, Vector

import wf_art as A

MOD = "bl_ext.user_default.mpfb"


def enable():
    if MOD not in bpy.context.preferences.addons:
        addon_utils.enable(MOD, default_set=True, persistent=True)
    import importlib

    return importlib.import_module(MOD + ".services.humanservice").HumanService


PRESETS = {
    "explorer": dict(
        phenotype=dict(gender=1.0, age=0.56, muscle=0.6, weight=0.45, proportions=0.75, height=0.6, cupsize=0.5, firmness=0.5,
                       race=dict(asian=0.0, caucasian=0.85, african=0.15)),
        skin="young_caucasian_male2/young_caucasian_male2.mhmat", hair="short02/short02.mhclo",
        eyebrows="eyebrow001/eyebrow001.mhclo", clothes=["male_casualsuit05/male_casualsuit05.mhclo", "shoes03/shoes03.mhclo"],
    ),
    "fisher": dict(
        phenotype=dict(gender=1.0, age=0.85, muscle=0.55, weight=0.62, proportions=0.6, height=0.5, cupsize=0.5, firmness=0.5,
                       race=dict(asian=0.0, caucasian=1.0, african=0.0)),
        skin="old_caucasian_male/old_caucasian_male.mhmat", hair="short04/short04.mhclo",
        eyebrows="eyebrow006/eyebrow006.mhclo", clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"],
    ),
    "trader": dict(
        phenotype=dict(gender=1.0, age=0.7, muscle=0.5, weight=0.55, proportions=0.6, height=0.55, cupsize=0.5, firmness=0.5,
                       race=dict(asian=0.2, caucasian=0.3, african=0.5)),
        skin="middleage_african_male/middleage_african_male.mhmat", hair="short01/short01.mhclo",
        eyebrows="eyebrow002/eyebrow002.mhclo", clothes=["male_casualsuit06/male_casualsuit06.mhclo", "shoes01/shoes01.mhclo"],
    ),
}


def human(kind, name=None):
    HS = enable()
    p = PRESETS[kind]
    info = HS._create_default_human_info_dict()
    info["phenotype"] = p["phenotype"]
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"
    info["eyebrows"] = p["eyebrows"]
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
    info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["hair"] = p["hair"]
    info["clothes"] = p["clothes"]
    info["skin_mhmat"] = p["skin"]
    info["skin_material_type"] = "ENHANCED_SSS"
    info["eyes_material_type"] = "PROCEDURAL_EYES"
    info["name"] = name or kind
    st = HS.get_default_deserialization_settings()
    st["subdiv_levels"] = 1
    basemesh = HS.deserialize_from_dict(info, st)
    rig = basemesh.parent if basemesh.parent and basemesh.parent.type == "ARMATURE" else None
    return basemesh, rig


# ---------------------------------------------------------------- recolour (MakeHuman clothes share one atlas)
def recolor(obj, hue_lo, hue_hi, sat_min, target_hue, target_sat, value_mul, sat_mul=None):
    """Re-dye the pixels of one hue band (e.g. the blue jeans) in every material of obj. Shader-only:
    texture -> HSV, band mask, swap hue/sat, scale value. Godot/Unity: same 6-node trick or bake it."""
    for slot in obj.material_slots:
        m = slot.material
        if m is None or not m.use_nodes:
            continue
        nt = m.node_tree
        b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is None or not b.inputs["Base Color"].is_linked:
            continue
        src = b.inputs["Base Color"].links[0].from_socket
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.mode = "HSV"
        nt.links.new(src, sep.inputs["Color"])
        h, s, v = sep.outputs[0], sep.outputs[1], sep.outputs[2]
        m1 = A.maprange(nt, h, hue_lo - 0.03, hue_lo)
        m2 = A.maprange(nt, h, hue_hi + 0.03, hue_hi)
        m3 = A.maprange(nt, s, sat_min - 0.05, sat_min)
        mask = A.math_node(nt, "MULTIPLY", A.math_node(nt, "MULTIPLY", m1, m2), m3)
        comb = nt.nodes.new("ShaderNodeCombineColor")
        comb.mode = "HSV"
        comb.inputs[0].default_value = target_hue
        if sat_mul is None:
            comb.inputs[1].default_value = target_sat
        else:
            nt.links.new(A.math_node(nt, "MULTIPLY", s, sat_mul, clamp=True), comb.inputs[1])
        nt.links.new(A.math_node(nt, "MULTIPLY", v, value_mul, clamp=True), comb.inputs[2])
        out = A.mixc(nt, mask, src, comb.outputs[0])
        nt.links.new(out, b.inputs["Base Color"])


def tame_eyes(objs):
    """Procedural MPFB eyes read too bright under a sun: lower the sclera/iris emission-like brightness."""
    for o in objs:
        if "high-poly" not in o.name:
            continue
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.use_nodes:
                continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    if n.inputs["Base Color"].is_linked:
                        src = n.inputs["Base Color"].links[0].from_socket
                        dim = A.math_col_mul(m.node_tree, src, A.maprange(m.node_tree, A.noise(m.node_tree, 1.0), 0, 1, 0.62, 0.62))
                        m.node_tree.links.new(dim, n.inputs["Base Color"])


# ---------------------------------------------------------------- pose (armature space, MakeHuman faces -Y, its left is +X)
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


def aim(pb, direction):
    base = (_cur_rot(pb.parent) if pb.parent else Matrix.Identity(3)) @ _rest3(pb)
    rd = base.col[1].rotation_difference(Vector(direction).normalized()).to_matrix()
    pb.matrix = Matrix.Translation(_head_now(pb)) @ (rd @ base).to_4x4()
    _upd()


def turn(pb, rx=0.0, ry=0.0, rz=0.0):
    """Rotate a bone (and its children) about armature axes, degrees, around its head."""
    base = (_cur_rot(pb.parent) if pb.parent else Matrix.Identity(3)) @ _rest3(pb)
    cur = _cur_rot(pb) @ _rest3(pb)
    R = Matrix.Rotation(math.radians(rz), 3, "Z") @ Matrix.Rotation(math.radians(ry), 3, "Y") @ Matrix.Rotation(math.radians(rx), 3, "X")
    pb.matrix = Matrix.Translation(_head_now(pb)) @ (R @ cur).to_4x4()
    _upd()


def _blen(pbs, names):
    return sum((pbs[n].bone.tail_local - pbs[n].bone.head_local).length for n in names)


def ik(pbs, upper, lower, target, pole):
    s = _head_now(pbs[upper[0]])
    l1, l2 = _blen(pbs, upper), _blen(pbs, lower)
    t = Vector(target)
    d = min((t - s).length, l1 + l2 - 1e-3)
    n = (t - s).normalized()
    pv = Vector(pole) - n * Vector(pole).dot(n)
    pv.normalize()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - a * a))
    j = s + n * a + pv * hh
    for nm in upper:
        aim(pbs[nm], j - s)
    for nm in lower:
        aim(pbs[nm], (s + n * d) - j)


def curl(pbs, side, amount_deg, thumb_deg=15.0):
    for f in range(1, 6):
        for k in range(1, 4):
            nm = f"finger{f}-{k}.{side}"
            if nm in pbs:
                pb = pbs[nm]
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = (math.radians(thumb_deg if f == 1 else amount_deg * (1.0 if k > 1 else 0.6)), 0, 0)
    _upd()


# sides: MakeHuman ".L" is the character's left = +X; front = -Y. Targets are absolute armature coords
# for a 1.8 m figure (wrist target = wrist joint, ankle unchanged unless given).
POSES = {
    "stand_look": dict(spine=(-2, 0, 0), chest=(0, 0, -6), neck=(0, 0, -8), head=(-6, 0, -14),
                       wristL=(0.26, -0.02, 1.00), poleL=(0.3, 1, 0), wristR=(-0.25, -0.05, 1.01), poleR=(-0.3, 1, 0),
                       handL=(0.05, -0.15, -1), handR=(-0.05, -0.2, -1), curl=38),
    "walk": dict(spine=(4, 0, 0), chest=(0, 0, 5), neck=(0, 0, -3), head=(-3, 0, -5),
                 wristL=(0.24, -0.20, 1.04), poleL=(0.2, 1, 0), wristR=(-0.24, 0.17, 1.03), poleR=(-0.2, 1, 0.2),
                 handL=(0.0, -0.4, -1), handR=(0.0, 0.2, -1), curl=35,
                 legL=((0.16, -0.30, 0.10), (0, -1, 0)), legR=((-0.17, 0.26, 0.16), (0, -1, 0))),
    "talk": dict(spine=(-3, 0, 0), chest=(0, 4, 6), neck=(0, 0, 4), head=(-4, 5, 6),
                 wristL=(0.25, -0.03, 1.00), poleL=(0.3, 1, 0), wristR=(-0.30, -0.30, 1.22), poleR=(-1, 0.4, -0.6),
                 handL=(0.05, -0.15, -1), handR=(-0.5, -0.9, 0.5), curl=30),
    "vend": dict(spine=(6, 0, 0), chest=(5, 0, 0), neck=(0, 0, 0), head=(-8, 0, 12),
                 wristL=(0.20, -0.32, 1.06), poleL=(1, 0.5, -0.6), wristR=(-0.20, -0.32, 1.06), poleR=(-1, 0.5, -0.6),
                 handL=(0, -1, -0.3), handR=(0, -1, -0.3), curl=25),
}


def pose(rig, name):
    P = POSES[name]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    pbs = rig.pose.bones
    for pb in pbs:
        pb.matrix_basis = Matrix.Identity(4)
    _upd()
    turn(pbs["spine04"], *P["spine"])
    turn(pbs["spine02"], *P["chest"])
    turn(pbs["neck01"], *P["neck"])
    turn(pbs["head"], *P["head"])
    for s in ("L", "R"):
        ik(pbs, [f"upperarm01.{s}", f"upperarm02.{s}"], [f"lowerarm01.{s}", f"lowerarm02.{s}"], P[f"wrist{s}"], P[f"pole{s}"])
        aim(pbs[f"wrist.{s}"], P[f"hand{s}"])
        if f"leg{s}" in P:
            tgt, pole_ = P[f"leg{s}"]
            ik(pbs, [f"upperleg01.{s}", f"upperleg02.{s}"], [f"lowerleg01.{s}", f"lowerleg02.{s}"], tgt, pole_)
            aim(pbs[f"foot.{s}"], (0, -1, -0.35))
        curl(pbs, s, P["curl"])
    bpy.ops.object.mode_set(mode="OBJECT")


def place(rig, loc, yaw_deg):
    """Character faces +Y at yaw 0 (MakeHuman faces -Y, so add 180)."""
    rig.location = loc
    rig.rotation_euler = (0, 0, math.radians(yaw_deg + 180.0))
    _upd()


def bone_world(rig, name, local=(0, 0, 0)):
    pb = rig.pose.bones[name]
    return rig.matrix_world @ pb.matrix @ (pb.bone.matrix_local.inverted() @ (pb.bone.matrix_local @ Vector(local)))


def attach(obj, rig, bone):
    mw = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = mw


def character(kind, pose_name, loc=(0, 0, 0), yaw_deg=0.0, gear=True):
    body, rig = human(kind)
    kids = [c for c in rig.children]
    extra = []
    if gear:
        import wf_gear as G

        extra = G.GEAR[kind](rig, kids)
    pose(rig, pose_name)
    tame_eyes(kids)
    if kind == "explorer":
        for c in kids:
            if "casualsuit" in c.name:
                recolor(c, 0.52, 0.68, 0.12, 0.08, 0.28, 0.42)  # jeans -> dark brown canvas trousers
    if kind == "fisher":
        for c in kids:
            if "worksuit" in c.name:
                recolor(c, 0.50, 0.70, 0.08, 0.075, 0.9, 1.0)  # light-blue overalls -> orange oilskin bibs
    if kind == "trader":
        for c in kids:
            if "casualsuit" in c.name:
                recolor(c, 0.52, 0.68, 0.12, 0.10, 0.25, 0.75)  # jeans -> sand linen trousers
    place(rig, loc, yaw_deg)
    return rig, [body] + kids + extra
