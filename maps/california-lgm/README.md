# California — Last Glacial Maximum (Gathering Storm)

Separate alternate map, approximately 21 ka. **The modern map is preserved.**

Open `inspect.html` locally for a fully offline viewer with a modern/LGM comparison selector, change colors, region jumps, resources and per-hex glacier evidence. No server is required. Read [RECONSTRUCTION.md](RECONSTRUCTION.md) for the important chronology and resolution limits.

## Install alongside the modern map

Copy **California_LastGlacialMaximum.Civ6Map** to your existing Civ VI `Saves/WorldBuilder` folder. On this Mac, that folder is:

```text
~/Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Saves/WorldBuilder
```

Its unique identity and display name, **California — Last Glacial Maximum (Gathering Storm)**, differ from the modern map. Select Gathering Storm. The map can be opened in WorldBuilder; gameplay loading has not yet been tested for this alternate. The user's previously enabled WorldBuilder setting also applies to it.

## Contents and checks

- 7,040 tiles; 4,698 land; 75 glacier proxies.
- 118 exposed ocean hexes relative to the modern map; 340 total named natural/pluvial lake hexes.
- 57/57 static checks pass. Native format, feature legality, river flow, Bay drainage, island separation, major lake connectivity and starts are checked.
- `map_data.json` is editable source data; `modern_reference.json` is the comparison snapshot.
- `paleo_lakes.csv`, `resource_counts.csv`, `suggested_starts.csv` and `glaciers.csv` provide plain-table inspection.

## Rebuild / validate

Python standard-library tools:

```sh
python3 tools/rebuild_native.py --output My_LGM.Civ6Map
python3 tools/validate_map.py --report validation_report.json
```

Full geography rebuild (work on a copy; requires the original modern-map source cache, listed in MODERN_SOURCE_DATA.md, plus numpy/scipy/shapely/pyproj/pyshp/Pillow):

```sh
python3 tools/build_lgm.py --data /path/to/source_data
python3 tools/finalize_reconstruction.py
python3 tools/balance_starts.py
python3 tools/rebuild_native.py --output California_LastGlacialMaximum.Civ6Map --force
python3 tools/validate_map.py --report validation_report.json
```

The geography stage uses `California_GatheringStorm.Civ6Map` as an intermediate filename **inside this alternate package only**; the final delivery is the distinct LastGlacialMaximum filename. `source_data/tioga_usgs_sim3414.zip` contains the original USGS ice polygon. The larger modern topography/source cache is not duplicated here.
