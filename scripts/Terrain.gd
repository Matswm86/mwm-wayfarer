class_name Terrain
extends Node3D

## Builds the fjord terrain from the baked files in assets/terrain/ (tools/terrain/npz_to_godot.py).
## Tiles form a quadtree with visibility ranges (HLOD): a tile hides and its four children show
## when the camera is closer than LOD_SPLIT x tile size. Heights come from textures in the shader;
## every tile at a level shares one flat grid mesh.
## Terrain data (c) Kartverket, CC BY 4.0.

var meta: Dictionary = {}
var coarse_img: Image
var fine_img: Image
var material: ShaderMaterial
var tile_count: int = 0
## Beauty corner (pass 3): leaf tiles (finest level, 160 m) inside this rect of tile indices are
## not built; scenes/BeautyCorner.tscn draws them as lightmapped meshes. Set before build().
var skip_leaf: Rect2i = Rect2i()
## Tile nodes per level: Vector2i(tile i, j) -> MeshInstance3D (corner meshes take their
## visibility parent from here).
var tile_nodes: Array[Dictionary] = []

var _coarse: Dictionary = {}
var _fine: Dictionary = {}
## CPU copies of the height grids for height_at (perf pass 3: Image.get_pixel plus dictionary
## lookups cost about 10 us per call; raw arrays and cached grid numbers about a fifth of that).
var _c_data: PackedFloat32Array
var _f_data: PackedFloat32Array
var _c_grid: PackedFloat32Array  # x0, z0, step, nx, nz
var _f_grid: PackedFloat32Array  # x0, z0, step, nx, nz, feather
var _tex_cache: Dictionary = {}
var _noise: NoiseTexture2D


func load_data() -> void:
	var f := FileAccess.open(SpikeConfig.TERRAIN_DIR + "terrain.json", FileAccess.READ)
	meta = JSON.parse_string(f.get_as_text())
	_coarse = meta["coarse"]
	_fine = meta["fine"]
	coarse_img = _load_heights("coarse_h.bin", int(_coarse["nx"]), int(_coarse["nz"]))
	fine_img = _load_heights("fine_h.bin", int(_fine["nx"]), int(_fine["nz"]))
	_c_data = coarse_img.get_data().to_float32_array()
	_f_data = fine_img.get_data().to_float32_array()
	_c_grid = PackedFloat32Array(
		[
			float(_coarse["x0"]),
			float(_coarse["z0"]),
			float(_coarse["step"]),
			float(_coarse["nx"]),
			float(_coarse["nz"])
		]
	)
	_f_grid = PackedFloat32Array(
		[
			float(_fine["x0"]),
			float(_fine["z0"]),
			float(_fine["step"]),
			float(_fine["nx"]),
			float(_fine["nz"]),
			float(_fine["feather"])
		]
	)


func _load_heights(file_name: String, nx: int, nz: int) -> Image:
	var bytes := FileAccess.get_file_as_bytes(SpikeConfig.TERRAIN_DIR + file_name)
	var img := Image.create_from_data(nx, nz, false, Image.FORMAT_RF, bytes)
	return img


## Shader parameters every terrain-following material needs.
func apply_height_params(mat: ShaderMaterial) -> void:
	mat.set_shader_parameter("coarse_h", _texture(coarse_img))
	mat.set_shader_parameter("fine_h", _texture(fine_img))
	mat.set_shader_parameter("coarse_rect", _rect(_coarse))
	mat.set_shader_parameter("fine_rect", _rect(_fine))
	mat.set_shader_parameter(
		"coarse_texel", Vector2(1.0 / float(_coarse["nx"]), 1.0 / float(_coarse["nz"]))
	)
	mat.set_shader_parameter(
		"fine_texel", Vector2(1.0 / float(_fine["nx"]), 1.0 / float(_fine["nz"]))
	)
	mat.set_shader_parameter("coarse_step", float(_coarse["step"]))
	mat.set_shader_parameter("fine_step", float(_fine["step"]))
	mat.set_shader_parameter("fine_feather", float(_fine["feather"]))


## Baked sun visibility, sky visibility, concavity and scree (tools/spike/bake_terrain_light.py),
## for every material that sits on the terrain (terrain, trees, ground cover).
func apply_light_params(mat: ShaderMaterial) -> void:
	mat.set_shader_parameter("coarse_light", load(SpikeConfig.TERRAIN_DIR + "coarse_light.png"))
	mat.set_shader_parameter("fine_light", load(SpikeConfig.TERRAIN_DIR + "fine_light.png"))


