"""Procedural Norwegian village pieces (CC0, our own): skigard fence segment and hjell (stockfish drying rack).

skigard_4m.glb : 4.0 m segment along +X, post pairs every 1.0 m (bark poles, 1.55 m), split rails of weathered
                 grey spruce leaning ~32 deg, spaced 0.24 m, tied to the posts with withy rings. Tiles end to end.
hjell_6m.glb   : 6 m section along +X of tall pole A-frames (3.6 m) with three ridge poles a side, stockfish
                 hung in tied pairs over the poles.
Each with LOD0 / LOD1 (LOD1: 6-sided -> 4-sided poles, fewer fish). Materials use tiling 2K textures
(wood_weathered_*, pole_bark_*) and a 512 stockfish map; UV2-free, no transparency.
Run: wf_run.sh tools/assets/build_skigard_hjell.py <log>
"""
import math
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

OUT = (Path.home() / "MWM/projects/mwm-wayfarer/assets/incoming/village_props")
rng = np.random.default_rng(11)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, tex, uv_scale=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(OUT / f"{tex}_albedo.png"))
    nt.links.new(ta.outputs[0], b.inputs["Base Color"])
    if (OUT / f"{tex}_normal.png").exists():
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(str(OUT / f"{tex}_normal.png"))
        tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = bpy.data.images.load(str(OUT / f"{tex}_orm.png"))
    to.image.colorspace_settings.name = "Non-Color"
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], b.inputs["Roughness"])
    return m


M_WOOD = mat("wood_weathered", "wood_weathered")
M_BARK = mat("pole_bark", "pole_bark")
M_FISH = mat("stockfish", "stockfish")


def pole(bm, uv, mi, a, b, r0, r1, sides, flat=1.0, u_per_m=0.6):
    """Tapered pole from a to b; flat < 1 squashes it (split rail). UV: u round, v along length (tiling)."""
    a, b = Vector(a), Vector(b)
    ax = (b - a).normalized()
    ref = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    s1 = ax.cross(ref).normalized()
    s2 = ax.cross(s1).normalized()
    length = (b - a).length
    ring = []
    for end, r in ((a, r0), (b, r1)):
        vs = []
        for k in range(sides + 1):
            t = 2 * math.pi * k / sides
            p = end + s1 * math.cos(t) * r + s2 * math.sin(t) * r * flat
            vs.append(bm.verts.new(p))
        ring.append(vs)
    off = rng.random()
    for k in range(sides):
        f = bm.faces.new((ring[0][k], ring[0][k + 1], ring[1][k + 1], ring[1][k]))
        f.material_index = mi
        u0, u1 = k / sides * 0.35 + off, (k + 1) / sides * 0.35 + off
        for lp, (u, v) in zip(f.loops, ((u0, 0), (u1, 0), (u1, length * u_per_m), (u0, length * u_per_m))):
            lp[uv].uv = (u, v)
    for vs, rev in ((ring[0], True), (ring[1], False)):  # caps
        cap = vs[:-1][::-1] if rev else vs[:-1]
        f = bm.faces.new(cap)
        f.material_index = mi
        for lp in f.loops:
            lp[uv].uv = (0.5 + (lp.vert.co - (a if rev else b)).dot(s1) * 2, 0.5 + (lp.vert.co - (a if rev else b)).dot(s2) * 2)


def ring_tie(bm, uv, mi, c, axis, r, sides=6):
    """Withy tie: a thin flat band round the post pair."""
    pole(bm, uv, mi, c - axis * 0.02, c + axis * 0.02, r, r, sides, 1.0, 1.0)


