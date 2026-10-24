"""California Civ VI generator. Derived schema: je-suis-tm (Apache-2.0).
All geography and map generation below are new; see SOURCES.md for source data.
Usage: python tools/build_geography.py --data /path/to/source_data
Run on a copy: this replaces the native map and map_data.json.
Dependencies: numpy scipy pyshp shapely pyproj pillow.
Expected data: extracted Natural Earth directories land, states, lakes,
lakes_north_america, rivers_lake_centerlines, rivers_north_america; EPA shapefile
in ecoregions/; Terrarium tiles dem/7-{x}-{y}.png (x18..24, y46..52);
dwr_rivers.geojson, delta_rivers.geojson, socal_rivers.geojson, imperial_rivers.geojson,
forest_landcover_2021.tif (included in source_data/), nevada_rivers.geojson and nevada_lakes.geojson from the services
in SOURCES.md. Afterward run place_iconic_resources.py, place_regional_resources.py, balance_starts.py,
rebuild_native.py --viewer-only and validate_map.py.
"""
from pathlib import Path
import json, math, sqlite3, shutil, heapq, collections, random, hashlib
import numpy as np
import shapefile
from PIL import Image
from pyproj import Transformer, CRS
from shapely.geometry import shape, Point, Polygon, LineString, box, mapping
from shapely.ops import transform, unary_union, linemerge
from shapely import contains_xy
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parent.parent
import argparse
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data',type=Path,required=True);args=ap.parse_args()
DATA=args.data; OUT=ROOT
W,H=80,88; P=15500.; DY=P*math.sqrt(3)/2; R=P/math.sqrt(3); X0=-500000.; Y0=-685000.
proj=Transformer.from_crs(4326,3310,always_xy=True); inv=Transformer.from_crs(3310,4326,always_xy=True)
xy=np.array([(X0+(x+.5*(y%2))*P,Y0+y*DY) for y in range(H) for x in range(W)])
ll=np.array(inv.transform(xy[:,0],xy[:,1])).T
bounds=box(X0-P/2,Y0-R,X0+(W-.5)*P,Y0+(H-1)*DY+R)
geo_bounds=box(-128,31,-111,44)
angles=np.radians([90,30,-30,-90,-150,150]); offsets=np.c_[np.cos(angles),np.sin(angles)]*R
polys=[Polygon(c+offsets) for c in xy]; kd=cKDTree(xy)
rng=random.Random(6192026)

def records(name,project=True):
 p=next((DATA/name).rglob('*.shp'));rd=shapefile.Reader(str(p),encoding='utf-8',encodingErrors='replace')
 for sr in rd.iterShapeRecords():
  if not sr.shape.points:continue
  bb=sr.shape.bbox
  if project and (bb[2]<-128 or bb[0]>-111 or bb[3]<31 or bb[1]>44):continue
  g=shape(sr.shape.__geo_interface__)
  if not g.is_valid:g=g.buffer(0)
  if project:g=transform(proj.transform,g.intersection(geo_bounds))
  if not g.is_empty:yield sr.record.as_dict(),g

print('Reading coast, lakes and ecology',flush=True)
land=unary_union([g for d,g in records('land')])
states=[(d,g) for d,g in records('states') if g.intersects(bounds)]
cal=next(g for d,g in states if d['name']=='California')
assert bounds.contains(cal),'California clipped!'
landmask=contains_xy(land,xy[:,0],xy[:,1]); island_edits=[]
# Preserve small real islands as a minimum of one intersecting hex.
for g in cal.geoms if hasattr(cal,'geoms') else [cal]:
 if g.area>2e10:continue
 ids=kd.query_ball_point([g.centroid.x,g.centroid.y],P*2)
 if ids and not any(landmask[i] and polys[i].intersects(g) for i in ids):
  i=max(ids,key=lambda i:polys[i].intersection(g).area)
  if polys[i].intersection(g).area>0:
   landmask[i]=True;island_edits.append(i)

# Keep sub-tile Bay narrows open instead of accidentally creating an inland lake.
# These are named real waterway locations, widened to the minimum one game tile.
strait_edits=[]
for name,lon,lat in [('Golden Gate',-122.49,37.82),('Carquinez Strait',-122.22,38.06),('Suisun Bay',-122.03,38.055),('Colorado estuary',-114.94,31.89),('Upper Gulf of California',-114.84,31.76)]:
 i=int(kd.query(proj.transform(lon,lat))[1]);landmask[i]=False;strait_edits.append({'name':name,'id':i})

lakes=[]; lake_names={};waterkind={}
for ds in ['lakes','lakes_north_america']:
 for d,g in records(ds):
  name=d.get('name_en') or d.get('name') or 'Unnamed lake'
  if not g.intersects(bounds) or g.area<12e6:continue
  # Dry lake beds stay land; no artificial water at Owens Lake or Great Basin playas.
  if name in ['Owens','Owens Lake'] or 'intermittent' in str(d.get('featurecla','')).lower():continue
  lakes.append((name,g))
  for i in kd.query_ball_point([g.centroid.x,g.centroid.y],max(g.bounds[2]-g.bounds[0],g.bounds[3]-g.bounds[1])+P):
   if g.contains(Point(xy[i])) or polys[i].intersection(g).area>polys[i].area*.30:
    lake_names[i]=name;waterkind[i]='lake';landmask[i]=False
# National NHD fills an omitted but important Carson River reservoir.
for f in json.loads((DATA/'nevada_lakes.geojson').read_text())['features']:
 name=f['properties'].get('gnis_name') or f['properties'].get('GNIS_Name') or f['properties'].get('GNIS_NAME')
 assert name
 g=transform(lambda x,y,z=None:proj.transform(x,y),shape(f['geometry']))
 if not g.is_valid:g=g.buffer(0)
 lakes.append((name,g))
 candidates=[i for i in kd.query_ball_point([g.centroid.x,g.centroid.y],P*3) if polys[i].intersects(g)]
 if candidates:
  i=max(candidates,key=lambda i:polys[i].intersection(g).area)
  landmask[i]=False;lake_names[i]=name;waterkind[i]='lake'

# Preserve recognizable natural lakes even when below a tile's area.
for name,g in lakes:
 if any(w in name.lower() for w in ['tahoe','mono','clear','pyramid','walker','salton','goose','almanor','klamath','honey','eagle']):
  i=int(kd.query([g.centroid.x,g.centroid.y])[1]);landmask[i]=False;lake_names[i]=name;waterkind[i]='lake'

# Keep each continuous lake polygon connected after rasterization. Narrow arms
# otherwise become disconnected ponds and sever river systems (notably Lake Mead).
def native_adj(i):
 x,y=i%W,i//W
 for a,b in [(x-1,y),(x+1,y),(x+y%2-1,y-1),(x+y%2,y-1),(x+y%2-1,y+1),(x+y%2,y+1)]:
  if 0<=a<W and 0<=b<H:yield b*W+a
