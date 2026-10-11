extends Node3D

## Phone performance spike: the real Naeroyfjord valley (Kartverket DTM, CC BY 4.0) on the
## Mobile renderer. Builds the world from assets/terrain/ at start; the PerfOverlay buttons
## switch presets and run the benchmark flight. Not the game: no gameplay systems.

signal warmed_up

var terrain: Terrain
var forest: Forest
var near_trees: NearTrees
var rocks: CliffRocks
var grass: Grass
var grass_far: Grass
var player: Player
var bench: Bench
var controls: TouchControls
var sun: DirectionalLight3D
var env: Environment
var village: Village
var corner: Node3D
var waterfall: Waterfall
var corner_ground: ShaderMaterial
var wildlife: Wildlife
var water: MeshInstance3D
var water_foam: ShaderMaterial
var water_plain: ShaderMaterial
var preset_index: int = 2
var forest_index: int = 2
var foam_on: bool = true
var vsync_on: bool = true
## True once the boot warm-up has rendered every preset (see _warm_up).
var warm: bool = false


func _ready() -> void:
	var t0: int = Time.get_ticks_msec()
	terrain = Terrain.new()
	terrain.name = "Terrain"
	terrain.load_data()
	var has_corner: bool = ResourceLoader.exists(SpikeConfig.CORNER_SCENE)
	if has_corner:
		terrain.skip_leaf = SpikeConfig.CORNER_TILES
	terrain.build()
	add_child(terrain)
	if has_corner:
		_build_corner()
	_build_environment()
	_build_water()
	_build_probes()
	_build_village()
	_build_waterfall()
	_build_ingrid()
	forest = Forest.new()
	forest.name = "Forest"
	add_child(forest)
	forest.build(terrain)
	near_trees = NearTrees.new()
	near_trees.name = "NearTrees"
	add_child(near_trees)
	near_trees.build(forest, SpikeConfig.TREE_MESHES)
	rocks = CliffRocks.new()
	rocks.name = "CliffRocks"
	add_child(rocks)
	rocks.build()
	_build_player()
	grass = Grass.new()
	grass.name = "Grass"
	add_child(grass)
	grass.build(terrain)
	grass.target = player
	grass_far = Grass.new()
	grass_far.name = "GrassFar"
	add_child(grass_far)
	grass_far.build(
		terrain,
		SpikeConfig.GRASS_FAR_RADIUS,
		SpikeConfig.GRASS_FAR_SPACING,
		SpikeConfig.GRASS_RADIUS * 0.85,
		SpikeConfig.GRASS_FAR_SCALE
	)
	grass_far.target = player
	if corner:
		for g: Grass in [grass, grass_far]:
			g.mat.set_shader_parameter("corner_mask", load(SpikeConfig.CORNER_MASK))
			g.mat.set_shader_parameter("corner_rect", corner.get_meta("rect"))
	wildlife = Wildlife.new()
	wildlife.name = "Wildlife"
	add_child(wildlife)
	wildlife.build(terrain)
	wildlife.target = player
	bench = Bench.new()
	bench.name = "Bench"
	add_child(bench)
	bench.build(terrain.meta["bench_path"])

	var ui := CanvasLayer.new()
	add_child(ui)
	controls = TouchControls.new()
	ui.add_child(controls)
	player.controls = controls

	PerfOverlay.preset_pressed.connect(_on_preset)
	PerfOverlay.foam_pressed.connect(_on_foam)
	PerfOverlay.forest_pressed.connect(_on_forest)
	PerfOverlay.bench_pressed.connect(_on_bench)
	PerfOverlay.vsync_pressed.connect(_on_vsync)
	PerfOverlay.parts_pressed.connect(_on_parts)
	apply_preset(preset_index)
	set_vsync(true)
	print(
		(
			"SPIKE ready in %d ms: %d terrain tiles, %d trees"
			% [Time.get_ticks_msec() - t0, terrain.tile_count, forest.visible_trees()]
		)
	)
	_warm_up()


