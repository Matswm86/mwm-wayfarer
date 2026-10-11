"""Meadow ground cover from Poly Haven plants (CC0): one 2048 atlas (4 x 4 tiles of 512) + clump meshes.

tiles 0-9   side view (camera level), plant base on the tile's bottom edge  -> near clumps (crossed cards)
tiles 10-15 oblique view (60 deg down), plant centred                      -> far ground-cover cards (35-120 m)
Writes assets/incoming/ground_cover/:
  meadow_atlas_albedo.png (RGBA, alpha = cut) / meadow_atlas_normal.png (tangent space, OpenGL) /
  meadow_atlas_orm.png / meadow_atlas.json (tile name, view, world size in m)
  meadow_clumps.glb  one node per side tile: 3 crossed quads (6 tris), bent-up normals, COLOR_0 = base AO
Run: wf_run.sh tools/assets/ground_cover.py <log>
"""
import json
import math
import subprocess
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PH = (Path.home() / "MWM/scratch/wayfarer/ph")
OUT = (Path.home() / "MWM/projects/mwm-wayfarer/assets/incoming/ground_cover")
TMP = (Path.home() / "MWM/scratch/wayfarer/gc_tmp")
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
TILES = [  # (label, asset, node substring, view)
    ("grass_tall", "grass_medium_01", "tall_a", "side"),
    ("grass_large", "grass_medium_01", "large_b", "side"),
    ("grass_mid", "grass_medium_02", "", "side"),
    ("sorrel", "shrub_sorrel_01", "", "side"),
    ("dandelion", "dandelion_01", "", "side"),
    ("nettle", "nettle_plant", "", "side"),
    ("fern", "fern_02", "fern_02_a", "side"),
    ("weed", "weed_plant_02", "", "side"),
    ("celandine", "celandine_01", "_a_", "side"),
    ("grass_small", "grass_medium_01", "small_a", "side"),
    ("far_grass", "grass_medium_01", "large_b", "far"),
    ("far_grass2", "grass_medium_02", "", "far"),
    ("far_periwinkle", "periwinkle_plant", "", "far"),
    ("far_shrub", "shrub_04", "", "far"),
    ("far_celandine", "celandine_01", "_b_", "far"),
    ("far_fern", "fern_02", "fern_02_b", "far"),
]


def reset():
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
    sc.cycles.samples = 16
    sc.cycles.max_bounces = 1
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.render.image_settings.color_mode = "RGBA"
    sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0, 0, 0)
    sc.world.light_settings.distance = 0.15
    return sc


def override(objs, mode):
    done = set()
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if not m or m.name in done:
                continue
            done.add(m.name)
            nt = m.node_tree
            b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            base = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].is_linked else None
            alpha = b.inputs["Alpha"].links[0].from_socket if b.inputs["Alpha"].is_linked else None
            nrm = b.inputs["Normal"].links[0].from_socket if b.inputs["Normal"].is_linked else None
            for n in list(nt.nodes):
                if n.name.startswith("gc_"):
                    nt.nodes.remove(n)
            em = nt.nodes.new("ShaderNodeEmission")
            em.name = "gc_em"
            if mode == "albedo":
                if base is not None:
                    nt.links.new(base, em.inputs[0])
                else:
                    em.inputs[0].default_value = b.inputs["Base Color"].default_value
            elif mode == "ao":
                ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
                ao.name = "gc_ao"
                ao.inputs["Distance"].default_value = 0.08
                nt.links.new(ao.outputs["AO"], em.inputs[0])
            else:
                if nrm is None:
                    g = nt.nodes.new("ShaderNodeNewGeometry")
                    g.name = "gc_geo"
                    nrm = g.outputs["Normal"]
                vt = nt.nodes.new("ShaderNodeVectorTransform")
                vt.name = "gc_vt"
                vt.vector_type = "NORMAL"
                vt.convert_from, vt.convert_to = "WORLD", "CAMERA"
                nt.links.new(nrm, vt.inputs[0])
                ma = nt.nodes.new("ShaderNodeVectorMath")
                ma.name = "gc_ma"
                ma.operation = "MULTIPLY_ADD"
                ma.inputs[1].default_value = (0.5, 0.5, -0.5)  # Cycles camera +Z looks away
                ma.inputs[2].default_value = (0.5, 0.5, 0.5)
                nt.links.new(vt.outputs[0], ma.inputs[0])
                nt.links.new(ma.outputs[0], em.inputs[0])
            final = em.outputs[0]
            if alpha is not None:
                tr = nt.nodes.new("ShaderNodeBsdfTransparent")
                tr.name = "gc_tr"
                mx = nt.nodes.new("ShaderNodeMixShader")
                mx.name = "gc_mx"
                gt = nt.nodes.new("ShaderNodeMath")  # hard cut: partial alpha carries the texture's black fringe
                gt.name = "gc_gt"
                gt.operation = "GREATER_THAN"
                gt.inputs[1].default_value = 0.5
                nt.links.new(alpha, gt.inputs[0])
                nt.links.new(gt.outputs[0], mx.inputs[0])
                nt.links.new(tr.outputs[0], mx.inputs[1])
                nt.links.new(em.outputs[0], mx.inputs[2])
                final = mx.outputs[0]
            nt.links.new(final, out.inputs[0])


