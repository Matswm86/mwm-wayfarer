"""Check renders for a retargeted character (opens scratch/wayfarer/<name>_rt.blend).
Writes assets/incoming/<name>/<name>_check.png: [talk-camera waist-up | face close-up | idle | walk a | walk b | run]
Run: wf_run.sh tools/assets/char_check.py <log> -- <name>
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

name = sys.argv[sys.argv.index("--") + 1]
REPO = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=f"{Path.home()}/MWM/scratch/wayfarer/{name}_rt.blend")
sc = bpy.context.scene
try:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "AgX"
sc.eevee.taa_render_samples = 64
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(REPO / "assets/_raw/polyhaven/hdri/kloofendal_48d_partly_cloudy_puresky_4k.hdr"))
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
w.node_tree.links.new(env.outputs[0], bg.inputs[0])
bg.inputs[1].default_value = 0.8
sd = bpy.data.lights.new("sun", "SUN")
sd.energy = 4.0
sd.color = (1.0, 0.92, 0.82)
sd.angle = math.radians(1.5)
sun = bpy.data.objects.new("sun", sd)
sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
bpy.ops.mesh.primitive_plane_add(size=40)
gm = bpy.data.materials.new("g")
gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.13, 0.14, 0.10, 1)
bpy.context.object.data.materials.append(gm)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
head = next(b for b in arm.pose.bones if "head" in b.name.lower() and "end" not in b.name.lower() and "top" not in b.name.lower())
cam_d = bpy.data.cameras.new("c")
cam = bpy.data.objects.new("c", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 640, 900
shots = [("talk", 10, "talk"), ("talk", 10, "face"), ("idle", 0, "body"), ("walk", 6, "body"), ("walk", 22, "body"), ("run", 5, "body")]
outs = []
for i, (clip, frame, kind) in enumerate(shots):
    for tr in arm.animation_data.nla_tracks:
        tr.mute = True
    arm.animation_data.action = bpy.data.actions[clip]
    sc.frame_set(frame)
    bpy.context.view_layer.update()
    hp = arm.matrix_world @ head.head
    if kind == "face":
        cam_d.lens = 85
        tgt = hp + Vector((0, 0, 0.08))
        cam.location = tgt + Vector((0.25, -1.1, 0.02))
    elif kind == "talk":
        cam_d.lens = 60
        tgt = hp + Vector((0, 0, -0.35))
        cam.location = tgt + Vector((0.9, -3.6, 0.05))
    else:
        cam_d.lens = 50
        tgt = Vector((0, 0, 0.92))
        cam.location = tgt + Vector((3.2, -4.2, 0.3))
    d = (tgt - cam.location).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    p = f"{Path.home()}/MWM/scratch/wayfarer/{name}_shot{i}.png"
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    outs.append(p)
print("CHECK", outs)
