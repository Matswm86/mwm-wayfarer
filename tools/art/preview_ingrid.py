"""Talk-distance check of an NPC (default Ingrid): waist-up front view at about 1.6 m, day light.
BLENDER_USER_RESOURCES=~/MWM/data/tools/blender_user blender -b --factory-startup -P tools/art/preview_ingrid.py -- out.png [kind]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wf_art as A  # noqa: E402
import wf_mh as M  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
out = argv[0]
kind = argv[1] if len(argv) > 1 else "ingrid"
pose = argv[2] if len(argv) > 2 else "talk_calm"
A.reset()
A.eevee(samples=48, res=(1200, 1000))
A.world_hdri("kloofendal_48d_partly_cloudy_puresky_4k.hdr", 25, 0.9)
A.sun(30, 152, color=(1.0, 0.8, 0.6), energy=4.0, angle=1.5)
M.character(kind, pose, loc=(0, 0, 0), yaw_deg=160)
A.camera((0.25, -1.7, 1.55), (0.0, 0, 1.35), lens=45)
A.render(out)