## Seamless value noise shared by the terrain shaders (generated once, no file).
func world_noise() -> NoiseTexture2D:
	if _noise:
		return _noise
	var n := FastNoiseLite.new()
	n.seed = 7
	n.noise_type = FastNoiseLite.TYPE_VALUE_CUBIC
	n.frequency = 1.0 / 48.0
	n.fractal_octaves = 5
	_noise = NoiseTexture2D.new()
	_noise.width = 512
	_noise.height = 512
	_noise.seamless = true
	_noise.normalize = true
	_noise.generate_mipmaps = true
	_noise.noise = n
	return _noise


## One mipmapped height texture per image, shared by every material.
func _texture(img: Image) -> ImageTexture:
	if _tex_cache.has(img):
		return _tex_cache[img]
	var copy := img.duplicate() as Image
	copy.generate_mipmaps()
	var tex := ImageTexture.create_from_image(copy)
	_tex_cache[img] = tex
	return tex


func _rect(g: Dictionary) -> Vector4:
	var st: float = float(g["step"])
	return Vector4(
		float(g["x0"]),
		float(g["z0"]),
		st * (float(g["nx"]) - 1.0),
		st * (float(g["nz"]) - 1.0),
	)


func build() -> void:
	material = ShaderMaterial.new()
	material.shader = load("res://shaders/terrain.gdshader")
	apply_height_params(material)
	for key: String in ["rock_mask", "rock_nrm"]:
		material.set_shader_parameter(key, load(SpikeConfig.TERRAIN_DIR + "tex/%s.png" % key))
	for key: String in ["grass", "turf", "soil", "scree"]:
		material.set_shader_parameter(
			key + "_tex", load(SpikeConfig.TERRAIN_DIR + "tex/%s.png" % key)
		)
	material.set_shader_parameter("noise_tex", world_noise())
	apply_light_params(material)
	material.set_shader_parameter(
		"coarse_detail", load(SpikeConfig.TERRAIN_DIR + "coarse_detail.png")
	)
	material.set_shader_parameter("fine_detail", load(SpikeConfig.TERRAIN_DIR + "fine_detail.png"))
	material.set_shader_parameter("forest_mask", load(SpikeConfig.TERRAIN_DIR + "forest_mask.png"))
	material.set_shader_parameter("skirt_depth", SpikeConfig.SKIRT_DEPTH)

	var levels: Array = meta["levels"]
	var x0: float = float(_coarse["x0"])
	var z0: float = float(_coarse["z0"])
	var meshes: Dictionary = {}
	var prev: Dictionary = {}  # Vector2i -> MeshInstance3D of the previous level
	var prev_size: float = 0.0
	var complete: Dictionary = {}  # previous-level tiles that hide for all four children
	for li in levels.size():
		var lv: Dictionary = levels[li]
		var size: float = float(lv["size"])
		var cells: int = int(lv["cells"])
		if not meshes.has(cells):
			meshes[cells] = _grid_mesh(cells)
		var leaf: bool = li == levels.size() - 1
		# a tile hides for its children only when all four exist (the 160 m level covers the
		# fine data only; a parent on its edge with some children missing left a hole)
		var has_children: Dictionary = {}
		if not leaf:
			var nxt: Dictionary = levels[li + 1]
			var ratio: int = int(size / float(nxt["size"]))
			var count: Dictionary = {}
			for t: Array in nxt["tiles"]:
				var key := Vector2i(int(t[0]) / ratio, int(t[1]) / ratio)
				count[key] = int(count.get(key, 0)) + 1
			for key: Vector2i in count:
				if int(count[key]) == ratio * ratio:
					has_children[key] = true
		var cur: Dictionary = {}
		for t: Array in lv["tiles"]:
			var ti: int = int(t[0])
			var tj: int = int(t[1])
			if li > 0 and not complete.has(Vector2i(ti, tj) / int(prev_size / size)):
				continue
			if leaf and skip_leaf.has_point(Vector2i(ti, tj)):
				continue
			var lo: float = float(t[2]) - SpikeConfig.SKIRT_DEPTH - size / float(cells)
			var hi: float = float(t[3])
			var mi := MeshInstance3D.new()
			mi.mesh = meshes[cells]
			mi.material_override = material
			mi.position = Vector3(x0 + (ti + 0.5) * size, 0.0, z0 + (tj + 0.5) * size)
			mi.scale = Vector3(size, 1.0, size)
			mi.custom_aabb = AABB(Vector3(-0.5, lo, -0.5), Vector3(1.0, hi - lo, 1.0))
			var casts: bool = li >= SpikeConfig.SHADOW_LEVEL
			mi.cast_shadow = (
				GeometryInstance3D.SHADOW_CASTING_SETTING_ON
				if casts
				else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			)
			if has_children.has(Vector2i(ti, tj)):
				mi.visibility_range_begin = size * SpikeConfig.LOD_SPLIT
				mi.visibility_range_begin_margin = size * SpikeConfig.LOD_MARGIN
			add_child(mi)
			if li > 0:
				var ratio_up: int = int(prev_size / size)
				var parent: MeshInstance3D = prev.get(Vector2i(ti / ratio_up, tj / ratio_up))
				if parent:
					mi.visibility_parent = mi.get_path_to(parent)
			cur[Vector2i(ti, tj)] = mi
			tile_count += 1
		prev = cur
		tile_nodes.append(cur)
		prev_size = size
		complete = has_children


