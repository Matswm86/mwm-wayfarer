"""Character check: explorer (back 3/4) and an NPC (front) at game distances.
BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user blender -b --factory-startup -P tools/art/preview_mh.py -- out.png npc_kind"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import bpy
import wf_art as A
import wf_mh as M

argv = sys.argv[sys.argv.index("--") + 1:]
out, npc = argv[0], argv[1]
A.reset()
A.eevee(samples=48, res=(1600, 1000))
A.world_hdri("evening_road_01_puresky_4k.hdr", 0, 1.0)
A.sun(25, 200, energy=3.0)
M.character("explorer", "stand_look", loc=(-0.5, 0, 0), yaw_deg=150)
M.character(npc, "talk", loc=(0.8, 0.6, 0), yaw_deg=200)
bpy.ops.mesh.primitive_plane_add(size=20)
A.camera((0.3, 3.6, 1.55), (0.15, 0, 1.2), lens=40)
A.render(out)
