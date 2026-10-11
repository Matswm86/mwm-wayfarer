"""Re-export GLBs after their PNG textures were edited on disk: every embedded image whose name matches a PNG
next to the GLB (same stem) is replaced by that file. usage: blender -b -P regrade_glb.py -- <glb> [<glb> ...]"""
import sys
from pathlib import Path

import bpy

for glb in sys.argv[sys.argv.index("--") + 1:]:
    p = Path(glb)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(p))
    n = 0
    for im in bpy.data.images:
        cand = p.parent / f"{im.name.split('.')[0]}.png"
        if cand.exists():
            im.filepath = str(cand)
            im.reload()
            n += 1
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=str(p), use_selection=True, export_format="GLB", export_image_format="AUTO",
                              export_tangents=True)
    print("RG", p.name, "images replaced", n, flush=True)
