"""Turn a Poly Haven full-geometry tree (CC0, 4-7 M triangles) into a phone game tree.

Output per variant (assets/incoming/<species>/):
  <name>.glb              nodes <name>_LOD0 and <name>_LOD1, two surfaces each:
                            bark   (decimated trunk + branches, UV unwrapped, baked from the scan)
                            leaves (alpha-cut twig cards, bent "crown" normals, COLOR_0 = crown AO,
                                    UV2.x = sway weight 0 at the trunk .. 1 at the crown edge)
  <name>_bark_albedo.png / _bark_normal.png (OpenGL) / _bark_orm.png   (2048, baked AO in R)
  <species>_leaves_albedo.png (RGBA, alpha = cut) / _leaves_normal.png / _leaves_orm.png
                            (2048, 4x4 tiles of 512 px rendered from the real twig geometry;
                             shared by all variants of the species, written by the first variant)

How:
  twigs  -> voxel grid (CF_VOXEL m); each occupied voxel gets one card (two crossed quads where the
            cluster is thick) placed on the voxel's principal plane, sized from its spread; the card
            shows a random tile of the atlas. Tiles are orthographic renders of 16 real voxels
            (camera on the voxel's plane normal, near/far clip = slab around the voxel, soft round
            alpha edge so no tile shows a square border).
  trunk  -> decimate to CF_TRUNK_TRIS, smart-UV, bake diffuse / normal / AO / roughness from the
            full-resolution scan (Cycles).
  LOD1   -> same atlas, voxels 2x larger, trunk decimated to CF_TRUNK_TRIS_LOD1.

Run: wf_run.sh tools/assets/cardify_tree.py <log> -- <model> <node> <species> <name>
     e.g. -- pine_tree_01 pine_tree_01_a_LOD0 scots_pine scots_pine_a
Env: CF_VOXEL (0.5), CF_TRUNK_TRIS (6000), CF_TRUNK_TRIS_LOD1 (900), CF_ATLAS (1 = render the
     leaf atlas), CF_SEED.
"""

from __future__ import annotations

import math
import os
import re
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[2]
PH = REPO / "assets/_raw/polyhaven/models"
TEX2K = (Path.home() / "MWM/scratch/wayfarer/ph2k")
TMP = (Path.home() / "MWM/scratch/wayfarer/cardify_tmp")

model, node, species, name = sys.argv[sys.argv.index("--") + 1:][:4]
OUT = REPO / "assets/incoming" / species
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
VOXEL = float(os.environ.get("CF_VOXEL", 0.42))
TRUNK_TRIS = int(os.environ.get("CF_TRUNK_TRIS", 9000))
TRUNK_TRIS_LOD1 = int(os.environ.get("CF_TRUNK_TRIS_LOD1", 700))
DO_ATLAS = os.environ.get("CF_ATLAS", "1") == "1"
rng = np.random.default_rng(int(os.environ.get("CF_SEED", 7)))
TILES = 4  # 4 x 4 tiles
TILE_PX = 512


def log(*a):
    print("CF", *a, flush=True)


# ---------------------------------------------------------------- scene
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
sc.view_settings.view_transform = "Standard"
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0, 0, 0)

