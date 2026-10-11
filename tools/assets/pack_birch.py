"""Birch: lolipop_1707 'Five Birch trees pack (lowpoly, LODs)' (Sketchfab, CC BY 4.0) -> game GLBs.
Textures come from the author's 4K source, flipped to the GLB's UV convention and reduced to 2K
(assets/incoming/downy_birch/downy_birch_*.png, made by the inline step in the art log).
Per variant one GLB with nodes <name>_LOD0/1/2 (author's LODs), two surfaces each (bark, leaves);
leaves get COLOR_0 = crown AO (inner/lower leaves darker) and UV2.x = sway weight (0 trunk .. 1 crown edge).

Run: wf_run.sh tools/assets/pack_birch.py <log> -- <pack.glb>
"""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "assets/incoming/downy_birch"
pack = sys.argv[sys.argv.index("--") + 1]
VARIANTS = {"a": "Birch_3", "b": "Birch_4", "c": "Birch_5"}  # Birch_5 is the multi-stem one


def log(*a):
    print("BI", *a, flush=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=pack)
for o in bpy.data.objects:
    if o.type == "MESH":
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
for o in list(bpy.data.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action="SELECT")
bpy.context.view_layer.objects.active = bpy.data.objects[0]
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def mk_mat(kind):
    m = bpy.data.materials.new(f"downy_birch_{kind}")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(OUT / f"downy_birch_{kind}_albedo.png"))
    if kind == "leaves":
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs[0].default_value = 1.0
        nt.links.new(ta.outputs[0], mul.inputs[6])
        nt.links.new(vc.outputs[0], mul.inputs[7])
        nt.links.new(mul.outputs[2], b.inputs["Base Color"])
        lt = nt.nodes.new("ShaderNodeMath")
        lt.operation = "LESS_THAN"
        lt.inputs[1].default_value = 0.5
        one = nt.nodes.new("ShaderNodeMath")
        one.operation = "SUBTRACT"
        one.inputs[0].default_value = 1.0
        nt.links.new(ta.outputs[1], lt.inputs[0])
        nt.links.new(lt.outputs[0], one.inputs[1])
        nt.links.new(one.outputs[0], b.inputs["Alpha"])
        m.surface_render_method = "DITHERED"
    else:
        nt.links.new(ta.outputs[0], b.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(OUT / f"downy_birch_{kind}_normal.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs[0], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], b.inputs["Normal"])
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = bpy.data.images.load(str(OUT / f"downy_birch_{kind}_orm.png"))
    to.image.colorspace_settings.name = "Non-Color"
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], b.inputs["Roughness"])
    nt.links.new(sp.outputs[2], b.inputs["Metallic"])
    m.use_backface_culling = False
    return m


MAT = {"leaves": mk_mat("leaves"), "bark": mk_mat("bark")}


def crown_attrs(o, centre_xy, zlo, zhi, rmax):
    me = o.data
    me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    if "UV2" not in me.uv_layers:
        me.uv_layers.new(name="UV2")
    col = me.color_attributes["Col"]
    uv2 = me.uv_layers["UV2"]
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            rr = min(1.0, Vector((v.x - centre_xy[0], v.y - centre_xy[1])).length / max(rmax, 0.1))
            zt = (v.z - zlo) / max(zhi - zlo, 0.1)
            ao = float(np.clip(0.38 + 0.5 * rr**0.8 + 0.15 * zt, 0.3, 1.0)) if o["kind"] == "leaves" else 1.0
            col.data[li].color = (ao, ao, ao, 1.0)
            uv2.data[li].uv = (rr if o["kind"] == "leaves" else 0.0, 0.0)


