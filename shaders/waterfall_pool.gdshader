// Plunge pool at the foot of the cascade (scripts/Waterfall.gd): dark clear water, glossy, with a
// churning foam ring where the falls land on one side and calmer edges.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

uniform float radius = 7.0;
uniform vec3 deep : source_color = vec3(0.02, 0.04, 0.045);
uniform vec3 foam_color : source_color = vec3(0.9, 0.93, 0.94);

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

varying vec3 lpos;

void vertex() {
	lpos = VERTEX;
}

void fragment() {
	float r = length(lpos.xz) / radius;
	float ang = atan(lpos.z, lpos.x);
	float n = vnoise(vec2(ang * 3.0, r * 6.0 - TIME * 0.6)) * 0.6 + vnoise(lpos.xz * 1.3 + TIME * 0.3) * 0.4;
	float foam = smoothstep(0.55, 0.85, n) * smoothstep(0.85, 0.2, r);
	ALBEDO = mix(deep, foam_color, foam);
	ROUGHNESS = mix(0.05, 0.5, foam);
	SPECULAR = 0.6;
	// soft shore: fades into the wet stones at the rim
	ALPHA = smoothstep(1.0, 0.82, r) * mix(0.85, 1.0, foam);
	vec2 w = vec2(vnoise(lpos.xz * 2.0 + TIME), vnoise(lpos.xz * 2.0 - TIME + 3.1)) - 0.5;
	NORMAL = normalize((VIEW_MATRIX * vec4(w.x * 0.3, 1.0, w.y * 0.3, 0.0)).xyz);
}
