class_name GpuParts
extends Node

## "GPU parts" (perf pass 3): measures what each feature of the current preset costs on THIS
## device's GPU. At a few fixed views on the bench path it renders the preset as is, then with one
## feature switched off, alternating the two (so clock and heat drift cancel), and reports the GPU
## time saved per feature. The phone runs it from the overlay button; tests/profile.gd runs the
## same code on the laptop. Main.gd owns the presets; this only flips switches and restores them
## with Main.apply_preset.
## Bench corner pass (2026-10-11): the phone button measures "here", the player's own camera where
## he stands (his yaw and +-25 deg), so standing at the spawn gives the beauty corner's costs;
## tests/profile.gd can still measure the bench path views. The corner cases hide one group of the
## corner (or the player, Ingrid, animals, waterfall) and put it back afterwards.

const VIEWS: Array[float] = [0.0, 0.08, 0.2, 0.5, 0.85]
const FRAMES := 24
const SETTLE := 6
const ROUNDS := 2
const CASES: Array[String] = [
	"msaa 4x->2x",
	"msaa off",
	"sun shadows off",
	"shadow filter low",
	"shadow 2 splits",
	"tree shadows off",
	"ground cover off",
	"far clumps off",
	"near pine meshes off",
	"impostor forest off",
	"foam water off",
	"glow off",
	"rock detail -1",
	"render scale 0.85",
	"corner houses off",
	"corner props off",
	"corner rocks off",
	"corner birches off",
	"corner ground off",
	"player off",
	"ingrid+animals off",
	"waterfall off",
	"village off",
]
## "here" views: yaw offsets (rad) round the player's own view.
const HERE_YAWS: Array[float] = [0.0, -0.45, 0.45]

var main: Node
var vp_rid: RID
var here: bool = false
var _here_yaw: float = 0.0
var _hidden: Array[Node3D] = []


## Returns one line per case: "name  -x.x ms (base y.y)". Leaves the preset as it found it.
## at_player: measure at the player's view (see the header) instead of the bench path views.
func run(m: Node, viewport: Viewport, at_player: bool = false) -> Array[String]:
	main = m
	here = at_player
	_here_yaw = main.player.yaw
	vp_rid = viewport.get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp_rid, true)
	var preset: int = main.preset_index
	var lines: Array[String] = []
	var base_all: float = 0.0
	for c in CASES:
		var saved: float = 0.0
		var base_sum: float = 0.0
		for r in ROUNDS:
			main.apply_preset(preset)
			Engine.max_fps = 0
			var b: float = await _views()
			_apply(c, viewport)
			var x: float = await _views()
			_show_hidden()
			saved += b - x
			base_sum += b
		main.apply_preset(preset)
		base_all += base_sum / ROUNDS
		var line := "%-22s %+5.1f ms" % [c, -saved / ROUNDS]
		lines.append(line)
		print("GPUPARTS ", line)
	main.apply_preset(preset)
	main.player.yaw = _here_yaw
	var where: String = "%d views here" % HERE_YAWS.size() if here else "%d views" % VIEWS.size()
	lines.push_front("base GPU %.1f ms (avg of %s)" % [base_all / CASES.size(), where])
	return lines


func _views() -> float:
	if here:
		return await _here_views()
	var acc: float = 0.0
	for u in VIEWS:
		main.bench.place(u)
		main.bench.camera.current = true
		for i in SETTLE:
			await get_tree().process_frame
		var g: float = 0.0
		for i in FRAMES:
			await get_tree().process_frame
			g += RenderingServer.viewport_get_measured_render_time_gpu(vp_rid)
		acc += g / FRAMES
	return acc / VIEWS.size()


func _here_views() -> float:
	var acc: float = 0.0
	main.player.camera.current = true
	for y in HERE_YAWS:
		main.player.yaw = _here_yaw + y
		for i in SETTLE:
			await get_tree().process_frame
		var g: float = 0.0
		for i in FRAMES:
			await get_tree().process_frame
			g += RenderingServer.viewport_get_measured_render_time_gpu(vp_rid)
		acc += g / FRAMES
	return acc / HERE_YAWS.size()


func _hide(nodes: Array) -> void:
	for n: Node3D in nodes:
		if n and n.visible:
			n.visible = false
			_hidden.append(n)


func _show_hidden() -> void:
	for n in _hidden:
		n.visible = true
	_hidden.clear()


func _corner_part(part: String) -> Node3D:
	if main.corner == null:
		return null
	return main.corner.get_node_or_null(part) as Node3D


func _apply(c: String, viewport: Viewport) -> void:
	match c:
		"corner houses off":
			_hide([_corner_part("Houses")])
		"corner props off":
			_hide([_corner_part("Props")])
		"corner rocks off":
			_hide([_corner_part("Rocks")])
		"corner birches off":
			_hide([_corner_part("Trees")])
		"corner ground off":
			_hide([_corner_part("Ground")])
		"player off":
			_hide([main.player.model])
		"ingrid+animals off":
			_hide([main.get_node("Ingrid"), main.wildlife])
		"waterfall off":
			_hide([main.waterfall])
		"village off":
			_hide([main.village])
		"msaa 4x->2x":
			if viewport.msaa_3d == Viewport.MSAA_4X:
				viewport.msaa_3d = Viewport.MSAA_2X
		"msaa off":
			viewport.msaa_3d = Viewport.MSAA_DISABLED
		"sun shadows off":
			main.sun.shadow_enabled = false
		"shadow filter low":
			RenderingServer.directional_soft_shadow_filter_set_quality(
				RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW
			)
			main.sun.shadow_blur = 1.0
		"shadow 2 splits":
			main.sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
		"tree shadows off":
			main.forest.set_shadows(false)
			main.near_trees.set_shadows(false)
		"ground cover off":
			main.grass.set_density(0.0)
		"far clumps off":
			main.grass_far.set_density(0.0)
		"near pine meshes off":
			main.near_trees.set_radius(0.0)
		"impostor forest off":
			main.forest.set_density(0.0)
		"foam water off":
			main.set_foam(false)
		"glow off":
			main.env.glow_enabled = false
		"rock detail -1":
			var q: int = int(main.terrain.material.get_shader_parameter("quality"))
			main.terrain.material.set_shader_parameter("quality", maxi(q - 1, 0))
		"render scale 0.85":
			viewport.scaling_3d_scale = minf(viewport.scaling_3d_scale, 0.85)