SRC_GLB = os.environ.get("CF_SRC_GLB")  # any glTF tree (e.g. a Sketchfab card tree); model/node then only label it
TWIG_RE = re.compile(os.environ.get("CF_TWIG_RE", r"twig$"))
TRUNK_RE = re.compile(os.environ.get("CF_TRUNK_RE", r"trunk"))
DROP_RE = re.compile(os.environ.get("CF_DROP_RE", r"dead"))
if SRC_GLB:
    bpy.ops.import_scene.gltf(filepath=SRC_GLB)
    ms = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in ms:  # keep the Sketchfab root's Y-up -> Z-up rotation before dropping the parents
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.ops.object.select_all(action="DESELECT")
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.join()
    src = ms[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    src.parent = None
    src.name = node
else:
    gl = next((PH / model).glob("*.gltf"))
    bpy.ops.import_scene.gltf(filepath=str(gl))
    src = bpy.data.objects[node]
for o in list(bpy.data.objects):
    if o is not src:
        bpy.data.objects.remove(o, do_unlink=True)
src.location = (0, 0, 0)
bpy.context.view_layer.update()
log("loaded", node, len(src.data.polygons), "faces")


def tex(path: Path, colour: bool) -> bpy.types.Image:
    im = bpy.data.images.load(str(path), check_existing=True)
    im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return im


def k2(part: str) -> Path:
    return TEX2K / f"{model}_{part}_2k.png"


# upgrade every material to the 2K set (+ twig alpha, which the 1K glTF lacks)
for m in src.data.materials:
    part = m.name.replace(f"{model}_", "")
    if part == "dead_branches":
        part = "bark"
    if not k2(f"{part}_diff").exists():
        # generic glTF material: name the nodes the overrides look for
        nt = m.node_tree
        b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        if b.inputs["Base Color"].is_linked and b.inputs["Base Color"].links[0].from_node.type == "TEX_IMAGE":
            img_n = b.inputs["Base Color"].links[0].from_node
            img_n.name = "diff"
            if b.inputs["Alpha"].is_linked:
                al = nt.nodes.new("ShaderNodeMath")
                al.operation = "ADD"
                al.inputs[1].default_value = 0.0
                al.name = "alpha"
                nt.links.new(img_n.outputs["Alpha"], al.inputs[0])
        nm = next((n for n in nt.nodes if n.type == "NORMAL_MAP"), None)
        if nm is None:
            nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.name = "nmap"
        m.surface_render_method = "DITHERED"
        continue
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    t_d = nt.nodes.new("ShaderNodeTexImage")
    t_d.image = tex(k2(f"{part}_diff"), True)
    t_d.name = "diff"
    nt.links.new(t_d.outputs[0], b.inputs["Base Color"])
    t_n = nt.nodes.new("ShaderNodeTexImage")
    t_n.image = tex(k2(f"{part}_nor_gl"), False)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.name = "nmap"
    nt.links.new(t_n.outputs[0], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], b.inputs["Normal"])
    t_a = nt.nodes.new("ShaderNodeTexImage")
    t_a.image = tex(k2(f"{part}_arm"), False)
    t_a.name = "arm"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(t_a.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], b.inputs["Roughness"])
    if k2(f"{part}_alpha").exists():
        t_al = nt.nodes.new("ShaderNodeTexImage")
        t_al.image = tex(k2(f"{part}_alpha"), False)
        t_al.name = "alpha"
        nt.links.new(t_al.outputs[0], b.inputs["Alpha"])
    m.surface_render_method = "DITHERED"

# ---------------------------------------------------------------- split twig vs wood
mats = [m.name for m in src.data.materials]
twig_idx = [i for i, n in enumerate(mats) if TWIG_RE.search(n)]
log("twig materials", [mats[i] for i in twig_idx])
me = src.data
npoly = len(me.polygons)
mat_idx = np.empty(npoly, np.int32)
me.polygons.foreach_get("material_index", mat_idx)
centres = np.empty(npoly * 3, np.float32)
me.polygons.foreach_get("center", centres)
centres = centres.reshape(-1, 3)
areas = np.empty(npoly, np.float32)
me.polygons.foreach_get("area", areas)
is_twig = np.isin(mat_idx, twig_idx)
tw = centres[is_twig]
tw_area = areas[is_twig]
log("twig faces", len(tw), "wood faces", int((~is_twig).sum()))

z0 = float(centres[:, 2].min())
height = float(centres[:, 2].max() - z0)
# trunk axis: mean x,y of the lowest wood faces
low = centres[(~is_twig) & (centres[:, 2] < z0 + 1.0)]
axis_xy = low[:, :2].mean(0) if len(low) else np.zeros(2)
log(f"height {height:.2f} axis {axis_xy}")

# full-res twig object (render source) and wood object (bake source)
bpy.ops.object.select_all(action="DESELECT")
src.select_set(True)
bpy.context.view_layer.objects.active = src
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
sel = np.zeros(npoly, bool)
sel[is_twig] = True
me.polygons.foreach_set("select", sel)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.separate(type="SELECTED")
bpy.ops.object.mode_set(mode="OBJECT")
wood_hi = src
wood_hi.name = "wood_hi"
twig_hi = next(o for o in bpy.data.objects if o is not wood_hi)
twig_hi.name = "twig_hi"
log("separated")


