# Forest cover audit

Lassen Peak is now mountain terrain at plot 5784. The central DEM sample missed the summit within this coarse hex; the summit correction preserves the surrounding forested hills.

The old rules assigned a low random forest probability to the central coastal mountains. A map-wide audit now supplements EPA ecoregions with **NLCD 2021 deciduous, evergreen and mixed forest classes**. This adds missing woodland in Big Sur, the Santa Cruz Mountains, northern California, the Sierra and other forested uplands.

## Regional results

These bounding-box summaries are orientation regions, overlap in places, and are not administrative forest boundaries.

| Region | Land hexes | Final forest hexes | Added forest hexes retained |
|---|---:|---:|---:|
| Big Sur / Santa Lucia | 19 | 8 | 7 |
| Santa Cruz Mountains | 20 | 12 | 3 |
| North Coast / Klamath | 276 | 214 | 25 |
| Sierra Nevada | 627 | 176 | 48 |
| Southern California mountains | 294 | 39 | 2 |
| Intermountain West | 1922 | 263 | 205 |

## Method and limits

The cached MRLC WMS image covers 125°W–112°W, 32°N–43°N at 1560 × 1320 pixels (roughly 0.7–0.9 km per pixel). Its categorical RGB forest colors are sampled on a 1 km lattice within each hex. Ocean/no-data samples are excluded. This is an approximate forest-class land-area fraction, **not canopy density or a 30 m raster analysis**. The percentage is inspectable on each covered hex.

Passable, non-desert land with at least 30% sampled forest is given a forest feature. One spurious low-cover Basin and Range forest was removed. Existing moist-region forests are otherwise retained: contemporary burn scars and development should not erase every generalized forest belt. Flat valley corridors and floodplains retain priority; mountains cannot also carry the normal Civ VI forest feature. Crops and orchards are distinct NLCD classes and do not trigger this correction. Mexico and areas outside source coverage retain the ecoregion/elevation approximation.

Big Sur remains a mosaic: forested canyons and mixed evergreen woodland coexist with open chaparral and grassland hexes. USDA Forest Service research supports this mixed landscape. The map represents regional landscape character, not exact 2026 tree cover.

## Sources and reproduction

- [MRLC data services](https://www.mrlc.gov/data-services-page), legacy layer `mrlc_display:NLCD_2021_Land_Cover_L48`.
- [USFS Big Sur forest composition research](https://research.fs.usda.gov/treesearch/36473).
- [USFS Cone Peak Gradient vegetation](https://research.fs.usda.gov/psw/rnas/locations/cone-peak-gradient).
- [NPS Lassen park significance](https://www.nps.gov/lavo/learn/management/park-significance.htm).

`forest_audit.json` records individual corrections and regional totals. `source_data/forest_landcover_2021.tif` preserves the exact categorical WMS image used; copy it into the generator's data directory alongside the other source datasets.
