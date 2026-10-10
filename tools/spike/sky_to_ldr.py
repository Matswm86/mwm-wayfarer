"""Poly Haven HDRI (CC0) -> LDR panorama for the Godot sky, plus the sun direction it contains.

Run: blender -b --factory-startup -P tools/spike/sky_to_ldr.py -- <in.hdr> <out.jpg> [width]
Scales the HDR so the 98th percentile of the sky (sun excluded) maps to 1.0, writes an sRGB
JPEG and prints the scale (use as PanoramaSkyMaterial energy) and the sun azimuth/elevation.
"""

import math
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1 :]
src, dst = args[0], args[1]
width = int(args[2]) if len(args) > 2 else 4096

img = bpy.data.images.load(src)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]  # row 0 = top
lum = px @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
az = (ix + 0.5) / w * 360.0
el = 90.0 - (iy + 0.5) / h * 180.0
print(
    f"SUN pixel ({ix},{iy}) lum {lum[iy, ix]:.1f} -> u {ix / w:.4f} azimuth_u {az:.1f} deg elevation {el:.1f} deg"
)
upper = lum[: h // 2]
p995 = float(np.percentile(upper[upper < lum[iy, ix] * 0.05], 98.0))
scale = 1.0 / p995
print(f"SCALE {scale:.4f} (sky energy {p995:.4f})")

# paint the sun out (the game has its own DirectionalLight at a lower elevation): inside 7 deg
# the sky takes the 20th-percentile colour of the 7-8 deg ring (blue sky, not cloud) (the edge of the glow), feathered to 9 deg
yy, xx = np.mgrid[0:h, 0:w]
dx = np.minimum(np.abs(xx - ix), w - np.abs(xx - ix)) * 360.0 / w * math.cos(math.radians(el))
dy = (yy - iy) * 180.0 / h
dist = np.hypot(dx, dy)
edge = np.percentile(px[(dist > 7.0) & (dist < 8.0)], 20.0, axis=0)
t = np.clip((9.0 - dist) / 2.0, 0.0, 1.0)
t = (t * t * (3.0 - 2.0 * t))[..., None]
px = px * (1.0 - t) + edge * t
print("SUN painted out:", int((dist <= 9.0).sum()), "pixels, edge colour", edge)

# downsample by box filter to width x width/2
f = w // width
small = px[: (h // f) * f, : (w // f) * f].reshape(h // f, f, w // f, f, 3).mean(axis=(1, 3))
small = np.clip(small * scale, 0.0, 1.0)
srgb = np.where(small <= 0.0031308, small * 12.92, 1.055 * np.power(small, 1 / 2.4) - 0.055)
out = bpy.data.images.new("out", small.shape[1], small.shape[0], alpha=False)
rgba = np.concatenate([srgb[::-1], np.ones(srgb.shape[:2] + (1,), np.float32)], axis=2)
out.pixels = rgba.ravel().tolist()
out.filepath_raw = dst
out.file_format = "JPEG"
bpy.context.scene.render.image_settings.quality = 90
out.save(filepath=dst, quality=90)
print("WROTE", dst, small.shape)
