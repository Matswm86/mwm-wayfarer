"""Scanned rock (Poly Haven, CC0) -> phone rock with LOD0/1/2 and a baked texture set.

Run: wf_run.sh tools/assets/bake_rock.py <log> -- <gltf> <name> <tris_lod0> <tex_px> [split]
  split: the scan is a set of separate stones -> one shared atlas, one node per stone
         (<name>_<i>_LOD0/1/2); otherwise one piece (<name>_LOD0/1/2).
Writes assets/incoming/rocks/<name>.glb + <name>_albedo/_normal/_orm.png
  albedo  graded towards fjord gneiss: saturation RK_SAT (0.5), mean sRGB luminance RK_LUM (0.33),
          slight cool tint; set RK_SAT=1 RK_LUM=0 to keep the scan's own colour
  normal  OpenGL (Godot), baked from the full scan (+ its own normal map)
  orm     R = AO (low mesh, Cycles) x scan AO, G = roughness from the scan, B = 0
Env: RK_LOD1 (0.3) and RK_LOD2 (0.08) = triangle ratios of LOD0; RK_MINPART (0.02) = drop loose parts
     smaller than this fraction of the biggest piece's bounding diagonal; RK_MAXPARTS (8).
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

REPO = Path(__file__).resolve().parents[2]
args = sys.argv[sys.argv.index("--") + 1:]
gltf, name, tris0, px = args[0], args[1], int(args[2]), int(args[3])
split = len(args) > 4 and args[4] == "split"
OUT = REPO / "assets/incoming/rocks"
OUT.mkdir(parents=True, exist_ok=True)
SAT = float(os.environ.get("RK_SAT", 0.35))
LUM = float(os.environ.get("RK_LUM", 0.33))
R1 = float(os.environ.get("RK_LOD1", 0.3))
R2 = float(os.environ.get("RK_LOD2", 0.08))
MINPART = float(os.environ.get("RK_MINPART", 0.02))
MAXPARTS = int(os.environ.get("RK_MAXPARTS", 8))


def log(*a):
    print("RK", *a, flush=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
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
sc.world = bpy.data.worlds.new("w")
sc.world.color = (1, 1, 1)

bpy.ops.import_scene.gltf(filepath=gltf)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
dup = [o for o in meshes if o.name.lower().startswith("low") or o.data.name.lower().startswith("low")]
if dup and len(dup) < len(meshes):  # some scan sets ship their own low-poly copy on top of the stones
    for o in dup:
        log("drop duplicate low mesh", o.name)
        bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
hi = meshes[0]
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
for o in list(bpy.data.objects):
    if o is not hi:
        bpy.data.objects.remove(o, do_unlink=True)
hi.parent = None
hi.name = "hi"
ntri = sum(len(p.vertices) - 2 for p in hi.data.polygons)
dim = max(hi.dimensions)
log("scan", ntri, "tris, size", tuple(round(v, 2) for v in hi.dimensions))

# ---------------------------------------------------------------- low mesh
lo = hi.copy()
lo.data = hi.data.copy()
lo.name = "lo"
sc.collection.objects.link(lo)
bm = bmesh.new()
bm.from_mesh(lo.data)
nv0 = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dim * 1e-5)  # glTF splits every UV seam
log("welded", nv0, "->", len(bm.verts))
# drop scan crumbs: loose parts far smaller than the biggest one
parts = []
seen = set()
bm.verts.ensure_lookup_table()
for v in bm.verts:
    if v.index in seen:
        continue
    st, isl = [v], []
    while st:
        x = st.pop()
        if x.index in seen:
            continue
        seen.add(x.index)
        isl.append(x)
        st.extend(e.other_vert(x) for e in x.link_edges if e.other_vert(x).index not in seen)
    co = np.array([q.co[:] for q in isl])
    parts.append((float(np.linalg.norm(co.max(0) - co.min(0))), isl))
parts.sort(key=lambda t: -t[0])
big = parts[0][0]
keep = [p for p in parts if p[0] >= big * (0.25 if split else MINPART)]
if split:
    keep = keep[:MAXPARTS]
drop = [v for p in parts if p not in keep for v in p[1]]
bmesh.ops.delete(bm, geom=drop, context="VERTS")
bm.to_mesh(lo.data)
bm.free()
log("parts kept", len(keep), "of", len(parts))
cur = sum(len(p.vertices) - 2 for p in lo.data.polygons)
mod = lo.modifiers.new("dec", "DECIMATE")
mod.ratio = min(1.0, tris0 / max(cur, 1))
mod.use_collapse_triangulate = True
bpy.ops.object.select_all(action="DESELECT")
lo.select_set(True)
bpy.context.view_layer.objects.active = lo
bpy.ops.object.modifier_apply(modifier="dec")
log("LOD0 tris", len(lo.data.polygons))
while lo.data.uv_layers:
    lo.data.uv_layers.remove(lo.data.uv_layers[0])
lo.data.uv_layers.new(name="UVMap")
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.6)
bpy.ops.uv.pack_islands(margin=0.003)
bpy.ops.object.mode_set(mode="OBJECT")
lo.data.materials.clear()
mat = bpy.data.materials.new(name)
mat.use_nodes = True
lo.data.materials.append(mat)
nt = mat.node_tree
img_node = nt.nodes.new("ShaderNodeTexImage")
nt.nodes.active = img_node

# scan AO (glTF occlusion) as emission, to multiply in
ao_src = next((im for im in bpy.data.images if any(k in (im.name + im.filepath).lower() for k in ("_arm", "_ao_", "_ao."))), None)
for im in bpy.data.images:
    log("image", im.name, im.filepath)
log("scan ao/arm image", ao_src.name if ao_src else None)

imgs = {}
for kind in ("albedo", "normal", "rough", "ao", "scanao"):
    im = bpy.data.images.new(f"{name}_{kind}", px, px, alpha=False, float_buffer=kind == "normal")
    im.colorspace_settings.name = "sRGB" if kind == "albedo" else "Non-Color"
    imgs[kind] = im

sc.cycles.samples = 16
bk = sc.render.bake
bk.use_selected_to_active = True
bk.cage_extrusion = dim * 0.006
bk.max_ray_distance = dim * 0.03
bk.margin = 16
bk.use_pass_direct = False
bk.use_pass_indirect = False
bk.use_pass_color = True


def select_pair():
    bpy.ops.object.select_all(action="DESELECT")
    hi.select_set(True)
    lo.select_set(True)
    bpy.context.view_layer.objects.active = lo


for kind, btype in (("albedo", "DIFFUSE"), ("normal", "NORMAL"), ("rough", "ROUGHNESS")):
    select_pair()
    img_node.image = imgs[kind]
    bpy.ops.object.bake(type=btype)
    log("baked", kind)

# scan AO: route arm.R / ao into emission of the high mesh, bake EMIT
if ao_src is not None:
    saved = []
    for m in hi.data.materials:
        t = m.node_tree
        out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
        prev = out.inputs[0].links[0].from_socket if out.inputs[0].is_linked else None
        ti = t.nodes.new("ShaderNodeTexImage")
        ti.image = ao_src
        uvn = t.nodes.new("ShaderNodeUVMap")
        t.links.new(uvn.outputs[0], ti.inputs[0])
        sep = t.nodes.new("ShaderNodeSeparateColor")
        t.links.new(ti.outputs[0], sep.inputs[0])
        em = t.nodes.new("ShaderNodeEmission")
        t.links.new(sep.outputs[0], em.inputs[0])
        t.links.new(em.outputs[0], out.inputs[0])
        saved.append((t, out, prev))
    select_pair()
    img_node.image = imgs["scanao"]
    bpy.ops.object.bake(type="EMIT")
    for t, out, prev in saved:
        if prev is not None:
            t.links.new(prev, out.inputs[0])
    log("baked scan ao")
else:
    imgs["scanao"].pixels.foreach_set(np.ones(px * px * 4, np.float32))  # no scan AO

bk.use_selected_to_active = False
bpy.ops.object.select_all(action="DESELECT")
lo.select_set(True)
img_node.image = imgs["ao"]
sc.cycles.samples = 64
sc.world.light_settings.distance = dim * 0.15
bpy.ops.object.bake(type="AO")
log("baked ao")


def arr(im):
    return np.array(im.pixels[:], np.float32).reshape(px, px, 4)


def save(a3, path, colour):
    im = bpy.data.images.new(path.stem, px, px, alpha=False)
    im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    im.pixels.foreach_set(np.dstack([np.clip(a3, 0, 1), np.ones(a3.shape[:2])]).astype(np.float32).ravel())
    im.filepath_raw = str(path)
    im.file_format = "PNG"
    im.save()


al = arr(imgs["albedo"])[..., :3]
valid = al.sum(-1) > 0.003
if SAT < 0.999 or LUM > 0:
    L = (al * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    g = L + (al - L) * SAT
    g *= np.array([0.97, 1.0, 1.035])
    if LUM > 0:
        cur_l = float((g * np.array([0.2126, 0.7152, 0.0722])).sum(-1)[valid].mean())
        g *= LUM / max(cur_l, 1e-3)
    al = np.where(valid[..., None], g, al)
log("albedo mean sRGB", al[valid].mean(0).round(3))
save(al, OUT / f"{name}_albedo.png", True)
save(arr(imgs["normal"])[..., :3], OUT / f"{name}_normal.png", False)
ao = arr(imgs["scanao"])[..., 0] * (0.7 + 0.3 * arr(imgs["ao"])[..., 0])  # low-mesh AO is unreliable on open scan sheets
ro = arr(imgs["rough"])[..., 0]
save(np.dstack([ao, ro, np.zeros_like(ao)]), OUT / f"{name}_orm.png", False)

# final material
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(b.outputs[0], out.inputs[0])
ta = nt.nodes.new("ShaderNodeTexImage")
ta.image = bpy.data.images.load(str(OUT / f"{name}_albedo.png"))
nt.links.new(ta.outputs[0], b.inputs["Base Color"])
tn = nt.nodes.new("ShaderNodeTexImage")
tn.image = bpy.data.images.load(str(OUT / f"{name}_normal.png"))
tn.image.colorspace_settings.name = "Non-Color"
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(tn.outputs[0], nm.inputs["Color"])
nt.links.new(nm.outputs[0], b.inputs["Normal"])
to = nt.nodes.new("ShaderNodeTexImage")
to.image = bpy.data.images.load(str(OUT / f"{name}_orm.png"))
to.image.colorspace_settings.name = "Non-Color"
sp = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(to.outputs[0], sp.inputs[0])
nt.links.new(sp.outputs[1], b.inputs["Roughness"])
nt.links.new(sp.outputs[2], b.inputs["Metallic"])

bpy.data.objects.remove(hi, do_unlink=True)

# ---------------------------------------------------------------- LODs + split + export
lods = [lo]
for k, r in ((1, R1), (2, R2)):
    c = lo.copy()
    c.data = lo.data.copy()
    sc.collection.objects.link(c)
    m_ = c.modifiers.new("dec", "DECIMATE")
    m_.ratio = r
    bpy.ops.object.select_all(action="DESELECT")
    c.select_set(True)
    bpy.context.view_layer.objects.active = c
    bpy.ops.object.modifier_apply(modifier="dec")
    lods.append(c)

final = []
for k, ob in enumerate(lods):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    pieces = [ob]
    if split:
        bpy.ops.mesh.separate(type="LOOSE")
        pieces = [o for o in bpy.context.selected_objects]
        pieces.sort(key=lambda o: -max(o.dimensions))
        pieces = pieces[:MAXPARTS]
    for i, p in enumerate(pieces):
        # pivot: bottom centre of the piece
        bpy.ops.object.select_all(action="DESELECT")
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        mn_z = min((p.matrix_world @ Vector(c)).z for c in p.bound_box)
        sc.cursor.location = (p.location.x, p.location.y, mn_z)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        p.location = (0, 0, 0) if not split else (i * dim * 0.6, 0, 0)
        p.name = f"{name}_{chr(97 + i)}_LOD{k}" if split else f"{name}_LOD{k}"
        p.data.name = p.name
        final.append(p)
for p in final:
    t = sum(len(q.vertices) - 2 for q in p.data.polygons)
    log(f"RESULT {p.name} tris={t} size=({p.dimensions.x:.2f},{p.dimensions.y:.2f},{p.dimensions.z:.2f})")
bpy.ops.object.select_all(action="DESELECT")
for p in final:
    p.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=str(OUT / f"{name}.glb"),
    use_selection=True,
    export_format="GLB",
    export_image_format="AUTO",
    export_tangents=True,
)
log("exported", OUT / f"{name}.glb")
