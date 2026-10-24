# Sampled source inputs

`grid_inputs.json` is the portable measured input to `tools/build_maps.py`. It contains 37 elevations per hex, sampled annual rainfall, modern land overlap, island labels and simplified reference coast/river geometry. The package rebuild needs only this file, rule lists and the schema/metadata template.

The acquisition scripts are provenance records of the build workspace, not a turn-key GIS downloader: their relative paths assume `work/hawaii/data`, the separately downloaded Natural Earth land shapefile at `work/data/land`, and `outputs/Hawaii_Civ6`. Full re-acquisition requires requests, numpy, Pillow, pyproj, shapely, scipy and pyshp. `acquire_prepare.py` expects the annual `_ann` raster extracted by `acquire_more_data.py`. The initial river query in `acquire_download.py` was exploratory and truncated; the final input uses the paginated perennial query and the complete named-major-river query instead. No truncated query is used by the generator.