meta = []
for i, (label, asset, sub, view) in enumerate(TILES):
    sc = reset()
    bpy.ops.import_scene.gltf(filepath=str(PH / f"{asset}_2k/{asset}_2k.gltf"))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    pick = [o for o in meshes if sub in o.name] if sub else meshes
    if not pick:
        pick = meshes
    first = pick[0]
    keep = {first} | {o for o in meshes if o.parent == first}
    if sub == "" and len(meshes) > 1:
        keep = {meshes[0]}
    for o in meshes:
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    keep = [o for o in bpy.data.objects if o.type == "MESH"]
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in keep:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    w_, d_, h_ = hi.x - lo.x, hi.y - lo.y, hi.z - lo.z
    cd = bpy.data.cameras.new("c")
    cd.type = "ORTHO"
    cam = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    if view == "side":
        size = max(w_, h_) * 1.04
        cd.ortho_scale = size
        cam.location = (cx, lo.y - 20, lo.z + size / 2)
        cam.rotation_euler = (math.radians(90), 0, 0)
    else:
        size = max(w_, d_ * math.sin(math.radians(60)) + h_ * math.cos(math.radians(60))) * 1.15
        cd.ortho_scale = size
        e = math.radians(60)
        dvec = Vector((0, -math.cos(e), math.sin(e)))
        cam.location = Vector((cx, cy, lo.z + h_ * 0.3)) + dvec * 20
        cam.rotation_euler = (-dvec).to_track_quat("-Z", "Y").to_euler()
    cd.clip_end = 100
    for mode in ("albedo", "normal", "ao"):
        override(keep, mode)
        sc.view_settings.view_transform = "Standard" if mode == "albedo" else "Raw"
        sc.render.filepath = str(TMP / f"t{i:02d}_{mode}.png")
        bpy.ops.render.render(write_still=True)
    meta.append({"tile": i, "name": label, "source": f"Poly Haven {asset} (CC0)", "view": view,
                 "world_size_m": round(size, 3), "plant_height_m": round(h_, 3)})
    print("GC tile", i, label, round(size, 2), flush=True)

(OUT / "meadow_atlas.json").write_text(json.dumps({"tiles_per_row": 4, "tile_px": 512, "tiles": meta,
    "note": "side tiles: plant base on the tile bottom edge; far tiles: 60 deg down view, centred"}, indent=1))
