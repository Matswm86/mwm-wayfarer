// Baked per-texel terrain detail (tools/spike/bake_terrain_detail.py): R, G = normal x, z;
// B = wetness (D8 flow accumulation); A = convexity. Needs terrain_height.gdshaderinc first.
// Terrain data (c) Kartverket, CC BY 4.0.

uniform sampler2D coarse_detail : filter_linear_mipmap, repeat_disable;
uniform sampler2D fine_detail : filter_linear_mipmap, repeat_disable;

vec4 detail_sample(vec2 p) {
	vec2 uvc = clamp((p - coarse_rect.xy) / coarse_rect.zw, vec2(0.0), vec2(1.0));
	uvc = uvc * (1.0 - coarse_texel) + 0.5 * coarse_texel;
	vec4 dc = texture(coarse_detail, uvc);
	vec2 d = min(p - fine_rect.xy, fine_rect.xy + fine_rect.zw - p);
	float inner = min(d.x, d.y);
	if (inner <= 0.0) {
		return dc;
	}
	vec2 uvf = (p - fine_rect.xy) / fine_rect.zw;
	uvf = uvf * (1.0 - fine_texel) + 0.5 * fine_texel;
	return mix(dc, texture(fine_detail, uvf), smoothstep(0.0, fine_feather, inner));
}

vec3 detail_normal(vec4 dt) {
	vec2 xz = dt.rg * 2.0 - 1.0;
	return normalize(vec3(xz.x, sqrt(max(1.0 - dot(xz, xz), 0.0)), xz.y));
}
