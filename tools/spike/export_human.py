"""Export a MakeHuman character (preset from tools/art/wf_mh.py) for the Godot spike: simple
textured materials, decimated, a looping 4 s idle (breathing sway) and, with --walk, a 1 s walk
cycle. Kinds used: "ingrid" (the dock NPC, GDD 6.4) and "explorer" (the player).
MakeHuman system assets and MPFB output are CC0.

BLENDER_USER_RESOURCES=<dir with the MPFB extension> \
blender -b --factory-startup -P tools/spike/export_human.py -- <kind> <out.glb> [--walk]
"""

from __future__ import annotations

import colorsys
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "art"))
import wf_mh as M  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1 :]
KIND = ARGS[0]
OUT = Path(ARGS[1]).resolve()
WALK = "--walk" in ARGS
# pixel re-dye per clothing item: (hue lo, hue hi, sat min, new hue, new sat, value scale)
DYES = {
    "ingrid": {"worksuit": (0.50, 0.70, 0.08, 0.075, 0.9, 1.0)},  # blue overalls -> orange bibs
    "explorer": {"casualsuit": (0.52, 0.68, 0.12, 0.08, 0.28, 0.42)},  # jeans -> brown canvas
}
TEX = 512
TARGET_TRIS = 14000


def build():
    HS = M.enable()
    p = M.PRESETS[KIND]
    info = HS._create_default_human_info_dict()
    info["phenotype"] = p["phenotype"]
    info["rig"] = "default"
    info["eyes"] = "low-poly/low-poly.mhclo"
    info["eyebrows"] = p["eyebrows"]
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"
    info["hair"] = p["hair"]
    info["clothes"] = p["clothes"]
    info["skin_mhmat"] = p["skin"]
    info["skin_material_type"] = "MAKESKIN"
    info["eyes_material_type"] = "MAKESKIN"
    info["name"] = KIND
    st = HS.get_default_deserialization_settings()
    st["subdiv_levels"] = 0
    body = HS.deserialize_from_dict(info, st)
    rig = body.parent
    return rig, [body] + [c for c in rig.children if c is not body and c.type == "MESH"]


def first_image(mat):
    if not mat or not mat.use_nodes:
        return None
    imgs = [n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    diff = [i for i in imgs if "diffuse" in i.name.lower() or "_d" in i.name.lower()]
    return (diff or imgs or [None])[0]


def dye(img, lo, hi, smin, hue, sat, vmul):
    """Same re-dye as wf_mh.character, baked into the pixels (glTF cannot carry the node trick)."""
    px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
    hsv = np.array([colorsys.rgb_to_hsv(*c) for c in px[:, :3]])
    m = (hsv[:, 0] > lo) & (hsv[:, 0] < hi) & (hsv[:, 1] > smin)
    for k in np.nonzero(m)[0]:
        px[k, :3] = colorsys.hsv_to_rgb(hue, sat, min(1.0, hsv[k, 2] * vmul))
    img.pixels[:] = px.ravel()


def simplify(objs):
    done = {}
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if m is None or m.name in done:
                continue
            img = first_image(m)
            new = bpy.data.materials.new(m.name + "_s")
            new.use_nodes = True
            nt = new.node_tree
            b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Roughness"].default_value = 0.8
            if img is not None:
                img = img.copy()
                if img.size[0] > TEX:
                    img.scale(TEX, TEX)
                for key, d in DYES.get(KIND, {}).items():
                    if key in o.name:
                        dye(img, *d)
                t = nt.nodes.new("ShaderNodeTexImage")
                t.image = img
                nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
                if any(k in o.name.lower() for k in ("hair", "braid", "eyebrow", "eyelash")):
                    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
                    new.blend_method = "CLIP" if hasattr(new, "blend_method") else None
            done[m.name] = new
            slot.material = new


def decimate(objs):
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    ratio = min(1.0, TARGET_TRIS / max(tris, 1))
    print("HUMAN tris before", tris, "ratio", round(ratio, 3))
    for o in objs:
        if "eyelash" in o.name.lower() or "eyebrow" in o.name.lower():
            continue
        mod = o.modifiers.new("dec", "DECIMATE")
        mod.ratio = ratio
        # decimate before the armature so the exporter applies it and keeps skinning
        while o.modifiers.find("dec") > 0:
            bpy.ops.object.select_all(action="DESELECT")
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_move_up(modifier="dec")


def key_all(pbs, frame):
    for pb in pbs:
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        pb.keyframe_insert("location", frame=frame)


def new_action(rig, name):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = act
    return act


def set_pose(rig, name):
    M.pose(rig, name)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"


def idle(rig):
    new_action(rig, "idle")
    set_pose(rig, "stand_look")
    pbs = rig.pose.bones
    key_all(pbs, 1)
    key_all(pbs, 121)
    M.turn(pbs["spine04"], 1.6, 0, 0)
    M.turn(pbs["spine02"], 1.2, 0, 2)
    M.turn(pbs["head"], 0, 0, 10)
    key_all(pbs, 61)
    bpy.ops.object.mode_set(mode="OBJECT")


def walk(rig):
    """Two contact poses (wf_mh "walk" and its mirror), 30 frames per cycle at 30 fps."""
    w = M.POSES["walk"]
    M.POSES["walk_b"] = dict(
        w,
        wristL=(0.24, 0.17, 1.03),
        poleL=(0.2, 1, 0.2),
        wristR=(-0.24, -0.20, 1.04),
        poleR=(-0.2, 1, 0),
        handL=(0.0, 0.2, -1),
        handR=(0.0, -0.4, -1),
        legL=((0.17, 0.26, 0.16), (0, -1, 0)),
        legR=((-0.16, -0.30, 0.10), (0, -1, 0)),
    )
    new_action(rig, "walk")
    set_pose(rig, "walk")
    key_all(rig.pose.bones, 1)
    key_all(rig.pose.bones, 31)
    bpy.ops.object.mode_set(mode="OBJECT")
    set_pose(rig, "walk_b")
    key_all(rig.pose.bones, 16)
    bpy.ops.object.mode_set(mode="OBJECT")


def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    rig, meshes = build()
    simplify(meshes)
    decimate(meshes)
    idle(rig)
    if WALK:
        walk(rig)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    for o in meshes:
        o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(OUT),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_animations=True,
        export_skins=True,
        export_morph=False,
        export_image_format="JPEG",
        export_animation_mode="ACTIONS",
    )
    print("HUMAN exported", OUT, OUT.stat().st_size)


main()
