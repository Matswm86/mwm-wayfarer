class_name Village
extends Node3D

## The look-dev village (tools/spike/export_village.py from tools/art/wf_build.py): turf-roof
## timber houses, boathouses and boats as one mesh, one surface per Poly Haven (CC0) texture set,
## plus the Poly Haven pier. The GLB is already in the world frame. Each surface gets a tiling
## PBR material (UV1, world metres) tinted by the vertex colour, with the Cycles-baked ambient
## occlusion on UV2 (contact shadow under eaves and between boards; no SSAO on Mobile).

const DIR := "res://assets/models/village/"
## How much of the baked occlusion also darkens the sun (eaves, gaps), not only the sky light.
const AO_LIGHT_AFFECT := 0.45

var surfaces: int = 0


## variant "" = all houses and boats; "_naust" = only the two boathouses (the beauty corner has
## the scanned houses and the designer's boats).
func build(variant: String = "") -> void:
	var info: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string(DIR + "materials%s.json" % variant)
	)
	var ao: Texture2D = load(DIR + "village%s_ao.png" % variant)
	var houses := (load(DIR + "village%s.glb" % variant) as PackedScene).instantiate() as Node3D
	add_child(houses)
	for mi: MeshInstance3D in houses.find_children("*", "MeshInstance3D", true, false):
		for s in mi.mesh.get_surface_count():
			var key: String = mi.mesh.surface_get_material(s).resource_name
			mi.set_surface_override_material(s, _material(key, info.get(key, {}), ao))
			surfaces += 1
	var pier := (load(DIR + "pier.glb") as PackedScene).instantiate() as Node3D
	add_child(pier)


func _material(key: String, m: Dictionary, ao: Texture2D) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.resource_name = key
	mat.vertex_color_use_as_albedo = true
	mat.ao_enabled = true
	mat.ao_texture = ao
	mat.ao_on_uv2 = true
	mat.ao_light_affect = AO_LIGHT_AFFECT
	var set_name: String = str(m.get("set", "flat"))
	if set_name == "flat":
		mat.roughness = 0.08 if key == "glass" else 0.6
		mat.metallic_specular = 0.6 if key == "glass" else 0.4
		return mat
	var tex: String = DIR + "tex/" + set_name
	var s: float = float(m.get("uv_scale", 1.0))
	mat.uv1_scale = Vector3(s, s, 1.0)
	mat.albedo_texture = load(tex + "_albedo.jpg")
	mat.normal_enabled = true
	mat.normal_texture = load(tex + "_normal.jpg")
	mat.roughness_texture = load(tex + "_arm.jpg")
	mat.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
	mat.roughness = 1.0
	return mat
