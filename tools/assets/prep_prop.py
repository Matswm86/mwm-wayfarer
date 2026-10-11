"""Prop GLB -> game GLB: flattened, real-world size (longest side = <size_m>), pivot bottom centre,
material rebuilt from <prefix>_albedo/_normal/_orm.png, LOD1 at RP_LOD1 (0.35) of LOD0, unskinned junk removed.
Run: wf_run.sh tools/assets/prep_prop.py <log> -- <glb> <name> <size_m> <tex_prefix> [rot_z_deg]
"""
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

a = sys.argv[sys.argv.index("--") + 1:]
glb, name, size, pre = a[0], a[1], float(a[2]), a[3]
rot = float(a[4]) if len(a) > 4 else 0.0
OUT = (Path.home() / "MWM/projects/mwm-wayfarer/assets/incoming/village_props")
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
ms = [o for o in bpy.data.objects if o.type == "MESH"]
for o in ms:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
for o in list(bpy.data.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action="SELECT")
bpy.context.view_layer.objects.active = ms[0]
bpy.ops.object.join()
ob = ms[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new()
bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5 * max(ob.dimensions))
bm.to_mesh(ob.data)
bm.free()
s = size / max(ob.dimensions)
lo = Vector([min((v.co[i] for v in ob.data.vertices)) for i in range(3)])
hi = Vector([max((v.co[i] for v in ob.data.vertices)) for i in range(3)])
ob.data.transform(Matrix.Rotation(math.radians(rot), 4, "Z") @ Matrix.Scale(s, 4) @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
ob.data.materials.clear()
m = bpy.data.materials.new(name)
m.use_nodes = True
nt = m.node_tree
b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
ta = nt.nodes.new("ShaderNodeTexImage")
ta.image = bpy.data.images.load(pre + "_albedo.png")
nt.links.new(ta.outputs[0], b.inputs["Base Color"])
tn = nt.nodes.new("ShaderNodeTexImage")
tn.image = bpy.data.images.load(pre + "_normal.png")
tn.image.colorspace_settings.name = "Non-Color"
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(tn.outputs[0], nm.inputs["Color"])
nt.links.new(nm.outputs[0], b.inputs["Normal"])
to = nt.nodes.new("ShaderNodeTexImage")
to.image = bpy.data.images.load(pre + "_orm.png")
to.image.colorspace_settings.name = "Non-Color"
sp = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(to.outputs[0], sp.inputs[0])
nt.links.new(sp.outputs[1], b.inputs["Roughness"])
nt.links.new(sp.outputs[2], b.inputs["Metallic"])
ob.data.materials.append(m)
ob.name = ob.data.name = f"{name}_LOD0"
l1 = ob.copy()
l1.data = ob.data.copy()
bpy.context.scene.collection.objects.link(l1)
d = l1.modifiers.new("d", "DECIMATE")
d.ratio = float(os.environ.get("RP_LOD1", 0.35))
bpy.ops.object.select_all(action="DESELECT")
l1.select_set(True)
bpy.context.view_layer.objects.active = l1
bpy.ops.object.modifier_apply(modifier="d")
l1.name = l1.data.name = f"{name}_LOD1"
for o in (ob, l1):
    print(f"PP RESULT {o.name} tris={sum(len(p.vertices) - 2 for p in o.data.polygons)} size={tuple(round(v, 2) for v in o.dimensions)}")
bpy.ops.object.select_all(action="DESELECT")
ob.select_set(True)
l1.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), use_selection=True, export_format="GLB", export_image_format="AUTO", export_tangents=True)