lake_connectors=[]
for name,g in lakes:
 for part in g.geoms if g.geom_type=='MultiPolygon' else [g]:
  existing={i for i,n in lake_names.items() if n==name and polys[i].intersects(part)}
  if len(existing)<2:continue
  covered={i for i in range(W*H) if polys[i].intersects(part)}
  frac={i:polys[i].intersection(part).area/polys[i].area for i in covered}
  linked={next(iter(existing))}
  while not existing<=linked:
   q=[(0,i) for i in linked];heapq.heapify(q);distance={i:0 for i in linked};prev={};target=None
   while q:
    cost,u=heapq.heappop(q)
    if cost!=distance[u]:continue
    if u in existing-linked:target=u;break
    for v in native_adj(u):
     if v not in covered:continue
     nc=cost+(.05 if v in existing else 1+4*(1-frac[v]))
     if nc<distance.get(v,1e30):distance[v]=nc;prev[v]=u;heapq.heappush(q,(nc,v))
   if target is None:break
   u=target
   while u not in linked:
    linked.add(u)
    if u not in existing:
     landmask[u]=False;lake_names[u]=name;waterkind[u]='lake'
     lake_connectors.append({'name':name,'id':u,'source_water_fraction':round(frac[u],3)})
    u=prev[u]

# Preserve the real San Francisco Peninsula's narrow land neck at San Bruno.
# The intersecting hex is 48% source land but its center falls just offshore.
peninsula_edits=[]
i=3858;landmask[i]=True;lake_names.pop(i,None);waterkind.pop(i,None)
peninsula_edits.append({'name':'San Francisco Peninsula / San Bruno land neck','id':i,'source_land_fraction':round(polys[i].intersection(land).area/polys[i].area,3)})

# Sample DEM at 49 positions across every hex, at ~1km source resolution.
tiles={}
for f in (DATA/'dem').glob('*.png'):
 z,x,y=map(int,f.stem.split('-'));a=np.asarray(Image.open(f)).astype(float);tiles[x,y]=a[:,:,0]*256+a[:,:,1]+a[:,:,2]/256-32768

def dem(lon,lat):
 tx=(np.asarray(lon)+180)/360*128;ty=(1-np.arcsinh(np.tan(np.radians(lat)))/np.pi)/2*128
 ix=np.floor(tx).astype(int);iy=np.floor(ty).astype(int);px=np.clip(((tx-ix)*256).astype(int),0,255);py=np.clip(((ty-iy)*256).astype(int),0,255)
 return np.array([tiles[a,b][d,c] for a,b,c,d in zip(ix,iy,px,py)])
samples=[]
for dx in np.linspace(-P*.43,P*.43,7):
 for dy in np.linspace(-R*.75,R*.75,7):
  if abs(dx)/(P/2)+abs(dy)/R>1.95:continue
  lon,lat=inv.transform(xy[:,0]+dx,xy[:,1]+dy);samples.append(dem(lon,lat))
a=np.array(samples);z=dem(ll[:,0],ll[:,1]);zmin=np.percentile(a,10,axis=0);zmax=np.percentile(a,90,axis=0);relief=zmax-zmin
# Use the central 6 km of each hex to distinguish flat basin floors from
# adjacent range walls within the same 15.5 km cell.
inner=[]
for dx in [-3000,-1500,0,1500,3000]:
 for dy in [-3000,-1500,0,1500,3000]:
  lon,lat=inv.transform(xy[:,0]+dx,xy[:,1]+dy);inner.append(dem(lon,lat))
inner=np.array(inner);local_relief=np.percentile(inner,90,axis=0)-np.percentile(inner,10,axis=0)
# Ecoregion polygons supply terrain/vegetation zones, not arbitrary latitude bands.
ecopath=next((DATA/'ecoregions').glob('*.prj')); ep=Transformer.from_crs(CRS.from_wkt(ecopath.read_text()),3310,always_xy=True)
eco=['Ocean']*(W*H); ecolist=[]
for d,g in records('ecoregions',False):
 g=transform(ep.transform,g)
 if not g.intersects(bounds):continue
 ecolist.append((d['US_L3NAME'],g))
 mask=contains_xy(g,xy[:,0],xy[:,1])
 for i in np.where(mask)[0]:eco[i]=d['US_L3NAME']
# An enlarged coastal land hex may have its center offshore. Assign its ecology
# from the source land portion instead of calling it Baja California by default.
for i in range(W*H):
 if landmask[i] and eco[i]=='Ocean' and ll[i,1]>32.5:
  overlaps=[(polys[i].intersection(g).area,name) for name,g in ecolist if g.intersects(polys[i])]
  if overlaps:eco[i]=max(overlaps)[1]
terrain=[];features={}
for i,(lon,lat) in enumerate(ll):
 if not landmask[i]:terrain.append('TERRAIN_COAST' if i in lake_names else 'TERRAIN_OCEAN');continue
 e=eco[i]
 if e=='Ocean':e=eco[i]='Northern Baja California (latitude/elevation approximation)'
 base='PLAINS'; fp=0
 if e in ['Coast Range','Klamath Mountains/California High North Coast Range','Cascades']:
  base='GRASS';fp=.88
 elif e=='Sierra Nevada':
  base='GRASS' if z[i]<1900 else 'PLAINS';fp=.83 if 700<z[i]<2850 else .25
 elif e=='Eastern Cascades Slopes and Foothills':base='PLAINS';fp=.63
 elif 'Central California Valley' in e:base='GRASS' if lat>37.2 else 'PLAINS';fp=.02
 elif 'Chaparral' in e or 'Coast' in e or 'Foothills' in e:
  base='GRASS' if lat>36.5 and z[i]<600 else 'PLAINS';fp=.15 if z[i]>250 else .04
 elif 'California Mountains' in e:base='PLAINS';fp=.63 if z[i]>1250 else .14
 elif any(k in e for k in ['Mojave','Sonoran','Basin and Range','Plateau']):
  base='DESERT' if ('Mojave' in e or 'Sonoran' in e or z[i]<1750) else 'PLAINS';fp=.14 if z[i]>2100 else 0
 elif 'Baja' in e:
  base='DESERT' if lon>-116 or z[i]<250 and lon>-116.8 else 'PLAINS';fp=.35 if z[i]>1400 else .02
 else:base='PLAINS';fp=.10
 # Relative relief prevents broad elevated Nevada basins becoming mountains.
 mountain=(zmax[i]>2550 and relief[i]>700) or (zmax[i]>1700 and relief[i]>1150) or z[i]>3150
 hill=relief[i]>240 or (relief[i]>150 and z[i]>650)
 if 'Basin and Range' in e and local_relief[i]<180:hill=False
 if z[i]>3000:base='TUNDRA';fp=0
 if mountain:kind=base+'_MOUNTAIN'
 elif hill:kind=base+'_HILLS'
 else:kind=base
 terrain.append('TERRAIN_'+kind)
 if not mountain and base!='DESERT' and rng.random()<fp:features[i]='FEATURE_FOREST'

