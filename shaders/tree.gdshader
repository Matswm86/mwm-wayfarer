// Pine forest for MultiMeshInstance3D. Two meshes share this shader: a low-poly pine (near) and a
// single cone (far). Each tree picks its LOD by its own distance to `lod_center` (the camera,
// set by script every frame), so a chunk can hold both and no tree is drawn twice.
// A uniform is used instead of CAMERA_POSITION_WORLD so the shadow pass makes the same choice.

shader_type spatial;
render_mode cull_disabled, specular_disabled;

uniform vec3 lod_center;
uniform float lod_radius = 320.0;
uniform bool is_far = false;
uniform vec3 tint : source_color = vec3(1.0);

void vertex() {
	vec3 root = MODEL_MATRIX[3].xyz;
	float d = distance(root.xz, lod_center.xz);
	bool hide = is_far ? (d < lod_radius) : (d >= lod_radius);
	if (hide) {
		VERTEX = vec3(0.0);
	}
}

void fragment() {
	// near meshes carry vertex colours; far cones are white and take the per-instance colour
	ALBEDO = COLOR.rgb * tint;
	ROUGHNESS = 0.9;
}
