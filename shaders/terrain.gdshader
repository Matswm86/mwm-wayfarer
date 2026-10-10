// Fjord terrain: flat grid tiles displaced in the vertex shader from the baked height textures.
// Mesh contract (scripts/Terrain.gd): unit grid -0.5..0.5 in x/z, UV2.x = cells per edge,
// UV2.y = 1 on skirt vertices (dropped down to hide cracks between LOD levels).
// Node scale (tile, 1, tile), node y = 0.
// Material: grass green-gold low, rock on steep, alpine grass-rock high, snow above ~1300 m.
// Textures: Poly Haven (CC0) leafy_grass, aerial_rocks_02 (albedo + normal), aerial_grass_rock.

shader_type spatial;
render_mode world_vertex_coords, cull_back, specular_disabled;

#include "res://shaders/terrain_height.gdshaderinc"

uniform sampler2D grass_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_nrm : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D alpine_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform float grass_scale = 0.125;
// rock at two scales: fine detail and a large one that breaks the tiling
uniform float rock_scale = 0.05;
uniform float rock_scale_big = 0.0085;
uniform float rock_normal_strength = 0.9;
uniform float alpine_scale = 0.03;
uniform vec3 grass_tint : source_color = vec3(0.86, 0.86, 0.55);
uniform vec3 rock_tint : source_color = vec3(0.80, 0.83, 0.84);
uniform vec3 alpine_tint : source_color = vec3(0.85, 0.85, 0.72);
uniform vec3 snow_color : source_color = vec3(0.92, 0.94, 0.97);
uniform vec3 seabed_color : source_color = vec3(0.10, 0.17, 0.16);
// slope (normal.y) where soft ground turns to rock: cos 40 deg = 0.77, cos 32 deg = 0.85
uniform vec2 rock_slope = vec2(0.77, 0.85);
uniform vec2 alpine_height = vec2(550.0, 800.0);
uniform vec2 snow_height = vec2(1250.0, 1400.0);
// wet rock: darker in the splash band just above the waterline
uniform float wet_height = 2.5;
uniform float wet_darken = 0.5;
uniform float skirt_depth = 6.0;

varying vec3 wpos;
varying vec3 wnor;

void vertex() {
	float tile = length(MODEL_MATRIX[0].xyz);
	float spacing = tile / UV2.x;
	vec2 p = VERTEX.xz;
	float h = terrain_height(p, spacing);
	wnor = terrain_normal(p, spacing);
	VERTEX.y = h - UV2.y * (skirt_depth + spacing * 0.5);
	NORMAL = wnor;
	wpos = VERTEX;
}

void fragment() {
	vec3 n = normalize(wnor);
	// macro variation breaks texture tiling at distance
	float macro = texture(alpine_tex, wpos.xz * 0.0021).g;
	macro = mix(0.82, 1.18, macro);

	vec3 grass = texture(grass_tex, wpos.xz * grass_scale).rgb * grass_tint;
	vec3 alpine = texture(alpine_tex, wpos.xz * alpine_scale).rgb * alpine_tint;

	// rock: biplanar side projections (zy facing x, xy facing z), two scales each
	vec3 ax = abs(n);
	float wx = ax.x / max(ax.x + ax.z, 1e-4);
	vec2 uvx = wpos.zy;
	vec2 uvz = wpos.xy;
	vec3 rock_a = mix(texture(rock_tex, uvz * rock_scale).rgb, texture(rock_tex, uvx * rock_scale).rgb, wx);
	vec3 rock_b = mix(texture(rock_tex, uvz * rock_scale_big).rgb, texture(rock_tex, uvx * rock_scale_big).rgb, wx);
	vec3 rock = mix(rock_a, rock_b, 0.5) * 1.15 * rock_tint;
	vec2 nz = texture(rock_nrm, uvz * rock_scale).xy * 2.0 - 1.0;
	vec2 nx = texture(rock_nrm, uvx * rock_scale).xy * 2.0 - 1.0;
	vec2 nzb = texture(rock_nrm, uvz * rock_scale_big).xy * 2.0 - 1.0;
	vec2 nxb = texture(rock_nrm, uvx * rock_scale_big).xy * 2.0 - 1.0;
	nz += nzb;
	nx += nxb;
	// tangent frames of the two planes: (x, y) for the z-facing plane, (z, y) for the x-facing one
	vec3 dn = (1.0 - wx) * (nz.x * vec3(sign(n.z), 0.0, 0.0) + nz.y * vec3(0.0, 1.0, 0.0))
		+ wx * (nx.x * vec3(0.0, 0.0, -sign(n.x)) + nx.y * vec3(0.0, 1.0, 0.0));

	float a = smoothstep(alpine_height.x, alpine_height.y, wpos.y);
	vec3 soft = mix(grass, alpine, a);
	float r = 1.0 - smoothstep(rock_slope.x, rock_slope.y, n.y);
	vec3 col = mix(soft * macro, rock, r);
	// wet rock and stones at the waterline
	float wet = 1.0 - smoothstep(0.0, wet_height, wpos.y);
	col *= mix(1.0, wet_darken, wet * max(r, 0.5));
	// snow only on flatter high ground; steep faces stay rock
	float s = smoothstep(snow_height.x, snow_height.y, wpos.y + 120.0 * (macro - 1.0));
	s *= smoothstep(0.70, 0.85, n.y);
	col = mix(col, snow_color, s);
	col = mix(col, seabed_color, smoothstep(0.0, -6.0, wpos.y));

	vec3 nn = normalize(n + dn * rock_normal_strength * r * (1.0 - s));
	ALBEDO = col;
	ROUGHNESS = mix(0.95, 0.55, wet);
	NORMAL = normalize((VIEW_MATRIX * vec4(nn, 0.0)).xyz);
}
