// Fjord terrain: flat grid tiles displaced in the vertex shader from the baked height textures.
// Mesh contract (scripts/Terrain.gd): unit grid -0.5..0.5 in x/z, UV2.x = cells per edge,
// UV2.y = 1 on skirt vertices (dropped down to hide cracks between LOD levels).
// Node scale (tile, 1, tile), node y = 0.
//
// Visual pass 2 (2026-10-10):
// - heights are float32 now (float16 stepped 0.5-1 m above 512 m and drew contour "wood grain");
// - lighting uses the baked per-texel DEM normal (bake_terrain_detail.py), so far tiles with
//   40-80 m vertex spacing still show every rib and chute of the 10 m data;
// - rock = true triplanar, three projections blended by the scan heights (no stretch on any
//   facing), at two scales (64 m bands + 12 m cracks) plus a 3 m grain near the camera on Ultra,
//   with the cliff scan normal at each scale. Gneiss colour comes from a palette; the scans give
//   foliation, cracks and cavities;
// - streaks follow the DEM's real drainage (flow accumulation): water-stained, darker, glossy
//   seams down the walls; moss in hollows and wet less-steep spots; paler dry ridges;
// - ground = meadow grass low, alpine turf high with heather patches, rock outcrops on convex
//   knolls, scree aprons, all blended by the scan heights; two scales against tiling;
// - wet band 0-3 m above the water; snow by height, slope and aspect (shaded faces hold more);
// - baked sun and sky visibility (bake_terrain_light.py) as before.
// quality: 0 = Low (one rock scale, no scan normals), 1 = Medium/High, 2 = Ultra (+ 3 m grain).
// Textures: Poly Haven (CC0) cliff_side, rock_face_03, leafy_grass, sparse_grass,
// forest_ground_04, rock_ground_02. Heights and baked maps from Kartverket DTM, CC BY 4.0.

shader_type spatial;
render_mode world_vertex_coords, cull_back;

#include "res://shaders/terrain_height.gdshaderinc"
#include "res://shaders/terrain_light.gdshaderinc"
#include "res://shaders/terrain_detail.gdshaderinc"

// R cliff brightness, G rock-face brightness, B cliff height, A rock-face height
uniform sampler2D rock_mask : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
// albedo + height in alpha
uniform sampler2D grass_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D turf_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D soil_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D scree_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
// generated seamless value noise (scripts/Terrain.gd), red channel
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
// forest stand density over the coarse grid (npz_to_godot.py): forest floor under the trees
uniform sampler2D forest_mask : filter_linear_mipmap, repeat_disable;
uniform int quality = 1;
uniform vec3 to_sun = vec3(-0.5, 0.5, 0.7);
// colours are linear values
uniform vec3 gneiss_dark = vec3(0.075, 0.078, 0.082);
uniform vec3 gneiss_light = vec3(0.36, 0.36, 0.35);
uniform vec3 rust_color = vec3(0.24, 0.15, 0.09);
uniform vec3 lichen_color = vec3(0.21, 0.23, 0.15);
uniform vec3 moss_color = vec3(0.07, 0.11, 0.035);
uniform vec3 heather_color = vec3(0.13, 0.095, 0.085);
uniform vec3 grass_tint = vec3(0.70, 0.84, 0.52);
uniform vec3 turf_tint = vec3(0.95, 1.0, 0.80);
uniform vec3 scree_tint = vec3(0.80, 0.82, 0.86);
uniform vec3 far_green = vec3(0.075, 0.10, 0.05);
uniform vec3 snow_color = vec3(0.82, 0.85, 0.88);
uniform vec3 seabed_color = vec3(0.10, 0.17, 0.16);
uniform vec2 alpine_height = vec2(520.0, 760.0);
uniform vec2 snow_height = vec2(1150.0, 1400.0);
uniform float rock_normal_strength = 0.9;
uniform float skirt_depth = 6.0;
uniform float sky_ao_strength = 0.85;

varying vec3 wpos;
varying vec3 vnor;
varying float sun_vis;
varying float spec_k;

float maprange(float v, float a, float b, float c, float d) {
	return mix(c, d, clamp((v - a) / (b - a), 0.0, 1.0));
}

// weights for three layers from base weights and per-layer heights (sharp, height-led seams)
vec3 height_weights(vec3 w, vec3 h, float depth) {
	vec3 s = w + h * depth * w;
	float m = max(s.x, max(s.y, s.z)) - depth;
	vec3 r = max(s - m, vec3(0.0));
	return r / max(r.x + r.y + r.z, 1e-4);
}

// two-layer height blend: t = 0 -> a, 1 -> b
float hblend(float ha, float hb, float t, float depth) {
	float a = ha + (1.0 - t) * 2.0;
	float b = hb + t * 2.0;
	float m = max(a, b) - depth;
	float wa = max(a - m, 0.0);
	float wb = max(b - m, 0.0);
	return wb / max(wa + wb, 1e-4);
}

