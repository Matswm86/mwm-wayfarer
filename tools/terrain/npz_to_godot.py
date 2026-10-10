"""Bake the Naeroyfjord terrain (Kartverket DTM, CC BY 4.0) into files the Godot spike loads.

Input:  assets/_raw/dem/naeroy_game.npz (made by tools/terrain/dem_to_game.py)
Output: assets/terrain/
  coarse_h.bin   float32 heights, 1281 x 1281, 10 m step, row-major (row = Godot z, col = Godot x)
  fine_h.bin     float32 heights, 1201 x 1561, 2.5 m step, the 2 m DTM area round the village
  water_depth.png 8-bit depth below sea level (0 = shore, 255 = 60 m or deeper), same frame as coarse
  trees.bin      float32 records (x, y, z, yaw, scale, species 0 pine / 1 birch), Godot space,
                 sorted by forest chunk
  terrain.json   frame, LOD tile bounds, forest chunks, spawn, village, waterfall, Ingrid, bench path

Frame mapping (document of record): scene (x, y, h) -> Godot (x, h, -y).
Scene +X = east shore, scene +Y = down-fjord, so Godot -Z looks down the fjord.

Run with a Python that has numpy: python tools/terrain/npz_to_godot.py
"""

from __future__ import annotations

import json
import math
import struct
import zlib
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "_raw" / "dem" / "naeroy_game.npz"
OUT = ROOT / "assets" / "terrain"

# Crop: 12 800 m square, village near the middle in x, more room down-fjord than up.
SIZE = 12800.0
CX0 = -6160.0  # Godot x of the first column
CZ0 = -9300.0  # Godot z of the first row (= scene y 9300)
CSTEP = 10.0
CN = int(SIZE / CSTEP) + 1  # 1281 samples per side

# LOD quadtree: tile size (m) and cells per tile edge per level. The last level exists only over
# the 2.5 m fine data.
LEVELS = [(2560.0, 32), (1280.0, 32), (640.0, 32), (320.0, 32), (160.0, 64)]
FOREST_CHUNK = 640.0
TREES_HIGH = 90000
# tree line (m) before noise; Naeroyfjord birch and pine thin out at about 500-650 m
TREE_LINE = 560.0
# cliff rock meshes: count, one per cell (m), within this radius of the village (m)
ROCK_COUNT = 2400
ROCK_CELL = 22.0
ROCK_RADIUS = 1800.0
BIRCH_BELOW = 320.0  # birch mixes in on the lower slopes, pine above
SEED = 7