# ---------------------------------------------------------------- card layout
def card_layout(voxel: float, min_area_frac: float) -> list[dict]:
    key = np.floor(tw / voxel).astype(np.int64)
    k = (key[:, 0] + 100000) * 10**10 + (key[:, 1] + 100000) * 10**5 + (key[:, 2] + 100000)
    order = np.argsort(k)
    ks = k[order]
    starts = np.flatnonzero(np.r_[True, ks[1:] != ks[:-1]])
    ends = np.r_[starts[1:], len(ks)]
    tot_area = tw_area.sum()
    cards = []
    for s, e in zip(starts, ends):
        idx = order[s:e]
        a = tw_area[idx]
        if a.sum() < tot_area * min_area_frac or len(idx) < 6:
            continue
        p = tw[idx]
        c = (p * a[:, None]).sum(0) / a.sum()
        cov = np.cov((p - c).T, aweights=a)
        w, v = np.linalg.eigh(cov)
        sig = np.sqrt(np.maximum(w, 1e-6))
        e3, e1 = v[:, 0], v[:, 2]
        cards.append({"c": c, "e1": e1, "e3": e3, "sig": sig[::-1], "area": float(a.sum())})
    return cards


def crown_profile(cards):
    zs = np.array([c["c"][2] for c in cards])
    rs = np.array([np.linalg.norm(c["c"][:2] - axis_xy) for c in cards])
    bands = np.linspace(zs.min(), zs.max() + 1e-3, 13)
    prof = []
    for lo, hi in zip(bands[:-1], bands[1:]):
        m = (zs >= lo) & (zs < hi)
        prof.append(np.percentile(rs[m], 90) if m.sum() > 3 else 0.5)
    return bands, np.maximum(np.array(prof), 0.5)


# ---------------------------------------------------------------- leaf atlas (16 real tiles)
def emission_override(obj, mode: str):
    for m in obj.data.materials:
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        for n in list(nt.nodes):
            if n.name.startswith("ov_"):
                nt.nodes.remove(n)
        em = nt.nodes.new("ShaderNodeEmission")
        em.name = "ov_em"
        if mode == "albedo":
            nt.links.new(nt.nodes["diff"].outputs[0], em.inputs[0])
        elif mode == "ao":
            ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
            ao.name = "ov_ao"
            ao.inputs["Distance"].default_value = 0.25
            nt.links.new(ao.outputs["AO"], em.inputs[0])
        elif mode == "normal":
            vt = nt.nodes.new("ShaderNodeVectorTransform")
            vt.name = "ov_vt"
            vt.vector_type = "NORMAL"
            vt.convert_from = "WORLD"
            vt.convert_to = "CAMERA"
            nt.links.new(nt.nodes["nmap"].outputs[0], vt.inputs[0])
            # Cycles camera space: +Z points forward (away from the viewer), so flip Z for tangent blue
            ma = nt.nodes.new("ShaderNodeVectorMath")
            ma.name = "ov_ma"
            ma.operation = "MULTIPLY_ADD"
            ma.inputs[1].default_value = (0.5, 0.5, -0.5)
            ma.inputs[2].default_value = (0.5, 0.5, 0.5)
            nt.links.new(vt.outputs[0], ma.inputs[0])
            nt.links.new(ma.outputs[0], em.inputs[0])
        final = em.outputs[0]
        if "alpha" in nt.nodes:
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            tr.name = "ov_tr"
            mx = nt.nodes.new("ShaderNodeMixShader")
            mx.name = "ov_mx"
            nt.links.new(nt.nodes["alpha"].outputs[0], mx.inputs[0])
            nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(em.outputs[0], mx.inputs[2])
            final = mx.outputs[0]
        nt.links.new(final, out.inputs[0])


def restore_materials(obj):
    for m in obj.data.materials:
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.name.startswith("ov_"):
                nt.nodes.remove(n)
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        nt.links.new(b.outputs[0], out.inputs[0])



def twig_islands():
    """Vertex island labels of the twig mesh (min-label propagation + pointer jumping, numpy only)."""
    me_ = twig_hi.data
    nv = len(me_.vertices)
    co = np.empty(nv * 3, np.float32)
    me_.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) @ np.array(twig_hi.matrix_world)[:3, :3].T + np.array(twig_hi.matrix_world)[:3, 3]
    nl = len(me_.loops)
    lv = np.empty(nl, np.int64)
    me_.loops.foreach_get("vertex_index", lv)
    np_ = len(me_.polygons)
    ls = np.empty(np_, np.int64)
    lt = np.empty(np_, np.int64)
    me_.polygons.foreach_get("loop_start", ls)
    me_.polygons.foreach_get("loop_total", lt)
    nxt = np.arange(nl) + 1
    last = ls + lt - 1
    nxt[last] = ls
    a, b = lv, lv[nxt]
    lab = np.arange(nv)
    for it in range(200):
        m = np.minimum(lab[a], lab[b])
        old = lab.copy()
        np.minimum.at(lab, a, m)
        np.minimum.at(lab, b, m)
        lab = lab[lab]
        lab = lab[lab]
        if np.array_equal(lab, old):
            break
    uniq, inv = np.unique(lab, return_inverse=True)
    log("twig islands", len(uniq), "iterations", it)
    return co, inv, len(uniq), lv, ls, lt


