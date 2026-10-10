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

var _coarse: Dictionary = {}
var _fine: Dictionary = {}
var _tex_cache: Dictionary = {}


func load_data() -> void:
	var f := FileAccess.open(SpikeConfig.TERRAIN_DIR + "terrain.json", FileAccess.READ)
	meta = JSON.parse_string(f.get_as_text())
	_coarse = meta["coarse"]
	_fine = meta["fine"]
	coarse_img = _load_heights("coarse_h.bin", int(_coarse["nx"]), int(_coarse["nz"]))
	fine_img = _load_heights("fine_h.bin", int(_fine["nx"]), int(_fine["nz"]))


func _load_heights(file_name: String, nx: int, nz: int) -> Image:
	var bytes := FileAccess.get_file_as_bytes(SpikeConfig.TERRAIN_DIR + file_name)
	var img := Image.create_from_data(nx, nz, false, Image.FORMAT_RH, bytes)
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
	material.set_shader_parameter("grass_tex", load("res://assets/textures/grass_albedo.jpg"))
	material.set_shader_parameter("rock_tex", load("res://assets/textures/rock_albedo.jpg"))
	material.set_shader_parameter("rock_nrm", load("res://assets/textures/rock_normal.jpg"))
	material.set_shader_parameter("alpine_tex", load("res://assets/textures/alpine_albedo.jpg"))
	material.set_shader_parameter("skirt_depth", SpikeConfig.SKIRT_DEPTH)

	var levels: Array = meta["levels"]
	var x0: float = float(_coarse["x0"])
	var z0: float = float(_coarse["z0"])
	var meshes: Dictionary = {}
	var prev: Dictionary = {}  # Vector2i -> MeshInstance3D of the previous level
	var prev_size: float = 0.0
	for li in levels.size():
		var lv: Dictionary = levels[li]
		var size: float = float(lv["size"])
		var cells: int = int(lv["cells"])
		if not meshes.has(cells):
			meshes[cells] = _grid_mesh(cells)
		var leaf: bool = li == levels.size() - 1
		var has_children: Dictionary = {}
		if not leaf:
			var nxt: Dictionary = levels[li + 1]
			var ratio: int = int(size / float(nxt["size"]))
			for t: Array in nxt["tiles"]:
				has_children[Vector2i(int(t[0]) / ratio, int(t[1]) / ratio)] = true
		var cur: Dictionary = {}
		for t: Array in lv["tiles"]:
			var ti: int = int(t[0])
			var tj: int = int(t[1])
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
		prev_size = size


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
	var hc: float = _bilinear(coarse_img, _coarse, x, z)
	var fx0: float = float(_fine["x0"])
	var fz0: float = float(_fine["z0"])
	var st: float = float(_fine["step"])
	var fx1: float = fx0 + st * (float(_fine["nx"]) - 1.0)
	var fz1: float = fz0 + st * (float(_fine["nz"]) - 1.0)
	var inner: float = minf(minf(x - fx0, fx1 - x), minf(z - fz0, fz1 - z))
	if inner <= 0.0:
		return hc
	var k: float = smoothstep(0.0, float(_fine["feather"]), inner)
	return lerpf(hc, _bilinear(fine_img, _fine, x, z), k)


func _bilinear(img: Image, g: Dictionary, x: float, z: float) -> float:
	var st: float = float(g["step"])
	var fx: float = clampf((x - float(g["x0"])) / st, 0.0, float(g["nx"]) - 1.001)
	var fz: float = clampf((z - float(g["z0"])) / st, 0.0, float(g["nz"]) - 1.001)
	var i: int = int(fx)
	var j: int = int(fz)
	var tx: float = fx - i
	var tz: float = fz - j
	var top: float = lerpf(img.get_pixel(i, j).r, img.get_pixel(i + 1, j).r, tx)
	var bot: float = lerpf(img.get_pixel(i, j + 1).r, img.get_pixel(i + 1, j + 1).r, tx)
	return lerpf(top, bot, tz)
