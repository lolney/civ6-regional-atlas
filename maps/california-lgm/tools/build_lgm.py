from pathlib import Path
import argparse,zipfile,re
package=Path(__file__).resolve().parent.parent
ap=argparse.ArgumentParser(description='Rebuild LGM geography from the original cached modern-map source datasets. Overwrites this package map data; work on a copy.')
ap.add_argument('--data',type=Path,required=True);args=ap.parse_args()
with zipfile.ZipFile(package/'source_data/tioga_usgs_sim3414.zip') as z:z.extractall(package/'source_data/tioga')
s=(package/'tools/modern_generator.py').read_text()
s=s.replace("OUT=ROOT/'outputs/California_Civ6'","OUT=ROOT/'outputs/California_LGM'")
s=s.replace('# All topological neighbours and unique Civ VI owned edges.',"exec((ROOT/'work/lgm/geography.py').read_text())\n\n# All topological neighbours and unique Civ VI owned edges.")
s=s.replace('selected={};river_routes=[]', "exec((ROOT/'work/lgm/river_extensions.py').read_text())\nselected={};river_routes=[]")
s=s.replace('dry=l.difference(raster_lake_union)','dry=l.difference(unary_union([raster_lake_union,glacier_union]))')
s=s.replace("name=f['properties'].get('GNIS_Name') or f['properties'].get('gnis_name')","name=f['properties'].get('GNIS_Name') or f['properties'].get('gnis_name')\n  if name in ['New River','Alamo River']:continue")
a=s.index('# Southern coastal river density');b=s.index('rg=collections.defaultdict(list)',a);s=s[:a]+s[b:]
s=s.replace(",'southern_coastal_river_density':socal_audit",'')
s=s.replace('rg=collections.defaultdict(list)\nfor ei in selected:', """# Delta confluence on the exposed Bay floor (one coarse-grid edge).
join=next(ei for ei,e in enumerate(edges) if e['i']==4182 and e['side']=='NE')
if join not in selected:selected[join]={'name':'San Joaquin','error':name_geom['San Joaquin'].distance(Point(mid[join]))}
rg=collections.defaultdict(list)
for ei in selected:""")

s=s.replace("'AACA6192-0284-4288-9000-619202600002'","'CACA2100-2100-4210-8210-000000000021'")
s=s.replace("name='California — Huge ('+('Base Game' if edition=='Base' else 'Gathering Storm')+')'","name='California — Last Glacial Maximum (Gathering Storm)'")
s=s.replace("desc='80 × 88. Real coastlines, elevation-derived terrain, mapped rivers; balanced resources. No world wrap.'","desc='80 × 88. Approximate 21 ka landscape; lower seas, pluvial lakes, shifted biomes and alpine glaciers. See reconstruction notes.'")
s=s.replace("'forest_reference_percent':round(float(forest_fraction[i])*100,1) if valid_samples[i]>=20 else None,","'paleobiome':biomes[i],'glacier':glaciers.get(i),'modern_terrain':json.loads((ROOT/'outputs/California_Civ6/map_data.json').read_text())['tiles'][i]['terrain'],")
# Avoid repeated JSON reads in tile loop.
s=s.replace("for i in range(W*H):\n preview['tiles']", "modern_preview=json.loads((ROOT/'outputs/California_Civ6/map_data.json').read_text())\nfor i in range(W*H):\n preview['tiles']")
s=s.replace("json.loads((ROOT/'outputs/California_Civ6/map_data.json').read_text())['tiles'][i]['terrain']","modern_preview['tiles'][i]['terrain']")
s=s.replace("'tahoe_terrain_corrections':tahoe_edits","'tahoe_terrain_corrections':tahoe_edits,'paleo_lakes':paleo_lake_audit,'epoch_ka':21,'sea_level_m':-125,'continental_ice_sheet_hexes':0")
# Name remains internal for compatibility with supplied balance script; rename at export.
s=s.replace("ROOT=Path(__file__).resolve().parent.parent",'ROOT=Path('+repr(str(package))+')')
s=s.replace("DATA=ROOT/'work/data'",'DATA=Path('+repr(str(args.data.resolve()))+')')
s=s.replace("OUT=ROOT/'outputs/California_LGM'",'OUT=ROOT')
s=s.replace("ROOT/'work/lgm/geography.py'","ROOT/'tools/geography_reconstruction.py'").replace("ROOT/'work/lgm/river_extensions.py'","ROOT/'tools/river_extensions.py'")
s=s.replace("ROOT/'outputs/California_Civ6/map_data.json'","ROOT/'modern_reference.json'")
a=s.index('import xml.etree.ElementTree as ET');b=s.index('# Gathering Storm resource additions',a)
s=s[:a]+"rules=json.loads((ROOT/'rules.json').read_text())['resources']\nrterr=collections.defaultdict(set,{k:set(v) for k,v in rules['terrains'].items()});rfeat=collections.defaultdict(set,{k:set(v) for k,v in rules['features'].items()})\n"+s[b:]
a=s.index("ref=ROOT/'work/civ6-reference");b=s.index("(OUT/'schema.sql').write_text(schema)",a)+len("(OUT/'schema.sql').write_text(schema)")
s=s[:a]+"schema=(ROOT/'schema.sql').read_text()"+s[b:]
exec(compile(s,'lgm_generator','exec'))