# Audit woodland distribution using sampled NLCD 2021 forest classes.
# WMS is a ~0.8 km categorical rendering, not the original 30 m raster.
lc_image=Image.open(DATA/'forest_landcover_2021.tif').convert('RGB')
lc=np.asarray(lc_image); forest_rgb={(104,170,99),(28,99,48),(181,201,142)}
forest_samples=np.zeros(W*H); valid_samples=np.zeros(W*H)
for dx in np.arange(-7500,7501,1000):
 for dy in np.arange(-8500,8501,1000):
  if not Polygon(offsets).covers(Point(dx,dy)):continue
  lon,lat=inv.transform(xy[:,0]+dx,xy[:,1]+dy)
  xx=np.floor((np.asarray(lon)+125)/13*lc.shape[1]).astype(int)
  yy=np.floor((43-np.asarray(lat))/11*lc.shape[0]).astype(int)
  inside=(xx>=0)&(xx<lc.shape[1])&(yy>=0)&(yy<lc.shape[0])
  for i in np.where(inside & landmask)[0]:
   rgb=tuple(lc[yy[i],xx[i]])
   if rgb in {(255,255,255),(71,107,160)}:continue
   valid_samples[i]+=1;forest_samples[i]+=rgb in forest_rgb
forest_fraction=np.divide(forest_samples,valid_samples,out=np.zeros(W*H),where=valid_samples>0)
forest_edits=[]
for i in range(W*H):
 if not landmask[i] or valid_samples[i]<20 or any(k in terrain[i] for k in ['MOUNTAIN','DESERT']):continue
 # Forest-class area, not canopy density. Orchards/crops are separate classes.
 if forest_fraction[i]>=.30 and features.get(i)!='FEATURE_FOREST':
  features[i]='FEATURE_FOREST';forest_edits.append({'id':i,'action':'added','forest_fraction':round(float(forest_fraction[i]),3)})
 # Remove isolated procedural trees in strongly non-forested arid uplands.
 elif forest_fraction[i]<.03 and 'Basin and Range' in eco[i] and features.get(i)=='FEATURE_FOREST':
  features.pop(i);forest_edits.append({'id':i,'action':'removed','forest_fraction':round(float(forest_fraction[i]),3)})

# Explicit summit: a hex-center DEM sample misses Lassen Peak's summit.
lassen_id=int(kd.query(proj.transform(-121.505,40.488))[1])
terrain[lassen_id]='TERRAIN_GRASS_MOUNTAIN';features.pop(lassen_id,None)

# Preserve narrow, real valley-floor corridors that a 15.5 km footprint mixes
# with neighboring range walls. These control lines are documented in the audit.
valley_axes={
 'Owens Valley':('DESERT',[(-118.52,37.47),(-118.40,37.36),(-118.29,37.17),(-118.24,37.04),(-118.25,36.94),(-118.20,36.8),(-118.15,36.69),(-118.06,36.60),(-118.00,36.50),(-118.02,36.30)]),
 'Salinas Valley':(None,[(-121.64,36.68),(-121.36,36.43),(-121.11,36.21),(-120.91,35.99)]),
 'Smith Valley':('DESERT',[(-119.47,38.74),(-119.40,38.77),(-119.33,38.81),(-119.31,38.87)]),
 'Mason Valley':('DESERT',[(-119.18,38.88),(-119.14,38.97),(-119.17,39.06),(-119.15,39.18)]),
 'Carson Valley':('DESERT',[(-119.77,39.16),(-119.78,38.96),(-119.7,38.86)]),
 'Death Valley':('DESERT',[(-117.36,36.995),(-117.27,36.89),(-117.20,36.80),(-117.14,36.70),(-117.06,36.60),(-116.90,36.47),(-116.81,36.24),(-116.72,36.05)])}
valley_edits=[]
for name,(base,points) in valley_axes.items():
 line=LineString([proj.transform(lon,lat) for lon,lat in points]);ids=[];changed=[]
 for i in range(W*H):
  if not landmask[i] or not polys[i].intersects(line):continue
  ids.append(i);old=terrain[i]
  kind=base or old.replace('TERRAIN_','').split('_')[0]
  terrain[i]='TERRAIN_'+kind
  if old!=terrain[i]:changed.append({'id':i,'before':old,'after':terrain[i]})
  if features.get(i)=='FEATURE_FOREST':features.pop(i)
 valley_edits.append({'name':name,'axis_lonlat':points,'tiles':ids,'changes':changed})

# Preserve the Tahoe mountain basin at this coarse scale. Boundary cells mix
# the forested shoreline with the dry Carson Valley; do not display a desert shore.
tahoe_edits=[]
tahoe_shore={j for i,n in lake_names.items() if n=='Tahoe' for j in native_adj(i) if landmask[j]}
for i in sorted(tahoe_shore):
 old=terrain[i]
 if 'DESERT' in old:terrain[i]=old.replace('DESERT','PLAINS')
 if 'MOUNTAIN' not in terrain[i]:features[i]='FEATURE_FOREST'
 if old!=terrain[i]:tahoe_edits.append({'id':i,'before':old,'after':terrain[i],'reason':'Forested Tahoe shore / mixed Carson Valley hex'})
for name,lon,lat in [('Crystal Range / Pyramid Peak',-120.157,38.845),('Rubicon highlands',-120.137,39.00),('Ellis Peak',-120.258,39.067),('Granite Chief',-120.26,39.191)]:
 i=int(kd.query(proj.transform(lon,lat))[1]);old=terrain[i]
 assert landmask[i] and i not in {j for v in valley_edits for j in v['tiles']}
 terrain[i]='TERRAIN_PLAINS_MOUNTAIN';features.pop(i,None)
 tahoe_edits.append({'id':i,'before':old,'after':terrain[i],'reason':name})

# All topological neighbours and unique Civ VI owned edges.
vertices=[];vindex={};edges=[];vadj=collections.defaultdict(list);padj=collections.defaultdict(list)
def vid(p):
 key=tuple(round(float(t),2) for t in p)
 if key not in vindex:vindex[key]=len(vertices);vertices.append(list(p))
 return vindex[key]
