"""Check renders of Poly Haven models: blender -b --factory-startup -P tools/art/preview_protos.py -- out_dir name [name...]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import bpy
from mathutils import Vector
import wf_art as A

argv = sys.argv[sys.argv.index("--") + 1:]
out = Path(argv[0])
for name in argv[1:]:
    A.reset()
    A.eevee(samples=16, res=(640, 400))
    A.world_hdri("kloofendal_48d_partly_cloudy_puresky_4k.hdr", 0, 1.0)
    c = A.proto(name)
    e = A.inst(c, (0, 0, 0))
    lo, hi = A.bounds(c.objects)
    sz = hi - lo
    print("SIZE", name, [round(v, 2) for v in sz], "lo", [round(v, 2) for v in lo])
    ctr = (lo + hi) / 2
    r = max(sz) * 1.4
    A.camera(ctr + Vector((r * 0.6, -r, r * 0.45)), ctr, lens=35)
    A.render(out / f"proto_{name}.png")
