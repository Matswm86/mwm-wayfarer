"""Beauty corner (pass 3): photogrammetry scans of real Norwegian buildings -> game GLBs.

Sources (Sketchfab, CC BY 4.0, downloaded with the owner's token into
~/MWM/scratch/wayfarer/p3/dl/<uid>/src/, never committed):
  cabin56  "Cabin 56, Norsk Folkemuseum" by Epic_Tree_Store (johngreenstone), d032f905bb1c...
  evju     "Stabbur fra Evju bygdetun" by Kulturarv i Telemark fylkeskommune (sindrearn), a3f76ecf...

Per building:
  1. import the source mesh (its UVs match the full-size scan texture; the GLB download is 1K);
  2. cut the scanned ground away: up-facing low faces outside the wall footprint, and the plinth
     skirt below the ground;
  3. scale to real size (ridge height), origin at the ground under the footprint centre, +Y up;
  4. LOD0 = collapse-decimated copy (UVs kept), LOD1 = lighter copy;
  5. bake the full scan's surface into a tangent-space normal map on LOD0's UVs (Cycles,
     selected-to-active), so the decimated walls keep every log edge and turf clump;
  6. export assets/models/corner/<name>.glb (LOD0 + LOD1 nodes) + <name>_albedo.jpg (the scan
     texture, 4K) + <name>_normal.png.

Run (about 5-10 min, GPU Cycles):
  blender -b --factory-startup -P tools/spike/export_corner_houses.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import bmesh
import bpy
import mathutils

ROOT = Path(__file__).resolve().parents[2]
DL = Path.home() / "MWM" / "scratch" / "wayfarer" / "p3" / "dl"
OUT = ROOT / "assets" / "models" / "corner"
OUT.mkdir(parents=True, exist_ok=True)

# name: source mesh, texture, ridge height (m), LOD0 / LOD1 triangle targets, normal map px,
# ground band (source units, z range where the scanned ground lies), extra yaw (deg)
BUILDINGS = {
    "cabin56": {
        "mesh": DL / "d032f905bb1c41cc8a6d5f8b35057055/src/source/untitled.obj",
        "tex": DL / "d032f905bb1c41cc8a6d5f8b35057055/src/textures/Baked.jpg",
        "ridge": 7.2,
        "lod0": 70000,
        "lod1": 12000,
        "nrm_px": 4096,
    },
    "evju": {
        "mesh": DL / "a3f76ecf65a148a0ba3a1c696b8cddef/src/source/Evju.dae",
        "tex": DL / "a3f76ecf65a148a0ba3a1c696b8cddef/src/textures/Evju.jpeg",
        "ridge": 7.6,
        "lod0": 60000,
        "lod1": 10000,
        "nrm_px": 4096,
    },
}


def log(*a) -> None:
    print("CORNER", *a, flush=True)


def clean() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_mesh(path: Path, axes: tuple[str, str] | None = None) -> bpy.types.Object:
    if path.suffix == ".obj" and axes:
        bpy.ops.wm.obj_import(filepath=str(path), forward_axis=axes[0], up_axis=axes[1])
    elif path.suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    else:
        bpy.ops.wm.collada_import(filepath=str(path))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # one material with the full-size scan texture
    ob.data.materials.clear()
    return ob


def ground_level(ob: bpy.types.Object) -> tuple[float, float]:
    """(ground z under the walls, top of the scanned ground) from the vertex heights."""
    zs = sorted(v.co.z for v in ob.data.vertices)
    zmin, zmax = zs[0], zs[-1]
    span = zmax - zmin
    # the scanned ground is the densest low band: the histogram peak in the lower 40 %
    bins = [0] * 60
    for z in zs:
        k = min(int((z - zmin) / span * 60), 59)
        bins[k] += 1
    low = bins[: int(60 * 0.4)]
    peak = low.index(max(low))
    g = zmin + (peak + 0.5) / 60 * span
    return g, g + span * 0.06


def footprint(ob: bpy.types.Object, g: float, span: float) -> tuple[float, float, float, float]:
    """XY box of the walls: vertices 15-35 % of the height above the ground."""
    lo, hi = g + 0.15 * span, g + 0.35 * span
    xs = [v.co.x for v in ob.data.vertices if lo < v.co.z < hi]
    ys = [v.co.y for v in ob.data.vertices if lo < v.co.z < hi]
    xs.sort()
    ys.sort()
    n = len(xs)
    # trim 1 % each side against stray scan points (fence posts stay outside)
    return xs[n // 100], xs[-n // 100 - 1], ys[n // 100], ys[-n // 100 - 1]


def cut_ground(ob: bpy.types.Object) -> tuple[float, tuple]:
    zs = [v.co.z for v in ob.data.vertices]
    span = max(zs) - min(zs)
    g, g_top = ground_level(ob)
    x0, x1, y0, y1 = footprint(ob, g, span)
    pad = 0.04 * span
    log(f"ground {g:.2f} (top {g_top:.2f}), footprint x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f}")
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        inside = x0 - pad < c.x < x1 + pad and y0 - pad < c.y < y1 + pad
        up = f.normal.z > 0.55
        if (
            c.z < g - 0.03 * span
            or not inside
            and up
            and c.z < g_top
            or not inside
            and c.z < g - 0.005 * span
        ):  # plinth skirt and its underside
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    # drop small floating islands left behind (bits of grass, debris)
    bm.faces.ensure_lookup_table()
    seen = set()
    islands = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]
        isl = []
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            isl.append(cur)
            for e in cur.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        stack.append(nf)
        islands.append(isl)
    islands.sort(key=len, reverse=True)
    small = [f for isl in islands[1:] if len(isl) < 200 for f in isl]
    bmesh.ops.delete(bm, geom=small, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    log(f"kept {len(ob.data.polygons)} faces ({len(kill)} ground, {len(small)} debris cut)")
    return g, (x0, x1, y0, y1)


def material(name: str, tex: Path, nrm: Path | None) -> bpy.types.Material:
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(str(tex))
    nt.links.new(ti.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    if nrm:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(str(nrm))
        tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], bsdf.inputs["Normal"])
    return m


def decimated(src: bpy.types.Object, name: str, tris: int) -> bpy.types.Object:
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name
    bpy.context.scene.collection.objects.link(ob)
    cur = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = min(1.0, tris / max(cur, 1))
    mod.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier="dec")
    bpy.ops.object.shade_smooth()
    log(f"{name}: {cur} -> {sum(len(p.vertices) - 2 for p in ob.data.polygons)} tris")
    return ob


def bake_normal(high: bpy.types.Object, low: bpy.types.Object, px: int, out: Path) -> None:
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
            break
        except TypeError:
            continue
    sc.cycles.samples = 1
    img = bpy.data.images.new(low.name + "_nrm", px, px, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color"
    mat = low.data.materials[0]
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    mat.node_tree.nodes.active = node
    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    zs = [v.co.z for v in low.data.vertices]
    ext = (max(zs) - min(zs)) * 0.004
    bpy.ops.object.bake(
        type="NORMAL",
        use_selected_to_active=True,
        cage_extrusion=ext,
        max_ray_distance=ext * 3,
        margin=8,
        normal_space="TANGENT",
    )
    img.filepath_raw = str(out)
    img.file_format = "PNG"
    img.save()
    mat.node_tree.nodes.remove(node)
    log("normal map", out.name)


def build(name: str, spec: dict) -> None:
    clean()
    ob = import_mesh(spec["mesh"], spec.get("obj_axes"))
    g, (x0, x1, y0, y1) = cut_ground(ob)
    zs = [v.co.z for v in ob.data.vertices]
    k = spec["ridge"] / (max(zs) - g)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for v in ob.data.vertices:
        v.co = mathutils.Vector(((v.co.x - cx) * k, (v.co.y - cy) * k, (v.co.z - g) * k))
    ob.data.update()
    log(f"{name}: scale {k:.4f}, footprint {(x1 - x0) * k:.1f} x {(y1 - y0) * k:.1f} m")
    tex = OUT / f"{name}_albedo.jpg"
    if spec.get("tex_px"):
        im = bpy.data.images.load(str(spec["tex"]))
        im.scale(spec["tex_px"], spec["tex_px"])
        im.filepath_raw = str(tex)
        im.file_format = "JPEG"
        bpy.context.scene.render.image_settings.quality = 92
        im.save()
    else:
        shutil.copy(spec["tex"], tex)
    nrm = OUT / f"{name}_normal.png"
    ob.data.materials.append(material(name, tex, None))
    ob.name = name + "_high"
    lod0 = decimated(ob, f"{name}_LOD0", spec["lod0"])
    bake_normal(ob, lod0, spec["nrm_px"], nrm)
    lod1 = decimated(ob, f"{name}_LOD1", spec["lod1"])
    final = material(name, tex, nrm)
    for o in (lod0, lod1):
        o.data.materials.clear()
        o.data.materials.append(final)
    bpy.data.objects.remove(ob)
    bpy.ops.object.select_all(action="DESELECT")
    lod0.select_set(True)
    lod1.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(OUT / f"{name}.glb"),
        use_selection=True,
        export_format="GLB",
        export_image_format="NONE",
        export_yup=True,
        export_apply=True,
    )
    log("exported", name)


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else list(BUILDINGS)
    for n in only:
        build(n, BUILDINGS[n])