edge_by_pair={}
for i,c in enumerate(xy):
 vs=[vid(p) for p in c+offsets]
 for k in range(6):
  pair=tuple(sorted((vs[k],vs[(k+1)%6])))
  edge_by_pair.setdefault(pair,[]).append((i,k))
for (u,v),owners in edge_by_pair.items():
 if len(owners)!=2:continue
 i,j=owners[0][0],owners[1][0];padj[i].append(j);padj[j].append(i)
 own=next(((i,k) for i,k in owners if k in [1,2,3]),None)
 if not own:raise RuntimeError('edge parity error')
 o,k=own
 ei=len(edges);edges.append({'u':u,'v':v,'i':o,'side':{1:'W',2:'NW',3:'NE'}[k],'tiles':[i,j]})
 if landmask[i] and landmask[j]:vadj[u].append((v,ei));vadj[v].append((u,ei))
# Coast extends two tiles from actual shoreline.
water_distance={i:0 for i in np.where(landmask)[0]};q=collections.deque(water_distance)
while q:
 i=q.popleft()
 if water_distance[i]>=2:continue
 for j in padj[i]:
  if j not in water_distance:water_distance[j]=water_distance[i]+1;q.append(j)
for i in range(W*H):
 if not landmask[i] and (i in lake_names or water_distance.get(i,99)<=2):terrain[i]='TERRAIN_COAST'

print('Routing geographic rivers on legal hex edges',flush=True)
va=np.array(vertices);validnodes=np.array(sorted(vadj));vkd=cKDTree(va[validnodes]);mid=np.array([(va[e['u']]+va[e['v']])/2 for e in edges])
vwater=set()
for edge in edges:
 if any(not landmask[i] for i in edge['tiles']):vwater.update([edge['u'],edge['v']])
shore_nodes=np.array(sorted(vwater.intersection(vadj)))
shore_kd=cKDTree(va[shore_nodes])
sea_nodes=set()
for e in edges:
 if any(not landmask[i] and i not in lake_names for i in e['tiles']):sea_nodes.update([e['u'],e['v']])
sea_nodes=np.array(sorted(sea_nodes.intersection(vadj)));sea_kd=cKDTree(va[sea_nodes])
lake_union=unary_union([g for _,g in lakes])
# Rivers must meet the water actually represented on the game grid.
raster_lake_union=unary_union([polys[i] for i in lake_names])
source_rivers=[];rawgroups=collections.defaultdict(list)
for ds in ['rivers_lake_centerlines','rivers_north_america']:
 for d,g in records(ds):
  name=d.get('name_en') or d.get('name') or 'Unnamed tributary'
  if not g.intersects(bounds):continue
  # Seasonal desert channels are an overlay only; Civ has no seasonal-river type.
  intermittent='Intermittent' in d.get('featurecla','')
  for line in g.geoms if hasattr(g,'geoms') else [g]:
   if not isinstance(line,LineString):continue
   clipped=line.intersection(bounds)
   for part in clipped.geoms if hasattr(clipped,'geoms') else [clipped]:
    if not isinstance(part,LineString) or part.length<100:continue
    source_rivers.append({'name':name,'seasonal':intermittent,'points':np.round(np.array(part.simplify(1000).coords),1).tolist()})
    if not intermittent:rawgroups[name].append(part)
# Supplement gaps in the global data with USGS NHD linework distributed by California DWR.
dwrfile=DATA/'dwr_rivers.geojson'
if dwrfile.exists():
 groups=collections.defaultdict(list)
 national=json.loads((DATA/'nevada_rivers.geojson').read_text())['features']
 national_names={f['properties']['gnis_name'] for f in national}
 supplemental=json.loads(dwrfile.read_text())['features']
 for filename in ['socal_rivers.geojson','delta_rivers.geojson','imperial_rivers.geojson']:
  supplemental.extend(json.loads((DATA/filename).read_text())['features'])
 # Avoid noding slightly different copies of the same NHD network into tiny fragments.
 supplemental=[f for f in supplemental if (f['properties'].get('GNIS_Name') or f['properties'].get('gnis_name')) not in national_names]+national
 for f in supplemental:
  name=f['properties'].get('GNIS_Name') or f['properties'].get('gnis_name')
  g=shape(f['geometry'])
  # Strip optional elevation coordinate; geographic projection is 2D.
  g=transform(lambda x,y,z=None:proj.transform(x,y),g).intersection(bounds)
  if not g.is_empty:groups[name.replace(' River','')].append(g)
 for name,parts in groups.items():
  merged=unary_union(parts)
  if merged.geom_type=='MultiLineString':merged=linemerge(merged)
  for line in merged.geoms if hasattr(merged,'geoms') else [merged]:
   if not isinstance(line,LineString) or line.length<3000:continue
   source_rivers.append({'name':name,'seasonal':False,'points':np.round(np.array(line.simplify(1000).coords),1).tolist()})
   rawgroups[name].append(line)
# Natural Earth leaves several major courses unnamed. Match substantial overlap
# with named NHD courses; keep unmatched tributaries distinct for watershed checks.
unnamed=rawgroups.pop('Unnamed tributary',[])
for idx,g in enumerate(unnamed,1):
 matches=[]
 for n,parts in rawgroups.items():
  h=unary_union(parts)
  fraction=g.intersection(h.buffer(P*.3)).length/max(g.length,1)
  reciprocal=h.intersection(g.buffer(P*.3)).length/max(h.length,1)
  if fraction>.65 and reciprocal>.65:matches.append((fraction+reciprocal,n))
 name=max(matches)[1] if matches else f'Unnamed tributary {idx:02d}'
 rawgroups[name].append(g)
 for r in source_rivers:
  if r['name']=='Unnamed tributary' and g.hausdorff_distance(LineString(r['points']))<P*.1:r['name']=name
selected={};river_routes=[]
# Merge reservoir centerlines and split source segments before rasterization.
lines=[]
for name,gs in rawgroups.items():
 # Preserve complete source courses: noding overlapping NE/NHD copies fragments them.
 g=linemerge(gs) if len(gs)>1 else gs[0]
 for l in g.geoms if hasattr(g,'geoms') else [g]:
  if not isinstance(l,LineString):continue
  dry=l.difference(raster_lake_union)
  for part in dry.geoms if hasattr(dry,'geoms') else [dry]:
   if isinstance(part,LineString) and part.length>P*.6:lines.append((name,part))
lines.sort(key=lambda t:-t[1].length)

