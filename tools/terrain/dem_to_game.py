"""Resample the Kartverket DTM (© Kartverket, CC BY 4.0) into the fjord scene's game frame.

Game frame: +Y runs down the fjord axis from Gudvangen, +X points to the right (east) shore.
Output npz: grid (heights in metres, water bottom made negative), grid origin/step, and per-y
shore tables xs (right shore x) and W (water width) that scene_fjord.py uses for placement.
Run with the geo venv: ~/MWM/data/tools/geo-venv/bin/python tools/terrain/dem_to_game.py
"""

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "_raw" / "dem" / "naeroy_dtm10.tif"
OUT = ROOT / "assets" / "_raw" / "dem" / "naeroy_game.npz"

HEAD = np.array([57435.0, 6776385.0])  # southern tip of the fjord water (UTM33)
AXIS = np.array([0.654, 0.757])  # fjord direction, bearing 41 deg
START = 1300.0  # game y=0 sits this far down the fjord from the head
STEP = 10.0
X0, X1, Y0, Y1 = -7000.0, 7000.0, -4000.0, 11000.0

src = rasterio.open(SRC)
dem = src.read(1).astype(np.float64)
water = dem <= 1.0
lab, _ = ndimage.label(water)
fjord = lab == np.argmax(np.bincount(lab.ravel())[1:]) + 1
depth = ndimage.distance_transform_edt(fjord) * 10.0
z = np.where(fjord, -10.0 - 30.0 * np.minimum(1.0, depth / 120.0), np.maximum(dem, 1.0))

right = np.array([AXIS[1], -AXIS[0]])
origin = HEAD + AXIS * START
xs_g = np.arange(X0, X1 + STEP, STEP)
ys_g = np.arange(Y0, Y1 + STEP, STEP)
GX, GY = np.meshgrid(xs_g, ys_g)
E = origin[0] + GX * right[0] + GY * AXIS[0]
N = origin[1] + GX * right[1] + GY * AXIS[1]
inv = ~src.transform
col, row = inv * (E, N)
col = np.clip(col - 0.5, 0, dem.shape[1] - 1.001)
row = np.clip(row - 0.5, 0, dem.shape[0] - 1.001)
grid = ndimage.map_coordinates(z, [row, col], order=1)

# shore tables: for each y, the water run that continues the previous one
ty = np.arange(-500.0, 4000.0 + STEP, STEP)
xs_t, w_t = np.zeros_like(ty), np.zeros_like(ty)
centre = 0.0
for i, y in enumerate(ty):
    j = int(round((y - Y0) / STEP))
    wrow = grid[j] < 0
    runs, k = [], 0
    while k < len(wrow):
        if wrow[k]:
            s = k
            while k < len(wrow) and wrow[k]:
                k += 1
            runs.append((xs_g[s], xs_g[k - 1]))
        k += 1
    if runs:
        a, b = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - centre))
        centre = (a + b) / 2
        xs_t[i], w_t[i] = b, max(20.0, b - a)
    else:
        xs_t[i], w_t[i] = (xs_t[i - 1], w_t[i - 1]) if i else (40.0, 80.0)

np.savez_compressed(OUT, grid=grid.astype(np.float32), x0=X0, y0=Y0, step=STEP, ty=ty, xs=xs_t, w=w_t)
print("saved", OUT, grid.shape, "z", round(float(grid.min())), round(float(grid.max())))
for y in (0, 25, 200, 500, 1000, 1500, 2500, 3500):
    i = int((y + 500) / STEP)
    print(f"y={y:5d} right shore x={xs_t[i]:7.0f} width={w_t[i]:5.0f}")
