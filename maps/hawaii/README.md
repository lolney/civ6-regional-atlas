# Hawaiʻi — modern and Last Glacial Maximum

Two native Civilization VI: Gathering Storm WorldBuilder maps, each **84 × 54 (Standard), 4,536 hexes**, north-up and non-wrapping. They cover the eight main Hawaiian Islands on the same 9 km grid.

**All islands are connected by continuous Coast-water routes for early ships.** The islands remain separated by water in the modern map. The LGM map joins Maui, Lānaʻi and Molokaʻi into Maui Nui through exposed land, while Kahoʻolawe remains separate.

## Inspect

Open **inspect.html** directly in a browser; both complete datasets and the pictograms are embedded and work offline. The published atlas provides the same inspector online.

- Switch **Landscape version** between modern and LGM without losing your map position.
- Scroll to zoom, drag to pan, click a hex, or use the region and plot selectors.
- Toggle original Civ-like resource icons; Resource focus lists all 44 standard resources with counts, including zeroes.
- Use **Changes from modern** to find exposed seabed, biome changes and the Mauna Kea ice cap.
- Reference coastlines and river traces are available as an overlay. They depict modern source geography, not measured LGM river courses.
- Each deliberately converted navigation tile explains its Coast classification in the detail panel; its measured seafloor elevation is preserved.

Native files: **Hawaii_Modern.Civ6Map** and **Hawaii_LGM.Civ6Map**. Their names and package IDs are distinct from each other and the earlier California maps.

## Install / open in WorldBuilder

Copy either or both `.Civ6Map` files into your active Civ VI **Saves/WorldBuilder** directory, then restart Civ VI. For current Mac Steam installations, that directory is:

```text
~/Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Saves/WorldBuilder/
```

Open the desired map in WorldBuilder. If listed under Additional Content, enable its map entry, select Gathering Storm, and choose it in advanced game setup. The titles are **Hawaiʻi — Modern (Gathering Storm)** and **Hawaiʻi — Last Glacial Maximum (Gathering Storm)**. WorldBuilder must be enabled in your local game settings.

The maps declare Gathering Storm as their only dependency. No resource mod or YnAMP is required. This deliverable is terrain/map data, not a saved game or scripted scenario.

## Playability

Standard describes the grid dimensions, not the amount of land. This faithful regional crop is mostly ocean. **Six civilizations and few city-states** are a reasonable starting setup, rather than the usual eight, but this has not been playtested. Suggested positions favor food, usable land, production, coast/river access and separation. Island sizes remain asymmetric. Several coastal starts lack river freshwater; housing will need attention.

The six numbered starts are inspector suggestions, not assigned native player slots. For exact placement, use `suggested_starts.csv` to assign starts in WorldBuilder. Automatic spawning remains untested. The map does not invent oil, coal or uranium deposits; later-era access depends on trade, alternatives or your own WorldBuilder edits. Iron and aluminum are explicitly gameplay abstractions of volcanic parent material, not economic ore inventories.

## Verification and rebuilding

**89/89 static checks pass**, including SQLite integrity, the 35-table schema, Gathering Storm terrain/feature/resource compatibility, native-to-viewer equality, eight modern islands, Maui Nui connectivity, coast-only travel between every island, connected river courses reaching a shore vertex, and start placement constraints.

Run these commands from the extracted package folder using Python 3 (standard library only):

```sh
python3 tools/build_maps.py
python3 tools/validate_maps.py
```

The first command overwrites the two native maps, editable JSON datasets, and inspector from the included sampled geographic inputs and deterministic generator. The second writes `validation_report.json`. Back up edits before rebuilding. The original GIS acquisition scripts and source citations are retained for provenance; rebuilding from the included inputs needs no network or GIS packages.

**Neither map has been loaded inside Civ VI.** Static checks cannot establish automatic starts, AI behavior, volcanic disasters, river rendering, flooding, dams or improvements in the engine. Coastal flood-level attributes and native river naming records are not authored.

The missing-resource audit adds cattle and twelve other previously absent types to both climates; see [RESOURCE_AUDIT.md](RESOURCE_AUDIT.md).

See [RECONSTRUCTION.md](RECONSTRUCTION.md) for model assumptions and [SOURCES.md](SOURCES.md) for scientific sources.
