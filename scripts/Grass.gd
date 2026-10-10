class_name Grass
extends MultiMeshInstance3D

## Grass blades on a world-aligned grid within GRASS_RADIUS of the player. The node jumps in
## GRASS_SPACING steps so the grid points (and the hashed jitter in the shader) stay fixed in
## the world. Density = share of the shuffled instances drawn.

const CLUMP_BLADES := 5

var target: Node3D
var mat: ShaderMaterial
var _count: int = 0


func build(terrain: Terrain) -> void:
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/grass.gdshader")
	terrain.apply_height_params(mat)
	mat.set_shader_parameter("grass_radius", SpikeConfig.GRASS_RADIUS)
	mat.set_shader_parameter("grid_spacing", SpikeConfig.GRASS_SPACING)
	mat.set_shader_parameter("grass_tex", load("res://assets/textures/grass_albedo.jpg"))
	material_override = mat
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

	var pts: Array[Vector3] = []
	var r: float = SpikeConfig.GRASS_RADIUS
	var s: float = SpikeConfig.GRASS_SPACING
	var n: int = int(r / s)
	for j in range(-n, n + 1):
		for i in range(-n, n + 1):
			var p := Vector3(i * s, 0.0, j * s)
			if p.length() <= r:
				pts.append(p)
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for k in range(pts.size() - 1, 0, -1):
		var o: int = rng.randi_range(0, k)
		var tmp: Vector3 = pts[k]
		pts[k] = pts[o]
		pts[o] = tmp
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _blade_mesh()
	mm.instance_count = pts.size()
	for k in pts.size():
		mm.set_instance_transform(k, Transform3D(Basis.IDENTITY, pts[k]))
	multimesh = mm
	_count = pts.size()
	# blades sit anywhere from the shore to the knolls; the node stays at y = 0
	custom_aabb = AABB(Vector3(-r, -20.0, -r), Vector3(2.0 * r, 700.0, 2.0 * r))


func set_density(d: float) -> void:
	visible = d > 0.0
	multimesh.visible_instance_count = int(_count * d)


func blade_count() -> int:
	return multimesh.visible_instance_count if visible else 0


func _process(_delta: float) -> void:
	if target == null or not visible:
		return
	var s: float = SpikeConfig.GRASS_SPACING
	var p := target.global_position
	global_position = Vector3(snappedf(p.x, s), 0.0, snappedf(p.z, s))
	mat.set_shader_parameter("grass_center", p)


## One clump: CLUMP_BLADES thin tapered blades, roots within 8 cm, tips leaning outward.
## UV.x = per-blade random value, UV.y = 0 root .. 1 tip (grass.gdshader contract).
func _blade_mesh() -> ArrayMesh:
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var normals := PackedVector3Array()
	for b in CLUMP_BLADES:
		var a: float = TAU * (b + rng.randf() * 0.6) / CLUMP_BLADES
		var dir := Vector3(cos(a), 0.0, sin(a))
		var side := Vector3(-dir.z, 0.0, dir.x)
		var root := dir * rng.randf_range(0.0, 0.08)
		var tall: float = rng.randf_range(0.28, 0.5)
		var lean: float = rng.randf_range(0.05, 0.16)
		var w: float = rng.randf_range(0.018, 0.03)
		var tip := root + dir * lean + Vector3(0.0, tall, 0.0)
		var r: float = rng.randf()
		verts.append_array([root - side * w, tip, root + side * w])
		uvs.append_array([Vector2(r, 0.0), Vector2(r, 1.0), Vector2(r, 0.0)])
		normals.append_array([dir, dir, dir])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh
