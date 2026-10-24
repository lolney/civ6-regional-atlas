# Review of previously missing resources

Reviewed all 19 resource types that were absent before this pass. **Fourteen now have placements; five remain absent.** The map now contains 39 of its 44 available resource types. Counts below are occupied tiles, not strategic-resource quantities.

| Resource | Tiles | Placement or reason for absence |
|---|---:|---|
| Furs | 18 | Northern California, southern Oregon and Sierra forests; beaver, otter and other furbearers. [Source](https://wildlife.ca.gov/Conservation/Mammals/Beaver). |
| Cotton | 19 | Fresno, Kings, Merced and Tulare counties, plus Imperial and Palo Verde valleys. [Source](https://www.cdfa.ca.gov/Statistics/PDFs/2022-2023_california_agricultural_statistics_review.pdf). |
| Olives | 10 | Corning/Tehama, Orland/Glenn, Yolo, Tulare and San Joaquin groves. [Source](https://www.cdfa.ca.gov/Statistics/PDFs/2022-2023_california_agricultural_statistics_review.pdf). |
| Coffee | 1 | One small Goleta/Santa Barbara planting; documented commercial production, exaggerated to a whole game tile. [Source](https://cesantabarbara.ucanr.edu/files/179297.pdf). |
| Jade | 1 | One coastal Big Sur nephrite deposit near Jade Cove, placed on adjacent land. [Source](https://sanctuaries.noaa.gov/science/conservation/pdfs/Zones.pdf). |
| Diamonds | 1 | One Cherokee/Oroville placer occurrence. These are documented diamonds, not a replacement for omitted gold. Their rarity is represented by one tile. [Source](https://pubs.usgs.gov/bul/1042g/report.pdf). |
| Dyes | 3 | Native woodland plant pigments and tannins in North Coast and Sierra foothill habitats; a broad resource-category interpretation. [Source](https://www.fs.usda.gov/psw/publications/lake/psw_2024_lake004.pdf). |
| Spices | 3 | California bay laurel in the Santa Lucia Range, Santa Cruz Mountains and North Coast. This represents local seasoning leaves rather than tropical pepper. [Source](https://research.fs.usda.gov/silvics/california-laurel). |
| Sugar | 4 | Imperial Valley sugar-beet farming. The Sugar category represents the crop product, despite the game’s usual sugar-cane association. [Source](https://my.ucanr.edu/repository/fileAccessPublic.cfm?fn=ca1208p7-175555.pdf). |
| Tobacco | 3 | Native Nicotiana habitat in the North Coast, Sierra foothills and southern California. Not a claim of a modern commercial tobacco belt. [Source](https://www.calflora.org/app/taxon?crn=5862). |
| Incense | 3 | Aromatic brittlebush resin in the Coachella, Mojave and lower Colorado deserts; an explicit interpretation of the incense category. [Source](https://research.fs.usda.gov/feis/species-reviews/encfar). |
| Turtles | 1 | One San Diego coastal green-turtle habitat tile. Preserves coast without adding a fictitious tropical coral reef; this is a documented procedural spawn exception. [Source](https://www.fisheries.noaa.gov/west-coast/science-data/green-turtle-research-and-conservation-southern-california). |
| Tea | 1 | One historical Wakamatsu/Gold Hill placement near Coloma. The 1869–1871 colony was small and short-lived; this is a historical reference, not a modern producing district. [Source](https://ohp.parks.ca.gov/ListedResources/Detail/815). |
| Silk | 1 | One historical Wakamatsu sericulture placement near Coloma, with the same small-scale historical interpretation as Tea. [Source](https://www.parks.ca.gov/?page_id=24738). |
| Amber | 0 | Kept absent: no sufficiently convincing, locatable amber deposit was identified in this audit. Ordinary fresh tree resin is not treated as fossil amber. |
| Bananas | 0 | Kept absent: a suitable regional production district was not verified. Garden cultivation alone did not justify a tile or artificial rainforest. |
| Cocoa | 0 | Kept absent: no convincing outdoor cacao district was identified within this temperate/desert map. |
| Ivory | 0 | Kept absent: the map has no native elephant resource; fossil mammoths and elephant seals are not substituted. |
| Pearls | 0 | Kept absent: the documented Gulf pearl industry is centered much farther south than the small upper-Gulf corner in this map. A local pearl fishery was not verified. [Source](https://repository.library.noaa.gov/view/noaa/3028/noaa_3028_DS1.pdf). |

Resource counts and locations are game-scale interpretations across eras. A single coffee, diamond or historical tea/silk tile does not imply a large industry. All such qualifications also appear when selecting the deposit in the inspector. Existing named wine, oil, silver, mercury, copper and salt districts remain in place.

The complete inventory is in `resource_counts.csv`, including zeroes. `iconic_resources.csv` contains the exact authored plot locations. Procedural spawn exceptions are listed individually in `validation_report.json`; native IDs and improvement domains are checked, but actual improvement construction remains untested in Civ VI.

Imperial Valley floodplains follow newly added **New and Alamo River** NHD reaches into the Salton Sea. They represent the requested irrigated agricultural fertility, not a claim that current farms depend on uncontrolled annual flooding. [California Water Boards basin overview](https://water.waterboards.ca.gov/coloradoriver/water_issues/programs/salton_sea/).
