#!/usr/bin/env python3
"""Add researched missing resources after place_iconic_resources.py, before balance_starts.py.
Standard library only. Terrain is preserved. Run only once per fresh generation.
"""
import json,pathlib,math,collections,sqlite3
ROOT=pathlib.Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'map_data.json').read_text());T=D['tiles'];rules=json.loads((ROOT/'resource_rules.json').read_text())
# Conservative expansion placement facts: olives on grass/plains; turtles spawn on reef.
rules['terrains']['RESOURCE_OLIVES']=['TERRAIN_GRASS','TERRAIN_GRASS_HILLS','TERRAIN_PLAINS','TERRAIN_PLAINS_HILLS']
rules['features']['RESOURCE_TURTLES']=['FEATURE_REEF']
(ROOT/'resource_rules.json').write_text(json.dumps(rules,indent=2)+'\n')
vr=json.loads((ROOT/'rules.json').read_text());vr['resources']=rules;(ROOT/'rules.json').write_text(json.dumps(vr,indent=2)+'\n')
anchors=[]
def add(name,res,lon,lat,count=1,radius=25,kind='land',note=''):
 anchors.append(dict(name=name,resource=res,lon=lon,lat=lat,count=count,radius_km=radius,proxy='',sea=kind=='sea',kind=kind,note=note))
for name,x,y,n in [('Kings County cotton',-119.65,36.12,4),('Fresno County cotton',-120.21,36.53,4),('Merced County cotton',-120.73,37.03,3),('Tulare County cotton',-119.40,36.20,2),('Imperial Valley cotton',-115.53,32.91,4),('Palo Verde Valley cotton',-114.63,33.61,2)]:add(name,'COTTON',x,y,n,30,'flat')
for name,x,y,n in [('Klamath fur-bearing wildlife',-123.55,41.50,3),('Trinity fur-bearing wildlife',-123.10,40.8,3),('Eel River fur-bearing wildlife',-123.7,40.25,2),('Russian River fur-bearing wildlife',-122.93,38.72,2),('Upper Sacramento fur-bearing wildlife',-122.3,40.55,2),('Northern Sierra fur-bearing wildlife',-120.38,39.6,3),('Southern Oregon fur-bearing wildlife',-122.25,42.0,3)]:add(name,'FURS',x,y,n,32,'forest',note='Beaver, otter and forest furbearers; historical habitat and fur trade, not a modern trapping forecast.')
for name,x,y,n in [('Corning / Tehama olive groves',-122.16,39.93,3),('Orland / Glenn olive groves',-122.19,39.75,2),('Yolo County olive groves',-121.95,38.71,2),('Lindsay / Tulare olive groves',-119.09,36.20,2),('San Joaquin County olive groves',-121.22,37.91,1)]:add(name,'OLIVES',x,y,n,28,'flat')
add('Goleta / Santa Barbara coffee','COFFEE',-119.91,34.45,1,20,note='Small documented commercial coffee plantings; one tile is a scale exaggeration.')
add('Jade Cove / Big Sur nephrite','JADE',-121.47,35.91,1,23,note='Coastal nephrite occurrence; represented on the adjacent land hex.')
add('Cherokee / Oroville placer diamonds','DIAMONDS',-121.54,39.65,1,24,note='Documented rare placer diamonds; not a large diamond field and not a gold substitute.')
for name,x,y in [('North Coast woodland plant dyes',-123.6,40.3),('Mendocino woodland plant dyes',-123.35,39.3),('Sierra foothill woodland plant dyes',-120.6,38.45)]:add(name,'DYES',x,y,1,30,'forest',note='Native plant pigments and tannins; resource-category abstraction.')
for name,x,y in [('Santa Lucia Range California bay leaves',-121.35,36.20),('Santa Cruz Mountains bay leaves',-122.07,37.2),('North Coast California bay leaves',-123.3,39.9)]:add(name,'SPICES',x,y,1,25,'forest',note='California bay laurel seasoning; not tropical pepper cultivation.')
add('Imperial Valley sugar beets','SUGAR',-115.55,32.91,4,30,'floodplain',note='Sugar represents documented sugar-beet farming, not sugar cane.')
for name,x,y in [('North Coast native tobacco',-123.35,40.65),('Sierra foothills native tobacco',-120.6,38.1),('Southern California native tobacco',-117.0,33.3)]:add(name,'TOBACCO',x,y,1,30,note='Native Nicotiana habitat; not a modern commercial tobacco belt.')
for name,x,y in [('Coachella brittlebush resin',-116.18,33.7),('Lower Colorado brittlebush resin',-114.7,34.6),('Mojave brittlebush resin',-115.9,34.4)]:add(name,'INCENSE',x,y,1,28,'flat',note='Incense abstracts aromatic brittlebush resin (incienso), not frankincense trees.')
add('San Diego coastal green turtles','TURTLES',-117.20,32.72,1,22,'sea',note='Documented green-turtle coastal habitat. Authored on coast without a tropical coral-reef feature.')
add('Wakamatsu historic tea colony','TEA',-120.89,38.76,1,24,note='Small historical tea cultivation at the 1869–1871 Wakamatsu colony; a historical reference, not a modern tea district.')
add('Wakamatsu historic silk colony','SILK',-120.89,38.76,1,24,'forest',note='Small historical sericulture at the 1869–1871 Wakamatsu colony; not a modern silk industry.')
def km(t,a):return math.hypot((t['lon']-a['lon'])*111.32*math.cos(math.radians(a['lat'])),(t['lat']-a['lat'])*111.32)
def spawn_ok(t,r):
 k='RESOURCE_'+r
 return ('FEATURE_'+t['feature'] in rules['features'].get(k,[])) if t['feature'] else ('TERRAIN_'+t['terrain'] in rules['terrains'].get(k,[]))
