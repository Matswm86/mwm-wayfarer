"""Add normal + ORM maps to a retargeted character (scratch/wayfarer/<name>_rt.blend) and re-export its GLB.
  ORM.R  AO baked with Cycles at the rest pose (4K)
  ORM.G  roughness estimate: skin-coloured texels 0.5, everything else 0.85 (the scans ship albedo only)
  normal detail normal from the albedo's high-pass (cloth weave, seams, wrinkles), strength ~0.5, OpenGL
Run: wf_run.sh tools/assets/char_maps.py <log> -- <name>
"""
import subprocess
import sys
from pathlib import Path

import bpy

name = sys.argv[sys.argv.index("--") + 1]
OUT = (Path.home() / "MWM/projects/mwm-wayfarer/assets/incoming") / name
bpy.ops.wm.open_mainfile(filepath=f"{Path.home()}/MWM/scratch/wayfarer/{name}_rt.blend")
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
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
arm.data.pose_position = "REST"
meshes = [o for o in sc.objects if o.type == "MESH" and o.visible_get()]
albedo = None
for o in meshes:
    for m in o.data.materials:
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b and b.inputs["Base Color"].is_linked and b.inputs["Base Color"].links[0].from_node.type == "TEX_IMAGE":
            albedo = albedo or b.inputs["Base Color"].links[0].from_node.image
N = 4096
ao = bpy.data.images.new(f"{name}_ao", N, N, alpha=False)
ao.colorspace_settings.name = "Non-Color"
for o in meshes:
    for m in o.data.materials:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.name = "ao_target"
        t.image = ao
        m.node_tree.nodes.active = t
sc.cycles.samples = 64
sc.world = sc.world or bpy.data.worlds.new("w")
sc.world.light_settings.distance = 0.25
sc.render.bake.margin = 16
sc.render.bake.use_selected_to_active = False
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.bake(type="AO")
ao.filepath_raw = str(OUT / f"{name}_ao_tmp.png")
ao.file_format = "PNG"
ao.save()
alb_path = OUT / f"{name}_albedo.png"
if not alb_path.exists():
    import shutil

    src = Path(bpy.path.abspath(albedo.filepath))
    if src.exists():
        shutil.copy(src, alb_path)
    else:
        albedo.reload()
        albedo.filepath_raw = str(alb_path)
        albedo.file_format = "PNG"
        albedo.save()
print("CM baked ao", flush=True)
compose = f'''
import numpy as np
from PIL import Image, ImageFilter
N={N}
a=Image.open("{alb_path}").convert("RGB").resize((N,N),Image.LANCZOS)
A=np.asarray(a).astype(np.float32)/255
L=(A*[0.2126,0.7152,0.0722]).sum(-1)
h=L-np.asarray(Image.fromarray((L*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32)/255
h=np.asarray(Image.fromarray(np.clip((h+0.5)*255,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32)/255
gx=np.roll(h,-1,1)-np.roll(h,1,1); gy=np.roll(h,-1,0)-np.roll(h,1,0)
k=2.5; n=np.dstack([-gx*k, gy*k, np.ones_like(h)]); n/=np.linalg.norm(n,axis=-1,keepdims=True)
Image.fromarray(((n*0.5+0.5)*255).astype(np.uint8)).save("{OUT}/{name}_normal.png")
r,g,b=A[...,0],A[...,1],A[...,2]
skin=((r>g)&(g>b)&(r-b>0.08)&(r>0.25)&((r-g)<0.35)).astype(np.float32)
skin=np.asarray(Image.fromarray((skin*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32)/255
rough=0.85-0.35*skin
ao=np.asarray(Image.open("{OUT}/{name}_ao_tmp.png").convert("L").resize((N,N))).astype(np.float32)/255
ao=0.25+0.75*ao
Image.fromarray((np.dstack([ao,rough,np.zeros_like(ao)])*255).astype(np.uint8)).save("{OUT}/{name}_orm.png")
print("CM composed")
'''
subprocess.run(["python3", "-c", compose], check=True)
(OUT / f"{name}_ao_tmp.png").unlink()
for o in meshes:
    for m in o.data.materials:
        nt = m.node_tree
        nt.nodes.remove(nt.nodes["ao_target"])
        b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        if not b.inputs["Normal"].is_linked:
            tn = nt.nodes.new("ShaderNodeTexImage")
            tn.image = bpy.data.images.load(str(OUT / f"{name}_normal.png"), check_existing=True)
            tn.image.colorspace_settings.name = "Non-Color"
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value = 0.6
            nt.links.new(tn.outputs[0], nm.inputs["Color"])
            nt.links.new(nm.outputs[0], b.inputs["Normal"])
        to = nt.nodes.new("ShaderNodeTexImage")
        to.image = bpy.data.images.load(str(OUT / f"{name}_orm.png"), check_existing=True)
        to.image.colorspace_settings.name = "Non-Color"
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(to.outputs[0], sp.inputs[0])
        nt.links.new(sp.outputs[1], b.inputs["Roughness"])
        nt.links.new(sp.outputs[2], b.inputs["Metallic"])
arm.data.pose_position = "POSE"
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o in meshes:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), use_selection=True, export_format="GLB",
                          export_image_format="AUTO", export_animations=True, export_animation_mode="NLA_TRACKS",
                          export_force_sampling=True, export_morph=True, export_skins=True)
print("CM exported", OUT / f"{name}.glb", flush=True)
