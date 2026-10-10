"""Shared helpers for the MWM Wayfarer art drafts (Blender 4.5, run with `blender -b --factory-startup`).

Patterns follow Race Riders tools/art/rr_art.py + mock_world.py: Poly Haven CC0 scans as PBR, HDRI sky with a
matched sun, EEVEE without ray tracing, depth fog mixed in the compositor (Godot/Unity depth fog equivalent).
Blender metres, Z up.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "assets" / "_raw"
PH = RAW / "polyhaven"
BUILD = RAW / "build"
MOCK = ROOT / "docs" / "mockups"
FONTS = ROOT / "assets" / "fonts"
BUILD.mkdir(parents=True, exist_ok=True)


def srgb_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexc(h: str, a: float = 1.0) -> tuple:
    h = h.lstrip("#")
    return (*[srgb_lin(int(h[i : i + 2], 16) / 255) for i in (0, 2, 4)], a)


def reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def load_image(path, non_color=False):
    img = bpy.data.images.load(str(path), check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def ph_maps(name: str) -> dict:
    d = PH / "textures" / name
    out = {}
    for f in d.glob("*"):
        stem = f.stem.lower()
        for key in ("diffuse", "nor_gl", "rough", "arm", "ao", "displacement"):
            if f"_{key}_" in stem:
                out[key] = f
    return out


def tex_nodes(nt, name, vec_socket, box=False):
    """Albedo/normal/rough sockets of a Poly Haven texture set, sampled at vec_socket."""
    mp = ph_maps(name)
    out = {}

    def img(key, nc):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = load_image(mp[key], nc)
        if box:
            n.projection = "BOX"
            n.projection_blend = 0.3
        nt.links.new(vec_socket, n.inputs["Vector"])
        return n

    out["albedo"] = img("diffuse", False).outputs["Color"]
    out["normal"] = img("nor_gl", True).outputs["Color"]
    if "rough" in mp:
        out["rough"] = img("rough", True).outputs["Color"]
    else:
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(img("arm", True).outputs["Color"], sp.inputs["Color"])
        out["rough"] = sp.outputs["Green"]
    return out


def mapping(nt, scale, coords="UV", rot=0.0, src=None):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    s = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    mp.inputs["Scale"].default_value = s
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    nt.links.new(src if src is not None else tc.outputs[coords], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def mixc(nt, fac, a, b, blend="MIX"):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    m.blend_type = blend
    if isinstance(fac, (int, float)):
        m.inputs["Factor"].default_value = fac
    else:
        nt.links.new(fac, m.inputs["Factor"])
    for i, v in ((6, a), (7, b)):
        if isinstance(v, (tuple, list)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[2]


def mixf(nt, fac, a, b):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "FLOAT"
    if isinstance(fac, (int, float)):
        m.inputs["Factor"].default_value = fac
    else:
        nt.links.new(fac, m.inputs["Factor"])
    for i, v in ((2, a), (3, b)):
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def math_node(nt, op, a, b=None, clamp=False):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    m.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def maprange(nt, v, a, b, c=0.0, d=1.0, clamp=True):
    m = nt.nodes.new("ShaderNodeMapRange")
    m.clamp = clamp
    m.inputs["From Min"].default_value = a
    m.inputs["From Max"].default_value = b
    m.inputs["To Min"].default_value = c
    m.inputs["To Max"].default_value = d
    nt.links.new(v, m.inputs["Value"])
    return m.outputs["Result"]


def noise(nt, scale, vec=None, detail=4.0, rough=0.55):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    if vec is None:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        vec = tc.outputs["Object"]
    nt.links.new(vec, n.inputs["Vector"])
    return n.outputs["Fac"]


def tint(nt, col, rgb):
    return mixc(nt, 1.0, col, (*rgb, 1.0), blend="MULTIPLY")


def pbr(name, tex, scale=1.0, coords="UV", box=False, tint_rgb=None, nstrength=1.0, rough_add=0.0, hue=None):
    """Material from one Poly Haven set. coords 'Object' + box=True for meshes without good UVs."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = bsdf(m)
    vec = mapping(nt, scale, coords)
    T = tex_nodes(nt, tex, vec, box=box)
    col = T["albedo"]
    if hue is not None:
        hs = nt.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Hue"].default_value = hue[0]
        hs.inputs["Saturation"].default_value = hue[1]
        hs.inputs["Value"].default_value = hue[2]
        nt.links.new(col, hs.inputs["Color"])
        col = hs.outputs["Color"]
    if tint_rgb is not None:
        col = tint(nt, col, tint_rgb)
    nt.links.new(col, b.inputs["Base Color"])
    r = T["rough"]
    if rough_add:
        r = math_node(nt, "ADD", r, rough_add, clamp=True)
    nt.links.new(r, b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = nstrength
    nt.links.new(T["normal"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def flat_mat(name, rgba, rough=0.6, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = bsdf(m)
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        b.inputs["Emission Color"].default_value = emit
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


# ---------------------------------------------------------------- models (Poly Haven glTF)
_PROTO: dict[str, bpy.types.Collection] = {}


def lib_root():
    c = bpy.data.collections.get("_lib")
    if c is None:
        c = bpy.data.collections.new("_lib")
        bpy.context.scene.collection.children.link(c)
        bpy.context.view_layer.layer_collection.children["_lib"].exclude = True
    return c


def proto(name: str, sub: str | None = None, tint_rgb=None, hue=None) -> bpy.types.Collection:
    """Import a Poly Haven model once into a hidden collection; returns the collection for instancing.
    sub: keep only mesh objects whose name contains `sub` (for sets like rock_moss_set_01)."""
    key = f"{name}:{sub}:{tint_rgb}:{hue}"
    if key in _PROTO:
        return _PROTO[key]
    d = PH / "models" / name
    gl = next(d.glob("*.gltf"))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(gl))
    new = [o for o in bpy.data.objects if o not in before]
    c = bpy.data.collections.new(key)
    lib_root().children.link(c)
    for o in new:
        for uc in list(o.users_collection):
            uc.objects.unlink(o)
        keep = o.type == "MESH" and (sub is None or sub in o.name)
        if keep:
            c.objects.link(o)
        else:
            if o.type != "MESH":
                continue
            bpy.data.objects.remove(o)
    # flatten parents and centre on the ground at the origin
    objs = list(c.objects)
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    if sub is not None and objs:
        lo = Vector((min(min((o.matrix_world @ Vector(b)).x for b in o.bound_box) for o in objs),
                     min(min((o.matrix_world @ Vector(b)).y for b in o.bound_box) for o in objs),
                     min(min((o.matrix_world @ Vector(b)).z for b in o.bound_box) for o in objs)))
        hi = Vector((max(max((o.matrix_world @ Vector(b)).x for b in o.bound_box) for o in objs),
                     max(max((o.matrix_world @ Vector(b)).y for b in o.bound_box) for o in objs),
                     0))
        off = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        for o in objs:
            o.location -= off
    if tint_rgb is not None or hue is not None:
        done = set()
        for o in objs:
            for s in o.material_slots:
                mt = s.material
                if mt is None or mt.name in done:
                    continue
                done.add(mt.name)
                nt = mt.node_tree
                b = bsdf(mt)
                if not b.inputs["Base Color"].is_linked:
                    continue
                src = b.inputs["Base Color"].links[0].from_socket
                if hue is not None:
                    hs = nt.nodes.new("ShaderNodeHueSaturation")
                    hs.inputs["Hue"].default_value = hue[0]
                    hs.inputs["Saturation"].default_value = hue[1]
                    hs.inputs["Value"].default_value = hue[2]
                    nt.links.new(src, hs.inputs["Color"])
                    src = hs.outputs["Color"]
                if tint_rgb is not None:
                    src = tint(nt, src, tint_rgb)
                nt.links.new(src, b.inputs["Base Color"])
    _PROTO[key] = c
    return c


def proto_variants(name, decimate=None):
    """One collection per mesh of a multi-variant Poly Haven model (e.g. fir_tree_01 has 3 trees), optionally
    decimated (LOD for distant instances)."""
    key = f"{name}:variants:{decimate}"
    if key in _PROTO:
        return _PROTO[key]
    base = proto(name)
    out = []
    for i, src in enumerate(sorted(base.objects, key=lambda o: o.name)):
        o = src.copy()
        if decimate:
            o.data = src.data.copy()
        c = bpy.data.collections.new(f"{name}_v{i}_{decimate}")
        lib_root().children.link(c)
        c.objects.link(o)
        lo, hi = bounds([o])
        o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        if decimate:
            d = o.modifiers.new("dec", "DECIMATE")
            d.ratio = decimate
        out.append(c)
    _PROTO[key] = out
    return out


def bounds(objs):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def proto_size(c):
    lo, hi = bounds(c.objects)
    return hi - lo


def inst(c, loc, yaw=0.0, scale=1.0, tilt=(0.0, 0.0), name=None):
    e = bpy.data.objects.new(name or c.name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = c
    e.location = loc
    e.rotation_euler = (tilt[0], tilt[1], yaw)
    e.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale
    link(e)
    return e


# ---------------------------------------------------------------- terrain
def grid_mesh(name, fn, x0, x1, y0, y1, nx, ny, mat=None):
    """Heightfield z = fn(x, y) on a regular grid; UV = world metres."""
    verts, faces, uvs = [], [], []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            verts.append((x, y, fn(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        p.use_smooth = True
        for li in p.loop_indices:
            v = verts[me.loops[li].vertex_index]
            uvl.data[li].uv = (v[0], v[1])
    o = link(bpy.data.objects.new(name, me))
    if mat:
        o.data.materials.append(mat)
    return o


def terrain_mat(name, layers, slope=(0.55, 0.8), height=None, macro=0.012, macro_amp=(0.78, 1.15), extra=None, box_all=False):
    """Slope/height blended terrain: layers = dict(flat=(tex, tile, tint), steep=(tex, tile, tint),
    high=(tex, tile, tint) optional). Godot/Unity: one splat shader, slope from the normal, triplanar steep layer.
    slope: (start, end) of normal.z where the flat layer takes over from the steep one."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = bsdf(m)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sepn = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sepn.inputs["Vector"])
    sepp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sepp.inputs["Vector"])
    nz = noise(nt, 0.08, tc.outputs["Object"], detail=3)
    # break the slope line with noise
    nzs = math_node(nt, "ADD", sepn.outputs["Z"], math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", nz, 0.5), 0.35))
    flatw = maprange(nt, nzs, slope[0], slope[1])
    L = {}
    for key, (tex, tile, tnt) in layers.items():
        box = box_all or key == "steep"
        vec = mapping(nt, 1.0 / tile, "Object" if box else "UV", src=tc.outputs["Object"] if box else None)
        T = tex_nodes(nt, tex, vec, box=box)
        if tnt is not None:
            T["albedo"] = tint(nt, T["albedo"], tnt)
        L[key] = T
    col = mixc(nt, flatw, L["steep"]["albedo"], L["flat"]["albedo"])
    rough = mixf(nt, flatw, L["steep"]["rough"], L["flat"]["rough"])
    nrm = mixc(nt, flatw, L["steep"]["normal"], L["flat"]["normal"])
    if "high" in L and height is not None:
        hw = maprange(nt, math_node(nt, "ADD", sepp.outputs["Z"], math_node(nt, "MULTIPLY", nz, 6.0)), height[0], height[1])
        hw = math_node(nt, "MULTIPLY", hw, flatw)
        col = mixc(nt, hw, col, L["high"]["albedo"])
        rough = mixf(nt, hw, rough, L["high"]["rough"])
        nrm = mixc(nt, hw, nrm, L["high"]["normal"])
    if "low" in L and extra is not None:  # shore band (beach) by height
        lw = maprange(nt, math_node(nt, "ADD", sepp.outputs["Z"], math_node(nt, "MULTIPLY", nz, extra[2])), extra[1], extra[0])
        col = mixc(nt, lw, col, L["low"]["albedo"])
        rough = mixf(nt, lw, rough, L["low"]["rough"])
        nrm = mixc(nt, lw, nrm, L["low"]["normal"])
    # macro variation against tiling
    mac = noise(nt, macro, tc.outputs["Object"], detail=2)
    macv = maprange(nt, mac, 0.3, 0.7, macro_amp[0], macro_amp[1])
    col = mixc(nt, 1.0, col, macv, blend="MULTIPLY") if False else math_col_mul(nt, col, macv)
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(rough, b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm, nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def math_col_mul(nt, col, f):
    v = nt.nodes.new("ShaderNodeVectorMath")
    v.operation = "SCALE"
    nt.links.new(col, v.inputs[0])
    nt.links.new(f, v.inputs["Scale"])
    return v.outputs[0]


def water_mat(name, deep, shallow, rough=0.03, wave_scale=0.6, wave_strength=0.25, depth_obj=None, foam=None):
    """Water: dark reflective surface, colour from a deep/shallow blend fed by a fresnel-ish term.
    Godot/Unity: one water shader, scrolling normal maps, screen depth for the shallow tint."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    col = mixc(nt, lw.outputs["Facing"], shallow, deep)
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.5
    b.inputs["IOR"].default_value = 1.33
    w1 = nt.nodes.new("ShaderNodeTexWave")
    w1.wave_type = "BANDS"
    w1.bands_direction = "DIAGONAL"
    w1.inputs["Scale"].default_value = wave_scale
    w1.inputs["Distortion"].default_value = 8.0
    w1.inputs["Detail"].default_value = 3.0
    mpv = mapping(nt, (1.0, 2.5, 1.0), "Object")
    nt.links.new(mpv, w1.inputs["Vector"])
    n2 = noise(nt, wave_scale * 6, tc.outputs["Object"], detail=6, rough=0.6)
    h = math_node(nt, "ADD", math_node(nt, "MULTIPLY", w1.outputs["Fac"], 0.6), n2)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = wave_strength
    bump.inputs["Distance"].default_value = 0.2
    nt.links.new(h, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


# ---------------------------------------------------------------- world, light, render
def world_hdri(hdri: str, rot_deg: float, strength=1.0, sky_tint=None, sky_strength=None):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("sky")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(PH / "hdri" / hdri))
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot_deg))
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = strength
    col = env.outputs["Color"]
    if sky_tint is not None:
        col = mixc(nt, 1.0, col, (*sky_tint, 1), blend="MULTIPLY")
    nt.links.new(col, bg.inputs["Color"])
    return w, nt, env


def sun(elev_deg, azim_deg, color=(1.0, 0.92, 0.8), energy=4.0, angle=1.0):
    """azim: direction the light comes FROM, degrees from +Y towards +X."""
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy = energy
    ld.color = color
    ld.angle = math.radians(angle)
    o = link(bpy.data.objects.new("sun", ld))
    e = math.radians(elev_deg)
    a = math.radians(azim_deg)
    d = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))  # towards the sun
    o.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    for attr, v in (("use_shadow", True), ("shadow_maximum_resolution", 0.001), ("use_contact_shadow", True)):
        if hasattr(ld, attr):
            try:
                setattr(ld, attr, v)
            except Exception:  # noqa: BLE001
                pass
    return o


def eevee(samples=64, res=(1920, 1080), exposure=0.0, look="AgX - Medium High Contrast", raytrace=False):
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE"
    ee = sc.eevee
    ee.taa_render_samples = samples
    for attr, val in (
        ("use_raytracing", True),
        ("ray_tracing_method", "PROBE"),
        ("use_shadows", True),
        ("shadow_ray_count", 2),
        ("shadow_step_count", 10),
        ("use_gtao", True),
        ("gtao_distance", 1.0),
        ("use_volumetric_shadows", True),
        ("volumetric_tile_size", "8"),
        ("volumetric_end", 3000.0),
        ("volumetric_samples", 64),
        ("clamp_surface_indirect", 10.0),
        ("fast_gi_method", "GLOBAL_ILLUMINATION"),
        ("use_fast_gi", True),
    ):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, val)
            except Exception:  # noqa: BLE001
                pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = look
    except TypeError:
        pass
    sc.view_settings.exposure = exposure
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"


def camera(loc, target, lens=32.0, sensor=36.0, clip_end=25000.0, dof=None):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.1
    cd.clip_end = clip_end
    if dof is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = dof[0]
        cd.dof.aperture_fstop = dof[1]
    o = link(bpy.data.objects.new("cam", cd))
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return o


def compositor_fog(fog_rgb, start, depth, fog_max, sky_haze=0.1, glare=False, vignette=0.0, haze_power=1.0):
    """Depth fog on geometry (mist pass, quadratic), sky gets a light horizon haze. Mirrors the Race Riders mock."""
    sc = bpy.context.scene
    w = sc.world
    w.mist_settings.start = start
    w.mist_settings.depth = depth
    w.mist_settings.falloff = "QUADRATIC" if haze_power != 1.0 else "LINEAR"
    sc.render.film_transparent = True
    vl = sc.view_layers[0]
    vl.use_pass_mist = True
    vl.use_pass_environment = True
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new("CompositorNodeRLayers")
    mul = nt.nodes.new("CompositorNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = fog_max
    nt.links.new(rl.outputs["Mist"], mul.inputs[0])
    mix = nt.nodes.new("CompositorNodeMixRGB")
    mix.inputs[2].default_value = (*fog_rgb, 1)
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(rl.outputs["Image"], mix.inputs[1])
    sa = nt.nodes.new("CompositorNodeSetAlpha")
    nt.links.new(mix.outputs[0], sa.inputs["Image"])
    nt.links.new(rl.outputs["Alpha"], sa.inputs["Alpha"])
    env = nt.nodes.new("CompositorNodeMixRGB")
    env.inputs[0].default_value = sky_haze
    env.inputs[2].default_value = (*fog_rgb, 1)
    nt.links.new(rl.outputs["Env"], env.inputs[1])
    ao = nt.nodes.new("CompositorNodeAlphaOver")
    nt.links.new(env.outputs[0], ao.inputs[1])
    nt.links.new(sa.outputs[0], ao.inputs[2])
    last = ao.outputs[0]
    if glare:
        g = nt.nodes.new("CompositorNodeGlare")
        g.glare_type = "FOG_GLOW" if hasattr(g, "glare_type") else g.glare_type
        try:
            g.quality = "HIGH"
            g.threshold = 1.0
            g.mix = -0.85
            g.size = 8
        except Exception:  # noqa: BLE001
            pass
        nt.links.new(last, g.inputs["Image"])
        last = g.outputs["Image"]
    if vignette > 0:
        el = nt.nodes.new("CompositorNodeEllipseMask")
        el.width = 1.25
        el.height = 1.3
        bl = nt.nodes.new("CompositorNodeBlur")
        bl.size_x = 400
        bl.size_y = 400
        bl.filter_type = "GAUSS"
        nt.links.new(el.outputs["Mask"], bl.inputs["Image"])
        vm = nt.nodes.new("CompositorNodeMixRGB")
        vm.blend_type = "MULTIPLY"
        inv = nt.nodes.new("CompositorNodeMath")
        inv.operation = "MULTIPLY_ADD"
        nt.links.new(bl.outputs["Image"], inv.inputs[0])
        inv.inputs[1].default_value = vignette
        inv.inputs[2].default_value = 1.0 - vignette
        vm.inputs[0].default_value = 1.0
        nt.links.new(last, vm.inputs[1])
        nt.links.new(inv.outputs[0], vm.inputs[2])
        last = vm.outputs[0]
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(last, comp.inputs["Image"])
    return nt


def render(out_path, save_blend=None):
    import time

    sc = bpy.context.scene
    sc.render.filepath = str(out_path)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    print(f"RENDER {out_path} {dt:.1f}s")
    if save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(save_blend))
    return dt


def rng(seed):
    return random.Random(seed)


def look_at_rot(src, dst):
    return (Vector(dst) - Vector(src)).to_track_quat("Y", "Z").to_euler()


def scatter(c, n, sample_fn, seed, scale=(0.8, 1.2), yaw=True, tilt=0.0):
    r = rng(seed)
    out = []
    for _ in range(n):
        p = sample_fn(r)
        if p is None:
            continue
        out.append(
            inst(
                c,
                p,
                yaw=r.uniform(0, math.tau) if yaw else 0.0,
                scale=r.uniform(*scale),
                tilt=(r.uniform(-tilt, tilt), r.uniform(-tilt, tilt)),
            )
        )
    return out


def mat_rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


# ---------------------------------------------------------------- impostor cards (distant trees)
def impostor(c, res=512, name=None, hdri="qwantani_dusk_2_puresky_4k.hdr", sun_dir=(0.4, -0.6, 0.7), tint=(1, 1, 1)):
    """Render a prototype collection from the side (orthographic, transparent) and return a collection with a
    crossed-quad card using that image (alpha clip). The phone approach for anything past ~60 m.
    Race Riders tree_pine_*.glb are made the same way."""
    name = name or f"imp_{c.name}"
    if name in _PROTO:
        return _PROTO[name]
    lo, hi = bounds(c.objects)
    size = hi - lo
    wdt = max(size.x, size.y)
    sc0 = bpy.context.scene
    sc = bpy.data.scenes.new(name)
    sc.collection.children.link(c)
    w = bpy.data.worlds.new(name)
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16
    sc.render.film_transparent = True
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * size.z / wdt)
    sc.view_settings.view_transform = "Standard"
    ld = bpy.data.lights.new(name + "_sun", "SUN")
    ld.energy = 3.0
    lo_ = bpy.data.objects.new(name + "_sun", ld)
    sc.collection.objects.link(lo_)
    lo_.rotation_euler = (-Vector(sun_dir)).to_track_quat("-Z", "Y").to_euler()
    cd = bpy.data.cameras.new(name + "_cam")
    cd.type = "ORTHO"
    cd.ortho_scale = max(wdt, size.z)
    co = bpy.data.objects.new(name + "_cam", cd)
    sc.collection.objects.link(co)
    cz = (lo.z + hi.z) / 2
    co.location = ((lo.x + hi.x) / 2, lo.y - 100, cz)
    co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co
    path = BUILD / f"{name}.png"
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True, scene=sc.name)
    sc.collection.children.unlink(c)
    bpy.data.scenes.remove(sc)
    # card material
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = bsdf(m)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(str(path))
    col = tint_socket = t.outputs["Color"]
    if tint != (1, 1, 1):
        col = mixc(nt, 1.0, tint_socket, (*tint, 1), blend="MULTIPLY")
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.85
    m.surface_render_method = "BLENDED"
    try:
        m.use_backface_culling = False
    except Exception:  # noqa: BLE001
        pass
    hw = wdt / 2
    verts = [(-hw, 0, 0), (hw, 0, 0), (hw, 0, size.z), (-hw, 0, size.z), (0, -hw, 0), (0, hw, 0), (0, hw, size.z), (0, -hw, size.z)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)] * 2
    for p in me.polygons:
        for k, li in enumerate(p.loop_indices):
            uvl.data[li].uv = uv[k]
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    cc = bpy.data.collections.new(name)
    lib_root().children.link(cc)
    cc.objects.link(o)
    _PROTO[name] = cc
    return cc


