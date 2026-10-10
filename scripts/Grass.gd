class_name Grass
extends MultiMeshInstance3D

## Ground cover (grass clumps, tall dry grass, ferns, shrubs as crossed cards from Poly Haven
## plant scans, shaders/ground_cover.gdshader) on a world-aligned grid within GRASS_RADIUS of the
## player. The node jumps in GRASS_SPACING steps so the grid points (and the hashed choice of
## plant in the shader) stay fixed in the world. Density = share of the shuffled instances drawn.

const CARDS := "res://assets/models/ground/"
## Cumulative pick weights per card (ground_cards.json order): short grass x2, tall grass x2,
## fern, shrub.
const CARD_PICK: Array[float] = [0.34, 0.68, 0.82, 0.92, 0.96, 1.0]
## Per card: scale (short grass doubled so tufts merge into a sward) and brightness.
const CARD_SCALE: Array[float] = [2.2, 2.2, 1.0, 1.0, 0.8, 1.0]
const CARD_GAIN: Array[float] = [1.9, 1.9, 1.0, 1.0, 1.2, 1.0]

var target: Node3D
var mat: ShaderMaterial
var _count: int = 0


func build(terrain: Terrain) -> void:
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/ground_cover.gdshader")
	terrain.apply_height_params(mat)
	terrain.apply_light_params(mat)
	mat.set_shader_parameter("grass_radius", SpikeConfig.GRASS_RADIUS)
	mat.set_shader_parameter("grid_spacing", SpikeConfig.GRASS_SPACING)
	mat.set_shader_parameter("cards", load(CARDS + "ground_cards.png"))
	var info: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string(CARDS + "ground_cards.json")
	)
	var sizes := PackedFloat32Array()
	for c: Dictionary in info["cards"]:
		sizes.append(float(c["size_m"]))
	mat.set_shader_parameter("card_count", float(sizes.size()))
	mat.set_shader_parameter("card_size", sizes)
	mat.set_shader_parameter("card_pick", PackedFloat32Array(CARD_PICK))
	mat.set_shader_parameter("card_scale", PackedFloat32Array(CARD_SCALE))
	mat.set_shader_parameter("card_gain", PackedFloat32Array(CARD_GAIN))
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
	mm.mesh = _card_mesh()
	mm.instance_count = pts.size()
	for k in pts.size():
		mm.set_instance_transform(k, Transform3D(Basis.IDENTITY, pts[k]))
	multimesh = mm
	_count = pts.size()
	# plants sit anywhere from the shore to the knolls; the node stays at y = 0
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


## Two crossed unit cards, x -0.5..0.5, y 0..1 (ground_cover.gdshader contract).
func _card_mesh() -> ArrayMesh:
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	for q in 2:
		var d := Vector3(1.0, 0.0, 0.0) if q == 0 else Vector3(0.0, 0.0, 1.0)
		var a := -d * 0.5
		var b := d * 0.5
		var up := Vector3(0.0, 1.0, 0.0)
		verts.append_array([a, b, b + up, a, b + up, a + up])
		uvs.append_array(
			[
				Vector2(0, 1),
				Vector2(1, 1),
				Vector2(1, 0),
				Vector2(0, 1),
				Vector2(1, 0),
				Vector2(0, 0)
			]
		)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh
