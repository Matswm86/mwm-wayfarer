// Waterfall ribbon: white water streaks scrolling down the strip, soft edges, foamier at the foot.
// Mesh contract (scripts/Main.gd): UV.x across the strip 0..1, UV.y along it, 0 at the top,
// in metres / 10.
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform float speed = 1.6;
uniform vec4 water_color : source_color = vec4(0.97, 0.99, 1.0, 1.0);
uniform vec4 shade_color : source_color = vec4(0.55, 0.66, 0.68, 1.0);
uniform float opacity = 0.95;
// above 1 so the white water stays bright after the AgX tonemap, as sunlit foam does
uniform float brightness = 1.35;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), f.x),
		mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), f.x), f.y);
}

void fragment() {
	vec2 p = vec2(UV.x * 9.0, UV.y * 3.0 - TIME * speed);
	float streak = vnoise(p) * 0.65 + vnoise(p * vec2(2.0, 3.0)) * 0.35;
	float edge = smoothstep(0.0, 0.25, UV.x) * smoothstep(1.0, 0.75, UV.x);
	float a = edge * smoothstep(0.25, 0.6, streak + 0.15);
	ALBEDO = mix(shade_color.rgb, water_color.rgb, smoothstep(0.35, 0.8, streak)) * brightness;
	ALPHA = clamp(a * opacity, 0.0, 1.0);
}
