# Sources and method

Built September 2026. All final terrain, resource and river rows are stored both in the native map and in `map_data.json`; the validator checks equality. District coordinates are approximate regional/field centers snapped to nearby usable hexes, not surveyed parcel boundaries.

## Geographic inputs

| Input | Source and role |
|---|---|
| Land, islands, borders and lakes | [Natural Earth 1:10m](https://www.naturalearthdata.com/downloads/10m-physical-vectors/), including the North American lake supplement and admin-1 boundaries. Natural Earth data are public domain. |
| River courses | [Natural Earth rivers and lake centerlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/), plus the North American supplement. |
| Detailed California rivers | USGS National Hydrography Dataset reaches distributed by [California DWR's Major Rivers and Creeks item](https://www.arcgis.com/home/item.html?id=96b5e9ff480d43efa3ebf63519e00ada). Queried named reaches from its hosted layer 1, including an additional 114 Sacramento/San Joaquin Delta reaches in bbox −122.1,37.65 to −121.1,38.65 (`delta_rivers.geojson`). |
| Supplemental Southern California reaches | A [redistributed California NHD service](https://services1.arcgis.com/eGSDp8lpKe5izqVc/ArcGIS/rest/services/California_Rivers__Streams__and_Waterways_WFL1/FeatureServer/5), for San Diego, Ventura and Santa Maria. This is a supplemental distribution, not the DWR-hosted service. |
| Elevation | [Mapzen/Tilezen Terrarium tiles](https://github.com/tilezen/joerd/blob/master/docs/formats.md), public S3 elevation-tiles-prod tiles at zoom 7. Source elevations include USGS 3DEP, NOAA ETOPO1, INEGI, SRTM and GMTED. See [Tilezen's attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md). The proposed NOAA ETOPO2022 download was not used. |
| Ecological regions | [US EPA Level III ecoregions](https://www.epa.gov/eco-research/ecoregions), `us_eco_l3`, used for grass/plains/desert and generalized woodland character. |

Projection: **EPSG:3310, California Albers**. Center grid origin: x = −500,000 m, y = −685,000 m. Neighbor-center distance: 15,500 m. Row spacing: 15,500 × √3 / 2 m. Pointy-top hexes, odd rows shifted east by half a hex, row 0 at the south. All of the source California polygon is contained in the rectangular bounds.

Terrain uses tile-wide elevation samples and 90th-to-10th-percentile relief. Valley differentiation uses a 5 × 5 sample across the central 6 km. Basin and Range centers with less than 180 m of local relief remain flat unless independently classified as mountains. Terrain thresholds are modeling choices, not an official landform classification.

River routing uses shortest paths on the actual legal land-bank hex-edge graph, with penalties for displacement from the source course. Duplicate source courses are merged without severing the primary line. Shared vertices require compatible drainage families; small source-supported gaps can be reconnected. A spanning forest removes snapping loops, followed by downstream orientation. See the JSON notes for each gap repair and endpoint adjustment. Lakes connect their entering/exiting river systems through water, not blue edges over the lake interior. River clipping uses the actual rasterized lake hexes, and narrow source-supported water connections keep Mead continuous. Manual minimum-width geographic axes preserve Owens, Salinas, Carson and Death Valley floors; one San Bruno land hex and two Colorado estuary/Gulf water hexes correct raster bottlenecks. Every edit is recorded in `map_data.json` notes; see `LANDFORM_AUDIT.md`.

## Iconic resource anchors

| Resource | Districts and primary evidence |
|---|---|
| Wine | Napa, Sonoma/Russian River, Alexander Valley, Mendocino, Lodi, Paso Robles, Santa Ynez, Temecula, Santa Lucia Highlands, Livermore, Santa Cruz Mountains. [TTB's established AVAs](https://www.ttb.gov/regulated-commodities/beverage-alcohol/wine/established-avas) and [AVA map explorer](https://www.ttb.gov/regulated-commodities/beverage-alcohol/wine/ava-map-explorer). |
| Silver | Comstock and Tonopah: [USGS precious-metal district study](https://www.usgs.gov/programs/mineral-resources-program/science/magmatic-tectonic-history-and-component-sources-major). Cerro Gordo and other California mining districts: [California Geological Survey minerals inventory](https://www.conservation.ca.gov/cgs/minerals/critical). |
| Oil | Los Angeles City, Wilmington/Long Beach, Kern River, Midway-Sunset, Elk Hills, Lost Hills, South Belridge, Coalinga, Cat Canyon and offshore fields. [CalGEM annual report](https://www.conservation.ca.gov/calgem/Documents/2021%20CalGEM%20Supervisor%20Annual%20Report.pdf), [Well Finder](https://www.conservation.ca.gov/calgem/Pages/WellFinder.aspx) and [field-specific project locations](https://www.conservation.ca.gov/index/Pages/ProjectPlug.aspx). |
| Mercury | New Almaden, New Idria and Clear Lake. [USGS California mercury research](https://www.usgs.gov/centers/california-water-science-center/science/mercury). |
| Copper | Copperopolis, Yerington, Ely/Robinson, Bagdad and Jerome. Regional geologic placement informed by USGS district publications, including [Yerington](https://www.usgs.gov/media/files/mrerp-report-06hqgr0171) and [Ely](https://www.usgs.gov/publications/porphyry-copper-deposit-exposed-liberty-open-pit-mine-near-ely-nevada-part-2-formation). |
| Salt / evaporites | Bonneville/Pilot Valley: [USGS hydrology study](https://pubs.usgs.gov/publication/wsp2057). Great Salt Lake: [USGS geochemical study](https://www.usgs.gov/publications/geochemical-evolution-great-salt-lake-utah-usa). Nevada saline basins and Clayton/Columbus districts: [USGS Salt Resources of the United States](https://pubs.usgs.gov/bul/0669/report.pdf). Smoke Creek basin: [USGS hydrogeologic setting](https://pubs.usgs.gov/wri/1993/4043/report.pdf). Death Valley, Owens and Searles: [USGS saline basin study](https://www.usgs.gov/publications/salines-owens-searles-and-panamint-basins-southeastern-california). Carrizo: [BLM Soda Lake](https://www.blm.gov/visit/soda-lake-overlook). Game salt abstracts mixed evaporite and saline-playa geography; cluster sizes are gameplay choices. |

Gold deposits are omitted at the user's request. There are no gold-resource substitutions. No rare-earth deposit is relabeled as aluminum. Remaining strategic and bonus resources are gameplay distributions rather than asserted real-world deposits. Vineyards, rice, citrus and ranching represent regional economic geography across eras, not an ancient Californian crop inventory.

## Civ VI format and rules

The native schema was extracted from an actual WorldBuilder file in [je-suis-tm's Civ VI modding repository](https://github.com/je-suis-tm/Sid-Meier-s-Civilization-6-modding), under Apache 2.0. All inherited terrain, players, DLC dependencies and scenario data were cleared. See `NOTICE.md` and `LICENSE-APACHE-2.0.txt`.

Identifier and placement facts were checked against the game's [base gameplay data](https://github.com/mrobaczyk/civ6/tree/main/Base/Assets/Gameplay/Data), with Gathering Storm floodplain extensions. River edge/flow enums were checked against game map utility code and the reference converter. These are textual identifiers, not arbitrary numeric IDs.

Authored resources are stored directly in `PlotResources`. Some intentionally differ from procedural `Resource_ValidTerrains` / `Resource_ValidFeatures` spawning filters. The game data's `Improvement_ValidResources` and `Improvement_ValidTerrains` support their corresponding mines, plantations and oil wells. [YnAMP's Civ VI importer](https://github.com/Gedemon/Civ6-YnAMP/blob/master/Override/AssignStartingPlots.lua) likewise directly sets imported resources. This is evidence for the format approach, not an in-engine validation of this particular map.

The inspector's medallion resource pictograms are original Canvas drawings. No Firaxis icon artwork was extracted or redistributed.

The complete inspector resource catalog contains 41 ordinary base-game map resources plus Amber, Olives and Turtles, documented in the [official Rise and Fall manual, pp. 19–20](https://steamcdn-a.akamaihd.net/steam/apps/645402/manuals/CIV_VI_EXP_ONLINE_MANUAL_ENG.PDF) and available with Gathering Storm. Optional resource packs and non-map/special resources are excluded. Catalog entries are included even when their count is zero.

## Later river, mountain and resource revisions

- The DWR service also supplied 179 New/Alamo River reaches in bbox −116.1,32.45 to −115.15,33.35 (`imperial_rivers.geojson`). These drain into the Salton Sea, independently of the main Colorado. [California Water Boards basin overview](https://water.waterboards.ca.gov/coloradoriver/water_issues/programs/salton_sea/).
- [USGS National Map NHD flowlines, layer 6](https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6) supplied 1,694 reaches named Carson River, East Fork Carson River, West Fork Carson River, Walker River, East Walker River and West Walker River. Query extent −120.5,37.7 to −117.7,40.25; fields `gnis_name,fcode,flowdir`; GeoJSON EPSG:4326; `maxAllowableOffset=.0005`. Stored as `nevada_rivers.geojson`. The national copy replaces overlapping DWR copies of these names to avoid destructive duplicate-line noding.
- [USGS NHD waterbodies, layer 12](https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/12) supplied Lahontan Reservoir (`nevada_lakes.geojson`), queried by name in bbox −119.5,39.1 to −118.8,39.65. The simplified polygon is repaired for validity and its largest-overlap hex retained. At this map scale the reservoir is enlarged to one tile.
- Agricultural interpretation: [USGS Walker Basin science](https://www.usgs.gov/centers/nevada-water-science-center/science/science-walker-river-basin), [Carson basin description](https://nevada.usgs.gov/crfld/Carson/basindesc.htm), and [Lahontan Valley irrigation study](https://pubs.water.usgs.gov/sir20055102/sir2005-5102.pdf). Flat riverbanks in the named irrigated valleys receive floodplain fertility without changing adjacent ridges. This is not a flood-hazard map.
- Tahoe mountain/forest geography: [USFS Lake Tahoe Basin management plan](https://www.fs.usda.gov/sites/nfs/files/legacy-media/laketahoebasin/Final%20LMP%20-%20July%202016.pdf) and [Desolation Wilderness plan](https://www.fs.usda.gov/Internet/FSE_DOCUMENTS/fsm9_045945.pdf). Four named western highland control points preserve ranges that the whole-hex relief threshold understated. Two eastern shore cells use forested plains to retain both the forested lake margin and a passable Carson Valley at this scale.
- `RESOURCE_AUDIT.md` records the evidence and interpretation for all 19 previously missing resources. Fourteen types were added; five remain absent. Deposits of unusual crops and the historic Wakamatsu colony are explicitly labeled as small or historical rather than implying major contemporary production.

## Forest audit and Lassen revision

See [FOREST_AUDIT.md](FOREST_AUDIT.md). The exact public MRLC categorical image is included in `source_data/forest_landcover_2021.tif`. Reproduction request:

```text
https://www.mrlc.gov/geoserver/mrlc_display/wms?service=WMS&version=1.1.1&request=GetMap&layers=mrlc_display:NLCD_2021_Land_Cover_L48&styles=&srs=EPSG:4326&bbox=-125,32,-112,43&width=1560&height=1320&format=image/geotiff
```

This uses USGS NLCD 2021 forest classes, downsampled by the WMS rendering; it does not claim original 30 m precision.
