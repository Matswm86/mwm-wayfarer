// Ground cover round the player (graphics pass 2026-10-10): grass clumps, dry tall grass, ferns
// and small shrubs, each two crossed cards cut from renders of Poly Haven plant scans (CC0,
// tools/spike/bake_ground_cards.py). One MultiMeshInstance3D on a world grid that follows the
// player in GRASS_SPACING steps (scripts/Grass.gd); kind, jitter, turn and size come from a hash
// of the grid point, so the field stays put. Plants thin out toward `grass_radius` and vanish on
// water, rock and high ground. Lit by the sun times the baked terrain sun visibility, sky light by
// the baked sky visibility.
//
// The grid/hash placement and wind come from the earlier blade shader, ported from
// "stylized-components" by Christian Ortiz (Cortiz), MIT licence (commit 1cece0a); licence text in
// LICENSE-stylized-components.txt next to this file.
//
// Mesh contract: two crossed unit quads, x -0.5..0.5, y 0..1, UV (0,1) bottom left.

shader_type spatial;
render_mode cull_disabled, world_vertex_coords;

#include "res://shaders/terrain_height.gdshaderinc"
#include "res://shaders/terrain_light.gdshaderinc"

uniform sampler2D cards : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float card_count = 6.0;
// per card: size in metres (square frames)
uniform float card_size[6];
// per card: extra scale and brightness (the short-grass scans are small and dark)
uniform float card_scale[6];
uniform float card_gain[6];
// cumulative pick weights per card (last = 1.0)
uniform float card_pick[6];
uniform vec3 grass_center;
// forest stand density (npz_to_godot.py): ferns and shrubs under the trees, not meadow grass
uniform sampler2D forest_mask : filter_linear, repeat_disable;
uniform float grass_radius = 40.0;
uniform float grid_spacing = 0.6;
// far ring (Ultra): fades in from inner_radius, bigger clumps
uniform float inner_radius = 0.0;
uniform float size_mult = 1.0;
uniform vec2 size_jitter = vec2(0.8, 1.3);
uniform vec3 tint = vec3(1.2, 1.3, 1.05);
uniform float wind_strength = 0.08;
uniform float wind_speed = 1.3;
uniform vec2 wind_dir = vec2(1.0, 0.3);

varying float sun_vis;
varying float sky_vis;
varying float shade;
varying float gain;
varying vec3 soft_n;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

void vertex() {
	vec3 grid_pt = MODEL_MATRIX[3].xyz;
	vec2 key = floor(grid_pt.xz / grid_spacing + 0.5);
	float r1 = hash12(key);
	float r2 = hash12(key + 17.3);
	float r3 = hash12(key + 41.9);
	float r4 = hash12(key + 73.1);
	vec2 base_xz = grid_pt.xz + (vec2(r1, r2) - 0.5) * grid_spacing;
	float kind = 0.0;
	for (int i = 0; i < 5; i++) {
		kind += step(card_pick[i], r4);
	}
	vec2 fuv = clamp((grid_pt.xz - coarse_rect.xy) / coarse_rect.zw, vec2(0.0), vec2(1.0));
	float forest = textureLod(forest_mask, fuv * (1.0 - coarse_texel) + 0.5 * coarse_texel, 0.0).r;
	if (hash12(key + 5.7) < forest * 0.85) {
		kind = r3 < 0.65 ? 4.0 : 5.0;
	}
	float size = card_size[int(kind)] * card_scale[int(kind)] * mix(size_jitter.x, size_jitter.y, r3);

	float ground = terrain_height(base_xz, 1.0);
	vec3 gn = terrain_normal(base_xz, 1.5);
	float gd = distance(base_xz, grass_center.xz);
	float keep = 1.0 - smoothstep(grass_radius * 0.75, grass_radius, gd);
	keep *= inner_radius > 0.0 ? smoothstep(inner_radius * 0.8, inner_radius, gd) : 1.0;
	size *= size_mult;
	keep *= smoothstep(0.4, 1.0, ground) * smoothstep(0.72, 0.82, gn.y) * (1.0 - smoothstep(500.0, 600.0, ground));
	size *= keep;

	vec3 local = VERTEX - grid_pt;
	float ang = r1 * 6.2831;
	float ca = cos(ang);
	float sa = sin(ang);
	vec3 p = vec3(local.x * ca - local.z * sa, local.y, local.x * sa + local.z * ca) * size;
	vec2 wd = normalize(wind_dir);
	float sway = sin(dot(base_xz, wd) * 0.4 + TIME * wind_speed) * wind_strength * local.y * local.y;
	p.xz += wd * sway * size;
	VERTEX = vec3(base_xz.x, ground - 0.03, base_xz.y) + p;
	// soft normals: mostly up, so the cards light like a canopy, not like flat boards
	NORMAL = normalize(vec3(-sa, 0.0, ca) * 0.35 + vec3(0.0, 1.0, 0.0));
	soft_n = NORMAL;
	UV = vec2((kind + UV.x) / card_count, UV.y);
	vec4 baked = light_sample(base_xz);
	sun_vis = baked.r;
	sky_vis = baked.g;
	shade = 0.85 + 0.3 * r2;
	gain = card_gain[int(kind)];
}

void fragment() {
	vec4 c = texture(cards, UV);
	ALBEDO = c.rgb * tint * shade * gain;
	// same soft normal on both sides of the card (cull_disabled would flip it on the back face)
	NORMAL = normalize((VIEW_MATRIX * vec4(soft_n, 0.0)).xyz);
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.4;
	ALPHA_ANTIALIASING_EDGE = 0.3;
	ALPHA_TEXTURE_COORDINATE = UV * vec2(512.0 * card_count, 512.0);
	ROUGHNESS = 0.85;
	SPECULAR = 0.2;
	// darker at the root, where the clump shades itself
	AO = mix(1.0, sky_vis, 0.8) * mix(0.45, 1.0, smoothstep(1.0, 0.35, UV.y));
	AO_LIGHT_AFFECT = 0.35;
}

void light() {
	float vis = LIGHT_IS_DIRECTIONAL ? min(ATTENUATION, sun_vis) : ATTENUATION;
	float wrap = clamp((dot(NORMAL, LIGHT) + 0.4) / 1.4, 0.0, 1.0);
	// thin blades glow when the sun is behind them
	float through = pow(clamp(-dot(VIEW, LIGHT), 0.0, 1.0), 3.0) * 0.8;
	vec3 leaf = clamp(ALBEDO * 2.0, vec3(0.0), vec3(1.0));
	DIFFUSE_LIGHT += (wrap * vis * LIGHT_COLOR + through * vis * LIGHT_COLOR * leaf) / PI;
}
