class_name SpikeConfig
extends RefCounted

## Every tunable number of the performance spike lives here.

const TERRAIN_DIR := "res://assets/terrain/"
## Beauty corner (pass 3): spawn, village, shore and cliff foot as lightmapped real meshes with
## scanned houses, props, rocks and birches (tools/spike/build_corner.gd, bake_corner.sh).
## CORNER_TILES = the finest terrain tiles (160 m) it replaces, same rect as the builder.
const CORNER_SCENE := "res://scenes/BeautyCorner.tscn"
const CORNER_TILES := Rect2i(38, 55, 4, 4)
const CORNER_MASK := "res://assets/terrain/corner/corner_mask.png"
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
## Ultra: conifers within tree_geo m of the camera are meshes (scripts/NearTrees.gd), full detail
## within TREE_LOD0_RADIUS, the light LOD beyond.
const TREE_LOD0_RADIUS := 22.0
## Cliff rocks (scripts/CliffRocks.gd): LOD0 / LOD1 / LOD2 distance limits (m), albedo tint.
## Off on every preset for now: the Poly Haven stand-ins read as dark planks on the gneiss;
## turn on ("rocks") when the designer's cliff set replaces them.
const ROCK_LOD_RANGES := Vector3(90.0, 320.0, 900.0)
const ROCK_TINT := Color(0.62, 0.66, 0.72)
## One model per forest variant (0-1 pines, 2-3 firs in trees.json): designer's Scots pine a/b and
## Norway spruce a/b (pass 3).
const TREE_MESHES: Array[String] = [
	"res://assets/models/corner/trees/scots_pine_a.glb",
	"res://assets/models/corner/trees/scots_pine_b.glb",
	"res://assets/models/corner/trees/norway_spruce_a.glb",
	"res://assets/models/corner/trees/norway_spruce_b.glb",
]

## Ground cover: one plant (two crossed cards) per GRASS_SPACING m grid point within
## GRASS_RADIUS of the player.
const GRASS_RADIUS := 35.0
const GRASS_SPACING := 0.5
## Ultra: a second ring of bigger, sparser clumps from about 30 m out to GRASS_FAR_RADIUS.
const GRASS_FAR_RADIUS := 95.0
const GRASS_FAR_SPACING := 1.9
const GRASS_FAR_SCALE := 1.7

## Skin shading (Humans.skin): material names that are skin, light through skin.
const SKIN_MATERIALS: Array[String] = ["body", "skin", "head", "face"]
const SKIN_BACKLIGHT := Color(0.32, 0.1, 0.06)
## Player model (pass 3): Luca, a scanned man (designer's player_luca; scan Renderpeople CC BY 4.0,
## Quaternius clips CC0); faces +Z like every glTF rig (Player turns it to the body's -Z).
## Ingrid: designer's ingrid_farmer (CC BY 4.0).
const PLAYER_MODEL := "res://assets/models/characters/player_luca.glb"
const INGRID_MODEL := "res://assets/models/characters/ingrid_farmer.glb"
## Locomotion blend for the scanned rigs: [clip, ground speed m/s, playback rate]. The clips are
## authored at about 1.4 (walk), 3.5 (run) and 6 m/s (sprint); the game's walk speed jogs and its
## run sprints, with rates that keep the feet near the ground speed.
const PLAYER_GAITS: Array = [
	["idle", 0.0, 1.0],
	["walk", 1.4, 1.0],
	["run", 4.5, 1.25],
	["sprint", 8.0, 1.3],
]
const PLAYER_WALK := 4.5
const PLAYER_RUN := 8.0
## Walk clip playback rate at walking speed (feet match the ground).
const ANIM_WALK_RATE := 1.3
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
const GRADE_LUT := "res://assets/luts/grade.png"
const AMBIENT_ENERGY := 1.0
## Aerial perspective (DESIGN.md 7.2 rules 3 and 8): depth fog from 200 m, curve 1.7 to 0.36 at
## 9 km (about 0.03 at 2 km, 0.12 at 4 km), blue-grey, never milky: far ridges layer.
const FOG_COLOR := Color(0.62, 0.74, 0.90)
const FOG_MAX := 0.36
const FOG_BEGIN := 200.0
const FOG_END := 9000.0
const FOG_CURVE := 1.7
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

## Waterfall (pass 3, scripts/Waterfall.gd): path resample step (m); half-widths (top, foot) of the
## white-water core and the veil (true size; the shader widens them only with distance); spray
## and mist sheet sizes; plunge pool radius; wet rock decal width and darkness.
const FALLS_STEP := 3.0
const FALLS_CORE := Vector2(2.0, 3.2)
const FALLS_VEIL := Vector2(3.2, 4.6)
const FALLS_SPRAY_SIZE := 4.0
const FALLS_MIST_SIZE := 18.0
const FALLS_POOL_RADIUS := 7.0
const FALLS_WET_WIDTH := 22.0
const FALLS_WET_STRENGTH := 0.55

