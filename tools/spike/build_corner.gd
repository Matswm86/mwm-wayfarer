extends SceneTree

## Builds the beauty corner (pass 3): scenes/BeautyCorner.tscn and its meshes, ready for the
## lightmap bake (tools/spike/bake_corner.sh). Run headless from the project dir:
##   godot --headless --audio-driver Dummy -s res://tools/spike/build_corner.gd
##
## The corner = 4 x 4 finest terrain tiles (160 m) round the spawn, Skarvik village, the shore and
## the cliff foot east of the houses. Contents:
## - Ground: real meshes of those tiles from the 2.5 m heights (same heights as the shader tiles,
##   which Terrain.gd skips there), terrain_corner.gdshader, lightmap UV2.
## - Mask (R path, G gravel yards, B shore pebbles, A wet sand) for the ground shader.
## - Houses: photogrammetry scans (tools/spike/export_corner_houses.py) on the village slots.
## - Props (designer's village_props), rocks on the shore, meadow and cliff foot (designer's
##   rocks), birches round the village (designer's downy_birch, dynamic, not baked).
## - Bake-only nodes the game removes: BakeSun (indirect light from the sun), Occluder (the
##   valley round the corner, so the lightmap knows how much sky the walls hide).
## - LightmapGI.
## Static meshes are copied to assets/models/corner/baked/*.res with a lightmap UV2
## (ArrayMesh.lightmap_unwrap); LOD1/LOD2 stay unbaked (probe-lit) beyond their range.

const SCENE := "res://scenes/BeautyCorner.tscn"
const OUT := "res://assets/terrain/corner/"
const BAKED := "res://assets/models/corner/baked/"
const MODELS := "res://assets/models/corner/"
## Finest-level tile indices of the corner (Terrain.skip_leaf uses the same rect).
const TILES := Rect2i(38, 55, 4, 4)
const LEAF := 160.0
const CELLS := 64
const MASK_PX := 1024
## Lightmap texels per metre: ground, houses, props and rocks.
const TEXEL_GROUND := 0.5
const TEXEL_HOUSE := 0.12
const TEXEL_PROP := 0.1
const TEXEL_ROCK := 0.2
## Shadow-only proxies (lightest LOD) cast the sun shadow out to this distance.
const SHADOW_RANGE := 260.0
## Village street: spawn -> houses -> jetty corner -> along the houses -> cliff path (x, z).
const PATH: Array[Vector2] = [
	Vector2(126, -25),
	Vector2(150, -52),
	Vector2(178, -82),
	Vector2(200, -108),
	Vector2(219, -132),
	Vector2(233, -158),
	Vector2(250, -178),
	Vector2(268, -192),
	Vector2(287, -212),
	Vector2(296, -232),
	Vector2(318, -256),
	Vector2(338, -282),
	Vector2(352, -310),
]
const SPUR: Array[Vector2] = [Vector2(233, -158), Vector2(228, -168), Vector2(224, -172)]

var terrain: Terrain
var rng := RandomNumberGenerator.new()
var corner: Node3D
var x0: float
var z0: float
var size: float
var houses: Array[Dictionary] = []
var _unwrap_cache := {}


func _init() -> void:
	rng.seed = 1880
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(BAKED))
	terrain = Terrain.new()
	terrain.load_data()
	var c: Dictionary = terrain.meta["coarse"]
	x0 = float(c["x0"]) + TILES.position.x * LEAF
	z0 = float(c["z0"]) + TILES.position.y * LEAF
	size = TILES.size.x * LEAF
	print("CORNER rect x %.0f..%.0f z %.0f..%.0f" % [x0, x0 + size, z0, z0 + size])
	corner = Node3D.new()
	corner.name = "BeautyCorner"
	_houses()
	_mask()
	_ground()
	if OS.get_environment("WF_CORNER_NO_OCCLUDER") != "1":
		_occluder()
	_props()
	_rocks()
	_trees()
	_lighting()
	_own(corner, corner)
	var ps := PackedScene.new()
	var err := ps.pack(corner)
	if err == OK:
		err = ResourceSaver.save(ps, SCENE)
	print("CORNER saved %s (%s)" % [SCENE, error_string(err)])
	terrain.free()
	corner.free()
	quit(0 if err == OK else 1)


func _own(n: Node, owner_node: Node) -> void:
	for ch in n.get_children():
		ch.owner = owner_node
		_own(ch, owner_node)


func _h(x: float, z: float) -> float:
	return terrain.height_at(x, z)


