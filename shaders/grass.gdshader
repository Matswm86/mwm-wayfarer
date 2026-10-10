// Grass blades round the player for one MultiMeshInstance3D.
//
// Ported from "stylized-components" by Christian Ortiz (Cortiz), MIT licence,
// https://github.com/cortiz2894/stylized-components (commit 1cece0a), via
// game-studio/templates/shaders/stylized_grass.gdshader. Full licence text:
// LICENSE-stylized-components.txt next to this file.
// Changes for Wayfarer: green-gold palette; the blade stands on the terrain height textures
// (terrain_height.gdshaderinc); jitter, turn and size come from a hash of the world grid point,
// so the field stays put while the MultiMesh node follows the player in GRASS_SPACING steps;
// blades fade out toward `grass_radius` and vanish on water, rock and high ground.
//
// Mesh contract (scripts/Grass.gd): one clump of thin blades in metres, about 0.45 m tall;
// UV.x = per-blade random value (colour variation), UV.y = 0 at the root, 1 at the tip.
// Instance transforms are pure translations on a regular grid.

shader_type spatial;
render_mode cull_disabled, specular_disabled, world_vertex_coords;

#include "res://shaders/terrain_height.gdshaderinc"

group_uniforms field;
uniform vec3 grass_center;
uniform float grass_radius = 40.0;
uniform float grid_spacing = 0.5;
uniform vec2 clump_scale = vec2(0.6, 1.35);
// the terrain's own grass texture: blade roots take its colour so the clump melts into the ground
uniform sampler2D grass_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform float grass_tex_scale = 0.125;
uniform vec3 grass_tex_tint : source_color = vec3(0.86, 0.86, 0.55);

group_uniforms wind;
uniform float wind_strength : hint_range(0.0, 1.0) = 0.12;
uniform float wind_speed : hint_range(0.0, 5.0) = 1.3;
uniform float wind_freq : hint_range(0.01, 3.0) = 0.4;
uniform float wind_turbulence : hint_range(0.0, 1.0) = 0.3;
uniform float wind_lean : hint_range(0.0, 1.0) = 0.4;
uniform vec2 wind_dir = vec2(1.0, 0.3);

group_uniforms colors;
uniform vec4 color_bottom : source_color = vec4(0.30, 0.36, 0.12, 1.0);
uniform vec4 color_top : source_color = vec4(0.66, 0.62, 0.30, 1.0);
uniform float brightness : hint_range(0.0, 2.0) = 0.9;
uniform float grad_start : hint_range(0.0, 1.0) = 0.1;
uniform float grad_end : hint_range(0.0, 1.0) = 1.0;
uniform float grad_power : hint_range(0.1, 4.0) = 1.4;
uniform vec4 ground_color : source_color = vec4(0.33, 0.37, 0.16, 1.0);
uniform float ground_blend : hint_range(0.0, 1.0) = 0.9;
uniform float ground_blend_height : hint_range(0.01, 1.0) = 0.45;

group_uniforms patches;
uniform vec4 patch_lush : source_color = vec4(0.42, 0.52, 0.18, 1.0);
uniform vec4 patch_dry : source_color = vec4(0.76, 0.66, 0.36, 1.0);
uniform float patch_strength : hint_range(0.0, 1.0) = 0.45;
uniform float patch_scale : hint_range(0.01, 2.0) = 0.12;
uniform float patch_bias : hint_range(0.1, 4.0) = 1.2;

group_uniforms translucency;
uniform vec4 trans_color : source_color = vec4(0.80, 0.80, 0.40, 1.0);
uniform float trans_strength : hint_range(0.0, 5.0) = 1.6;
uniform float trans_power : hint_range(0.5, 10.0) = 3.0;
uniform float trans_tip : hint_range(0.0, 1.0) = 0.6;
uniform float trans_shadow : hint_range(0.0, 1.0) = 1.0;

group_uniforms lighting;
uniform bool receive_shadow = true;
group_uniforms;

