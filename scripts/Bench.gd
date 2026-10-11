class_name Bench
extends Node3D

## Fixed camera flight over the village and the fjord (points from terrain.json, made from
## the scene_fjord.py shore line). run() flies it once and returns the frame statistics.
## run_corner() measures what the player sees instead: the player stands at the spawn in the
## start view and looks round (SpikeConfig.CORNER_LOOK s), then runs the worn path through the
## beauty corner (SpikeConfig.CORNER_WALK) with his own camera, and is put back at the spawn.

signal finished(stats: Dictionary)

var camera: Camera3D
var running: bool = false
var curve: Curve3D
## Set by Main for run_corner().
var player: Player
var controls: TouchControls
var spawn: Vector3
var spawn_yaw: float = 0.0
var _wp: int = 0


func build(points: Array) -> void:
	camera = Camera3D.new()
	camera.fov = 62.0
	camera.near = 0.3
	camera.far = 9000.0
	add_child(camera)
	curve = Curve3D.new()
	var pts: Array[Vector3] = []
	for p: Array in points:
		pts.append(Vector3(float(p[0]), float(p[1]), float(p[2])))
	for i in pts.size():
		var prev: Vector3 = pts[maxi(i - 1, 0)]
		var nxt: Vector3 = pts[mini(i + 1, pts.size() - 1)]
		var tan := (nxt - prev) / 6.0
		curve.add_point(pts[i], -tan, tan)
	curve.bake_interval = 2.0


## Camera at a point on the path, 0..1, looking a little ahead and down.
func place(u: float) -> void:
	var length := curve.get_baked_length()
	var p := curve.sample_baked(u * length, true)
	var ahead := curve.sample_baked(minf(u + 0.035, 1.0) * length, true)
	if ahead.distance_to(p) < 1.0:
		ahead = p + Vector3(0.0, 0.0, -10.0)
	var look := ahead + Vector3(0.0, -0.25 * ahead.distance_to(p) - 4.0, 0.0)
	camera.global_position = p
	camera.look_at(look, Vector3.UP)


func view(pos: Vector3, target: Vector3) -> void:
	camera.global_position = pos
	camera.look_at(target, Vector3.UP)
	camera.current = true


func run(seconds: float) -> Dictionary:
	camera.current = true
	place(0.0)
	return await _measure(seconds, _path_step.bind(seconds))


func _path_step(t: float, _dt: float, seconds: float) -> void:
	place(clampf(t / seconds, 0.0, 1.0))


## The corner pass (see the header). Same statistics as run().
func run_corner(seconds: float) -> Dictionary:
	_reset_player()
	_wp = 0
	player.camera.current = true
	var stats: Dictionary = await _measure(seconds, _corner_step)
	controls.move = Vector2.ZERO
	_reset_player()
	return stats


func _reset_player() -> void:
	player.global_position = spawn
	player.velocity = Vector3.ZERO
	player.yaw = spawn_yaw
	player.pitch = -0.12
	controls.move = Vector2.ZERO


## Look round at the spawn, then steer the stick toward the next path point (camera behind).
func _corner_step(t: float, dt: float) -> void:
	var look: float = SpikeConfig.CORNER_LOOK
	if t < look:
		player.yaw = spawn_yaw + sin(maxf(t, 0.0) / look * TAU) * 0.6
		controls.move = Vector2.ZERO
		return
	var pos := Vector2(player.global_position.x, player.global_position.z)
	var walk: Array[Vector2] = SpikeConfig.CORNER_WALK
	while _wp < walk.size() and pos.distance_to(walk[_wp]) < 3.0:
		_wp += 1
	if _wp >= walk.size():
		controls.move = Vector2.ZERO
		return
	var d := (walk[_wp] - pos).normalized()
	player.yaw = lerp_angle(player.yaw, atan2(-d.x, -d.y), minf(1.0, dt * 3.0))
	var fwd := Vector2(-sin(player.yaw), -cos(player.yaw))
	var right := Vector2(cos(player.yaw), -sin(player.yaw))
	controls.move = Vector2(d.dot(right), -d.dot(fwd)).normalized()


## Runs `step(t, dt)` every frame for `seconds` after the warm-up and collects frame statistics.
func _measure(seconds: float, step: Callable) -> Dictionary:
	running = true
	var frames := PackedFloat32Array()
	var gpu := PackedFloat32Array()
	var cpu_sum: float = 0.0
	var phys_sum: float = 0.0
	var draws_sum: float = 0.0
	var draws_max: float = 0.0
	var prims_sum: float = 0.0
	var prims_max: float = 0.0
	var t: float = -SpikeConfig.BENCH_WARMUP
	while t < seconds:
		await get_tree().process_frame
		var dt: float = get_process_delta_time()
		t += dt
		step.call(t, dt)
		if t <= 0.0:
			continue
		frames.append(dt * 1000.0)
		gpu.append(PerfOverlay.gpu_ms())
		cpu_sum += PerfOverlay.cpu_ms()
		phys_sum += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
		var dc: float = Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		var pr: float = Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		draws_sum += dc
		prims_sum += pr
		draws_max = maxf(draws_max, dc)
		prims_max = maxf(prims_max, pr)
	running = false
	var n: int = maxi(frames.size(), 1)
	var total_ms: float = 0.0
	for f in frames:
		total_ms += f
	frames.sort()
	var gpu_total: float = 0.0
	for g in gpu:
		gpu_total += g
	gpu.sort()
	var stats := {
		"frames": frames.size(),
		"avg_fps": 1000.0 * n / maxf(total_ms, 0.001),
		"p95_ms": frames[int(floor((n - 1) * 0.95))] if frames.size() > 0 else 0.0,
		"max_ms": frames[frames.size() - 1] if frames.size() > 0 else 0.0,
		"gpu_avg_ms": gpu_total / n,
		"gpu_p95_ms": gpu[int(floor((n - 1) * 0.95))] if gpu.size() > 0 else 0.0,
		"cpu_avg_ms": cpu_sum / n,
		"phys_avg_ms": phys_sum / n,
		"avg_draws": draws_sum / n,
		"max_draws": draws_max,
		"avg_prims": prims_sum / n,
		"max_prims": prims_max,
		"vram_mb": Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
		"ram_mb": Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0,
	}
	finished.emit(stats)
	return stats


static func format(name: String, s: Dictionary) -> String:
	return (
		(
			"%-6s %5.1f fps  p95 %4.1f  max %4.1f ms  GPU %4.1f / p95 %4.1f ms"
			+ "  CPU %3.1f + phys %3.1f ms  draws %d/%d  %dk prims"
		)
		% [
			name,
			s["avg_fps"],
			s["p95_ms"],
			s["max_ms"],
			s["gpu_avg_ms"],
			s["gpu_p95_ms"],
			s["cpu_avg_ms"],
			s["phys_avg_ms"],
			int(s["avg_draws"]),
			int(s["max_draws"]),
			int(s["max_prims"] / 1000.0),
		]
	)