func _slope(x: float, z: float) -> float:
	var dx: float = _h(x + 1.5, z) - _h(x - 1.5, z)
	var dz: float = _h(x, z + 1.5) - _h(x, z - 1.5)
	return rad_to_deg(atan(Vector2(dx, dz).length() / 3.0))


func _normal(x: float, z: float) -> Vector3:
	var dx: float = _h(x + 2.0, z) - _h(x - 2.0, z)
	var dz: float = _h(x, z + 2.0) - _h(x, z - 2.0)
	return Vector3(-dx, 4.0, -dz).normalized()


# ---------------------------------------------------------------- houses (scans on the slots)


func _houses() -> void:
	var list: Array = terrain.meta["village"]
	var holder := Node3D.new()
	holder.name = "Houses"
	corner.add_child(holder)
	var meshes := {
		"cabin56": _scan_meshes("cabin56"),
		"evju": _scan_meshes("evju"),
	}
	var count := {"cabin56": 0, "evju": 0}
	for i in list.size():
		var h: Dictionary = list[i]
		var boathouse: bool = int(h["wall"]) == 3 and float(h["w"]) == 5.0 and float(h["d"]) == 9.0
		if boathouse:
			continue
		var kind: String = "cabin56" if float(h["d"]) >= 8.0 else "evju"
		var p: Array = h["pos"]
		var pos := Vector3(float(p[0]), 0.0, float(p[2]))
		var yaw: float = deg_to_rad(float(h["yaw"]))
		var basis := Basis(Vector3.UP, yaw)
		# sit the house on the lowest corner of its footprint, a little sunk
		var hw: float = 4.8 if kind == "cabin56" else 3.5
		var hd: float = 6.2 if kind == "cabin56" else 3.5
		var lo: float = INF
		for cx: float in [-hw, hw]:
			for cz: float in [-hd, hd]:
				var q: Vector3 = pos + basis * Vector3(cx, 0.0, cz)
				lo = minf(lo, _h(q.x, q.z))
		pos.y = maxf(lo - 0.15, 0.2)
		var n: int = int(count[kind])
		count[kind] = n + 1
		var scale := Vector3.ONE
		if n % 2 == 1:
			scale.x = -1.0  # mirrored copy: the same scan reads as a different house
		var node := Node3D.new()
		node.name = "%s_%d" % [kind, i]
		node.transform = Transform3D(basis.scaled(scale), pos)
		holder.add_child(node)
		_add_lods(node, meshes[kind], [45.0, 0.0], TEXEL_HOUSE, kind)
		houses.append({"pos": pos, "yaw": yaw, "kind": kind, "hw": hw, "hd": hd})
		print("CORNER house %s at %s yaw %.0f" % [kind, pos, float(h["yaw"])])


## LOD0 / LOD1 meshes of a scanned building with its scan albedo and baked normal map.
func _scan_meshes(kind: String) -> Array[Mesh]:
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = load(MODELS + kind + "_albedo.jpg")
	mat.normal_enabled = true
	mat.normal_texture = load(MODELS + kind + "_normal.png")
	mat.roughness = 0.88
	mat.metallic_specular = 0.3
	ResourceSaver.save(mat, BAKED + kind + "_mat.tres")
	mat = load(BAKED + kind + "_mat.tres")
	var src := _glb_meshes(MODELS + kind + ".glb")
	var out: Array[Mesh] = []
	for lod: String in ["LOD0", "LOD1"]:
		var m: ArrayMesh = (src[kind + "_" + lod] as ArrayMesh).duplicate()
		m.surface_set_material(0, mat)
		out.append(m)
	return out


## name -> mesh of every MeshInstance3D in an imported GLB.
func _glb_meshes(path: String) -> Dictionary:
	var inst := (load(path) as PackedScene).instantiate()
	var out := {}
	for mi: MeshInstance3D in inst.find_children("*", "MeshInstance3D", true, false):
		out[String(mi.name)] = mi.mesh
	inst.free()
	return out


