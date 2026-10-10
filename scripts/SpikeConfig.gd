class_name SpikeConfig
extends RefCounted

## Every tunable number of the performance spike lives here.

const TERRAIN_DIR := "res://assets/terrain/"
## A tile splits into its four children when the camera is closer than this times its size.
const LOD_SPLIT := 1.0
const LOD_MARGIN := 0.1
## Tiles from this level down cast real-time shadows (0 = 2560 m ... 4 = 160 m; 5 = none).
## None since the graphics pass: the terrain's shadow on itself is baked (bake_terrain_light.py),
## which saves the terrain triangles in every shadow split.
const SHADOW_LEVEL := 5
const SKIRT_DEPTH := 6.0

## Trees: pines within this radius of the camera, cones beyond (switch done per tree in the shader).
const TREE_NEAR_RADIUS := 320.0
const TREE_NEAR_CHUNK := 640.0
const TREE_FAR_CHUNK := 2560.0
const TREE_FAR_END := 7000.0

## Ground cover: one plant (two crossed cards) per GRASS_SPACING m grid point within
## GRASS_RADIUS of the player.
const GRASS_RADIUS := 35.0
const GRASS_SPACING := 0.5

const PLAYER_WALK := 4.5
const PLAYER_RUN := 8.0
const GRAVITY := 18.0
const CAM_DISTANCE := 4.2
const CAM_HEIGHT := 1.7
const ORBIT_SPEED := 0.006
## Collision heightmap around the spawn, metres per side (2.5 m data).
const COLLISION_SIZE := 1200.0

const SUN_ELEVATION_DEG := 30.0
const SUN_AZIMUTH_DEG := 215.0
const SUN_ENERGY := 2.5
## DESIGN.md 7.2 rule 7: a 30 deg morning sun is near white.
const SUN_COLOR := Color(1.0, 0.90, 0.78)

## Sky: Poly Haven kloofendal_48d_partly_cloudy (CC0) as an LDR panorama with the sun painted
## out (tools/spike/sky_to_ldr.py); energy restores the HDR level, rotation lines the cloud glow up
## with the sun azimuth.
const SKY_TEXTURE := "res://assets/sky/kloofendal_48d_partly_cloudy.jpg"
const SKY_ENERGY := 1.56
const SKY_ROTATION_DEG := 180.0
const EXPOSURE := 0.9
const AMBIENT_ENERGY := 1.0
## Aerial perspective (DESIGN.md 7.2 rules 3 and 8): depth fog from 200 m, at most 0.22,
## quadratic falloff, blue-grey, never milky.
const FOG_COLOR := Color(0.62, 0.74, 0.90)
const FOG_MAX := 0.22
const FOG_BEGIN := 200.0
const FOG_END := 7000.0
const FOG_CURVE := 2.0
const FOG_AERIAL := 0.5
const FOG_SUN_SCATTER := 0.08

## Reflection probes over the fjord water: centre x, centre z, size x, size z (metres).
const WATER_PROBES: Array[Vector4] = [
	Vector4(150.0, -1300.0, 3600.0, 4200.0),
	Vector4(0.0, -5400.0, 4200.0, 5200.0),
]
const WATER_PROBE_HEIGHT := 40.0

## Box reflection probe over the village street: centre x, centre z, size x, size z (metres).
const VILLAGE_PROBE := Vector4(270.0, -195.0, 200.0, 220.0)
const VILLAGE_PROBE_HEIGHT := 12.0
## Contact shadows (scripts/Lighting.gd): soft dark decals under animals and characters and round
## house footprints, the ambient occlusion the Mobile renderer cannot compute.
const CONTACT_FADE_BEGIN := 45.0
## Render layer of animals and characters (bit 2), so ground decals skip them.
const ACTOR_LAYER := 2
const CONTACT_STRENGTH := 0.55
const HOUSE_AO_STRENGTH := 0.5

## Waterfall: ribbon half-width at the top and the foot (m), height above the gully floor (m),
## mist puff size (m). Wide and bright enough to read from the village about 1.1 km away.
const FALLS_WIDTH := Vector2(15.0, 28.0)
const FALLS_LIFT := 7.0
const FALLS_MIST_SIZE := 55.0

const BENCH_SECONDS := 60.0
const BENCH_WARMUP := 1.0
## Boot warm-up: frames rendered per preset and view so every pipeline compiles before play.
const WARMUP_FRAMES := 3