name_geom={n:unary_union(gs) for n,gs in rawgroups.items()}
# Known drainage families prevent headwaters in adjacent coastal watersheds or
# opposite sides of the Sierra divide from becoming false confluences at this scale.
basin_family={}
for family,names in {
 'Sacramento':['Sacramento','Pit','Feather','North Fork Feather','Yuba','North Yuba','American','North Fork American','S.  Fk.  American','Mokelumne','Cosumnes'],
 'San Joaquin':['San Joaquin','Kings','Fresno Slough','Merced','Stanislaus','Tuolumne'],
 'Klamath':['Klamath','Trinity','Sprague'],
 'Eel':['Eel','North Fork Eel'],
 'Colorado':['Colorado','Bill Williams','Gila','Salt','Verde','Hardy','Virgin','Muddy'],
 'Humboldt':['Humboldt','Reese'],
 'Salton':['New','Alamo'],
 'Walker':['Walker','East Walker','West Walker'],
 'Carson':['Carson','East Fork Carson','West Fork Carson'],
 'Sevier':['Sevier','San Pitch']}.items():
 for name in names:basin_family[name]=family
def same_basin(a,b):return basin_family.get(a,a)==basin_family.get(b,b)

def route(name,line,start_rank=0,end_rank=0,alternate=False):
 # Dijkstra follows the entire real line; distance penalty keeps paths in its corridor.
 coords=np.array(line.coords)
 # Distinct nearby watersheds must not share a coarse-grid vertex accidentally.
 occupied=collections.defaultdict(set)
 for ei,d in selected.items():
  for u in [edges[ei]['u'],edges[ei]['v']]:occupied[u].add(d['name'])
 allowed={}
 for u,names in occupied.items():
  local=Point(va[u]).buffer(P*1.5)
  allowed[u]=all(n==name or (same_basin(n,name) and name_geom[name].intersection(local).distance(name_geom[n].intersection(local))<500) for n in names)
 # Watershed divides must survive coarse shoreline snapping. In particular,
 # the Carson forks flow east of Tahoe and must never gain a Tahoe connection.
 excluded_lakes={'Carson':{'Tahoe'},'Walker':{'Tahoe','Lahontan Reservoir'},'Truckee':{'Walker','Lahontan Reservoir'}}.get(basin_family.get(name,name),set())
 if excluded_lakes:
  for edge in edges:
   if any(lake_names.get(i) in excluded_lakes for i in edge['tiles']):
    allowed[edge['u']]=False;allowed[edge['v']]=False
 def nearest_available(p,rank):
  _,indices=vkd.query(p,k=18)
  available=[int(validnodes[j]) for j in indices if allowed.get(int(validnodes[j]),True)]
  return available[min(rank,len(available)-1)] if available else int(validnodes[indices[0]])
 start=nearest_available(coords[0],start_rank);end=nearest_available(coords[-1],end_rank)
 # Join real confluences to previously snapped rivers within one hex.
 for which in [0,1]:
  p=coords[0 if which==0 else -1]
  if selected and not alternate:
   used=set(v for ei in selected for v in (edges[ei]['u'],edges[ei]['v']))
   near=[]
   local=Point(p).buffer(P*1.4)
   for v in used:
    if np.linalg.norm(va[v]-p)>=P*.70 or not allowed.get(v,True):continue
    touching={selected[ei]['name'] for _,ei in vadj[v] if ei in selected}
    if any(n==name or (same_basin(n,name) and name_geom[name].intersection(local).distance(name_geom[n].intersection(local))<500) for n in touching):near.append(v)
   if near:
    v=min(near,key=lambda v:np.linalg.norm(va[v]-p))
    if which==0:start=v
    else:end=v
 # A mapped mouth at a sea/lake shore must terminate at a shoreline vertex.
 for which in [0,1]:
  p=Point(coords[0 if which==0 else -1])
  at_grid_lake_mouth=raster_lake_union.boundary.distance(p)<2
  if not alternate and (at_grid_lake_mouth or min(land.boundary.distance(p),lake_union.distance(p))<P*.12):
   coastal=land.boundary.distance(p)<raster_lake_union.distance(p)
   nodes,tree=(sea_nodes,sea_kd) if coastal else (shore_nodes,shore_kd)
   distshore,idx=tree.query([p.x,p.y])
   if distshore<P*1.4 and allowed.get(int(nodes[idx]),True):
    if which==0:start=int(nodes[idx])
    else:end=int(nodes[idx])
 if start==end:return []
 dist={start:0};prev={};queue=[(0,start)];maxdist=P*2.5
 while queue:
  cost,u=heapq.heappop(queue)
  if cost!=dist.get(u):continue
  if u==end:break
  for v,ei in vadj[u]:
   if not allowed.get(v,True):continue
   d=line.distance(Point(mid[ei]))
   if d>maxdist:continue
   weight=1+8*(d/P)**2
   nc=cost+weight
   if nc<dist.get(v,1e30):dist[v]=nc;prev[v]=(u,ei);heapq.heappush(queue,(nc,v))
 if end not in dist:return []
 result=[];u=end
 while u!=start:u0,ei=prev[u];result.append(ei);u=u0
 return result[::-1]
failed=[];endpoint_adjustments=[]
for name,line in lines:
 path=route(name,line)
 if not path:
  alternatives=10 if name=='East Fork Carson' else 4
  for a,b in sorted(((a,b) for a in range(alternatives) for b in range(alternatives)),key=lambda p:sum(p)):
   path=route(name,line,a,b,True)
   if path:
    endpoint_adjustments.append({'name':name,'length_km':round(line.length/1000,1),'start_alternative':a,'end_alternative':b});break
 if not path:failed.append({'name':name,'length_km':round(line.length/1000,1)});continue
 for ei in path:
  if ei not in selected:selected[ei]={'name':name,'error':line.distance(Point(mid[ei]))}
 river_routes.append({'name':name,'edges':path})
