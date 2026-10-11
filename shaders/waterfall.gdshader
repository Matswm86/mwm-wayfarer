// Cascade ribbon (pass 3, scripts/Waterfall.gd). Mesh contract: UV.x across 0..1, UV.y metres
// along / 10 (0 at the top); COLOR.r steepness 0..1, COLOR.gb the side direction (x, z) packed
// to 0..1, COLOR.a the position across (-1..1).
// - Far widening: vertices move sideways so the strip is at least `min_px_angle` radians wide on
//   screen (reads from the village 1.3 km off; true size up close).
// - White water where steep: two layers of streaks stretched along the flow, scrolling at a speed
//   that grows with the steepness; on the flatter run-out clear dark water with moving glints.
// - Lit (sun and sky), so it sits in the scene instead of glowing like the old unshaded strip.
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform float speed = 1.8;
uniform float opacity = 0.92;
uniform float streak_scale = 7.0;
uniform float min_px_angle = 0.0035;
// far lift: from far away the gully sides hide water that lies in the gully floor
uniform float lift_per_m = 0.005;
uniform vec3 foam_color : source_color = vec3(0.82, 0.86, 0.87);
uniform vec3 water_color : source_color = vec3(0.05, 0.08, 0.08);

varying float steep;
varying float across;

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

void vertex() {
	steep = COLOR.r;
	across = COLOR.a;
	vec3 side = vec3(COLOR.g * 2.0 - 1.0, 0.0, COLOR.b * 2.0 - 1.0);
	vec3 world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float dist = length(world - CAMERA_POSITION_WORLD);
	// extra half-width so the strip never gets thinner than min_px_angle on screen
	float extra = max(dist * min_px_angle - 3.0, 0.0);
	VERTEX += (inverse(mat3(MODEL_MATRIX)) * side) * across * extra;
	VERTEX.y += max(dist * lift_per_m - 1.5, 0.0);
}

float fbm(vec2 p) {
	return vnoise(p) * 0.5 + vnoise(p * 2.03 + 1.7) * 0.3 + vnoise(p * 4.01 + 3.1) * 0.2;
}

void fragment() {
	float t = TIME * speed * (0.4 + steep * 1.4);
	// streaks: stretched along the flow (a few metres long), fine across, two layers at
	// different speeds, plus thin fast strands on steep runs
	vec2 q1 = vec2(UV.x * streak_scale, UV.y * 2.5 - t);
	vec2 q2 = vec2(UV.x * streak_scale * 2.7 + 0.37, UV.y * 4.3 - t * 1.45);
	float n1 = fbm(q1);
	float n2 = fbm(q2);
	float foam = n1 * 0.6 + n2 * 0.5;
	float white = smoothstep(0.52 - steep * 0.22, 0.7 - steep * 0.12, foam);
	float strands = vnoise(vec2(UV.x * streak_scale * 6.0, UV.y * 0.9 - t * 0.9));
	white = clamp(white * 0.85 + strands * strands * steep * 0.6, 0.0, 1.0);
	float edge = smoothstep(0.0, 0.2, UV.x) * smoothstep(1.0, 0.8, UV.x);
	// ragged sides: the foam frays out
	edge *= smoothstep(0.2, 0.55, vnoise(vec2(UV.x * 24.0, UV.y * 3.0 - t * 0.5)) + edge * 0.55);
	ALBEDO = mix(water_color, foam_color * mix(0.75, 1.05, n2), white);
	ROUGHNESS = mix(0.06, 0.55, white);
	SPECULAR = 0.5;
	// clear water lets the wet rock show; foam is near opaque; gaps between the streaks
	ALPHA = clamp(edge * mix(0.2 + steep * 0.2, 0.95, white) * opacity, 0.0, 1.0);
	EMISSION = foam_color * white * 0.06;
}