## Renders every preset from a few views behind a loading cover so the shader pipelines
## (shadows on/off, foam water, MSAA variants) compile at boot instead of mid-flight.
func _warm_up() -> void:
	var t0: int = Time.get_ticks_msec()
	PerfOverlay.set_buttons_enabled(false)
	PerfOverlay.show_result("Loading: preparing shaders")
	var start: int = preset_index
	var views: Array[float] = [0.02, 0.12, 0.45, 0.62]
	for i in SpikeConfig.PRESETS.size():
		apply_preset(i)
		for f: bool in [true, false]:
			set_foam(f)
			player.camera.current = true
			for k in SpikeConfig.WARMUP_FRAMES:
				await get_tree().process_frame
		for u in views:
			bench.place(u)
			bench.camera.current = true
			for k in SpikeConfig.WARMUP_FRAMES:
				await get_tree().process_frame
	apply_preset(start)
	player.camera.current = true
	await get_tree().process_frame
	PerfOverlay.hide_result()
	PerfOverlay.set_buttons_enabled(true)
	warm = true
	print("WARMUP %d ms" % (Time.get_ticks_msec() - t0))
	warmed_up.emit()


## VSync off lets the bench show real frame times instead of the display cap (Android may
## still limit the rate; the readout shows the mode the driver actually reports).
func set_vsync(on: bool) -> void:
	vsync_on = on
	DisplayServer.window_set_vsync_mode(
		DisplayServer.VSYNC_ENABLED if on else DisplayServer.VSYNC_DISABLED
	)
	Engine.max_fps = int(SpikeConfig.PRESETS[preset_index]["fps_cap"])
	PerfOverlay.set_button_text("vsync", "VSync: %s" % ("on" if on else "off"))
	_update_status()


func vsync_mode_name() -> String:
	var names: Array[String] = ["off", "on", "adaptive", "mailbox"]
	return names[clampi(DisplayServer.window_get_vsync_mode(), 0, 3)]


func _update_status() -> void:
	var p: Dictionary = SpikeConfig.PRESETS[preset_index]
	var aa: String = "MSAA %dx" % int(p["msaa"]) if int(p["msaa"]) > 0 else "no MSAA"
	if bool(p["fxaa"]):
		aa += " + FXAA"
	var cap: int = int(p["fps_cap"])
	var cap_text: String = "cap %d fps" % cap if cap > 0 else "no cap"
	PerfOverlay.status_line = "VSync %s   %s   %s" % [vsync_mode_name(), aa, cap_text]


func _on_vsync() -> void:
	set_vsync(not vsync_on)