# Reconnect sub-tile digitization gaps at genuine shared river courses/confluences.
# Lake/ocean mouths remain separate edges; water bodies provide the connection.
river_union=unary_union([g for gs in rawgroups.values() for g in gs])
name_geom={n:unary_union(gs) for n,gs in rawgroups.items()}
gap_links=[]
for iteration in range(80):
 graph=collections.defaultdict(list)
 for ei,d in selected.items():
  edge=edges[ei];graph[edge['u']].append((edge['v'],ei));graph[edge['v']].append((edge['u'],ei))
 components_of={};cc=0
 for v in graph:
  if v in components_of:continue
  todo=[v];components_of[v]=cc
  while todo:
   u=todo.pop()
   for v2,ei in graph[u]:
    if v2 not in components_of:components_of[v2]=cc;todo.append(v2)
  cc+=1
 ends=[v for v in graph if len(graph[v])==1 and v not in vwater]
 allnodes=np.array(list(graph));tree=cKDTree(va[allnodes]);candidates=[]
 for u in ends:
  name1=selected[graph[u][0][1]]['name']
  for idx in tree.query_ball_point(va[u],P*1.65):
   v=int(allnodes[idx])
   if components_of[u]==components_of[v] or v in vwater:continue
   name2=selected[graph[v][0][1]]['name']
   if not same_basin(name1,name2):continue
   segment=LineString([va[u],va[v]])
   if any(river_union.distance(segment.interpolate(f,normalized=True))>P*.6 for f in [.25,.5,.75]):continue
   region=segment.buffer(P)
   if name1!=name2 and name_geom[name1].intersection(region).distance(name_geom[name2].intersection(region))>500:continue
   candidates.append((np.linalg.norm(va[u]-va[v]),u,v,name1,name2))
 linked=False
 for distance,start,end,n1,n2 in sorted(candidates):
  corridor=LineString([va[start],va[end]]);q=[(0,start)];distances={start:0};prev={}
  while q:
   cost,u=heapq.heappop(q)
   if cost!=distances.get(u):continue
   if u==end:break
   for v,ei in vadj[u]:
    if corridor.distance(Point(mid[ei]))>P*.8:continue
    if v in graph and components_of[v] not in [components_of[start],components_of[end]]:continue
    d=river_union.distance(Point(mid[ei]))
    if d>P*.75:continue
    nc=cost+1+8*(d/P)**2
    if nc<distances.get(v,1e30):distances[v]=nc;prev[v]=(u,ei);heapq.heappush(q,(nc,v))
  if end not in distances:continue
  path=[];u=end
  while u!=start:u0,ei=prev[u];path.append(ei);u=u0
  if len(path)>6:continue
  name=n1 if name_geom[n1].length>name_geom[n2].length else n2
  new=0
  for ei in path:
   if ei not in selected:selected[ei]={'name':name,'error':river_union.distance(Point(mid[ei]))};new+=1
  if new:
   gap_links.append({'from':n1,'to':n2,'new_edges':new,'gap_km':round(distance/1000,2)});linked=True;break
 if not linked:break
print('Reconnected river gaps:',len(gap_links),flush=True)
# Remove rare snapping loops using a minimum-error spanning forest.
parent=list(range(len(va)))
def root(u):
 while parent[u]!=u:parent[u]=parent[parent[u]];u=parent[u]
 return u
removed=[]
for ei in sorted(selected,key=lambda ei:selected[ei]['error']):
 e=edges[ei];a,b=root(e['u']),root(e['v'])
 if a==b:removed.append(ei)
 else:parent[a]=b
for ei in removed:del selected[ei]
# Southern coastal river density is deliberately generalized for semi-arid play.
# Remove smaller complete systems, then prune headwater leaves, never middle edges.
socal_box=(-120.7,32.5,-116.4,34.85)
def is_socal(ei):
 lon,lat=inv.transform(*mid[ei]);return socal_box[0]<lon<socal_box[2] and socal_box[1]<lat<socal_box[3]
# San Diego's source mouth falls just inland of the rasterized coast. Preserve
# its final one-edge link to the ocean before shortening any upper courses.
sd_mouth=next(ei for ei,e in enumerate(edges) if e['i']==689 and e['side']=='NW')
assert all(landmask[i] for i in edges[sd_mouth]['tiles'])
selected[sd_mouth]={'name':'San Diego','error':name_geom['San Diego'].distance(Point(mid[sd_mouth]))}
socal_before={ei for ei in selected if is_socal(ei)}
socal_removed=[]
minor_coastal={'Otay','Sweetwater','Santa Margarita','Ventura','San Gabriel'}
for ei in list(selected):
 if ei in socal_before and selected[ei]['name'] in minor_coastal:
  socal_removed.append({'edge':ei,'name':selected[ei]['name'],'reason':'Omitted smaller coastal system'});del selected[ei]
target_socal=round(len(socal_before)*.5)
while sum(ei in selected for ei in socal_before)>target_socal:
 degree=collections.Counter(v for ei in selected for v in [edges[ei]['u'],edges[ei]['v']])
 counts=collections.Counter(d['name'] for ei,d in selected.items() if ei in socal_before)
 candidates=[]
 for ei in socal_before.intersection(selected):
  e=edges[ei];n=selected[ei]['name']
  if counts[n]<=3:continue
  for v in [e['u'],e['v']]:
   if degree[v]==1 and v not in vwater:
    candidates.append((counts[n],float(sea_kd.query(va[v])[0]),ei))
 if not candidates:break
 ei=max(candidates)[2];socal_removed.append({'edge':ei,'name':selected[ei]['name'],'reason':'Upstream leaf pruning'});del selected[ei]
socal_audit={'bbox':socal_box,'before_edges':len(socal_before),'after_edges':sum(ei in selected for ei in socal_before),'removed':socal_removed,'method':'Whole smaller coastal systems omitted; upstream leaves pruned; source overlay retained'}

rg=collections.defaultdict(list)
for ei in selected:
 e=edges[ei];rg[e['u']].append((e['v'],ei));rg[e['v']].append((e['u'],ei))
# Flow each connected drainage toward its lowest mouth, preferring shoreline vertices.
vwater=set()
for e in edges:
 if any(not landmask[i] for i in e['tiles']):vwater.update([e['u'],e['v']])
vll=np.array(inv.transform(va[:,0],va[:,1])).T;vz=dem(vll[:,0],vll[:,1]);seen=set();components=[]
for v in rg:
 if v in seen:continue
 comp=[];todo=[v];seen.add(v)
 while todo:
  u=todo.pop();comp.append(u)
  for a,ei in rg[u]:
   if a not in seen:seen.add(a);todo.append(a)
 shore=[u for u in comp if u in vwater]
 ends=[u for u in comp if len(rg[u])==1]
 sink=min(set(shore+ends) or comp,key=lambda u:vz[u]);todo=[sink];depth={sink:0}
 while todo:
  u=todo.pop()
  for a,ei in rg[u]:
   if a in depth:continue
   depth[a]=depth[u]+1;todo.append(a)
   # a flows into u: north=0, northeast=1, southeast=2, south=3, southwest=4,northwest=5.
   dx,dy=va[u]-va[a]
   flow=(0 if dy>0 else 3) if abs(dx)<1 else (1 if dy>0 else 2) if dx>0 else (5 if dy>0 else 4)
   selected[ei]['flow']=flow;selected[ei]['from']=a;selected[ei]['to']=u
 components.append({'nodes':len(comp),'mouth':va[sink].tolist(),'coastal_or_lake':sink in vwater})
# Marshes at actual delta / valley wetlands, no artificial jungle or ice.
for i in range(W*H):
 lon,lat=ll[i]
 if terrain[i]=='TERRAIN_GRASS' and ((-121.85<lon<-121.35 and 37.85<lat<38.25) or (39.0<lat<39.8 and -122.05<lon<-121.8)):
  features[i]='FEATURE_MARSH'