## Graphics presets: render scale, sun shadows, forest density, grass density, water depth foam,
## MSAA sample count (0, 2, 4) and FXAA (screen-space, Mobile renderer supports both in 4.6),
## glow (bloom), sun shadow distance, PSSM splits and shadow atlas size.
## terrain_quality: 0 one rock scale, no scan normals; 1 two scales + normals; 2 + 3 m grain.
## shadow_blur: sun shadow softening radius (Ultra, with the softer filter, kills stair-steps).
## fps_cap: Engine.max_fps (0 = display rate). shadow_quality: soft shadow filter
## (RenderingServer.ShadowQuality, 1 = very low ... 5 = ultra). Ultra (visual pass 2) spends the
## 60 fps budget (16.7 ms) of the owner's phone; Low/Medium/High keep the pass 1 costs.
const PRESETS: Array[Dictionary] = [
	{
		"name": "Low",
		"shadow_blur": 1.0,
		"terrain_quality": 0,
		"fps_cap": 0,
		"shadow_quality": 1,
		"scale": 0.7,
		"shadows": false,
		"forest": 0.2,
		"grass": 0.0,
		"foam": false,
		"msaa": 0,
		"fxaa": false,
		"glow": false,
		"shadow_distance": 0.0,
		"shadow_splits": 2,
		"shadow_atlas": 2048,
	},
	{
		"name": "Medium",
		"shadow_blur": 1.0,
		"terrain_quality": 1,
		"fps_cap": 0,
		"shadow_quality": 1,
		"scale": 0.85,
		"shadows": true,
		"forest": 0.4,
		"grass": 0.5,
		"foam": false,
		"msaa": 2,
		"fxaa": false,
		"glow": true,
		"shadow_distance": 120.0,
		"shadow_splits": 2,
		"shadow_atlas": 2048,
	},
	{
		"name": "High",
		"shadow_blur": 1.0,
		"terrain_quality": 1,
		"fps_cap": 0,
		"shadow_quality": 1,
		"scale": 1.0,
		"shadows": true,
		"forest": 0.6,
		"grass": 1.0,
		"foam": true,
		"msaa": 4,
		"fxaa": false,
		"glow": true,
		"shadow_distance": 160.0,
		"shadow_splits": 4,
		"shadow_atlas": 4096,
	},
	{
		"name": "Ultra",
		"shadow_blur": 1.6,
		"terrain_quality": 2,
		"fps_cap": 60,
		"shadow_quality": 3,
		"scale": 1.0,
		"shadows": true,
		"forest": 1.0,
		"grass": 1.0,
		"foam": true,
		"msaa": 4,
		"fxaa": false,
		"glow": true,
		"shadow_distance": 240.0,
		"shadow_splits": 4,
		"shadow_atlas": 4096,
	},
]
## Share of the 90 000 placed trees per preset (High keeps the pass 1 count of about 54 000).
const FOREST_STEPS: Array[float] = [0.2, 0.4, 0.6, 1.0]

## Wildlife (scripts/Wildlife.gd). area = centre x, z; radius in m; size = longest side of the
## model in m; walk speed m/s; flee = distance at which it runs from the player (0 = ignores);
## range = visibility range in m; low = how many of `count` the Low preset keeps; fly = altitude.
const WILDLIFE: Array[Dictionary] = [
	{
		"species": "doe",
		"count": 3,
		"low": 2,
		"area": [165.0, 30.0],
		"radius": 40.0,
		"size": 1.7,
		"walk": 1.2,
		"flee": 30.0,
		"range": 300.0,
	},
	{
		"species": "deer",
		"count": 2,
		"low": 1,
		"area": [180.0, 10.0],
		"radius": 40.0,
		"size": 1.9,
		"walk": 1.3,
		"flee": 30.0,
		"range": 300.0,
	},
	{
		"species": "elk",
		"count": 1,
		"low": 0,
		"area": [255.0, 60.0],
		"radius": 35.0,
		"size": 2.5,
		"walk": 1.4,
		"flee": 35.0,
		"range": 400.0,
	},
	{
		"species": "moose",
		"count": 1,
		"low": 0,
		"area": [270.0, -10.0],
		"radius": 35.0,
		"size": 3.0,
		"walk": 1.3,
		"flee": 25.0,
		"range": 400.0,
	},
	{
		"species": "fox",
		"count": 1,
		"low": 0,
		"area": [205.0, -60.0],
		"radius": 30.0,
		"size": 1.1,
		"walk": 1.1,
		"flee": 18.0,
		"range": 150.0,
	},
	{
		"species": "rabbit",
		"count": 3,
		"low": 0,
		"area": [150.0, -40.0],
		"radius": 25.0,
		"size": 0.45,
		"walk": 0.6,
		"flee": 10.0,
		"range": 80.0,
	},
	{
		"species": "wolf",
		"count": 2,
		"low": 0,
		"area": [-290.0, -440.0],
		"radius": 30.0,
		"size": 1.6,
		"walk": 1.4,
		"flee": 0.0,
		"range": 600.0,
	},
	{
		"species": "bear",
		"count": 1,
		"low": 0,
		"area": [-300.0, 250.0],
		"radius": 30.0,
		"size": 2.0,
		"walk": 1.0,
		"flee": 0.0,
		"range": 600.0,
	},
	{
		"species": "eagle",
		"count": 1,
		"low": 1,
		"area": [400.0, -200.0],
		"radius": 250.0,
		"size": 2.1,
		"speed": 14.0,
		"fly": 450.0,
		"flee": 0.0,
		"range": 2500.0,
	},
	{
		"species": "gull",
		"count": 5,
		"low": 2,
		"area": [20.0, -60.0],
		"radius": 90.0,
		"size": 2.2,
		"speed": 9.0,
		"fly": 30.0,
		"flee": 0.0,
		"range": 600.0,
	},
]
