"""Blender: print mesh/material/texture summary of GLBs.  blender -b -P inspect_glb.py -- a.glb b.glb"""
import sys
import bpy
for path in sys.argv[sys.argv.index("--") + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    tris = 0
    print("=====", path.split("/")[-1])
    for o in bpy.data.objects:
        if o.type == "MESH":
            t = sum(len(p.vertices) - 2 for p in o.data.polygons)
            tris += t
            d = o.dimensions
            print(f"  {o.name[:40]:40s} tris={t:7d} dim=({d.x:.1f},{d.y:.1f},{d.z:.1f}) mats={[m.name for m in o.data.materials][:4]}")
        elif o.type == "ARMATURE":
            print(f"  ARMATURE {o.name} bones={len(o.data.bones)}")
    print("  TOTAL tris", tris, "actions", [a.name for a in bpy.data.actions][:12])
    for im in bpy.data.images:
        print("  img", im.name[:50], tuple(im.size))