const BENCH_SECONDS := 60.0
const BENCH_WARMUP := 1.0
## "Bench corner" (Bench.run_corner): seconds per preset, seconds standing at the spawn looking
## round, then the worn village path the player runs (x, z; tools/spike/build_corner.gd PATH).
const CORNER_BENCH_SECONDS := 45.0
const CORNER_LOOK := 8.0
const CORNER_WALK: Array[Vector2] = [
	Vector2(150, -52),
	Vector2(178, -82),
	Vector2(200, -108),
	Vector2(219, -132),
	Vector2(233, -158),
	Vector2(250, -178),
	Vector2(268, -192),
	Vector2(287, -212),
	Vector2(296, -232),
	Vector2(318, -256),
	Vector2(338, -282),
	Vector2(352, -310),
]
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
## Perf pass 3 (phone Ultra GPU p95 27.2 ms, High frame p95 19.4 ms): High capped at 60 fps
## (uncapped it paced 8.3 / 16.7 / 25 ms frames on the 120 Hz display); Ultra render scale 0.9,
## soft shadow filter one step lower (blur 1.3), far clumps to 95 m at 1.9 m spacing (about a
## third of the cards). Laptop GPU parts (tests/profile.gd) ranked these the cheapest cuts
## in look per ms.
const PRESETS: Array[Dictionary] = [
	{
		"name": "Low",
		"corner_lods": {
			"Houses": [-1.0, 40.0, 0.0],
			"Props": [-1.0, 50.0],
			"Rocks": [-1.0, 25.0, 140.0],
			"Trees": [-1.0, -1.0, 110.0],
		},
		"rocks": false,
		"tree_geo": 0.0,
		"grass_far": false,
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
		"corner_lods": {
			"Houses": [25.0, 70.0, 0.0],
			"Props": [18.0, 90.0],
			"Rocks": [18.0, 70.0, 300.0],
			"Trees": [12.0, 24.0, 130.0],
		},
		"rocks": false,
		"tree_geo": 0.0,
		"grass_far": false,
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
		"corner_lods": {
			"Houses": [35.0, 110.0, 0.0],
			"Props": [28.0, 130.0],
			"Rocks": [30.0, 120.0, 600.0],
			"Trees": [22.0, 45.0, 150.0],
		},
		"rocks": false,
		"tree_geo": 0.0,
		"grass_far": false,
		"shadow_blur": 1.0,
		"terrain_quality": 1,
		"fps_cap": 60,
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
		"corner_lods": {
			"Houses": [45.0, 150.0, 0.0],
			"Props": [35.0, 160.0],
			"Rocks": [40.0, 150.0, 900.0],
			"Trees": [30.0, 60.0, 150.0],
		},
		"rocks": false,
		"tree_geo": 70.0,
		"grass_far": true,
		"shadow_blur": 1.3,
		"terrain_quality": 2,
		"fps_cap": 60,
		"shadow_quality": 2,
		"scale": 0.9,
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
## corner_lods (corner pass 2026-10-11): visibility end (m) of each LOD of the beauty corner's
## scanned houses, props, rocks and birches (children named LOD*, in order; Main._apply_corner).
## Each LOD begins where the previous visible one ends; 0 = no end; -1 = that LOD is off. Ultra =
## the ranges baked by tools/spike/build_corner.gd (plus the house LOD2 from 150 m). Low and
## Medium start on the light LODs (the lightmapped LOD0 only on Medium, close up) so the corner
## fits their prim and draw budgets:
## Low has no birch meshes (cards only), no full-detail houses, rocks or props.
## The Evju storehouses get a third LOD at run time (3000 triangles, tools/spike/house_lod2.gd),
## also their shadow proxy; the log cabins keep two (a model's last LOD takes the last range).
## Corner rocks cast their sun shadow from the lightest LOD out to this range (m).
const CORNER_HOUSE_LOD2 := "res://assets/models/corner/baked/%s_LOD2.res"
const CORNER_ROCK_SHADOW_RANGE := 150.0
## Share of the 90 000 placed trees per preset (High keeps the pass 1 count of about 54 000).
const FOREST_STEPS: Array[float] = [0.2, 0.4, 0.6, 1.0]

## Animal fur (all species): rough, low specular (glossy fur mirrored the blue sky), soft rim.
const FUR_ROUGHNESS := 0.92
const FUR_SPECULAR := 0.22
const FUR_RIM := 0.35
## Wildlife (scripts/Wildlife.gd). Does and deer graze 45-70 m ahead of the spawn view.
## area = centre x, z; radius in m; size = longest side of the model in m; walk speed m/s;
## flee = distance at which it runs from the player (0 = ignores);
## range = visibility range in m; low = how many of `count` the Low preset keeps; fly = altitude.
const WILDLIFE: Array[Dictionary] = [
	{
		"species": "doe",
		"count": 3,
		"low": 2,
		"area": [175.0, -60.0],
		"radius": 15.0,
		"size": 1.7,
		"walk": 1.2,
		"flee": 30.0,
		"range": 300.0,
	},
	{
		"species": "deer",
		"count": 2,
		"low": 1,
		"area": [192.0, -35.0],
		"radius": 15.0,
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
