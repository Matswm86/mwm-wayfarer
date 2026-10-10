// Forest impostors (graphics pass 2026-10-10). Every tree is one camera-facing quad that shows
// pre-rendered frames of a scanned Poly Haven tree (CC0; tools/spike/bake_tree_impostors.py):
// 8 directions round the tree at two heights (5 and 40 deg). Near trees blend the two nearest
// directions and both heights and are lit with the baked normals; far trees take one frame.
// Each tree picks near/far by its own distance to `lod_center` (the camera, set by script every
// frame), so a chunk can hold both and no tree is drawn twice; a uniform rather than
// CAMERA_POSITION_WORLD so the shadow pass makes the same choice.
// The sun is limited by the baked terrain sun visibility at the tree's root (trees in the shadow
// of a fjord wall stay dark), and the sky light by the baked sky visibility.
// Instance data: transform (yaw + uniform scale), INSTANCE_CUSTOM.r = variant, .g = tint jitter.

shader_type spatial;
render_mode world_vertex_coords, cull_disabled;

#include "res://shaders/terrain_height.gdshaderinc"
#include "res://shaders/terrain_light.gdshaderinc"

uniform sampler2D atlas_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D atlas_normal : filter_linear_mipmap, repeat_disable;
uniform vec2 atlas_px = vec2(4096.0, 2560.0);
uniform float variants = 5.0;
// per variant: frame height in metres and frame centre above the root, at instance scale 1
uniform vec2 frame_info[5];
uniform vec3 tints[5];
uniform vec3 lod_center;
uniform float lod_radius = 320.0;
uniform bool is_far = false;
uniform float elev_low = 5.0;
uniform float elev_high = 40.0;
uniform float wind_strength = 0.012;
uniform float geo_radius = 0.0;

varying vec4 uv_a;  // low row: nearest two directions
varying vec4 uv_b;  // high row
varying vec2 blend;  // x: direction blend, y: height blend
varying float yaw;
varying vec3 tint;
varying float sun_vis;
varying float sky_vis;

vec2 frame_uv(float row, float elev_i, float az_i, vec2 q) {
	return vec2((elev_i * 8.0 + az_i + q.x) / 16.0, (row + q.y) / variants);
}

void vertex() {
	vec3 root = MODEL_MATRIX[3].xyz;
	float sc = length(MODEL_MATRIX[0].xyz);
	yaw = atan(-MODEL_MATRIX[0].z, MODEL_MATRIX[0].x);
	float d = distance(root.xz, lod_center.xz);
	bool hide = is_far ? (d < lod_radius) : (d >= lod_radius);
	// conifers near the camera are real meshes (scripts/NearTrees.gd)
	hide = hide || (distance(root, lod_center) < geo_radius && INSTANCE_CUSTOM.r < 3.5);
	float row = floor(INSTANCE_CUSTOM.r + 0.5);
	vec2 fi = frame_info[int(row)] * sc;
	vec3 centre = root + vec3(0.0, fi.y, 0.0);
	vec3 v = PROJECTION_MATRIX[3][3] > 0.5 ? INV_VIEW_MATRIX[2].xyz : CAMERA_POSITION_WORLD - centre;
	v = normalize(v);
	// view direction in the tree's own frame (undo the instance yaw)
	float c = cos(yaw);
	float s = sin(yaw);
	vec3 vl = vec3(c * v.x - s * v.z, v.y, s * v.x + c * v.z);
	float az = atan(vl.x, vl.z);
	float f = mod(az / (TAU / 8.0) + 8.0, 8.0);
	float a0 = floor(f);
	float a1 = mod(a0 + 1.0, 8.0);
	float el = degrees(asin(clamp(vl.y, -1.0, 1.0)));
	blend = vec2(f - a0, clamp((el - elev_low) / (elev_high - elev_low), 0.0, 1.0));
	if (is_far) {
		a0 = blend.x < 0.5 ? a0 : a1;
		blend.x = 0.0;
	}
	// near trees turn round the vertical axis only, so a close quad never tilts into the slope
	// or toward a camera above it (that cut a hard straight edge through crowns at spawn)
	vec3 vflat = normalize(vec3(v.x, 0.0, v.z) + vec3(1e-4, 0.0, 0.0));
	float upright = PROJECTION_MATRIX[3][3] > 0.5 ? 0.0 : 1.0 - smoothstep(60.0, 140.0, d);
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), v));
	right = normalize(mix(right, normalize(cross(vec3(0.0, 1.0, 0.0), vflat)), upright));
	vec3 up = normalize(mix(cross(v, right), vec3(0.0, 1.0, 0.0), upright));
	vec2 q = UV;
	VERTEX = centre + right * (q.x - 0.5) * fi.x * 0.5 + up * (0.5 - q.y) * fi.x;
	// wind: the crown sways, the trunk foot stays put
	float bend = (1.0 - q.y) * (1.0 - q.y);
	float gust = sin(TIME * 0.9 + root.x * 0.05 + root.z * 0.03) * 0.6 + sin(TIME * 2.3 + root.z * 0.2) * 0.25;
	VERTEX += right * gust * bend * fi.x * wind_strength;
	uv_a = vec4(frame_uv(row, 0.0, a0, q), frame_uv(row, 0.0, a1, q));
	uv_b = vec4(frame_uv(row, 1.0, a0, q), frame_uv(row, 1.0, a1, q));
	tint = tints[int(row)] * (0.85 + 0.3 * INSTANCE_CUSTOM.g);
	vec4 baked = light_sample(root.xz);
	sun_vis = baked.r;
	sky_vis = baked.g;
	if (hide) {
		VERTEX = vec3(0.0);
	}
	NORMAL = v;
}

