class_name NearTrees
extends Node3D

## Real tree meshes near the camera (visual pass 2, Ultra): conifers within `radius` of the
## camera are drawn as geometry (LOD0 within SpikeConfig.TREE_LOD0_RADIUS, LOD1 beyond) instead
## of impostor quads; the impostor shader hides the same trees (Forest.set_geo_radius). The set
## is gathered from the forest's chunk buffers a few times a second on a worker thread (perf pass
## 3: the gather took about 0.9 ms on the laptop main thread, a frame spike every 0.25 s on the
## phone); the result is applied on the main thread when the task is done.
## Models (pass 3): one per forest variant (SpikeConfig.TREE_MESHES; the forest's variants 0-1 are
## pines, 2-3 firs): the graphic designer's scots_pine a/b (card version of Poly Haven pine_tree_01,
## CC0) and norway_spruce a/b (PlantCatalog, CC BY 4.0), each scaled to the forest's tree height.

const REFRESH := 0.25

var forest: Forest
var radius: float = 0.0
var _lod0: Array[MultiMeshInstance3D] = []
var _lod1: Array[MultiMeshInstance3D] = []
## Shadow-only copies of every near tree with the light LOD (perf pass 3: LOD0 cards in four shadow
## splits cost more than the trees on screen).
var _shadow: Array[MultiMeshInstance3D] = []
var _height: PackedFloat32Array = PackedFloat32Array()
var _timer: float = 0.0
var _task: int = -1
var _result: Array[PackedFloat32Array] = []


func build(f: Forest, scene_paths: Array[String]) -> void:
	forest = f
	for scene_path in scene_paths:
		var root := (load(scene_path) as PackedScene).instantiate() as Node3D
		var meshes: Dictionary = {}
		var h: float = 20.0
		for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
			var key: String = "lod1" if String(mi.name).ends_with("LOD1") else "lod0"
			meshes[key] = _prepared(mi.mesh)
			if key == "lod0":
				h = mi.get_aabb().end.y
		root.free()
		_height.append(h)
		_lod0.append(_multimesh(meshes["lod0"]))
		_lod1.append(_multimesh(meshes.get("lod1", meshes["lod0"])))
		_lod0.back().cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_lod1.back().cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var sh := _multimesh(meshes.get("lod1", meshes["lod0"]))
		sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		_shadow.append(sh)
	set_radius(0.0)


## 0 turns the geometry trees off (every tree stays an impostor).
func set_radius(r: float) -> void:
	radius = r
	visible = r > 0.0
	forest.set_geo_radius(r)
	if not visible:
		for v in _lod0.size():
			_lod0[v].multimesh.instance_count = 0
			_lod1[v].multimesh.instance_count = 0
			_shadow[v].multimesh.instance_count = 0
	_timer = 0.0


func _exit_tree() -> void:
	if _task >= 0:
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1


func _process(delta: float) -> void:
	if _task >= 0 and WorkerThreadPool.is_task_completed(_task):
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1
		if visible and _result.size() == 2 * _lod0.size():
			_apply(_result)
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
	_apply(_collect(c, forest.chunks_near(c, radius)))


func _apply(r: Array[PackedFloat32Array]) -> void:
	for v in _lod0.size():
		_fill(_lod0[v].multimesh, r[2 * v])
		_fill(_lod1[v].multimesh, r[2 * v + 1])
		_fill(_shadow[v].multimesh, r[2 * v] + r[2 * v + 1])


## Rows of the conifers within the radius, per model:
## [model0 LOD0, model0 LOD1, model1 LOD0, ...]. Reads only the forest's buffers,
## which never change after build (density is read as a count), so it is safe on a worker thread.
func _collect(c: Vector3, chunks: Array[int]) -> Array[PackedFloat32Array]:
	var nv: int = _lod0.size()
	var out: Array[PackedFloat32Array] = []
	for i in 2 * nv:
		out.append(PackedFloat32Array())
	var r2: float = radius * radius
	var r0: float = SpikeConfig.TREE_LOD0_RADIUS
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
			var v: int = mini(int(buf[o + 12]), nv - 1)
			var k: float = Forest.CONIFER_HEIGHT / _height[v]
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
			out[2 * v + (0 if d2 < r0 * r0 else 1)].append_array(row)
	return out


func set_shadows(on: bool) -> void:
	for mmi: MultiMeshInstance3D in _shadow:
		mmi.visible = on


func count() -> int:
	var n: int = 0
	for v in _lod0.size():
		n += _lod0[v].multimesh.instance_count + _lod1[v].multimesh.instance_count
	return n


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
