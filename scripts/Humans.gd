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