void vertex() {
	float tile = length(MODEL_MATRIX[0].xyz);
	float spacing = tile / UV2.x;
	vec2 p = VERTEX.xz;
	float h = terrain_height(p, spacing);
	vnor = terrain_normal(p, spacing);
	VERTEX.y = h - UV2.y * (skirt_depth + spacing * 0.5);
	NORMAL = vnor;
	wpos = VERTEX;
}

void fragment() {
	float dist = length(wpos - CAMERA_POSITION_WORLD);
	vec4 baked = light_sample(wpos.xz);
	vec4 dt = detail_sample(wpos.xz);
	vec3 n = detail_normal(dt);
	float concave = baked.b;
	float flow = dt.b;
	float convex = dt.a;

	float n12 = texture(noise_tex, wpos.xz / 80.0).r;          // ~12 m patches
	float n60 = texture(noise_tex, wpos.xz / 420.0 + 0.31).r;  // ~60 m patches
	float n300 = texture(noise_tex, wpos.xz / 2400.0).r;       // ~300 m regions
	float mac = maprange(n300, 0.25, 0.75, 0.82, 1.15);

	// ---- rock: true triplanar, weights led by the scan heights
	vec3 an = abs(n);
	vec3 bw = pow(an, vec3(4.0));
	bw /= bw.x + bw.y + bw.z;
	// projections with v up the face, so scan "up" stays world up on every facing
	vec2 px = vec2(wpos.z * sign(n.x), -wpos.y);
	vec2 py = wpos.xz;
	vec2 pz = vec2(-wpos.x * sign(n.z), -wpos.y);
	// macro: the strata-free rock-face scan at 90 m and 37 m (no common period, so no visible
	// repeat on a 1 km wall); cliff strata only at the 12 m scale
	vec4 mx = texture(rock_mask, px / 90.0);
	vec4 my = texture(rock_mask, py / 90.0);
	vec4 mz = texture(rock_mask, pz / 90.0);
	vec3 tw = height_weights(bw, vec3(mx.a, my.a, mz.a), 0.35);
	vec4 m90 = mx * tw.x + my * tw.y + mz * tw.z;
	vec4 ax = texture(rock_mask, px / 37.0 + 0.53);
	vec4 ay = texture(rock_mask, py / 37.0 + 0.53);
	vec4 az = texture(rock_mask, pz / 37.0 + 0.53);
	vec4 m37 = ax * tw.x + ay * tw.y + az * tw.z;
	float tone = m90.g * 0.55 + m37.g * 0.45;
	float cav = m90.a * 0.5 + m37.a * 0.5;
	vec3 dn = vec3(0.0);
	float near12 = maprange(dist, 1400.0, 500.0, 0.0, 1.0);
	if (quality > 0) {
		vec2 tx = texture(rock_nrm, px / 37.0 + 0.53).xy * 2.0 - 1.0;
		vec2 ty = texture(rock_nrm, py / 37.0 + 0.53).xy * 2.0 - 1.0;
		vec2 tz = texture(rock_nrm, pz / 37.0 + 0.53).xy * 2.0 - 1.0;
		dn = tw.x * vec3(0.0, tx.y, tx.x * sign(n.x)) + tw.y * vec3(ty.x, 0.0, ty.y)
			+ tw.z * vec3(-tz.x * sign(n.z), tz.y, 0.0);
		if (near12 > 0.0) {
			vec4 dx = texture(rock_mask, px / 12.0 + 0.37);
			vec4 dy = texture(rock_mask, py / 12.0 + 0.37);
			vec4 dz = texture(rock_mask, pz / 12.0 + 0.37);
			vec3 tw2 = height_weights(bw, vec3(dx.b, dy.b, dz.b), 0.3);
			vec4 m12 = dx * tw2.x + dy * tw2.y + dz * tw2.z;
			tone = mix(tone, tone * 0.6 + m12.r * 0.45, near12);
			cav = mix(cav, cav * 0.5 + m12.b * 0.5, near12);
			vec2 ux = texture(rock_nrm, px / 12.0 + 0.37).xy * 2.0 - 1.0;
			vec2 uy = texture(rock_nrm, py / 12.0 + 0.37).xy * 2.0 - 1.0;
			vec2 uz = texture(rock_nrm, pz / 12.0 + 0.37).xy * 2.0 - 1.0;
			vec3 dn2 = tw2.x * vec3(0.0, ux.y, ux.x * sign(n.x)) + tw2.y * vec3(uy.x, 0.0, uy.y)
				+ tw2.z * vec3(-uz.x * sign(n.z), uz.y, 0.0);
			dn = mix(dn, dn * 0.5 + dn2 * 0.8, near12);
		}
		if (quality > 1 && dist < 70.0) {
			float k = maprange(dist, 70.0, 25.0, 0.0, 1.0);
			vec2 gx = texture(rock_nrm, px / 3.0 + 0.71).xy * 2.0 - 1.0;
			vec2 gy = texture(rock_nrm, py / 3.0 + 0.71).xy * 2.0 - 1.0;
			vec2 gz = texture(rock_nrm, pz / 3.0 + 0.71).xy * 2.0 - 1.0;
			dn += k * 0.6 * (tw.x * vec3(0.0, gx.y, gx.x) + tw.y * vec3(gy.x, 0.0, gy.y)
				+ tw.z * vec3(gz.x, gz.y, 0.0));
			float g3 = texture(rock_mask, py / 3.0 + 0.71).g * tw.y
				+ texture(rock_mask, px / 3.0 + 0.71).g * (tw.x + tw.z);
			tone = mix(tone, tone * 0.7 + g3 * 0.35, k);
		}
	}
	// gneiss: dark to light grey by the scan tone, broad 60-300 m variation, foliation bands
	// (gently dipping strata from a squashed noise), rusty iron stain where water runs
	vec2 hdir = normalize(vec2(-n.z, n.x) + vec2(1e-4));
	float across = dot(wpos.xz, hdir);
	float strata = texture(noise_tex, vec2(across / 900.0, (wpos.y + across * 0.12) / 22.0)).r;
	float t = clamp(tone * 0.8 + (strata - 0.5) * 0.3 + (n60 - 0.5) * 0.35 - 0.05, 0.0, 1.0);
	vec3 gneiss = mix(gneiss_dark, gneiss_light, t * t * (3.0 - 2.0 * t)) * mac;
	// vertical seep streaks across the face plus the DEM's real drainage lines
	float streak = texture(noise_tex, vec2(across / 30.0, wpos.y / 340.0)).r * 0.6
		+ texture(noise_tex, vec2(across / 8.0, wpos.y / 110.0) + 0.5).r * 0.4;
	float seep = clamp(flow * 1.6 + maprange(streak, 0.55, 0.8, 0.0, 0.6), 0.0, 1.0);
	gneiss = mix(gneiss, gneiss * 0.42, seep * 0.75);
	gneiss = mix(gneiss, rust_color * 0.6, seep * maprange(n60, 0.55, 0.8, 0.0, 0.35));
	// dry ridges paler, lichen on them, cavities darker
	gneiss *= 1.0 + convex * 0.25;
	float lich = maprange(texture(noise_tex, wpos.xz / 160.0 + vec2(0.37, 0.11)).r + convex * 0.25, 0.55, 0.75, 0.0, 1.0);
	gneiss = mix(gneiss, lichen_color, lich * 0.4);
	gneiss *= mix(0.55, 1.0, cav);
	// moss on benches, hollows and wet less-steep rock
	float rock_moss = clamp(concave * 0.7 + flow * 0.5, 0.0, 1.0) * maprange(an.y, 0.45, 0.8, 0.2, 1.0);
	gneiss = mix(gneiss, moss_color * (0.8 + 0.4 * n12), rock_moss * 0.6);

	// ---- soft ground: meadow grass low, turf and heather high, two scales against tiling
	float gnear = maprange(dist, 250.0, 60.0, 0.0, 1.0);
	vec4 g_big = texture(grass_tex, wpos.xz / 31.0);
	vec4 g_small = texture(grass_tex, wpos.xz / 6.5);
	vec4 grass = mix(g_big, g_small, 0.35 + 0.65 * gnear);
	vec4 turf = texture(turf_tex, wpos.xz / 9.0);
	float alp = smoothstep(alpine_height.x, alpine_height.y, wpos.y + 120.0 * (n60 - 0.5));
	float tw_alp = hblend(grass.a, turf.a, clamp(alp + (n12 - 0.5) * 0.4, 0.0, 1.0), 0.4);
	vec3 soft = mix(grass.rgb * grass_tint, turf.rgb * turf_tint, tw_alp);
	// heather: patches on drier, convex ground from 150 m up
	float heath = maprange(n60 + convex * 0.4 - flow * 0.6, 0.55, 0.72, 0.0, 1.0)
		* smoothstep(150.0, 300.0, wpos.y) * (1.0 - smoothstep(900.0, 1100.0, wpos.y));
	soft = mix(soft, heather_color * (0.7 + 0.6 * turf.a), heath * 0.45);
	// lush, darker, mossier in the wet hollows
	soft = mix(soft, moss_color * (0.9 + 0.5 * grass.a), clamp(concave * 0.5 + flow * 0.45, 0.0, 0.7));
	soft *= mac;
	// soil and forest floor on steeper soft ground, along the drainage and under the stands
	vec2 fuv = clamp((wpos.xz - coarse_rect.xy) / coarse_rect.zw, vec2(0.0), vec2(1.0));
	float forest = texture(forest_mask, fuv * (1.0 - coarse_texel) + 0.5 * coarse_texel).r;
	vec4 soil = texture(soil_tex, wpos.xz / 7.0);
	float bare = maprange(an.y, 0.86, 0.74, 0.0, 0.7) + flow * 0.2 + forest * 0.8;
	soft = mix(soft, soil.rgb * 0.75, hblend(grass.a, soil.a, clamp(bare, 0.0, 1.0), 0.35) * 0.8);

	// steep = 1 on faces steeper than about 50 deg, rock from about 38 deg; rock outcrops on
	// convex knolls and edges break through the turf
	float outcrop = maprange(convex + (n12 - 0.5) * 0.6, 0.45, 0.75, 0.0, 1.0) * maprange(an.y, 0.95, 0.8, 0.0, 1.0);
	float steep_t = clamp(maprange(an.y + (n12 - 0.5) * 0.18, 0.74, 0.6, 0.0, 1.0) + outcrop, 0.0, 1.0);
	float steep = hblend(grass.a * 0.6, cav, steep_t, 0.25);
	vec3 col = mix(soft, gneiss, steep);

	// scree aprons under the cliffs
	vec4 scr = texture(scree_tex, wpos.xz / 5.0);
	float sc = clamp(baked.a * 1.3 - 0.45 + (n12 - 0.5) * 0.6, 0.0, 1.0) * (1.0 - steep);
	sc = hblend(grass.a, scr.a, sc, 0.3);
	col = mix(col, scr.rgb * scree_tint * mac * 0.8, sc);

	// far: the tiled detail fades toward flat forest green on soft ground (rock keeps its
	// macro scan: at 64 m it does not tile visibly)
	float far_w = maprange(dist, 1800.0, 6000.0, 0.0, 0.7);
	vec3 far_soft = far_green * mac * mix(1.0, 0.6, forest);
	col = mix(col, mix(far_soft, col, steep), far_w);

	// snow: high, flatter, and more on faces turned away from the sun
	float shade_aspect = 0.5 - 0.5 * dot(normalize(n.xz + vec2(1e-4)), normalize(to_sun.xz));
	float s = smoothstep(snow_height.x, snow_height.y, wpos.y + 160.0 * (n60 - 0.5) + 180.0 * shade_aspect);
	s *= smoothstep(0.55, 0.8, an.y + convex * -0.1 + concave * 0.15);
	col = mix(col, snow_color, s);
	// wet band 0-3 m above the water: darker and glossy
	float wet = maprange(wpos.y + 1.5 * (n12 - 0.5), 3.2, 0.4, 0.0, 1.0);
	// the band follows sloping shores; flat deltas and floodplains at 1-3 m stay dry
	wet *= 1.0 - smoothstep(0.985, 0.997, an.y);
	col = mix(col, col * 0.38, wet * 0.75);
	col = mix(col, seabed_color, smoothstep(0.0, -6.0, wpos.y));

	vec3 nn = normalize(n + dn * rock_normal_strength * steep * (1.0 - s));
	ALBEDO = col;
	float rough = mix(mix(0.93, 0.8, steep), 0.55, s);
	rough = mix(rough, 0.6, seep * steep);
	rough = mix(rough, 0.35, wet);
	ROUGHNESS = mix(rough, 1.0, far_w);
	spec_k = mix(mix(0.1, 0.18, seep * steep), 0.35, wet);
	SPECULAR = spec_k;
	NORMAL = normalize((VIEW_MATRIX * vec4(nn, 0.0)).xyz);
	// sky light: baked horizon occlusion times the scan cavities on rock
	AO = mix(1.0, baked.g, sky_ao_strength) * mix(1.0, 0.55 + 0.45 * cav, steep);
	AO_LIGHT_AFFECT = 0.0;
	sun_vis = baked.r;
}

// Lambert diffuse; the sun is limited by the baked sun visibility (min with the real-time shadow).
// Specular is occluded by the same visibility and by the scan cavities.
void light() {
	float vis = LIGHT_IS_DIRECTIONAL ? min(ATTENUATION, sun_vis) : ATTENUATION;
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	DIFFUSE_LIGHT += ndl * vis * LIGHT_COLOR / PI;
	vec3 h = normalize(VIEW + LIGHT);
	float r = max(ROUGHNESS, 0.05);
	float a2 = r * r * r * r;
	float ndh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float d = ndh * ndh * (a2 - 1.0) + 1.0;
	float spec = a2 / (PI * d * d) * spec_k;
	SPECULAR_LIGHT += spec * ndl * vis * LIGHT_COLOR * 0.25;
}