pack = f'''
import numpy as np
from PIL import Image, ImageFilter
T="{TMP}"; O="{OUT}"
alb=np.zeros((2048,2048,4),np.uint8); nor=np.zeros((2048,2048,3),np.uint8); orm=np.zeros((2048,2048,3),np.uint8)
for i in range(16):
    y,x=(i//4)*512,(i%4)*512
    a=np.asarray(Image.open(f"{{T}}/t{{i:02d}}_albedo.png").convert("RGBA")).astype(np.float32)
    n=np.asarray(Image.open(f"{{T}}/t{{i:02d}}_normal.png").convert("RGBA")).astype(np.float32)
    o=np.asarray(Image.open(f"{{T}}/t{{i:02d}}_ao.png").convert("RGBA")).astype(np.float32)
    m=a[...,3]>10; rgb=a[...,:3].copy()
    fill=rgb[m].mean(0) if m.any() else np.array([70,90,40.])
    rgb[~m]=fill
    for r in (2,6,14):
        bl=np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)
        rgb=np.where(m[...,None],a[...,:3],bl)
    alb[y:y+512,x:x+512]=np.dstack([rgb.astype(np.uint8),a[...,3].astype(np.uint8)])
    nn=n[...,:3]; nn[~m]=(128,128,255); nor[y:y+512,x:x+512]=nn.astype(np.uint8)
    ao=o[...,0]; ao[~m]=255
    orm[y:y+512,x:x+512]=np.dstack([ao,np.full_like(ao,0.85*255),np.zeros_like(ao)]).astype(np.uint8)
Image.fromarray(alb,"RGBA").save(O+"/meadow_atlas_albedo.png",optimize=True)
Image.fromarray(nor).save(O+"/meadow_atlas_normal.png",optimize=True)
Image.fromarray(orm).save(O+"/meadow_atlas_orm.png",optimize=True)
print("GC packed")
'''
subprocess.run(["python3", "-c", pack], check=True)

# clump meshes
bpy.ops.wm.read_factory_settings(use_empty=True)
m = bpy.data.materials.new("meadow_atlas")
m.use_nodes = True
nt = m.node_tree
b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
ta = nt.nodes.new("ShaderNodeTexImage")
ta.image = bpy.data.images.load(str(OUT / "meadow_atlas_albedo.png"))
nt.links.new(ta.outputs[0], b.inputs["Base Color"])
lt = nt.nodes.new("ShaderNodeMath")
lt.operation = "LESS_THAN"
lt.inputs[1].default_value = 0.4
one = nt.nodes.new("ShaderNodeMath")
one.operation = "SUBTRACT"
one.inputs[0].default_value = 1.0
nt.links.new(ta.outputs[1], lt.inputs[0])
nt.links.new(lt.outputs[0], one.inputs[1])
nt.links.new(one.outputs[0], b.inputs["Alpha"])
tn = nt.nodes.new("ShaderNodeTexImage")
tn.image = bpy.data.images.load(str(OUT / "meadow_atlas_normal.png"))
tn.image.colorspace_settings.name = "Non-Color"
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(tn.outputs[0], nm.inputs["Color"])
nt.links.new(nm.outputs[0], b.inputs["Normal"])
m.use_backface_culling = False
objs = []
for t in meta:
    if t["view"] != "side":
        continue
    i, s = t["tile"], t["world_size_m"]
    u0, v0 = (i % 4) / 4, 1 - (i // 4 + 1) / 4
    verts, faces, uvs, nors = [], [], [], []
    for k in range(3):
        a = math.radians(60 * k + 15)
        d = Vector((math.cos(a), math.sin(a), 0))
        fn = Vector((-d.y, d.x, 0))
        base = len(verts)
        for sx, sz in ((-0.5, 0), (0.5, 0), (0.5, 1), (-0.5, 1)):
            verts.append(d * sx * s + Vector((0, 0, sz * s)))
            uvs.append((u0 + (sx + 0.5) / 4, v0 + sz / 4))
            nors.append((fn * 0.35 + Vector((0, 0, 1)) * 0.65).normalized())
        faces.append((base, base + 1, base + 2, base + 3))
    me = bpy.data.meshes.new(f"clump_{t['name']}")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.uv_layers.new(name="UVMap")
    me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    uvl = me.uv_layers["UVMap"]
    col = me.color_attributes["Col"]
    for p in me.polygons:
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            uvl.data[li].uv = uvs[vi]
            ao = 0.55 + 0.45 * min(1.0, verts[vi].z / max(s, 0.01))
            col.data[li].color = (ao, ao, ao, 1)
    me.normals_split_custom_set_from_vertices([tuple(n) for n in nors])
    me.materials.append(m)
    o = bpy.data.objects.new(f"clump_{t['name']}", me)
    bpy.context.scene.collection.objects.link(o)
    o.location.x = len(objs) * 1.2
    objs.append(o)
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT / "meadow_clumps.glb"), use_selection=True, export_format="GLB",
                          export_image_format="AUTO", export_vertex_color="ACTIVE", export_all_vertex_colors=True)
print("GC clumps", len(objs))