## Adds LOD nodes under `parent`: lods[0] lightmap-unwrapped and baked, the rest probe-lit beyond
## the given ranges (ranges = visibility end of each LOD; 0 = none). None of them casts the sun
## shadow: a "Shadow" node draws the lightest LOD in the shadow maps only (out to SHADOW_RANGE), so
## a 70k-triangle scan costs 12k triangles per shadow split instead of 70k.
func _add_lods(
	parent: Node3D, lods: Array, ranges: Array, texel: float, key: String, shadow: bool = true
) -> void:
	var lightest: Mesh = null
	for k in lods.size():
		var mesh: Mesh = lods[k]
		if mesh == null:
			continue
		var mi := MeshInstance3D.new()
		mi.name = "LOD%d" % k
		if k == 0:
			mesh = _unwrapped(mesh, texel, key)
			mi.gi_mode = GeometryInstance3D.GI_MODE_STATIC
		else:
			mesh = _saved(mesh, "%s_LOD%d" % [key, k])
			mi.gi_mode = GeometryInstance3D.GI_MODE_DYNAMIC
		if k <= 1:
			lightest = mesh
		mi.mesh = mesh
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var end: float = float(ranges[k]) if k < ranges.size() else 0.0
		var begin: float = float(ranges[k - 1]) if k > 0 else 0.0
		mi.visibility_range_begin = begin
		mi.visibility_range_end = end
		mi.visibility_range_begin_margin = 4.0 if begin > 0.0 else 0.0
		mi.visibility_range_end_margin = 4.0 if end > 0.0 else 0.0
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		parent.add_child(mi)
	if lightest and shadow:
		var sh := MeshInstance3D.new()
		sh.name = "Shadow"
		sh.mesh = lightest
		sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		sh.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		sh.visibility_range_end = SHADOW_RANGE
		parent.add_child(sh)


## A mesh saved to its own file (keeps the scene file small), once per key.
func _saved(mesh: Mesh, key: String) -> Mesh:
	if _unwrap_cache.has(key):
		return _unwrap_cache[key]
	var path: String = BAKED + key.validate_filename() + ".res"
	ResourceSaver.save(mesh, path)
	var saved: Mesh = load(path)
	_unwrap_cache[key] = saved
	return saved


## A copy of the mesh with a lightmap UV2, saved once per source mesh.
func _unwrapped(mesh: Mesh, texel: float, key: String) -> Mesh:
	if _unwrap_cache.has(key):
		return _unwrap_cache[key]
	var file_name: String = key.validate_filename()
	var path: String = BAKED + file_name + ".res"
	var am: ArrayMesh = (mesh as ArrayMesh).duplicate()
	var err := am.lightmap_unwrap(Transform3D.IDENTITY, texel)
	if err != OK:
		print("CORNER unwrap failed for %s: %s" % [file_name, error_string(err)])
	ResourceSaver.save(am, path)
	var saved: Mesh = load(path)
	_unwrap_cache[key] = saved
	print("CORNER unwrapped %s (%d surfaces)" % [file_name, saved.get_surface_count()])
	return saved


# ---------------------------------------------------------------- ground mask


