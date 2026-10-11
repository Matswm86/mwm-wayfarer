extends Node

## Dev-only screenshot bot. Run under Xvfb with CAPTURE_DIR set (see game-studio CLAUDE.md).
## Fixed cameras (visual pass 2): spawn, village street, meadow animals, cliff close, forest
## slope, high view and Ingrid at the dock, for each preset in CAPTURE_PRESETS (indices into
## SpikeConfig.PRESETS, default "0,3" = Low and Ultra). Every shot prints draws, primitives and
## VRAM. Then a 2 s walk and an optional bench (laptop fps means nothing for phones).
## CAPTURE_BENCH_SECONDS sets the bench length (default 0 = skip).
## CAPTURE_HIDE_UI=1 hides the readout and buttons (clean frames for look comparisons).
## CAPTURE_SUFFIX is appended to every file name (e.g. "_before").
## CAPTURE_SET=beauty (pass 3): only spawn and the six beauty-corner cameras (village street, house
## close-up at 5 m, shoreline, cliff foot, waterfall from the village, waterfall close).

const CLIFF_TARGET := Vector3(420.0, 0.0, -500.0)
const CLIFF_CAMERA := Vector3(320.0, 0.0, -540.0)
const FOREST_TARGET := Vector3(-430.0, 0.0, 775.0)
const FOREST_CAMERA := Vector3(-215.0, 0.0, 545.0)
## eye height inside the densest stand near the spawn (115 trees within 40 m)
const STAND_CAMERA := Vector3(140.0, 0.0, 118.0)
const STAND_TARGET := Vector3(176.0, 0.0, 166.0)

var out_dir: String = OS.get_environment("CAPTURE_DIR")
var suffix: String = OS.get_environment("CAPTURE_SUFFIX")
var main: Node3D


func _ready() -> void:
	main = load("res://scenes/Main.tscn").instantiate()
	add_child(main)
	if not main.warm:
		await main.warmed_up
	if OS.get_environment("CAPTURE_HIDE_UI") == "1":
		PerfOverlay.set_ui_visible(false)
	if OS.get_environment("CAPTURE_NO_LIGHTMAP") == "1" and main.corner:
		(main.corner.get_node("LightmapGI") as LightmapGI).light_data = null
	if OS.get_environment("CAPTURE_NO_WATER") == "1":
		main.water.visible = false
	await _frames(30)
	var path: Array = main.terrain.meta["bench_path"]
	var high := _v(path[7])
	var spawn_look := _v(path[1]) + Vector3(0.0, -60.0, -300.0)

	var presets: Array[int] = [0, SpikeConfig.PRESETS.size() - 1]
	var env_p: String = OS.get_environment("CAPTURE_PRESETS")
	if env_p != "":
		presets.clear()
		for s: String in env_p.split(","):
			presets.append(int(s))
	var beauty: bool = OS.get_environment("CAPTURE_SET") == "beauty"
	for preset in presets:
		main.apply_preset(preset)
		var tag: String = str(SpikeConfig.PRESETS[preset]["name"]).to_lower()
		main.player.camera.current = true
		_ground_cover_follows(main.player)
		await _frames(45)
		await _shot("spawn_%s" % tag)
		if beauty:
			_ground_cover_follows(main.bench.camera)
			await _beauty(tag)
			continue
		_ground_cover_follows(main.bench.camera)
		await _village_street(tag)
		await _animals(tag)
		await _view(CLIFF_CAMERA, 5.0, CLIFF_TARGET, 5.0, "cliff_close_%s" % tag)
		await _view(FOREST_CAMERA, 45.0, FOREST_TARGET, 20.0, "forest_slope_%s" % tag)
		await _view(STAND_CAMERA, 1.7, STAND_TARGET, 4.0, "forest_inside_%s" % tag)
		main.bench.view(high, spawn_look)
		await _frames(45)
		await _shot("high_view_%s" % tag)
		var ing: Node3D = main.get_node("Ingrid")
		var ip := ing.global_position
		main.bench.view(ip + Vector3(-2.2, 1.7, 3.2), ip + Vector3(0.0, 1.35, 0.0))
		await _frames(45)
		await _shot("ingrid_dock_%s" % tag)

	_ground_cover_follows(main.player)
	# walk forward for 2 s with the stick held, to prove movement and collision
	main.apply_preset(presets[presets.size() - 1])
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

	var secs := float(OS.get_environment("CAPTURE_BENCH_SECONDS"))
	if secs > 0.0:
		var list: Array[int] = []
		for i in SpikeConfig.PRESETS.size():
			list.append(i)
		await main.run_bench(list, secs)
		await _frames(10)
		await _shot("bench_result")
	print("CAPTURE DONE")
	get_tree().quit()


