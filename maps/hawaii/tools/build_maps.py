#!/usr/bin/env python3
"""Rebuild both native Hawaii maps and the comparison inspector; Python 3 stdlib only.
The included source_data/grid_inputs.json preserves the measured, sampled inputs.
"""
from pathlib import Path
import json,math,copy,collections,heapq,random,sqlite3,uuid,csv
ROOT=Path(__file__).resolve().parent.parent
S=json.loads((ROOT/'source_data/grid_inputs.json').read_text());W,H=S['width'],S['height'];N=W*H;P=S['pitch_km'];SQ=math.sqrt(3)
RULES=json.loads((ROOT/'rules.json').read_text());RR=json.loads((ROOT/'resource_rules.json').read_text());CAT=json.loads((ROOT/'resource_catalog.json').read_text())
xy=[(i%W+.5*((i//W)%2),i//W*SQ/2) for i in range(N)]
nb=[[] for _ in range(N)]
for i in range(N):
 x,y=i%W,i//W
 for xx,yy in [(x-1,y),(x+1,y),(x+y%2-1,y-1),(x+y%2,y-1),(x+y%2-1,y+1),(x+y%2,y+1)]:
  if 0<=xx<W and 0<=yy<H:nb[i].append(yy*W+xx)
def dist(a,b):return math.dist(xy[a],xy[b])
def hexdist(a,b):
 def cube(i):
  y=i//W;q=i%W-(y-y%2)//2;return q,y,-q-y
 return max(abs(x-y) for x,y in zip(cube(a),cube(b)))
def rings(i,n):
 seen={i};q=[i]
 for _ in range(n):q=[v for u in q for v in nb[u] if v not in seen and not seen.add(v)]
 return seen
def nearest(lon,lat,ids=None):return min(range(N) if ids is None else ids,key=lambda i:((S['tiles'][i]['lon']-lon)*math.cos(math.radians(lat)))**2+(S['tiles'][i]['lat']-lat)**2)
def components(mask):
 groups=[];seen=set()
 for i in sorted(mask):
  if i in seen:continue
  found={i};seen.add(i);q=[i]
  for u in q:
   for v in nb[u]:
    if v in mask and v not in seen:seen.add(v);found.add(v);q.append(v)
  groups.append(found)
 return groups
# Integer hex vertices guarantee exact shared corners; each native edge stored once.
E=[];edgepairs={};vpos={};vt=collections.defaultdict(set)
for i in range(N):
 x,y=i%W,i//W;cx=2*x+y%2;cy=3*y
 vs=[(cx+dx,cy+dy) for dx,dy in [(0,2),(1,1),(1,-1),(0,-2),(-1,-1),(-1,1)]]
 for v in vs:vpos[v]=(v[0]/2,v[1]/(2*SQ));vt[v].add(i)
 for k in range(6):edgepairs.setdefault(tuple(sorted([vs[k],vs[(k+1)%6]])),[]).append((i,k))
for (u,v),owners in edgepairs.items():
 if len(owners)!=2:continue
 i,k=next((i,k) for i,k in owners if k in [1,2,3]);E.append({'u':u,'v':v,'plot':i,'side':{1:'W',2:'NW',3:'NE'}[k],'tiles':[o[0] for o in owners]})
def pointline(p,pts):
 best=1e9
 for a,b in zip(pts,pts[1:]):
  dx,dy=b[0]-a[0],b[1]-a[1];f=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy or 1)));best=min(best,math.dist(p,(a[0]+f*dx,a[1]+f*dy)))
 return best
SUMMITS=[('Mauna Kea',-155.468,19.821,False),('Mauna Loa',-155.608,19.475,True),('Kīlauea',-155.287,19.421,True),('Haleakalā',-156.253,20.709,True),('Hualālai',-155.865,19.692,True),('Kohala',-155.717,20.087,False),('West Maui',-156.587,20.893,False),('Waiʻaleʻale',-159.500,22.071,False),('Koʻolau',-157.820,21.414,False),('Waiʻanae',-158.148,21.507,False),('East Molokaʻi',-156.878,21.122,False)]
# Shorter streams remain in the source overlay; a river cannot be smaller than one native edge.
PRIORITY=['Wailuku River','North Fork Wailua River','Hanalei River','Waimea River','ʻĪao Stream','Hakalau Stream','Wainiha River','Halawa Stream','Hālawa Stream','Waipiʻo Stream','Hanawī Stream','Kīpapa Stream','ʻŌpaeʻula Stream']
def make(epoch):
 lgm=epoch=='lgm';rng=random.Random(9202026)
 land={t['id'] for t in S['tiles'] if t['land_fraction']>=.40 or (lgm and sum(z>=-125 for z in t['elevation_samples'])/len(t['elevation_samples'])>=.4)}
 edits=[]
 for name,(lon,lat) in S['island_references'].items():
  ids=[t['id'] for t in S['tiles'] if t['island']==name]
  if not any(i in land for i in ids):
   i=max(ids,key=lambda i:S['tiles'][i]['land_fraction']);land.add(i);edits.append({'plot':i,'reason':'Minimum one hex for '+name})
 # Preserve the three documented Maui Nui members across sub-hex saddle connections.
 # Any added bridge must be shallower than -180m at a sampled point; never bridge deep channels.
 if lgm:
  refs=[nearest(*S['island_references'][n],land) for n in ['Molokaʻi','Lānaʻi','Maui']]
  for target in refs[1:]:
   groups=components(land);connected=next(g for g in groups if refs[0] in g)
   if target in connected:continue
   todo=[(0.,u) for u in connected];heapq.heapify(todo);cost={u:0 for u in connected};prev={}
   while todo:
    c,u=heapq.heappop(todo)
    if c!=cost[u]:continue
    if u==target:break
    for v in nb[u]:
     t=S['tiles'][v]
     if v not in land and max(t['elevation_samples']) < -180:continue
     nc=c+(0.02 if v in land else 1+max(0,-125-max(t['elevation_samples']))/20)
     if nc<cost.get(v,1e9):cost[v]=nc;prev[v]=u;heapq.heappush(todo,(nc,v))
   if target in cost:
    u=target
    while u not in connected:
     if u not in land:land.add(u);edits.append({'plot':u,'reason':'Minimum hex connection for documented Maui Nui saddle; generalized from bathymetry'})
     u=prev[u]
 coast={v for u in land for v in rings(u,2) if v not in land}
 ts=[]
 for t0 in S['tiles']:
  t={k:copy.deepcopy(t0[k]) for k in ['id','lon','lat','elevation','relief','local_relief','rainfall_mm','island']};i=t['id'];z=max(0,t['elevation']);rain=t['rainfall_mm'] or 500
  t.update(feature='',resource='',quantity=0,goody=False,lake='',california=False,glacier=None,rainfall_inferred=t0.get('rainfall_inferred',False))
  if i not in land:terrain='COAST' if i in coast else 'OCEAN';bio='Pacific Ocean';temp=None
  else:
   effective_z=z+(125 if lgm else 0);temp=25.5-.006*effective_z-(4.5 if lgm else 0)
   adjusted_rain=rain*(.8 if lgm else 1);t['scenario_rainfall_mm']=round(adjusted_rain)
   if lgm and temp<3:base='TUNDRA';bio='Alpine periglacial desert'
   elif temp<8:base='DESERT';bio='Alpine cinder / lava desert'
   elif adjusted_rain<650:base='PLAINS';bio='Dry leeward grassland / shrubland'
   elif adjusted_rain<1150:base='PLAINS';bio='Seasonal woodland / mesic scrub'
   else:base='GRASS';bio='Moist windward or Kona slopes'
   hills=t['local_relief']>=170 or (z>250 and t['local_relief']>=100)
   terrain=base+('_HILLS' if hills else '')
   if temp>=8 and adjusted_rain>=1150:
    t['feature']='JUNGLE' if temp>=19 and adjusted_rain>=1800 else 'FOREST';bio='Wet tropical forest' if t['feature']=='JUNGLE' else 'Mesic / montane broadleaf forest'
   elif temp>=8 and 850<=adjusted_rain<1150 and (i*31%7<2):t['feature']='FOREST';bio='Open seasonal woodland'
  t.update(terrain=terrain,ecoregion=(t['island']+' · ' if t['island'] else '')+bio,biome=bio,temperature_c=round(temp,1) if temp is not None else None)
  if lgm:t['paleobiome']=bio
  ts.append(t)
 peaks={}
 for name,lon,lat,volcano in SUMMITS:
  i=nearest(lon,lat,land);peaks[name]=i;t=ts[i];t['terrain']=t['terrain'].split('_')[0]+'_MOUNTAIN';t['feature']='VOLCANO' if volcano else '';t['landmark']=name
 if lgm:
  i=peaks['Mauna Kea'];ts[i].update(terrain='SNOW_MOUNTAIN',feature='',glacier={'basis':'USGS-documented Makanaka ice cap; one 70 km² hex approximation','confidence':'high for presence, approximate boundary'},paleobiome='Mauna Kea summit ice cap',biome='Mauna Kea summit ice cap')
 # Modern reef potential is limited to shallow, nearshore water; LGM shifts with sea level.
 for i in sorted(coast):
  depth=-(ts[i]['elevation']+(125 if lgm else 0))
  if 0<depth<65 and i%3!=0:ts[i]['feature']='REEF'
 # Geographically routed rivers, separate watersheds, explicit shoreline endpoints.
 adj=collections.defaultdict(list);shore=set()
 for ei,e in enumerate(E):
  if all(t in land for t in e['tiles']):
   adj[e['u']].append((e['v'],ei));adj[e['v']].append((e['u'],ei))
 for v in adj:
  if any(i not in land for i in vt[v]):shore.add(v)
 chosen={};occupied=set();routes=[];omitted=[]
 for name in PRIORITY:
  candidates=[r for r in S['sourceRivers'] if r['name']==name]
  if not candidates:continue
  src=max(candidates,key=lambda r:r['length_km']);pts=src['points'];a,b=pts[0],pts[-1]
  # endpoint closest to modern coast is the mouth, even when LGM coast moves seaward.
  def coastdist(p):return min(pointline(p,c) for c in S['coastlines'])
  head,mouth=(a,b) if coastdist(b)<coastdist(a) else (b,a)
  av=[v for v in adj if v not in occupied and math.dist(vpos[v],head)<1.5]
  shores=sorted([v for v in shore if v not in occupied and math.dist(vpos[v],mouth)<(4 if lgm else 1.8)],key=lambda v:math.dist(vpos[v],mouth))
  if not av or not shores:omitted.append(name);continue
  starts_allowed=sorted(av,key=lambda v:math.dist(vpos[v],head))[:8];targets=set(shores[:2]);q=[(math.dist(vpos[v],head)*5,v) for v in starts_allowed];heapq.heapify(q);cost={v:math.dist(vpos[v],head)*5 for v in starts_allowed};prev={};end=None
  while q:
   c,u=heapq.heappop(q)
   if c!=cost[u]:continue
   if u in targets and u in prev:end=u;break
   for v,ei in adj[u]:
    if v in occupied:continue
    e=E[ei]
    if any(ts[i]['terrain'].endswith('MOUNTAIN') for i in e['tiles']):continue
    mid=((vpos[u][0]+vpos[v][0])/2,(vpos[u][1]+vpos[v][1])/2);err=pointline(mid,pts)
    if err>(3.5 if lgm else 1.5):continue
    # Penalize long detours strongly, especially for very short island streams.
    nc=c+1+4*err*err
    if nc<cost.get(v,1e9):cost[v]=nc;prev[v]=(u,ei);heapq.heappush(q,(nc,v))
  if end is None:omitted.append(name);continue
  path=[];v=end
  while v in prev:
   u,ei=prev[v];path.append((ei,u,v));v=u
  path.reverse()
  if len(path)>max(3,int(src['length_km']/P*3)+3):omitted.append(name);continue
  for ei,u,v in path:
   dx,dy=v[0]-u[0],v[1]-u[1];flow=(0 if dy>0 else 3) if dx==0 else (1 if dy>0 else 2) if dx>0 else (5 if dy>0 else 4)
   e=E[ei];chosen[ei]={'plot':e['plot'],'side':e['side'],'flow':flow,'name':name,'points':[list(vpos[u]),list(vpos[v])],'offset_km':round(pointline(((vpos[u][0]+vpos[v][0])/2,(vpos[u][1]+vpos[v][1])/2),pts)*P,2)};occupied.update([u,v])
  routes.append({'name':name,'edges':len(path),'mouth_vertex':end})
 riverland={i for ei in chosen for i in E[ei]['tiles']}
 # Small low alluvial areas only. No huge continental-style floodplain fabrication.
 for i in riverland:
  t=ts[i]
  if t['terrain'] in ['GRASS','PLAINS'] and t['elevation']<150:t['feature']='FLOODPLAINS_'+('GRASSLAND' if t['terrain']=='GRASS' else 'PLAINS')
 def eligible(i,r):
  t=ts[i];f='FEATURE_'+t['feature'];k='RESOURCE_'+r
  return f in RR['features'].get(k,[]) if t['feature'] else 'TERRAIN_'+t['terrain'] in RR['terrains'].get(k,[])
 def put(i,r,note=None):
  ts[i]['resource']=r;ts[i]['quantity']=2 if r in ['HORSES','IRON','NITER','ALUMINUM'] else 1
  if note:ts[i]['resource_basis']=note
 # These are gameplay resources, including introduced crops/livestock in both epochs.
 weights={'FISH':14,'CRABS':3,'WHALES':2,'PEARLS':2,'BANANAS':4,'SUGAR':4,'RICE':3,'CATTLE':3,'SHEEP':3,'HORSES':2,'COFFEE':3,'CITRUS':2,'TEA':1,'SPICES':2,'STONE':5,'SALT':1,'IRON':2,'ALUMINUM':1,'NITER':1}
 for t in ts:
  i=t['id']
  if rng.random()>(.36 if i in land else .32):continue
  opts=[r for r in weights if eligible(i,r)]
  if opts:put(i,rng.choices(opts,[weights[r] for r in opts])[0])
 # Civ coffee requires flat grass or rainforest. Use a single canopy proxy in the
 # actual Kona belt, keeping its hilly topography; explicitly disclose the feature exception.
 kona=nearest(-155.88,19.48,[i for i in land if ts[i]['terrain'] in ['GRASS','GRASS_HILLS'] and ts[i]['feature'] in ['FOREST','JUNGLE','']])
 ts[kona]['feature']='JUNGLE';ts[kona]['ecoregion']+=' · coffee canopy game proxy';put(kona,'COFFEE','Kona coffee belt; one rainforest-feature canopy proxy required by native coffee placement rules. Gameplay crop in both epochs.')
 iconic=[{'name':'Kona coffee belt','resource':'COFFEE','plots':[kona]}]
 for name,r,lon,lat,note in [('Hāmākua sugar belt','SUGAR',-155.31,20.03,'Historic plantation crop; gameplay resource in both epochs.'),('Central Maui sugar belt','SUGAR',-156.45,20.85,'Historic plantation crop; gameplay resource in both epochs.'),('Hanalei wet agriculture','RICE',-159.48,22.20,'Rice is a game proxy for irrigated food production, including taro.'),('Waimea ranch country','HORSES',-155.66,20.01,'Introduced ranch livestock; gameplay resource.'),('Molokaʻi dryland salt','SALT',-157.14,21.05,'Generalized coastal salt production; not an evaporite ore field.')]:
  ids=[i for i in land if eligible(i,r) and math.dist(xy[i],xy[nearest(lon,lat)])<5]
  if ids:
   i=nearest(lon,lat,ids);put(i,r,note);iconic.append({'name':name,'resource':r,'plots':[i]})
 # Audit absent resource types against documented Hawaiian occurrences.
 resource_audit=[];reserved={a['plots'][0] for a in iconic if a['resource'] in ['COFFEE','SUGAR','RICE']}
 for plan in json.loads((ROOT/'source_data/resource_plan.json').read_text()):
  r=plan['resource'];anchor=nearest(plan['lon'],plan['lat']);options=[]
  for i,t in enumerate(ts):
   if i in reserved or (plan['island'] and t['island']!=plan['island']):continue
   distance=dist(i,anchor)*P
   if distance>plan['radius_km'] or t['terrain'].endswith('MOUNTAIN') or t['glacier']:continue
   terr,feat=t['terrain'],t['feature'];mode=plan['mode'];changes=[]
   if mode=='pasture':
    if terr not in ['GRASS','PLAINS','GRASS_HILLS','PLAINS_HILLS'] or t['local_relief']>300 or feat.startswith('FLOODPLAINS'):continue
    # A representative pasture patch within the 70 km² cell; never flatten a mountain.
    if terr!='GRASS':changes.append(terr+' → GRASS pasture');terr='GRASS'
    if feat:changes.append(feat+' cleared for pasture');feat=''
   elif mode in ['clear','quarry']:
    if terr in ['COAST','OCEAN'] or feat.startswith('FLOODPLAINS'):continue
    if feat in ['FOREST','JUNGLE']:changes.append(feat+' cleared for '+('quarry' if mode=='quarry' else 'crop'));feat=''
   elif mode=='canopy':
    if terr not in ['GRASS','GRASS_HILLS','PLAINS','PLAINS_HILLS'] or feat.startswith('FLOODPLAINS'):continue
    if feat!='JUNGLE':changes.append((feat or 'open land')+' → JUNGLE plantation canopy');feat='JUNGLE'
   elif mode=='woodland':
    if terr not in ['GRASS','GRASS_HILLS','PLAINS','PLAINS_HILLS'] or feat.startswith('FLOODPLAINS'):continue
    if feat!='FOREST':changes.append((feat or 'open land')+' → FOREST woodland-edge habitat');feat='FOREST'
   elif mode=='vineyard' and terr.endswith('HILLS') and feat not in ['FOREST']:
    if terr not in ['GRASS_HILLS','PLAINS_HILLS']:continue
    changes.append((feat or 'open land')+' → FOREST perennial-crop canopy');feat='FOREST'
   k='RESOURCE_'+r
   valid='FEATURE_'+feat in RR['features'].get(k,[]) if feat else 'TERRAIN_'+terr in RR['terrains'].get(k,[])
   if not valid:continue
   # Close regional location takes priority; prefer no clearing/terraforming where similar.
   score=distance+len(changes)*2+(1 if t['resource'] else 0)
   options.append((score,i,terr,feat,changes,distance))
  if not options:
   resource_audit.append({**plan,'placed':False,'reason':'No geographically close native-legal tile without excessive changes.'});continue
  _,i,terr,feat,changes,distance=min(options);t=ts[i];before={k:t[k] for k in ['terrain','feature','resource']};t['terrain']=terr;t['feature']=feat;t['goody']=False
  t['land_use_adjustment']='; '.join(changes) if changes else None
  put(i,r,plan['note']+(' Native game representation: '+'; '.join(changes)+'.' if changes else ''))
  t['resource_source']=plan['source'];reserved.add(i)
  resource_audit.append({**plan,'placed':True,'plot':i,'distance_km':round(distance,1),'before':before,'changes':changes})
  iconic.append({'name':plan['name'],'resource':r,'plots':[i]})
 iconic=[a for a in iconic if ts[a['plots'][0]]['resource']==a['resource']]
 # Six suggested maritime starts: one per larger western island and three on Hawaiʻi.
 # Score coastal food, usable land, production, resources; never use modern cities as anchors.
 starts=[]
 for name,count in [('Kauaʻi',1),('Oʻahu',1),('Maui',1),('Hawaiʻi',3)]:
  ids=[i for i in land if ts[i]['island']==name and not ts[i]['terrain'].endswith('MOUNTAIN') and not ts[i]['terrain'].startswith(('SNOW','TUNDRA','DESERT')) and 3<i%W<W-4 and 3<i//W<H-4 and (i in riverland or any(v not in land for v in nb[i]))]
  for _ in range(count):
   candidates=[i for i in ids if all(dist(i,s['id'])>=6 for s in starts)]
   if not candidates:break
   def score(i):
    ring=rings(i,2);usable=[j for j in ring if j in land and not ts[j]['terrain'].endswith('MOUNTAIN')]
    food=sum(ts[j]['resource'] in ['FISH','CRABS','BANANAS','CATTLE','RICE','SUGAR','SHEEP'] for j in ring)
    return len(usable)*2+food*3+sum(ts[j]['feature'] in ['FOREST','JUNGLE'] or ts[j]['terrain'].endswith('HILLS') for j in usable)+(7 if i in riverland else 0)-max(0,ts[i]['elevation'])/350
   i=max(candidates,key=lambda i:(score(i),-i));starts.append({'id':i,'name':f'Start {len(starts)+1:02d}','region':name,'metrics':{}})
   # Nearby bonus food and an iron placement improve playability without altering topography.
   for r in ['FISH','FISH','IRON']:
    opts=[j for j in rings(i,3) if not ts[j]['resource'] and eligible(j,r)]
    if opts:put(min(opts,key=lambda j:dist(i,j)),r,'Gameplay balance; iron represents basaltic iron, not a mapped economic ore deposit.' if r=='IRON' else 'Coastal food balancing.')
 for s in starts:
  i=s['id'];ring=rings(i,3)
  for r in ['FISH','BANANAS','SHEEP','CATTLE']:
   if sum(ts[j]['resource'] in ['FISH','CRABS','BANANAS','CATTLE','RICE','SUGAR','SHEEP'] for j in ring)>=5:break
   opts=[j for j in ring if not ts[j]['resource'] and eligible(j,r)]
   if opts:put(min(opts,key=lambda j:dist(i,j)),r,'Food added for the suggested start.')
  lux={ts[j]['resource'] for j in ring if any(r['id']==ts[j]['resource'] and r['class']=='luxury' for r in CAT['resources'])}
  for r in ['WHALES','PEARLS','COFFEE','SUGAR','CITRUS','SPICES','SALT']:
   if len(lux)>=2:break
   opts=[j for j in ring if not ts[j]['resource'] and eligible(j,r)]
   if r not in lux and opts:put(min(opts,key=lambda j:dist(i,j)),r,'Luxury access for maritime start balance.');lux.add(r)
 for s in starts:
  i=s['id'];ring=rings(i,3);food=sum(ts[j]['resource'] in ['FISH','CRABS','BANANAS','CATTLE','RICE','SUGAR','SHEEP'] for j in ring)
  s['metrics']={'fresh_water':i in riverland,'nearest_start_hexes':min(hexdist(i,o['id']) for o in starts if o!=s),'passable_ring3':sum(j in land and not ts[j]['terrain'].endswith('MOUNTAIN') for j in ring),'food_resources_ring3':food,'luxury_types_ring3':len({ts[j]['resource'] for j in ring if any(r['id']==ts[j]['resource'] and r['class']=='luxury' for r in CAT['resources'])}),'score':round(score(i),1)}
 for i in sorted(land):
  if ts[i]['feature']==ts[i]['resource']=='' and not ts[i]['terrain'].endswith('MOUNTAIN') and all(dist(i,s['id'])>3 for s in starts) and i%19==0:ts[i]['goody']=True
 stats={'tiles':N,'land':len(land),'water':N-len(land),'mountains':sum(t['terrain'].endswith('MOUNTAIN') for t in ts),'hills':sum(t['terrain'].endswith('HILLS') for t in ts),'forests':sum(t['feature']=='FOREST' for t in ts),'rainforests':sum(t['feature']=='JUNGLE' for t in ts),'reefs':sum(t['feature']=='REEF' for t in ts),'floodplains':sum(t['feature'].startswith('FLOODPLAINS') for t in ts),'glacier_hexes':sum(bool(t['glacier']) for t in ts),'river_edges':len(chosen),'river_names':len(routes),'resource_tiles':sum(bool(t['resource']) for t in ts),'exposed_seabed_hexes':0}
 return {'width':W,'height':H,'pitch_km':P,'projection':S['projection'],'epoch':epoch,'tiles':ts,'rivers':list(chosen.values()),'sourceRivers':S['sourceRivers'],'coastlines':S['coastlines'],'boundaries':[],'lakes':[],'starts':starts,'resource_catalog':CAT,'iconic_deposits':iconic,'stats':stats,'landmarks':peaks,'notes':{'resource_audit':resource_audit,'coast_generalizations':edits,'river_routes':routes,'omitted_rivers':omitted,'recommended_players':6,'resource_placement_exceptions':'Crops and livestock are gameplay analogues in both epochs. Iron and aluminum are balance abstractions of volcanic parent material, not economic deposits. No invented oil, coal, or uranium.','paleo_lakes':[]}}

def connect_coastal_routes(d):
 """Join all coast-water components without converting or crossing a land tile."""
 ts=d['tiles'];coast={t['id'] for t in ts if t['terrain']=='COAST'};routes=[]
 while len(components(coast))>1:
  gs=components(coast);connected=max(gs,key=len);targets=coast-connected
  q=[(0.,i) for i in connected];heapq.heapify(q);cost={i:0. for i in connected};prev={};end=None
  while q:
   c,u=heapq.heappop(q)
   if c!=cost[u]:continue
   if u in targets:end=u;break
   for v in nb[u]:
    if ts[v]['terrain'] not in ['OCEAN','COAST']:continue
    step=.01 if v in coast else 1+min(6000,max(0,-ts[v]['elevation']))/100000
    nc=c+step
    if nc<cost.get(v,1e9):cost[v]=nc;prev[v]=u;heapq.heappush(q,(nc,v))
  if end is None:raise ValueError('No water-only route between island coast components')
  u=end;added=[]
  while u not in connected:
   if u not in coast:
    ts[u]['terrain']='COAST';ts[u]['game_coast_corridor']=True;coast.add(u);added.append(u)
   u=prev[u]
  routes.append({'added_plots':added,'reason':'User-requested continuous coast route for early ships; actual channel depth retained in elevation field.'})
 d['notes']['coast_navigation_routes']=routes;d['stats']['navigation_coast_hexes']=sum(len(r['added_plots']) for r in routes)

def write_native(d):
 epoch=d['epoch'];title='Hawaiʻi — '+('Last Glacial Maximum' if epoch=='lgm' else 'Modern')+' (Gathering Storm)';name='Hawaii_'+('LGM' if epoch=='lgm' else 'Modern')+'.Civ6Map';meta=json.loads((ROOT/'source_data/metadata_template.json').read_text());identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://codex.local/hawaii-standard-'+epoch)).upper();key=identity.replace('-','')
 meta['Map']=[['Default',W,H,23,18,0,0,'MAPSIZE_STANDARD']]
 meta['MetaData']=[['MetaDataVersion','1'],['AppVersion','1.0.12.43 (899997)'],['DisplayName',title],['ID',identity],['IsMod','1'],['LastUpdated','1789948800']]
 for row in meta['ModProperties']:
  if row[0]=='ID':row[1]=identity
  elif row[0] in ['Name','Description']:row[1]='LOC_HI'+key+'_'+row[0].upper()
 meta['ModText']=[['en_US','LOC_HI'+key+'_NAME',title],['en_US','LOC_HI'+key+'_DESCRIPTION','84 × 54; main Hawaiian Islands at 9 km hex spacing. '+('Approximate 21 ka climate and -125 m sea level.' if epoch=='lgm' else 'Modern coastline and rainfall-based biomes.')]]
 meta['ModSettings_Properties']=[['WorldBuilder','WORLDBUILDER','Name','LOC_HI'+key+'_NAME'],['WorldBuilder','WORLDBUILDER','Description','LOC_HI'+key+'_DESCRIPTION']]
 f=ROOT/name
 if f.exists():f.unlink()
 c=sqlite3.connect(f);c.executescript((ROOT/'schema.sql').read_text())
 for table,rows in meta.items():
  if rows:c.executemany('INSERT INTO "'+table+'" VALUES('+','.join('?' for _ in rows[0])+')',rows)
 c.executemany('INSERT INTO Plots VALUES(?,?,?,?)',[(t['id'],'TERRAIN_'+t['terrain'],'CONTINENT_OCEANIA' if t['terrain'] not in ['COAST','OCEAN'] else '',int(t['terrain'].endswith('MOUNTAIN'))) for t in d['tiles']])
 c.executemany('INSERT INTO PlotFeatures VALUES(?,?)',[(t['id'],'FEATURE_'+t['feature']) for t in d['tiles'] if t['feature']])
 c.executemany('INSERT INTO PlotResources VALUES(?,?,?)',[(t['id'],'RESOURCE_'+t['resource'],t['quantity']) for t in d['tiles'] if t['resource']])
 c.executemany('INSERT INTO PlotImprovements VALUES(?,?,?)',[(t['id'],'IMPROVEMENT_GOODY_HUT',-1) for t in d['tiles'] if t['goody']])
 rivers={}
 for r in d['rivers']:
  row=rivers.setdefault(r['plot'],[r['plot'],0,0,0,-1,-1,-1]);flag,flow={'W':(2,4),'NW':(3,5),'NE':(1,6)}[r['side']];row[flag]=1;row[flow]=r['flow']
 c.executemany('INSERT INTO PlotRivers VALUES(?,?,?,?,?,?,?)',rivers.values());c.commit();c.execute('VACUUM');c.close()
 (ROOT/(epoch+'_data.json')).write_text(json.dumps(d,separators=(',',':')))
 print(name,d['stats'],flush=True)

def write_exports(modern,lgm):
 with (ROOT/'resource_counts.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['resource','class','modern_tiles','lgm_tiles']);mc=collections.Counter(t['resource'] for t in modern['tiles']);lc=collections.Counter(t['resource'] for t in lgm['tiles'])
  for r in CAT['resources']:w.writerow([r['id'],r['class'],mc[r['id']],lc[r['id']]])
 with (ROOT/'suggested_starts.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['epoch','start','region','plot','x','y','freshwater','nearest_start_hexes','passable_ring3','food_resources_ring3','luxury_types_ring3'])
  for d in [modern,lgm]:
   for st in d['starts']:w.writerow([d['epoch'],st['name'],st['region'],st['id'],st['id']%W,st['id']//W,*[st['metrics'][k] for k in ['fresh_water','nearest_start_hexes','passable_ring3','food_resources_ring3','luxury_types_ring3']]])
 (ROOT/'resource_audit.json').write_text(json.dumps({d['epoch']:d['notes']['resource_audit'] for d in [modern,lgm]},indent=2,ensure_ascii=False))

if __name__=='__main__':
 modern=make('modern');lgm=make('lgm');connect_coastal_routes(modern);connect_coastal_routes(lgm)
 for t,m in zip(lgm['tiles'],modern['tiles']):t['modern_terrain']=m['terrain']
 lgm['stats']['exposed_seabed_hexes']=sum(m['terrain'] in ['COAST','OCEAN'] and t['terrain'] not in ['COAST','OCEAN'] for m,t in zip(modern['tiles'],lgm['tiles']))
 write_native(modern);write_native(lgm);write_exports(modern,lgm)
 template=ROOT/'tools/viewer_template.html'
 if template.exists():(ROOT/'inspect.html').write_text(template.read_text().replace('__MAP_DATA__',json.dumps(lgm,separators=(',',':')).replace('</','<\\/')).replace('__MODERN_DATA__',json.dumps(modern,separators=(',',':')).replace('</','<\\/')))
