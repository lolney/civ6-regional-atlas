#!/usr/bin/env python3
"""Read-only Civ6Map structural and content validator (Python standard library only).
Not an engine emulator: loading, starts, disasters, AI and visuals require Civ VI.
"""
import argparse,collections,hashlib,json,math,pathlib,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent

def validate(path):
 errors=[];checks=[];warnings=[]
 def check(name,condition,detail=None):
  checks.append({'check':name,'pass':bool(condition),'detail':detail})
  if not condition:errors.append(name)
 c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
 d=json.loads((ROOT/'map_data.json').read_text())
 integrity=[r[0] for r in c.execute('PRAGMA integrity_check')]
 check('SQLite integrity',integrity==['ok'],integrity)
 check('SQLite foreign_key_check',not list(c.execute('PRAGMA foreign_key_check')))
 # Compare every table's column signature with a real WorldBuilder DB schema.
 reference=sqlite3.connect(':memory:');reference.executescript((ROOT/'schema.sql').read_text())
 tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 expected={r[0] for r in reference.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 check('WorldBuilder tables present',expected<=tables,{'expected':len(expected),'actual':len(tables)})
 sig=lambda db,t:[tuple(r[1:]) for r in db.execute('PRAGMA table_info("'+t+'")')]
 check('WorldBuilder column schema',all(sig(c,t)==sig(reference,t) for t in expected if t in tables))
 _,w,h,top,bottom,wx,wy,size=c.execute('SELECT * FROM Map').fetchone()
 check('Dimensions and Huge classification',w==80 and h==88 and size=='MAPSIZE_HUGE')
 check('Regional non-wrapping map',wx==0 and wy==0 and top>bottom)
 plots={r[0]:r[1:] for r in c.execute('SELECT * FROM Plots')}; n=w*h
 check('Dense complete zero-based plot IDs',set(plots)==set(range(n)),len(plots))
 rules=json.loads((ROOT/'rules.json').read_text()); resources={r[0]:r[1:] for r in c.execute('SELECT * FROM PlotResources')};features=dict(c.execute('SELECT * FROM PlotFeatures'))
 check('Known terrain and continent identifiers',all(t in rules['terrains'] and (not con or con in rules['continents']) for t,con,imp in plots.values()))
 check('Mountains are impassable; other terrain passable',all(imp==int(t.endswith('_MOUNTAIN')) for t,con,imp in plots.values()))
 badrefs={t:[r[0] for r in c.execute('SELECT ID FROM '+t) if r[0] not in plots] for t in ['PlotFeatures','PlotResources','PlotRivers','PlotCliffs','PlotImprovements']}
 check('Plot child rows reference valid plots',not any(badrefs.values()),badrefs)
 check('Legal feature terrains',all(f in rules['features'] and plots[i][0] in rules['features'][f] for i,f in features.items()))
 rr=rules['resources'];bad=[];spawn_mismatches=[];declared={e['plot']:e for e in d.get('resource_placement_exceptions',[])}
 for i,(r,count) in resources.items():
  f=features.get(i); valid=r in rr['terrains'] or r in rr['features']
  spawn_ok=(f in rr['features'].get(r,[])) if f else plots[i][0] in rr['terrains'].get(r,[])
  if not valid or count<1:bad.append(i)
  if not spawn_ok:spawn_mismatches.append(i)
 check('Native resource identifiers and positive quantities',not bad,bad)
 check('All procedural resource spawn exceptions explicitly documented',set(spawn_mismatches)==set(declared) and all(resources[i][0]=='RESOURCE_'+e['resource'] and plots[i][0]=='TERRAIN_'+e['terrain'] for i,e in declared.items()),declared)
 # Mine, plantation and oil well support resource-bearing passable land. Oil wells
 # explicitly support all flat/hill land terrains in the game's Improvements data.
 check('Authored deposits use passable improvement domains',all((e['resource']=='TURTLES' and plots[i][0]=='TERRAIN_COAST') or (e['resource'] in ['WINE','SILVER','OIL','MERCURY','COPPER','SALT','COFFEE','COTTON','OLIVES','JADE','DIAMONDS','DYES','FURS','INCENSE','SPICES','SUGAR','TOBACCO','TEA','SILK'] and not plots[i][2] and plots[i][0] not in ['TERRAIN_COAST','TERRAIN_OCEAN']) for i,e in declared.items()))
 check('All seven strategic resources represented',all('RESOURCE_'+r in {v[0] for v in resources.values()} for r in ['HORSES','IRON','NITER','COAL','OIL','ALUMINUM','URANIUM']))
 def neighbor(i,side):
  x,y=i%w,i//w
  a,b={'W':(x+1,y),'NW':(x+y%2,y-1),'NE':(x+y%2-1,y-1)}[side]
  return b*w+a if 0<=a<w and 0<=b<h else None
 def endpoints(i,side):
  # Integer lattice: horizontal half-tile units, vertical one-sixth-height units.
  x,y=i%w,i//w;cx=2*x+y%2;cy=3*y
  return {'W':((cx+1,cy+1),(cx+1,cy-1)), 'NW':((cx+1,cy-1),(cx,cy-2)), 'NE':((cx,cy-2),(cx-1,cy-1))}[side]
 edges=[];river_bad=[];outgoing=collections.defaultdict(list);undirected=collections.defaultdict(set)
 for i,ne,west,nw,ef,sef,swf in c.execute('SELECT * FROM PlotRivers'):
  for side,flag,flow,allowed in [('W',west,ef,(0,3)),('NW',nw,sef,(1,4)),('NE',ne,swf,(2,5))]:
   if flag not in [0,1] or (flag and flow not in allowed) or (not flag and flow!=-1):river_bad.append((i,side,'flag/direction mismatch'))
   if not flag:continue
   j=neighbor(i,side)
   if j is None or any(plots[k][0] in ['TERRAIN_COAST','TERRAIN_OCEAN'] for k in [i,j]):river_bad.append((i,side,'not between two land hexes'))
   a,b=endpoints(i,side)
   if flow in [0,1,2]:a,b=b,a
   outgoing[a].append(b);undirected[a].add(b);undirected[b].add(a);edges.append((i,side,flow,a,b))
 check('Legal river flags, directions and bank ownership',not river_bad,river_bad[:20])
 check('Unique owned river edges',len(edges)==len(set((e[0],e[1]) for e in edges)),len(edges))
 check('River flow converges without forked outflows',all(len(v)<=1 for v in outgoing.values()))
 state={}
 def visit(u):
  if state.get(u)==1:return False
  if state.get(u)==2:return True
  state[u]=1
  for v in outgoing[u]:
   if not visit(v):return False
  state[u]=2;return True
 check('No directed river cycles',all(visit(u) for u in list(outgoing)))
 # Flood-independent water connectivity: Golden Gate must link both Bay basins to open ocean.
 def all_neighbors(i):
  x,y=i%w,i//w
  for a,b in [(x-1,y),(x+1,y),(x+y%2-1,y-1),(x+y%2,y-1),(x+y%2-1,y+1),(x+y%2,y+1)]:
   if 0<=a<w and 0<=b<h:yield b*w+a
 water={i for i,(t,_,_) in plots.items() if t in ['TERRAIN_COAST','TERRAIN_OCEAN']};ocean={i for i in water if i%w==0};todo=list(ocean)
 while todo:
  i=todo.pop()
  for j in all_neighbors(i):
   if j in water and j not in ocean:ocean.add(j);todo.append(j)
 check('San Francisco and San Pablo Bays connect to Pacific',3859 in ocean and 4179 in ocean)
 attrs=dict(c.execute('SELECT * FROM MapAttributes'));deps=list(c.execute('SELECT ID FROM ModDependencies'))
 check('Gathering Storm ruleset and only intended dependency',attrs.get('Ruleset')=='RULESET_EXPANSION_2' and [r[0].lower() for r in deps]==['4873eb62-8ccc-4574-b784-dda455e74e68'])
 check('WorldBuilder map loader and self-packaging metadata',attrs.get('MapScript')=='WorldBuilderMap.lua' and dict(c.execute('SELECT * FROM MetaData')).get('IsMod')=='1' and ('WorldBuilder','WORLDBUILDER','File','[self]') in list(c.execute('SELECT * FROM ModSettings_Items')))
 check('No inherited scenario players, cities or units',all(c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0]==0 for t in ['Players','Cities','Units','StartPositions']))
 check('Tribal villages on free passable land',all(i in plots and not plots[i][2] and i not in water and i not in resources and i not in features and t=='IMPROVEMENT_GOODY_HUT' and owner==-1 for i,t,owner in c.execute('SELECT * FROM PlotImprovements')))
 d=json.loads((ROOT/'map_data.json').read_text())
 check('Preview terrain/feature/resource rows match native file',all(plots[t['id']][0]=='TERRAIN_'+t['terrain'] and features.get(t['id'],'')==('FEATURE_'+t['feature'] if t['feature'] else '') and resources.get(t['id'],('',0))==(('RESOURCE_'+t['resource'] if t['resource'] else ''),t['quantity']) for t in d['tiles']))
 check('Preview river edges match native file',set((r['plot'],r['side'],r['flow']) for r in d['rivers'])==set(e[:3] for e in edges))
 component={};cc=0
 for v in undirected:
  if v in component:continue
  todo=[v];component[v]=cc
  while todo:
   u=todo.pop()
   for z in undirected[u]:
    if z not in component:component[z]=cc;todo.append(z)
  cc+=1
 courses=collections.defaultdict(set)
 for r in d['rivers']:courses[r['name']].add(component[endpoints(r['plot'],r['side'])[0]])
 separate=[('Truckee','Sacramento'),('Truckee','American'),('Mad','Eel'),('Big','Noyo'),('Russian','Big'),('Los Angeles','San Gabriel'),('Sweetwater','Otay'),('Otay','Tijuana'),('San Luis Rey','Santa Margarita'),('Carson','Walker'),('Carson','Truckee'),('East Fork Carson','West Walker'),('New','Alamo')]
 check('Neighboring distinct watersheds remain separate',all(courses[a].isdisjoint(courses[b]) for a,b in separate),separate)

 # Landform regressions: test actual map connectivity, not only valid row syntax.
 def reach(graph,start):
  seen={start};todo=[start]
  while todo:
   u=todo.pop()
   for v in graph.get(u,()):
    if v not in seen:seen.add(v);todo.append(v)
  return seen
 land_graph={i:set(j for j in all_neighbors(i) if j not in water) for i in plots if i not in water}
 check('San Francisco Peninsula is attached to mainland',3938 in land_graph and 3700 in reach(land_graph,3938))
 for valley in d['notes'].get('valley_corridors',[]):
  ids=set(valley['tiles']);flat={i for i in ids if plots[i][0] in ['TERRAIN_GRASS','TERRAIN_PLAINS','TERRAIN_DESERT']}
  corridor={i:set(all_neighbors(i))&flat for i in flat}
  check(valley['name']+' floor is flat and continuously traversable',bool(ids) and flat==ids and ids<=reach(corridor,min(ids)),{'tiles':len(ids),'changed':len(valley['changes'])})
 water_comp={};water_groups=[]
 for i in water:
  if i in water_comp:continue
  group=reach({j:set(all_neighbors(j))&water for j in water},i);k=len(water_groups);water_groups.append(group)
  for j in group:water_comp[j]=k
 water_at=collections.defaultdict(set)
 for i in water:
  x,y=i%w,i//w;cx=2*x+y%2;cy=3*y
  for dx,dy in [(0,2),(1,1),(1,-1),(0,-2),(-1,-1),(-1,1)]:water_at[cx+dx,cy+dy].add(water_comp[i])
 def wet_graph(names):
  graph=collections.defaultdict(set)
  for r in d['rivers']:
   if r['name'] not in names:continue
   a,b=endpoints(r['plot'],r['side']);graph[a].add(b);graph[b].add(a)
  for v in list(graph):
   for k in water_at[v]:graph[v].add(('water',k));graph['water',k].add(v)
  return graph
 families={'Sacramento':{'Sacramento','American','Feather','North Fork American','North Yuba','S.  Fk.  American','North Fork Feather','Pit'},'San Joaquin':{'San Joaquin','Fresno Slough','Kings','Merced','Stanislaus','Tuolumne'}}
 pacific=('water',water_comp[3859])
 for name,names in families.items():
  connected=reach(wet_graph(names),pacific)
  trunk=[endpoints(r['plot'],r['side']) for r in d['rivers'] if r['name']==name]
  check(name+' main stem reaches Pacific through the Bay',bool(trunk) and all(a in connected and b in connected for a,b in trunk))
 mead=[t['id'] for t in d['tiles'] if t['lake']=='Mead']
 check('Lake Mead is one connected water body',bool(mead) and len({water_comp[i] for i in mead})==1,len(mead))
 colorado=wet_graph({'Colorado'});gulf=('water',water_comp[65]);connected=reach(colorado,gulf);unconnected=set(colorado)-connected;boundary_parts=[]
 while unconnected:
  component=reach(colorado,next(iter(unconnected)));unconnected-=component
  ends=[v for v in component if v[0]!='water' and len(colorado[v])==1]
  boundary_parts.append(ends)
 check('Colorado continuous through reservoirs to Gulf, except real crop exits',len(connected)>50 and all(ends and all(v[0]>=2*w-1 for v in ends) for ends in boundary_parts),{'connected_nodes':len(connected),'outside_crop_endpoints':boundary_parts})
 # Regional river/terrain requests, checked against the same native edge lattice.
 for name,names,target_lake in [('Walker',{'Walker','East Walker','West Walker'},'Walker'),('Carson',{'Carson','East Fork Carson','West Fork Carson'},'Lahontan Reservoir'),('New',{'New'},'Salton Sea'),('Alamo',{'Alamo'},'Salton Sea')]:
  graph=wet_graph(names);lake_ids=[t['id'] for t in d['tiles'] if t['lake']==target_lake]
  connected=reach(graph,('water',water_comp[lake_ids[0]])) if lake_ids else set()
  check(name+' river network is continuous to '+target_lake,bool(graph) and bool(lake_ids) and set(graph)<=connected,{'nodes':len(graph),'connected_nodes':len(connected)})
 tahoe=[t['id'] for t in d['tiles'] if t['lake']=='Tahoe'];tahoe_banks={j for i in tahoe for j in all_neighbors(i) if j not in water}
 check('Tahoe has no desert shoreline and Carson does not drain into it',bool(tahoe) and all(not plots[i][0].startswith('TERRAIN_DESERT') for i in tahoe_banks) and ('water',water_comp[tahoe[0]]) not in wet_graph({'Carson','East Fork Carson','West Fork Carson'}))
 massifs=[e['id'] for e in d['notes'].get('tahoe_terrain_corrections',[]) if e['after'].endswith('_MOUNTAIN')]
 check('Four mapped mountain cells west and southwest of Tahoe',len(set(massifs))==4 and all(plots[i][0].endswith('_MOUNTAIN') for i in massifs),massifs)
 imperial=[t['id'] for t in d['tiles'] if -116<t['lon']<-115.1 and 32.5<t['lat']<33.2 and features.get(t['id'],'').startswith('FEATURE_FLOODPLAINS')]
 check('Imperial Valley has connected agricultural floodplains',len(imperial)>=14 and set(imperial)<=reach({i:set(all_neighbors(i))&set(imperial) for i in imperial},imperial[0]),len(imperial))
 nevada_fp=[t['id'] for t in d['tiles'] if -120<t['lon']<-115 and 38.65<t['lat']<41.25 and 'Basin and Range' in t['ecoregion'] and features.get(t['id'],'').startswith('FEATURE_FLOODPLAINS')]
 check('Northern Nevada agricultural valleys have riverbank floodplains',len(nevada_fp)>=35,len(nevada_fp))
 check('Entire sourced California polygon fits the map',d['stats']['california_polygon_contained'])
 check('Every retained river segment routed',not d['notes']['unrouted_segments'])
 check('Median river-edge displacement under half a hex',d['stats']['median_river_offset_km']<d['pitch_km']/2,d['stats']['median_river_offset_km'])
 check('Maximum river-edge displacement under 1.5 hexes',d['stats']['max_river_offset_km']<d['pitch_km']*1.5,d['stats']['max_river_offset_km'])
 check('Twelve generic balanced suggestions',len(d['starts'])==12 and all(s['name'].startswith('Start ') and s.get('metrics',{}).get('fresh_water') for s in d['starts']))
 check('Suggested starts have expansion space and separation',all(s.get('metrics',{}).get('passable_ring3',0)>=25 and s.get('metrics',{}).get('nearest_start_hexes',0)>=12 for s in d['starts']))
 check('Suggested starts passable and on land',all(s['id'] not in water and not plots[s['id']][2] for s in d['starts']))
 check('Suggested starts are at least six hexes inside every edge',all(6<=s['id']%w<w-6 and 6<=s['id']//w<h-6 for s in d['starts']))
 bank={e[0] for e in edges}|{neighbor(e[0],e[1]) for e in edges}
 fps={i for i,f in features.items() if f.startswith('FEATURE_FLOODPLAINS')}
 check('Floodplains are flat and touch an actual river edge',bool(fps) and fps<=bank and all(plots[i][0] in ['TERRAIN_GRASS','TERRAIN_PLAINS','TERRAIN_DESERT'] for i in fps),len(fps))
 seen=set();sizes=[]
 for i in fps:
  if i in seen:continue
  todo=[i];seen.add(i);group=[]
  while todo:
   u=todo.pop();group.append(u)
   for j in all_neighbors(u):
    if j in fps and j not in seen:seen.add(j);todo.append(j)
  sizes.append(len(group))
 check('Floodplain groups have at least three connected tiles',all(x>=3 for x in sizes),sizes)
 check('Named resource districts actually present in native map',bool(d.get('iconic_deposits')) and all(resources.get(i,('',0))[0]=='RESOURCE_'+a['resource'] and d['tiles'][i].get('deposit',{}).get('name')==a['name'] and d['tiles'][i]['deposit']['distance_km']<=a['radius_km'] for a in d.get('iconic_deposits',[]) for i in a['plots']))
 check('Gold and Gold Country proxies omitted as requested',all(not t.get('deposit',{}).get('proxy') for t in d['tiles']) and not any(r[0]=='RESOURCE_GOLD' for r in resources.values()))
 catalog=json.loads((ROOT/'resource_catalog.json').read_text())
 catalog_ids={r['id'] for r in catalog['resources']}
 expected_catalog={'BANANAS','CATTLE','COPPER','CRABS','DEER','FISH','RICE','SHEEP','STONE','WHEAT','AMBER','CITRUS','COCOA','COFFEE','COTTON','DIAMONDS','DYES','FURS','GYPSUM','INCENSE','IVORY','JADE','MARBLE','MERCURY','OLIVES','PEARLS','SALT','SILK','SILVER','SPICES','SUGAR','TEA','TOBACCO','TRUFFLES','TURTLES','WHALES','WINE','ALUMINUM','COAL','HORSES','IRON','NITER','OIL','URANIUM'}
 check('Inspector catalog includes all 44 standard Gathering Storm map resources',catalog_ids==expected_catalog and len(catalog['resources'])==44 and d.get('resource_catalog')==catalog)
 native_counts=collections.Counter(r.removeprefix('RESOURCE_') for r,count in resources.values())
 preview_counts=collections.Counter(t['resource'] for t in d['tiles'] if t['resource'])
 check('Every resource count agrees between native map and inspector',native_counts==preview_counts and set(native_counts)<=catalog_ids and sum(native_counts.values())==d['stats']['resource_tiles'],{r:native_counts[r] for r in sorted(catalog_ids)})
 salts=[a for a in d['iconic_deposits'] if a['resource']=='SALT']
 check('Salt is concentrated in named flat western basins',len(salts)>=15 and any(a['name']=='Bonneville Salt Flats' and len(a['plots'])>=5 for a in salts) and all(plots[i][0] in ['TERRAIN_DESERT','TERRAIN_PLAINS','TERRAIN_GRASS'] and i not in features for a in salts for i in a['plots']),{'districts':len(salts),'anchored_salt_tiles':sum(len(a['plots']) for a in salts),'total_salt_tiles':native_counts['SALT']})
 basin=[t for t in d['tiles'] if 'Basin and Range' in t['ecoregion'] and t.get('local_relief',999)<180 and not t['terrain'].endswith('MOUNTAIN')]
 check('Low-relief Basin and Range valley centers remain flat',bool(basin) and all(not t['terrain'].endswith('HILLS') for t in basin),len(basin))
 if declared:warnings.append(f'{len(declared)} explicitly authored resource placements lie outside procedural spawn filters; native identifiers and broad improvement domains were checked, but the map still needs engine testing.')
 density=d['notes']['southern_coastal_river_density']
 check('Southern coastal river edges reduced by about half',.45<=density['after_edges']/density['before_edges']<=.55,{'before':density['before_edges'],'after':density['after_edges']})
 for name in ['Santa Ynez','Santa Clara','Los Angeles','Santa Ana','San Luis Rey','San Diego','Tijuana']:
  g=wet_graph({name});connected=reach(g,pacific)
  check(name+' retained lower course remains connected to Pacific',len(g)>1 and set(g)<=connected)
 check('Lassen Peak is a mountain',plots[d['notes']['lassen_mountain']][0].endswith('_MOUNTAIN'))
 big_sur=[t for t in d['tiles'] if -122<t['lon']<-121.25 and 35.8<t['lat']<36.6 and t['feature']=='FOREST']
 check('Big Sur contains mapped forest mosaic',len(big_sur)>=7,{'forest_tiles':len(big_sur)})
 check('Forest reference percentages bounded',all(t.get('forest_reference_percent') is None or 0<=t['forest_reference_percent']<=100 for t in d['tiles']))
 warnings.extend(['Engine loading, automatic player placement, AI, dams and disasters have not been tested.', 'Floodplain features are present, but flood events and dam eligibility require in-game testing; static SQLite checks cannot validate engine river metadata.', 'Source geometry is simplified at 15.5 km per hex. Tiny islands, lakes and Bay narrows are enlarged; intermittent channels are shown only in the reference overlay.', 'Coarse-grid flow is oriented toward low drainage endpoints; it is not a hydraulic simulation.'])
 c.close();return {'status':'PASS' if not errors else 'FAIL','file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'engine_tested':False,'checks_passed':sum(c['pass'] for c in checks),'checks_total':len(checks),'errors':errors,'checks':checks,'warnings':warnings,'stats':d['stats']}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('map',nargs='?',type=pathlib.Path,default=ROOT/'California_GatheringStorm.Civ6Map');p.add_argument('--report',type=pathlib.Path);a=p.parse_args()
 try:r=validate(a.map)
 except Exception as e:print(f'Validation failed: {e}',file=sys.stderr);sys.exit(2)
 text=json.dumps(r,indent=2)
 if a.report:a.report.write_text(text+'\n')
 print(f"{r['status']}: {r['checks_passed']}/{r['checks_total']} checks. Engine tested: no.")
 for e in r['errors']:print('FAIL:',e)
 sys.exit(0 if r['status']=='PASS' else 1)
