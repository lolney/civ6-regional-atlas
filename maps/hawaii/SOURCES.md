# Sources and provenance

Retrieved 20 September 2026. The source input file preserves per-hex measured samples, simplified coastlines and river traces; the game generator is deterministic and separate from acquisition.

## Geographic inputs

- [Natural Earth 1:10m land polygons](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-land/): modern island outlines; public domain.
- [Mapzen/Tilezen terrain tiles](https://github.com/tilezen/joerd): elevation and bathymetry, Terrarium zoom 9, fetched from the public `elevation-tiles-prod` S3 dataset. Decoding: red × 256 + green + blue / 256 − 32768 m. USGS/NOAA and other underlying source attributions apply; see TERRAIN-ATTRIBUTION.md. Zoom level is not a guarantee of uniform source resolution, especially offshore.
- [Rainfall Atlas of Hawaiʻi downloads](https://rainfall.geography.hawaii.edu/downloads): statewide annual ASCII grid in millimeters, 250 m cells, 1978–2007 mean. Giambelluca et al. (2013), [Online Rainfall Atlas of Hawaiʻi](https://journals.ametsoc.org/view/journals/bams/94/3/bams-d-11-00228.1.xml). The atlas, rather than a hand-drawn wet-side mask, drives the modern rainfall field.
- [USGS National Hydrography Dataset service](https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6): named perennial streams in −160.4,18.8 to −154.7,22.5; selected major names also queried for artificial flow paths. Simplification tolerance 500 m. Natural land and rivers are further generalized when converted to hexes.

## Paleoenvironmental evidence

- [USGS: Sea Level and Climate](https://pubs.usgs.gov/fs/fs2-00/): approximately 125 m lower global sea level during the last glacial maximum. The map applies a fixed −125 m scenario, without a local tectonic correction.
- [USGS: Drowned reefs and antecedent karst topography, Auʻau channel](https://pubs.usgs.gov/publication/70023950): documents LGM connections among Maui, Lānaʻi and Molokaʻi, later drowned by rising sea level. The map preserves this configuration while keeping Kahoʻolawe separate.
- Price & Elliott-Fisk (2004), *Topographic History of the Maui Nui Complex, Hawaiʻi, and Its Implications for Biogeography*, [University of Hawaiʻi repository](https://scholarspace.manoa.hawaii.edu/server/api/core/bitstreams/6f1c22da-eedc-461d-969f-1c0f3b9138ab/content): additional contextual reference for Maui Nui history; full-text retrieval was blocked during this build. The coast is computed from bathymetry, not digitized from that paper.
- Anslow, Clark, Kurz & Hostetler (2010), [Geochronology and paleoclimatic implications of the last deglaciation of the Mauna Kea Ice Cap](https://www.usgs.gov/publications/geochronology-and-paleoclimatic-implications-last-deglaciation-mauna-kea-ice-cap), DOI 10.1016/j.epsl.2010.06.025: local retreat beginning about 20.5 ± 2.5 ka, cooling around 4.5 ± 1°C, and potentially enhanced high-elevation precipitation. The later ~15.4 ka readvance is distinct from the chosen ~21 ka snapshot.
- [USGS: Mauna Kea glacier action](https://www.usgs.gov/news/volcano-watch-mauna-kea-a-good-place-observe-glacier-action): roughly 28 square miles of summit glaciation, close to one map hex.
- [USGS: Glaciers existed on Mauna Kea during recent ice ages](https://www.usgs.gov/volcanoes/mauna-kea/science/glaciers-existed-mauna-kea-during-recent-ice-ages): preserved glacial evidence and the uncertainty about former Mauna Loa ice beneath later lava.
- Hotchkiss & Juvik (1999), [A Late-Quaternary Pollen Record from Kaʻau Crater, Oʻahu](https://www.sciencedirect.com/science/article/pii/S0033589499920525): lower late-glacial precipitation at this site and a pollen-based temperature depression of 3–5°C. This supports avoiding a blanket “all Hawaiʻi became wetter” treatment; the chosen 0.8 rainfall multiplier is a modeling assumption, not a direct statewide finding.
- [NPS: Hawaiʻi volcanoes](https://www.nps.gov/havo/learn/nature/volcanoes.htm) and [USGS: Mauna Kea geology and history](https://www.usgs.gov/volcanoes/mauna-kea/science/geology-and-history-mauna-kea): volcanic landscape context.

## Game format and validation

- Installed Civ VI XML: base `Maps.xml` confirms Standard = 84 × 54; base and Gathering Storm feature/resource tables establish allowed identifiers and combinations. The package contains derived identifier/compatibility lists, not game artwork or game executables.
- [je-suis-tm / Sid-Meier-s-Civilization-6-modding](https://github.com/je-suis-tm/Sid-Meier-s-Civilization-6-modding): Apache-2.0 WorldBuilder SQLite schema reference, originally extracted from `nouveau.Civ6Map`. Reference geography is not retained.
- Python's SQLite integrity check plus the included custom `tools/validate_maps.py` provide static validation. This is not an official Firaxis validator or certification. In-game behavior has not been tested.
- [Aspyr: Mac Steam game-file location](https://support.aspyr.com/hc/en-us/articles/19003861040653-Game-Files-Missing-after-update-Civilization-VI-Mac-Steam): installation directory guidance, previously verified against the installed game on this Mac.

## Resource audit

Additional primary references and decisions for cattle, crops, native plant products, wildlife and basalt stone are linked individually in RESOURCE_AUDIT.md and source_data/resource_plan.json. Every proposed placement is preserved with its evidence and the final per-epoch tile in resource_audit.json.
