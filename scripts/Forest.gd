class_name Forest
extends Node3D

## Pines and birches from assets/terrain/trees.bin (placed by tools/terrain/npz_to_godot.py on
## 5-40 degree slopes between 5 m and ~500 m, birch mixed in below ~320 m).
## Near chunks (640 m) draw a
## ~29-triangle pine or a ~36-triangle birch, far chunks (2560 m) a 5-triangle cone tinted per
## tree; the shader hides each tree in the wrong LOD by its own distance,
## so per tree there is exactly one mesh drawn. Density = the first share of each chunk's
## (shuffled) trees.

const STRIDE := 6  # x, y, z, yaw, scale, species
const FAR_COLORS: Array[Color] = [Color(0.055, 0.10, 0.05), Color(0.16, 0.22, 0.07)]

var density: float = 1.0
var near_mat: ShaderMaterial
var far_mat: ShaderMaterial

var _chunks: Array = []  # [ci, cj, start, count] per 640 m chunk
var _buffers: Array = []  # per 640 m chunk: [pine buffer, birch buffer], 12 floats per tree
var _far_buffers: Array[PackedFloat32Array] = []  # per chunk, 16 floats per tree (with colour)
var _near: Array = []  # per chunk: [pine MMI, birch MMI]
var _far: Dictionary = {}  # Vector2i (2560 m cell) -> MultiMeshInstance3D
var _far_members: Dictionary = {}  # Vector2i -> Array of chunk indices
var _total: int = 0


func build(meta: Dictionary) -> void:
	var forest: Dictionary = meta["forest"]
	var coarse: Dictionary = meta["coarse"]
	var x0: float = float(coarse["x0"])
	var z0: float = float(coarse["z0"])
	_chunks = forest["chunks"]
	var bytes := FileAccess.get_file_as_bytes(SpikeConfig.TERRAIN_DIR + "trees.bin")
	var data := bytes.to_float32_array()
	_total = data.size() / STRIDE

	var shader: Shader = load("res://shaders/tree.gdshader")
	near_mat = ShaderMaterial.new()
	near_mat.shader = shader
	near_mat.set_shader_parameter("lod_radius", SpikeConfig.TREE_NEAR_RADIUS)
	far_mat = ShaderMaterial.new()
	far_mat.shader = shader
	far_mat.set_shader_parameter("lod_radius", SpikeConfig.TREE_NEAR_RADIUS)
	far_mat.set_shader_parameter("is_far", true)
	var pine := _pine_mesh()
	var birch := _birch_mesh()
	var cone := _cone_mesh()
	var ratio: float = SpikeConfig.TREE_FAR_CHUNK
	var half_diag: float = SpikeConfig.TREE_NEAR_CHUNK * 0.75

	for k in _chunks.size():
		var c: Array = _chunks[k]
		var start: int = int(c[2])
		var count: int = int(c[3])
		var bufs: Array[PackedFloat32Array] = [PackedFloat32Array(), PackedFloat32Array()]
		var far := PackedFloat32Array()
		for t in count:
			var o: int = (start + t) * STRIDE
			var sp: int = int(data[o + 5])
			var b := Basis(Vector3.UP, data[o + 3]).scaled(Vector3.ONE * data[o + 4])
			var xf: Array[float] = [
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
				data[o + 2]
			]
			bufs[sp].append_array(PackedFloat32Array(xf))
			far.append_array(PackedFloat32Array(xf))
			var col: Color = FAR_COLORS[sp] * (0.85 + 0.3 * fposmod(data[o + 3] * 7.13, 1.0))
			far.append_array(PackedFloat32Array([col.r, col.g, col.b, 1.0]))
		_buffers.append(bufs)
		_far_buffers.append(far)

		var pair: Array[MultiMeshInstance3D] = []
		for sp in 2:
			var mmi := MultiMeshInstance3D.new()
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = pine if sp == 0 else birch
			mmi.multimesh = mm
			mmi.material_override = near_mat
			mmi.visibility_range_end = SpikeConfig.TREE_NEAR_RADIUS + half_diag
			mmi.visibility_range_end_margin = 40.0
			add_child(mmi)
			pair.append(mmi)
		_near.append(pair)

		var cx: float = x0 + (int(c[0]) + 0.5) * SpikeConfig.TREE_NEAR_CHUNK
		var cz: float = z0 + (int(c[1]) + 0.5) * SpikeConfig.TREE_NEAR_CHUNK
		var cell := Vector2i(int((cx - x0) / ratio), int((cz - z0) / ratio))
		if not _far.has(cell):
			var fm := MultiMeshInstance3D.new()
			var fmm := MultiMesh.new()
			fmm.transform_format = MultiMesh.TRANSFORM_3D
			fmm.use_colors = true
			fmm.mesh = cone
			fm.multimesh = fmm
			fm.material_override = far_mat
			fm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			fm.visibility_range_end = SpikeConfig.TREE_FAR_END
			add_child(fm)
			_far[cell] = fm
			_far_members[cell] = []
		(_far_members[cell] as Array).append(k)
	set_density(density)


