extends Node3D

## Phone performance spike: the real Naeroyfjord valley (Kartverket DTM, CC BY 4.0) on the
## Mobile renderer. Builds the world from assets/terrain/ at start; the PerfOverlay buttons
## switch presets and run the benchmark flight. Not the game: no gameplay systems.

var terrain: Terrain
var forest: Forest
var grass: Grass
var player: Player
var bench: Bench
var controls: TouchControls
var sun: DirectionalLight3D
var water: MeshInstance3D
var water_foam: ShaderMaterial
var water_plain: ShaderMaterial
var preset_index: int = 2
var forest_index: int = 2
var foam_on: bool = true


func _ready() -> void:
	var t0: int = Time.get_ticks_msec()
	terrain = Terrain.new()
	terrain.name = "Terrain"
	terrain.load_data()
	terrain.build()
	add_child(terrain)
	_build_environment()
	_build_water()
	_build_village()
	_build_waterfall()
	_build_ingrid()
	forest = Forest.new()
	forest.name = "Forest"
	add_child(forest)
	forest.build(terrain.meta)
	_build_player()
	grass = Grass.new()
	grass.name = "Grass"
	add_child(grass)
	grass.build(terrain)
	grass.target = player
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
	apply_preset(preset_index)
	print(
		(
			"SPIKE ready in %d ms: %d terrain tiles, %d trees"
			% [Time.get_ticks_msec() - t0, terrain.tile_count, forest.visible_trees()]
		)
	)


func _build_environment() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.25, 0.45, 0.74)
	sky_mat.sky_horizon_color = Color(0.70, 0.79, 0.87)
	sky_mat.ground_bottom_color = Color(0.66, 0.74, 0.80)
	sky_mat.ground_horizon_color = Color(0.70, 0.79, 0.87)
	sky_mat.sun_angle_max = 20.0
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.9
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0
	env.fog_enabled = true
	env.fog_light_color = Color(0.70, 0.78, 0.85)
	env.fog_density = 0.00014
	env.fog_aerial_perspective = 0.35
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
	sun.light_color = Color(1.0, 0.95, 0.86)
	sun.light_energy = 1.25
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = SpikeConfig.SHADOW_DISTANCE
	sun.shadow_blur = 1.0


func _build_water() -> void:
	var c: Dictionary = terrain.meta["coarse"]
	var size: float = float(c["step"]) * (float(c["nx"]) - 1.0)
	var rect := Vector4(float(c["x0"]), float(c["z0"]), size, size)
	var depth_tex: Texture2D = load("res://assets/terrain/water_depth.png")
	water_foam = ShaderMaterial.new()
	water_foam.shader = load("res://shaders/water_foam.gdshader")
	water_plain = ShaderMaterial.new()
	water_plain.shader = load("res://shaders/water_plain.gdshader")
	for m: ShaderMaterial in [water_foam, water_plain]:
		m.set_shader_parameter("depth_map", depth_tex)
		m.set_shader_parameter("depth_rect", rect)
	var plane := PlaneMesh.new()
	plane.size = Vector2(size, size)
	water = MeshInstance3D.new()
	water.mesh = plane
	water.position = Vector3(rect.x + size * 0.5, 0.0, rect.y + size * 0.5)
	water.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	water.material_override = water_foam
	add_child(water)


## Simple house blocks at the scene_fjord.py village spots, one mesh for the whole village.
func _build_village() -> void:
	var walls: Array[Color] = [
		Color(0.55, 0.16, 0.12),
		Color(0.78, 0.56, 0.24),
		Color(0.90, 0.88, 0.84),
		Color(0.17, 0.14, 0.12)
	]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for h: Dictionary in terrain.meta["village"]:
		var p: Array = h["pos"]
		var base := Vector3(float(p[0]), float(p[1]), float(p[2]))
		var xf := Transform3D(Basis(Vector3.UP, deg_to_rad(float(h["yaw"]))), base)
		_house(st, xf, float(h["w"]), float(h["d"]), 2.9, walls[int(h["wall"])])
	var j: Dictionary = terrain.meta["jetty"]
	var a := Vector3(float(j["from"][0]), float(j["from"][1]), float(j["from"][2]))
	var b := Vector3(float(j["to"][0]), float(j["to"][1]), float(j["to"][2]))
	var mid := (a + b) * 0.5
	var xj := Transform3D(Basis(Vector3.UP, atan2(b.x - a.x, b.z - a.z)), mid - Vector3(0, 0.3, 0))
	_box(st, xj, Vector3(2.4, 0.3, a.distance_to(b)), Color(0.35, 0.27, 0.20))
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.roughness = 0.85
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m
	add_child(mi)


