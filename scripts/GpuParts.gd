class_name GpuParts
extends Node

## "GPU parts" (perf pass 3): measures what each feature of the current preset costs on THIS
## device's GPU. At a few fixed views on the bench path it renders the preset as is, then with one
## feature switched off, alternating the two (so clock and heat drift cancel), and reports the GPU
## time saved per feature. The phone runs it from the overlay button; tests/profile.gd runs the
## same code on the laptop. Main.gd owns the presets; this only flips switches and restores them
## with Main.apply_preset.

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
]

var main: Node
var vp_rid: RID


## Returns one line per case: "name  -x.x ms (base y.y)". Leaves the preset as it found it.
func run(m: Node, viewport: Viewport) -> Array[String]:
	main = m
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
			saved += b - x
			base_sum += b
		main.apply_preset(preset)
		base_all += base_sum / ROUNDS
		var line := "%-22s %+5.1f ms" % [c, -saved / ROUNDS]
		lines.append(line)
		print("GPUPARTS ", line)
	main.apply_preset(preset)
	lines.push_front("base GPU %.1f ms (avg of %d views)" % [base_all / CASES.size(), VIEWS.size()])
	return lines


func _views() -> float:
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


func _apply(c: String, viewport: Viewport) -> void:
	match c:
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
