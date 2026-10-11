extends Node

## Taps overlay buttons with synthetic screen touches (the event type a phone sends) and
## reports whether each button's action ran.

var main: Node


func _ready() -> void:
	main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	add_child(main)
	if not main.warm:
		await main.warmed_up
	for i in 10:
		await get_tree().process_frame
	await _tap("vsync")
	print("PROBE vsync_on after tap: ", main.vsync_on, " mode ", main.vsync_mode_name())
	await _tap("vsync")
	print("PROBE vsync_on after 2nd tap: ", main.vsync_on, " mode ", main.vsync_mode_name())
	# High -> Ultra (60 fps cap, softer shadows, near pine meshes, far grass) -> Low
	await _tap("preset")
	print(
		"PROBE preset after tap: ",
		SpikeConfig.PRESETS[main.preset_index]["name"],
		" max_fps ",
		Engine.max_fps,
		" near trees on ",
		main.near_trees.visible,
		" far grass on ",
		main.grass_far.visible
	)
	await _tap("preset")
	print(
		"PROBE preset after 2nd tap: ",
		SpikeConfig.PRESETS[main.preset_index]["name"],
		" max_fps ",
		Engine.max_fps
	)
	await _tap("forest")
	print("PROBE forest density after tap: ", main.forest.density)
	await _tap("foam")
	print("PROBE foam after tap: ", main.foam_on)
	await _tap("result")
	print("PROBE result tap ok")
	await _tap("parts")
	for i in 5:
		await get_tree().process_frame
	print("PROBE GPU parts running after tap: ", main.bench.running)
	while main.bench.running:
		await get_tree().process_frame
	print("PROBE GPU parts result: ", PerfOverlay._result.text.split("\n").slice(0, 4))
	# Low: the corner on its light LODs (no lightmapped house LOD0, no birch meshes)
	main.apply_preset(0)
	var house: Node3D = main.corner.get_node("Houses").get_child(0)
	var birch: Node3D = main.corner.get_node("Trees").get_child(0)
	print(
		"PROBE Low corner: house LOD0 visible ",
		house.get_node("LOD0").visible,
		", birch LOD0 visible ",
		birch.get_node("LOD0").visible
	)
	main.apply_preset(3)
	print("PROBE Ultra corner: house LOD0 visible ", house.get_node("LOD0").visible)
	var spawn: Vector3 = main.player.global_position
	await _tap("corner")
	for i in 5:
		await get_tree().process_frame
	print("PROBE corner bench running after tap: ", main.bench.running)
	var walked: float = 0.0
	while main.bench.running:
		await get_tree().process_frame
		walked = maxf(walked, main.player.global_position.distance_to(spawn))
	var pp: Vector3 = main.player.global_position
	var back := Vector2(pp.x - spawn.x, pp.z - spawn.z)
	# horizontal: the reset puts him at the spawn height plus 0.5 m and he drops to the ground
	print("PROBE corner bench: player went %.0f m from the spawn, back at the spawn %s" % [
		walked, back.length() < 0.5])
	print("PROBE corner bench result: ", PerfOverlay._result.text.split("\n").slice(0, 5))
	await _tap("bench_all")
	for i in 5:
		await get_tree().process_frame
	print("PROBE bench running after tap: ", main.bench.running)
	get_tree().quit()


func _tap(id: String) -> void:
	var b: Button = PerfOverlay._buttons[id]
	var c: Vector2 = b.get_global_rect().get_center()
	print(
		"PROBE tap ", id, " at ", c, " disabled=", b.disabled, " visible=", b.is_visible_in_tree()
	)
	var e := InputEventScreenTouch.new()
	e.index = 0
	e.position = c
	e.pressed = true
	Input.parse_input_event(e)
	await get_tree().process_frame
	var r := InputEventScreenTouch.new()
	r.index = 0
	r.position = c
	r.pressed = false
	Input.parse_input_event(r)
	for i in 3:
		await get_tree().process_frame
