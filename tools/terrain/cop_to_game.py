"""Resample Copernicus DEM GLO-30 tiles into a local metric game frame for the non-Norway look-dev scenes.

Data: Copernicus WorldDEM-30 (GLO-30), see assets/_raw/dem/cop30/SOURCE.md for licence and the required notice.
Frame: transverse Mercator centred on the preset origin, +X east, +Y north, metres. Output npz: grid (heights,
sea floor shaped by distance from shore when the preset has sea=True), x0, y0, step.

Run with the geo venv: ~/MWM/data/tools/geo-venv/bin/python tools/terrain/cop_to_game.py <preset>
Presets: kefalonia (R2 archipelago look-dev, Myrtos bay to Assos), wadirum (R3 canyon look-dev).
"""

import sys
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
COP = ROOT / "assets" / "_raw" / "dem" / "cop30"

PRESETS = {
    # lon, lat of the frame origin; extent in metres; tile
    "kefalonia": dict(
        tile="N38_00_E020_00",
        lon=20.540,
        lat=38.340,
        ext=(-6000, 6000, -5000, 9000),
        step=10.0,
        sea=True,
    ),
    # sharpen=(sigma_m, amount): unsharp mask on the 30 m data; GLO-30 rounds Wadi Rum's near-vertical sandstone walls
    # into 40-50 deg domes. Clamped so the valley floor never drops below its local minimum (no trenches at the toe).
    "wadirum": dict(
        tile="N29_00_E035_00",
        lon=35.449,
        lat=29.556,
        ext=(-5000, 5000, -4000, 8000),
        step=10.0,
        sea=False,
        sharpen=(45.0, 0.9),
    ),
}


def main(name: str) -> None:
    p = PRESETS[name]
    src = rasterio.open(COP / f"Copernicus_DSM_COG_10_{p['tile']}_DEM.tif")
    dem = src.read(1).astype(np.float64)
    if p["sea"]:
        # DSM sea is ~0 m; give it a believable shelf: shallow sand for the first ~200 m, then deeper water
        sea = dem <= 0.5
        lab, _ = ndimage.label(sea)
        big = lab == np.argmax(np.bincount(lab.ravel())[1:]) + 1
        d = ndimage.distance_transform_edt(big) * 30.0
        dem = np.where(
            big, -(0.4 + 30.0 * (1.0 - np.exp(-((d / 420.0) ** 1.5)))), np.maximum(dem, 0.6)
        )
    if p.get("sharpen"):
        sig, amt = p["sharpen"]
        blur = ndimage.gaussian_filter(dem, sig / 30.0)
        floor = ndimage.minimum_filter(dem, size=int(2 * sig / 30.0) + 1)
        dem = np.maximum(dem + amt * (dem - blur), floor)
    tm = Transformer.from_crs(
        f"+proj=tmerc +lat_0={p['lat']} +lon_0={p['lon']} +k=1 +x_0=0 +y_0=0 +ellps=WGS84",
        "EPSG:4326",
        always_xy=True,
    )
    x0, x1, y0, y1 = p["ext"]
    st = p["step"]
    xs = np.arange(x0, x1 + st, st)
    ys = np.arange(y0, y1 + st, st)
    GX, GY = np.meshgrid(xs, ys)
    lon, lat = tm.transform(GX, GY)
    inv = ~src.transform
    col, row = inv * (lon, lat)
    col = np.clip(col - 0.5, 0, dem.shape[1] - 1.001)
    row = np.clip(row - 0.5, 0, dem.shape[0] - 1.001)
    grid = ndimage.map_coordinates(dem, [row, col], order=3, mode="nearest")
    out = ROOT / "assets" / "_raw" / "dem" / f"{name}_game.npz"
    np.savez_compressed(out, grid=grid.astype(np.float32), x0=x0, y0=y0, step=st)
    print("saved", out, grid.shape, "z", round(float(grid.min()), 1), round(float(grid.max()), 1))


if __name__ == "__main__":
    main(sys.argv[1])
