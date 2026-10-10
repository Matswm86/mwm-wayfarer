// Fjord water WITH depth-texture shore foam (reads the depth buffer: costs a depth copy per frame).
// Body and licence: fjord_water.gdshaderinc.
shader_type spatial;
render_mode unshaded, blend_mix, cull_back, shadows_disabled, specular_disabled, depth_draw_never;
#define WATER_DEPTH_FOAM
#include "res://shaders/fjord_water.gdshaderinc"
