class_name SpikeConfig
extends RefCounted

## Every tunable number of the performance spike lives here.

const TERRAIN_DIR := "res://assets/terrain/"
## A tile splits into its four children when the camera is closer than this times its size.
const LOD_SPLIT := 1.0
const LOD_MARGIN := 0.1
## Tiles from this level down cast shadows (0 = 2560 m ... 4 = 160 m).
const SHADOW_LEVEL := 3
const SKIRT_DEPTH := 6.0

## Trees: pines within this radius of the camera, cones beyond (switch done per tree in the shader).
const TREE_NEAR_RADIUS := 320.0
const TREE_NEAR_CHUNK := 640.0
const TREE_FAR_CHUNK := 2560.0
const TREE_FAR_END := 7000.0

## Grass: one blade per GRASS_SPACING m grid point within GRASS_RADIUS of the player.
const GRASS_RADIUS := 40.0
const GRASS_SPACING := 0.6

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
const SUN_ENERGY := 2.0
## DESIGN.md 7.2 rule 7: a 30 deg morning sun is near white.
const SUN_COLOR := Color(1.0, 0.90, 0.78)

## Sky: Poly Haven kloofendal_48d_partly_cloudy (CC0) as an LDR panorama with the sun painted
## out (tools/spike/sky_to_ldr.py); energy restores the HDR level, rotation lines the cloud glow up
## with the sun azimuth.
const SKY_TEXTURE := "res://assets/sky/kloofendal_48d_partly_cloudy.jpg"
const SKY_ENERGY := 1.56
const SKY_ROTATION_DEG := 180.0
const EXPOSURE := 0.85
const AMBIENT_ENERGY := 1.5
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

const BENCH_SECONDS := 60.0
const BENCH_WARMUP := 1.0
## Boot warm-up: frames rendered per preset and view so every pipeline compiles before play.
const WARMUP_FRAMES := 3

## Graphics presets: render scale, sun shadows, forest density, grass density, water depth foam,
## MSAA sample count (0, 2, 4) and FXAA (screen-space, Mobile renderer supports both in 4.6),
## glow (bloom), sun shadow distance, PSSM splits and shadow atlas size.
const PRESETS: Array[Dictionary] = [
	{
		"name": "Low",
		"rock_detail": false,
		"scale": 0.7,
		"shadows": false,
		"forest": 0.35,
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
		"rock_detail": true,
		"scale": 0.85,
		"shadows": true,
		"forest": 0.65,
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
		"rock_detail": true,
		"scale": 1.0,
		"shadows": true,
		"forest": 1.0,
		"grass": 1.0,
		"foam": true,
		"msaa": 4,
		"fxaa": false,
		"glow": true,
		"shadow_distance": 160.0,
		"shadow_splits": 4,
		"shadow_atlas": 4096,
	},
]
const FOREST_STEPS: Array[float] = [0.35, 0.65, 1.0]