# Floodplain fertility follows flat alluvial river banks, concentrated in the
# Sacramento/San Joaquin valleys and lower Colorado; no flattening of hills.
riverplots=set(i for ei in selected for i in edges[ei]['tiles'])
fp_candidates=set()
for i in riverplots:
 if terrain[i] not in ['TERRAIN_GRASS','TERRAIN_PLAINS','TERRAIN_DESERT']:continue
 e=eco[i];lon,lat=ll[i]
 central=e=='Central California Valley'
 lower_colorado=('Sonoran' in e or 'Mojave' in e or 'Baja' in e) and z[i]<450 and relief[i]<180
 coastal=('Coast' in e or 'Foothills' in e) and z[i]<350 and relief[i]<160
 basin=('Basin and Range' in e) and relief[i]<95
 nevada_ag = (38.65<lat<40.2 and -120.0<lon<-118.15 or 40.15<lat<41.25 and -118.5<lon<-115.0) and 'Basin and Range' in e and local_relief[i]<180
 mapped_ag_floor=any(i in v['tiles'] for v in valley_edits if v['name'] in ['Smith Valley','Mason Valley','Carson Valley'])
 if central or lower_colorado or coastal or basin or nevada_ag or mapped_ag_floor:fp_candidates.add(i)
# Contiguous groups of >=3 are more useful in GS than isolated floodplain hexes.
seen_fp=set()
for i in sorted(fp_candidates):
 if i in seen_fp:continue
 group=[];todo=[i];seen_fp.add(i)
 while todo:
  u=todo.pop();group.append(u)
  for v in padj[u]:
   if v in fp_candidates and v not in seen_fp:seen_fp.add(v);todo.append(v)
 if len(group)>=3:
  for u in group:
   features[u]={'TERRAIN_GRASS':'FEATURE_FLOODPLAINS_GRASSLAND','TERRAIN_PLAINS':'FEATURE_FLOODPLAINS_PLAINS','TERRAIN_DESERT':'FEATURE_FLOODPLAINS'}[terrain[u]]

# Yosemite retains measured Sierra Nevada terrain; the game's two-tile wonder would
# require clearing its real river edges and flattening nearby mountain terrain.

# Resource legality is derived from shipped XML rather than guessed numeric IDs.
rules=json.loads((ROOT/'resource_rules.json').read_text())
rterr=collections.defaultdict(set,{k:set(v) for k,v in rules['terrains'].items()});rfeat=collections.defaultdict(set,{k:set(v) for k,v in rules['features'].items()})
# Gathering Storm resource additions (see reference source and rules documentation).
rfeat['RESOURCE_RICE'].add('FEATURE_FLOODPLAINS_GRASSLAND')
rfeat['RESOURCE_WHEAT'].add('FEATURE_FLOODPLAINS_PLAINS')
rfeat['RESOURCE_NITER'].update(['FEATURE_FLOODPLAINS_GRASSLAND','FEATURE_FLOODPLAINS_PLAINS'])
resources={}
# Diverse but regionally plausible foods, minerals and strategic resources.
weights={'FISH':9,'CRABS':2,'WHALES':1,'WHEAT':7,'CATTLE':5,'SHEEP':6,'DEER':7,'RICE':2,'STONE':6,'COPPER':5,'WINE':3,'CITRUS':2,'SALT':3,'GYPSUM':2,'SILVER':3,'MERCURY':2,'MARBLE':1,'TRUFFLES':2,'HORSES':4,'IRON':5,'NITER':4,'COAL':4,'OIL':4,'ALUMINUM':4,'URANIUM':2}
strategic={'HORSES','IRON','NITER','COAL','OIL','ALUMINUM','URANIUM'}
def eligible(i,r):
 f=features.get(i)
 if f and f not in rfeat[r]:return False
 return (f in rfeat[r]) if f else terrain[i] in rterr[r]
for i in range(W*H):
 if 'MOUNTAIN' in terrain[i] or terrain[i]=='TERRAIN_OCEAN':continue
 if rng.random()>(.27 if landmask[i] else .20):continue
 opts=[k for k in weights if eligible(i,'RESOURCE_'+k)]
 if opts:
  k=rng.choices(opts,[weights[k] for k in opts])[0];resources[i]=('RESOURCE_'+k,2 if k in strategic else 1)
# Regional strategic distribution; balance without terraforming geography.
for by in range(0,H,22):
 for bx in range(0,W,20):
  ids=[y*W+x for y in range(by,min(by+22,H)) for x in range(bx,min(bx+20,W)) if landmask[y*W+x]]
  if len(ids)<65:continue
  for k in sorted(strategic):
   if any(resources.get(i,('',0))[0]=='RESOURCE_'+k for i in ids):continue
   avail=[i for i in ids if i not in resources and eligible(i,'RESOURCE_'+k)]
   if avail:resources[rng.choice(avail)]=('RESOURCE_'+k,2)

# Generic start recommendations are added by balance_starts.py.
riverplots=set(i for ei in selected for i in edges[ei]['tiles']);starts=[]
# Tribal villages spaced far enough to avoid clumping.
goodies=[]
for i in rng.sample(list(range(W*H)),W*H):
 if len(goodies)>=65:break
 if landmask[i] and 'MOUNTAIN' not in terrain[i] and i not in features and i not in resources and all(np.linalg.norm(xy[i]-xy[j])>P*4 for j in goodies) and all(np.linalg.norm(xy[i]-xy[s['id']])>P*2 for s in starts):goodies.append(i)

rrows={}
for ei,d in selected.items():
 e=edges[ei];row=rrows.setdefault(e['i'],[e['i'],0,0,0,-1,-1,-1]);side=e['side']
 flag,flow={'W':(2,4),'NW':(3,5),'NE':(1,6)}[side];row[flag]=1;row[flow]=d['flow']

