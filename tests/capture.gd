extends Node

## Dev-only screenshot bot. Run under Xvfb with CAPTURE_DIR set (see game-studio CLAUDE.md).
## Shots: spawn view and a high view over the fjord at the Low and High presets, plus a close
## look at a fjord wall (LOD cracks) and the joystick drawn. Then a short bench per preset that
## logs draw calls and primitives (laptop fps means nothing for phones).
## CAPTURE_BENCH_SECONDS sets the bench length (default 20, 0 = skip).
## CAPTURE_HIDE_UI=1 hides the readout and buttons (clean frames for look comparisons; the
## draw and primitive counts are still printed per shot).

var out_dir: String = OS.get_environment("CAPTURE_DIR")
var main: Node3D


func _ready() -> void:
	main = load("res://scenes/Main.tscn").instantiate()
	add_child(main)
	if not main.warm:
		await main.warmed_up
	if OS.get_environment("CAPTURE_HIDE_UI") == "1":
		PerfOverlay.set_ui_visible(false)
	await _frames(30)
	var path: Array = main.terrain.meta["bench_path"]
	var high := _v(path[7])
	var spawn_look := _v(path[1]) + Vector3(0.0, -60.0, -300.0)
	var wall_pos := _v(path[4]) + Vector3(120.0, -60.0, 0.0)

	for preset in [2, 0, 1]:
		main.apply_preset(preset)
		var tag: String = str(SpikeConfig.PRESETS[preset]["name"]).to_lower()
		main.player.camera.current = true
		await _frames(45)
		await _shot("spawn_%s" % tag)
		if preset == 1:
			continue
		await _village_street(tag)
		var ing: Node3D = main.get_node("Ingrid")
		var ip := ing.global_position
		main.bench.view(ip + Vector3(-5.0, 2.2, 7.0), ip + Vector3(0.0, 1.3, 0.0))
		await _frames(45)
		await _shot("ingrid_dock_%s" % tag)
		if preset == 2:
			var fall: Array = main.terrain.meta["waterfall"]
			var top := _v(fall[0])
			main.bench.view(Vector3(250.0, 12.0, -230.0), top.lerp(_v(fall[fall.size() - 1]), 0.6))
			await _frames(60)
			await _shot("waterfall_from_village_high")
		main.bench.view(high, spawn_look)
		await _frames(45)
		await _shot("fjord_high_view_%s" % tag)
		main.bench.view(wall_pos, wall_pos + Vector3(500.0, 120.0, -200.0))
		await _frames(45)
		await _shot("wall_close_%s" % tag)

	# walk forward for 2 s with the stick held, to prove movement and collision
	main.apply_preset(2)
	main.player.camera.current = true
	var start: Vector3 = main.player.global_position
	main.controls.move = Vector2(0.0, -1.0)
	await get_tree().create_timer(2.0).timeout
	main.controls.move = Vector2.ZERO
	await _frames(20)
	var end: Vector3 = main.player.global_position
	print(
		(
			"WALK moved %.1f m, ground y %.2f, player y %.2f, on floor %s"
			% [
				start.distance_to(end),
				main.terrain.height_at(end.x, end.z),
				end.y,
				main.player.is_on_floor()
			]
		)
	)
	await _shot("after_walk_high")

	var secs := float(OS.get_environment("CAPTURE_BENCH_SECONDS"))
	if OS.get_environment("CAPTURE_BENCH_SECONDS") == "":
		secs = 20.0
	if secs > 0.0:
		var list: Array[int] = [0, 1, 2]
		await main.run_bench(list, secs)
		await _frames(10)
		await _shot("bench_result")
	print("CAPTURE DONE")
	get_tree().quit()


## Eye height in the village street between the houses, looking down the row of houses.
func _village_street(tag: String) -> void:
	var a := Vector3(224.0, 0.0, -128.0)
	var b := Vector3(300.0, 0.0, -250.0)
	a.y = main.terrain.height_at(a.x, a.z) + 1.7
	b.y = main.terrain.height_at(b.x, b.z) + 2.5
	main.bench.view(a, b)
	await _frames(45)
	await _shot("village_street_%s" % tag)


func _v(p: Array) -> Vector3:
	return Vector3(float(p[0]), float(p[1]), float(p[2]))


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(shot_name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var dc := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	var pr := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	var vram := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
	var path := out_dir.path_join(shot_name + ".png")
	img.save_png(path)
	print("SHOT %-24s draws %4d  prims %7d  vram %.0f MB  -> %s" % [shot_name, dc, pr, vram, path])