func _seg_dist(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var t: float = clampf((p - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
	return p.distance_to(a + ab * t)


func _line_dist(p: Vector2, line: Array[Vector2]) -> float:
	var d: float = INF
	for i in line.size() - 1:
		d = minf(d, _seg_dist(p, line[i], line[i + 1]))
	return d


func _mask() -> void:
	var img := Image.create(MASK_PX, MASK_PX, false, Image.FORMAT_RGBA8)
	var px: float = size / MASK_PX
	var wobble := FastNoiseLite.new()
	wobble.seed = 5
	wobble.frequency = 0.05
	for j in MASK_PX:
		for i in MASK_PX:
			var x: float = x0 + (i + 0.5) * px
			var z: float = z0 + (j + 0.5) * px
			var p := Vector2(x, z)
			var w: float = wobble.get_noise_2d(x, z)
			# path: 1.4 m worn core, frayed edge to about 2.6 m
			var dp: float = minf(_line_dist(p, PATH), _line_dist(p, SPUR))
			var path: float = 1.0 - smoothstep(1.2 + w * 0.5, 2.6 + w * 0.8, dp)
			# gravel yards round the houses (front and sides worn)
			var yard: float = 0.0
			for hs: Dictionary in houses:
				var hp: Vector3 = hs["pos"]
				var r: float = maxf(float(hs["hw"]), float(hs["hd"])) + 2.0
				var d: float = Vector2(hp.x, hp.z).distance_to(p)
				yard = maxf(yard, 1.0 - smoothstep(r - 1.0 + w * 1.5, r + 2.5 + w * 2.0, d))
			var h: float = _h(x, z)
			var shore: float = 1.0 - smoothstep(1.1 + w * 0.6, 2.0 + w * 0.8, h)
			shore *= smoothstep(-2.5, -1.2, h)
			var sand: float = (1.0 - smoothstep(0.1, 0.55 + w * 0.3, h)) * smoothstep(-1.5, -0.4, h)
			img.set_pixel(i, j, Color(path, yard * 0.85, shore, sand * 0.8))
	img.generate_mipmaps()
	img.save_png(OUT + "corner_mask.png")
	print("CORNER mask %d px (%.2f m/px)" % [MASK_PX, px])


# ---------------------------------------------------------------- ground meshes


func _ground_material() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/terrain_corner.gdshader")
	var dir := SpikeConfig.TERRAIN_DIR
	var c: Dictionary = terrain.meta["coarse"]
	var f: Dictionary = terrain.meta["fine"]
	for g: Array in [["coarse", c], ["fine", f]]:
		var d: Dictionary = g[1]
		var st: float = float(d["step"])
		m.set_shader_parameter(
			g[0] + "_rect",
			Vector4(
				float(d["x0"]),
				float(d["z0"]),
				st * (float(d["nx"]) - 1.0),
				st * (float(d["nz"]) - 1.0)
			)
		)
		m.set_shader_parameter(g[0] + "_texel", Vector2(1.0 / float(d["nx"]), 1.0 / float(d["nz"])))
		m.set_shader_parameter(g[0] + "_step", st)
	m.set_shader_parameter("fine_feather", float(f["feather"]))
	for key: String in ["rock_mask", "rock_nrm"]:
		m.set_shader_parameter(key, load(dir + "tex/%s.png" % key))
	for key: String in ["grass", "turf", "soil", "scree"]:
		m.set_shader_parameter(key + "_tex", load(dir + "tex/%s.png" % key))
	m.set_shader_parameter("noise_tex", terrain.world_noise())
	m.set_shader_parameter("coarse_light", load(dir + "coarse_light.png"))
	m.set_shader_parameter("fine_light", load(dir + "fine_light.png"))
	m.set_shader_parameter("coarse_detail", load(dir + "coarse_detail.png"))
	m.set_shader_parameter("fine_detail", load(dir + "fine_detail.png"))
	m.set_shader_parameter("forest_mask", load(dir + "forest_mask.png"))
	m.set_shader_parameter("quality", 2)
	m.set_shader_parameter("corner_rect", Vector4(x0, z0, size, size))
	m.set_shader_parameter("corner_mask", load(OUT + "corner_mask.png"))
	for key: String in ["path", "gravel", "pebbles", "sand"]:
		m.set_shader_parameter(key + "_tex", load(dir + "tex/%s.png" % key))
	m.set_shader_parameter("path_nrm", load(dir + "tex/path_nrm.png"))
	m.set_shader_parameter("pebbles_nrm", load(dir + "tex/pebbles_nrm.png"))
	ResourceSaver.save(m, OUT + "corner_ground.tres")
	return load(OUT + "corner_ground.tres")


func _ground() -> void:
	var mat := _ground_material()
	var holder := Node3D.new()
	holder.name = "Ground"
	corner.add_child(holder)
	var leaf: Array = (terrain.meta["levels"] as Array).back()["tiles"]
	var have := {}
	for t: Array in leaf:
		have[Vector2i(int(t[0]), int(t[1]))] = true
	var c: Dictionary = terrain.meta["coarse"]
	for tj in range(TILES.position.y, TILES.end.y):
		for ti in range(TILES.position.x, TILES.end.x):
			if not have.has(Vector2i(ti, tj)):
				print("CORNER no leaf tile %d,%d" % [ti, tj])
				continue
			var tx0: float = float(c["x0"]) + ti * LEAF
			var tz0: float = float(c["z0"]) + tj * LEAF
			var mesh := _tile_mesh(tx0, tz0)
			mesh.surface_set_material(0, mat)
			var path := OUT + "ground_%d_%d.res" % [ti, tj]
			ResourceSaver.save(mesh, path)
			var mi := MeshInstance3D.new()
			mi.name = "Tile_%d_%d" % [ti, tj]
			mi.mesh = load(path)
			mi.gi_mode = GeometryInstance3D.GI_MODE_STATIC
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			holder.add_child(mi)
	print("CORNER ground tiles %d" % holder.get_child_count())


## One 160 m tile at 2.5 m (65 x 65 vertices) plus a skirt, world coordinates, UV2 = lightmap.
func _tile_mesh(tx0: float, tz0: float) -> ArrayMesh:
	var n: int = CELLS + 1
	var st: float = LEAF / CELLS
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uv2 := PackedVector2Array()
	var idx := PackedInt32Array()
	var margin: float = 2.0 / (LEAF / TEXEL_GROUND)
	for j in n:
		for i in n:
			var x: float = tx0 + i * st
			var z: float = tz0 + j * st
			verts.append(Vector3(x, _h(x, z), z))
			norms.append(_normal(x, z))
			uv2.append(Vector2(i, j) / float(CELLS) * (1.0 - 2.0 * margin) + Vector2.ONE * margin)
	for j in CELLS:
		for i in CELLS:
			var a: int = j * n + i
			idx.append_array([a, a + 1, a + n, a + 1, a + n + 1, a + n])
	# skirt round the edge (hides cracks against coarser shader tiles)
	var ring: Array[int] = []
	for i in n:
		ring.append(i)
	for j in range(1, n):
		ring.append(j * n + CELLS)
	for i in range(CELLS - 1, -1, -1):
		ring.append(CELLS * n + i)
	for j in range(CELLS - 1, 0, -1):
		ring.append(j * n)
	var base: int = verts.size()
	for v in ring:
		verts.append(verts[v] - Vector3(0.0, 6.0, 0.0))
		norms.append(norms[v])
		uv2.append(uv2[v])
	var m: int = ring.size()
	for k in m:
		var a0: int = ring[k]
		var a1: int = ring[(k + 1) % m]
		var b0: int = base + k
		var b1: int = base + (k + 1) % m
		idx.append_array([a0, b0, a1, a1, b0, b1, a0, a1, b0, a1, b1, b0])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_TEX_UV2] = uv2
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var px: int = int(LEAF / TEXEL_GROUND)
	mesh.lightmap_size_hint = Vector2i(px, px)
	return mesh


# ---------------------------------------------------------------- bake-only occluder


## The valley round the corner (8 km at 40 m, a hole where the corner is), so the bake sees the
## walls hide the sky and the evening side of the fjord. Removed by Main at run time.
func _occluder() -> void:
	var st: float = 40.0
	var half: float = 4000.0
	var cx: float = x0 + size * 0.5
	var cz: float = z0 + size * 0.5
	var n: int = int(2.0 * half / st) + 1
	var verts := PackedVector3Array()
	var uv2 := PackedVector2Array()
	var idx := PackedInt32Array()
	for j in n:
		for i in n:
			var x: float = cx - half + i * st
			var z: float = cz - half + j * st
			var inside: bool = x > x0 + 1.0 and x < x0 + size - 1.0 and z > z0 + 1.0
			inside = inside and z < z0 + size - 1.0
			verts.append(Vector3(x, _h(x, z) - (3.0 if inside else 0.5), z))
			uv2.append(Vector2(i, j) / float(n - 1))
	for j in n - 1:
		for i in n - 1:
			var qx: float = cx - half + (i + 0.5) * st
			var qz: float = cz - half + (j + 0.5) * st
			if qx > x0 and qx < x0 + size and qz > z0 and qz < z0 + size:
				continue
			var a: int = j * n + i
			idx.append_array([a, a + 1, a + n, a + 1, a + n + 1, a + n])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_TEX_UV2] = uv2
	arrays[Mesh.ARRAY_INDEX] = idx
	var st_tool := SurfaceTool.new()
	st_tool.create_from_arrays(arrays)
	st_tool.generate_normals()
	var mesh := st_tool.commit()
	var mat := StandardMaterial3D.new()
	# average of the lit walls and slopes (gneiss, turf), for the light they bounce
	mat.albedo_color = Color(0.16, 0.17, 0.14)
	mat.roughness = 1.0
	mesh.surface_set_material(0, mat)
	mesh.lightmap_size_hint = Vector2i(64, 64)
	ResourceSaver.save(mesh, OUT + "occluder.res")
	var mi := MeshInstance3D.new()
	mi.name = "BakeOccluder"
	mi.mesh = load(OUT + "occluder.res")
	mi.gi_mode = GeometryInstance3D.GI_MODE_STATIC
	mi.gi_lightmap_scale = GeometryInstance3D.LIGHTMAP_SCALE_1X
	corner.add_child(mi)


# ---------------------------------------------------------------- props


func _prop(holder: Node3D, file: String, pos: Vector3, yaw: float, s: float = 1.0) -> Node3D:
	var meshes := _glb_meshes(MODELS + "props/" + file + ".glb")
	var node := Node3D.new()
	node.name = "%s_%d" % [file, holder.get_child_count()]
	node.transform = Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3.ONE * s), pos)
	holder.add_child(node)
	# thin fence rails: their sun shadow is a few pixels, not worth a draw per segment
	_add_lods(
		node,
		[meshes.get(file + "_LOD0"), meshes.get(file + "_LOD1")],
		[35.0, 160.0],
		TEXEL_PROP,
		file,
		not file.begins_with("skigard")
	)
	return node