func _build_environment() -> void:
	var sky_mat := ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	sky_mat.set_shader_parameter("panorama", load(SpikeConfig.SKY_TEXTURE))
	sky_mat.set_shader_parameter("energy", SpikeConfig.SKY_ENERGY)
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_128
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.sky_rotation = Vector3(0.0, deg_to_rad(SpikeConfig.SKY_ROTATION_DEG), 0.0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = SpikeConfig.AMBIENT_ENERGY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = SpikeConfig.EXPOSURE
	env.adjustment_enabled = true
	env.adjustment_color_correction = _grade_lut()
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.2
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_light_color = SpikeConfig.FOG_COLOR
	env.fog_density = SpikeConfig.FOG_MAX
	env.fog_depth_begin = SpikeConfig.FOG_BEGIN
	env.fog_depth_end = SpikeConfig.FOG_END
	env.fog_depth_curve = SpikeConfig.FOG_CURVE
	env.fog_aerial_perspective = SpikeConfig.FOG_AERIAL
	env.fog_sun_scatter = SpikeConfig.FOG_SUN_SCATTER
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	sun = DirectionalLight3D.new()
	var el: float = deg_to_rad(SpikeConfig.SUN_ELEVATION_DEG)
	var az: float = deg_to_rad(SpikeConfig.SUN_AZIMUTH_DEG)
	var to_sun := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
	add_child(sun)
	sun.look_at_from_position(Vector3.ZERO, -to_sun, Vector3.UP)
	terrain.material.set_shader_parameter("to_sun", to_sun)
	if corner_ground:
		corner_ground.set_shader_parameter("to_sun", to_sun)
	sun.light_color = SpikeConfig.SUN_COLOR
	sun.light_energy = SpikeConfig.SUN_ENERGY
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_blend_splits = true
	sun.shadow_normal_bias = 1.5
	sun.shadow_bias = 0.05
	sun.shadow_blur = 1.0
	# cascades: most texels near the player (with 240 m on Ultra: 19, 48, 108, 240 m)
	sun.directional_shadow_split_1 = 0.08
	sun.directional_shadow_split_2 = 0.2
	sun.directional_shadow_split_3 = 0.45


## The beauty corner (scenes/BeautyCorner.tscn): lightmapped ground meshes in place of the
## terrain's finest tiles, scanned houses, props, rocks and birches. The bake-only sun and valley
## occluder are removed; each ground tile shows when its 320 m parent tile hides, like the
## shader tiles it replaces.
func _build_corner() -> void:
	corner = (load(SpikeConfig.CORNER_SCENE) as PackedScene).instantiate() as Node3D
	add_child(corner)
	for n: String in ["BakeSun", "BakeOccluder"]:
		var node := corner.get_node_or_null(n)
		if node:
			node.free()
	var parents: Dictionary = terrain.tile_nodes[terrain.tile_nodes.size() - 2]
	for mi: MeshInstance3D in corner.get_node("Ground").get_children():
		var parts: PackedStringArray = String(mi.name).split("_")
		var key := Vector2i(int(parts[1]) / 2, int(parts[2]) / 2)
		var parent: MeshInstance3D = parents.get(key)
		if parent:
			mi.visibility_parent = mi.get_path_to(parent)
		corner_ground = mi.mesh.surface_get_material(0) as ShaderMaterial
	var rect := Vector4(
		float(terrain.meta["coarse"]["x0"]) + SpikeConfig.CORNER_TILES.position.x * 160.0,
		float(terrain.meta["coarse"]["z0"]) + SpikeConfig.CORNER_TILES.position.y * 160.0,
		SpikeConfig.CORNER_TILES.size.x * 160.0,
		SpikeConfig.CORNER_TILES.size.y * 160.0
	)
	corner.set_meta("rect", rect)


## Colour grade toward the key frame (docs/mockups/key_fjord_rock.jpg): a 33^3 LUT fitted by
## game-studio tools/refmatch/fit_lut.py at strength 0.4 on the Ultra spawn capture, stored as a
## PNG strip (tools/spike/cube_to_png.py; the .cube stays in assets/_raw/luts/) and rebuilt
## here as a 3D texture.
func _grade_lut() -> ImageTexture3D:
	var strip: Image = (load(SpikeConfig.GRADE_LUT) as Texture2D).get_image()
	strip.convert(Image.FORMAT_RGB8)
	var n: int = strip.get_height()
	var slices: Array[Image] = []
	for b in n:
		slices.append(strip.get_region(Rect2i(b * n, 0, n, n)))
	var tex := ImageTexture3D.new()
	tex.create(Image.FORMAT_RGB8, n, n, n, false, slices)
	return tex


## Box probes over the fjord, captured once at boot: the water mirrors the walls and the forest.
func _build_probes() -> void:
	for r: Vector4 in SpikeConfig.WATER_PROBES:
		var probe := ReflectionProbe.new()
		probe.update_mode = ReflectionProbe.UPDATE_ONCE
		probe.size = Vector3(r.z, 2400.0, r.w)
		probe.position = Vector3(r.x, SpikeConfig.WATER_PROBE_HEIGHT, r.y)
		probe.origin_offset = Vector3.ZERO
		probe.max_distance = 12000.0
		probe.blend_distance = 300.0
		probe.box_projection = false
		probe.intensity = 1.0
		probe.ambient_mode = ReflectionProbe.AMBIENT_DISABLED
		add_child(probe)


func _build_water() -> void:
	var c: Dictionary = terrain.meta["coarse"]
	var size: float = float(c["step"]) * (float(c["nx"]) - 1.0)
	var rect := Vector4(float(c["x0"]), float(c["z0"]), size, size)
	var depth_tex: Texture2D = load("res://assets/terrain/water_depth.png")
	water_foam = ShaderMaterial.new()
	water_foam.shader = load("res://shaders/water_foam.gdshader")
	water_plain = ShaderMaterial.new()
	water_plain.shader = load("res://shaders/water_plain.gdshader")
	var wave_a := _wave_texture(3, 0.9)
	var wave_b := _wave_texture(17, 0.6)
	for m: ShaderMaterial in [water_foam, water_plain]:
		m.set_shader_parameter("depth_map", depth_tex)
		m.set_shader_parameter("depth_rect", rect)
		m.set_shader_parameter("wave_a", wave_a)
		m.set_shader_parameter("wave_b", wave_b)
	var plane := PlaneMesh.new()
	plane.size = Vector2(size, size)
	water = MeshInstance3D.new()
	water.mesh = plane
	water.position = Vector3(rect.x + size * 0.5, 0.0, rect.y + size * 0.5)
	water.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	water.material_override = water_foam
	add_child(water)


## Seamless normal map from noise for the water ripples (generated at boot, no file).
func _wave_texture(seed_value: int, bump: float) -> NoiseTexture2D:
	var n := FastNoiseLite.new()
	n.seed = seed_value
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = 0.012
	n.fractal_octaves = 4
	var t := NoiseTexture2D.new()
	t.width = 512
	t.height = 512
	t.seamless = true
	t.as_normal_map = true
	t.bump_strength = bump * 8.0
	t.generate_mipmaps = true
	t.noise = n
	return t


## The look-dev village as real buildings (scripts/Village.gd, tools/spike/export_village.py).
func _build_village() -> void:
	village = Village.new()
	village.name = "Village"
	add_child(village)
	village.build("_naust" if corner else "")
	for h: Dictionary in terrain.meta["village"]:
		var boathouse: bool = int(h["wall"]) == 3 and float(h["w"]) == 5.0 and float(h["d"]) == 9.0
		if corner and not boathouse:
			continue  # scanned house: its lightmap holds the contact shading
		var p: Array = h["pos"]
		var pos := Vector3(float(p[0]), float(p[1]), float(p[2]))
		Lighting.footprint_shadow(village, pos, float(h["w"]), float(h["d"]), float(h["yaw"]))
	Lighting.village_probe(self)


## The cascade down the real gully on the east wall (scripts/Waterfall.gd).
func _build_waterfall() -> void:
	waterfall = Waterfall.new()
	waterfall.name = "Waterfall"
	add_child(waterfall)
	waterfall.build(terrain)


## Ingrid (GDD 6.4), idle on the shore by the jetty. MakeHuman CC0, tools/spike/export_human.py.
func _build_ingrid() -> void:
	var info: Dictionary = terrain.meta["ingrid"]
	var p: Array = info["pos"]
	var ingrid := (load(SpikeConfig.INGRID_MODEL) as PackedScene).instantiate() as Node3D
	ingrid.name = "Ingrid"
	add_child(ingrid)
	var pos := Vector3(float(p[0]), 0.0, float(p[2]))
	pos.y = terrain.height_at(pos.x, pos.z)
	ingrid.global_position = pos
	ingrid.rotation.y = deg_to_rad(float(info["yaw_deg"]))
	Lighting.contact_shadow(ingrid, 0.55, SpikeConfig.CONTACT_STRENGTH)
	var anim := Humans.find_player(ingrid)
	Humans.loop_all(anim)
	Humans.skin(ingrid)
	if anim:
		anim.play("idle")


func _build_player() -> void:
	var sp: Array = terrain.meta["spawn"]
	var spawn := Vector3(float(sp[0]), float(sp[1]), float(sp[2]))
	# collision: the 2.5 m data round the spawn, kept inside the fine area minus its feather
	var step: float = float(terrain.meta["fine"]["step"])
	var fx0: float = float(terrain.meta["fine"]["x0"])
	var fz0: float = float(terrain.meta["fine"]["z0"])
	var n: int = int(SpikeConfig.COLLISION_SIZE / step) + 1
	var i0: int = int(round((spawn.x - fx0) / step)) - n / 2
	var j0: int = int(round((spawn.z - 305.0 - fz0) / step)) - n / 2
	var region := terrain.fine_img.get_region(Rect2i(i0, j0, n, n))
	region.convert(Image.FORMAT_RF)
	var heights := region.get_data().to_float32_array()
	for k in heights.size():
		heights[k] /= step
	var hm := HeightMapShape3D.new()
	hm.map_width = n
	hm.map_depth = n
	hm.map_data = heights
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	cs.shape = hm
	cs.scale = Vector3.ONE * step
	var cx: float = fx0 + (i0 + (n - 1) * 0.5) * step
	var cz: float = fz0 + (j0 + (n - 1) * 0.5) * step
	cs.position = Vector3(cx, 0.0, cz)
	body.add_child(cs)
	add_child(body)

	player = Player.new()
	player.name = "Player"
	add_child(player)
	player.build()
	player.terrain = terrain
	player.global_position = spawn + Vector3(0.0, 0.5, 0.0)
	player.yaw = deg_to_rad(float(terrain.meta["spawn_yaw_deg"]))
	var half: float = SpikeConfig.COLLISION_SIZE * 0.5 - 5.0
	player.bounds = Rect2(cx - half, cz - half, 2.0 * half, 2.0 * half)
	player.camera.current = true
	Lighting.contact_shadow(player, 0.55, SpikeConfig.CONTACT_STRENGTH)


func apply_preset(i: int) -> void:
	preset_index = i
	var p: Dictionary = SpikeConfig.PRESETS[i]
	var vp := get_viewport()
	vp.scaling_3d_scale = float(p["scale"])
	var msaa_modes: Dictionary = {
		0: Viewport.MSAA_DISABLED, 2: Viewport.MSAA_2X, 4: Viewport.MSAA_4X
	}
	vp.msaa_3d = msaa_modes[int(p["msaa"])]
	vp.screen_space_aa = (
		Viewport.SCREEN_SPACE_AA_FXAA if bool(p["fxaa"]) else Viewport.SCREEN_SPACE_AA_DISABLED
	)
	Engine.max_fps = int(p["fps_cap"])
	RenderingServer.directional_soft_shadow_filter_set_quality(
		int(p["shadow_quality"]) as RenderingServer.ShadowQuality
	)
	sun.shadow_enabled = bool(p["shadows"])
	sun.shadow_blur = float(p["shadow_blur"])
	sun.directional_shadow_max_distance = maxf(float(p["shadow_distance"]), 1.0)
	sun.directional_shadow_mode = (
		DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
		if int(p["shadow_splits"]) == 4
		else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	)
	RenderingServer.directional_shadow_atlas_set_size(int(p["shadow_atlas"]), true)
	env.glow_enabled = bool(p["glow"])
	terrain.material.set_shader_parameter("quality", int(p["terrain_quality"]))
	if corner_ground:
		corner_ground.set_shader_parameter("quality", int(p["terrain_quality"]))
	forest_index = SpikeConfig.FOREST_STEPS.find(float(p["forest"]))
	forest.set_density(float(p["forest"]))
	forest.set_shadows(bool(p["shadows"]))
	near_trees.set_radius(float(p["tree_geo"]))
	rocks.set_enabled(bool(p["rocks"]))
	grass.set_density(float(p["grass"]))
	grass_far.set_density(1.0 if bool(p["grass_far"]) else 0.0)
	wildlife.set_density(i > 0)
	set_foam(bool(p["foam"]))
	PerfOverlay.set_button_text("preset", "Preset: %s" % p["name"])
	_update_forest_text()
	_update_status()


func set_foam(on: bool) -> void:
	foam_on = on
	water.material_override = water_foam if on else water_plain
	PerfOverlay.set_button_text("foam", "Foam: %s" % ("on" if on else "off"))


func _update_forest_text() -> void:
	PerfOverlay.set_button_text(
		"forest", "Forest: %d%% (%d)" % [int(forest.density * 100.0), forest.visible_trees()]
	)


func _on_preset() -> void:
	apply_preset((preset_index + 1) % SpikeConfig.PRESETS.size())


func _on_foam() -> void:
	set_foam(not foam_on)


func _on_forest() -> void:
	forest_index = (maxi(forest_index, 0) + 1) % SpikeConfig.FOREST_STEPS.size()
	forest.set_density(SpikeConfig.FOREST_STEPS[forest_index])
	_update_forest_text()


func _on_bench(all_presets: bool) -> void:
	if bench.running or not warm:
		return
	var list: Array[int] = [preset_index]
	if all_presets:
		list.clear()
		for k in SpikeConfig.PRESETS.size():
			list.append(k)
	run_bench(list, SpikeConfig.BENCH_SECONDS)


## "GPU parts": what each feature of the current preset costs on this device's GPU
## (scripts/GpuParts.gd, about 2 minutes).
func _on_parts() -> void:
	if bench.running or not warm:
		return
	bench.running = true
	var start_vsync: bool = vsync_on
	set_vsync(false)
	PerfOverlay.set_buttons_enabled(false)
	PerfOverlay.show_result("GPU parts: measuring (about 2 min)")
	var grass_target := grass.target
	grass.target = bench.camera
	grass_far.target = bench.camera
	var parts := GpuParts.new()
	add_child(parts)
	var lines: Array[String] = await parts.run(self, get_viewport())
	parts.queue_free()
	grass.target = grass_target
	grass_far.target = grass_target
	player.camera.current = true
	set_vsync(start_vsync)
	bench.running = false
	PerfOverlay.set_buttons_enabled(true)
	PerfOverlay.show_result(
		(
			"GPU parts, %s (%s): ms saved per switch\n%s"
			% [SpikeConfig.PRESETS[preset_index]["name"], OS.get_model_name(), "\n".join(lines)]
		)
	)


## Flies the bench path once per preset; restores the player camera and the starting preset.
func run_bench(list: Array[int], seconds: float) -> Array[Dictionary]:
	var start_preset: int = preset_index
	var start_vsync: bool = vsync_on
	set_vsync(false)
	var mode: String = vsync_mode_name()
	PerfOverlay.set_buttons_enabled(false)
	var grass_target := grass.target
	grass.target = bench.camera
	grass_far.target = bench.camera
	var lines: Array[String] = []
	var out: Array[Dictionary] = []
	for i in list:
		apply_preset(i)
		var s: Dictionary = await bench.run(seconds)
		s["preset"] = SpikeConfig.PRESETS[i]["name"]
		out.append(s)
		var line := Bench.format(str(s["preset"]), s)
		lines.append(line)
		print("BENCH ", line)
	grass.target = grass_target
	grass_far.target = grass_target
	if list.size() > 1:
		apply_preset(start_preset)
	player.camera.current = true
	set_vsync(start_vsync)
	PerfOverlay.set_buttons_enabled(true)
	PerfOverlay.show_result(
		(
			"Bench %d s (%s, vsync %s)\n%s"
			% [int(seconds), OS.get_model_name(), mode, "\n".join(lines)]
		)
	)
	return out
