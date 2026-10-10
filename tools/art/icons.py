"""Item icons for the trade mock: each Poly Haven model rendered on transparent, 256 px.
blender -b --factory-startup -P tools/art/icons.py -- <out_dir> name [name...]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import wf_art as A  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
out = Path(argv[0])
out.mkdir(parents=True, exist_ok=True)
for name in argv[1:]:
    A.reset()
    A.eevee(samples=24, res=(256, 256), exposure=0.2, look="AgX - Base Contrast")
    A.world_hdri("kloofendal_48d_partly_cloudy_puresky_4k.hdr", 30, 1.0)
    bpy.context.scene.render.film_transparent = True
    c = A.proto(name)
    A.inst(c, (0, 0, 0))
    lo, hi = A.bounds(c.objects)
    ctr = (lo + hi) / 2
    r = max(hi - lo) * 1.9
    cam = A.camera(ctr + Vector((r * 0.55, -r, r * 0.55)), ctr, lens=50)
    cam.data.sensor_fit = "AUTO"
    A.render(out / f"{name}.png")
