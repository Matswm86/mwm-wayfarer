class_name Bench
extends Node3D

## Fixed camera flight over the village and the fjord (points from terrain.json, made from
## the scene_fjord.py shore line). run() flies it once and returns the frame statistics.

signal finished(stats: Dictionary)

var camera: Camera3D
var running: bool = false
var curve: Curve3D


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
	running = true
	camera.current = true
	var frames := PackedFloat32Array()
	var gpu := PackedFloat32Array()
	var draws_sum: float = 0.0
	var draws_max: float = 0.0
	var prims_sum: float = 0.0
	var prims_max: float = 0.0
	var t: float = -SpikeConfig.BENCH_WARMUP
	place(0.0)
	while t < seconds:
		await get_tree().process_frame
		var dt: float = get_process_delta_time()
		t += dt
		place(clampf(t / seconds, 0.0, 1.0))
		if t <= 0.0:
			continue
		frames.append(dt * 1000.0)
		gpu.append(PerfOverlay.gpu_ms())
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
			+ "  draws %d/%d  %dk prims"
		)
		% [
			name,
			s["avg_fps"],
			s["p95_ms"],
			s["max_ms"],
			s["gpu_avg_ms"],
			s["gpu_p95_ms"],
			int(s["avg_draws"]),
			int(s["max_draws"]),
			int(s["max_prims"] / 1000.0),
		]
	)
