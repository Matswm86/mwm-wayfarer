"""Impostor atlas for one species from its game-tree GLBs (LOD0), same layout as tools/spike/bake_tree_impostors.py
so shaders/tree.gdshader can read it: per variant one row of 16 frames (8 azimuths at 5 deg, then 8 at 40 deg),
frames FRAME_W x FRAME_H px, orthographic.

  <species>_impostor_albedo.png  colour x (vertex AO already in the mesh) x local AO, alpha = coverage
                                  (coverage thickened x1.6 so distant mips do not dissolve into confetti;
                                  colour bled into the empty pixels so mips never darken the edge)
  <species>_impostor_normal.png  world-space normal (tree-local, before instance yaw), 0.5 + 0.5 * n,
                                  rendered with the Raw view transform (the spike baker used Standard,
                                  which sRGB-encodes the data)
  <species>_impostor.json        same keys as assets/models/trees/trees.json

Run: wf_run.sh tools/assets/bake_impostors.py <log> -- <species> <glb1> [<glb2> ...]
"""

import json
import math
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO = Path(__file__).resolve().parents[2]
args = sys.argv[sys.argv.index("--") + 1:]
species, glbs = args[0], args[1:]
OUT = REPO / "assets/incoming" / species
TMP = (Path.home() / "MWM/scratch/wayfarer/imp_tmp") / species
TMP.mkdir(parents=True, exist_ok=True)
AZ = 8
ELEV = [5.0, 40.0]
FW, FH = 256, 512


def reset():
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
    sc.cycles.samples = 24
    sc.cycles.max_bounces = 1
    sc.cycles.use_denoising = False
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = FW, FH
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0, 0, 0)
    sc.world.light_settings.distance = 1.0
    return sc


def override(objs, mode):
    done = set()
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if m is None or m.name in done:
                continue
            done.add(m.name)
            nt = m.node_tree
            b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            base = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].is_linked else None
            alpha = b.inputs["Alpha"].links[0].from_socket if b.inputs["Alpha"].is_linked else None
            for n in list(nt.nodes):
                if n.name.startswith("imp_"):
                    nt.nodes.remove(n)
            em = nt.nodes.new("ShaderNodeEmission")
            em.name = "imp_em"
            if mode == "albedo":
                ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
                ao.name = "imp_ao"
                ao.inputs["Distance"].default_value = 1.0
                mul = nt.nodes.new("ShaderNodeMix")
                mul.name = "imp_mul"
                mul.data_type = "RGBA"
                mul.blend_type = "MULTIPLY"
                mul.inputs["Factor"].default_value = 0.15  # crown AO is already in COLOR_0 and the leaf atlas
                if base is not None:
                    nt.links.new(base, mul.inputs[6])
                else:
                    mul.inputs[6].default_value = b.inputs["Base Color"].default_value
                nt.links.new(ao.outputs["AO"], mul.inputs[7])
                nt.links.new(mul.outputs[2], em.inputs["Color"])
            else:
                nmap = b.inputs["Normal"].links[0].from_socket if b.inputs["Normal"].is_linked else None
                if nmap is None:
                    geo = nt.nodes.new("ShaderNodeNewGeometry")
                    geo.name = "imp_geo"
                    nmap = geo.outputs["Normal"]
                vm = nt.nodes.new("ShaderNodeVectorMath")
                vm.name = "imp_vm"
                vm.operation = "MULTIPLY_ADD"
                vm.inputs[1].default_value = (0.5, 0.5, 0.5)
                vm.inputs[2].default_value = (0.5, 0.5, 0.5)
                nt.links.new(nmap, vm.inputs[0])
                nt.links.new(vm.outputs[0], em.inputs["Color"])
            final = em.outputs[0]
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


variants = []
for vi, glb in enumerate(glbs):
    sc = reset()
    bpy.ops.import_scene.gltf(filepath=glb)
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    keep = [o for o in objs if o.name.endswith("LOD0")] or objs
    for o in objs:
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in keep:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    h = hi.z - lo.z
    r = max(hi.x - lo.x, hi.y - lo.y) * 0.5
    size = max(h * 1.04, 4.0 * r * 1.04)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + h / 2))
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = size
    cd.clip_start, cd.clip_end = 0.1, 400
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for mode in ("albedo", "normal"):
        override(keep, mode)
        sc.view_settings.view_transform = "Standard" if mode == "albedo" else "Raw"
        for ei, el in enumerate(ELEV):
            for ai in range(AZ):
                az = 2 * math.pi * ai / AZ
                e = math.radians(el)
                d = Vector((math.sin(az) * math.cos(e), -math.cos(az) * math.cos(e), math.sin(e)))
                cam.location = centre + d * 150
                cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
                sc.render.filepath = str(TMP / f"v{vi}_{mode}_{ei}_{ai}.png")
                bpy.ops.render.render(write_still=True)
    variants.append({"model": Path(glb).stem, "node": keep[0].name, "height": h, "frame_m": size, "centre_z": centre.z - lo.z})
    print("IMP variant", vi, Path(glb).stem, round(h, 2), round(size, 2), flush=True)

meta = {"azimuths": AZ, "elevations_deg": ELEV, "frame_px": [FW, FH], "variants": variants,
        "note": "frames: azimuth a views the tree from direction (sin a, -cos a) in Blender = (sin a, cos a) in Godot x, z"}
(OUT / f"{species}_impostor.json").write_text(json.dumps(meta, indent=1))
pack = f'''
import numpy as np
from PIL import Image, ImageFilter
T="{TMP}"; n={len(glbs)}; FW={FW}; FH={FH}
alb=np.zeros((FH*n, FW*16, 4), np.uint8); nor=np.zeros((FH*n, FW*16, 4), np.uint8)
for v in range(n):
    for ei in range(2):
        for ai in range(8):
            x=(ei*8+ai)*FW; y=v*FH
            a=np.asarray(Image.open(f"{{T}}/v{{v}}_albedo_{{ei}}_{{ai}}.png").convert("RGBA")).astype(np.float32)
            nm=np.asarray(Image.open(f"{{T}}/v{{v}}_normal_{{ei}}_{{ai}}.png").convert("RGBA")).astype(np.float32)
            al=np.clip(a[...,3]*1.6,0,255)
            rgb=a[...,:3].copy(); m=a[...,3]>8
            fill=rgb[m].mean(0) if m.any() else np.array([60,70,50.])
            im=Image.fromarray(np.where(m[...,None],rgb,fill).astype(np.uint8))
            for r in (2,6,16):
                bl=np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32)
                rgb=np.where(m[...,None],rgb,bl); im=Image.fromarray(rgb.astype(np.uint8))
            alb[y:y+FH,x:x+FW]=np.dstack([rgb.astype(np.uint8),al.astype(np.uint8)])
            nn=nm[...,:3]; nn[~m]=(128,128,255)
            nor[y:y+FH,x:x+FW]=np.dstack([nn.astype(np.uint8),al.astype(np.uint8)])
Image.fromarray(alb,"RGBA").save("{OUT}/{species}_impostor_albedo.png",optimize=True)
Image.fromarray(nor[...,:3]).save("{OUT}/{species}_impostor_normal.png",optimize=True)
print("IMP packed", alb.shape)
'''
subprocess.run(["python3", "-c", pack], check=True)
