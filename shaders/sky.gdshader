// Sky (visual pass 2): the Poly Haven kloofendal_48d_partly_cloudy panorama (CC0, sun painted
// out by tools/spike/sky_to_ldr.py) plus a real sun disc and a forward-scatter halo at the
// directional light, so the sky, the sun and the clouds' bright side agree.

shader_type sky;

uniform sampler2D panorama : source_color, filter_linear_mipmap;
uniform float energy = 1.56;
// angular radius of the disc (deg) and its brightness over the sky
uniform float sun_size_deg = 0.55;
uniform float sun_gain = 40.0;
uniform float halo_gain = 0.35;

void sky() {
	vec3 c = texture(panorama, SKY_COORDS).rgb * energy;
	if (LIGHT0_ENABLED && !AT_CUBEMAP_PASS) {
		float cd = dot(EYEDIR, LIGHT0_DIRECTION);
		float r = radians(sun_size_deg);
		float disc = smoothstep(cos(r * 1.15), cos(r * 0.85), cd);
		c += LIGHT0_COLOR * LIGHT0_ENERGY * disc * sun_gain;
	}
	if (LIGHT0_ENABLED) {
		float cd = dot(EYEDIR, LIGHT0_DIRECTION);
		// Mie-like forward scatter round the sun, brightest near it, warm white
		float halo = pow(max(cd, 0.0), 12.0) * 0.6 + pow(max(cd, 0.0), 200.0);
		c += LIGHT0_COLOR * halo * halo_gain;
	}
	COLOR = c;
}
