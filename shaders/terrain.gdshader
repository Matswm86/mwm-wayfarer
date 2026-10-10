// Fjord terrain: flat grid tiles displaced in the vertex shader from the baked height textures.
// Mesh contract (scripts/Terrain.gd): unit grid -0.5..0.5 in x/z, UV2.x = cells per edge,
// UV2.y = 1 on skirt vertices (dropped down to hide cracks between LOD levels).
// Node scale (tile, 1, tile), node y = 0.
//
// Graphics pass 2026-10-10, ported from the approved Blender look (tools/art/scene_fjord.py
// rock_layer, docs/DESIGN.md 7.1 "Rock pass 10-10 b"):
// - faces steeper than about 48 deg are dark grey gneiss (albedo 0.18-0.32): the cliff_side scan
//   at 40 m and 7 m (7 m grain only within 350-900 m and not on Low), a 300 m macro noise,
//   vertical seep streaks, olive lichen; rockfall chutes from 400 m out (noise stretched along
//   the fall line); real gullies from the DEM concavity darken the rock and hold moss;
// - scree aprons (grey rubble) under the cliffs, from the baked scree mask;
// - grass low, greyer thinner turf with rock showing high, snow only on flatter ground above ~1250 m;
// - a darker glossy wet band 0-3 m above the water;
// - beyond 1.5 km the tiled scans fade (max 85 %) to flat forest green / rock grey;
// - baked light (tools/spike/bake_terrain_light.py): the sun is multiplied by the baked sun
//   visibility (the fjord walls shadow the valley, which the 160 m real-time shadows cannot),
//   the sky light by the baked sky visibility (AO; the Mobile renderer has no SSAO);
// - low specular (0.12), full roughness far: grazing sky reflections turned far slopes white.
// Textures: Poly Haven (CC0) leafy_grass, cliff_side (albedo + normal),
// gray_rocks. Heights and baked maps from Kartverket DTM, CC BY 4.0.

shader_type spatial;
render_mode world_vertex_coords, cull_back;

#include "res://shaders/terrain_height.gdshaderinc"

uniform sampler2D grass_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D cliff_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D cliff_nrm : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D scree_tex : source_color, filter_linear_mipmap, repeat_enable;
// generated seamless value noise (scripts/Terrain.gd), red channel, 512 px per tile
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
// baked light: R sun, G sky, B concavity, A scree; same rects as the height textures
uniform sampler2D coarse_light : filter_linear_mipmap, repeat_disable;
uniform sampler2D fine_light : filter_linear_mipmap, repeat_disable;

// colours are linear values, copied from the Blender look-dev material (no sRGB hint)
uniform bool detail_7m = true;
uniform float grass_scale = 0.14;
uniform vec3 grass_tint = vec3(0.62, 0.78, 0.50);
uniform vec3 alpine_tint = vec3(0.58, 0.63, 0.55);
uniform vec3 gneiss_base = vec3(0.27, 0.28, 0.29);
uniform vec3 lichen_color = vec3(0.20, 0.22, 0.14);
uniform vec3 moss_color = vec3(0.10, 0.15, 0.06);
uniform vec3 scree_tint = vec3(0.62, 0.64, 0.66);
uniform vec3 far_green = vec3(0.085, 0.11, 0.06);
uniform vec3 far_grey = vec3(0.13, 0.135, 0.14);
uniform vec3 snow_color = vec3(0.80, 0.83, 0.86);
uniform vec3 seabed_color = vec3(0.10, 0.17, 0.16);
uniform vec2 alpine_height = vec2(560.0, 760.0);
uniform vec2 snow_height = vec2(1250.0, 1400.0);
uniform float rock_normal_strength = 0.8;
uniform float skirt_depth = 6.0;
uniform float sky_ao_strength = 0.8;

varying vec3 wpos;
varying vec3 wnor;
varying float sun_vis;
varying float spec_k;

