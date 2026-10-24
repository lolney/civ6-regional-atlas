# Executed in the generator namespace after modern terrain preparation.
from scipy.ndimage import label
modern_landmask=landmask.copy();modern_lake_names=dict(lake_names)
# Global sea-level lowering; retain inland below-sea-level depressions as land.
landmask=contains_xy(land,xy[:,0],xy[:,1]) | (z>=-125)
lake_names={};waterkind={}
# Modern impoundments and the 1905 Salton Sea are intentionally absent.
keep={'Tahoe','Clear','Eagle','Goose','Upper Klamath','Lower Klamath','Bear'}
lakes=[(n,g) for n,g in lakes if n in keep]
for n,g in lakes:
 for i in range(W*H):
  if g.contains(Point(xy[i])) or polys[i].intersection(g).area>polys[i].area*.3:
   lake_names[i]=n;landmask[i]=False
# Preserve small source islands; combine northern Channel Islands into Santarosae.
for i in island_edits:landmask[i]=True
santarosae_line=LineString([proj.transform(*p) for p in [(-120.42,34.03),(-120.12,33.97),(-119.78,34.02),(-119.39,34.01)]])
for i in range(W*H):
 if polys[i].intersects(santarosae_line):landmask[i]=True
# Minimum-width Anacapa passage prevents a false mainland bridge.
landmask[1556]=False
# Basins are DEM-connected, not rectangle fills. Levels are scenario estimates.
# name, level m (modern datum), bbox lonlat, seed lonlat, uncertainty m
lake_specs=[
 ('Bonneville',1450,(-114.5,38.3,-111.0,42.3),(-113.0,40.8),60),
 ('Lahontan — western basins',1260,(-120.5,39.2,-118.3,41.8),(-119.55,40.1),30),
 ('Lahontan — Carson/Humboldt',1220,(-119.1,39.0,-117.4,40.9),(-118.55,39.75),35),
 ('Lahontan — Walker',1230,(-119.0,38.3,-118.3,39.15),(-118.7,38.7),40),
 ('Russell (Mono)',2073,(-119.35,37.7,-118.55,38.45),(-119.02,38.02),30),
 ('Owens',1145,(-118.35,36.2,-117.7,36.8),(-117.98,36.43),25),
 ('Searles',670,(-117.75,35.2,-117.15,36.0),(-117.4,35.7),35),
 ('Manly',0,(-117.5,35.6,-116.4,37.1),(-116.82,36.25),50),
 ('Mojave',287,(-116.35,35.0,-115.85,35.7),(-116.1,35.25),15),
 ('Honey',1240,(-120.6,39.8,-119.75,40.65),(-120.2,40.2),30),
 ('Surprise',1380,(-120.4,41.0,-119.8,42.0),(-120.12,41.55),35),
 ('Chewaucan',1320,(-121.0,42.1,-120.0,43.0),(-120.55,42.7),40),
 ('Warner',1430,(-120.05,41.9,-119.3,43.0),(-119.8,42.3),35),
 ('Franklin',1830,(-115.8,39.8,-114.9,40.8),(-115.43,40.15),30),
 ('Tulare',65,(-120.1,35.5,-119.0,36.5),(-119.7,36.0),20)]
paleo_lake_audit=[]
for name,level,bbox,seed,uncertainty in lake_specs:
 west,south,east,north=bbox
 lo,la=np.meshgrid(np.arange(west,east,.009),np.arange(south,north,.009));zz=dem(lo.ravel(),la.ravel()).reshape(lo.shape)
 mask=zz<level;labels,count=label(mask)
 # Locate the connected low point near the documented basin center.
 near=(lo-seed[0])**2+(la-seed[1])**2
 indices=np.where(mask,near,np.inf);yy,xx=np.unravel_index(indices.argmin(),indices.shape)
 region=labels==labels[yy,xx];parts=[]
 for row in range(region.shape[0]):
  ids=np.where(region[row])[0]
  for run in np.split(ids,np.where(np.diff(ids)>1)[0]+1):
   if len(run):parts.append(box(lo[row,run[0]]-.0045,la[row,0]-.0045,lo[row,run[-1]]+.0045,la[row,0]+.0045))
 g=transform(proj.transform,unary_union(parts)).intersection(bounds)
 lakes.append((name,g));ids=[]
 for i in range(W*H):
  if g.contains(Point(xy[i])) or polys[i].intersection(g).area>polys[i].area*.25:
   landmask[i]=False;lake_names[i]=name;ids.append(i)
 if not ids and not g.is_empty:
  i=int(kd.query([g.representative_point().x,g.representative_point().y])[1]);landmask[i]=False;lake_names[i]=name;ids=[i]
 paleo_lake_audit.append({'name':name,'level_m':level,'scenario_sensitivity_m':uncertainty,'bbox':bbox,'seed':seed,'plots':ids,'source_area_km2':round(g.area/1e6),'confidence':'moderate' if name in ['Bonneville','Russell (Mono)'] else 'low-to-moderate'})
 print('LGM lake',name,len(ids),flush=True)