## Waterfall down the real gully near scene y=1300 (path from terrain.json, traced like
## scene_fjord.py falls_real): one scrolling ribbon plus mist particles at the foot.
func _build_waterfall() -> void:
	var pts: Array[Vector3] = []
	for p: Array in terrain.meta["waterfall"]:
		pts.append(Vector3(float(p[0]), float(p[1]), float(p[2])))
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	var along: float = 0.0
	for i in pts.size():
		var d: Vector3 = pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]
		var side := Vector3(-d.z, 0.0, d.x).normalized()
		var t: float = float(i) / float(pts.size() - 1)
		var w: float = lerpf(9.0, 18.0, t)
		if i > 0:
			along += pts[i].distance_to(pts[i - 1])
		verts.append(pts[i] - side * w + Vector3(0.0, 5.0, 0.0))
		verts.append(pts[i] + side * w + Vector3(0.0, 5.0, 0.0))
		uvs.append(Vector2(0.0, along / 10.0))
		uvs.append(Vector2(1.0, along / 10.0))
		if i > 0:
			var a: int = (i - 1) * 2
			idx.append_array([a, a + 1, a + 2, a + 1, a + 3, a + 2])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/waterfall.gdshader")
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)

	var mist := GPUParticles3D.new()
	mist.amount = 24
	mist.lifetime = 5.0
	mist.visibility_aabb = AABB(Vector3(-60, -10, -60), Vector3(120, 90, 120))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 12.0
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 50.0
	pm.initial_velocity_min = 2.0
	pm.initial_velocity_max = 5.0
	pm.gravity = Vector3(0, 0.3, 0)
	pm.scale_min = 0.7
	pm.scale_max = 1.4
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0))
	fade.set_color(1, Color(1, 1, 1, 0))
	fade.add_point(0.3, Color(1, 1, 1, 0.45))
	var ramp := GradientTexture1D.new()
	ramp.gradient = fade
	pm.color_ramp = ramp
	mist.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(26, 26)
	var qm := StandardMaterial3D.new()
	qm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	qm.vertex_color_use_as_albedo = true
	var blob := GradientTexture2D.new()
	var bg := Gradient.new()
	bg.set_color(0, Color(0.92, 0.95, 0.96, 1))
	bg.set_color(1, Color(0.92, 0.95, 0.96, 0))
	blob.gradient = bg
	blob.fill = GradientTexture2D.FILL_RADIAL
	blob.fill_from = Vector2(0.5, 0.5)
	blob.fill_to = Vector2(1.0, 0.5)
	qm.albedo_texture = blob
	quad.material = qm
	mist.draw_pass_1 = quad
	mist.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mist.position = pts[pts.size() - 1] + Vector3(0, 4, 0)
	add_child(mist)


## Ingrid (GDD 6.4), idle on the shore by the jetty. MakeHuman CC0, tools/spike/export_human.py.
func _build_ingrid() -> void:
	var info: Dictionary = terrain.meta["ingrid"]
	var p: Array = info["pos"]
	var ingrid := (load("res://assets/models/ingrid.glb") as PackedScene).instantiate() as Node3D
	ingrid.name = "Ingrid"
	add_child(ingrid)
	var pos := Vector3(float(p[0]), 0.0, float(p[2]))
	pos.y = terrain.height_at(pos.x, pos.z)
	ingrid.global_position = pos
	ingrid.rotation.y = deg_to_rad(float(info["yaw_deg"]))
	var anim := Humans.find_player(ingrid)
	Humans.loop_all(anim)
	if anim:
		anim.play("idle")


