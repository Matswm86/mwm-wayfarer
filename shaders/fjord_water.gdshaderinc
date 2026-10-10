// Fjord water body, shared by water_foam.gdshader (depth-texture foam) and water_plain.gdshader.
//
// Realistic lit water (graphics pass 2026-10-10): a dark, almost black-green body that is mostly
// reflection. The engine does the reflection: low roughness + Schlick fresnel pick up the
// ReflectionProbes over the fjord (scripts/Main.gd) and the sky, so the walls mirror in the water.
// Waves are two scrolling normal maps (generated NoiseTextures, no files) plus a slow swell.
// Shallows: lighter, see-through green over the chart-depth shelf (Kartverket, CC BY 4.0).
// Shore foam: a broken white band from the chart depth (all presets) and, with WATER_DEPTH_FOAM,
// the depth-buffer intersection line (costs a depth copy per frame).
//
// The hash and foam helpers come from "stylized-components" by Christian Ortiz (Cortiz), MIT
// licence, https://github.com/cortiz2894/stylized-components (commit 1cece0a); licence text in
// LICENSE-stylized-components.txt next to this file.

uniform sampler2D wave_a : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D wave_b : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float wave_scale_a = 0.045;
uniform float wave_scale_b = 0.11;
uniform vec2 wave_dir_a = vec2(0.020, -0.012);
uniform vec2 wave_dir_b = vec2(-0.014, -0.026);
uniform float wave_strength = 0.16;
// waves calm down with distance so the far water stays a clean mirror
uniform float wave_fade_distance = 1800.0;

uniform vec3 deep_color : source_color = vec3(0.010, 0.032, 0.036);
uniform vec3 shallow_color : source_color = vec3(0.10, 0.22, 0.17);
uniform float deep_alpha = 0.96;
uniform float shallow_alpha = 0.62;
uniform float roughness_near = 0.03;
uniform float roughness_far = 0.01;

// water_depth.png: 0 = shore, 1 = 60 m or deeper; rect = x0, z0, width, depth in metres
uniform sampler2D depth_map : filter_linear, repeat_disable;
uniform vec4 depth_rect;
uniform float shallow_depth = 0.12;
uniform float foam_band = 0.02;
uniform vec3 foam_color : source_color = vec3(0.82, 0.86, 0.85);

#ifdef WATER_DEPTH_FOAM
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
uniform float foam_line_width = 0.6;
#endif

varying vec3 wpos;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(hash12(i), hash12(i + vec2(1.0, 0.0)), f.x),
		mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), f.x),
		f.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 xz = wpos.xz;
	float dist = length(wpos - CAMERA_POSITION_WORLD);
	float calm = clamp(dist / wave_fade_distance, 0.0, 1.0);

	vec3 na = texture(wave_a, xz * wave_scale_a + wave_dir_a * TIME).xyz;
	vec3 nb = texture(wave_b, xz * wave_scale_b + wave_dir_b * TIME).xyz;
	vec3 n = normalize(na + nb - 1.0);
	NORMAL_MAP = mix(vec3(0.5, 0.5, 1.0), n, wave_strength * (1.0 - 0.8 * calm));
	NORMAL_MAP_DEPTH = 1.0;

	float wd = texture(depth_map, (xz - depth_rect.xy) / depth_rect.zw).r;
	float shallow = 1.0 - smoothstep(0.0, shallow_depth, wd);
	vec3 col = mix(deep_color, shallow_color, shallow * 0.85);
	float alpha = mix(deep_alpha, shallow_alpha, shallow);

	// broken foam band where the chart depth reaches the shore
	float band = 1.0 - smoothstep(0.0, foam_band, wd);
	float breakup = vnoise(xz * 0.9 + vec2(TIME * 0.15, 0.0)) * 0.6 + vnoise(xz * 3.1) * 0.4;
	float foam = band * smoothstep(0.35, 0.75, breakup);

#ifdef WATER_DEPTH_FOAM
	float raw = texture(depth_tex, SCREEN_UV).r;
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, raw);
	vec4 view = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	float scene_d = -view.z / view.w;
	float diff = abs(scene_d - (-VERTEX.z));
	float line = 1.0 - smoothstep(0.0, foam_line_width * (0.6 + breakup), diff);
	foam = max(foam, line * 0.9);
#endif

	ALBEDO = mix(col, foam_color, foam);
	ROUGHNESS = mix(mix(roughness_near, roughness_far, calm), 0.7, foam);
	METALLIC = 0.0;
	SPECULAR = mix(0.5, 0.2, foam);
	ALPHA = clamp(max(alpha, foam), 0.0, 1.0);
}