func _on_ground(x: float, z: float, sink: float = 0.05) -> Vector3:
	return Vector3(x, _h(x, z) - sink, z)


func _props() -> void:
	var holder := Node3D.new()
	holder.name = "Props"
	corner.add_child(holder)
	# boats: two pulled up on the pebbles by the boathouses, one at the jetty
	_prop(holder, "boat_tarred", _on_ground(213.0, -161.0, 0.1), deg_to_rad(75.0))
	_prop(holder, "boat_painted", _on_ground(244.0, -199.0, 0.1), deg_to_rad(-60.0))
	_prop(holder, "boat_fishing", Vector3(206.0, -0.35, -167.5), deg_to_rad(90.0))
	# woodpiles against the gable or side walls
	for k in houses.size():
		if k % 2 == 1:
			continue
		var hs: Dictionary = houses[k]
		var b := Basis(Vector3.UP, float(hs["yaw"]))
		var off: Vector3 = b * Vector3(float(hs["hw"]) + 0.7, 0.0, rng.randf_range(-2.0, 2.0))
		var p: Vector3 = hs["pos"] + off
		var file: String = "woodpile_split" if k % 4 == 0 else "woodpile_logs"
		_prop(holder, file, _on_ground(p.x, p.z), float(hs["yaw"]), 1.6 if k % 4 == 0 else 1.0)
	# skigard along the uphill side of the path and round the field by the spawn
	_fence(holder, [Vector2(150, -30), Vector2(176, -58), Vector2(196, -80)])
	_fence(holder, [Vector2(255, -160), Vector2(275, -172), Vector2(296, -192)])
	_fence(holder, [Vector2(318, -240), Vector2(334, -262)])
	# hjell: two 6 m racks in a row on open ground between the spawn and the jetty
	_prop(holder, "hjell_6m", _on_ground(186.0, -122.0), deg_to_rad(-40.0))
	_prop(holder, "hjell_6m", _on_ground(190.6, -126.0), deg_to_rad(-40.0))


