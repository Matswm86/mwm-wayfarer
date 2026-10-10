# Terrain source: Copernicus DEM GLO-30 (R2 archipelago and R3 canyon look-dev)

## Files
- `Copernicus_DSM_COG_10_N38_00_E020_00_DEM.tif`: 1x1 degree tile, Kefalonia (Greece) west coast. Used for R2.
- `Copernicus_DSM_COG_10_N29_00_E035_00_DEM.tif`: 1x1 degree tile, Wadi Rum (Jordan). Used for R3.
- `Copernicus_DSM_COG_10_N30_00_E035_00_DEM.tif`: 1x1 degree tile, Petra area (Jordan). Downloaded as a candidate, not used.
- Fetched 2026-10-10 from the public AWS Open Data bucket `copernicus-dem-30m`
  (`https://copernicus-dem-30m.s3.amazonaws.com/<name>/<name>.tif`, listed at https://registry.opendata.aws/copernicus-dem/).
- `../kefalonia_game.npz`, `../wadirum_game.npz`: the same data resampled (bicubic, 10 m) into the scene frames by
  `tools/terrain/cop_to_game.py`; the Kefalonia sea floor is invented (a shelf shaped by distance from the shore),
  since the DSM has no bathymetry.

## Licence (verified 2026-10-10 from the official licence text)
Source: "Licence for the use of the Copernicus WorldDEM-30", instance COP-DEM-GLO-30-F Global 30m Full, Free & Open,
https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf

Quotes:
- Preamble: "Copernicus is therefore making it available on a free basis for the general public under the terms and
  conditions of this Licence." ("General Public" = "any natural or legal person".)
- Article 3: "The rights granted under this Licence are worldwide and without limitation in time."
- Article 4: rights of "(a) reproduction; (b) distribution; (c) communication to the General Public; (d) adaptation,
  modification and combination with other data and information."
- Article 5: "The use rights granted under this licence are free of charge to the User."
- No non-commercial restriction appears in the licence. The licence excludes WorldDEM-10. The Earth Engine catalogue
  notes GLO-30 is free worldwide except Armenia and Azerbaijan; neither tile here is in those countries.

## Required notices (Article 6)
We adapt the data (resample, reshape the sea floor, add small-scale relief), so Article 6(b) applies. In the game
credits and store listing:

> produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved

Article 6(c) also requires this sentence in the licence or legal notice of anything we distribute:

> The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.

Article 6(d): do not suggest that Copernicus, ESA, the EU or Airbus endorses the game. The "WorldDEM" trade mark may
only be used to refer to this data.
