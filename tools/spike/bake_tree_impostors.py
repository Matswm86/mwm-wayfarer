"""Render impostor atlases of the Poly Haven (CC0) trees for the Godot forest.

The scanned trees are 4-17 million triangles each, far beyond a phone. Each variant is rendered
from 8 directions round the tree at two heights (5 and 40 deg above the horizon), orthographic,
into frames of FRAME_W x FRAME_H px:
  trees_albedo.png  colour x local ambient occlusion, alpha = coverage
  trees_normal.png  world-space normal (tree-local, before the instance's yaw), 0.5 + 0.5 * n
Layout: one row of 16 frames per variant (8 azimuths at 5 deg, then 8 at 40 deg), one row per
variant (VARIANTS order). trees.json holds the frame size in metres and the base offset.

Run (about 10-20 min, Cycles GPU):
  BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user blender -b --factory-startup \
      -P tools/spike/bake_tree_impostors.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "assets" / "_raw" / "polyhaven" / "models"
OUT = ROOT / "assets" / "models" / "trees"
TMP = ROOT / "assets" / "_raw" / "build" / "impostors"
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

# (model, node name inside the glTF): pine and spruce-like fir for the conifer belt, a broadleaf
# for the birch slots (Poly Haven has no birch; island_tree_01 is the closest CC0 broadleaf)
VARIANTS = [
    ("pine_tree_01", "pine_tree_01_a_LOD0"),
    ("pine_tree_01", "pine_tree_01_c_LOD0"),
    ("fir_tree_01", "fir_tree_01_a_LOD0"),
    ("fir_tree_01", "fir_tree_01_b_LOD0"),
    ("island_tree_01", "island_tree_01_LOD0"),
]
AZIMUTHS = 8
ELEVATIONS = [5.0, 40.0]
FRAME_W, FRAME_H = 256, 512
SAMPLES = 24
ONLY = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dev
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == dev
            sc.cycles.device = "GPU"
            break
        except TypeError:
            continue
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = False
    sc.render.use_persistent_data = (
        True  # keep the BVH of the multi-million-triangle tree between frames
    )
    sc.render.film_transparent = True
    sc.render.resolution_x = FRAME_W
    sc.render.resolution_y = FRAME_H
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0, 0, 0)
    sc.world.light_settings.distance = 1.5


def load_variant(model: str, node: str) -> list[bpy.types.Object]:
    gl = next((PH / model).glob("*.gltf"))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(gl))
    new = [o for o in bpy.data.objects if o not in before]
    keep = [
        o
        for o in new
        if o.type == "MESH" and (o.name == node or (o.parent and o.parent.name == node))
    ]
    for o in new:
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    return keep


def bounds(objs) -> tuple[Vector, Vector]:
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def override(objs, mode: str) -> None:
    """mode 'albedo': emission = base colour x AO; 'normal': emission = world normal packed 0..1."""
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            nt = m.node_tree
            b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            base = (
                b.inputs["Base Color"].links[0].from_socket
                if b.inputs["Base Color"].is_linked
                else None
            )
            alpha = b.inputs["Alpha"].links[0].from_socket if b.inputs["Alpha"].is_linked else None
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            for n in list(nt.nodes):
                if n.name.startswith("imp_"):
                    nt.nodes.remove(n)
            em = nt.nodes.new("ShaderNodeEmission")
            em.name = "imp_em"
            if mode == "albedo":
                ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
                ao.name = "imp_ao"
                ao.inputs["Distance"].default_value = 1.2
                mul = nt.nodes.new("ShaderNodeMix")
                mul.name = "imp_mul"
                mul.data_type = "RGBA"
                mul.blend_type = "MULTIPLY"
                mul.inputs["Factor"].default_value = 0.85
                if base is not None:
                    nt.links.new(base, mul.inputs[6])
                else:
                    mul.inputs[6].default_value = b.inputs["Base Color"].default_value
                nt.links.new(ao.outputs["AO"], mul.inputs[7])
                nt.links.new(mul.outputs[2], em.inputs["Color"])
            else:
                geo = nt.nodes.new("ShaderNodeNewGeometry")
                geo.name = "imp_geo"
                vm = nt.nodes.new("ShaderNodeVectorMath")
                vm.name = "imp_vm"
                vm.operation = "MULTIPLY_ADD"
                vm.inputs[1].default_value = (0.5, 0.5, 0.5)
                vm.inputs[2].default_value = (0.5, 0.5, 0.5)
                nt.links.new(geo.outputs["Normal"], vm.inputs[0])
                nt.links.new(vm.outputs[0], em.inputs["Color"])
            final = em.outputs["Emission"]
            if alpha is not None:
                tr = nt.nodes.new("ShaderNodeBsdfTransparent")
                tr.name = "imp_tr"
                mx = nt.nodes.new("ShaderNodeMixShader")
                mx.name = "imp_mx"
                nt.links.new(alpha, mx.inputs["Fac"])
                nt.links.new(tr.outputs[0], mx.inputs[1])
                nt.links.new(em.outputs[0], mx.inputs[2])
                final = mx.outputs[0]
            nt.links.new(final, out.inputs["Surface"])


def render_variant(vi: int, model: str, node: str) -> dict:
    reset()
    objs = load_variant(model, node)
    lo, hi = bounds(objs)
    # the camera aims at the crown's centre (the glTF variants sit side by side in their file)
    h = hi.z - lo.z
    r = max(hi.x - lo.x, hi.y - lo.y) * 0.5
    size = max(h * 1.04, 4.0 * r * 1.04)  # frame height in metres; width = size / 2
    print(f"bounds x {lo.x:.1f}..{hi.x:.1f} y {lo.y:.1f}..{hi.y:.1f}", flush=True)
    centre = Vector(((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, lo.z + h * 0.5))
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = size
    cam_data.clip_start = 0.1
    cam_data.clip_end = 400.0
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    print(f"VARIANT {vi} {node}: height {h:.1f} m radius {r:.1f} m frame {size:.1f} m", flush=True)
    for mode in ("albedo", "normal"):
        override(objs, mode)
        for ei, el in enumerate(ELEVATIONS):
            for ai in range(AZIMUTHS):
                az = 2.0 * math.pi * ai / AZIMUTHS
                e = math.radians(el)
                d = Vector((math.sin(az) * math.cos(e), -math.cos(az) * math.cos(e), math.sin(e)))
                cam.location = centre + d * 150.0
                cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
                path = TMP / f"v{vi}_{mode}_{ei}_{ai}.png"
                bpy.context.scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
    return {"model": model, "node": node, "height": h, "frame_m": size, "centre_z": centre.z - lo.z}


def main() -> None:
    meta_path = OUT / "trees.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    variants = meta.get("variants", [None] * len(VARIANTS))
    for vi, (model, node) in enumerate(VARIANTS):
        if ONLY and str(vi) not in ONLY:
            continue
        variants[vi] = render_variant(vi, model, node)
    meta = {
        "azimuths": AZIMUTHS,
        "elevations_deg": ELEVATIONS,
        "frame_px": [FRAME_W, FRAME_H],
        "variants": variants,
        "note": "frames: azimuth a views the tree from direction (sin a, -cos a) in Blender = (sin a, cos a) in Godot x, z",
    }
    meta_path.write_text(json.dumps(meta, indent=1))
    print("frames rendered; run tools/spike/pack_tree_atlas.py")


main()