vec4 light_sample(vec2 p) {
	vec2 uvc = clamp((p - coarse_rect.xy) / coarse_rect.zw, vec2(0.0), vec2(1.0));
	uvc = uvc * (1.0 - coarse_texel) + 0.5 * coarse_texel;
	vec4 lc = texture(coarse_light, uvc);
	vec2 d = min(p - fine_rect.xy, fine_rect.xy + fine_rect.zw - p);
	float inner = min(d.x, d.y);
	if (inner <= 0.0) {
		return lc;
	}
	vec2 uvf = (p - fine_rect.xy) / fine_rect.zw;
	uvf = uvf * (1.0 - fine_texel) + 0.5 * fine_texel;
	return mix(lc, texture(fine_light, uvf), smoothstep(0.0, fine_feather, inner));
}

float lum(vec3 c) {
	return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

float maprange(float v, float a, float b, float c, float d) {
	return mix(c, d, clamp((v - a) / (b - a), 0.0, 1.0));
}

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
	float dist = length(wpos - CAMERA_POSITION_WORLD);
	vec4 baked = light_sample(wpos.xz);
	float concave = baked.b;

	// world noise at three scales
	float n80 = texture(noise_tex, wpos.xz / 80.0).r;          // ~12 m features
	float n300 = texture(noise_tex, wpos.xz / 2400.0).r;       // ~300 m features
	float mac = maprange(n300, 0.3, 0.7, 0.7, 1.2);

	// soft ground: grass low, alpine grass-rock high
	vec3 grass = texture(grass_tex, wpos.xz * grass_scale).rgb * grass_tint;
	// high ground: the same turf, greyer and thinner, rock showing through (no stretched aerial scan)
	vec3 alpine = mix(grass * alpine_tint * 1.4, gneiss_base * 0.9, 0.35 + 0.3 * n80);
	vec3 soft = mix(grass, alpine, smoothstep(alpine_height.x, alpine_height.y, wpos.y + 80.0 * (n80 - 0.5)));
	soft *= mac;
	// moss holds in the hollows
	soft = mix(soft, moss_color * (0.8 + 0.4 * n80), concave * 0.45);

	// gneiss: biplanar side projections (zy facing x, xy facing z)
	vec3 ax = abs(n);
	float wx = ax.x / max(ax.x + ax.z, 1e-4);
	vec2 uvx = wpos.zy;
	vec2 uvz = wpos.xy;
	// the top projection joins in on slopes up to about 60 deg so the scan never stretches
	float wy = smoothstep(0.35, 0.75, ax.y);
	vec3 big = mix(texture(cliff_tex, uvz / 40.0).rgb, texture(cliff_tex, uvx / 40.0).rgb, wx);
	big = mix(big, texture(cliff_tex, wpos.xz / 40.0).rgb, wy);
	vec3 gneiss = mix(gneiss_base, big, 0.2) * maprange(lum(big), 0.0, 0.5, 0.65, 1.3) * mac;
	vec2 nzb = texture(cliff_nrm, uvz / 40.0).xy * 2.0 - 1.0;
	vec2 nxb = texture(cliff_nrm, uvx / 40.0).xy * 2.0 - 1.0;
	float near_w = detail_7m ? maprange(dist, 900.0, 350.0, 0.0, 1.0) : 0.0;
	if (near_w > 0.0) {
		mat2 rot = mat2(vec2(0.825, 0.565), vec2(-0.565, 0.825));
		vec3 fine = mix(texture(cliff_tex, rot * uvz / 7.0).rgb, texture(cliff_tex, rot * uvx / 7.0).rgb, wx);
		fine = mix(fine, texture(cliff_tex, rot * wpos.xz / 7.0).rgb, wy);
		gneiss *= mix(1.0, maprange(lum(fine), 0.0, 0.6, 0.6, 1.3), near_w);
		nzb = mix(nzb, texture(cliff_nrm, rot * uvz / 7.0).xy * 2.0 - 1.0, near_w * 0.5);
		nxb = mix(nxb, texture(cliff_nrm, rot * uvx / 7.0).xy * 2.0 - 1.0, near_w * 0.5);
	}
	// vertical seep streaks: noise squashed along the fall line
	float along = mix(wpos.x, wpos.z, wx);
	float streak = texture(noise_tex, vec2(along / 33.0, wpos.y / 300.0)).r;
	streak = streak * 0.6 + texture(noise_tex, vec2(along / 9.0, wpos.y / 90.0) + 0.5).r * 0.4;
	gneiss *= maprange(streak, 0.3, 0.7, 0.6, 1.05);
	float lich = maprange(texture(noise_tex, wpos.xz / 160.0 + vec2(0.37, 0.11)).r, 0.55, 0.68, 0.0, 1.0);
	gneiss = mix(gneiss, lichen_color, lich * 0.45);
	gneiss = mix(gneiss, gneiss * 0.6 + moss_color * 0.3, concave * 0.5);

	// steep = 1 on faces steeper than about 52 deg, rock starts showing from about 40 deg
	float steep = maprange(n.y + (n80 - 0.5) * 0.25, 0.77, 0.62, 0.0, 1.0);
	vec3 col = mix(soft, gneiss, steep);

	// scree aprons under the cliffs
	vec3 scree = texture(scree_tex, wpos.xz / 6.0).rgb * scree_tint;
	float sc = clamp(baked.a * 1.3 - 0.45 + (n80 - 0.5) * 0.6, 0.0, 1.0) * (1.0 - steep);
	col = mix(col, scree * mac, sc);

	// far: fade the tiled scans to flat green / grey by slope (max 85 %)
	float far_w = maprange(dist, 1500.0, 5000.0, 0.0, 0.85);
	vec3 far_col = mix(far_green, far_grey, steep) * mac;
	col = mix(col, far_col, far_w);
	// rockfall chutes and ribs, readable from 400 m out
	float rib = abs(texture(noise_tex, vec2(along / 160.0, wpos.y / 1300.0) + vec2(0.71, 0.23)).r - 0.5);
	float gully_w = steep * maprange(dist, 400.0, 1500.0, 0.0, 1.0);
	col *= mix(1.0, maprange(rib, 0.0, 0.4, 0.6, 1.12), gully_w);
	col *= mix(1.0, 0.75, concave * steep);

	// snow on flatter high ground only
	float s = smoothstep(snow_height.x, snow_height.y, wpos.y + 120.0 * (n80 - 0.5));
	s *= smoothstep(0.72, 0.86, n.y);
	col = mix(col, snow_color, s);
	// wet band 0-3 m above the water: darker and glossy
	float wet = maprange(wpos.y + 1.5 * (n80 - 0.5), 3.2, 0.4, 0.0, 1.0);
	col = mix(col, col * 0.38, wet * 0.75);
	col = mix(col, seabed_color, smoothstep(0.0, -6.0, wpos.y));

	vec3 dn = (1.0 - wx) * (nzb.x * vec3(sign(n.z), 0.0, 0.0) + nzb.y * vec3(0.0, 1.0, 0.0))
		+ wx * (nxb.x * vec3(0.0, 0.0, -sign(n.x)) + nxb.y * vec3(0.0, 1.0, 0.0));
	vec3 nn = normalize(n + dn * rock_normal_strength * steep * (1.0 - wy) * (1.0 - s) * (1.0 - far_w));

	ALBEDO = col;
	float rough = mix(mix(0.95, 0.82, steep), 0.55, s);
	rough = mix(rough, 0.25, wet);
	ROUGHNESS = mix(rough, 1.0, far_w);
	SPECULAR = mix(0.12, 0.4, wet);
	spec_k = mix(0.12, 0.4, wet);
	NORMAL = normalize((VIEW_MATRIX * vec4(nn, 0.0)).xyz);
	AO = mix(1.0, baked.g, sky_ao_strength);
	AO_LIGHT_AFFECT = 0.0;
	sun_vis = baked.r;
}

// Lambert diffuse; the sun is limited by the baked sun visibility (min with the real-time shadow).
void light() {
	float vis = LIGHT_IS_DIRECTIONAL ? min(ATTENUATION, sun_vis) : ATTENUATION;
	DIFFUSE_LIGHT += clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * vis * LIGHT_COLOR / PI;
	vec3 h = normalize(VIEW + LIGHT);
	float r = max(ROUGHNESS, 0.05);
	float a2 = r * r * r * r;
	float ndh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float d = ndh * ndh * (a2 - 1.0) + 1.0;
	float spec = a2 / (PI * d * d) * spec_k;
	SPECULAR_LIGHT += spec * clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * vis * LIGHT_COLOR * 0.25;
}
