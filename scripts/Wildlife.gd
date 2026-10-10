class_name Wildlife
extends Node3D

## Valley wildlife (GDD: animals graze, flee or ignore; no combat). Rigged Sketchfab models from
## the owner (assets/models/animals/, slimmed by tools/spike/export_animals.py; authors and
## licences in assets/models/animals/CREDITS.md). Ground animals graze, wander inside their
## area and flee from the player; birds circle. Placement, sizes and counts per preset live in
## SpikeConfig.WILDLIFE. Far animals stop animating and are culled by visibility range.

const DIR := "res://assets/models/animals/"

var target: Node3D
var terrain: Terrain
var animals: Array[Animal] = []
var _rng := RandomNumberGenerator.new()


class Animal:
	extends RefCounted
	var node: Node3D
	var anim: AnimationPlayer
	var spec: Dictionary
	var clips: Dictionary
	var home: Vector3
	var goal: Vector3
	var state: String = "graze"
	var timer: float = 0.0
	var angle: float = 0.0
	var tier: int = 0


func build(t: Terrain) -> void:
	terrain = t
	_rng.seed = 2026
	var info: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR + "animals.json"))
	for spec: Dictionary in SpikeConfig.WILDLIFE:
		var species: String = spec["species"]
		var scene := load(DIR + species + ".glb") as PackedScene
		var clips: Dictionary = (info[species] as Dictionary)["clips"]
		for i in int(spec["count"]):
			var a := Animal.new()
			a.spec = spec
			a.clips = clips
			a.tier = 0 if i < int(spec["low"]) else 1
			a.node = scene.instantiate() as Node3D
			a.node.name = "%s_%d" % [species, i]
			add_child(a.node)
			_fit_size(a.node, float(spec["size"]))
			_fur(a.node)
			if not spec.has("fly"):
				Lighting.contact_shadow(
					a.node, float(spec["size"]) * 0.42, SpikeConfig.CONTACT_STRENGTH
				)
			_set_ranges(a.node, float(spec["range"]))
			a.anim = Humans.find_player(a.node)
			Humans.loop_all(a.anim)
			var c: Array = spec["area"]
			a.home = Vector3(float(c[0]), 0.0, float(c[1]))
			a.angle = _rng.randf() * TAU
			if spec.has("fly"):
				a.state = "fly"
				_play(a, "fly", 1.0)
			else:
				a.node.global_position = _ground_point(a.home, float(spec["radius"]))
				a.node.rotation.y = _rng.randf() * TAU
				a.timer = _rng.randf_range(2.0, 8.0)
				_play(a, "graze", 1.0)
				if a.anim:
					a.anim.seek(_rng.randf() * 3.0, true)
			animals.append(a)


## Low preset keeps only the first animals of each kind (draw call budget).
func set_density(full: bool) -> void:
	for a in animals:
		a.node.visible = full or a.tier == 0


func count_visible() -> int:
	var n: int = 0
	for a in animals:
		n += 1 if a.node.visible else 0
	return n


