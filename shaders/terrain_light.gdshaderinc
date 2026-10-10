// Baked terrain light lookup (tools/spike/bake_terrain_light.py): R sun visibility, G sky
// visibility, B concavity, A scree. Needs terrain_height.gdshaderinc first (rects and texels).
// Terrain data (c) Kartverket, CC BY 4.0.

uniform sampler2D coarse_light : filter_linear_mipmap, repeat_disable;
uniform sampler2D fine_light : filter_linear_mipmap, repeat_disable;

vec4 light_sample(vec2 p) {
	vec2 uvc = clamp((p - coarse_rect.xy) / coarse_rect.zw, vec2(0.0), vec2(1.0));
	uvc = uvc * (1.0 - coarse_texel) + 0.5 * coarse_texel;
	vec4 lc = textureLod(coarse_light, uvc, 0.0);
	vec2 d = min(p - fine_rect.xy, fine_rect.xy + fine_rect.zw - p);
	float inner = min(d.x, d.y);
	if (inner <= 0.0) {
		return lc;
	}
	vec2 uvf = (p - fine_rect.xy) / fine_rect.zw;
	uvf = uvf * (1.0 - fine_texel) + 0.5 * fine_texel;
	return mix(lc, textureLod(fine_light, uvf, 0.0), smoothstep(0.0, fine_feather, inner));
}
