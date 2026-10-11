class_name Waterfall
extends Node3D

## The cascade down the real gully on the east wall (pass 3; path from terrain.json, traced like
## scene_fjord.py falls_real): 413 m of drop over 880 m, steepest (45-52 deg) between about 200 m
## and 60 m. Replaces the single wide ribbon and the mist puffs of pass 1:
## - two ribbons that hug the gully's cross-section (terrain heights at every vertex): a white-water
##   core and a thinner veil, foam scrolling faster where the gully is steeper
##   (shaders/waterfall.gdshader; COLOR.r = steepness, UV.y = metres along / 10);
## - the ribbons widen with camera distance only (vertex shader), so the falls read from the
##   village 1.3 km away and are true size up close;
## - splash droplets and spray where a steep run meets flatter ground, mist sheets drifting off
##   the main foot, a plunge pool there;
## - dark wet rock (decals) along the steep part.
## Numbers in SpikeConfig (FALLS_*).

var points: Array[Vector3] = []
var foot: Vector3 = Vector3.ZERO
var mouth: Vector3 = Vector3.ZERO
var mat_core: ShaderMaterial
var mat_veil: ShaderMaterial


func build(terrain: Terrain) -> void:
	var raw: Array[Vector3] = []
	for p: Array in terrain.meta["waterfall"]:
		raw.append(Vector3(float(p[0]), float(p[1]), float(p[2])))
	points = _resample(raw, SpikeConfig.FALLS_STEP)
	var shader: Shader = load("res://shaders/waterfall.gdshader")
	mat_core = ShaderMaterial.new()
	mat_core.shader = shader
	mat_veil = ShaderMaterial.new()
	mat_veil.shader = shader
	mat_veil.set_shader_parameter("opacity", 0.45)
	mat_veil.set_shader_parameter("speed", 1.1)
	mat_veil.set_shader_parameter("streak_scale", 5.0)
	mat_veil.render_priority = -1
	add_child(_ribbon(terrain, SpikeConfig.FALLS_CORE, 0.35, mat_core, "Core"))
	add_child(_ribbon(terrain, SpikeConfig.FALLS_VEIL, 0.2, mat_veil, "Veil"))
	var feet := _feet()
	for i in feet.size():
		var p: Vector3 = points[feet[i]]
		add_child(_splash(p, 1.0 if i == 0 else 0.6))
	foot = points[feet[0]] if feet.size() > 0 else points[points.size() - 1]
	# the mouth, where the stream runs into the fjord: the only part the village can see (the
	# cascade itself is behind the spur of the east wall, checked by line of sight on the DEM)
	mouth = points[points.size() - 1]
	add_child(_splash(mouth + Vector3(0.0, -0.3, 0.0), 0.5))
	add_child(_mist(foot))
	add_child(_pool(terrain, foot))
	_wet_rock()


## Evenly spaced points along the traced path (Catmull-Rom through the trace).
func _resample(raw: Array[Vector3], step: float) -> Array[Vector3]:
	var curve := Curve3D.new()
	for i in raw.size():
		var prev: Vector3 = raw[maxi(i - 1, 0)]
		var nxt: Vector3 = raw[mini(i + 1, raw.size() - 1)]
		var tan := (nxt - prev) / 6.0
		curve.add_point(raw[i], -tan, tan)
	curve.bake_interval = step
	var out: Array[Vector3] = []
	var length := curve.get_baked_length()
	var d: float = 0.0
	while d <= length:
		out.append(curve.sample_baked(d, true))
		d += step
	return out


## Steepness (drop per metre along the ground) at point i, smoothed over a few points.
func _grad(i: int) -> float:
	var a: Vector3 = points[maxi(i - 3, 0)]
	var b: Vector3 = points[mini(i + 3, points.size() - 1)]
	var run: float = Vector2(b.x - a.x, b.z - a.z).length()
	return (a.y - b.y) / maxf(run, 0.1)