func _fence(holder: Node3D, line: Array[Vector2]) -> void:
	for i in line.size() - 1:
		var a: Vector2 = line[i]
		var b: Vector2 = line[i + 1]
		var d: float = a.distance_to(b)
		var dir := (b - a) / d
		var yaw: float = atan2(-dir.y, dir.x)
		var k: float = 0.0
		while k + 4.0 <= d:
			var p := a + dir * k
			_prop(holder, "skigard_4m", _on_ground(p.x, p.y, 0.15), yaw)
			k += 3.9


# ---------------------------------------------------------------- rocks


func _rock(holder: Node3D, file: String, part: String, pos: Vector3, basis: Basis) -> void:
	var meshes := _glb_meshes(MODELS + "rocks/" + file + ".glb")
	var pre: String = file + ("_" + part if part != "" else "")
	var node := Node3D.new()
	node.name = "%s_%d" % [pre, holder.get_child_count()]
	node.transform = Transform3D(basis, pos)
	holder.add_child(node)
	_add_lods(
		node,
		[meshes.get(pre + "_LOD0"), meshes.get(pre + "_LOD1"), meshes.get(pre + "_LOD2")],
		[40.0, 150.0, 900.0],
		TEXEL_ROCK,
		pre,
		not file.begins_with("boulders_a")
	)


