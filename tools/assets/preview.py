"""Item syntax: label=path[#target_height_m][@name_filter1,filter2]
Look-dev preview: render GLB/GLTF models side by side in neutral daylight (Eevee).

blender -b --factory-startup -P preview.py -- out.png "label1=path1[@obj_filter]" "label2=path2" ...
Each model is scaled to its native size (metres), placed in a row on a grey-green ground plane.
Env: PV_SCALE (multiply all), PV_W/PV_H (resolution), PV_ELEV (camera elevation deg), PV_DIST (cam distance factor)
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HDRI = (Path.home() / "MWM/projects/mwm-wayfarer/assets/_raw/polyhaven/hdri/kloofendal_48d_partly_cloudy_puresky_4k.hdr")
args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]
items = args[1:]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
try:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = int(os.environ.get("PV_W", 1920))
sc.render.resolution_y = int(os.environ.get("PV_H", 1080))
sc.view_settings.view_transform = "AgX"
sc.eevee.taa_render_samples = 64
try:
    sc.eevee.use_shadows = True
    sc.eevee.use_raytracing = True
except AttributeError:
    pass

w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(HDRI))
bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
bg.inputs[1].default_value = 0.9
nt.links.new(env.outputs[0], bg.inputs[0])

sun_d = bpy.data.lights.new("sun", "SUN")
sun_d.energy = 4.0
sun_d.color = (1.0, 0.92, 0.82)
sun_d.angle = math.radians(1.5)
sun = bpy.data.objects.new("sun", sun_d)
sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(35))

x = 0.0
gap = float(os.environ.get("PV_GAP", 1.0))
scale = float(os.environ.get("PV_SCALE", 1.0))
max_h = 0.0
labels = []
for it in items:
    label, path = it.split("=", 1)
    filt = None
    want_h = None
    if "@" in path:
        path, filt = path.split("@", 1)
    if "#" in path:
        path, want_h = path.split("#", 1)
        want_h = float(want_h)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    if filt:
        keep = [o for o in new if o.type != "MESH" or any(f in o.name for f in filt.split(","))]
        for o in new:
            if o not in keep:
                bpy.data.objects.remove(o)
        new = keep
    meshes = [o for o in new if o.type == "MESH"]
    skip = os.environ.get("PV_SKIP_MAT")
    if skip:
        import bmesh
        for o in meshes:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bad = [f for f in bm.faces if skip in o.data.materials[f.material_index].name]
            bmesh.ops.delete(bm, geom=bad, context="FACES")
            bm.to_mesh(o.data)
            bm.free()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(dg)
        me_ = ev.to_mesh()
        step = max(1, len(me_.vertices) // 4000)
        pts += [ev.matrix_world @ me_.vertices[i].co for i in range(0, len(me_.vertices), step)]
        ev.to_mesh_clear()
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    root = bpy.data.objects.new(f"root_{label}", None)
    sc.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    scale = float(os.environ.get("PV_SCALE", 1.0))
    if want_h:
        scale = want_h / (mx.z - mn.z)
    width = (mx.x - mn.x) * scale
    root.scale = (scale,) * 3
    root.location = (x - mn.x * scale, -(mn.y + mx.y) / 2 * scale, -mn.z * scale)
    labels.append((label, x + width / 2, (mx.z - mn.z) * scale))
    max_h = max(max_h, (mx.z - mn.z) * scale)
    x += width + gap
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    print(f"PV {label}: tris={tris} raw=({mx.x-mn.x:.2f},{mx.y-mn.y:.2f},{mx.z-mn.z:.2f}) scale={scale:.4f}")

# alpha: make every image-alpha material clip and ensure backface visible
for m in bpy.data.materials:
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "DITHERED"
    m.use_backface_culling = False

span = x - gap
bpy.ops.mesh.primitive_plane_add(size=1, location=(span / 2, 0, 0))
g = bpy.context.object
g.scale = (span * 3 + 40, span * 3 + 40, 1)
gm = bpy.data.materials.new("ground")
gm.use_nodes = True
p = next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
p.inputs["Base Color"].default_value = (0.16, 0.17, 0.12, 1)
p.inputs["Roughness"].default_value = 1.0
g.data.materials.append(gm)

cam_d = bpy.data.cameras.new("cam")
cam_d.lens = float(os.environ.get("PV_LENS", 50))
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
aspect = sc.render.resolution_x / sc.render.resolution_y
fov_h = 2 * math.atan(36 / 2 / cam_d.lens)
fit = max(span / (2 * math.tan(fov_h / 2)), max_h / (2 * math.tan(fov_h / aspect / 2))) * float(os.environ.get("PV_DIST", 1.12))
elev = math.radians(float(os.environ.get("PV_ELEV", 8)))
crop = float(os.environ.get("PV_CROP", 0))  # >0: frame only the top fraction (faces)
target = Vector((span / 2, 0, max_h * 0.45))
if crop > 0:
    fit = max(span / (2 * math.tan(fov_h / 2)), max_h * crop / (2 * math.tan(fov_h / aspect / 2))) * float(os.environ.get("PV_DIST", 1.12))
    target = Vector((span / 2, 0, max_h * (1 - crop / 2)))
cam.location = target + Vector((0, -fit * math.cos(elev), fit * math.sin(elev)))
cam.rotation_euler = (math.radians(90) - elev, 0, 0)
cam_d.clip_end = 5000
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("PV wrote", out)