def tile_mesh(isl, frame):
    """Temp mesh of the twig islands that sit completely inside the tile frame (no cut sprays)."""
    co, inv, n_isl, lv, ls, lt = isl
    c, e1, e2, e3, hs, depth = frame
    d = co - c
    x, y, z = np.abs(d @ e1), np.abs(d @ e2), np.abs(d @ e3)
    big = np.zeros(n_isl, np.float32)
    # radial fit (disc, not square) so a dense tile never shows a boxy outline
    for comp, lim in ((np.hypot(x, y), hs), (z, depth)):
        mx = np.zeros(n_isl, np.float32)
        np.maximum.at(mx, inv, comp / lim)
        big = np.maximum(big, mx)
    keep_isl = big <= 0.98
    vkeep = keep_isl[inv]
    fkeep = vkeep[lv[ls]]
    fidx = np.flatnonzero(fkeep)
    me_ = twig_hi.data
    nl_all = len(me_.loops)
    uv_all = np.empty(nl_all * 2, np.float32)
    me_.uv_layers[0].data.foreach_get("uv", uv_all)
    uv_all = uv_all.reshape(-1, 2)
    loops = np.concatenate([np.arange(ls[f], ls[f] + lt[f]) for f in fidx]) if len(fidx) else np.zeros(0, np.int64)
    used_v = np.unique(lv[loops])
    remap = -np.ones(len(co), np.int64)
    remap[used_v] = np.arange(len(used_v))
    m = bpy.data.meshes.new("tile")
    m.vertices.add(len(used_v))
    m.vertices.foreach_set("co", co[used_v].ravel())
    m.loops.add(len(loops))
    m.loops.foreach_set("vertex_index", remap[lv[loops]])
    m.polygons.add(len(fidx))
    starts = np.r_[0, np.cumsum(lt[fidx])[:-1]]
    m.polygons.foreach_set("loop_start", starts)
    m.polygons.foreach_set("loop_total", lt[fidx])
    m.update(calc_edges=True)
    uvl = m.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", uv_all[loops].ravel())
    for mt in twig_hi.data.materials:
        m.materials.append(mt)
    mi_all = np.empty(len(me_.polygons), np.int32)
    me_.polygons.foreach_get("material_index", mi_all)
    m.polygons.foreach_set("material_index", mi_all[fidx])
    ob = bpy.data.objects.new("tile", m)
    sc.collection.objects.link(ob)
    return ob, int(keep_isl.sum())