def usable(t,a):
 if t.get('deposit') or 'MOUNTAIN' in t['terrain']:return False
 if a['kind']=='sea':return t['terrain']=='COAST' and not t['lake']
 if t['terrain'] in ['COAST','OCEAN']:return False
 if a['kind']=='forest':return t['feature']=='FOREST'
 if a['kind']=='flat' and ('HILLS' in t['terrain'] or t['feature']=='FOREST'):return False
 if a['kind']=='floodplain':return t['feature'].startswith('FLOODPLAINS')
 return True
for a in anchors:
 candidates=[t for t in T if usable(t,a) and km(t,a)<=a['radius_km']]
 candidates.sort(key=lambda t:km(t,a)+(0 if spawn_ok(t,a['resource']) else 8)+(7 if t['resource'] else 0))
 if len(candidates)<a['count']:raise RuntimeError(f"Insufficient plots: {a['name']}: {len(candidates)} / {a['count']}")
 a['plots']=[]
 for t in candidates[:a['count']]:
  t.update(resource=a['resource'],quantity=1,goody=False,deposit={'name':a['name'],'resource':a['resource'],'proxy':'','distance_km':round(km(t,a),2),'anchor_lon':a['lon'],'anchor_lat':a['lat'],'note':a['note']})
  a['plots'].append(t['id'])
D['iconic_deposits'].extend(anchors)
# Recompute declarations, since a new crop can replace an ordinary generated resource.
D['resource_placement_exceptions']=[dict(plot=t['id'],resource=t['resource'],terrain=t['terrain'],feature=t['feature'],reason='Authored geographic resource; outside procedural spawn filters. '+t.get('deposit',{}).get('name','')) for t in T if t['resource'] and not spawn_ok(t,t['resource'])]
D['stats'].update(resource_tiles=sum(bool(t['resource']) for t in T),goody_huts=sum(t['goody'] for t in T),iconic_resource_tiles=sum(bool(t.get('deposit')) for t in T))
D['notes']['resource_method']+=' Researched additions include cotton, furs, olives, coffee, jade, diamonds, plant dyes, bay-leaf spices, beet sugar, native tobacco, aromatic resin, coastal turtles and the historic Wakamatsu tea/silk colony. Their interpretation and remaining absences are documented in RESOURCE_AUDIT.md.'
(ROOT/'map_data.json').write_text(json.dumps(D,separators=(',',':')))
c=sqlite3.connect(ROOT/'California_GatheringStorm.Civ6Map');c.execute('DELETE FROM PlotResources');c.executemany('INSERT INTO PlotResources VALUES(?,?,?)',[(t['id'],'RESOURCE_'+t['resource'],t['quantity']) for t in T if t['resource']]);c.execute('DELETE FROM PlotImprovements');c.executemany('INSERT INTO PlotImprovements VALUES(?,?,?)',[(t['id'],'IMPROVEMENT_GOODY_HUT',-1) for t in T if t['goody']]);c.commit();c.close()
print(json.dumps({'added_districts':len(anchors),'resource_counts':dict(collections.Counter(t['resource'] for t in T if t['resource']))},indent=2))
