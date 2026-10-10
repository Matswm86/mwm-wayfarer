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
const SHADOW_DISTANCE := 70.0

const BENCH_SECONDS := 60.0
const BENCH_WARMUP := 1.0

## Graphics presets: render scale, sun shadows, forest density, grass density, water depth foam.
const PRESETS: Array[Dictionary] = [
	{"name": "Low", "scale": 0.7, "shadows": false, "forest": 0.35, "grass": 0.0, "foam": false},
	{"name": "Medium", "scale": 0.85, "shadows": true, "forest": 0.65, "grass": 0.5, "foam": false},
	{"name": "High", "scale": 1.0, "shadows": true, "forest": 1.0, "grass": 1.0, "foam": true},
]
const FOREST_STEPS: Array[float] = [0.35, 0.65, 1.0]
