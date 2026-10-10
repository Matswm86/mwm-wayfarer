"""Check sheet for the characters: front and back three-quarter views. blender -b --factory-startup -P tools/art/preview_chars.py -- out.png kind pose"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import bpy
import wf_art as A
import wf_char as C

argv = sys.argv[sys.argv.index("--") + 1:]
out, kind, pose = argv[0], argv[1], argv[2]
A.reset()
A.eevee(samples=32, res=(1600, 1000))
A.world_hdri("evening_road_01_puresky_4k.hdr", 0, 1.0)
A.sun(30, 150, energy=3.5)
rig1, o1 = C.character(kind, pose, loc=(-0.6, 0, 0), yaw_deg=200)
rig2, o2 = C.character(kind, pose, loc=(0.6, 0, 0), yaw_deg=-30)
bpy.ops.mesh.primitive_plane_add(size=20)
A.camera((0, 4.2, 1.25), (0, 0, 1.0), lens=50)
A.render(out)
