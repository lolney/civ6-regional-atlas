# Landform and river audit

Updated 19 September 2026. All corrections are in the native map and offline inspector. Open **Inspect a region** to visit the named locations below. The included validator passes **73/73 static checks**; Civ VI engine behavior remains untested.

| Finding | Cause and correction | Verification |
|---|---|---|
| Owens Valley blocked by mountains | Elevation samples mixed the narrow floor with adjacent Sierra/Inyo relief. A geographic floor axis now preserves an 11-hex, flat desert corridor from north of Bishop through the Owens Lake/Olancha area. Three erroneous mountain barriers and six hill tiles were corrected. | All 11 corridor tiles are flat, passable and connected by hex sides. Adjacent ranges remain intact. |
| Sacramento and San Joaquin stopped short of the sea | Missing lower Delta reaches and coarse shoreline snapping left their mouths inland. Added 114 DWR-hosted NHD reaches and routed both systems to Suisun Bay. | Every main-stem edge has a connected river/water route through the Bay to the Pacific. Shared lower-basin edges can carry tributary names in the inspector. |
| San Francisco was an island | The grid-center coastline test missed the San Bruno neck. One hex with 48% source land coverage now preserves that narrow land connection. | San Francisco has a land route to Palo Alto and the mainland; the Golden Gate and Carquinez waterways remain open. |
| Colorado River had artificial gaps | Short source segments were discarded, and the river was clipped against reservoir outlines even where narrow water arms did not survive rasterization. Retained short segments, clipped against actual lake hexes, and connected Lake Mead with two source-supported water hexes. | The main course connects through Mead, Mohave and Havasu to the Gulf. Mead is one connected eight-hex water body. |
| Colorado estuary was cut off | The tidal mouth was too narrow for the coarse coast raster. Two minimum-width water hexes preserve the estuary and upper Gulf. | The lower Colorado reaches the Gulf water component at the map's southeast corner. |
| Salinas, Carson and Death Valley floors looked too hilly | Broad hex samples included nearby valley walls. Preserved narrow axes along the actual floors. | Continuous flat corridors: Salinas 9 tiles, Carson 4, Death Valley 10. Seven, three and six hill tiles corrected respectively. |

| Walker and lower Carson missing | California-only NHD coverage omitted the Nevada reaches. Added 1,694 nationally sourced reaches for their main stems and forks, using the national copy instead of overlapping California duplicates. Added the omitted Lahontan Reservoir as a minimum one-hex lake. | Each full network is connected through its mapped lake/reservoir. The Carson remains separate from Tahoe, Truckee and Walker. |
| Tahoe bordered by flat desert; western ranges too weak | Shoreline hexes combined Tahoe forest with the dry Carson Valley. Changed the two mixed desert shore cells to plains/forest, and preserved four mountain cells at the Crystal Range, Rubicon highlands, Ellis Peak and Granite Chief. | No Tahoe shoreline cell is desert. Four additional west/southwest mountain cells are present; the Carson Valley route remains passable. |
| Productive Imperial and northern Nevada valleys looked barren | Added New/Alamo NHD reaches and used local relief to identify flat irrigated valley banks in Nevada. | 16 connected Imperial Valley floodplain tiles and 41 in the northern Nevada agricultural audit area; 308 map-wide. All floodplains are flat and touch real placed river edges. |

A further mainland-connectivity scan compared every detached land component with the source continental polygon. **No artificial mainland islands remain.** The map has one mainland component and six island components containing eight hexes. This is a connectivity audit, not a claim that every coastline or island is exact at this scale.

## A visible break that is geographically justified

A small upper Colorado segment near the eastern edge exits the rectangular map and re-enters farther south. Its two open ends are both on the crop boundary; the intervening real river lies outside the map. It was not rerouted through unrelated terrain to connect it inside the rectangle. Similarly, blue river edges stop at reservoir shores and resume at their outlets: the water hexes provide the connection.

## Resource and inspection updates

Salt now has **92 resource tiles**, including **45 anchored tiles across 17 named saline districts**. Bonneville itself has five nearby salt tiles, with additional concentrations in Pilot Valley, the Great Salt Lake Desert, Great Salt Lake margins, Sevier basin, Carson/Humboldt sinks, Black Rock/Smoke Creek, and smaller Nevada and California playas. Named salt anchors use flat, feature-free land. Generic deposits remain for balance; salt represents mixed evaporite geography, not an estimate of mineable reserves.

A subsequent review added 14 previously absent types, including cotton and furs; see `RESOURCE_AUDIT.md`. Resource Focus lists all **44 standard placeable map resources available with Gathering Storm**, including the five resources still absent after the subsequent resource review. Every option includes a tile count; selecting an absent resource gives an explicit empty-state message. Counts represent occupied map tiles, not the stored quantity of strategic resources. Optional pack resources such as Honey/Maize, special game-mode resources, artifacts and non-map luxuries are outside this catalog.

## Evidence and limits

The automated checks read the native SQLite database, verify agreement with `map_data.json`, and test actual hex/river connectivity. The inspector was visually checked at Bonneville, San Francisco/Delta, Owens Valley, Lake Mead, Tahoe, and the Imperial Valley; zero-count resource selection was also exercised. `validation_report.json` records the individual checks, and `verification_notes.json` records export checks.

The grid has 15.5 km between centers. Minimum-width land, water and valley corridors deliberately resolve geographic bottlenecks in favor of the correct connection. Source elevation values are preserved even where a narrow valley floor requires a flatter game terrain category. Modern reservoir outlines and historic economic geography are combined; this is not a simulation of present-day discharge or an archaeological landscape.

Primary references: [USGS Owens Valley description](https://ca.water.usgs.gov/owens/report/desc.html), [California DWR Delta overview](https://water.ca.gov/water-basics/the-delta), [Bureau of Reclamation lower Colorado operations](https://www.usbr.gov/lc/riverops.html), [NPS Death Valley geology](https://www.nps.gov/deva/learn/nature/geology.htm). Full data and salt sources are in `SOURCES.md`.

## Latest terrain and forest revision

Lassen Peak is now a mountain. Smith and Mason valley floors are flat, with additional connected agricultural floodplains. The final map has 320 floodplain hexes and 1,018 forest hexes. The forest audit adds NLCD-informed woodland, including Big Sur; see [FOREST_AUDIT.md](FOREST_AUDIT.md) for regional counts, sampling methods and limits. The inspector has direct jumps to Lassen and Big Sur, plus sampled forest-area percentages in hex details.

## Southern coastal river density

The Santa Barbara–Los Angeles–San Diego area now has 56 game river edges, approximately half its former density. Santa Ynez, Santa Clara, Los Angeles, Santa Ana, San Luis Rey, San Diego and Tijuana retain connected lower courses to the Pacific. Ventura, San Gabriel, Santa Margarita, Sweetwater and Otay are omitted as a gameplay generalization; some retained upper courses are shortened by pruning headwater ends, never middle segments. Full source courses remain visible in the geographic overlay. A one-edge San Diego mouth correction connects its previously inland endpoint to the rasterized coast. This is a deliberate aridity/readability adjustment, not a statement that the omitted rivers do not exist.
