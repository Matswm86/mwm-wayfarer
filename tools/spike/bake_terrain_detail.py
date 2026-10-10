"""Bake per-texel terrain normals and water-flow masks for the fjord terrain (visual pass 2).

Far terrain tiles have 40-80 m between vertices, so vertex normals smear the relief of the 10 m
data. The shader reads this map per pixel instead, so every ridge, chute and bench of the DEM
lights correctly at any distance.

Output (RGBA8 PNG, one texel per height sample, same rect as the height files):
  assets/terrain/coarse_detail.png  over coarse_h.bin (10 m)
  assets/terrain/fine_detail.png    over fine_h.bin (2.5 m, village area)
  R, G = surface normal x, z (n * 0.5 + 0.5; y = sqrt(1 - x^2 - z^2))
  B = wetness: D8 flow accumulation (log scale), so water-stained streaks and moss follow the
      real fall lines and gullies of the DEM
  A = convexity: ridges and edges (drier, paler, lichen)

Run: python3 tools/spike/bake_terrain_detail.py   (numpy, scipy, Pillow; about 1 min)
Terrain data (c) Kartverket, CC BY 4.0.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
TER = ROOT / "assets" / "terrain"
# 8 neighbours (dj, di)
NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def load(name: str, g: dict) -> np.ndarray:
    return np.fromfile(TER / name, dtype="<f4").reshape(int(g["nz"]), int(g["nx"]))


def normals(h: np.ndarray, st: float) -> tuple[np.ndarray, np.ndarray]:
    gz, gx = np.gradient(h.astype(np.float64), st)
    n = np.stack([-gx, np.ones_like(gx), -gz], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n[..., 0], n[..., 2]


def flow_accumulation(h: np.ndarray, st: float) -> np.ndarray:
    """D8: every cell drains to its steepest lower neighbour; upstream cells summed by relaxation."""
    nz, nx = h.shape
    hp = np.pad(h, 1, mode="edge")
    best = np.zeros_like(h)
    recv = np.arange(h.size).reshape(h.shape)
    jj, ii = np.mgrid[0:nz, 0:nx]
    for dj, di in NB:
        d = st * (2.0**0.5 if dj and di else 1.0)
        drop = (h - hp[1 + dj : 1 + dj + nz, 1 + di : 1 + di + nx]) / d
        better = drop > best
        best = np.where(better, drop, best)
        tj = np.clip(jj + dj, 0, nz - 1)
        ti = np.clip(ii + di, 0, nx - 1)
        recv = np.where(better, tj * nx + ti, recv)
    recv = recv.ravel()
    own = np.arange(h.size)
    flows = recv != own
    src = own[flows]
    dst = recv[flows]
    acc = np.ones(h.size)
    inflow = np.zeros(h.size)
    # relaxation: acc = 1 + sum(acc of donors); converges after the longest flow path
    for it in range(4000):
        inflow[:] = np.bincount(dst, weights=acc[src], minlength=h.size)
        new = 1.0 + inflow
        if np.array_equal(new, acc):
            print(f"  flow converged after {it} passes")
            break
        acc = new
    return acc.reshape(h.shape)


def bake(h: np.ndarray, st: float, name: str, wet_extra: np.ndarray | None = None) -> np.ndarray:
    nx_, nz_ = normals(ndimage.gaussian_filter(h, 0.6), st)
    acc = flow_accumulation(ndimage.gaussian_filter(h, 1.0), st)
    area = acc * st * st  # m2 upstream
    # 0 below 3000 m2 upstream (sheet wash), 1 from 0.5 km2 (a real stream)
    wet = np.clip((np.log10(area) - np.log10(3000.0)) / 2.2, 0.0, 1.0) ** 1.5
    wet = ndimage.grey_dilation(wet, size=(3, 3))
    wet = ndimage.gaussian_filter(wet, 6.0 / st)
    if wet_extra is not None:
        wet = np.maximum(wet, wet_extra)
    sm = ndimage.gaussian_filter(h, 8.0 / st)
    lap = ndimage.laplace(sm) / (st * st)
    convex = np.clip(-lap / np.percentile(-lap[lap < 0], 95.0), 0.0, 1.0) ** 0.8
    img = np.stack([nx_ * 0.5 + 0.5, nz_ * 0.5 + 0.5, wet, convex], axis=-1)
    out = Image.fromarray(np.clip(img * 255.0 + 0.5, 0, 255).astype(np.uint8), "RGBA")
    out.save(TER / f"{name}_detail.png", optimize=True)
    print(f"wrote {name}_detail.png {out.size} wet mean {wet.mean():.3f}")
    return wet


def main() -> None:
    meta = json.loads((TER / "terrain.json").read_text())
    c, f = meta["coarse"], meta["fine"]
    hc = load("coarse_h.bin", c)
    hf = load("fine_h.bin", f)
    wet_c = bake(hc, float(c["step"]), "coarse")
    # carry the big streams of the whole valley into the fine area (bilinear from coarse)
    st_c, st_f = float(c["step"]), float(f["step"])
    jj, ii = np.mgrid[0 : hf.shape[0], 0 : hf.shape[1]].astype(np.float64)
    ci = (float(f["x0"]) + ii * st_f - float(c["x0"])) / st_c
    cj = (float(f["z0"]) + jj * st_f - float(c["z0"])) / st_c
    wet_up = ndimage.map_coordinates(wet_c, [cj, ci], order=1, mode="nearest")
    bake(hf, st_f, "fine", wet_up)


if __name__ == "__main__":
    main()
