// Terrain height lookup shared by the terrain, grass and anything else that sits on the ground.
// Heights: Kartverket DTM (c) Kartverket, CC BY 4.0, baked by tools/terrain/npz_to_godot.py.
// Two half-float height textures: the 10 m crop of the whole valley and the 2.5 m area round
// the village. Inside the fine area the fine data wins, feathered over `fine_feather` metres
// (same blend as tools/art/scene_fjord.py dem_h and the CPU collision sampler).

uniform sampler2D coarse_h : filter_linear_mipmap, repeat_disable;
uniform sampler2D fine_h : filter_linear_mipmap, repeat_disable;
// x0, z0 (Godot metres of the first sample), width, depth (metres between first and last sample)
uniform vec4 coarse_rect;
uniform vec4 fine_rect;
// 1 / samples per axis
uniform vec2 coarse_texel;
uniform vec2 fine_texel;
uniform float coarse_step = 10.0;
uniform float fine_step = 2.5;
uniform float fine_feather = 60.0;

float th_sample(sampler2D t, vec4 r, vec2 texel, vec2 p, float mip) {
	vec2 uv = clamp((p - r.xy) / r.zw, vec2(0.0), vec2(1.0));
	uv = uv * (1.0 - texel) + 0.5 * texel;
	return textureLod(t, uv, mip).r;
}

// spacing: the distance between the points the caller samples, picks the mip that avoids aliasing
float terrain_height(vec2 p, float spacing) {
	float hc = th_sample(coarse_h, coarse_rect, coarse_texel, p, max(log2(spacing / coarse_step), 0.0));
	vec2 d = min(p - fine_rect.xy, fine_rect.xy + fine_rect.zw - p);
	float inner = min(d.x, d.y);
	if (inner <= 0.0) {
		return hc;
	}
	float hf = th_sample(fine_h, fine_rect, fine_texel, p, max(log2(spacing / fine_step), 0.0));
	return mix(hc, hf, smoothstep(0.0, fine_feather, inner));
}

vec3 terrain_normal(vec2 p, float spacing) {
	float hx0 = terrain_height(p - vec2(spacing, 0.0), spacing);
	float hx1 = terrain_height(p + vec2(spacing, 0.0), spacing);
	float hz0 = terrain_height(p - vec2(0.0, spacing), spacing);
	float hz1 = terrain_height(p + vec2(0.0, spacing), spacing);
	return normalize(vec3(hx0 - hx1, 2.0 * spacing, hz0 - hz1));
}
