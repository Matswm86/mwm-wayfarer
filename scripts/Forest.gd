class_name Forest
extends Node3D

## Pines, spruces and birch stand-ins from assets/terrain/trees.bin (placed by
## tools/terrain/npz_to_godot.py on 5-40 degree slopes between 5 m and ~500 m, broadleaf mixed in
## below ~320 m). Every tree is an impostor quad (shaders/tree.gdshader) showing frames of a
## scanned Poly Haven tree (CC0, tools/spike/bake_tree_impostors.py). Near chunks (640 m) blend
## frames and cast shadows; far cells (2560 m) take one frame per tree. The shader hides each tree
## in the wrong LOD by its own distance, so per tree exactly one quad is drawn.
## Density = the first share of each chunk's (shuffled) trees.

const STRIDE := 6  # x, y, z, yaw, scale, species
const FLOATS := 16  # 12 transform + 4 custom
const DIR := "res://assets/models/trees/"
## Tree height at instance scale 1 (the old procedural pine was 13.2 m): conifers, broadleaf.
const CONIFER_HEIGHT := 14.0
const BROADLEAF_HEIGHT := 11.0
## The only broadleaf impostor is Poly Haven's island_tree_01, which reads as an olive grove in a
## Norwegian fjord; its places take pines and spruces until a birch impostor exists.
const USE_BROADLEAF := false
## Per impostor variant (trees.json order): albedo tint toward Norwegian forest greens.
const TINTS: Array[Vector3] = [
	Vector3(0.80, 0.92, 0.82),
	Vector3(0.80, 0.92, 0.82),
	Vector3(0.70, 0.86, 0.80),
	Vector3(0.70, 0.86, 0.80),
	Vector3(0.95, 1.05, 0.80),
]

var density: float = 1.0
var near_mat: ShaderMaterial
var far_mat: ShaderMaterial

var _chunks: Array = []  # [ci, cj, start, count] per 640 m chunk
var _buffers: Array[PackedFloat32Array] = []  # per 640 m chunk, FLOATS per tree
var _near: Array[MultiMeshInstance3D] = []
var _far: Dictionary = {}  # Vector2i (2560 m cell) -> MultiMeshInstance3D
var _far_members: Dictionary = {}  # Vector2i -> Array of chunk indices
var _total: int = 0
var _origin := Vector2.ZERO  # x0, z0 of the coarse grid (chunk 0, 0)


func build(terrain: Terrain) -> void:
	var meta: Dictionary = terrain.meta
	var forest: Dictionary = meta["forest"]
	var coarse: Dictionary = meta["coarse"]
	var x0: float = float(coarse["x0"])
	var z0: float = float(coarse["z0"])
	_origin = Vector2(x0, z0)
	_chunks = forest["chunks"]
	var bytes := FileAccess.get_file_as_bytes(SpikeConfig.TERRAIN_DIR + "trees.bin")
	var data := bytes.to_float32_array()
	_total = data.size() / STRIDE

	var info: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR + "trees.json"))
	var frames := PackedVector2Array()
	var tints := PackedVector3Array()
	var variants: Array = info["variants"]
	for vi in variants.size():
		var v: Dictionary = variants[vi]
		var target: float = BROADLEAF_HEIGHT if vi == variants.size() - 1 else CONIFER_HEIGHT
		var k: float = target / float(v["height"])
		frames.append(Vector2(float(v["frame_m"]) * k, float(v["centre_z"]) * k))
		tints.append(TINTS[vi])
	var shader: Shader = load("res://shaders/tree.gdshader")
	near_mat = ShaderMaterial.new()
	near_mat.shader = shader
	far_mat = ShaderMaterial.new()
	far_mat.shader = shader
	far_mat.set_shader_parameter("is_far", true)
	var albedo: Texture2D = load(DIR + "trees_albedo.png")
	for m: ShaderMaterial in [near_mat, far_mat]:
		terrain.apply_height_params(m)
		terrain.apply_light_params(m)
		m.set_shader_parameter("atlas_albedo", albedo)
		m.set_shader_parameter("atlas_normal", load(DIR + "trees_normal.png"))
		m.set_shader_parameter("atlas_px", Vector2(albedo.get_width(), albedo.get_height()))
		m.set_shader_parameter("variants", float(variants.size()))
		m.set_shader_parameter("frame_info", frames)
		m.set_shader_parameter("tints", tints)
		m.set_shader_parameter("lod_radius", SpikeConfig.TREE_NEAR_RADIUS)
	var quad := _quad_mesh()
	var ratio: float = SpikeConfig.TREE_FAR_CHUNK
	var half_diag: float = SpikeConfig.TREE_NEAR_CHUNK * 0.75

	for k in _chunks.size():
		var c: Array = _chunks[k]
		var start: int = int(c[2])
		var count: int = int(c[3])
		var buf := PackedFloat32Array()
		buf.resize(count * FLOATS)
		for t in count:
			var o: int = (start + t) * STRIDE
			var sp: int = int(data[o + 5])
			var b := Basis(Vector3.UP, data[o + 3]).scaled(Vector3.ONE * data[o + 4])
			var h: float = fposmod(data[o + 3] * 7.13, 1.0)
			# species 0: pines and spruces (spruce a little more common), 1: broadleaf
			var variant: int = int(fposmod(data[o + 3] * 13.7, 1.0) * 4.0)
			if sp == 1 and USE_BROADLEAF:
				variant = 4
			var w: int = t * FLOATS
			var row: Array[float] = [
				b.x.x,
				b.y.x,
				b.z.x,
				data[o],
				b.x.y,
				b.y.y,
				b.z.y,
				data[o + 1],
				b.x.z,
				b.y.z,
				b.z.z,
				data[o + 2],
				float(variant),
				h,
				0.0,
				0.0
			]
			for i in FLOATS:
				buf[w + i] = row[i]
		_buffers.append(buf)

		var mmi := _multimesh(quad, near_mat)
		mmi.visibility_range_end = SpikeConfig.TREE_NEAR_RADIUS + half_diag
		mmi.visibility_range_end_margin = 40.0
		add_child(mmi)
		_near.append(mmi)

		var cx: float = x0 + (int(c[0]) + 0.5) * SpikeConfig.TREE_NEAR_CHUNK
		var cz: float = z0 + (int(c[1]) + 0.5) * SpikeConfig.TREE_NEAR_CHUNK
		var cell := Vector2i(int((cx - x0) / ratio), int((cz - z0) / ratio))
		if not _far.has(cell):
			var fm := _multimesh(quad, far_mat)
			fm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			fm.visibility_range_end = SpikeConfig.TREE_FAR_END
			add_child(fm)
			_far[cell] = fm
			_far_members[cell] = []
		(_far_members[cell] as Array).append(k)
	set_density(density)


