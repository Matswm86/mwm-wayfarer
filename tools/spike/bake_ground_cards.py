"""Render ground-cover cards from Poly Haven (CC0) plant scans for the near ground cover.

Each plant is rendered from the side (orthographic, 512 x 512, colour x local AO, alpha = coverage)
(tools/spike/pack_ground_cards.py packs them into assets/models/ground/ground_cards.png, CARDS order); the Godot
ground cover draws each plant as two crossed quads. ground_cards.json holds each card's size in m.

Run (about 2 min):
  BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user blender -b --factory-startup \
      -P tools/spike/bake_ground_cards.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "assets" / "_raw" / "polyhaven" / "models"
OUT = ROOT / "assets" / "models" / "ground"
TMP = ROOT / "assets" / "_raw" / "build" / "ground_cards"
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
PX = 512
# (model, k): the k-th largest single plant in the Poly Haven set (sets hold several clumps side
# by side). Tall and short grass, fern, shrub (heather stand-in).
CARDS = [
    ("grass_medium_01", 0),
    ("grass_medium_01", 1),
    ("grass_medium_02", 0),
    ("grass_medium_02", 1),
    ("fern_02", 0),
    ("shrub_04", 0),
]


def setup() -> None:
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
    sc.cycles.samples = 32
    sc.cycles.use_denoising = False
    sc.render.film_transparent = True
    sc.render.resolution_x = PX
    sc.render.resolution_y = PX
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.world = bpy.data.worlds.new("w")
    sc.world.light_settings.distance = 0.3


def emission_override(objs) -> None:
    for o in objs:
        for slot in o.material_slots:
            nt = slot.material.node_tree
            b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            base = (
                b.inputs["Base Color"].links[0].from_socket
                if b.inputs["Base Color"].is_linked
                else None
            )
            alpha = b.inputs["Alpha"].links[0].from_socket if b.inputs["Alpha"].is_linked else None
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            em = nt.nodes.new("ShaderNodeEmission")
            ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
            ao.inputs["Distance"].default_value = 0.3
            mul = nt.nodes.new("ShaderNodeMix")
            mul.data_type = "RGBA"
            mul.blend_type = "MULTIPLY"
            mul.inputs["Factor"].default_value = 0.8
            if base is not None:
                nt.links.new(base, mul.inputs[6])
            nt.links.new(ao.outputs["AO"], mul.inputs[7])
            nt.links.new(mul.outputs[2], em.inputs["Color"])
            final = em.outputs[0]
            if alpha is not None:
                tr = nt.nodes.new("ShaderNodeBsdfTransparent")
                mx = nt.nodes.new("ShaderNodeMixShader")
                nt.links.new(alpha, mx.inputs["Fac"])
                nt.links.new(tr.outputs[0], mx.inputs[1])
                nt.links.new(em.outputs[0], mx.inputs[2])
                final = mx.outputs[0]
            nt.links.new(final, out.inputs["Surface"])


def render_card(i: int, model: str, k: int) -> dict:
    setup()
    gl = next((PH / model).glob("*.gltf"))
    bpy.ops.import_scene.gltf(filepath=str(gl))
    meshes = sorted(
        (o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: -len(o.data.polygons)
    )
    objs = [meshes[min(k, len(meshes) - 1)]]
    for o in meshes:
        if o not in objs:
            bpy.data.objects.remove(o, do_unlink=True)
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    emission_override(objs)
    size = max(hi.x - lo.x, hi.z - lo.z) * 1.02
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = size
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + size / 2))
    cam.location = centre + Vector((0.0, -50.0, 0.0))
    cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
    path = TMP / f"card{i}.png"
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"CARD {i} {model}: {size:.2f} m", flush=True)
    return {"model": model, "size_m": size}


def main() -> None:
    info = [render_card(i, m, k) for i, (m, k) in enumerate(CARDS)]
    (OUT / "ground_cards.json").write_text(json.dumps({"cards": info, "px": PX}, indent=1))
    print("cards rendered; run tools/spike/pack_ground_cards.py")


main()