## Camera `up_cam` m above the ground at `cam`, looking at a point `up_tgt` m above `tgt`.
func _view(cam: Vector3, up_cam: float, tgt: Vector3, up_tgt: float, shot_name: String) -> void:
	var c := Vector3(cam.x, maxf(main.terrain.height_at(cam.x, cam.z), 0.0) + up_cam, cam.z)
	var t := Vector3(tgt.x, main.terrain.height_at(tgt.x, tgt.z) + up_tgt, tgt.z)
	main.bench.view(c, t)
	await _frames(45)
	await _shot(shot_name)


## The nearest grazing deer at eye height, a few metres off.
func _animals(tag: String) -> void:
	var doe: Node3D = main.wildlife.animals[0].node
	var dp := doe.global_position
	var cam := dp + Vector3(6.0, 0.0, 8.0)
	cam.y = main.terrain.height_at(cam.x, cam.z) + 1.6
	main.bench.view(cam, dp + Vector3(0.0, 0.8, 0.0))
	await _frames(45)
	await _shot("meadow_animals_%s" % tag)


## Eye height in the village street between the houses, looking down the row of houses.
func _village_street(tag: String) -> void:
	var a := Vector3(224.0, 0.0, -128.0)
	var b := Vector3(300.0, 0.0, -250.0)
	a.y = main.terrain.height_at(a.x, a.z) + 1.7
	b.y = main.terrain.height_at(b.x, b.z) + 2.5
	main.bench.view(a, b)
	await _frames(45)
	await _shot("village_street_%s" % tag)


## The six fixed beauty-corner cameras (pass 3).
func _beauty(tag: String) -> void:
	var only: String = OS.get_environment("CAPTURE_ONLY")
	if only == "house":
		var hh: Node3D = main.corner.get_node("Houses").get_child(0)
		var hhp := hh.global_position
		var ff := hh.global_transform.basis.x.normalized()
		await _view(hhp + ff * 9.8, 1.7, hhp, 2.6, "b_house_%s" % tag)
		await _view(hhp - ff * 9.8, 1.7, hhp, 2.6, "b_house_west_%s" % tag)
		return
	# village street at eye height, down the path between the scanned houses
	await _view(
		Vector3(229.0, 0.0, -150.0), 1.7, Vector3(296.0, 0.0, -232.0), 3.0, "b_street_%s" % tag
	)
	# a scanned house from 5 m (the first cabin on the slots), eye height
	var house: Node3D = main.corner.get_node("Houses").get_child(0)
	var hp := house.global_position
	var front := house.global_transform.basis.x.normalized()
	await _view(hp + front * 9.8, 1.7, hp, 2.6, "b_house_%s" % tag)
	# shoreline: low on the pebbles, along the water to the jetty and boats
	await _view(
		Vector3(196.0, 0.0, -112.0), 1.5, Vector3(216.0, 0.0, -170.0), 0.5, "b_shore_%s" % tag
	)
	# cliff foot east of the houses: talus, rock faces, the wall above
	await _view(
		Vector3(318.0, 0.0, -245.0), 1.8, Vector3(405.0, 0.0, -250.0), 30.0, "b_cliff_%s" % tag
	)
	# the cascade from the village street
	var f: Vector3 = main.waterfall.foot
	var mo: Vector3 = main.waterfall.mouth
	main.bench.view(
		Vector3(290.0, main.terrain.height_at(290.0, -236.0) + 1.7, -236.0),
		mo + Vector3(30.0, 25.0, 0.0)
	)
	await _frames(45)
	await _shot("b_falls_far_%s" % tag)
	# the cascade close: a clear spot (no trees in the line) 43 m from the main foot, looking up
	await _view(
		f + Vector3(-36.0, 0.0, -24.0),
		3.0,
		f + Vector3(40.0, 0.0, 0.0),
		30.0,
		"b_falls_near_%s" % tag
	)


## Grass and ferns grow round whatever the shot looks from (the player in play).
func _ground_cover_follows(n: Node3D) -> void:
	main.grass.target = n
	main.grass_far.target = n


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
	var path := out_dir.path_join(shot_name + suffix + ".png")
	img.save_png(path)
	print(
		(
			"SHOT %-24s draws %4d  prims %7d  vram %.0f MB  near trees %d  rocks %d  -> %s"
			% [shot_name, dc, pr, vram, main.near_trees.count(), main.rocks.count(), path]
		)
	)
