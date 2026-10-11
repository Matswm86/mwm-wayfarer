// Fjord terrain: flat grid tiles displaced in the vertex shader from the baked height textures.
// Mesh contract (scripts/Terrain.gd): unit grid -0.5..0.5 in x/z, UV2.x = cells per edge,
// UV2.y = 1 on skirt vertices (dropped down to hide cracks between LOD levels).
// Node scale (tile, 1, tile), node y = 0.
//
// Visual pass 2 (2026-10-10):
// - heights are float32 now (float16 stepped 0.5-1 m above 512 m and drew contour "wood grain");
// - lighting uses the baked per-texel DEM normal (bake_terrain_detail.py), so far tiles with
//   40-80 m vertex spacing still show every rib and chute of the 10 m data;
// - rock = true triplanar, three projections blended by the scan heights (no stretch on any
//   facing), at two scales (64 m bands + 12 m cracks) plus a 3 m grain near the camera on Ultra,
//   with the cliff scan normal at each scale. Gneiss colour comes from a palette; the scans give
//   foliation, cracks and cavities;
// - streaks follow the DEM's real drainage (flow accumulation): water-stained, darker, glossy
//   seams down the walls; moss in hollows and wet less-steep spots; paler dry ridges;
// - ground = meadow grass low, alpine turf high with heather patches, rock outcrops on convex
//   knolls, scree aprons, all blended by the scan heights; two scales against tiling;
// - wet band 0-3 m above the water; snow by height, slope and aspect (shaded faces hold more);
// - baked sun and sky visibility (bake_terrain_light.py) as before.
// quality: 0 = Low (one rock scale, no scan normals), 1 = Medium/High, 2 = Ultra (+ 3 m grain).
// Textures: Poly Haven (CC0) cliff_side, rock_face_03, leafy_grass, sparse_grass,
// forest_ground_04, rock_ground_02. Heights and baked maps from Kartverket DTM, CC BY 4.0.

shader_type spatial;
render_mode world_vertex_coords, cull_back;

#include "res://shaders/terrain_body.gdshaderinc"