func _process(delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	var player_pos: Vector3 = target.global_position if target else Vector3.INF
	for a in animals:
		if not a.node.visible:
			continue
		if cam and a.anim:
			var far: bool = cam.global_position.distance_to(a.node.global_position) > 350.0
			a.anim.active = not far
		if a.state == "fly":
			_fly(a, delta)
		else:
			_ground(a, delta, player_pos)


func _fly(a: Animal, delta: float) -> void:
	var r: float = float(a.spec["radius"])
	var speed: float = float(a.spec["speed"])
	a.angle += speed / r * delta * (1.0 if a.home.x >= 0.0 else -1.0)
	var alt: float = float(a.spec["fly"]) + 8.0 * sin(a.angle * 0.7 + float(a.node.get_index()))
	var p := a.home + Vector3(cos(a.angle) * r, alt, sin(a.angle) * r)
	var ahead := a.home + Vector3(cos(a.angle + 0.05) * r, alt, sin(a.angle + 0.05) * r)
	a.node.global_position = p
	a.node.look_at(ahead, Vector3.UP, true)
	a.node.rotate_object_local(Vector3.FORWARD, 0.35)  # bank into the turn


func _ground(a: Animal, delta: float, player_pos: Vector3) -> void:
	var pos := a.node.global_position
	var flee_dist: float = float(a.spec["flee"])
	if flee_dist > 0.0 and pos.distance_to(player_pos) < flee_dist and a.state != "flee":
		var away := pos - player_pos
		away.y = 0.0
		a.goal = pos + away.normalized() * flee_dist * 2.0
		a.state = "flee"
		a.timer = 6.0
		_play(a, "run", 1.6)
	a.timer -= delta
	match a.state:
		"graze":
			if a.timer <= 0.0:
				a.goal = _ground_point(a.home, float(a.spec["radius"]))
				a.state = "walk"
				a.timer = 25.0
				_play(a, "walk", 1.0)
		"walk", "flee":
			var speed: float = float(a.spec["walk"]) * (2.6 if a.state == "flee" else 1.0)
			var to := a.goal - pos
			to.y = 0.0
			if to.length() < 1.0 or a.timer <= 0.0:
				a.state = "graze"
				a.timer = _rng.randf_range(5.0, 14.0)
				_play(a, "graze", 1.0)
				return
			var step: Vector3 = to.normalized() * minf(speed * delta, to.length())
			var nxt := pos + step
			nxt.y = terrain.height_at(nxt.x, nxt.z)
			if nxt.y < 0.3:
				a.goal = _ground_point(a.home, float(a.spec["radius"]))
				return
			a.node.global_position = nxt
			var want: float = atan2(step.x, step.z)
			a.node.rotation.y = lerp_angle(a.node.rotation.y, want, minf(1.0, delta * 4.0))


## Plays the clip for a role, falling back to walk / idle / graze, whichever the model has.
func _play(a: Animal, role: String, speed: float) -> void:
	if a.anim == null:
		return
	var order: Dictionary = {
		"graze": ["graze", "idle"],
		"walk": ["walk"],
		"run": ["run", "walk"],
		"fly": ["fly"],
	}
	for r: String in order.get(role, [role]):
		if a.clips.has(r):
			var clip: String = a.clips[r]
			var found := _clip_name(a.anim, clip)
			if found != "":
				a.anim.play(found, 0.4, speed)
				return


func _clip_name(anim: AnimationPlayer, clip: String) -> String:
	for n: StringName in anim.get_animation_list():
		if String(n) == clip or String(n).ends_with("/" + clip):
			return String(n)
	return ""


func _ground_point(centre: Vector3, radius: float) -> Vector3:
	for i in 40:
		var ang: float = _rng.randf() * TAU
		var d: float = sqrt(_rng.randf()) * radius
		var x: float = centre.x + cos(ang) * d
		var z: float = centre.z + sin(ang) * d
		var h: float = terrain.height_at(x, z)
		var hx: float = terrain.height_at(x + 2.0, z)
		var hz: float = terrain.height_at(x, z + 2.0)
		var slope: float = maxf(absf(hx - h), absf(hz - h)) / 2.0
		if h > 1.0 and slope < 0.45:
			return Vector3(x, h, z)
	return Vector3(centre.x, terrain.height_at(centre.x, centre.z), centre.z)


## Scales the model so its longest side is about `size` metres. Measured on the skeleton's bones
## in the rest pose (the skinned meshes' own boxes are in bind space and unreliable), plus 15 %
## for hooves, ears and fur beyond the outermost joints.
func _fit_size(root: Node3D, size: float) -> void:
	var skel := root.find_children("*", "Skeleton3D", true, false)
	if skel.is_empty():
		return
	var sk := skel[0] as Skeleton3D
	var box := AABB(sk.global_transform * sk.get_bone_global_rest(0).origin, Vector3.ZERO)
	for b in sk.get_bone_count():
		box = box.expand(sk.global_transform * sk.get_bone_global_rest(b).origin)
	var longest: float = maxf(box.size.x, maxf(box.size.y, box.size.z)) * 1.15
	if longest > 0.0:
		root.scale = Vector3.ONE * (size / longest)
	print("WILDLIFE %s bones span %.2f -> scale %.4f" % [root.name, longest, root.scale.x])


## Rough fur instead of the models' glossy defaults (roughness 0.6, specular 0.5 reflected the
## sky and tinted the does blue), with a soft rim like light caught in the coat.
func _fur(root: Node3D) -> void:
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		for s in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(s) as StandardMaterial3D
			if src == null:
				continue
			var m := src.duplicate() as StandardMaterial3D
			m.roughness = SpikeConfig.FUR_ROUGHNESS
			m.metallic_specular = SpikeConfig.FUR_SPECULAR
			m.rim_enabled = true
			m.rim = SpikeConfig.FUR_RIM
			m.rim_tint = 0.7
			mi.set_surface_override_material(s, m)


func _set_ranges(root: Node3D, end: float) -> void:
	for gi: GeometryInstance3D in root.find_children("*", "GeometryInstance3D", true, false):
		gi.visibility_range_end = end
		gi.visibility_range_end_margin = end * 0.1
		# skinned boxes are in bind space; a margin keeps the animal from being culled by mistake
		gi.extra_cull_margin = 4.0