def smoothstep(a: float, b: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def write_png_gray(path: Path, img: np.ndarray) -> None:
    """8-bit greyscale PNG with the standard library only (geo-venv has no Pillow)."""
    h, w = img.shape
    raw = b"".join(b"\x00" + img[r].astype(np.uint8).tobytes() for r in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def main() -> None:
    d = np.load(SRC)
    grid = d["grid"].astype(np.float64)
    gx0, gy0, gst = float(d["x0"]), float(d["y0"]), float(d["step"])
    fine = d["fine"].astype(np.float64)
    fx0, fy0, fst = float(d["fx0"]), float(d["fy0"]), float(d["fstep"])
    ty, txs = d["ty"], d["xs"]

    def xs(y):
        return np.interp(y, ty, txs)

    # scene P0 (scene_fjord.py): player spot on the east shore, 25 m down-fjord
    p0 = (float(xs(25.0)) + 16.0, 25.0, 5.5)
    view = (-0.07, 0.997)

    def edit(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
        """scene_fjord.py h(): village shelf + spawn knoll, without the fbm micro noise."""
        e = x - xs(y)
        m = (
            0.75
            * (1 - smoothstep(90, 170, e))
            * smoothstep(-5, 15, e)
            * smoothstep(-150, -50, y)
            * (1 - smoothstep(380, 480, y))
        )
        z = z * (1 - m) + (1.0 + 0.045 * np.minimum(e, 95)) * m
        dx, dy = x - p0[0], y - p0[1]
        k = np.exp(-((dx * dx + dy * dy) / (22.0**2)))
        along = dx * view[0] + dy * view[1]
        side = dx * view[1] - dy * view[0]
        zk = p0[2] - 0.10 * np.maximum(0.0, along) + 0.03 * np.maximum(0.0, -along) + 0.12 * side
        return z * (1 - k) + zk * k

    # ---- coarse crop, in Godot orientation (row j -> z = CZ0 + 10 j -> scene y = -z)
    j = np.arange(CN)
    i = np.arange(CN)
    rows = ((-(CZ0 + CSTEP * j)) - gy0) / gst
    cols = ((CX0 + CSTEP * i) - gx0) / gst
    assert rows.min() >= 0 and rows.max() <= grid.shape[0] - 1
    assert cols.min() >= 0 and cols.max() <= grid.shape[1] - 1
    coarse = grid[np.ix_(rows.astype(int), cols.astype(int))]
    X, Z = np.meshgrid(CX0 + CSTEP * i, CZ0 + CSTEP * j)
    coarse = edit(X, -Z, coarse)

    # ---- fine grid, flipped to Godot orientation
    fine_g = fine[::-1, :].copy()
    fnz, fnx = fine_g.shape
    fgx0 = fx0
    fgz0 = -(fy0 + fst * (fnz - 1))
    FX, FZ = np.meshgrid(fgx0 + fst * np.arange(fnx), fgz0 + fst * np.arange(fnz))
    fine_g = edit(FX, -FZ, fine_g)

    OUT.mkdir(parents=True, exist_ok=True)
    coarse.astype("<f4").tofile(OUT / "coarse_h.bin")
    fine_g.astype("<f4").tofile(OUT / "fine_h.bin")
    depth = np.clip(-coarse, 0.0, 60.0) / 60.0
    write_png_gray(OUT / "water_depth.png", np.round(depth * 255.0))

    # ---- height sampler (same blend as the terrain shader: fine wins inside, 60 m feather)
    def bil(g, ox, oz, st, x, z):
        fx = np.clip((x - ox) / st, 0.0, g.shape[1] - 1.001)
        fz = np.clip((z - oz) / st, 0.0, g.shape[0] - 1.001)
        c0, r0 = fx.astype(int), fz.astype(int)
        tx, tz = fx - c0, fz - r0
        top = g[r0, c0] * (1 - tx) + g[r0, c0 + 1] * tx
        bot = g[r0 + 1, c0] * (1 - tx) + g[r0 + 1, c0 + 1] * tx
        return top * (1 - tz) + bot * tz

    fgx1, fgz1 = fgx0 + fst * (fnx - 1), fgz0 + fst * (fnz - 1)

    def height(x, z):
        hc = bil(coarse, CX0, CZ0, CSTEP, x, z)
        inner = np.minimum(np.minimum(x - fgx0, fgx1 - x), np.minimum(z - fgz0, fgz1 - z))
        k = smoothstep(0.0, 60.0, inner)
        hf = bil(fine_g, fgx0, fgz0, fst, x, z)
        return hc * (1 - k) + hf * k

    # ---- LOD tile bounds
    levels = []
    for li, (ts, cells) in enumerate(LEVELS):
        n = int(SIZE / ts)
        tiles = []
        for tj in range(n):
            for ti in range(n):
                x0, z0 = CX0 + ti * ts, CZ0 + tj * ts
                if li == len(LEVELS) - 1 and (
                    x0 + ts < fgx0 or x0 > fgx1 or z0 + ts < fgz0 or z0 > fgz1
                ):
                    continue
                c0, c1 = int((x0 - CX0) / CSTEP), int((x0 + ts - CX0) / CSTEP)
                r0, r1 = int((z0 - CZ0) / CSTEP), int((z0 + ts - CZ0) / CSTEP)
                blk = coarse[r0 : r1 + 1, c0 : c1 + 1]
                lo, hi = float(blk.min()), float(blk.max())
                fc0, fc1 = int(max(0, (x0 - fgx0) / fst)), int(min(fnx - 1, (x0 + ts - fgx0) / fst))
                fr0, fr1 = int(max(0, (z0 - fgz0) / fst)), int(min(fnz - 1, (z0 + ts - fgz0) / fst))
                if fc1 > fc0 and fr1 > fr0:
                    fb = fine_g[fr0 : fr1 + 1, fc0 : fc1 + 1]
                    lo, hi = min(lo, float(fb.min())), max(hi, float(fb.max()))
                tiles.append([ti, tj, round(lo - 2.0, 1), round(hi + 2.0, 1)])
        levels.append({"size": ts, "cells": cells, "tiles": tiles})

    # ---- forest (visual pass 2): dense stands with clearings, not scattered single trees.
    # Density = altitude below a noisy tree line x slope (none on cliffs) x stand noise at
    # ~150 m and ~45 m with a sharp threshold; wet ground (DEM flow, coarse_detail.png B) is
    # denser and holds more birch. The same density field is saved as forest_mask.png so the
    # terrain draws forest floor under the stands.
    rng = np.random.default_rng(SEED)

    def smooth_noise(cells: int, sigma: float) -> np.ndarray:
        return ndimage.gaussian_filter(rng.random((cells, cells)), sigma, mode="wrap")

    n150 = smooth_noise(int(SIZE / 50), 3.0)
    n45 = smooth_noise(int(SIZE / 15), 3.0)
    n_line = smooth_noise(64, 2.0)
    for n in (n150, n45, n_line):
        n -= n.min()
        n /= n.max()
    wet_img = Image.open(OUT / "coarse_detail.png").getchannel("B")
    wet_grid = np.asarray(wet_img, dtype=np.float32) / 255.0

    def field(f, x, z):
        return bil(f, CX0, CZ0, SIZE / (f.shape[0] - 1), x, z)

    def density(x, z, hgt, slope):
        line = TREE_LINE + 160.0 * (field(n_line, x, z) - 0.5)
        alt = (1.0 - smoothstep(line - 90.0, line, hgt)) * smoothstep(3.0, 8.0, hgt)
        steep = 1.0 - smoothstep(33.0, 43.0, slope)
        wet = field(wet_grid, x, z)
        stand = 0.7 * field(n150, x, z) + 0.3 * field(n45, x, z) + 0.25 * wet
        stand = smoothstep(0.42, 0.56, stand)
        return alt * steep * stand, wet

    trees = []
    want = TREES_HIGH
    while len(trees) < want:
        m = 200000
        x = CX0 + rng.random(m) * SIZE
        z = CZ0 + rng.random(m) * SIZE
        hgt = height(x, z)
        dx = (height(x + 5, z) - height(x - 5, z)) / 10.0
        dz = (height(x, z + 5) - height(x, z - 5)) / 10.0
        slope = np.degrees(np.arctan(np.hypot(dx, dz)))
        sy = -z
        e = x - xs(sy)
        village = (sy > 90) & (sy < 300) & (e < 85) & (e > -40)
        spawn = np.hypot(x - p0[0], sy - p0[1]) < 16.0
        dens, wet = density(x, z, hgt, slope)
        ok = ~village & ~spawn & (rng.random(m) < dens**1.5)
        for xx, zz, hh, ww in zip(x[ok], z[ok], hgt[ok], wet[ok]):
            p_birch = (0.35 + 0.4 * ww) * (1.0 - smoothstep(BIRCH_BELOW * 0.5, BIRCH_BELOW, hh))
            birch = rng.random() < p_birch
            trees.append(
                (xx, hh - 0.3, zz, rng.uniform(0, math.tau), rng.uniform(0.7, 1.3), float(birch))
            )
            if len(trees) >= want:
                break
    # forest floor mask over the coarse grid
    slope_c = np.degrees(np.arctan(np.hypot(*np.gradient(coarse, CSTEP))))
    mask, _ = density(X, Z, coarse, slope_c)
    mask = ndimage.gaussian_filter(mask, 1.0)
    Image.fromarray(np.clip(mask * 255.0 + 0.5, 0, 255).astype(np.uint8), "L").save(
        OUT / "forest_mask.png", optimize=True
    )
    tr = np.array(trees, dtype=np.float32)
    nck = int(SIZE / FOREST_CHUNK)
    ci = np.clip(((tr[:, 0] - CX0) / FOREST_CHUNK).astype(int), 0, nck - 1)
    cj = np.clip(((tr[:, 2] - CZ0) / FOREST_CHUNK).astype(int), 0, nck - 1)
    key = cj * nck + ci
    order = np.lexsort((rng.random(len(tr)), key))  # by chunk, shuffled inside a chunk
    tr, key = tr[order], key[order]
    chunks = []
    for k in np.unique(key):
        idx = np.nonzero(key == k)[0]
        sub = tr[idx]
        chunks.append(
            [
                int(k % nck),
                int(k // nck),
                int(idx[0]),
                int(len(idx)),
                round(float(sub[:, 1].min()) - 1, 1),
                round(float(sub[:, 1].max()) + 25, 1),
            ]
        )
    tr.astype("<f4").tofile(OUT / "trees.bin")

    # ---- cliff rocks (visual pass 2): rock meshes along the steep bands round the village, at
    # most one per ROCK_CELL m cell on faces of 45-78 deg, half sunk into the slope; up = the
    # surface normal blended halfway to world up. Record: x, y, z, nx, ny, nz, yaw, size.
    rocks = []
    taken = set()
    tries = 0
    while len(rocks) < ROCK_COUNT and tries < 60:
        tries += 1
        m = 200000
        ang = rng.random(m) * math.tau
        rad = np.sqrt(rng.random(m)) * ROCK_RADIUS
        x = p0[0] + 150.0 + np.cos(ang) * rad
        z = -(p0[1] + 150.0) + np.sin(ang) * rad
        hgt = height(x, z)
        dx = (height(x + 3, z) - height(x - 3, z)) / 6.0
        dz = (height(x, z + 3) - height(x, z - 3)) / 6.0
        slope = np.degrees(np.arctan(np.hypot(dx, dz)))
        ok = (slope > 45.0) & (slope < 78.0) & (hgt > 3.0)
        for xx, zz, hh, gx, gz in zip(x[ok], z[ok], hgt[ok], dx[ok], dz[ok]):
            cell = (int(xx // ROCK_CELL), int(zz // ROCK_CELL))
            if cell in taken:
                continue
            taken.add(cell)
            n = np.array([-gx, 1.0, -gz])
            n /= np.linalg.norm(n)
            size = float(rng.uniform(8.0, 22.0))
            pos = np.array([xx, hh, zz]) - n * size * 0.3
            rocks.append((*pos, *n, rng.uniform(0, math.tau), size))
            if len(rocks) >= ROCK_COUNT:
                break
    np.array(rocks, dtype="<f4").tofile(OUT / "rocks.bin")
    print("rocks:", len(rocks))

    # ---- points of interest (scene_fjord.py coordinates)
    def gpt(x, y, up=0.0):
        return [
            round(float(x), 2),
            round(float(height(np.array(x), np.array(-y))) + up, 2),
            round(-float(y), 2),
        ]

    houses = [
        (28, 118, 12, 6.0, 9.0, 0),
        (46, 140, 98, 5.5, 8.0, 1),
        (22, 160, 8, 5.0, 7.0, 2),
        (55, 178, 95, 6.5, 10.0, 0),
        (30, 205, 15, 5.0, 7.0, 0),
        (62, 222, 100, 5.0, 7.5, 2),
        (36, 246, 20, 6.0, 8.0, 1),
        (70, 262, 90, 5.0, 6.5, 0),
        (14, 270, 5, 4.5, 6.0, 3),
        (5, 150, 90, 5.0, 9.0, 3),  # boathouses (naust)
        (5, 192, 90, 5.0, 9.0, 3),
    ]
    village = [
        {"pos": gpt(xs(y) + dx, y, -0.15), "yaw": yaw, "w": w, "d": dd, "wall": wall}
        for dx, y, yaw, w, dd, wall in houses
    ]
    # waterfall: scene_fjord.py falls_real(), down the real gully on the east wall near y=1300
    falls, fy = [], 1300.0
    for k in range(48):
        e = 520 - k * (505 / 47)
        fy = min(
            (fy + dd for dd in range(-24, 25, 4)),
            key=lambda yy: float(height(np.array(xs(yy) + e), np.array(-yy))),
        )
        falls.append(gpt(xs(fy) + e, fy, 1.5))
    yj = 172.0
    # Ingrid stands on the shore by the jetty, turned toward the spawn
    ing = (float(xs(yj)) + 5.0, yj - 5.0)
    # Godot yaw for a model facing +Z (glTF export of a MakeHuman figure)
    ing_yaw = math.degrees(math.atan2(p0[0] - ing[0], -(p0[1] - ing[1])))
    jetty = {"from": [float(xs(yj)) + 2, 0.6, -yj], "to": [float(xs(yj)) - 30, 0.6, -yj]}

    def air(e, y, alt):
        """Bench point: e = metres east of the east shore line, alt = metres above sea level."""
        return [round(float(xs(y) + e), 1), alt, round(-float(y), 1)]

    bench = [
        air(16, 10, 9),
        air(60, 170, 35),
        air(-150, 450, 45),
        air(-260, 900, 60),
        air(-250, 1500, 90),
        air(-180, 2300, 220),
        air(150, 2600, 520),
        air(300, 1900, 760),
        air(100, 1100, 520),
        air(-120, 500, 220),
        air(-60, 60, 40),
        air(16, 10, 9),
    ]
    meta = {
        "credit": "Terrain data (c) Kartverket, CC BY 4.0",
        "frame": "scene (x, y, h) -> Godot (x, h, -y); Godot -Z = down-fjord",
        "coarse": {"x0": CX0, "z0": CZ0, "step": CSTEP, "nx": CN, "nz": CN},
        "fine": {"x0": fgx0, "z0": fgz0, "step": fst, "nx": fnx, "nz": fnz, "feather": 60.0},
        "levels": levels,
        "forest": {"chunk": FOREST_CHUNK, "count": int(len(tr)), "chunks": chunks},
        "spawn": gpt(p0[0], p0[1], 1.0),
        "spawn_yaw_deg": -10.0,
        "village": village,
        "jetty": jetty,
        "waterfall": falls,
        "ingrid": {"pos": gpt(ing[0], ing[1]), "yaw_deg": round(ing_yaw, 1)},
        "bench_path": bench,
    }
    (OUT / "terrain.json").write_text(json.dumps(meta, separators=(",", ":")))
    sizes = {p.name: p.stat().st_size for p in OUT.iterdir()}
    print("tiles per level:", [len(lv["tiles"]) for lv in levels])
    print("trees:", len(tr), "chunks:", len(chunks))
    print("coarse h range:", float(coarse.min()), float(coarse.max()))
    print("spawn:", meta["spawn"])
    print("files:", sizes, "total MB:", round(sum(sizes.values()) / 1e6, 2))


if __name__ == "__main__":
    main()
