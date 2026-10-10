// Fjord water body, shared by water_foam.gdshader (depth-texture foam) and water_plain.gdshader.
//
// Ported from "stylized-components" by Christian Ortiz (Cortiz), MIT licence,
// https://github.com/cortiz2894/stylized-components (commit 1cece0a), via
// game-studio/templates/shaders/stylized_water.gdshader. Full licence text:
// LICENSE-stylized-components.txt next to this file.
// Changes for Wayfarer: realistic palette (deep blue-green, low-contrast cells), shallows tinted
// from a baked chart-depth map (Kartverket, CC BY 4.0), a sky-reflection fresnel, ripples and
// floaters removed (no gameplay in the spike). WATER_DEPTH_FOAM is defined by water_foam.gdshader.

group_uniforms pattern;
uniform float pattern_scale : hint_range(0.01, 1.5) = 0.45;
uniform float cell_smoothness : hint_range(0.01, 2.0) = 0.46;
uniform float edge_threshold : hint_range(0.0, 0.3) = 0.09;
uniform float edge_softness : hint_range(0.0, 0.1) = 0.1;
uniform vec2 flow = vec2(0.03, -0.10);
uniform float cell_speed : hint_range(0.0, 3.0) = 0.4;
uniform float noise_scale : hint_range(0.1, 10.0) = 0.6;
uniform float noise_flow_speed : hint_range(0.0, 2.0) = 0.08;
uniform float distort_amount : hint_range(0.0, 3.0) = 0.5;

group_uniforms colors;
uniform vec4 deep_color : source_color = vec4(0.035, 0.125, 0.145, 1.0);
uniform vec4 mid_color : source_color = vec4(0.065, 0.20, 0.215, 1.0);
uniform float mid_pos : hint_range(0.001, 0.999) = 0.5;
uniform vec4 highlight_color : source_color = vec4(0.16, 0.32, 0.33, 1.0);
uniform vec4 shallow_color : source_color = vec4(0.16, 0.38, 0.33, 1.0);
uniform float deep_opacity : hint_range(0.0, 1.0) = 0.9;
uniform float shallow_opacity : hint_range(0.0, 1.0) = 0.55;

group_uniforms reflection;
uniform vec4 sky_color : source_color = vec4(0.62, 0.74, 0.84, 1.0);
uniform float fresnel_power : hint_range(1.0, 8.0) = 5.0;
uniform float reflect_strength : hint_range(0.0, 1.0) = 0.45;

group_uniforms chart_depth;
// water_depth.png: 0 = shore, 1 = 60 m or deeper; rect = x0, z0, width, depth in metres
uniform sampler2D depth_map : filter_linear, repeat_disable;
uniform vec4 depth_rect;
uniform float shallow_depth : hint_range(0.01, 1.0) = 0.22;

group_uniforms distance_fade;
uniform float fade_distance : hint_range(10.0, 8000.0) = 3500.0;
uniform float fade_strength : hint_range(0.1, 5.0) = 1.3;
uniform vec4 horizon_color : source_color = vec4(0.70, 0.78, 0.85, 1.0);
uniform float horizon_mix : hint_range(0.0, 1.0) = 0.3;

group_uniforms intersection_foam;
uniform float foam_line_width : hint_range(0.01, 3.0) = 0.5;
uniform float foam_glow_width : hint_range(0.1, 10.0) = 1.8;
uniform vec4 foam_line_color : source_color = vec4(0.85, 0.90, 0.88, 1.0);
uniform float foam_line_opacity : hint_range(0.0, 1.0) = 0.85;
uniform vec4 foam_glow_color : source_color = vec4(0.45, 0.62, 0.60, 1.0);
uniform float foam_glow_opacity : hint_range(0.0, 1.0) = 0.35;

group_uniforms sparkles;
uniform float sparkle_cell : hint_range(0.5, 20.0) = 2.0;
uniform float sparkle_density : hint_range(0.0, 1.0) = 0.25;
uniform float sparkle_size : hint_range(0.01, 0.25) = 0.12;
uniform float sparkle_period : hint_range(0.2, 10.0) = 1.8;
uniform vec4 sparkle_color : source_color = vec4(1.0, 0.97, 0.9, 1.0);
uniform float sparkle_intensity : hint_range(0.0, 15.0) = 1.2;
uniform float sparkle_arm_sharpness : hint_range(1.0, 40.0) = 27.0;
uniform float sparkle_arm_falloff : hint_range(0.1, 8.0) = 4.8;
uniform float sparkle_glow_radius : hint_range(0.5, 12.0) = 12.0;
group_uniforms;

#ifdef WATER_DEPTH_FOAM
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
#endif