for vk, base in VARIANTS.items():
    nodes = []
    for lod, tag in ((0, ""), (1, "_LOD1"), (2, "_LOD2")):
        parts = []
        for kind, src in (("leaves", "Birch_Atlas"), ("bark", "Birch_bark")):
            nm = f"{base}{tag}_{src}_0"
            o = bpy.data.objects.get(nm)
            if o is None:
                log("missing", nm)
                continue
            c = o.copy()
            c.data = o.data.copy()
            bpy.context.scene.collection.objects.link(c)
            c.data.materials.clear()
            c.data.materials.append(MAT[kind])
            c["kind"] = kind
            parts.append(c)
        # crown frame from the leaves of this LOD
        lv = [p for p in parts if p["kind"] == "leaves"][0]
        co = np.array([v.co[:] for v in lv.data.vertices])
        trunk = [p for p in parts if p["kind"] == "bark"][0]
        tco = np.array([v.co[:] for v in trunk.data.vertices])
        root = tco[tco[:, 2] < tco[:, 2].min() + 0.5][:, :2].mean(0)
        rmax = float(np.percentile(np.linalg.norm(co[:, :2] - root, axis=1), 95))
        for p in parts:
            crown_attrs(p, root, co[:, 2].min(), co[:, 2].max(), rmax)
        bpy.ops.object.select_all(action="DESELECT")
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        j = parts[0]
        j.name = j.data.name = f"downy_birch_{vk}_LOD{lod}"
        # pivot at the trunk root, on the ground
        zmin = tco[:, 2].min()
        j.data.transform(__import__("mathutils").Matrix.Translation((-root[0], -root[1], -zmin)))
        j.location = (0, 0, 0)
        nodes.append(j)
        log(f"RESULT {j.name} tris={sum(len(p.vertices) - 2 for p in j.data.polygons)} size={tuple(round(v, 2) for v in j.dimensions)}")
    # LOD3 (~3k): from LOD2, keep 45 % of the leaf cards (scaled up 1.35x round their centre), bark decimated
    import bmesh

    rng = np.random.default_rng(5)
    l3 = nodes[2].copy()
    l3.data = nodes[2].data.copy()
    bpy.context.scene.collection.objects.link(l3)
    bm = bmesh.new()
    bm.from_mesh(l3.data)
    leaf_mi = [i for i, m in enumerate(l3.data.materials) if m.name.endswith("leaves")][0]
    seen, drop = set(), []
    for f in bm.faces:
        if f.index in seen or f.material_index != leaf_mi:
            continue
        isl, st = [], [f]
        while st:
            x = st.pop()
            if x.index in seen:
                continue
            seen.add(x.index)
            isl.append(x)
            st.extend(g for e in x.edges for g in e.link_faces if g.index not in seen)
        if rng.random() > 0.45:
            drop.extend(isl)
        else:
            vs = {v for q in isl for v in q.verts}
            c = sum((v.co for v in vs), Vector()) / len(vs)
            for v in vs:
                v.co = c + (v.co - c) * 1.35
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    bark_faces = [f for f in bm.faces if f.material_index != leaf_mi]
    bm.to_mesh(l3.data)
    bm.free()
    nb = len(bark_faces)
    dec = l3.modifiers.new("dec", "DECIMATE")
    dec.ratio = 1.0
    vg = l3.vertex_groups.new(name="bark")
    vg.add([v.index for p in l3.data.polygons if p.material_index != leaf_mi for v in [l3.data.vertices[i] for i in p.vertices]], 1.0, "REPLACE")
    dec.vertex_group = "bark"
    dec.ratio = min(1.0, 900 / max(nb, 1))
    bpy.ops.object.select_all(action="DESELECT")
    l3.select_set(True)
    bpy.context.view_layer.objects.active = l3
    bpy.ops.object.modifier_apply(modifier="dec")
    l3.vertex_groups.remove(l3.vertex_groups["bark"])
    l3.name = l3.data.name = f"downy_birch_{vk}_LOD3"
    nodes.append(l3)
    log(f"RESULT {l3.name} tris={sum(len(p.vertices) - 2 for p in l3.data.polygons)}")
    bpy.ops.object.select_all(action="DESELECT")
    for n in nodes:
        n.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"downy_birch_{vk}.glb"), use_selection=True, export_format="GLB",
                              export_image_format="AUTO", export_tangents=True, export_vertex_color="ACTIVE",
                              export_all_vertex_colors=True)
    log("exported", vk)
