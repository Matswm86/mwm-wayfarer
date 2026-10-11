// Beauty corner ground (pass 3): the terrain shader on real meshes round the village, spawn and
// cliff foot (tools/spike/build_corner.gd), lightmapped by LightmapGI, with the worn path, gravel
// yards, pebble shore and wet sand of the corner mask. Same look as terrain.gdshader elsewhere.

shader_type spatial;
render_mode world_vertex_coords, cull_back;

#define CORNER
#include "res://shaders/terrain_body.gdshaderinc"
