from pathlib import Path
import json,sqlite3,collections,shutil,re
root=Path(__file__).resolve().parent.parent;d=json.loads((root/'map_data.json').read_text());modern=json.loads((root/'modern_reference.json').read_text());rules=json.loads((root/'rules.json').read_text())
# Preserve surviving geologic deposits; agricultural resources remain gameplay.
for t in d['tiles']:
 m=modern['tiles'][t['id']]
 if t['lake'] and t['resource'] in ['WHALES','CRABS']:t['resource']='FISH'
 if t['glacier']:t['resource']='';t['quantity']=0;t['goody']=False
 if t['resource'] in ['CITRUS','RICE','WINE'] and t['terrain'].startswith(('TUNDRA','SNOW')):t['resource']='';t['quantity']=0
 if m.get('deposit') and m['resource'] in ['SILVER','COPPER','MERCURY','OIL','SALT','JADE','DIAMONDS']:
  r='RESOURCE_'+m['resource'];f='FEATURE_'+t['feature'] if t['feature'] else None
  valid=f in rules['resources']['features'].get(r,[]) if f else 'TERRAIN_'+t['terrain'] in rules['resources']['terrains'].get(r,[])
  if valid and not t['glacier']:
   t['resource']=m['resource'];t['quantity']=m['quantity'];t['goody']=False;t['deposit']=m['deposit']
# Extra northern fur resources (native habitat proxy), no cultivated cotton zones.
for t in d['tiles']:
 if t['feature']=='FOREST' and not t['resource'] and t['id']%17==0:t['resource']='FURS';t['quantity']=1;t['goody']=False
# Cap abundant strategic/luxury rolls and retain wetland fringes.
import random
rr=random.Random(21000)
for resource,cap in {'URANIUM':28,'NITER':44,'OIL':28,'WINE':17,'MERCURY':4,'ALUMINUM':39,'COAL':40,'IRON':63,'DEER':175}.items():
 ids=[t['id'] for t in d['tiles'] if t['resource']==resource]
 removable=[i for i in ids if not d['tiles'][i].get('deposit')];rr.shuffle(removable)
 for i in removable[:max(0,len(ids)-cap)]:d['tiles'][i]['resource']='';d['tiles'][i]['quantity']=0
for t in d['tiles']:
 i=t['id'];x,y=i%80,i//80
 adj=[b*80+a for a,b in [(x-1,y),(x+1,y),(x+y%2-1,y-1),(x+y%2,y-1),(x+y%2-1,y+1),(x+y%2,y+1)] if 0<=a<80 and 0<=b<88]
 if t['terrain']=='PLAINS' and not t['feature'] and not t['resource'] and any(d['tiles'][j]['lake'] for j in adj) and i%4==0:
  t['terrain']='GRASS';t['feature']='MARSH';t['goody']=False;t['paleobiome']='Pluvial lake-margin wetland'
