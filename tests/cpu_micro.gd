extends Node

## Dev-only: times each CPU system directly (repeated calls, Time.get_ticks_usec), so the result
## does not depend on the render sync or on other load on the machine as much as frame times do.
## Run headless: godot --headless --audio-driver Dummy res://tests/cpu_micro.tscn

var main: Node3D


func _ready() -> void:
	main = load("res://scenes/Main.tscn").instantiate()
	add_child(main)
	if not main.warm:
		await main.warmed_up
	main.apply_preset(3)
	main.bench.place(0.08)
	main.bench.camera.current = true
	for i in 10:
		await get_tree().process_frame
	_time("player move_and_slide", 200, func() -> void: main.player.move_and_slide())
	_time("player _physics_process", 200, func() -> void: main.player._physics_process(1.0 / 60.0))
	_time("wildlife _process", 200, func() -> void: main.wildlife._process(1.0 / 60.0))
	var anims: Array[Node] = main.find_children("*", "AnimationPlayer", true, false)
	_time(
		"all %d AnimationPlayers advance" % anims.size(),
		50,
		func() -> void:
			for a: AnimationPlayer in anims:
				if a.active:
					a.advance(1.0 / 60.0)
	)
	var active: int = 0
	for a: AnimationPlayer in anims:
		active += 1 if a.active else 0
	print("MICRO active AnimationPlayers: %d of %d" % [active, anims.size()])
	var trees: Array[Node] = main.find_children("*", "AnimationTree", true, false)
	_time(
		"AnimationTree advance",
		100,
		func() -> void:
			for t: AnimationTree in trees:
				t.advance(1.0 / 60.0)
	)
	var c: Vector3 = main.player.global_position
	_time("near_trees _gather (70 m)", 20, func() -> void: main.near_trees._gather(c))
	_time(
		"grass _process x2",
		200,
		func() -> void:
			main.grass._process(0.016)
			main.grass_far._process(0.016)
	)
	_time("forest _process", 200, func() -> void: main.forest._process(0.016))
	_time("overlay _process", 200, func() -> void: PerfOverlay._process(0.016))
	_time(
		"terrain height_at x100",
		50,
		func() -> void:
			for i in 100:
				main.terrain.height_at(c.x + i, c.z)
	)
	print("MICRO DONE")
	get_tree().quit()


func _time(label: String, n: int, f: Callable) -> void:
	f.call()
	var t0: int = Time.get_ticks_usec()
	for i in n:
		f.call()
	var us: float = float(Time.get_ticks_usec() - t0) / n
	print("MICRO %-36s %8.1f us per call" % [label, us])