func _rocks() -> void:
	var holder := Node3D.new()
	holder.name = "Rocks"
	corner.add_child(holder)
	var shore := 0
	var meadow := 0
	var talus := 0
	var faces := 0
	for attempt in 20000:
		var x: float = rng.randf_range(x0 + 10.0, x0 + size - 10.0)
		var z: float = rng.randf_range(z0 + 10.0, z0 + size - 10.0)
		var h: float = _h(x, z)
		var sl: float = _slope(x, z)
		var p2 := Vector2(x, z)
		if _line_dist(p2, PATH) < 4.0 or _near_house(p2, 4.0):
			continue
		var yaw := Basis(Vector3.UP, rng.randf() * TAU)
		# cliff pieces only on the wall behind the village (the beauty corner's cliff foot)
		var behind: bool = x > 320.0 and x < 470.0 and z > -320.0 and z < -120.0
		if h > -0.6 and h < 1.4 and shore < 24:
			# shore cobbles scaled up to boulders, half sunk
			var s: float = rng.randf_range(2.5, 6.0)
			var part: String = "a" if rng.randf() < 0.5 else "b"
			_rock(
				holder, "boulders_a", part, Vector3(x, h - 0.12 * s, z), yaw.scaled(Vector3.ONE * s)
			)
			shore += 1
		elif h > 2.0 and h < 30.0 and sl < 14.0 and meadow < 8 and rng.randf() < 0.05:
			var s2: float = rng.randf_range(0.7, 1.3)
			_rock(
				holder, "boulder_a", "", Vector3(x, h - 0.35 * s2, z), yaw.scaled(Vector3.ONE * s2)
			)
			meadow += 1
		elif sl > 22.0 and sl < 42.0 and h > 6.0 and h < 160.0 and talus < 18 and behind:
			# talus aprons at the cliff foot, turned so the apron runs down-slope
			var nrm := _normal(x, z)
			var down := Vector3(nrm.x, 0.0, nrm.z).normalized()
			var ts: float = rng.randf_range(1.5, 3.0)
			var b := Basis.looking_at(down, Vector3.UP).scaled(Vector3.ONE * ts)
			var file: String = "cliff_jagged_a" if talus % 2 == 0 else "cliff_jagged_b"
			_rock(holder, file, "", Vector3(x, h - 0.5 * ts, z), b)
			talus += 1
		elif sl > 45.0 and h > 25.0 and h < 260.0 and faces < 16 and behind:
			# cliff faces on the steep band, facing out of the slope, partly sunk
			var nrm2 := _normal(x, z)
			var out := Vector3(nrm2.x, 0.0, nrm2.z).normalized()
			# faces at wall scale (the scans are about 10 m; the wall is 150 m+): ledges and
			# buttresses that break the smooth terrain surface
			var s3: float = rng.randf_range(3.0, 6.0)
			var b2 := Basis.looking_at(-out, Vector3.UP).scaled(Vector3.ONE * s3)
			var file2: String = "cliff_face_a" if faces % 2 == 0 else "cliff_granite_a"
			_rock(holder, file2, "", Vector3(x, h - 1.2 * s3, z) - out * 1.2 * s3, b2)
			faces += 1
	print("CORNER rocks: shore %d, meadow %d, talus %d, faces %d" % [shore, meadow, talus, faces])


func _near_house(p: Vector2, pad: float) -> bool:
	for hs: Dictionary in houses:
		var hp: Vector3 = hs["pos"]
		if Vector2(hp.x, hp.z).distance_to(p) < maxf(float(hs["hw"]), float(hs["hd"])) + pad:
			return true
	return false


# ---------------------------------------------------------------- trees (dynamic)


## Birches round the village edges and along the path (groups of 3-5), real meshes with LODs.
func _trees() -> void:
	var holder := Node3D.new()
	holder.name = "Trees"
	corner.add_child(holder)
	var groups: Array[Vector2] = [
		Vector2(172, -40),
		Vector2(198, -66),
		Vector2(262, -140),
		Vector2(262, -118),
		Vector2(290, -282),
		Vector2(340, -236),
		Vector2(150, -8),
	]
	var n := 0
	for g in groups:
		for k in rng.randi_range(3, 5):
			var p: Vector2 = g + Vector2(rng.randf_range(-9, 9), rng.randf_range(-9, 9))
			if _line_dist(p, PATH) < 3.5 or _near_house(p, 3.0) or _h(p.x, p.y) < 1.5:
				continue
			var file: String = ["downy_birch_a", "downy_birch_b", "downy_birch_c"][n % 3]
			var t := Node3D.new()
			t.name = "%s_%d" % [file, n]
			var s: float = rng.randf_range(0.85, 1.2)
			t.transform = Transform3D(
				Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * s),
				_on_ground(p.x, p.y, 0.1)
			)
			holder.add_child(t)
			# designer NOTES: LOD0 to 30 m, LOD1 to 60 m, LOD3 to 150 m (LOD2 skipped)
			var ranges: Array[Vector2] = [Vector2(0, 30), Vector2(30, 60), Vector2(60, 150)]
			var lods: Array[String] = ["LOD0", "LOD1", "LOD3"]
			for li in lods.size():
				var mi := MeshInstance3D.new()
				mi.name = lods[li]
				mi.mesh = _tree_mesh(file, lods[li])
				mi.gi_mode = GeometryInstance3D.GI_MODE_DYNAMIC
				mi.visibility_range_begin = ranges[li].x
				mi.visibility_range_end = ranges[li].y
				mi.visibility_range_begin_margin = 3.0 if ranges[li].x > 0.0 else 0.0
				mi.visibility_range_end_margin = 3.0
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				t.add_child(mi)
			# one light shadow caster per tree (LOD3, about 1k triangles)
			var sh := MeshInstance3D.new()
			sh.name = "Shadow"
			sh.mesh = _tree_mesh(file, "LOD3")
			sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
			sh.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
			sh.visibility_range_end = 150.0
			t.add_child(sh)
			n += 1
	print("CORNER birches %d" % n)


