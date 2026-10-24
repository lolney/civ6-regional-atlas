# Regional Atlas for Civilization VI

[Explore the live atlas](https://lolney.github.io/civ6-regional-atlas/) · [Download all four native maps](https://lolney.github.io/civ6-regional-atlas/downloads/all-native-maps.zip)

Geographic **Gathering Storm** maps of California and Hawaiʻi, in modern and Last Glacial Maximum (~21 ka) climates. Each map has an offline inspector, editable geographic data, native WorldBuilder output, validation tools and source citations.

| Region | Modern | Last Glacial Maximum | Grid |
|---|---|---|---|
| California | [Native map](maps/california-modern/California_GatheringStorm.Civ6Map) | [Native map](maps/california-lgm/California_LastGlacialMaximum.Civ6Map) | 80 × 88, approximately Huge tile count |
| Hawaiʻi | [Native map](maps/hawaii/Hawaii_Modern.Civ6Map) | [Native map](maps/hawaii/Hawaii_LGM.Civ6Map) | 84 × 54, Standard |

The atlas lets visitors select all four maps, inspect terrain/rivers/resources, and download either a native map or a complete source package. Source packages work offline by opening their `inspect.html`. GitHub Pages serves the atlas without a backend.

Hawaiʻi includes continuous Coast-water routes between all islands and 29 resource types. Both climate versions use modern crops, ranch animals and introduced wildlife as gameplay analogues. California's maps include geographic river networks, regional resources, and an Ice Age alternate with pluvial lakes and alpine ice. Methods and uncertainty are documented within each map directory.

## Install

Copy the desired `.Civ6Map` files into your active Civ VI `Saves/WorldBuilder` folder, restart the game, and open them in WorldBuilder or select their map content in advanced setup using Gathering Storm. Enable WorldBuilder in the game's settings if needed. For exact suggested player positions, assign the inspector's listed starts in WorldBuilder; the native files do not force scenario player slots.

Typical locations:

- Windows: `Documents/My Games/Sid Meier's Civilization VI/Saves/WorldBuilder`
- Current Mac Steam: `~/Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Saves/WorldBuilder`

See the per-map README files for details. **Static validation passes, but in-game loading, automatic starts, AI behavior, disasters, dams and river rendering have not been tested.**

## Build and serve the atlas

Python 3, standard library only:

```sh
python3 tools/validate.py
python3 tools/build_site.py
python3 -m http.server 8769 --directory site
```

Open `http://127.0.0.1:8769`. The generated `site/` folder is ignored by Git and rebuilt by GitHub Actions. A push to `main` validates the map files, builds the site and ZIP downloads, and deploys GitHub Pages.

- `maps/`: authored maps, inspectors, editable data, generation tools, citations and licenses.
- `web/`: atlas interface.
- `tools/`: static-site builder and validation entry point.
- `.github/workflows/pages.yml`: GitHub Pages deployment.

The included final JSON data can rebuild native maps without large external GIS downloads. Full geographic re-acquisition requires the dependencies and caches described in the individual map packages.

## Credits and license

Project code and original resource pictograms: Apache-2.0. The native SQLite schema derives from je-suis-tm's Apache-2.0 WorldBuilder reference. Geographic sources include Natural Earth, USGS, NOAA, UH Rainfall Atlas, and Mapzen/Tilezen; underlying data terms continue to apply. See [NOTICE.md](NOTICE.md) and each package's `SOURCES.md` and terrain-attribution document. No extracted game artwork is distributed. Unofficial fan project.