# Assign reconstructed biomes from broad climate/elevation envelopes, not NLCD.
biomes={};glaciers={}
for i,(lon,lat) in enumerate(ll):
 features.pop(i,None)
 if not landmask[i]:terrain[i]='TERRAIN_COAST' if i in lake_names else 'TERRAIN_OCEAN';biomes[i]='Pluvial / natural lake' if i in lake_names else 'Pacific / Gulf';continue
 old=terrain[i];kind='_MOUNTAIN' if 'MOUNTAIN' in old else '_HILLS' if 'HILLS' in old else ''
 if not modern_landmask[i]:kind='_HILLS' if local_relief[i]>220 else ''
 e=eco[i];height=max(float(z[i]),0);r=random.Random(21000+i).random()
 alpine=height>max(1700,2600-(lat-35)*160)
 if alpine:base='TUNDRA';prob=.10;biome='Alpine tundra / periglacial steppe'
 elif 'Central California Valley' in e:base='PLAINS';prob=.22;biome='Cool grassland, parkland and riparian woodland'
 elif 'Basin and Range' in e or 'Plateau' in e:
  base='TUNDRA' if lat>39.5 and height>1500 else 'PLAINS';prob=.18 if height<1500 else .38;biome='Cold sagebrush steppe / open conifer woodland'
 elif any(k in e for k in ['Mojave','Sonoran','Baja']):
  base='DESERT' if height<350 else 'PLAINS';prob=0 if base=='DESERT' else .42;biome='Arid lowland scrub' if base=='DESERT' else 'Cool juniper woodland / steppe mosaic'
 elif lon<-121.5 and lat>39:base='PLAINS';prob=.76;biome='Cool conifer forest / parkland'
 elif 'Sierra' in e or 'Cascades' in e or 'Klamath' in e:base='PLAINS';prob=.74;biome='Lowered montane conifer forest belt'
 elif lon<-119 and lat>34.5:base='PLAINS';prob=.53;biome='Cool coastal woodland / grassland mosaic'
 else:base='PLAINS';prob=.4 if height>400 else .2;biome='Cool southern coastal parkland / scrub'
 terrain[i]='TERRAIN_'+base+kind;biomes[i]=biome
 if not kind.endswith('MOUNTAIN') and base!='DESERT' and r<prob:features[i]='FEATURE_FOREST'
# Mapped Yosemite Tioga polygon; mountain-belt approximations elsewhere.
gp=next((ROOT/'source_data/tioga').rglob('YOSE_glacier_extnt.shp'))
crs=CRS.from_wkt(gp.with_suffix('.prj').read_text());gt=Transformer.from_crs(crs,3310,always_xy=True)
yose_ice=unary_union([transform(gt.transform,shape(s.__geo_interface__)) for s in shapefile.Reader(str(gp)).shapes()])
sierra_axis=LineString([proj.transform(*p) for p in [(-120.85,39.8),(-120.22,39.2),(-119.95,38.6),(-119.5,38),(-118.85,37.45),(-118.6,37),(-118.3,36.55)]])
for i,(lon,lat) in enumerate(ll):
 if not landmask[i]:continue
 mapped=polys[i].intersection(yose_ice).area/polys[i].area
 near_sierra=sierra_axis.distance(Point(xy[i]))<18500 and 36.5<lat<39.9 and zmax[i]>2450 and z[i]>1750
 approximate=(near_sierra or ('Cascades' in eco[i] and z[i]>1800 and zmax[i]>2200) or ('Klamath' in eco[i] and z[i]>2000 and zmax[i]>2400) or (-115.7<lon<-115.1 and 40.1<lat<41 and z[i]>2450) or (-114.6<lon<-114.1 and 38.7<lat<39.5 and z[i]>2750) or (-120.4<lon<-120 and 41.4<lat<42 and z[i]>2400))
 # Within the detailed map's footprint, use the actual mapped ice boundary.
 if yose_ice.envelope.contains(Point(xy[i])):approximate=False
 if mapped>=.2 or approximate:
  glaciers[i]={'basis':'USGS mapped Tioga footprint' if mapped>=.2 else 'Regional elevation/range approximation','confidence':'higher' if mapped>=.2 else 'lower','mapped_fraction':round(mapped,3)}
for name,lon,lat in [('Lassen',-121.505,40.488),('Shasta',-122.195,41.409)]:
 i=int(kd.query(proj.transform(lon,lat))[1]);glaciers[i]={'basis':name+' alpine ice-cap minimum hex','confidence':'moderate','mapped_fraction':None}
for i in glaciers:terrain[i]='TERRAIN_SNOW_MOUNTAIN';features.pop(i,None);biomes[i]='Alpine glacier / icefield'
glacier_union=unary_union([polys[i] for i in glaciers])
print('LGM glacier hexes',len(glaciers),flush=True)
