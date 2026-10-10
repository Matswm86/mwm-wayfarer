"""Quick look at a saved scene: blender -b file.blend -P tools/art/quick.py -- out.png scale samples [nocomp] [notrees]"""
import sys
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
sc.render.resolution_percentage = int(float(argv[1]) * 100)
sc.eevee.taa_render_samples = int(argv[2])
if "nocomp" in argv:
    sc.use_nodes = False
    sc.render.film_transparent = False
if "notrees" in argv:
    for o in sc.objects:
        if o.instance_type == "COLLECTION" and o.instance_collection and ("fir" in o.instance_collection.name or "pine" in o.instance_collection.name):
            o.hide_render = True
for a in argv:
    if a.startswith("cam="):
        from mathutils import Vector
        v = [float(t) for t in a[4:].split(",")]
        c = sc.camera
        c.location = v[:3]
        c.rotation_euler = (Vector(v[3:6]) - Vector(v[:3])).to_track_quat("-Z", "Y").to_euler()
        c.data.dof.use_dof = False
        if len(v) > 6:
            c.data.lens = v[6]
if "noplanar" in argv:
    for o in sc.objects:
        if o.type == "LIGHT_PROBE":
            o.hide_render = True
if "nograss" in argv:
    for o in sc.objects:
        if o.instance_type == "COLLECTION" and o.instance_collection and "grass" in o.instance_collection.name:
            o.hide_render = True
if "nochar" in argv:
    for o in sc.objects:
        if o.name.startswith(("explorer", "fisher", "trader")):
            o.hide_render = True
sc.render.filepath = argv[0]
import time
t = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER", argv[0], round(time.time() - t, 1))