void fragment() {
	vec4 c;
	vec3 nb;
	if (is_far) {
		vec2 uv = blend.y < 0.5 ? uv_a.xy : uv_b.xy;
		c = texture(atlas_albedo, uv);
		nb = texture(atlas_normal, uv).xyz;
		ALPHA_TEXTURE_COORDINATE = uv * atlas_px;
	} else {
		vec4 lo = mix(texture(atlas_albedo, uv_a.xy), texture(atlas_albedo, uv_a.zw), blend.x);
		vec4 hi = mix(texture(atlas_albedo, uv_b.xy), texture(atlas_albedo, uv_b.zw), blend.x);
		c = mix(lo, hi, blend.y);
		vec3 nlo = mix(texture(atlas_normal, uv_a.xy).xyz, texture(atlas_normal, uv_a.zw).xyz, blend.x);
		vec3 nhi = mix(texture(atlas_normal, uv_b.xy).xyz, texture(atlas_normal, uv_b.zw).xyz, blend.x);
		nb = mix(nlo, nhi, blend.y);
		ALPHA_TEXTURE_COORDINATE = uv_a.xy * atlas_px;
	}
	// atlas normals: Blender world space of the unrotated tree -> Godot (x, z, -y), then the yaw
	nb = nb * 2.0 - 1.0;
	vec3 nl = normalize(vec3(nb.x, nb.z, -nb.y) + vec3(0.0, 0.15, 0.0));
	float cy = cos(yaw);
	float sy = sin(yaw);
	vec3 nw = vec3(cy * nl.x + sy * nl.z, nl.y, -sy * nl.x + cy * nl.z);
	ALBEDO = c.rgb * tint;
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.45;
	ALPHA_ANTIALIASING_EDGE = 0.3;
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	ROUGHNESS = 0.9;
	SPECULAR = 0.15;
	// crown occlusion: the lower and inner crown sees less sky (the impostor bake has no AO)
	float crown = mix(0.6, 1.0, smoothstep(0.95, 0.3, UV.y)) * mix(0.82, 1.0, abs(UV.x - 0.5) * 2.0);
	AO = mix(1.0, sky_vis, 0.8) * crown;
	AO_LIGHT_AFFECT = 0.25;
	// sky rim on the crown silhouette (fresnel), cool and faint
	float rim = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 3.0);
	EMISSION = vec3(0.10, 0.13, 0.16) * rim * sky_vis * 0.35;
}

// Wrapped diffuse (needles and leaves are not a hard surface) plus translucency: sun shining
// through the crown toward the camera, tinted by the leaf colour (Mobile has no subsurface).
void light() {
	float vis = LIGHT_IS_DIRECTIONAL ? min(ATTENUATION, sun_vis) : ATTENUATION;
	float wrap = clamp((dot(NORMAL, LIGHT) + 0.35) / 1.35, 0.0, 1.0);
	float through = pow(clamp(-dot(VIEW, LIGHT), 0.0, 1.0), 4.0) * 0.7;
	vec3 leaf = clamp(ALBEDO * 2.2, vec3(0.0), vec3(1.0));
	DIFFUSE_LIGHT += (wrap * vis * LIGHT_COLOR + through * vis * LIGHT_COLOR * leaf) / PI;
}
