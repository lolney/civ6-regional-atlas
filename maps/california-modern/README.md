# California — Civilization VI: Gathering Storm

An 80 × 88, north-up, non-wrapping WorldBuilder map. Its 7,040 hexes are almost exactly the tile count of the game's standard Huge map (106 × 66 = 6,996). It contains the full sourced California outline and Channel Islands, plus adjoining parts of Oregon, Nevada, Arizona, Utah and Baja California.

**This is a native `.Civ6Map` SQLite database, not a saved game or a picture. Static validation passes; it has not been loaded in Civ VI.**

## Inspect the map

Open **`inspect.html`** in a browser. It contains the map data and original resource pictograms, works offline, and needs no installation or network connection.

- Scroll to zoom, drag to pan, and click a hex for its game terrain, feature, resource, elevation and coordinates.
- **Inspect a region** jumps to the named wine, oil and mineral districts, representative valleys, rivers or suggested starts.
- **Resource focus** isolates a particular resource's icons and lists all 44 standard Gathering Storm map resources, including absent entries. Every option shows its tile count; `resource_counts.csv` provides the same complete inventory.
- Turn on **Source coastlines and rivers** to compare the snapped game geometry with the reference data. Dashed purple channels are seasonal reference courses, not permanent game rivers.
- Green stripes mark floodplains. Gold numbered circles mark suggested civilization starts. Modern place names are only orientation labels.
- The native file and inspector data are checked against one another by the included validator. `iconic_resources.csv` and `suggested_starts.csv` provide the same key locations as plain tables.

## Install

Copy `California_GatheringStorm.Civ6Map` into **`Saves/WorldBuilder`** under your active Civ VI user-data folder. Create the WorldBuilder subfolder if needed.

Typical Windows location:

```text
Documents\My Games\Sid Meier's Civilization VI\Saves\WorldBuilder
```

For current **Mac Steam**, Aspyr documents this user-data root:

```text
~/Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI
```

