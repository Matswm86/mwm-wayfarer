class_name Lighting
extends RefCounted

## Cheap stand-ins for what the Mobile renderer lacks (no SSAO, no contact shadows, no GI):
## soft dark decals under animals, characters and houses (ambient occlusion where they meet the
## ground), and the box reflection probe over the village. Numbers in SpikeConfig.

static var _blob: GradientTexture2D
static var _box: GradientTexture2D


## A soft round contact shadow under `node` (an animal or a character), `radius` metres, that
## follows it. Faded out with distance so far animals cost nothing.
static func contact_shadow(node: Node3D, radius: float, strength: float) -> Decal:
	var d := Decal.new()
	d.name = "ContactShadow"
	d.texture_albedo = _round()
	d.modulate = Color(0.0, 0.0, 0.0, strength)
	d.albedo_mix = 1.0
	d.normal_fade = 0.3
	d.upper_fade = 0.6
	d.lower_fade = 0.6
	d.distance_fade_enabled = true
	d.distance_fade_begin = SpikeConfig.CONTACT_FADE_BEGIN
	d.distance_fade_length = 20.0
	# the decal darkens the ground and the grass only, never the animal's own legs
	d.cull_mask = 1
	for gi: GeometryInstance3D in node.find_children("*", "GeometryInstance3D", true, false):
		gi.layers = SpikeConfig.ACTOR_LAYER
	node.add_child(d)
	# the decal lives in the node's frame; undo the model's own scale so the size is in metres
	var s: float = maxf(node.global_transform.basis.get_scale().x, 1e-4)
	d.size = Vector3(radius * 2.0, 1.6, radius * 2.0) / s
	d.position = Vector3(0.0, 0.2 / s, 0.0)
	return d


## A soft rectangular occlusion skirt round a house footprint (w x d metres, yaw degrees).
static func footprint_shadow(parent: Node3D, pos: Vector3, w: float, dd: float, yaw: float) -> void:
	var d := Decal.new()
	d.texture_albedo = _square()
	d.modulate = Color(0.0, 0.0, 0.0, SpikeConfig.HOUSE_AO_STRENGTH)
	d.size = Vector3(w + 2.4, 4.0, dd + 2.4)
	d.normal_fade = 0.3
	d.distance_fade_enabled = true
	d.distance_fade_begin = 180.0
	d.distance_fade_length = 60.0
	parent.add_child(d)
	d.global_position = pos + Vector3(0.0, 0.5, 0.0)
	d.rotation.y = deg_to_rad(yaw)


static func _round() -> GradientTexture2D:
	if _blob:
		return _blob
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.45, Color(1, 1, 1, 0.7))
	_blob = GradientTexture2D.new()
	_blob.gradient = g
	_blob.fill = GradientTexture2D.FILL_RADIAL
	_blob.fill_from = Vector2(0.5, 0.5)
	_blob.fill_to = Vector2(1.0, 0.5)
	_blob.width = 128
	_blob.height = 128
	return _blob


## Dark in the middle, fading over the outer metre or so (the footprint plus 1.2 m each side).
static func _square() -> GradientTexture2D:
	if _box:
		return _box
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.8, Color(1, 1, 1, 0.75))
	_box = GradientTexture2D.new()
	_box.gradient = g
	_box.fill = GradientTexture2D.FILL_SQUARE
	_box.fill_from = Vector2(0.5, 0.5)
	_box.fill_to = Vector2(1.0, 0.5)
	_box.width = 128
	_box.height = 128
	return _box


## Box-projected probe over the village street: houses, pier and boats reflect their
## neighbours (windows, wet boards) instead of the open sky.
static func village_probe(parent: Node3D) -> ReflectionProbe:
	var r: Vector4 = SpikeConfig.VILLAGE_PROBE
	var probe := ReflectionProbe.new()
	probe.name = "VillageProbe"
	probe.update_mode = ReflectionProbe.UPDATE_ONCE
	probe.size = Vector3(r.z, 60.0, r.w)
	probe.position = Vector3(r.x, SpikeConfig.VILLAGE_PROBE_HEIGHT, r.y)
	probe.box_projection = true
	probe.max_distance = 3000.0
	probe.blend_distance = 20.0
	probe.intensity = 1.0
	probe.ambient_mode = ReflectionProbe.AMBIENT_DISABLED
	parent.add_child(probe)
	return probe
