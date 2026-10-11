class_name Humans
extends RefCounted

## Helpers for the MakeHuman glTF characters (assets/models/*.glb).


static func find_player(root: Node) -> AnimationPlayer:
	if root is AnimationPlayer:
		return root as AnimationPlayer
	for c in root.get_children():
		var a := find_player(c)
		if a:
			return a
	return null


static func loop_all(anim: AnimationPlayer) -> void:
	if anim == null:
		return
	for lib_name: StringName in anim.get_animation_library_list():
		var lib := anim.get_animation_library(lib_name)
		for a_name: StringName in lib.get_animation_list():
			lib.get_animation(a_name).loop_mode = Animation.LOOP_LINEAR


## Skin that does not look like plastic on the Mobile renderer (no subsurface scattering there):
## wrapped diffuse so the light bleeds past the terminator, a red backlight for light through
## ears and fingers, a soft rim, low specular. Applied to every surface whose material name
## contains one of SpikeConfig.SKIN_MATERIALS.
static func skin(root: Node) -> void:
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		for s in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(s) as StandardMaterial3D
			if src == null or not _is_skin(src.resource_name):
				continue
			var m := src.duplicate() as StandardMaterial3D
			m.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT_WRAP
			m.roughness = 0.55
			m.metallic_specular = 0.35
			m.backlight_enabled = true
			m.backlight = SpikeConfig.SKIN_BACKLIGHT
			m.rim_enabled = true
			m.rim = 0.2
			m.rim_tint = 0.4
			mi.set_surface_override_material(s, m)


static func _is_skin(material_name: String) -> bool:
	for key: String in SpikeConfig.SKIN_MATERIALS:
		if material_name.to_lower().contains(key):
			return true
	return false


## Idle / walk / run blended by speed (m/s) through an AnimationTree. Clips missing from the model
## fall back: run -> walk played faster. Returns the tree; set "parameters/move/blend_position".
## points: [clip, speed m/s, playback rate] (default: idle / walk / run of the MakeHuman rig).
static func locomotion(anim: AnimationPlayer, points: Array = []) -> AnimationTree:
	if anim == null:
		return null
	var names: PackedStringArray = anim.get_animation_list()
	var space := AnimationNodeBlendSpace1D.new()
	space.min_space = 0.0
	space.max_space = SpikeConfig.PLAYER_RUN
	var rates: Array[float] = []
	if points.is_empty():
		points = [
			["idle", 0.0, 1.0],
			["walk", SpikeConfig.PLAYER_WALK, SpikeConfig.ANIM_WALK_RATE],
			["run", SpikeConfig.PLAYER_RUN, 1.0]
		]
	for p: Array in points:
		var clip: String = str(p[0])
		var rate: float = float(p[2])
		if not names.has(clip) and clip == "run" and names.has("walk"):
			clip = "walk"
			rate = SpikeConfig.ANIM_WALK_RATE * SpikeConfig.PLAYER_RUN / SpikeConfig.PLAYER_WALK
		if not names.has(clip):
			continue
		var node := AnimationNodeAnimation.new()
		node.animation = clip
		var blend := AnimationNodeBlendTree.new()
		blend.add_node("clip", node)
		var scale := AnimationNodeTimeScale.new()
		blend.add_node("rate", scale)
		blend.connect_node("rate", 0, "clip")
		blend.connect_node("output", 0, "rate")
		space.add_blend_point(blend, float(p[1]))
		rates.append(rate)
	var root := AnimationNodeBlendTree.new()
	root.add_node("move", space)
	root.connect_node("output", 0, "move")
	var tree := AnimationTree.new()
	tree.tree_root = root
	anim.get_parent().add_child(tree)
	tree.anim_player = tree.get_path_to(anim)
	# per-point playback rate (run from a sped-up walk)
	for i in rates.size():
		tree.set("parameters/move/%d/rate/scale" % i, rates[i])
	tree.active = true
	return tree
