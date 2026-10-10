class_name NearTrees
extends Node3D

## Real tree meshes near the camera (visual pass 2, Ultra): conifers within `radius` of the
## camera are drawn as geometry (LOD0 within SpikeConfig.TREE_LOD0_RADIUS, LOD1 beyond) instead
## of impostor quads; the impostor shader hides the same trees (Forest.set_geo_radius). The set
## is gathered from the forest's chunk buffers a few times a second on a worker thread (perf pass
## 3: the gather took about 0.9 ms on the laptop main thread, a frame spike every 0.25 s on the
## phone); the result is applied on the main thread when the task is done.
## Model: scots_pine_a, the graphic designer's card version of Poly Haven pine_tree_01 (CC0),
## tools/assets/cardify_tree.py; assets/models/trees/scots_pine/SOURCE.md.

const REFRESH := 0.25

var forest: Forest
var radius: float = 0.0
var _lod0: MultiMeshInstance3D
var _lod1: MultiMeshInstance3D
var _height: float = 20.0
var _timer: float = 0.0
var _task: int = -1
var _result: Array[PackedFloat32Array] = []


func build(f: Forest, scene_path: String) -> void:
	forest = f
	var root := (load(scene_path) as PackedScene).instantiate() as Node3D
	var meshes: Dictionary = {}
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		var key: String = "lod1" if String(mi.name).ends_with("LOD1") else "lod0"
		meshes[key] = _prepared(mi.mesh)
		if key == "lod0":
			_height = mi.get_aabb().end.y
	root.free()
	_lod0 = _multimesh(meshes["lod0"])
	_lod1 = _multimesh(meshes.get("lod1", meshes["lod0"]))
	set_radius(0.0)


## 0 turns the geometry trees off (every tree stays an impostor).
func set_radius(r: float) -> void:
	radius = r
	visible = r > 0.0
	forest.set_geo_radius(r)
	if not visible:
		_lod0.multimesh.instance_count = 0
		_lod1.multimesh.instance_count = 0
	_timer = 0.0


func _exit_tree() -> void:
	if _task >= 0:
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1


func _process(delta: float) -> void:
	if _task >= 0 and WorkerThreadPool.is_task_completed(_task):
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1
		if visible and _result.size() == 2:
			_fill(_lod0.multimesh, _result[0])
			_fill(_lod1.multimesh, _result[1])
	if not visible:
		return
	_timer -= delta
	if _timer > 0.0 or _task >= 0:
		return
	_timer = REFRESH
	var cam := get_viewport().get_camera_3d()
	if cam:
		var c: Vector3 = cam.global_position
		var chunks: Array[int] = forest.chunks_near(c, radius)
		_task = WorkerThreadPool.add_task(_gather_task.bind(c, chunks))


func _gather_task(c: Vector3, chunks: Array[int]) -> void:
	_result = _collect(c, chunks)


## Synchronous gather (tests and tools).
func _gather(c: Vector3) -> void:
	var r: Array[PackedFloat32Array] = _collect(c, forest.chunks_near(c, radius))
	_fill(_lod0.multimesh, r[0])
	_fill(_lod1.multimesh, r[1])


## Rows of the conifers within the radius, split LOD0 / LOD1. Reads only the forest's buffers,
## which never change after build (density is read as a count), so it is safe on a worker thread.
func _collect(c: Vector3, chunks: Array[int]) -> Array[PackedFloat32Array]:
	var near0 := PackedFloat32Array()
	var near1 := PackedFloat32Array()
	var r2: float = radius * radius
	var r0: float = SpikeConfig.TREE_LOD0_RADIUS
	var k: float = Forest.CONIFER_HEIGHT / _height
	for idx: int in chunks:
		var buf: PackedFloat32Array = forest.chunk_buffer(idx)
		var n: int = forest.chunk_visible_count(idx)
		for t in n:
			var o: int = t * Forest.FLOATS
			if buf[o + 12] > 3.5:  # broadleaf: no mesh yet, stays an impostor
				continue
			var dx: float = buf[o + 3] - c.x
			var dy: float = buf[o + 7] - c.y
			var dz: float = buf[o + 11] - c.z
			var d2: float = dx * dx + dy * dy + dz * dz
			if d2 >= r2:
				continue
			var row := PackedFloat32Array(
				[
					buf[o] * k,
					buf[o + 1] * k,
					buf[o + 2] * k,
					buf[o + 3],
					buf[o + 4] * k,
					buf[o + 5] * k,
					buf[o + 6] * k,
					buf[o + 7],
					buf[o + 8] * k,
					buf[o + 9] * k,
					buf[o + 10] * k,
					buf[o + 11]
				]
			)
			if d2 < r0 * r0:
				near0.append_array(row)
			else:
				near1.append_array(row)
	return [near0, near1]


func set_shadows(on: bool) -> void:
	for mmi: MultiMeshInstance3D in [_lod0, _lod1]:
		mmi.cast_shadow = (
			GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			if on
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		)


func count() -> int:
	return _lod0.multimesh.instance_count + _lod1.multimesh.instance_count


func _fill(mm: MultiMesh, data: PackedFloat32Array) -> void:
	mm.instance_count = data.size() / 12
	if data.size() > 0:
		mm.buffer = data


func _multimesh(mesh: Mesh) -> MultiMeshInstance3D:
	var mmi := MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mmi.multimesh = mm
	# instances span the whole near radius round the camera; never cull the node as a whole
	mmi.extra_cull_margin = 16384.0
	add_child(mmi)
	return mmi


## Leaves: two-sided cut-out cards lit through from behind (backlight), a soft rim; bark as is.
func _prepared(src: Mesh) -> Mesh:
	var mesh := src.duplicate() as Mesh
	for s in mesh.get_surface_count():
		var m := mesh.surface_get_material(s) as StandardMaterial3D
		if m == null:
			continue
		m = m.duplicate() as StandardMaterial3D
		if m.resource_name.contains("leaves"):
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			m.alpha_scissor_threshold = 0.4
			m.albedo_color = Color(0.85, 1.0, 0.8)
			# COLOR_0 = crown occlusion baked per card (tools/assets/cardify_tree.py)
			m.vertex_color_use_as_albedo = true
			m.backlight_enabled = true
			m.backlight = Color(0.16, 0.2, 0.06)
			# needles are not glossy: the default 0.5 specular turned the crowns sky-pale
			m.metallic_specular = 0.15
			m.rim_enabled = true
			m.rim = 0.25
			m.rim_tint = 0.6
		mesh.surface_set_material(s, m)
	return mesh