# Build from the real WorldBuilder schema, clearing all inherited content and DLC dependencies.
schema=(ROOT/'schema.sql').read_text()
for edition,ruleset,uid in [('GatheringStorm','RULESET_EXPANSION_2','AACA6192-0284-4288-9000-619202600002')]:
 path=OUT/f'California_{edition}.Civ6Map'
 if path.exists():path.unlink()
 c=sqlite3.connect(path);c.executescript(schema)
 c.execute('INSERT INTO Map VALUES(?,?,?,?,?,?,?,?)',('Default',W,H,43,31,0,0,'MAPSIZE_HUGE'))
 c.executemany('INSERT INTO MapAttributes VALUES(?,?)',[('MapScript','WorldBuilderMap.lua'),('Ruleset',ruleset)])
 c.executemany('INSERT INTO Plots VALUES(?,?,?,?)',[(i,terrain[i],'CONTINENT_NORTH_AMERICA' if landmask[i] else '',int('MOUNTAIN' in terrain[i])) for i in range(W*H)])
 c.executemany('INSERT INTO PlotFeatures VALUES(?,?)',features.items())
 c.executemany('INSERT INTO PlotResources VALUES(?,?,?)',[(i,*r) for i,r in resources.items()])
 c.executemany('INSERT INTO PlotRivers VALUES(?,?,?,?,?,?,?)',rrows.values())
 c.executemany('INSERT INTO PlotImprovements VALUES(?,?,?)',[(i,'IMPROVEMENT_GOODY_HUT',-1) for i in goodies])
 short=uid.replace('-',''); prefix='LOC_'+short
 name='California — Huge ('+('Base Game' if edition=='Base' else 'Gathering Storm')+')'
 desc='80 × 88. Real coastlines, elevation-derived terrain, mapped rivers; balanced resources. No world wrap.'
 c.executemany('INSERT INTO MetaData VALUES(?,?)',[('MetaDataVersion','1'),('AppVersion','1.0.12.43 (899997)'),('DisplayName',name),('ID',uid),('IsMod','1'),('LastUpdated','1789776000')])
 c.executemany('INSERT INTO ModProperties VALUES(?,?)',[('ID',uid),('Version','1'),('DBVersion','3'),('Name',prefix+'_MOD_TITLE'),('Type','WorldBuilderMap'),('Description',prefix+'_MOD_DESCRIPTION')])
 c.execute('INSERT INTO ModSettings VALUES(?,?)',('WorldBuilder','WORLDBUILDER'))
 c.execute('INSERT INTO ModSettings_Items VALUES(?,?,?,?)',('WorldBuilder','WORLDBUILDER','File','[self]'))
 c.executemany('INSERT INTO ModSettings_Properties VALUES(?,?,?,?)',[('WorldBuilder','WORLDBUILDER','Name',prefix+'_MAP_NAME'),('WorldBuilder','WORLDBUILDER','Description',prefix+'_MAP_DESCRIPTION')])
 for lang in ['en_US','fr_FR','de_DE','es_ES','it_IT','ja_JP','ko_KR','pl_PL','pt_BR','ru_RU','zh_Hans_CN','zh_Hant_HK']:
  c.executemany('INSERT INTO ModText VALUES(?,?,?)',[(lang,prefix+'_MOD_TITLE',name),(lang,prefix+'_MOD_DESCRIPTION',desc),(lang,prefix+'_MAP_NAME',name),(lang,prefix+'_MAP_DESCRIPTION',desc)])
 if edition=='GatheringStorm':c.execute('INSERT INTO ModDependencies VALUES(?,?)',('4873eb62-8ccc-4574-b784-dda455e74e68','{"LOC_EXPANSION2_MOD_TITLE":[]}'))
 c.commit();c.execute('VACUUM');c.close()

# Exact game data and projected source overlays for an independent viewer.
def normalized(points):return [[round((x-X0)/P,4),round((y-Y0)/P,4)] for x,y in points]
def geolines(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [normalized(g.exterior.simplify(900).coords)]
 if g.geom_type=='LineString':return [normalized(g.simplify(900).coords)]
 return [l for p in g.geoms for l in geolines(p)]
preview={'width':W,'height':H,'pitch_km':P/1000,'projection':'EPSG:3310 California Albers','tiles':[],
 'rivers':[],'sourceRivers':[dict(name=r['name'],seasonal=r['seasonal'],points=normalized(r['points'])) for r in source_rivers],
 'boundaries':[{'name':d['name'],'paths':geolines(g.intersection(bounds))} for d,g in states],
 'coastlines':geolines(land.intersection(bounds)), 'starts':starts,'lakes':[{'name':n,'paths':geolines(g.intersection(bounds))} for n,g in lakes if g.intersects(bounds)],
 'stats':{},'notes':{'island_minimum_hexes':island_edits,'straits_minimum_hexes':strait_edits,'unrouted_segments':failed,'cycle_edges_removed':len(removed),'river_components':components,'river_gap_repairs':gap_links,'river_endpoint_adjustments':endpoint_adjustments,'peninsula_land_connections':peninsula_edits,'valley_corridors':valley_edits,'lake_connectors':lake_connectors,'tahoe_terrain_corrections':tahoe_edits,'lassen_mountain':lassen_id,'forest_audit':forest_edits,'southern_coastal_river_density':socal_audit}}
for i in range(W*H):
 preview['tiles'].append({'id':i,'terrain':terrain[i].replace('TERRAIN_',''),'feature':features.get(i,'').replace('FEATURE_',''),'resource':resources.get(i,('',0))[0].replace('RESOURCE_',''),'quantity':resources.get(i,('',0))[1],'elevation':round(z[i]),'relief':round(relief[i]),'local_relief':round(local_relief[i]),'forest_reference_percent':round(float(forest_fraction[i])*100,1) if valid_samples[i]>=20 else None,'lat':round(ll[i,1],5),'lon':round(ll[i,0],5),'ecoregion':eco[i],'lake':lake_names.get(i,''),'california':cal.contains(Point(xy[i])),'goody':i in goodies})
for ei,d in selected.items():
 e=edges[ei];preview['rivers'].append({'plot':e['i'],'side':e['side'],'flow':d['flow'],'name':d['name'],'points':normalized([va[d['from']],va[d['to']]]),'offset_km':round(d['error']/1000,2)})
preview['stats']={'tiles':W*H,'land':int(sum(landmask)),'water':int(sum(~landmask)),'mountains':sum('MOUNTAIN' in t for t in terrain),'hills':sum('HILLS' in t for t in terrain),'forests':sum(f=='FEATURE_FOREST' for f in features.values()),'floodplains':sum(f.startswith('FEATURE_FLOODPLAINS') for f in features.values()),'river_edges':len(selected),'river_names':len(set(d['name'] for d in selected.values())),'resource_tiles':len(resources),'goody_huts':len(goodies),'median_river_offset_km':round(float(np.median([d['error']/1000 for d in selected.values()])),2),'max_river_offset_km':round(max(d['error']/1000 for d in selected.values()),2),'california_polygon_contained':bool(bounds.contains(cal))}
preview['resource_catalog']=json.loads((OUT/'resource_catalog.json').read_text())
(OUT/'map_data.json').write_text(json.dumps(preview,separators=(',',':')))
(OUT/'resource_rules.json').write_text(json.dumps({'terrains':{k:sorted(v) for k,v in rterr.items()},'features':{k:sorted(v) for k,v in rfeat.items()}},indent=2))
print(json.dumps(preview['stats'],indent=2));print('Unrouted:',failed)
