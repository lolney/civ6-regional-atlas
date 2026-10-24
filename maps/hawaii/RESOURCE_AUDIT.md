# Missing-resource audit

The audit adds **13 previously absent resource types** at 28 regionally grounded locations in each version. Both maps now contain **29 of the 44 standard resources**. Modern crops, ranch animals and introduced wildlife are intentionally available in the LGM scenario, as requested; the LGM map is a playable climate alternate, not a prehistoric species inventory.

Counts below are resource tiles, not production volumes or farm areas. Locations are generalized to 9 km spacing. `resource_counts.csv` includes every resource, including zeroes; `resource_audit.json` records coordinates, selected plots, sources, replaced resources, and any terrain/feature adjustments.

| Added resource | Tiles per version | Placement and basis |
|---|---:|---|
| Cattle | 4 | Parker Ranch/Waimea, Kahuku ranch country, ʻUlupalakua, and suitable southern Kauaʻi pasture. [Parker Ranch](https://www.parkerranch.com/), [NPS ranching history](https://www.nps.gov/havo/learn/historyculture/paniolo.htm), [ʻUlupalakua Ranch](https://ulupalakuaranch.com/), [Kauaʻi ranching](https://kauai-ranch.com/cattle/). The Kauaʻi placement is a regional pasture representation, not a surveyed ranch parcel. |
| Cocoa | 3 | Waialua/Oʻahu, East Hawaiʻi, and Kauaʻi crop regions. [UH cacao trials](https://www.ctahr.hawaii.edu/Site/StoryDetails.aspx?id=1749), [UH county crop profiles](https://www2.ctahr.hawaii.edu/counties/index.php). |
| Cotton | 2 | Dry leeward Oʻahu and western Molokaʻi, representing native maʻo. [Native Plants of Hawaiʻi](https://www.nativeplantsofhawaii.org/g/gossypium-tomentosum). No claim of industrial-scale cotton cultivation. |
| Deer | 3 | Maui, Molokaʻi and Lānaʻi, matching introduced axis deer. [Hawaiʻi DLNR](https://dlnr.hawaii.gov/blog/2026/05/21/nr26-66/). |
| Dyes | 3 | Oʻahu, Kauaʻi and East Hawaiʻi woodland, representing kapa dye plants such as kukui and noni. [NPS plant-use guide](https://www.nps.gov/puho/learn/nature/upload/Plant-ID-508.pdf). |
| Incense | 1 | Dry upland Hawaiʻi, as an ʻiliahi/sandalwood aromatic-product proxy. [DLNR ʻiliahi](https://dlnr.hawaii.gov/recreation/nah/hawaii/palila-forest-discovery-trail/iliahi/), [USDA Hawaiian sandalwood reference](https://www.ctahr.hawaii.edu/gsp/doc/Forestry/Little_Skolmen_CFT/CFT_Santalum_freycinetianum.pdf). |
| Olives | 1 | Kula uplands, where actual olive orchards operate. [Maui Olive Company](https://www.mauiolive.com/faq). |
| Stone | 3 | Oʻahu Hālawa area, Maui, and Hilo-area basalt/aggregate country. [USGS mineral industry](https://www.usgs.gov/centers/national-minerals-information-center/mineral-industry-hawaii), [Hawaiian Cement quarry history](https://hawaiiancement.com/history/). Exact quarry boundaries are not replicated; the Maui legal tile shifts roughly two hex spacings from the reference area. |
| Tea | 2 | Volcano and Mealani/Waimea uplands, with documented tea cultivation. [UH CTAHR tea-growing study](https://www.ctahr.hawaii.edu/oc/freepubs/pdf/NPH-9.pdf). |
| Tobacco | 1 | Historical Kona cultivation, supported by agricultural records. [UH agricultural history](https://www.ctahr.hawaii.edu/oc/freepubs/pdf/MP-180.pdf). Not a claim of a major present-day industry. |
| Turtles | 3 | Legal reef tiles around the central islands and Hawaiʻi. [NOAA Hawaiian green sea turtles](https://www.fisheries.noaa.gov/resource/outreach-materials/hawaiian-green-sea-turtle-brochure). Reef locations move with the LGM coast, so the central-islands tile may lie closer to Molokaʻi than Oʻahu. |
| Wheat | 1 | A flat Maui agricultural hex, a regional proxy for documented historical Kula wheat production. [UH agricultural history](https://www.ctahr.hawaii.edu/oc/freepubs/pdf/MP-180.pdf). |
| Wine | 1 | ʻUlupalakua vineyard district. [MauiWine's vineyard history](https://mauiwine.com/company/). |

## Placement compromises

Civ VI's stock rules matter: Cattle requires clear, flat Grass; Tea and Stone require compatible clear terrain; Cocoa requires Rainforest; Deer normally needs Forest; Wine on hills needs a Forest feature.

The audit therefore makes small land-use representations in both versions: four cattle pastures (one previously hilly Kahuku tile becomes flat; two dry Plains cells become Grass), localized plantation/quarry clearings, a woodland-edge cell on Lānaʻi, and canopy proxies for cacao and the sloping vineyard. These are recorded per tile. No mountain, river, island coastline or coast-navigation corridor is removed for a resource. The cold-climate surroundings remain intact; modern crops are deliberate game content.

Earlier native-legal placements and start balancing remain, including Kona coffee, sugar, rice, horses and maritime food. Some common resources are replaced at audited locations. Final totals are **242 resource tiles modern; 270 LGM**. Each suggested start still has food and luxury access under the static checks.

## Reviewed but still absent

These zeroes are intentional, not overlooked. “No suitable deposit identified” means this audit found no defensible map-scale placement; it does not claim that laboratory traces or every isolated occurrence are absent.

| Resource | Decision |
|---|---|
| Amber | No credible regional amber deposit identified; tropical living-tree resin is not equivalent to an amber deposit. |
| Coal | No coalfield identified in this young volcanic island setting. |
| Copper | No suitable copper ore district identified; trace metals in volcanic rock do not justify a copper mine resource. |
| Diamonds | No diamond-bearing deposit identified; Hawaiian olivine/peridot is not diamond. |
| Furs | No convincing terrestrial fur-bearing resource district identified. Axis deer already has its own resource. |
| Gypsum | No credible map-scale gypsum deposit identified. Minor volcanic alteration/sulfate occurrences are not forced into an ore-field tile. |
| Ivory | No elephant/walrus resource. Whale-tooth cultural material is not represented as a fictitious land-animal ivory population. |
| Jade | No suitable jade deposit identified; green olivine is not jade. |
| Marble | Basalt and limestone/reef rock are not marble; construction stone is represented by Stone. |
| Mercury | No appropriate mercury ore district identified. |
| Oil | No mapped petroleum field added. Imported/refined petroleum is not a natural deposit. |
| Silk | No sufficiently convincing contemporary sericulture district identified. Hawaiian kapa/paper mulberry is not silk. |
| Silver | No suitable silver ore district identified. |
| Truffles | No verified regional truffle-producing district identified. Documented cultivated mushrooms at Hāmākua are different fungi; they are not silently substituted for truffles. [Hawaiʻi Department of Agriculture](https://hdoa.hawaii.gov/add/soq-companies/hamakua-heritage-farm/). |
| Uranium | No mapped uranium ore district added. |

The [USGS industry overview](https://www.usgs.gov/centers/national-minerals-information-center/mineral-industry-hawaii) emphasizes aggregate, crushed stone and certain natural gemstones rather than a broad suite of metal ores. Existing Iron and Aluminum remain explicitly disclosed gameplay concessions. Completing the resource checklist was not treated as a reason to fabricate every deposit.