def world_fog(density=0.0004, color=(0.6, 0.66, 0.75), anisotropy=0.6, end=6000.0):
    """Height-less volumetric haze in the world (EEVEE volumetrics; alpha-correct on cards).
    Godot: Environment volumetric fog or plain depth fog on Mobile."""
    sc = bpy.context.scene
    w = sc.world
    nt = w.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (*color, 1)
    pv.inputs["Density"].default_value = density
    pv.inputs["Anisotropy"].default_value = anisotropy
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    ee = sc.eevee
    for attr, val in (("volumetric_end", end), ("volumetric_start", 1.0), ("volumetric_tile_size", "8"), ("volumetric_samples", 96), ("volumetric_sample_distribution", 0.95), ("use_volumetric_shadows", True)):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, val)
            except Exception:  # noqa: BLE001
                pass


def fog_box(center, size, density=0.0002, color=(0.6, 0.66, 0.75), anisotropy=0.5, end=9000.0, falloff_top=None):
    """Finite haze volume (a box), no volumetric shadows, so the low sun is not eaten by the fog.
    falloff_top: (z0, z1) density fades out between these heights (ground haze)."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
    o = bpy.context.active_object
    o.name = "fog"
    o.scale = size
    m = bpy.data.materials.new("fog")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (*color, 1)
    pv.inputs["Anisotropy"].default_value = anisotropy
    if falloff_top is None:
        pv.inputs["Density"].default_value = density
    else:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
        f = maprange(nt, sep.outputs["Z"], falloff_top[0], falloff_top[1], density, density * 0.15)
        nt.links.new(f, pv.inputs["Density"])
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    o.visible_shadow = False
    ee = bpy.context.scene.eevee
    for attr, val in (("volumetric_end", end), ("volumetric_start", 0.5), ("volumetric_tile_size", "16"), ("volumetric_samples", 48), ("volumetric_sample_distribution", 0.95), ("use_volumetric_shadows", False)):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, val)
            except Exception:  # noqa: BLE001
                pass
    return o