varying vec2 world_xz;

vec2 hash22(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.xx + p3.yz) * p3.zy);
}

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float smin(float a, float b, float k) {
	float h = max(k - abs(a - b), 0.0) / k;
	return min(a, b) - h * h * h * k / 6.0;
}

float voronoi_edge(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float md = 8.0;
	float sd = 8.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 n = vec2(float(x), float(y));
			vec2 pt = 0.5 + 0.5 * sin(TIME * cell_speed + 6.2831 * hash22(i + n));
			float d = length(n + pt - f);
			md = min(md, d);
			sd = smin(sd, d, cell_smoothness);
		}
	}
	return md - sd;
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

float fbm2(vec2 p) {
	return 0.5 * vnoise(p) + 0.25 * vnoise(p * 2.0);
}

vec2 foam_terms(float diff) {
	float line = 1.0 - smoothstep(0.0, foam_line_width, diff);
	float glow = exp(-diff / max(foam_glow_width, 0.001));
	return vec2(line, glow);
}

void vertex() {
	world_xz = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz;
}

void fragment() {
	vec2 distort = vec2(fbm2(world_xz * noise_scale + vec2(TIME * noise_flow_speed, 0.0)) - 0.5) * distort_amount;
	vec2 uv = world_xz * pattern_scale + flow * TIME + distort;
	float edge = voronoi_edge(uv);
	float t = smoothstep(edge_threshold - edge_softness, edge_threshold + edge_softness, edge);

	float mp = max(mid_pos, 1e-4);
	float seg0 = clamp(t / mp, 0.0, 1.0);
	float seg1 = clamp((t - mp) / max(1.0 - mp, 1e-4), 0.0, 1.0);
	vec3 color = mix(mix(deep_color.rgb, mid_color.rgb, seg0), mix(mid_color.rgb, highlight_color.rgb, seg1), step(mp, t));

	// chart depth: green-turquoise and see-through over shallow shelves
	float wd = texture(depth_map, (world_xz - depth_rect.xy) / depth_rect.zw).r;
	float shallow = 1.0 - smoothstep(0.0, shallow_depth, wd);
	color = mix(color, shallow_color.rgb, shallow * 0.8);
	float alpha = mix(deep_opacity, shallow_opacity, shallow);

	// sky reflection, stronger at grazing angles
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), fresnel_power);
	color = mix(color, sky_color.rgb, fres * reflect_strength);
	alpha = max(alpha, fres);

	vec2 foam = vec2(0.0);
#ifdef WATER_DEPTH_FOAM
	float raw = texture(depth_tex, SCREEN_UV).r;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec3 ndc = vec3(SCREEN_UV, raw) * 2.0 - 1.0;
#else
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, raw);
#endif
	vec4 view = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	float scene_d = -view.z / view.w;
	foam = foam_terms(abs(scene_d - (-VERTEX.z)));
#endif
	float line_a = foam.x * foam_line_opacity;
	float glow_a = foam.y * foam_glow_opacity;
	color = mix(color, foam_glow_color.rgb, glow_a);
	color = mix(color, foam_line_color.rgb, line_a);
	alpha = max(alpha, max(line_a, glow_a));

	float far = pow(clamp(length(world_xz - CAMERA_POSITION_WORLD.xz) / fade_distance, 0.0, 1.0), fade_strength);

	if (sparkle_density > 0.0 && sparkle_intensity > 0.0) {
		vec2 sp = world_xz / sparkle_cell;
		vec2 cell = floor(sp);
		float ph = hash12(cell + 71.3);
		float cyc = TIME / sparkle_period + ph;
		float id = floor(cyc);
		if (hash12(cell + id * 13.7) < sparkle_density) {
			vec2 c = 0.25 + 0.5 * hash22(cell + id * 7.1);
			vec2 q = (fract(sp) - c) / sparkle_size;
			float h_arm = exp(-abs(q.y) * sparkle_arm_sharpness) * exp(-abs(q.x) * sparkle_arm_falloff);
			float v_arm = exp(-abs(q.x) * sparkle_arm_sharpness) * exp(-abs(q.y) * sparkle_arm_falloff);
			float star = max(max(h_arm, v_arm), exp(-length(q) * sparkle_glow_radius));
			float fade_in_out = sin(fract(cyc) * PI);
			float s = star * fade_in_out * (1.0 - far) * (1.0 - shallow);
			color += sparkle_color.rgb * sparkle_intensity * s;
			alpha = max(alpha, clamp(s, 0.0, 1.0));
		}
	}

	color = mix(color, horizon_color.rgb, far * horizon_mix);
	ALBEDO = color;
	ALPHA = clamp(alpha, 0.0, 1.0);
}
