// Fjord water WITHOUT depth foam (no depth-buffer read). Body and licence: fjord_water.gdshaderinc.
shader_type spatial;
render_mode unshaded, blend_mix, cull_back, shadows_disabled, specular_disabled, depth_draw_never;
#include "res://shaders/fjord_water.gdshaderinc"