## A strip `half` metres wide each side (x = top width, y = foot width) of `across` + 1 vertices per
## row, each vertex `lift` m above the terrain, so the water lies in the gully.
func _ribbon(
	terrain: Terrain, half: Vector2, lift: float, mat: Material, node_name: String
) -> Node3D:
	var across: int = 6
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	var along: float = 0.0
	var n: int = points.size()
	for i in n:
		var d: Vector3 = points[mini(i + 1, n - 1)] - points[maxi(i - 1, 0)]
		var side := Vector3(-d.z, 0.0, d.x).normalized()
		if i > 0:
			along += points[i].distance_to(points[i - 1])
		var t: float = float(i) / float(n - 1)
		var w: float = lerpf(half.x, half.y, t)
		var steep: float = clampf(_grad(i) / 1.2, 0.0, 1.0)
		for k in across + 1:
			var u: float = float(k) / float(across)
			var p: Vector3 = points[i] + side * (u * 2.0 - 1.0) * w
			# hug the gully floor, never sink below the traced line (the trace is the thalweg)
			p.y = maxf(terrain.height_at(p.x, p.z), points[i].y - 0.5) + lift
			verts.append(p)
			norms.append(Vector3.UP)
			uvs.append(Vector2(u, along / 10.0))
			# r: steepness; g: side direction x, b: side z (vertex shader widens along it)
			cols.append(Color(steep, side.x * 0.5 + 0.5, side.z * 0.5 + 0.5, u * 2.0 - 1.0))
		if i > 0:
			var r0: int = (i - 1) * (across + 1)
			var r1: int = i * (across + 1)
			for k in across:
				idx.append_array([r0 + k, r0 + k + 1, r1 + k, r0 + k + 1, r1 + k + 1, r1 + k])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_COLOR] = cols
	arrays[Mesh.ARRAY_INDEX] = idx
	var st := SurfaceTool.new()
	st.create_from_arrays(arrays)
	st.generate_normals()
	var mesh := st.commit()
	var mi := MeshInstance3D.new()
	mi.name = node_name
	mi.mesh = mesh
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# the far widening happens in the vertex shader: grow the cull box to match
	mi.extra_cull_margin = 40.0
	return mi


## Indices where a steep run (> 0.9) gives way to flatter ground (< 0.5): splash and spray.
## The lowest one (biggest fall above it) first.
func _feet() -> Array[int]:
	var out: Array[int] = []
	var was_steep: bool = false
	for i in points.size():
		var g: float = _grad(i)
		if g > 0.9:
			was_steep = true
		elif was_steep and g < 0.5:
			out.append(i)
			was_steep = false
	out.reverse()
	return out


func _droplet_mesh(size: float, alpha: float) -> QuadMesh:
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	var qm := StandardMaterial3D.new()
	qm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	qm.vertex_color_use_as_albedo = true
	var blob := GradientTexture2D.new()
	var bg := Gradient.new()
	bg.set_color(0, Color(0.95, 0.97, 0.98, alpha))
	bg.set_color(1, Color(0.95, 0.97, 0.98, 0.0))
	blob.gradient = bg
	blob.fill = GradientTexture2D.FILL_RADIAL
	blob.fill_from = Vector2(0.5, 0.5)
	blob.fill_to = Vector2(1.0, 0.5)
	blob.width = 64
	blob.height = 64
	qm.albedo_texture = blob
	quad.material = qm
	return quad


func _fade_ramp(peak: float) -> GradientTexture1D:
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0))
	fade.set_color(1, Color(1, 1, 1, 0))
	fade.add_point(0.15, Color(1, 1, 1, peak))
	var ramp := GradientTexture1D.new()
	ramp.gradient = fade
	return ramp


## Droplets thrown up and out where the water lands, plus a low spray cloud.
func _splash(p: Vector3, k: float) -> Node3D:
	var holder := Node3D.new()
	holder.name = "Splash"
	holder.position = p + Vector3(0.0, 0.5, 0.0)
	var drops := GPUParticles3D.new()
	drops.amount = int(160 * k)
	drops.lifetime = 1.4
	drops.visibility_aabb = AABB(Vector3(-12, -4, -12), Vector3(24, 16, 24))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 2.5 * k
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 55.0
	pm.initial_velocity_min = 3.0
	pm.initial_velocity_max = 7.5
	pm.gravity = Vector3(0, -9.8, 0)
	pm.scale_min = 0.5
	pm.scale_max = 1.2
	pm.color_ramp = _fade_ramp(0.9)
	drops.process_material = pm
	drops.draw_pass_1 = _droplet_mesh(0.35, 1.0)
	drops.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	drops.visibility_range_end = 400.0
	holder.add_child(drops)
	var spray := GPUParticles3D.new()
	spray.amount = int(36 * k)
	spray.lifetime = 3.5
	spray.visibility_aabb = AABB(Vector3(-20, -4, -20), Vector3(40, 24, 40))
	var sm := ParticleProcessMaterial.new()
	sm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	sm.emission_sphere_radius = 3.0 * k
	sm.direction = Vector3(0, 1, 0)
	sm.spread = 70.0
	sm.initial_velocity_min = 1.0
	sm.initial_velocity_max = 2.5
	sm.gravity = Vector3(0.3, 0.2, 0)
	sm.scale_min = 0.8
	sm.scale_max = 1.6
	sm.color_ramp = _fade_ramp(0.35)
	spray.process_material = sm
	spray.draw_pass_1 = _droplet_mesh(SpikeConfig.FALLS_SPRAY_SIZE * k, 0.8)
	spray.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	holder.add_child(spray)
	return holder


## Big faint mist sheets drifting off the main foot (they also carry the falls from far away).
func _mist(p: Vector3) -> GPUParticles3D:
	var mist := GPUParticles3D.new()
	mist.name = "Mist"
	mist.amount = 14
	mist.lifetime = 7.0
	mist.position = p + Vector3(0.0, 3.0, 0.0)
	mist.visibility_aabb = AABB(Vector3(-60, -10, -60), Vector3(120, 70, 120))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 6.0
	pm.direction = Vector3(-1, 0.6, 0)
	pm.spread = 40.0
	pm.initial_velocity_min = 0.6
	pm.initial_velocity_max = 1.6
	pm.gravity = Vector3(0, 0.15, 0)
	pm.scale_min = 0.8
	pm.scale_max = 1.5
	pm.color_ramp = _fade_ramp(0.22)
	mist.process_material = pm
	mist.draw_pass_1 = _droplet_mesh(SpikeConfig.FALLS_MIST_SIZE, 0.7)
	mist.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mist


## Plunge pool: a small disc of dark clear water with a foam ring, set into the ground at the foot.
func _pool(terrain: Terrain, p: Vector3) -> MeshInstance3D:
	var disc := CylinderMesh.new()
	disc.top_radius = SpikeConfig.FALLS_POOL_RADIUS
	disc.bottom_radius = SpikeConfig.FALLS_POOL_RADIUS
	disc.height = 0.05
	disc.radial_segments = 32
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/waterfall_pool.gdshader")
	m.set_shader_parameter("radius", SpikeConfig.FALLS_POOL_RADIUS)
	var mi := MeshInstance3D.new()
	mi.name = "Pool"
	mi.mesh = disc
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# the water surface sits just below the lowest ground round the rim
	var lo: float = INF
	for a in 8:
		var q := p + Vector3(cos(a * TAU / 8.0), 0.0, sin(a * TAU / 8.0)) * 3.0
		lo = minf(lo, terrain.height_at(q.x, q.z))
	mi.position = Vector3(p.x, minf(lo, p.y) + 0.15, p.z)
	return mi


## Wet, dark rock along the steep part: dark glossy decals over the gully and its spray zone.
func _wet_rock() -> void:
	var tex := GradientTexture2D.new()
	var g := Gradient.new()
	g.set_color(0, Color(0.0, 0.0, 0.0, 1.0))
	g.set_color(1, Color(0.0, 0.0, 0.0, 0.0))
	g.add_point(0.55, Color(0.0, 0.0, 0.0, 0.8))
	tex.gradient = g
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	tex.width = 64
	tex.height = 64
	var step: int = 6
	for i in range(0, points.size() - step, step):
		var g0: float = _grad(i)
		if g0 < 0.6:
			continue
		var a: Vector3 = points[i]
		var b: Vector3 = points[i + step]
		var dcl := Decal.new()
		dcl.texture_albedo = tex
		dcl.modulate = Color(0.25, 0.27, 0.26, SpikeConfig.FALLS_WET_STRENGTH)
		dcl.albedo_mix = 1.0
		var length: float = a.distance_to(b) + 10.0
		dcl.size = Vector3(SpikeConfig.FALLS_WET_WIDTH, length, length)
		dcl.upper_fade = 0.2
		dcl.lower_fade = 0.2
		dcl.distance_fade_enabled = true
		dcl.distance_fade_begin = 1600.0
		dcl.distance_fade_length = 300.0
		dcl.cull_mask = 1
		add_child(dcl)
		dcl.global_position = (a + b) * 0.5
		var dirv := (b - a).normalized()
		dcl.look_at(dcl.global_position + Vector3(dirv.x, 0.0, dirv.z), Vector3.UP)