def render_atlas(cards):
    # pick 16 well-filled, flat clusters spread over the crown height
    flat = sorted(cards, key=lambda c: -c["area"] / (c["sig"][0] * c["sig"][1]))[: max(40, len(cards) // 8)]
    flat.sort(key=lambda c: c["c"][2])
    half = TILES * TILES // 2
    # 2x candidates per view; the densest 8 of each kind are kept after island selection
    pick = [flat[int(i)] for i in np.linspace(0, len(flat) - 1, 2 * half)]
    pick += [flat[int(i)] for i in np.linspace(1, len(flat) - 2, 2 * half)]
    cam_d = bpy.data.cameras.new("tilecam")
    cam_d.type = "ORTHO"
    cam = bpy.data.objects.new("tilecam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = TILE_PX
    sc.render.film_transparent = True
    sc.render.use_persistent_data = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    wood_hi.hide_render = True
    twig_hi.hide_render = True
    sc.cycles.max_bounces = 1
    isl = twig_islands()
    sizes, frames, tiles = [], [], []
    for i, c in enumerate(pick):
        size = float(max(VOXEL * 1.6, 2.2 * c["sig"][0]))
        up = Vector((0, 0, 1))
        radial = Vector((c["c"][0] - axis_xy[0], c["c"][1] - axis_xy[1], 0.0))
        if radial.length < 1e-3:
            radial = Vector((1, 0, 0))
        radial.normalize()
        if i < TILES * TILES:  # top view: the spray seen from above, image up = outward
            e3 = up
            e2 = radial
            e1 = e2.cross(e3).normalized()
        else:  # side view: looking along the tangent, image up = world up, right = outward
            e1 = radial
            e2 = up
            e3 = e1.cross(e2).normalized()
        depth = max(0.5 * size, 0.35)
        sizes.append(size)
        frames.append((Vector(c["c"]), e1, e2, e3, size, depth))
        ob, n = tile_mesh(isl, (np.array(c["c"]), np.array(e1), np.array(e2), np.array(e3), size / 2, depth))
        ob.hide_render = True
        tiles.append((len(ob.data.polygons), ob))
        log("candidate", i, "islands", n, "faces", len(ob.data.polygons))
    keep = []
    for lo_, hi_ in ((0, 2 * half), (2 * half, 4 * half)):
        best = sorted(range(lo_, hi_), key=lambda k: -tiles[k][0])[:half]
        keep += sorted(best)
    for k in range(len(tiles)):
        if k not in keep:
            bpy.data.objects.remove(tiles[k][1], do_unlink=True)
    frames = [frames[k] for k in keep]
    sizes = [sizes[k] for k in keep]
    tiles = [tiles[k][1] for k in keep]
    for mode, spp in (("albedo", 16), ("normal", 16), ("ao", 64)):
        emission_override(twig_hi, mode)
        # data passes must not be sRGB-encoded by the view transform
        sc.view_settings.view_transform = "Standard" if mode == "albedo" else "Raw"
        sc.cycles.samples = spp
        sc.cycles.use_denoising = False
        for i, (cv, e1, e2, e3, size, depth) in enumerate(frames):
            for j, t in enumerate(tiles):
                t.hide_render = j != i
            cam_d.ortho_scale = size
            cam_d.clip_start = 5.0 - depth - 0.2
            cam_d.clip_end = 5.0 + depth + 0.2
            rot = Matrix((e1, e2, e3)).transposed().to_4x4()
            cam.matrix_world = Matrix.Translation(cv + e3 * 5.0) @ rot
            sc.render.filepath = str(TMP / f"{species}_{mode}_{i:02d}.png")
            bpy.ops.render.render(write_still=True)
    for t in tiles:
        bpy.data.objects.remove(t, do_unlink=True)
    twig_hi.hide_render = False
    wood_hi.hide_render = False
    restore_materials(twig_hi)
    log("tiles rendered")
    return sizes


def pack_atlas():
    import subprocess

    subprocess.run(["python3", str(Path(__file__).with_name("pack_leaf_atlas.py")), str(TMP), str(OUT), species,
                    str(TILES), str(TILE_PX)], check=True)
    log("atlas written")


# ---------------------------------------------------------------- build card mesh
def build_cards(cards, label: str, tile_sizes, scale_boost: float) -> bpy.types.Object:
    bands, prof = crown_profile(cards)
    verts, faces, uvs, cols, sway, nors = [], [], [], [], [], []
    crown_c = np.array([axis_xy[0], axis_xy[1], 0.0])
    inset = 4 / (TILES * TILE_PX)
    for c in cards:
        radial = c["c"] - crown_c
        radial[2] = 0.0
        rl = np.linalg.norm(radial)
        rad_h = radial / rl if rl > 1e-3 else np.array([1.0, 0.0, 0.0])
        up = np.array([0.0, 0.0, 1.0])
        size = max(VOXEL * 1.15, 1.8 * c["sig"][0]) * scale_boost * rng.uniform(0.9, 1.15)
        h = size / 2
        ang = rng.uniform(-0.6, 0.6)  # yaw jitter round the trunk direction
        ca, sa = math.cos(ang), math.sin(ang)
        out = np.array([rad_h[0] * ca - rad_h[1] * sa, rad_h[0] * sa + rad_h[1] * ca, 0.0])
        tilt = rng.uniform(0.05, 0.35)  # sprays tip slightly upward at the tip
        # top card: normal near up, image-up points outward (matches the top tiles)
        e2t = out * math.cos(tilt) + up * math.sin(tilt)
        e3t = np.cross(np.cross(e2t, up), e2t)
        e3t /= np.linalg.norm(e3t)
        if e3t[2] < 0:
            e3t = -e3t
        e1t = np.cross(e2t, e3t)
        # side card: vertical, right = outward, up = world up (matches the side tiles)
        e1s = out
        e2s = up
        e3s = np.cross(e1s, e2s)
        half = TILES * TILES // 2
        quads = [(e1t, e2t, e3t, int(rng.integers(0, half)), 1.0), (e1s, e2s, e3s, int(rng.integers(half, 2 * half)), 0.8)]
        radial = c["c"] - crown_c
        radial[2] = 0.3 * max(abs(radial[0]) + abs(radial[1]), 0.3)
        z = c["c"][2]
        bi = int(np.clip(np.searchsorted(bands, z) - 1, 0, len(prof) - 1))
        rr = np.linalg.norm(c["c"][:2] - axis_xy) / prof[bi]
        ztop = (z - bands[0]) / max(bands[-1] - bands[0], 1e-3)
        ao = float(np.clip(0.30 + 0.55 * rr**0.8 + 0.15 * ztop, 0.28, 1.0))
        bend = radial / (np.linalg.norm(radial) + 1e-6)
        for a1, a2, nrm, t, hs in quads:
            tx, ty = t % TILES, t // TILES
            u0, u1 = tx / TILES + inset, (tx + 1) / TILES - inset
            v0, v1 = 1 - (ty + 1) / TILES + inset, 1 - ty / TILES - inset
            n_b = nrm * 0.35 + bend * 0.65
            n_b /= np.linalg.norm(n_b)
            i0 = len(verts)
            for sx, sy, uu, vv in ((-1, -1, u0, v0), (1, -1, u1, v0), (1, 1, u1, v1), (-1, 1, u0, v1)):
                verts.append(c["c"] + a1 * sx * h + a2 * sy * h * hs)
                uvs.append((uu, vv))
                cols.append((ao, ao, ao, 1.0))
                sway.append((float(np.clip(rr, 0, 1)), 0.0))
                nors.append(n_b)
            faces.append((i0, i0 + 1, i0 + 2, i0 + 3))
    mesh = bpy.data.meshes.new(f"{label}_leaves")
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.uv_layers.new(name="UVMap")
    mesh.uv_layers.new(name="UV2")
    mesh.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    # adding a layer reallocates the others: fetch every layer only after all exist
    uvl = mesh.uv_layers["UVMap"]
    uv2 = mesh.uv_layers["UV2"]
    col = mesh.color_attributes["Col"]
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uvl.data[li].uv = uvs[vi]
            uv2.data[li].uv = sway[vi]
            col.data[li].color = cols[vi]
    mesh.normals_split_custom_set_from_vertices([tuple(n) for n in nors])
    ob = bpy.data.objects.new(f"{label}_leaves", mesh)
    sc.collection.objects.link(ob)
    ob.data.materials.append(leaf_material())
    # triangulate for honest counts
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    return ob


_leaf_mat = None


def leaf_material():
    global _leaf_mat
    if _leaf_mat:
        return _leaf_mat
    m = bpy.data.materials.new(f"{species}_leaves")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(OUT / f"{species}_leaves_albedo.png"))
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    nt.links.new(ta.outputs[0], mul.inputs[6])
    nt.links.new(vc.outputs[0], mul.inputs[7])
    nt.links.new(mul.outputs[2], b.inputs["Base Color"])
    # glTF exporter reads 1 - (alpha < cutoff) as alphaMode MASK
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
    tn.image = bpy.data.images.load(str(OUT / f"{species}_leaves_normal.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs[0], nmap.inputs["Color"])
    nt.links.new(nmap.outputs[0], b.inputs["Normal"])
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = bpy.data.images.load(str(OUT / f"{species}_leaves_orm.png"))
    to.image.colorspace_settings.name = "Non-Color"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], b.inputs["Roughness"])
    b.inputs["Subsurface Weight"].default_value = 0.0
    m.surface_render_method = "DITHERED"
    m.use_backface_culling = False
    try:
        m.blend_method = "CLIP"
        m.alpha_threshold = 0.4
    except AttributeError:
        pass
    _leaf_mat = m
    return m


# ---------------------------------------------------------------- trunk: decimate + bake
def make_bark(label: str, target: int, bake: bool) -> bpy.types.Object:
    """Decimate trunk, branches and dead twigs with their own budgets (thin branches need more)."""
    share = {"trunk": 0.32, "bark": 0.68, "dead_branches": 0.0}
    parts = []
    for mi, mname in enumerate(mats):
        if mi in twig_idx or DROP_RE.search(mname):  # dead twigs decimate into shards; the cards cover them
            continue
        key = "trunk" if TRUNK_RE.search(mname) else ("dead_branches" if DROP_RE.search(mname) else "bark")
        p = wood_hi.copy()
        p.data = wood_hi.data.copy()
        sc.collection.objects.link(p)
        bm = bmesh.new()
        bm.from_mesh(p.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != mi], context="FACES")
        if key == "bark":
            # branches: keep the biggest pieces untouched until the budget is spent, drop the
            # twiglets (decimated tubes turn into flat ribbons; the leaf tiles carry their stems)
            seen, isl = set(), []
            for f in bm.faces:
                if f.index in seen:
                    continue
                cur_isl, st = [], [f]
                while st:
                    x = st.pop()
                    if x.index in seen:
                        continue
                    seen.add(x.index)
                    cur_isl.append(x)
                    st.extend(g for e in x.edges for g in e.link_faces if g.index not in seen)
                isl.append((sum(q.calc_area() for q in cur_isl), cur_isl))
            isl.sort(key=lambda t: -t[0])
            budget, used, drop = target * share[key], 0, []
            for area, faces_ in isl:
                if used + len(faces_) <= budget:
                    used += len(faces_)
                else:
                    drop.extend(faces_)
            bmesh.ops.delete(bm, geom=drop, context="FACES")
        bm.to_mesh(p.data)
        bm.free()
        cur = len(p.data.polygons)
        if cur == 0:
            bpy.data.objects.remove(p, do_unlink=True)
            continue
        mod = p.modifiers.new("dec", "DECIMATE")
        mod.ratio = min(1.0, target * share[key] / cur)
        mod.use_collapse_triangulate = True
        bpy.ops.object.select_all(action="DESELECT")
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.modifier_apply(modifier="dec")
        log(label, mname, cur, "->", len(p.data.polygons))
        parts.append(p)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    lo = parts[0]
    lo.name = f"{label}_bark"
    bm = bmesh.new()
    bm.from_mesh(lo.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(lo.data)
    bm.free()
    tris = len(lo.data.polygons)
    log(label, "bark tris", tris)
    if not bake:
        return lo
    while lo.data.uv_layers:
        lo.data.uv_layers.remove(lo.data.uv_layers[0])
    lo.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    lo.data.materials.clear()
    m = bpy.data.materials.new(f"{label}_bark")
    m.use_nodes = True
    lo.data.materials.append(m)
    nt = m.node_tree
    imgs = {}
    for kind in ("albedo", "normal", "ao", "rough"):
        im = bpy.data.images.new(f"{label}_{kind}", 2048, 2048, alpha=False)
        if kind != "albedo":
            im.colorspace_settings.name = "Non-Color"
        imgs[kind] = im
    node_img = nt.nodes.new("ShaderNodeTexImage")
    nt.nodes.active = node_img
    sc.cycles.samples = 32
    sc.render.bake.use_selected_to_active = True
    sc.render.use_persistent_data = False
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.render.bake.cage_extrusion = 0.08
    sc.render.bake.max_ray_distance = 0.3
    sc.render.bake.margin = 8
    bpy.ops.object.select_all(action="DESELECT")
    wood_hi.select_set(True)
    lo.select_set(True)
    bpy.context.view_layer.objects.active = lo
    for kind, btype in (("albedo", "DIFFUSE"), ("normal", "NORMAL"), ("rough", "ROUGHNESS")):
        node_img.image = imgs[kind]
        if btype == "DIFFUSE":
            sc.render.bake.use_pass_direct = False
            sc.render.bake.use_pass_indirect = False
            sc.render.bake.use_pass_color = True
        bpy.ops.object.bake(type=btype)
        px = np.array(imgs[kind].pixels[:], np.float32).reshape(-1, 4)
        log("baked", kind, px[:, :3].mean(0).round(3), "nonzero", float((px[:, :3].sum(1) > 0.01).mean()))
    # AO on the low mesh itself (includes the needles' shade? no: wood only, honest local AO)
    sc.render.bake.use_selected_to_active = False
    node_img.image = imgs["ao"]
    wood_hi.select_set(False)
    sc.cycles.samples = 64
    bpy.ops.object.bake(type="AO")
    log("baked ao")
    def arr(im):
        return np.array(im.pixels[:], np.float32).reshape(2048, 2048, 4)

    def save(a3, path, colour):
        im = bpy.data.images.new(path.stem, 2048, 2048, alpha=False)
        im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        im.pixels.foreach_set(np.dstack([a3, np.ones(a3.shape[:2], np.float32)]).ravel())
        im.filepath_raw = str(path)
        im.file_format = "PNG"
        im.save()

    # baked diffuse arrives linear in a float buffer; an sRGB image datablock stores it encoded
    save(arr(imgs["albedo"])[..., :3], OUT / f"{label}_bark_albedo.png", True)
    save(arr(imgs["normal"])[..., :3], OUT / f"{label}_bark_normal.png", False)
    ao = arr(imgs["ao"])[..., 0]
    ro = arr(imgs["rough"])[..., 0]
    save(np.dstack([ao, ro, np.zeros_like(ao)]), OUT / f"{label}_bark_orm.png", False)
    # final export material
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(OUT / f"{label}_bark_albedo.png"))
    nt.links.new(ta.outputs[0], b.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(OUT / f"{label}_bark_normal.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs[0], nmap.inputs["Color"])
    nt.links.new(nmap.outputs[0], b.inputs["Normal"])
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = bpy.data.images.load(str(OUT / f"{label}_bark_orm.png"))
    to.image.colorspace_settings.name = "Non-Color"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], b.inputs["Roughness"])
    nt.links.new(sep.outputs[2], b.inputs["Metallic"])
    return lo


# ---------------------------------------------------------------- main
cards0 = card_layout(VOXEL, 1e-5)
cards1 = card_layout(VOXEL * 2.0, 4e-5)
log("cards LOD0", len(cards0), "LOD1", len(cards1))
if DO_ATLAS or not (OUT / f"{species}_leaves_albedo.png").exists():
    sizes = render_atlas(cards0)
    pack_atlas()
    (OUT / f"{species}_tile_sizes.txt").write_text(" ".join(f"{s:.4f}" for s in sizes))
tile_sizes = [float(x) for x in (OUT / f"{species}_tile_sizes.txt").read_text().split()]

bark0 = make_bark(f"{name}", TRUNK_TRIS, bake=True)
# LOD1 = the baked LOD0 bark, small branch pieces removed, then decimated (keeps UVs + textures)
bark1 = bark0.copy()
bark1.data = bark0.data.copy()
bark1.name = f"{name}_l1_bark"
sc.collection.objects.link(bark1)
bm = bmesh.new()
bm.from_mesh(bark1.data)
seen = set()
drop = []
for f in bm.faces:
    if f.index in seen:
        continue
    isl, st = [], [f]
    while st:
        x = st.pop()
        if x.index in seen:
            continue
        seen.add(x.index)
        isl.append(x)
        st.extend(g for e in x.edges for g in e.link_faces if g.index not in seen)
    if sum(q.calc_area() for q in isl) < 0.35:
        drop.extend(isl)
bmesh.ops.delete(bm, geom=drop, context="FACES")
bm.to_mesh(bark1.data)
bm.free()
log("LOD1 wood after dropping small pieces", len(bark1.data.polygons))
if len(bark1.data.polygons) > TRUNK_TRIS_LOD1 * 2:
    mod = bark1.modifiers.new("dec", "DECIMATE")
    mod.ratio = TRUNK_TRIS_LOD1 * 2 / len(bark1.data.polygons)
    bpy.ops.object.select_all(action="DESELECT")
    bark1.select_set(True)
    bpy.context.view_layer.objects.active = bark1
    bpy.ops.object.modifier_apply(modifier="dec")

leaves0 = build_cards(cards0, name, tile_sizes, 1.0)
leaves1 = build_cards(cards1, f"{name}_l1", tile_sizes, 1.55)

bpy.data.objects.remove(twig_hi, do_unlink=True)
bpy.data.objects.remove(wood_hi, do_unlink=True)


def join(objs, nm):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = nm
    objs[0].data.name = nm
    return objs[0]


for b_ in (bark0, bark1):
    if "UV2" not in b_.data.uv_layers:
        b_.data.uv_layers.new(name="UV2")  # sway weight 0 on wood
    b_.data.uv_layers.active_index = 0
    b_.data.uv_layers[0].active_render = True
lod0 = join([bark0, leaves0], f"{name}_LOD0")
lod1 = join([bark1, leaves1], f"{name}_LOD1")
lod1.location.x = 0
for ob, lab in ((lod0, "LOD0"), (lod1, "LOD1")):
    t = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    log(f"RESULT {name} {lab} tris={t}")
bpy.ops.object.select_all(action="DESELECT")
lod0.select_set(True)
lod1.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=str(OUT / f"{name}.glb"),
    use_selection=True,
    export_format="GLB",
    export_image_format="AUTO",
    export_vertex_color="ACTIVE",
    export_all_vertex_colors=True,
    export_normals=True,
    export_tangents=True,
)
log("exported", OUT / f"{name}.glb")