func _house(st: SurfaceTool, xf: Transform3D, w: float, d: float, h: float, wall: Color) -> void:
	_box(st, xf * Transform3D(Basis(), Vector3(0, h * 0.5 - 1.0, 0)), Vector3(w, h + 2.0, d), wall)
	var roof := Color(0.27, 0.25, 0.17)
	var r: float = w * 0.5 + 0.4
	var ridge: float = h + w * 0.42
	var hd: float = d * 0.5 + 0.4
	var quads: Array = [
		[Vector3(-r, h, -hd), Vector3(0, ridge, -hd), Vector3(0, ridge, hd), Vector3(-r, h, hd)],
		[Vector3(0, ridge, -hd), Vector3(r, h, -hd), Vector3(r, h, hd), Vector3(0, ridge, hd)],
	]
	for q: Array in quads:
		_quad(st, xf, q, roof)
	var gw: float = w * 0.5
	var g0: Array = [
		Vector3(-gw, h, -d * 0.5), Vector3(gw, h, -d * 0.5), Vector3(0, ridge, -d * 0.5)
	]
	var g1: Array = [Vector3(gw, h, d * 0.5), Vector3(-gw, h, d * 0.5), Vector3(0, ridge, d * 0.5)]
	for g: Array in [g0, g1]:
		st.set_color(wall)
		for v: Vector3 in g:
			st.add_vertex(xf * v)


func _quad(st: SurfaceTool, xf: Transform3D, q: Array, col: Color) -> void:
	st.set_color(col)
	for k: int in [0, 1, 2, 0, 2, 3]:
		st.add_vertex(xf * (q[k] as Vector3))


func _box(st: SurfaceTool, xf: Transform3D, size: Vector3, col: Color) -> void:
	var e := size * 0.5
	var faces: Array = [
		[
			Vector3(-e.x, e.y, -e.z),
			Vector3(e.x, e.y, -e.z),
			Vector3(e.x, e.y, e.z),
			Vector3(-e.x, e.y, e.z)
		],
		[
			Vector3(-e.x, -e.y, e.z),
			Vector3(e.x, -e.y, e.z),
			Vector3(e.x, e.y, e.z),
			Vector3(-e.x, e.y, e.z)
		],
		[
			Vector3(e.x, -e.y, -e.z),
			Vector3(-e.x, -e.y, -e.z),
			Vector3(-e.x, e.y, -e.z),
			Vector3(e.x, e.y, -e.z)
		],
		[
			Vector3(e.x, -e.y, e.z),
			Vector3(e.x, -e.y, -e.z),
			Vector3(e.x, e.y, -e.z),
			Vector3(e.x, e.y, e.z)
		],
		[
			Vector3(-e.x, -e.y, -e.z),
			Vector3(-e.x, -e.y, e.z),
			Vector3(-e.x, e.y, e.z),
			Vector3(-e.x, e.y, -e.z)
		],
	]
	for f: Array in faces:
		_quad(st, xf, f, col)


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


func apply_preset(i: int) -> void:
	preset_index = i
	var p: Dictionary = SpikeConfig.PRESETS[i]
	get_viewport().scaling_3d_scale = float(p["scale"])
	sun.shadow_enabled = bool(p["shadows"])
	forest_index = SpikeConfig.FOREST_STEPS.find(float(p["forest"]))
	forest.set_density(float(p["forest"]))
	forest.set_shadows(bool(p["shadows"]))
	grass.set_density(float(p["grass"]))
	set_foam(bool(p["foam"]))
	PerfOverlay.set_button_text("preset", "Preset: %s" % p["name"])
	_update_forest_text()


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
	if bench.running:
		return
	var list: Array[int] = [preset_index]
	if all_presets:
		list = [0, 1, 2]
	run_bench(list, SpikeConfig.BENCH_SECONDS)


## Flies the bench path once per preset; restores the player camera and the starting preset.
func run_bench(list: Array[int], seconds: float) -> Array[Dictionary]:
	var start_preset: int = preset_index
	PerfOverlay.set_buttons_enabled(false)
	var grass_target := grass.target
	grass.target = bench.camera
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
	if list.size() > 1:
		apply_preset(start_preset)
	player.camera.current = true
	PerfOverlay.set_buttons_enabled(true)
	PerfOverlay.show_result(
		"Bench %d s (%s)\n%s" % [int(seconds), OS.get_model_name(), "\n".join(lines)]
	)
	return out
