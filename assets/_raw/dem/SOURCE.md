# Terrain source

- `naeroy_dtm10.tif`: Kartverket "DTM 10 Terrengmodell" via the national height WCS
  (`https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833`, coverage `nhm_dtm_topo_25833`),
  EPSG:25833 bbox 54000,6773000,67000,6789000 at 10 m, fetched 2026-10-10.
- Licence: open data, Creative Commons BY 4.0 (geonorge catalogue entry
  dddbb667-1303-4ac5-8640-7ec04c0e3918). Commercial use allowed with credit.
- Required credit in the game and store listing: "Terrain data © Kartverket" with a link to kartverket.no where possible.
- `naeroy_game.npz`: the same data rotated into the fjord scene frame by `tools/terrain/dem_to_game.py`.