def finish(bm, name):
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m_ in (M_WOOD, M_BARK, M_FISH):
        me.materials.append(m_)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def skigard(lod):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    sides = 6 if lod == 0 else 4
    for i in range(5):  # post pairs at x = 0..4
        x = i * 1.0
        for dy in (-0.07, 0.07):
            lean = rng.uniform(-0.02, 0.02)
            pole(bm, uv, 1, (x, dy, -0.25), (x + lean, dy * 0.85, 1.55), 0.045, 0.035, sides)
        if lod == 0:
            for z in (0.45, 1.05):
                ring_tie(bm, uv, 0, Vector((x, 0, z)), Vector((0, 0, 1)), 0.13, 6)
    # split rails: lean up towards +X, each spans ~2.6 m and rests in the post pairs
    ang = math.radians(32)
    run = 2.6 * math.cos(ang)
    rise = 2.6 * math.sin(ang)
    x0 = -run + 0.12
    while x0 < 4.0:
        a = Vector((x0, rng.uniform(-0.02, 0.02), 0.05))
        b = a + Vector((run, 0, rise))
        # clip to the segment so segments tile: keep the part with 0 <= x <= 4
        t0 = max(0.0, (0.0 - a.x) / run)
        t1 = min(1.0, (4.0 - a.x) / run)
        if t1 > t0 + 0.05:
            pa, pb = a.lerp(b, t0), a.lerp(b, t1)
            pole(bm, uv, 0, pa, pb, 0.05, 0.045, sides, 0.55)
        x0 += 0.24 if lod == 0 else 0.36
    return finish(bm, f"skigard_4m_LOD{lod}")


def stockfish(bm, uv, top, side, length=0.62):
    """One dried cod hanging head down from `top`: flattened tapered body, 2 x 6 quads."""
    secs = [(0.00, 0.012), (0.3, 0.065), (0.65, 0.04), (1.0, 0.05)]
    rings = []
    for t, w in secs:
        c = Vector(top) + Vector((0, side * 0.03, -t * length))
        rings.append([bm.verts.new(c + Vector((dx * w, side * dz * w * 0.25, 0))) for dx, dz in ((-1, 0), (0, 1), (1, 0), (0, -1))])
    for i in range(len(rings) - 1):
        for k in range(4):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % 4], rings[i + 1][(k + 1) % 4], rings[i + 1][k]))
            f.material_index = 2
            for lp, (u, v) in zip(f.loops, ((k / 4, secs[i][0]), ((k + 1) / 4, secs[i][0]), ((k + 1) / 4, secs[i + 1][0]), (k / 4, secs[i + 1][0]))):
                lp[uv].uv = (u, 1 - v)


def hjell(lod):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    sides = 6 if lod == 0 else 4
    for x in (0.0, 3.0, 6.0):  # A-frames
        for sy in (-1, 1):
            pole(bm, uv, 1, (x, sy * 1.1, -0.3), (x, sy * 0.15, 3.6), 0.07, 0.05, sides)
        pole(bm, uv, 1, (x, -0.9, 1.0), (x, 0.9, 1.0), 0.045, 0.04, sides)
    for sy in (-1, 1):
        for z in (1.9, 2.55, 3.15):
            y = sy * (1.1 - (z + 0.3) / 3.9 * 0.95)
            pole(bm, uv, 1, (-0.25, y, z), (6.25, y, z), 0.05, 0.045, sides)
            step = 0.22 if lod == 0 else 0.5
            x = 0.25
            while x < 5.8:
                if abs(x - 3.0) > 0.18:
                    for side in (-1, 1):  # a tied pair hangs either side of the pole
                        stockfish(bm, uv, (x + rng.uniform(-0.02, 0.02), y + side * 0.03, z - 0.03), side, rng.uniform(0.5, 0.7))
                x += step
    return finish(bm, f"hjell_6m_LOD{lod}")


for build, name in ((skigard, "skigard_4m"), (hjell, "hjell_6m")):
    objs = [build(0), build(1)]
    for o in objs:
        print(f"SH RESULT {o.name} tris={sum(len(p.vertices) - 2 for p in o.data.polygons)} size={tuple(round(v, 2) for v in o.dimensions)}")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), use_selection=True, export_format="GLB",
                              export_image_format="AUTO", export_tangents=True)