## Unit grid -0.5..0.5 with a skirt round the edge. UV2 = (cells, skirt flag).
func _grid_mesh(cells: int) -> ArrayMesh:
	var verts := PackedVector3Array()
	var uv2 := PackedVector2Array()
	var idx := PackedInt32Array()
	var n: int = cells + 1
	var c: float = float(cells)
	for j in n:
		for i in n:
			verts.append(Vector3(i / c - 0.5, 0.0, j / c - 0.5))
			uv2.append(Vector2(c, 0.0))
	for j in cells:
		for i in cells:
			var a: int = j * n + i
			idx.append_array([a, a + 1, a + n, a + 1, a + n + 1, a + n])
	# skirt: walk the border counter-clockwise, drop a copy of each edge vertex
	var ring: Array[int] = []
	for i in n:
		ring.append(i)
	for j in range(1, n):
		ring.append(j * n + cells)
	for i in range(cells - 1, -1, -1):
		ring.append(cells * n + i)
	for j in range(cells - 1, 0, -1):
		ring.append(j * n)
	var base: int = verts.size()
	for v in ring:
		verts.append(verts[v])
		uv2.append(Vector2(c, 1.0))
	var m: int = ring.size()
	for k in m:
		var a0: int = ring[k]
		var a1: int = ring[(k + 1) % m]
		var b0: int = base + k
		var b1: int = base + (k + 1) % m
		# both windings so the skirt shows from either side
		idx.append_array([a0, b0, a1, a1, b0, b1, a0, a1, b0, a1, b1, b0])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_TEX_UV2] = uv2
	arrays[Mesh.ARRAY_INDEX] = idx
	var normals := PackedVector3Array()
	normals.resize(verts.size())
	normals.fill(Vector3.UP)
	arrays[Mesh.ARRAY_NORMAL] = normals
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


## CPU height, same blend as the shader (bilinear, fine feathered into coarse).
func height_at(x: float, z: float) -> float:
	var hc: float = _bilinear(_c_data, _c_grid, x, z)
	var st: float = _f_grid[2]
	var fx1: float = _f_grid[0] + st * (_f_grid[3] - 1.0)
	var fz1: float = _f_grid[1] + st * (_f_grid[4] - 1.0)
	var inner: float = minf(minf(x - _f_grid[0], fx1 - x), minf(z - _f_grid[1], fz1 - z))
	if inner <= 0.0:
		return hc
	var k: float = smoothstep(0.0, _f_grid[5], inner)
	return lerpf(hc, _bilinear(_f_data, _f_grid, x, z), k)


func _bilinear(d: PackedFloat32Array, g: PackedFloat32Array, x: float, z: float) -> float:
	var st: float = g[2]
	var nx: int = int(g[3])
	var fx: float = clampf((x - g[0]) / st, 0.0, g[3] - 1.001)
	var fz: float = clampf((z - g[1]) / st, 0.0, g[4] - 1.001)
	var i: int = int(fx)
	var j: int = int(fz)
	var tx: float = fx - i
	var tz: float = fz - j
	var o: int = j * nx + i
	var top: float = lerpf(d[o], d[o + 1], tx)
	var bot: float = lerpf(d[o + nx], d[o + nx + 1], tx)
	return lerpf(top, bot, tz)
