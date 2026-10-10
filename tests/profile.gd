extends Node

## Dev-only CPU/GPU profiler (perf pass 3). Run under Xvfb like tests/capture.tscn.
## 1. Flies the bench path per preset (PROFILE_PRESETS, default "2,3") for PROFILE_SECONDS
##    (default 30) and prints per-frame averages and p95 of: frame time, script _process time,
##    physics time, render-thread CPU (culling + command recording), GPU time.
## 2. PROFILE_ABLATE=1: at fixed views on the path, toggles one feature at a time and prints the
##    GPU and CPU change it causes (laptop GPU != phone GPU; only the ratios guide the cuts).

var main: Node3D
var vp_rid: RID
var vp: Viewport


func _ready() -> void:
	main = load("res://scenes/Main.tscn").instantiate()
	# PROFILE_OFFSCREEN=1: render the 3D into a 1920x1080 SubViewport and keep the window tiny, so
	# the Xvfb present (a CPU copy) does not throttle the loop and the GPU keeps its clocks up.
	if OS.get_environment("PROFILE_OFFSCREEN") == "1":
		var sv := SubViewport.new()
		sv.size = Vector2i(1920, 1080)
		sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		add_child(sv)
		sv.add_child(main)
		vp = sv
	else:
		add_child(main)
		vp = get_viewport()
	if not main.warm:
		await main.warmed_up
	vp_rid = vp.get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp_rid, true)
	main.set_vsync(false)
	var presets: Array[int] = [2, 3]
	var env_p: String = OS.get_environment("PROFILE_PRESETS")
	if env_p != "":
		presets.clear()
		for s: String in env_p.split(","):
			presets.append(int(s))
	var secs: float = float(OS.get_environment("PROFILE_SECONDS"))
	if secs <= 0.0:
		secs = 30.0
	main.grass.target = main.bench.camera
	main.grass_far.target = main.bench.camera
	for p in presets:
		main.apply_preset(p)
		Engine.max_fps = 0
		await _fly(str(SpikeConfig.PRESETS[p]["name"]), secs)
	if OS.get_environment("PROFILE_CPU") == "1":
		await _cpu_ablate()
	if OS.get_environment("PROFILE_ABLATE") == "1":
		for p in presets:
			await _ablate(p)
	print("PROFILE DONE")
	get_tree().quit()


func _sample() -> Dictionary:
	return {
		"frame": get_process_delta_time() * 1000.0,
		"process": Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
		"physics": Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
		"render_cpu":
		(
			RenderingServer.viewport_get_measured_render_time_cpu(vp_rid)
			+ RenderingServer.get_frame_setup_time_cpu()
		),
		"gpu": RenderingServer.viewport_get_measured_render_time_gpu(vp_rid),
	}


func _fly(label: String, secs: float) -> void:
	var rows: Array[Dictionary] = []
	var t: float = -1.0
	main.bench.place(0.0)
	main.bench.camera.current = true
	while t < secs:
		await get_tree().process_frame
		t += get_process_delta_time()
		main.bench.place(clampf(t / secs, 0.0, 1.0))
		if t > 0.0:
			rows.append(_sample())
	print("PROFILE %-6s %s" % [label, _summary(rows)])


func _summary(rows: Array[Dictionary]) -> String:
	var out: PackedStringArray = []
	for k: String in ["frame", "process", "physics", "render_cpu", "gpu"]:
		var v := PackedFloat32Array()
		for r in rows:
			v.append(float(r[k]))
		v.sort()
		var s: float = 0.0
		for x in v:
			s += x
		var n: int = maxi(v.size(), 1)
		out.append("%s %.2f/p95 %.2f" % [k, s / n, v[int((n - 1) * 0.95)] if v.size() else 0.0])
	return "  ".join(out)


## Average GPU and render CPU over n frames from the current camera.
func _ablate(p: int) -> void:
	main.apply_preset(p)
	var parts := GpuParts.new()
	add_child(parts)
	var lines: Array[String] = await parts.run(main, vp)
	for line in lines:
		print("ABLATE %-6s %s" % [str(SpikeConfig.PRESETS[p]["name"]), line])
	parts.queue_free()


## Script time (Performance.TIME_PROCESS, ms) at a fixed camera over the village with one system
## switched off at a time. Animation players and trees count here: they run in the process step.
func _cpu_ablate() -> void:
	main.apply_preset(3)
	Engine.max_fps = 0
	main.bench.place(0.08)
	main.bench.camera.current = true
	var anims: Array[Node] = main.find_children("*", "AnimationPlayer", true, false)
	var trees: Array[Node] = main.find_children("*", "AnimationTree", true, false)
	var skels: Array[Node] = main.find_children("*", "Skeleton3D", true, false)
	print(
		(
			"CPU nodes: %d AnimationPlayer, %d AnimationTree, %d Skeleton3D, %d nodes total"
			% [anims.size(), trees.size(), skels.size(), get_tree().get_node_count()]
		)
	)
	var cases: Array[String] = [
		"base",
		"wildlife",
		"anim_players",
		"anim_trees",
		"grass",
		"overlay",
		"near_trees",
		"forest",
		"player",
		"all_scripts",
		"base",
	]
	for c in cases:
		var off: Array[Node] = []
		match c:
			"wildlife":
				off = [main.wildlife]
			"grass":
				off = [main.grass, main.grass_far]
			"overlay":
				off = [PerfOverlay]
			"near_trees":
				off = [main.near_trees]
			"forest":
				off = [main.forest]
			"player":
				off = [main.player]
			"anim_players":
				off = anims
			"anim_trees":
				off = trees
			"all_scripts":
				off = [
					main.wildlife,
					main.grass,
					main.grass_far,
					PerfOverlay,
					main.near_trees,
					main.forest,
					main.player
				]
				off.append_array(anims)
				off.append_array(trees)
		for n in off:
			n.process_mode = Node.PROCESS_MODE_DISABLED
		for i in 20:
			await get_tree().process_frame
		var acc := PackedFloat32Array()
		var phy := 0.0
		for i in 240:
			await get_tree().process_frame
			acc.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
			phy += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
		var tot := 0.0
		for v in acc:
			tot += v
		acc.sort()
		print(
			(
				"CPU %-14s process %.2f ms (p95 %.2f, max %.2f)  physics %.2f ms"
				% [c, tot / 240.0, acc[227], acc[239], phy / 240.0]
			)
		)
		for n in off:
			n.process_mode = Node.PROCESS_MODE_INHERIT
