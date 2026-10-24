# California at the Last Glacial Maximum: reconstruction notes

## What this represents

An **approximate 21,000 calendar years BP landscape**, at the same 80 × 88 grid and 15.5 km hex spacing as the modern version. It is a playable, evidence-informed scenario, not a precise or synchronous paleogeographic atlas. Ice and lake maxima occurred at different times. It deliberately avoids combining the largest known shoreline of every lake with the lowest sea level as if they were contemporaneous.

## Sea level and drainage

Sea level is set to **−125 m relative to today's datum**, using the modern terrain/bathymetric grid. Existing continental land remains land; exposed ocean cells become land where the center elevation exceeds −125 m. This exposes the Bay floor and continental shelf. The four northern Channel Islands are joined as **Santarosae**, with a minimum one-hex Anacapa passage to prevent a false mainland bridge. This minimum-width correction exceeds the width of some real straits.

This is not a full relative-sea-level model: no tectonic displacement, sediment removal, glacial isostatic adjustment or time-varying delta deposition is modeled. Modern reservoir surfaces are a further limitation of the DEM. Modern reservoirs and the modern Salton Sea are removed. The Salton Trough is left as an uncertain arid basin, rather than importing a late-Holocene Lake Cahuilla highstand into 21 ka.

Modern river valleys supply the inland reference network, re-routed to the new water boundaries. The exposed Bay/shelf Sacramento paleovalley and selected short coastal extensions are **inferred drainage paths**, not mapped paleochannels. Sacramento and San Joaquin join on land and reach the lowered Pacific coast. Colorado continues toward the southern crop boundary; its lowstand Gulf mouth can lie outside this rectangle. New/Alamo modern courses are omitted. The modern map's Southern California river-density reduction is not applied to this colder, effectively wetter scenario.

## Pluvial lakes

Each lake is a connected flood fill on a ~1 km sampled DEM, seeded in its basin, then rasterized to hexes by center inclusion or 25% area overlap. Small lakes use a minimum hex where possible. The chosen levels are **scenario estimates**; the sensitivity values are plausible adjustment ranges for exploration, not statistical confidence intervals. Bounded flood-fill domains avoid filling unrelated depressions. Modern deposition, rebound and imperfect DEM spill elevations limit precision.

| Lake / basin | Scenario level (m, modern datum) | Sensitivity (±m) | Native water hexes |
|---|---:|---:|---:|
| Bonneville | 1450 | 60 | 214 |
| Lahontan — western basins | 1260 | 30 | 48 |
| Lahontan — Carson/Humboldt | 1220 | 35 | 23 |
| Lahontan — Walker | 1230 | 40 | 1 |
| Russell (Mono) | 2073 | 30 | 3 |
| Owens | 1145 | 25 | 5 |
| Searles | 670 | 35 | 4 |
| Manly | 0 | 50 | 7 |
| Mojave | 287 | 15 | 1 |
| Honey | 1240 | 30 | 5 |
| Surprise | 1380 | 35 | 4 |
| Chewaucan | 1320 | 40 | 0 |
| Warner | 1430 | 35 | 3 |
| Franklin | 1830 | 30 | 4 |
| Tulare | 65 | 20 | 13 |

Bonneville uses an intermediate transgressive level, below the later ~1,552 m maximum. Lahontan's western and eastern subbasins are represented separately; its later ~1,338 m Sehoo maximum is not imposed. Russell uses the published Tioga-era approximation. Levels for the smaller basins are less securely constrained to the target date and should be treated as low-confidence scenario choices. Chewaucan lies outside or at the northern crop; zero hexes means it is not represented, not that the lake was dry.

Large native water bodies may behave like inland seas under Civ VI's lake-size rules. Their labels do not guarantee freshwater adjacency or lake-specific yields. Salt resources beneath expanded lakes are removed.

## Biomes

The map replaces modern vegetation with regional rules informed by pollen/midden literature: lower montane conifer belts, cold Great Basin steppe and open woodland, expanded juniper/conifer mosaics in parts of the Mojave, cooler coastal parkland, alpine tundra and some pluvial-margin marshes. Low hot/arid basins remain desert rather than turning every desert into dense forest. The Central Valley is principally cool grassland/parkland, represented by Plains.

These are **rule-based interpretations**, not downscaled PMIP/BIOME simulation output. Broad modern EPA regions provide location masks; elevation and latitude set cold/highland zones, with deterministic patchiness. No modern NLCD percentage is presented as ancient forest evidence. Hex details expose the assigned paleobiome.

## Glaciers and ice sheets

The detailed Yosemite Tioga polygon is rasterized where it covers at least 20% of a hex. Within its bounding footprint, this map overrides the broader Sierra approximation. Elsewhere, range axes and elevation thresholds approximate Sierra, Cascade, Trinity/Klamath, Warner and selected Nevada alpine ice. Shasta and Lassen each retain a minimum ice-cap hex. Those approximations are explicitly marked with lower confidence in the inspector. They do not resolve individual moraines, nunataks, valley tongues or ice thickness.

No continental ice-sheet tiles are placed: the Cordilleran and Laurentide ice sheets lay north of this regional crop. The normal Civ VI ICE feature is water-only, so **land glaciers use empty, impassable Snow Mountain terrain**. This preserves an ice barrier but visually and mechanically generalizes valley ice as mountains. There is no melting simulation, custom glacier mod or blanket Pacific sea ice. Snow/tundra alone outside glacier-tagged cells does not imply glacier coverage.

## Gameplay and inspection

Resources are Civ gameplay abstractions, not archaeological evidence of farming or mining at 21 ka. Valid surviving mineral districts are retained, inundated sites disappear, woodland fauna are redistributed, and strategic/luxury abundance is capped. Crop icons stand for gameplay potential; the map does not claim domesticated crops grew there. Starts are reselected for the altered land, rivers, food and expansion space; modern city names are only orientation labels. Native starts remain automatic rather than fixed player slots.

The offline inspector embeds both map versions. Switch **Landscape version** while keeping the same camera, or choose **Changes from modern**. Change colors distinguish new water, exposed waterbed, glacier cells and biome/terrain changes. Source overlays show reference geometry and inferred shelf extensions; they are not an independent paleogeographic truth layer.

See SOURCES.md for mapped versus interpretive evidence and validation_report.json for actual checks. Static validation cannot establish engine loading, in-game flooding, resource improvements or AI behavior.