Append `/Saves/WorldBuilder`. Older Mac installations may use the outer folder; App Store installations use a different container. Use the folder in which your installation actually writes its saves. [Aspyr's location guidance](https://support.aspyr.com/hc/en-us/articles/19003861040653-Game-Files-Missing-after-update-Civilization-VI-Mac-Steam).

Restart the game after copying. Enable **California — Huge (Gathering Storm)** in Additional Content if listed, then select the Gathering Storm ruleset and the map in Create Game / Advanced Setup. The map also carries WorldBuilder metadata so it can be opened for editing there. The [format reference's installation instructions](https://github.com/je-suis-tm/Sid-Meier-s-Civilization-6-modding) use this WorldBuilder folder.

The only declared dependency is Gathering Storm. No resource mod, YnAMP installation or leader pack is required. The inspector's **12 starts are suggestions**, not hard-coded player slots: native player/start tables remain empty for the game's automatic placement. If you want those exact positions, assign them in WorldBuilder using the listed plot coordinates.

## Geography and gameplay

Terrain uses real elevation and EPA ecoregions. Within Basin and Range regions, the relief across the central 6 km of a hex separates flat valley floors from nearby slopes; high absolute elevation alone does not make a valley a hill. Mountain ridges remain terrain-derived. Narrow floor corridors preserve traversable Owens, Salinas, Smith, Mason, Carson and Death valleys. See `LANDFORM_AUDIT.md` for the peninsula, Delta, Colorado and valley corrections, with connectivity evidence.

Rivers follow Natural Earth and USGS NHD linework, routed along legal Civ VI hex edges. Genuine sub-hex gaps are joined, separate known watersheds are kept apart, and flow is directed toward a low mouth. Rivers terminate at lakes and the sea; a lake can legitimately interrupt the sequence of blue river edges. The Walker/Carson forks and main stems use national USGS NHD coverage, including Lahontan Reservoir. Seasonal desert channels remain in the source overlay. Floodplains occupy connected groups of flat, actual riverbank tiles, particularly in the Central Valley and lower Colorado region. New/Alamo riverbanks represent Imperial Valley agriculture; additional northern Nevada valley banks represent irrigated farmland. These are fertility abstractions, not modern flood-frequency claims.

Resources emphasize recognizable economic geography: Napa/Sonoma and other wine regions; Comstock, Tonopah and Cerro Gordo silver; Los Angeles, Kern County and offshore oil; Coast Range mercury; named copper districts; and 92 salt tiles, with strong concentrations around Bonneville and other western saline basins. **Gold is deliberately omitted, with no proxy deposits.** The additional resource review added cotton, furs, olives and eleven other previously missing types at researched locations; see `RESOURCE_AUDIT.md` for the choices and remaining absences. Other deposits and agricultural resources provide gameplay balance. Their quantities are game values, not reserve estimates.

Some authored deposits are outside the game's **procedural resource-spawn filters**—for example, oil on Kern County plains and vineyards on hills. Their native resource IDs and broad improvement domains are checked; the actual terrain is preserved. These static checks do not prove that every authored combination behaves correctly in the game. Every such exception is explicitly listed in `map_data.json` and `validation_report.json`. This is an additional area to verify during the first in-game load.

## Validation and tools

From this folder, with Python 3:

```sh
python3 tools/validate_map.py --report validation_report.json
```

The validator uses only the standard library. It checks SQLite integrity, the real WorldBuilder table schema, plot references and identifiers, terrain/features/resources, river ownership and flow, cycles, coastal connectivity, floodplain groups, suggested starts, named deposits, California coverage, and native/preview agreement. The current release passes 73 checks, including the named landform regressions and the complete resource catalog/counts. It documents resource-spawn exceptions rather than silently treating them as ordinary procedural placements.

I found a useful native-map generation/schema reference, but no independent comprehensive `.Civ6Map` validator. The available [civ6-save-parser](https://github.com/pydt/civ6-save-parser) and [civ-6-map-viewer](https://github.com/MalTeeez/civ-6-map-viewer) target saved-game formats. SQLite tools can inspect the native database; Civ VI WorldBuilder and a new game remain the authoritative loading checks.

Included tools:

- `tools/validate_map.py`: read-only checks and JSON report.
- `tools/rebuild_native.py`: rebuild a native map from `map_data.json`, the schema and metadata snapshot; also refreshes the standalone inspector.
- `tools/place_iconic_resources.py`: reproduce district placement on a freshly generated geography.
- `tools/place_regional_resources.py`: add researched missing resources after district placement.
- `tools/balance_starts.py`: select generic starts using freshwater, early food/production potential, expansion space and separation. It adds limited resources, never moves the terrain.
- `tools/build_geography.py`: geospatial generation source. Requires the separately downloaded source datasets; see its header and `SOURCES.md`.

Run generation stages in this order: `build_geography.py`, `place_iconic_resources.py`, `place_regional_resources.py`, `balance_starts.py`, then `rebuild_native.py --viewer-only` and the validator. The resource-placement and start-selection scripts are generation stages, not read-only inspection tools. Run them on a copy when experimenting. They update both the native file and JSON; run `rebuild_native.py --viewer-only` afterward to refresh the HTML.

## Limits

At 15.5 km between adjacent centers, the map cannot resolve every narrow valley, tributary or offshore island. Small islands, selected lakes, narrow valley floors, the San Francisco Peninsula neck, and key Bay/Gulf waterways use a minimum width of one tile. The Colorado briefly exits the eastern crop before re-entering; that genuine outside-map interval remains disconnected in the rectangle. Lakes include some modern reservoirs. Ecoregions describe potential landscape character; forest placement is generalized, not a contemporary tree-cover inventory.

The map is an authored interpretation, not a cadastral or hydrological dataset. Flow directions and start quality are useful approximations, not hydraulic or game-engine simulations. The start score does not incorporate every civilization's abilities or every later-era yield.

In-game loading, automatic spawning, AI, river graphics, resource improvements, flooding and dam eligibility remain untested. Official [September 2019 patch notes](https://support.civilization.com/hc/en-us/articles/39409989034643-Patch-Notes-September-2019-Update) describe support for flooding on manually drawn WorldBuilder rivers, but static database checks cannot establish that the necessary engine behavior works here. Named river geography is available in the inspector; in-game named-river records are not authored. No volcanoes, coastal flooding levels, natural wonders, prebuilt cities or units are imposed.

See `SOURCES.md`, `NOTICE.md` and `validation_report.json` for provenance and validation details.

## Latest terrain and forest revision

Lassen Peak is now a mountain. Smith and Mason valley floors are flat, with additional connected agricultural floodplains. The final map has 320 floodplain hexes and 1,018 forest hexes. The forest audit adds NLCD-informed woodland, including Big Sur; see [FOREST_AUDIT.md](FOREST_AUDIT.md) for regional counts, sampling methods and limits. The inspector has direct jumps to Lassen and Big Sur, plus sampled forest-area percentages in hex details.

## Southern coastal river density

The Santa Barbara–Los Angeles–San Diego area now has 56 game river edges, approximately half its former density. Santa Ynez, Santa Clara, Los Angeles, Santa Ana, San Luis Rey, San Diego and Tijuana retain connected lower courses to the Pacific. Ventura, San Gabriel, Santa Margarita, Sweetwater and Otay are omitted as a gameplay generalization; some retained upper courses are shortened by pruning headwater ends, never middle segments. Full source courses remain visible in the geographic overlay. A one-edge San Diego mouth correction connects its previously inland endpoint to the rasterized coast. This is a deliberate aridity/readability adjustment, not a statement that the omitted rivers do not exist.