## A tree LOD mesh saved once with foliage materials per the designer's NOTES: leaves alpha
## scissor, two-sided, albedo x COLOR_0 (crown AO), light through the leaves; bark as is.
func _tree_mesh(file: String, lod: String) -> Mesh:
	var path: String = BAKED + "%s_%s.res" % [file, lod]
	if _unwrap_cache.has(path):
		return _unwrap_cache[path]
	var src: Mesh = _glb_meshes(MODELS + "trees/" + file + ".glb")[file + "_" + lod]
	var m: ArrayMesh = (src as ArrayMesh).duplicate()
	for si in m.get_surface_count():
		var mat := m.surface_get_material(si) as StandardMaterial3D
		if mat == null:
			continue
		mat = mat.duplicate() as StandardMaterial3D
		if mat.resource_name.to_lower().contains("lea"):
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			mat.alpha_scissor_threshold = 0.5
			mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			mat.vertex_color_use_as_albedo = true
			mat.backlight_enabled = true
			mat.backlight = Color(0.22, 0.26, 0.08)
			mat.metallic_specular = 0.2
		m.surface_set_material(si, mat)
	ResourceSaver.save(m, path)
	var saved: Mesh = load(path)
	_unwrap_cache[path] = saved
	return saved


# ---------------------------------------------------------------- lighting


func _sky_mean() -> Color:
	var img: Image = (load(SpikeConfig.SKY_TEXTURE) as Texture2D).get_image()
	if img.is_compressed():
		img.decompress()
	img.resize(256, 128)
	var acc := Color(0, 0, 0)
	var n: int = 0
	for y in 64:
		for x in 256:
			acc += img.get_pixel(x, y).srgb_to_linear()
			n += 1
	var c := Color(acc.r / n, acc.g / n, acc.b / n).linear_to_srgb()
	print("CORNER sky mean (sRGB) %s" % c)
	return c


func _lighting() -> void:
	var sun := DirectionalLight3D.new()
	sun.name = "BakeSun"
	var el: float = deg_to_rad(SpikeConfig.SUN_ELEVATION_DEG)
	var az: float = deg_to_rad(SpikeConfig.SUN_AZIMUTH_DEG)
	var to_sun := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
	sun.transform = Transform3D(Basis.looking_at(-to_sun, Vector3.UP), Vector3(0, 100, 0))
	sun.light_color = SpikeConfig.SUN_COLOR
	sun.light_energy = SpikeConfig.SUN_ENERGY
	sun.light_bake_mode = Light3D.BAKE_DYNAMIC
	sun.shadow_enabled = true
	corner.add_child(sun)
	var sky_mat := PanoramaSkyMaterial.new()
	sky_mat.panorama = load(SpikeConfig.SKY_TEXTURE)
	sky_mat.energy_multiplier = SpikeConfig.SKY_ENERGY
	var sky := Sky.new()
	sky.sky_material = sky_mat
	var lm := LightmapGI.new()
	lm.name = "LightmapGI"
	# WF_CORNER_QUALITY: low (default; about 1/4 the texels, quick, keeps the laptop GPU cool),
	# medium, high (the full 24 min bake), fast (lighting checks only)
	var q: String = OS.get_environment("WF_CORNER_QUALITY")
	var settings: Dictionary = {
		"fast": [LightmapGI.BAKE_QUALITY_LOW, 1, 0.2],
		"low": [LightmapGI.BAKE_QUALITY_LOW, 2, 0.5],
		"medium": [LightmapGI.BAKE_QUALITY_MEDIUM, 3, 0.75],
		"high": [LightmapGI.BAKE_QUALITY_HIGH, 3, 1.0],
	}
	var pick: Array = settings.get(q, settings["low"])
	lm.quality = pick[0]
	lm.bounces = pick[1]
	print("CORNER bake quality %s" % (q if settings.has(q) else "low"))
	lm.directional = false
	lm.use_denoiser = true
	# sky light for the bake: the custom-sky path baked almost no sky light here (Godot 4.6.2,
	# headless editor; shaded walls came out near black), so the bake uses a custom colour = the
	# mean of the sky panorama's upper half times the sky energy (the cloud sky is near uniform)
	lm.environment_mode = LightmapGI.ENVIRONMENT_MODE_CUSTOM_COLOR
	lm.environment_custom_color = _sky_mean()
	lm.environment_custom_energy = SpikeConfig.AMBIENT_ENERGY * SpikeConfig.SKY_ENERGY
	lm.environment_custom_sky = sky
	lm.texel_scale = pick[2]
	lm.max_texture_size = 4096
	lm.generate_probes_subdiv = LightmapGI.GENERATE_PROBES_SUBDIV_8
	corner.add_child(lm)