# Remove modern audit claims that do not describe this landscape.
d['notes']={k:v for k,v in d['notes'].items() if k in ['epoch_ka','sea_level_m','continental_ice_sheet_hexes','paleo_lakes','unrouted_segments','cycle_edges_removed','river_components','river_gap_repairs','river_endpoint_adjustments']}
d['notes']['resource_policy']='Civ gameplay resources, not a reconstruction of domestication or prehistoric industry. Submerged deposits removed; surviving legal geologic anchors retained. No modern farms or fixed cities.'
d['stats'].update(resource_tiles=sum(bool(t['resource']) for t in d['tiles']),glacier_hexes=sum(bool(t['glacier']) for t in d['tiles']),exposed_seabed_hexes=sum(t['terrain'] not in ['COAST','OCEAN'] and m['terrain'] in ['COAST','OCEAN'] and not m['lake'] for t,m in zip(d['tiles'],modern['tiles'])),pluvial_lake_hexes=sum(bool(t['lake']) for t in d['tiles']))
d['iconic_deposits']=[];d['resource_placement_exceptions']=[]
(root/'map_data.json').write_text(json.dumps(d,separators=(',',':')))
c=sqlite3.connect(root/'California_GatheringStorm.Civ6Map');tables=[x[0] for x in c.execute("select name from sqlite_master where type='table'")];meta={t:list(c.execute('select * from "'+t+'"')) for t in tables if t not in ['Plots','PlotFeatures','PlotResources','PlotRivers','PlotImprovements']};c.close();(root/'native_metadata.json').write_text(json.dumps(meta,indent=2))
# Snapshot of modern map is embedded for self-contained comparisons.
(root/'modern_reference.json').write_text(json.dumps(modern,separators=(',',':')))
s=(root/'tools/modern_viewer_template.html').read_text()
s=s.replace('<h1>California</h1>','<h1>California · Ice Age</h1>').replace('Civilization VI · Gathering Storm · 80 × 88 hexes · North up','Gathering Storm · ~21,000 years ago · sea level −125 m')
s=s.replace('<h2>Map layers</h2>','<h2>Compare landscapes</h2><select id="epoch" aria-label="Landscape version"><option value="lgm">Last Glacial Maximum (~21 ka)</option><option value="modern">Modern reference</option></select><p class="note">Same grid and camera. Approximate reconstruction; see uncertainty notes below.</p><h2>Map layers</h2>')
s=s.replace('<option value="elevation">Measured elevation</option>','<option value="elevation">Modern measured elevation</option><option value="changes">Changes from modern</option>')
s=s.replace("'use strict';const D=JSON.parse(document.getElementById('data').textContent),$=", "'use strict';const LGM=JSON.parse(document.getElementById('data').textContent),MODERN=JSON.parse(document.getElementById('modernData').textContent),params=new URLSearchParams(location.search),D=params.get('epoch')==='modern'?MODERN:LGM,$=")
s=s.replace('<script id="data"', '<script id="modernData" type="application/json">__MODERN_DATA__</script><script id="data"')
s=s.replace("$('legend').innerHTML=", "$('epoch').value=params.get('epoch')==='modern'?'modern':'lgm';$('epoch').onchange=()=>{const q=new URLSearchParams({epoch:$('epoch').value,cx:(cw/2-ox)/scale,cy:(ch/2-oy)/scale,zoom:scale});location.search=q.toString()};$('legend').innerHTML=")
s=s.replace(".filter(([k])=>k!=='SNOW')",'')
s=s.replace("const places=[", "const places=[['Bonneville',-113.1,40.5],['Lahontan',-119.2,40.4],['Lake Russell',-119,38],['Lake Manly',-116.85,36.3],['Santarosae',-120.05,34.02],")
s=s.replace("[['Lassen Peak'", "[['Exposed San Francisco Bay',-122.3,37.85],['Santarosae',-120.05,34.02],['Bonneville',-113.2,40.6],['Lahontan western basins',-119.45,40.45],['Carson pluvial basin',-118.65,39.7],['Russell (Mono)',-119.0,38.0],['Owens pluvial lake',-118,36.45],['Lake Manly',-116.85,36.3],['Tioga icefield / Yosemite',-119.4,37.9],['Mojave woodland',-115.7,35.5],['Lassen Peak'")
s=s.replace("ctx.fillStyle=$('mode').value==='elevation'?elevationColor(t.elevation):colors[base(t.terrain)]", "ctx.fillStyle=$('mode').value==='changes'?changeColor(t.id):$('mode').value==='elevation'?elevationColor(t.elevation):colors[base(t.terrain)]")
s=s.replace('function elevationColor(z)',"function changeColor(id){const a=LGM.tiles[id],b=MODERN.tiles[id],water=t=>['COAST','OCEAN'].includes(t.terrain);if(a.glacier)return '#c4f4ff';if(water(a)&&!water(b))return '#358ddd';if(!water(a)&&water(b))return '#e5b75c';if(a.terrain!==b.terrain||a.feature!==b.feature)return '#9d80b9';return '#42545c'}\nfunction elevationColor(z)")
s=s.replace('<dt>Terrain</dt>',"${t.paleobiome?`<dt>LGM biome</dt><dd>${t.paleobiome}</dd><dt>Modern terrain</dt><dd>${pretty(t.modern_terrain)}</dd>${t.glacier?`<dt>Glacier evidence</dt><dd>${t.glacier.basis} (${t.glacier.confidence} confidence)</dd>`:''}`:''}<dt>Terrain</dt>")
s=s.replace('function resize(){','let restoreCamera=true;function resize(){').replace('canvas.height=ch*dpr;fit();}','canvas.height=ch*dpr;fit();if(restoreCamera&&params.has("zoom")){scale=Number(params.get("zoom"));ox=cw/2-Number(params.get("cx"))*scale;oy=ch/2-Number(params.get("cy"))*scale;draw()}restoreCamera=false;}')
a=s.index('<section><h2>About this map</h2>');b=s.index('</footer>',a)+len('</footer>')
s=s[:a]+'''<section><h2>About this reconstruction</h2><div id="stats"></div><p class="note">Approximate 21 ka scenario. Sea level −125 m; connected basin fills use stated lake-level estimates. Modern reservoirs and the modern Salton Sea are absent. Continental ice sheets lie north of the map.</p><p class="note">Land glaciers use impassable Snow Mountain terrain: Civ VI has no native land-glacier feature. Yosemite uses USGS Tioga polygons; other icefields are generalized. Resources and starts serve Civ gameplay, not prehistoric agriculture or settlement.</p><p class="note">Change colors: pale cyan = glacier; blue = inundated land; gold = exposed waterbed; purple = changed biome/terrain. Measured elevations use the modern datum. City names and state boundaries are orientation aids.</p><p><a href="RECONSTRUCTION.md">Methods, lake levels and uncertainty</a> · <a href="validation_report.json">Validation</a> · <a href="README.md">Install</a></p></section><footer>USGS / NPS paleogeography; USGS Tioga ice polygons; modern terrain/bathymetry and NHD drainage generalized to 15.5 km hexes. Source overlay combines modern reference linework with explicitly inferred shelf extensions. <a href="SOURCES.md">Sources</a>. Offline comparison included.</footer>'''+s[b:]
s=s.replace("$('epoch').value=params.get('epoch')==='modern'?'modern':'lgm';","$('epoch').value=params.get('epoch')==='modern'?'modern':'lgm';document.querySelector('header p').textContent=D===MODERN?'Modern reference · Gathering Storm · same 80 × 88 grid':'Gathering Storm · ~21,000 years ago · sea level −125 m';")
s=s.replace('Imperial Valley agriculture','Salton Trough (modern agriculture location)').replace('Colorado River / Lake Mead','Colorado River / former Mead basin').replace('Colorado River / Gulf mouth','Colorado River / southern crop boundary').replace('Carson River / Fallon agriculture','Carson River / Fallon basin').replace('Humboldt River / Lovelock agriculture','Humboldt River / Lovelock basin')
s=(root/'tools/lgm_viewer_template.html').read_text()
(root/'tools/viewer_template.html').write_text(s.replace('__MODERN_DATA__',json.dumps(modern,separators=(',',':'))))
print('Finalized LGM metadata and comparison template')
