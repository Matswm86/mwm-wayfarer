class_name CliffRocks
extends Node3D

## Rock meshes along the steep bands round the village (visual pass 2, Ultra). Placement baked by
## tools/terrain/npz_to_godot.py into assets/terrain/rocks.bin (x, y, z, normal, yaw, size; slopes
## 45-78 deg, half sunk into the face). Every REFRESH s the rocks are sorted by distance into one
## MultiMesh per model and LOD (LOD0 within ROCK_LOD_RANGES.x, LOD1 within .y, LOD2 within .z,
## none beyond), so a whole wall costs a handful of draws. Models: tools/spike/export_rocks.py
## stand-ins (Poly Haven rock_face_01/02, CC0) until the designer's cliff set lands.

const STRIDE := 8
const REFRESH := 0.4
const MODELS: Array[String] = ["rock_face_01", "rock_face_02"]

var _xf: Array[Transform3D] = []
var _model: PackedInt32Array = PackedInt32Array()
var _mm: Array = []  # per model: [lod0, lod1, lod2] MultiMeshInstance3D
var _timer: float = 0.0


func build() -> void:
	var data := (
		FileAccess.get_file_as_bytes(SpikeConfig.TERRAIN_DIR + "rocks.bin").to_float32_array()
	)
	for i in data.size() / STRIDE:
		var o: int = i * STRIDE
		var n := Vector3(data[o + 3], data[o + 4], data[o + 5])
		var up := (n + Vector3.UP).normalized()
		var b := Basis(Quaternion(Vector3.UP, up)) * Basis(Vector3.UP, data[o + 6])
		b = b.scaled(Vector3.ONE * data[o + 7])
		_xf.append(Transform3D(b, Vector3(data[o], data[o + 1], data[o + 2])))
		_model.append(i % MODELS.size())
	for name: String in MODELS:
		var root := (load("res://assets/models/rocks/%s.glb" % name) as PackedScene).instantiate()
		var lods: Array = []
		for k in 3:
			var mi := root.find_child("%s_LOD%d" % [name, k], true, false) as MeshInstance3D
			lods.append(_multimesh(_gneiss(mi.mesh)))
		root.free()
		_mm.append(lods)
	set_enabled(false)


func set_enabled(on: bool) -> void:
	visible = on
	_timer = 0.0
	if not on:
		for lods: Array in _mm:
			for mmi: MultiMeshInstance3D in lods:
				mmi.multimesh.instance_count = 0


func count() -> int:
	var n: int = 0
	for lods: Array in _mm:
		for mmi: MultiMeshInstance3D in lods:
			n += mmi.multimesh.instance_count
	return n


func _process(delta: float) -> void:
	if not visible:
		return
	_timer -= delta
	if _timer > 0.0:
		return
	_timer = REFRESH
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var c := cam.global_position
	var r: Vector3 = SpikeConfig.ROCK_LOD_RANGES
	var buckets: Array = []
	for m in MODELS.size():
		buckets.append([[], [], []])
	for i in _xf.size():
		var d: float = _xf[i].origin.distance_to(c)
		var lod: int = 0 if d < r.x else (1 if d < r.y else (2 if d < r.z else 3))
		if lod < 3:
			(buckets[_model[i]][lod] as Array).append(_xf[i])
	for m in MODELS.size():
		for k in 3:
			var list: Array = buckets[m][k]
			var mm: MultiMesh = (_mm[m][k] as MultiMeshInstance3D).multimesh
			mm.instance_count = list.size()
			for j in list.size():
				mm.set_instance_transform(j, list[j])


func _multimesh(mesh: Mesh) -> MultiMeshInstance3D:
	var mmi := MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mmi.multimesh = mm
	mmi.extra_cull_margin = 16384.0
	add_child(mmi)
	return mmi


## The scans are warm sandstone-grey; pull them toward the fjord's grey gneiss.
func _gneiss(src: Mesh) -> Mesh:
	var mesh := src.duplicate() as Mesh
	for s in mesh.get_surface_count():
		var m := mesh.surface_get_material(s) as StandardMaterial3D
		if m:
			m = m.duplicate() as StandardMaterial3D
			m.albedo_color = SpikeConfig.ROCK_TINT
			mesh.surface_set_material(s, m)
	return mesh
