"""Export stand-in cliff rocks with three LODs for scripts/CliffRocks.gd (visual pass 2).

Poly Haven rock scans (CC0) from assets/_raw/polyhaven/models/, decimated in Blender to
LOD0 / LOD1 / LOD2 (TRIS below) and written as assets/models/rocks/<name>.glb with nodes
<name>_LOD0, <name>_LOD1, <name>_LOD2, centred on x/z, base at y = 0, longest side 1 m (the game
scales each rock). Replaced by the graphic designer's cliff set when it lands.

Run: blender -b --python tools/spike/export_rocks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "_raw" / "polyhaven" / "models"
OUT = ROOT / "assets" / "models" / "rocks"
ROCKS = ["rock_face_01", "rock_face_02"]
TRIS = [4000, 900, 160]


def clear() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def tris(ob: bpy.types.Object) -> int:
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def export(name: str) -> None:
    clear()
    gltf = next((SRC / name).glob("*.gltf"))
    bpy.ops.import_scene.gltf(filepath=str(gltf))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    base = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # normalise: centre x/z, base at 0, longest side 1 m (Blender z up)
    pts = [base.matrix_world @ Vector(c) for c in base.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    size = max(hi - lo)
    base.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.ops.object.transform_apply(location=True)
    base.scale = (1.0 / size,) * 3
    bpy.ops.object.transform_apply(scale=True)
    full = tris(base)
    objs = []
    for i, t in enumerate(TRIS):
        ob = base.copy()
        ob.data = base.data.copy()
        bpy.context.scene.collection.objects.link(ob)
        mod = ob.modifiers.new("dec", "DECIMATE")
        mod.ratio = min(1.0, t / full)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier="dec")
        ob.name = f"{name}_LOD{i}"
        objs.append(ob)
        print(f"{ob.name}: {tris(ob)} tris")
    bpy.data.objects.remove(base)
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(OUT / f"{name}.glb"),
        use_selection=True,
        export_format="GLB",
        export_yup=True,
    )


def main() -> None:
    for name in ROCKS:
        export(name)
    print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
