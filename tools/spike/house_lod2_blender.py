"""Corner pass (2026-10-11): a light LOD2 of each scanned house for distance views and the
sun-shadow proxy. Collapse-decimates the LOD1 node of assets/models/corner/<name>.glb (UVs kept)
to its TARGETS triangles and writes <out>/<name>_LOD2.glb; tools/spike/house_lod2.gd turns that into
assets/models/corner/baked/<name>_LOD2.res with the house material.

Run: blender -b --factory-startup -P tools/spike/house_lod2_blender.py -- <out dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "models" / "corner"
# triangle target per house. Only the Evju storehouse: the cabin56 scan (thin fence posts, a
# double-skin turf roof) tore open with holes at 3000 and still at 6000 triangles, so it keeps LOD1.
TARGETS = {"evju": 3000}

out = Path(sys.argv[sys.argv.index("--") + 1])
out.mkdir(parents=True, exist_ok=True)
for name, target in TARGETS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # merge the seam-split vertices so the decimator sees one surface (UVs stay as loop data)
    bpy.ops.import_scene.gltf(filepath=str(SRC / f"{name}.glb"), merge_vertices=True)
    lod1 = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.endswith("LOD1"))
    for o in list(bpy.data.objects):
        if o is not lod1:
            bpy.data.objects.remove(o, do_unlink=True)
    lod1.name = f"{name}_LOD2"
    bpy.context.view_layer.objects.active = lod1
    cur = sum(len(p.vertices) - 2 for p in lod1.data.polygons)
    mod = lod1.modifiers.new("dec", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = min(1.0, target / max(cur, 1))
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    tris = sum(len(p.vertices) - 2 for p in lod1.data.polygons)
    print(f"LOD2 {name}: {cur} -> {tris} triangles")
    bpy.ops.export_scene.gltf(
        filepath=str(out / f"{name}_LOD2.glb"), export_format="GLB", export_materials="NONE"
    )