func _multimesh(mesh: Mesh, mat: ShaderMaterial) -> MultiMeshInstance3D:
	var mmi := MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh
	mmi.multimesh = mm
	mmi.material_override = mat
	return mmi


func set_density(d: float) -> void:
	density = d
	for k in _near.size():
		var buf: PackedFloat32Array = _buffers[k]
		var n: int = int(ceil(buf.size() / float(FLOATS) * density))
		var mm: MultiMesh = _near[k].multimesh
		mm.instance_count = n
		if n > 0:
			mm.buffer = buf.slice(0, n * FLOATS)
	for cell: Vector2i in _far:
		var acc := PackedFloat32Array()
		for k: int in _far_members[cell]:
			var buf: PackedFloat32Array = _buffers[k]
			var n: int = int(ceil(buf.size() / float(FLOATS) * density))
			acc.append_array(buf.slice(0, n * FLOATS))
		var fmm: MultiMesh = (_far[cell] as MultiMeshInstance3D).multimesh
		fmm.instance_count = acc.size() / FLOATS
		if acc.size() > 0:
			fmm.buffer = acc


func set_shadows(on: bool) -> void:
	for mmi: MultiMeshInstance3D in _near:
		mmi.cast_shadow = (
			GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			if on
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		)


## Conifers within r of the camera are drawn as meshes by NearTrees; the impostors hide them.
func set_geo_radius(r: float) -> void:
	near_mat.set_shader_parameter("geo_radius", r)
	far_mat.set_shader_parameter("geo_radius", r)


## Indices of the 640 m chunks that overlap a circle of radius r round c.
func chunks_near(c: Vector3, r: float) -> Array[int]:
	var out: Array[int] = []
	var size: float = SpikeConfig.TREE_NEAR_CHUNK
	for k in _chunks.size():
		var ch: Array = _chunks[k]
		var x0: float = _origin.x + int(ch[0]) * size
		var z0: float = _origin.y + int(ch[1]) * size
		var nx: float = clampf(c.x, x0, x0 + size)
		var nz: float = clampf(c.z, z0, z0 + size)
		if Vector2(c.x - nx, c.z - nz).length() < r:
			out.append(k)
	return out


func chunk_buffer(k: int) -> PackedFloat32Array:
	return _buffers[k]


## Trees of chunk k drawn at the current density (the first share of the shuffled list).
func chunk_visible_count(k: int) -> int:
	return int(ceil(_buffers[k].size() / float(FLOATS) * density))


func visible_trees() -> int:
	return int(ceil(_total * density))


func _process(_delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var p := cam.global_position
	near_mat.set_shader_parameter("lod_center", p)
	far_mat.set_shader_parameter("lod_center", p)


## One quad (UV 0..1); the shader places it, the vertex positions only size the culling box
## (a 16 m wide, 28 m tall tree at scale 1).
func _quad_mesh() -> ArrayMesh:
	var verts := PackedVector3Array(
		[Vector3(-8, 0, -8), Vector3(8, 0, 8), Vector3(8, 28, 8), Vector3(-8, 28, -8)]
	)
	var uvs := PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh
