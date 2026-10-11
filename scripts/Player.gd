class_name Player
extends CharacterBody3D

## Walking capsule with a third-person orbit camera. Input comes from TouchControls
## (left-thumb stick, right-side drag). The camera never dips under the terrain.

var controls: TouchControls
var terrain: Terrain
var camera: Camera3D
var yaw: float = 0.0
var pitch: float = -0.12
var bounds: Rect2 = Rect2()
var model: Node3D
var anim: AnimationPlayer
var locomotion: AnimationTree
var _blend_speed: float = 0.0


func build() -> void:
	var shape := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.35
	cap.height = 1.75
	shape.shape = cap
	shape.position.y = 0.875
	add_child(shape)
	# scanned man (pass 3; SpikeConfig.PLAYER_MODEL), faces -Z like the body
	model = (load(SpikeConfig.PLAYER_MODEL) as PackedScene).instantiate() as Node3D
	add_child(model)
	anim = Humans.find_player(model)
	Humans.loop_all(anim)
	_scan_skin(model)
	locomotion = Humans.locomotion(anim, SpikeConfig.PLAYER_GAITS)
	camera = Camera3D.new()
	camera.fov = 60.0
	camera.near = 0.2
	camera.far = 9000.0
	add_child(camera)
	camera.top_level = true
	floor_snap_length = 0.6
	floor_max_angle = deg_to_rad(50.0)


## The scan has one albedo-only material (skin and clothes): soft, low specular, a faint rim.
static func _scan_skin(root: Node) -> void:
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		for si in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(si) as StandardMaterial3D
			if src == null:
				continue
			var m := src.duplicate() as StandardMaterial3D
			m.roughness = 0.75
			m.metallic_specular = 0.3
			m.rim_enabled = true
			m.rim = 0.15
			m.rim_tint = 0.5
			mi.set_surface_override_material(si, m)


func _physics_process(delta: float) -> void:
	var stick := Vector2.ZERO
	if controls:
		stick = controls.move
		var orbit := controls.take_orbit()
		yaw -= orbit.x * SpikeConfig.ORBIT_SPEED
		pitch = clampf(pitch - orbit.y * SpikeConfig.ORBIT_SPEED, -1.2, 0.5)
	var fwd := Vector3(-sin(yaw), 0.0, -cos(yaw))
	var right := Vector3(cos(yaw), 0.0, -sin(yaw))
	var speed: float = SpikeConfig.PLAYER_RUN if stick.length() > 0.9 else SpikeConfig.PLAYER_WALK
	var wish := (right * stick.x - fwd * stick.y) * speed
	velocity.x = wish.x
	velocity.z = wish.z
	velocity.y -= SpikeConfig.GRAVITY * delta
	move_and_slide()
	if bounds.size.x > 0.0:
		var p := global_position
		p.x = clampf(p.x, bounds.position.x, bounds.end.x)
		p.z = clampf(p.z, bounds.position.y, bounds.end.y)
		global_position = p
	if wish.length() > 0.1:
		rotation.y = atan2(-wish.x, -wish.z)
	if locomotion:
		# idle -> walk -> run blended by the actual ground speed, eased so starts and stops blend
		var ground: float = Vector2(velocity.x, velocity.z).length()
		_blend_speed = move_toward(_blend_speed, ground, delta * 16.0)
		locomotion.set("parameters/move/blend_position", _blend_speed)


func _process(_delta: float) -> void:
	if not camera.current:
		return
	var head := global_position + Vector3(0.0, SpikeConfig.CAM_HEIGHT, 0.0)
	var dir := Vector3(-sin(yaw) * cos(pitch), sin(pitch), -cos(yaw) * cos(pitch))
	var cam_pos := head - dir * SpikeConfig.CAM_DISTANCE
	if terrain:
		cam_pos.y = maxf(cam_pos.y, terrain.height_at(cam_pos.x, cam_pos.z) + 0.6)
	camera.global_position = cam_pos
	camera.look_at(head + dir * 2.0, Vector3.UP)