varying float blade_h;
varying float blade_rand;
varying vec2 blade_root;
varying float blade_patch;
varying vec3 blade_n;

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
	vec3 grid_pt = MODEL_MATRIX[3].xyz;
	vec2 key = floor(grid_pt.xz / grid_spacing + 0.5);
	float r1 = hash12(key);
	float r2 = hash12(key + 17.3);
	float r3 = hash12(key + 41.9);
	vec2 base_xz = grid_pt.xz + (vec2(r1, r2) - 0.5) * grid_spacing;
	vec3 local = VERTEX - grid_pt;
	float h = UV.y;
	blade_h = h;
	blade_rand = UV.x;

	float ang = r3 * 6.2831;
	float ca = cos(ang);
	float sa = sin(ang);
	float sc = mix(clump_scale.x, clump_scale.y, r1 * r2 + 0.3 * r3);
	// fade toward the edge of the field, and off on water, rock and high ground
	float ground = terrain_height(base_xz, 1.0);
	vec3 gn = terrain_normal(base_xz, 1.5);
	float keep = 1.0 - smoothstep(grass_radius * 0.7, grass_radius, distance(base_xz, grass_center.xz));
	keep *= smoothstep(0.3, 0.9, ground) * smoothstep(0.72, 0.82, gn.y) * (1.0 - smoothstep(500.0, 600.0, ground));
	float len = sc * keep;
	vec3 p = vec3(local.x * ca - local.z * sa, local.y, local.x * sa + local.z * ca) * len;
	vec3 base = vec3(base_xz.x, ground - 0.04, base_xz.y);
	VERTEX = base + p;
	blade_root = base.xz;
	NORMAL = normalize(vec3(-sa, 0.0, ca));
	blade_patch = 0.65 * vnoise(base.xz * patch_scale) + 0.35 * vnoise(base.xz * patch_scale * 2.0);

	float mask = h * h;
	vec2 wd = normalize(wind_dir + vec2(1e-5, 0.0));
	vec2 perp = vec2(-wd.y, wd.x);
	float ph = dot(VERTEX.xz, wd) * wind_freq;
	float primary = sin(ph + TIME * wind_speed);
	float second = sin(ph * 2.6 + TIME * wind_speed * 1.8 + 1.3) * 0.35;
	float turb = sin(dot(VERTEX.xz, perp) * wind_freq * 1.9 + TIME * wind_speed * 0.7 + 2.6) * wind_turbulence;
	float push = ((primary + second + turb) * wind_strength + wind_lean * wind_strength) * mask;
	VERTEX.xz += wd * push * len;
	VERTEX.y -= abs(push) * len * 0.3 * mask;

	blade_n = normalize((VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float g = clamp((blade_h - grad_start) / max(grad_end - grad_start, 0.001), 0.0, 1.0);
	vec3 c = mix(color_bottom.rgb, color_top.rgb, pow(g, grad_power));
	float pt = pow(clamp(blade_patch * 0.7 + blade_rand * 0.3, 0.0, 1.0), patch_bias);
	c = mix(c, mix(patch_lush.rgb, patch_dry.rgb, pt), patch_strength);
	c *= brightness * mix(0.8, 1.15, blade_rand);
	vec3 soil = texture(grass_tex, blade_root * grass_tex_scale).rgb * grass_tex_tint;
	c = mix(c, soil, ground_blend * (1.0 - smoothstep(0.0, ground_blend_height, blade_h)));
	ALBEDO = c;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
}

void light() {
	float att = receive_shadow ? ATTENUATION : 1.0;
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	DIFFUSE_LIGHT += ndl * att * LIGHT_COLOR / PI;
	float back = pow(max(dot(VIEW, -LIGHT), 0.0), trans_power);
	float thin = mix(1.0, blade_h, trans_tip);
	float edge = 1.0 - abs(dot(blade_n, LIGHT));
	float sh = mix(1.0, att, trans_shadow);
	SPECULAR_LIGHT += trans_color.rgb * trans_strength * back * thin * edge * sh * LIGHT_COLOR / PI;
}
