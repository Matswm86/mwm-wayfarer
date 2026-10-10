"""Export the look-dev village (tools/art/wf_build.py: turf-roof timber houses, boathouses, boats,
Poly Haven pier) to GLB for the Godot spike, with baked ambient occlusion.

Run (about 3-6 min, GPU Cycles bake):
  BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user blender -b --factory-startup \
      -P tools/spike/export_village.py
then: python3 tools/spike/village_textures.py   (copies and resizes the tiling textures)

Output in assets/models/village/:
  village.glb        all houses, boathouses and boats as one mesh, one surface per texture set.
                     Godot frame: the glTF exporter turns Blender (x, -z, y) into Godot (x, y, z), so
                     each house is built at its terrain.json position and needs no transform in Godot.
                     UV1 = world metres (tiling textures), UV2 = AO atlas, COLOR_0 = linear tint.
  village_ao.png     2048 px ambient occlusion on UV2 (Cycles, ground planes as occluders).
  pier.glb           the Poly Haven modular_wooden_pier (CC0), decimated, two sections along the jetty.
  materials.json     per surface: Poly Haven set, UV scale (repeats per metre), saturation, roughness.

Reads tools/art/ (owned by the art pipeline) and never writes there.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "art"))
import wf_art as A  # noqa: E402
import wf_build as B  # noqa: E402

OUT = ROOT / "assets" / "models" / "village"
OUT.mkdir(parents=True, exist_ok=True)
META = json.loads((ROOT / "assets" / "terrain" / "terrain.json").read_text())
WALLS = ["red", "ochre", "white", "tar"]
AO_SIZE = 2048


def g2b(p) -> tuple[float, float, float]:
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    return (float(p[0]), -float(p[2]), float(p[1]))


def build() -> list[bpy.types.Object]:
    roots = []
    houses = META["village"]
    main = [h for h in houses if not (h["wall"] == 3 and h["w"] == 5.0 and h["d"] == 9.0)]
    naust = [h for h in houses if h not in main]
    for i, h in enumerate(main):
        root, _ = B.nordic_house(
            g2b(h["pos"]),
            math.radians(h["yaw"]),
            w=h["w"],
            d=h["d"],
            h=2.8 + 0.4 * (i % 2),
            wall=WALLS[h["wall"]],
            lit=0.0,
            seed=i,
        )
        roots.append(root)
    for i, h in enumerate(naust):
        p = list(h["pos"])
        p[1] = max(0.2, p[1]) - 0.1
        root, _ = B.nordic_house(
            g2b(p),
            math.radians(h["yaw"]),
            w=5.0,
            d=9.0,
            h=2.4,
            pitch=32,
            wall="tar",
            lit=0.0,
            seed=20 + i,
            chimney=False,
        )
        roots.append(root)
    # boats along the jetty (scene_fjord.py layout, jetty runs along Godot -x)
    j = META["jetty"]
    jx, jz = float(j["from"][0]), float(j["from"][2])
    boats = [
        (-10, 3.0, 4, "#E9E4DA", False),
        (-18, -3.2, -6, "#2F5A4A", True),
        (-26, 3.4, 2, "#8E2B22", False),
    ]
    for i, (dx, dz, yaw, col, cab) in enumerate(boats):
        root = B.boat(
            g2b((jx + dx + 6.0, -0.28, jz - dz)),
            math.radians(90 + yaw),
            L=6.5 if not cab else 8.0,
            B=2.0 if not cab else 2.5,
            color=col,
            seed=i,
            cabin=cab,
        )
        root.location.z = -0.28
        roots.append(root)
    return roots


def material_info(m: bpy.types.Material) -> dict:
    """Poly Haven set, UV scale, tint, saturation and roughness of a wf_art material."""
    info = {
        "set": "flat",
        "uv_scale": 1.0,
        "tint": [1.0, 1.0, 1.0],
        "sat": 1.0,
        "value": 1.0,
        "rough": 0.7,
    }
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == "TEX_IMAGE" and n.image and "_diffuse_" in n.image.name:
            info["set"] = Path(n.image.filepath).parent.name
        if n.type == "MAPPING":
            info["uv_scale"] = float(n.inputs["Scale"].default_value[0])
        mul = n.type == "MIX" and n.blend_type == "MULTIPLY" and n.data_type == "RGBA"
        if mul and not n.inputs[7].is_linked:
            info["tint"] = list(n.inputs[7].default_value[:3])
        if n.type == "HUE_SAT":
            info["sat"] = float(n.inputs["Saturation"].default_value)
            info["value"] = float(n.inputs["Value"].default_value)
    b = A.bsdf(m)
    if info["set"] == "flat":
        info["tint"] = list(b.inputs["Base Color"].default_value[:3])
        info["rough"] = float(b.inputs["Roughness"].default_value)
    return info


def key_of(info: dict) -> str:
    if info["set"] == "flat":
        return "glass" if info["rough"] < 0.2 else "paint"
    # one surface per texture set (fewer draw calls); the tint lives in the vertex colour and the
    # set's albedo is desaturated once to the lowest saturation any material asked for
    return info["set"]


def bake_ready_mesh(roots: list[bpy.types.Object]) -> tuple[bpy.types.Object, dict]:
    """Apply modifiers, write tints to a colour attribute, join, map materials to texture-set slots."""
    meshes = [o for r in roots for o in r.children_recursive if o.type == "MESH"]
    dg = bpy.context.evaluated_depsgraph_get()
    mats: dict[str, dict] = {}
    slot_mats: dict[str, bpy.types.Material] = {}
    parts = []
    for o in meshes:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        col = me.color_attributes.new("tint", "FLOAT_COLOR", "CORNER")
        new_slots = []
        for mi, m in enumerate(me.materials):
            info = material_info(m)
            k = key_of(info)
            prev = mats.setdefault(k, {**info, "uv_scales": []})
            prev["uv_scales"].append(info["uv_scale"])
            prev["sat"] = min(prev["sat"], info["sat"])
            if k not in slot_mats:
                slot_mats[k] = bpy.data.materials.new(k)
            new_slots.append((mi, k, info))
        for p in me.polygons:
            _, k, info = new_slots[p.material_index] if new_slots else (0, "paint", None)
            t = info["tint"] if info else [1, 1, 1]
            v = info["value"] if info else 1.0
            for li in p.loop_indices:
                col.data[li].color = (t[0] * v, t[1] * v, t[2] * v, 1.0)
        keys = [k for _, k, _ in new_slots]
        me.materials.clear()
        for k in keys:
            me.materials.append(slot_mats[k])
        ob = bpy.data.objects.new(o.name + "_baked", me)
        A.link(ob)
        parts.append(ob)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in parts:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    village = bpy.context.active_object
    village.name = "village"
    # merge duplicate material slots
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.material_slot_remove_unused()
    for v in mats.values():
        v.pop("uv_scales")
    return village, mats


def dedupe_slots(ob: bpy.types.Object) -> None:
    names: dict[str, int] = {}
    remap = {}
    for i, s in enumerate(ob.material_slots):
        n = s.material.name.split(".")[0]
        if n in names:
            remap[i] = names[n]
        else:
            names[n] = i
    for p in ob.data.polygons:
        if p.material_index in remap:
            p.material_index = remap[p.material_index]
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.material_slot_remove_unused()


def bake_ao(village: bpy.types.Object) -> None:
    me = village.data
    uv2 = me.uv_layers.new(name="UV2")
    me.uv_layers.active = uv2
    bpy.ops.object.select_all(action="DESELECT")
    village.select_set(True)
    bpy.context.view_layer.objects.active = village
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.uv.pack_islands(margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")

    # ground occluders under every house and boat (deleted after the bake)
    occ = []
    for h in META["village"]:
        x, y, z = g2b(h["pos"])
        bpy.ops.mesh.primitive_plane_add(size=40.0, location=(x, y, z - 0.05))
        occ.append(bpy.context.active_object)

    img = bpy.data.images.new("village_ao", AO_SIZE, AO_SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color"
    for s in village.material_slots:
        m = s.material
        m.use_nodes = True
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = img
        m.node_tree.nodes.active = n
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
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
    except KeyError:
        pass
    sc.cycles.samples = 96
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.light_settings.distance = 6.0
    bpy.ops.object.select_all(action="DESELECT")
    village.select_set(True)
    bpy.context.view_layer.objects.active = village
    sc.render.bake.margin = 6
    bpy.ops.object.bake(type="AO", uv_layer="UV2")
    img.filepath_raw = str(OUT / "village_ao.png")
    img.file_format = "PNG"
    img.save()
    for o in occ:
        bpy.data.objects.remove(o, do_unlink=True)
    me.uv_layers.active = me.uv_layers[0]
    for s in village.material_slots:
        nt = s.material.node_tree
        for n in list(nt.nodes):
            if n.type == "TEX_IMAGE":
                nt.nodes.remove(n)
    print("AO baked", img.size[:])


def export_glb(objs: list[bpy.types.Object], path: Path) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_vertex_color="ACTIVE",
        export_all_vertex_colors=False,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_yup=True,
    )
    print("wrote", path, path.stat().st_size)


def pier() -> None:
    proto = A.proto("modular_wooden_pier")
    j = META["jetty"]
    a = g2b(j["from"])
    objs = []
    for k, dx in enumerate((-6.0, -22.0)):
        for src in proto.objects:
            o = src.copy()
            o.data = src.data.copy()
            A.link(o)
            o.matrix_world = src.matrix_world.copy()
            o.rotation_euler.z += math.radians(90)
            o.location = (a[0] + dx + o.location.x, a[1] + o.location.y, -0.6 + o.location.z)
            dec = o.modifiers.new("dec", "DECIMATE")
            dec.ratio = 0.3
            objs.append(o)
    bpy.context.view_layer.update()
    export_glb(objs, OUT / "pier.glb")


def main() -> None:
    A.reset()
    roots = build()
    # phone LOD0: turf roofs at subdivision 3 instead of the render's 5 (16x fewer triangles,
    # the 12 cm turf bumps still read); Godot generates the further LODs on import
    for r in roots:
        for o in r.children_recursive:
            for md in o.modifiers:
                if md.type == "SUBSURF":
                    md.levels = min(md.levels, 3)
    village, mats = bake_ready_mesh(roots)
    dedupe_slots(village)
    tris = sum(len(p.vertices) - 2 for p in village.data.polygons)
    print("village triangles", tris, "slots", [s.material.name for s in village.material_slots])
    bake_ao(village)
    village.data.color_attributes.active_color = village.data.color_attributes["tint"]
    export_glb([village], OUT / "village.glb")
    used = {s.material.name.split(".")[0] for s in village.material_slots}
    (OUT / "materials.json").write_text(
        json.dumps({k: v for k, v in mats.items() if k in used}, indent=1)
    )
    bpy.ops.object.select_all(action="DESELECT")
    for r in roots:
        for o in [r, *r.children_recursive]:
            bpy.data.objects.remove(o, do_unlink=True)
    pier()


main()
