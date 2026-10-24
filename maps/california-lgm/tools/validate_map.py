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
 check('Modern Bay floor is exposed',3859 not in water and 4179 not in water)
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
 pacific=('water',water_comp[0])
 for name,names in {'Sacramento':{'Sacramento','American','Feather','Pit'},'San Joaquin':{'San Joaquin','Kings','Fresno Slough','Sacramento'}}.items():
  g=wet_graph(names);conn=reach(g,pacific);trunk=[endpoints(r['plot'],r['side']) for r in d['rivers'] if r['name']==name]
  check(name+' reaches lowered Pacific coast',bool(trunk) and all(a in conn and b in conn for a,b in trunk))
 check('Unique LGM identity',dict(c.execute('SELECT * FROM MetaData'))['ID']=='CACA2100-2100-4210-8210-000000000021')
 check('All glacier proxies are empty impassable snow mountains',sum(bool(t.get('glacier')) for t in d['tiles'])>40 and all(t['terrain']=='SNOW_MOUNTAIN' and not t['feature'] and not t['resource'] and not t['goody'] for t in d['tiles'] if t.get('glacier')))
 check('No continental ice sheet within this southern crop',d['notes']['continental_ice_sheet_hexes']==0)
 check('Modern reservoirs and Salton Sea removed',not {t['lake'] for t in d['tiles']} & {'Mead','Mohave','Havasu','Shasta','Oroville','Millerton','Trinity','Almanor','Lahontan Reservoir','Salton Sea'})
 for name in ['Bonneville','Lahontan — western basins','Lahontan — Carson/Humboldt','Russell (Mono)','Owens','Searles','Manly']:
  ids={t['id'] for t in d['tiles'] if t['lake']==name}
  check(name+' represented as water',bool(ids) and ids<=water,len(ids))
  check(name+' is contiguous',bool(ids) and len({water_comp[i] for i in ids})==1)
 santarosae=[min(d['tiles'],key=lambda t:(t['lon']-lon)**2+(t['lat']-lat)**2)['id'] for lon,lat in [(-120.42,34.03),(-120.12,33.97),(-119.78,34.02),(-119.39,34.01)]]
 check('Santarosae islands connected to each other',all(i in land_graph and i in reach(land_graph,santarosae[0]) for i in santarosae),santarosae)
 check('Santarosae remains separate from mainland',santarosae[0] not in reach(land_graph,3938))
 bank={e[0] for e in edges}|{neighbor(e[0],e[1]) for e in edges};fps={i for i,f in features.items() if f.startswith('FEATURE_FLOODPLAINS')}
 check('Floodplains touch rivers and remain flat',fps<=bank and all(plots[i][0] in ['TERRAIN_GRASS','TERRAIN_PLAINS','TERRAIN_DESERT'] for i in fps))
 check('Twelve passable freshwater start suggestions',len(d['starts'])==12 and all(not plots[s['id']][2] and s['id'] not in water and s['metrics']['fresh_water'] for s in d['starts']))
 check('Start spacing and edge margin',all(s['metrics']['nearest_start_hexes']>=12 and 6<=s['id']%w<w-6 and 6<=s['id']//w<h-6 for s in d['starts']))
 check('Start food and expansion space',all(s['metrics']['food_resources_ring3']>=3 and s['metrics']['passable_ring3']>=25 for s in d['starts']))
 check('No omitted routed source segments',not d['notes']['unrouted_segments'],d['notes']['unrouted_segments'])
 check('Marine fauna excluded from inland lakes',all(not t['lake'] or t['resource'] not in ['WHALES','CRABS'] for t in d['tiles']))
 check('No warm water sea ice mistakenly used as land glaciers',not any(t['feature']=='ICE' for t in d['tiles']))
 warnings=['Paleogeography is an approximate 21 ka scenario, not a dated high-resolution reconstruction. See RECONSTRUCTION.md.', 'Civ VI uses snow mountains as a land-glacier proxy. Large lake water bodies may use marine gameplay behavior.', 'Engine loading and gameplay have not been tested for this alternate map.']
 c.close();return {'status':'PASS' if not errors else 'FAIL','file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'engine_tested':False,'checks_passed':sum(x['pass'] for x in checks),'checks_total':len(checks),'errors':errors,'checks':checks,'warnings':warnings,'stats':d['stats']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('map',nargs='?',type=pathlib.Path,default=ROOT/'California_LastGlacialMaximum.Civ6Map');p.add_argument('--report',type=pathlib.Path);a=p.parse_args()
 try:r=validate(a.map)
 except Exception as e:print(f'Validation failed: {e}',file=sys.stderr);sys.exit(2)
 text=json.dumps(r,indent=2)
 if a.report:a.report.write_text(text+'\n')
 print(f"{r['status']}: {r['checks_passed']}/{r['checks_total']} checks. Engine tested: no.")
 for e in r['errors']:print('FAIL:',e)
 sys.exit(0 if r['status']=='PASS' else 1)
