"""Bake sun shadow, sky occlusion and ground masks for the fjord terrain (graphics pass 2026-10-10).

The Mobile renderer has no SSAO and no GI, and the sun's real-time shadows reach only 160 m.
The sun is fixed in the spike, so the light the valley walls block can be baked from the
elevation data once: the shader multiplies the sun by channel R and the sky light by channel G.

Output (RGBA8 PNG, one texel per height sample, same rect as the height files):
  assets/terrain/coarse_light.png  over coarse_h.bin (10 m)
  assets/terrain/fine_light.png    over fine_h.bin (2.5 m, village area)
  R = sun visibility (soft horizon test toward the sun, all occluders up to 9 km)
  G = sky visibility (cosine-weighted horizon in 12 directions out to 1.2 km)
  B = concavity (gullies, chutes, hollows: moss and darker rock)
  A = scree (moderate slope within 60 m below a cliff face)

Run: python3 tools/spike/bake_terrain_light.py [--masks-only]   (numpy, scipy, Pillow; about 6 min,
--masks-only keeps R and G from the existing files and redoes B and A in seconds)
Terrain data (c) Kartverket, CC BY 4.0.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
TER = ROOT / "assets" / "terrain"
CFG = ROOT / "scripts" / "SpikeConfig.gd"


def config_value(name: str) -> float:
    for line in CFG.read_text().splitlines():
        if line.startswith(f"const {name} :="):
            return float(line.split(":=")[1].strip())
    raise KeyError(name)


SUN_EL = math.radians(config_value("SUN_ELEVATION_DEG"))
SUN_AZ = math.radians(config_value("SUN_AZIMUTH_DEG"))
# direction toward the sun in the Godot frame (same formula as scripts/Main.gd)
TO_SUN = np.array(
    [math.sin(SUN_AZ) * math.cos(SUN_EL), math.sin(SUN_EL), -math.cos(SUN_AZ) * math.cos(SUN_EL)]
)


def load(name: str, g: dict) -> np.ndarray:
    raw = np.fromfile(TER / name, dtype=np.float16).astype(np.float32)
    return raw.reshape(int(g["nz"]), int(g["nx"]))


class Field:
    """Height lookup in world metres: the fine grid where it exists, else the coarse grid."""

    def __init__(self, meta: dict):
        self.c = meta["coarse"]
        self.f = meta["fine"]
        self.hc = load("coarse_h.bin", self.c)
        self.hf = load("fine_h.bin", self.f)

    @staticmethod
    def _sample(
        h: np.ndarray, g: dict, x: np.ndarray, z: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        st = float(g["step"])
        i = (x - float(g["x0"])) / st
        j = (z - float(g["z0"])) / st
        inside = (i >= 0) & (j >= 0) & (i <= h.shape[1] - 1) & (j <= h.shape[0] - 1)
        v = ndimage.map_coordinates(h, [j, i], order=1, mode="nearest")
        return v, inside

    def height(self, x: np.ndarray, z: np.ndarray, use_fine: bool) -> np.ndarray:
        hc, _ = self._sample(self.hc, self.c, x, z)
        if not use_fine:
            return hc
        hf, inside = self._sample(self.hf, self.f, x, z)
        return np.where(inside, hf, hc)


def horizon_tan(field: Field, x, z, h0, dx, dz, dists, use_fine) -> np.ndarray:
    best = np.full(x.shape, -10.0, dtype=np.float32)
    for d in dists:
        hs = field.height(x + dx * d, z + dz * d, use_fine and d < 600.0)
        np.maximum(best, (hs - h0) / d, out=best)
    return best


def bake(field: Field, g: dict, h: np.ndarray, use_fine: bool, name: str, masks_only: bool) -> None:
    st = float(g["step"])
    nz, nx = h.shape
    jj, ii = np.mgrid[0:nz, 0:nx].astype(np.float32)
    x = float(g["x0"]) + ii * st
    z = float(g["z0"]) + jj * st
    h0 = h + 1.0  # lift the ray start a little so the cell itself never shadows

    if masks_only:
        old = np.asarray(Image.open(TER / f"{name}_light.png"), dtype=np.float32) / 255.0
        sun, sky = old[..., 0], old[..., 1]
    else:
        sun, sky = light(field, x, z, h0, h, st, use_fine, name)
    masks(h, st, sun, sky, name)


def light(field: Field, x, z, h0, h, st, use_fine, name):
    # R: sun. Steps grow with distance (fine detail near, cheap far), out to 9 km.
    d = np.concatenate([np.arange(st, 200.0, st), np.geomspace(200.0, 9000.0, 140)])
    hor = np.hypot(TO_SUN[0], TO_SUN[2])
    sdx, sdz = TO_SUN[0] / hor, TO_SUN[2] / hor
    ht = horizon_tan(field, x, z, h0, sdx, sdz, d, use_fine)
    sun_ang = SUN_EL
    hang = np.arctan(ht)
    # 2 degree penumbra: the sun disc and the data's softness
    sun = np.clip((sun_ang - hang) / math.radians(2.0) + 0.5, 0.0, 1.0)
    print(f"{name}: sun lit {sun.mean():.2f}")

    # G: sky visibility, cosine weighted, 12 directions, 1.2 km
    dd = np.concatenate([np.arange(st, 60.0, st), np.geomspace(60.0, 1200.0, 28)])
    sky = np.zeros_like(h)
    dirs = 12
    for k in range(dirs):
        a = 2.0 * math.pi * k / dirs
        t = horizon_tan(field, x, z, h0, math.cos(a), math.sin(a), dd, use_fine)
        el = np.clip(np.arctan(t), 0.0, math.pi / 2)
        sky += 1.0 - np.sin(el) ** 2
    sky /= dirs
    print(f"{name}: sky mean {sky.mean():.2f}")
    return sun, sky


def masks(h, st, sun, sky, name) -> None:

    # B: concavity from the Laplacian of the smoothed surface at two scales
    sm1 = ndimage.gaussian_filter(h, 15.0 / st)
    sm2 = ndimage.gaussian_filter(h, 60.0 / st)
    lap = ndimage.laplace(sm1) / (st * st) * 400.0 + ndimage.laplace(sm2) / (st * st) * 1600.0
    concave = np.clip(lap / np.percentile(lap[lap > 0], 97.0), 0.0, 1.0) ** 0.7

    # A: scree aprons, moderate slope (20-40 deg) within 60 m of a face steeper than 48 deg
    gy, gx = np.gradient(ndimage.gaussian_filter(h, 5.0 / st), st)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    cliff = slope > 48.0
    near_cliff = ndimage.maximum_filter(cliff.astype(np.uint8), size=max(3, int(120.0 / st))) > 0
    scree = near_cliff & (slope > 20.0) & (slope < 42.0) & (h > 2.0)
    scree = ndimage.gaussian_filter(scree.astype(np.float32), 10.0 / st)

    img = np.stack([sun, sky, concave, scree], axis=-1)
    out = Image.fromarray(np.clip(img * 255.0 + 0.5, 0, 255).astype(np.uint8), "RGBA")
    out.save(TER / f"{name}_light.png", optimize=True)
    print(f"wrote {name}_light.png {out.size}")


def main() -> None:
    meta = json.loads((TER / "terrain.json").read_text())
    field = Field(meta)
    masks_only = "--masks-only" in sys.argv
    bake(field, meta["fine"], field.hf, True, "fine", masks_only)
    bake(field, meta["coarse"], field.hc, False, "coarse", masks_only)


if __name__ == "__main__":
    main()