func set_density(d: float) -> void:
	density = d
	for k in _near.size():
		for sp in 2:
			var buf: PackedFloat32Array = _buffers[k][sp]
			var n: int = int(ceil(buf.size() / 12.0 * density))
			var mm: MultiMesh = (_near[k][sp] as MultiMeshInstance3D).multimesh
			mm.instance_count = n
			if n > 0:
				mm.buffer = buf.slice(0, n * 12)
	for cell: Vector2i in _far:
		var acc := PackedFloat32Array()
		for k: int in _far_members[cell]:
			var buf: PackedFloat32Array = _far_buffers[k]
			var n: int = int(ceil(buf.size() / 16.0 * density))
			acc.append_array(buf.slice(0, n * 16))
		var fmm: MultiMesh = (_far[cell] as MultiMeshInstance3D).multimesh
		fmm.instance_count = acc.size() / 16
		if acc.size() > 0:
			fmm.buffer = acc


func set_shadows(on: bool) -> void:
	for pair: Array in _near:
		for mmi: MultiMeshInstance3D in pair:
			mmi.cast_shadow = (
				GeometryInstance3D.SHADOW_CASTING_SETTING_ON
				if on
				else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			)


func visible_trees() -> int:
	return int(ceil(_total * density))


func _process(_delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var p := cam.global_position
	near_mat.set_shader_parameter("lod_center", p)
	far_mat.set_shader_parameter("lod_center", p)


func _pine_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_prism(st, 0.22, 0.0, 2.6, 4, Color(0.20, 0.14, 0.09))
	_cone(st, 2.7, 1.4, 7.4, 7, Color(0.05, 0.095, 0.045))
	_cone(st, 2.05, 4.6, 10.4, 7, Color(0.058, 0.108, 0.05))
	_cone(st, 1.35, 7.6, 13.2, 7, Color(0.066, 0.12, 0.055))
	st.generate_normals()
	return st.commit()


func _cone_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_cone(st, 2.6, 0.6, 13.0, 5, Color(1.0, 1.0, 1.0))
	st.generate_normals()
	return st.commit()


## Birch: pale trunk and a rounded two-part crown (double cones), lighter yellow-green.
func _birch_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_prism(st, 0.14, 0.0, 6.0, 4, Color(0.78, 0.76, 0.70))
	var crown := Color(0.15, 0.21, 0.065)
	_cone(st, 2.3, 5.2, 3.0, 8, crown * 0.85)
	_cone(st, 2.3, 5.2, 10.5, 8, crown)
	st.generate_normals()
	return st.commit()


func _cone(st: SurfaceTool, r: float, y0: float, y1: float, sides: int, col: Color) -> void:
	for i in sides:
		var a0: float = TAU * i / sides
		var a1: float = TAU * (i + 1) / sides
		st.set_color(col * 0.8)
		st.add_vertex(Vector3(cos(a0) * r, y0, sin(a0) * r))
		st.set_color(col * 1.15)
		st.add_vertex(Vector3(0.0, y1, 0.0))
		st.set_color(col * 0.8)
		st.add_vertex(Vector3(cos(a1) * r, y0, sin(a1) * r))


func _prism(st: SurfaceTool, r: float, y0: float, y1: float, sides: int, col: Color) -> void:
	st.set_color(col)
	for i in sides:
		var a0: float = TAU * i / sides
		var a1: float = TAU * (i + 1) / sides
		var p0 := Vector3(cos(a0) * r, y0, sin(a0) * r)
		var p1 := Vector3(cos(a1) * r, y0, sin(a1) * r)
		var q0 := Vector3(cos(a0) * r, y1, sin(a0) * r)
		var q1 := Vector3(cos(a1) * r, y1, sin(a1) * r)
		st.add_vertex(p0)
		st.add_vertex(q0)
		st.add_vertex(p1)
		st.add_vertex(p1)
		st.add_vertex(q0)
		st.add_vertex(q1)
