"""Face/upper-body check for an NPC. blender -b --factory-startup -P tools/art/preview_face.py -- out.png kind pose"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import wf_art as A
import wf_char as C

argv = sys.argv[sys.argv.index("--") + 1:]
out, kind, pose = argv[0], argv[1], argv[2]
A.reset()
A.eevee(samples=48, res=(1200, 1200))
A.world_hdri("evening_road_01_puresky_4k.hdr", 0, 1.0)
A.sun(25, 200, energy=3.0)
rig, objs = C.character(kind, pose, loc=(0, 0, 0), yaw_deg=180)
A.camera((0.25, -1.6, 1.5), (0, 0, 1.38), lens=60)
A.render(out)
