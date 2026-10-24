from pathlib import Path
import json,math,numpy as np,shapefile
from PIL import Image
from pyproj import Transformer,CRS
from shapely.geometry import shape,box,Polygon,Point,LineString
from shapely.ops import transform,unary_union,linemerge
from scipy.spatial import cKDTree
D=Path('work/hawaii/data');O=Path('outputs/Hawaii_Civ6');(O/'source_data').mkdir(exist_ok=True)
W,H=84,54;P=9000.;DY=P*3**.5/2;R=P/3**.5;X0=-(W-.5)*P/2;Y0=-(H-1)*DY/2
crs=CRS.from_proj4('+proj=laea +lat_0=20.6 +lon_0=-157.5 +datum=WGS84 +units=m');pr=Transformer.from_crs(4326,crs,always_xy=True);iv=Transformer.from_crs(crs,4326,always_xy=True)
xy=np.array([(X0+(x+.5*(y%2))*P,Y0+y*DY) for y in range(H) for x in range(W)]);ll=np.array(iv.transform(xy[:,0],xy[:,1])).T
angles=np.radians([90,30,-30,-90,-150,150]);offsets=np.c_[np.cos(angles),np.sin(angles)]*R
polys=[Polygon(c+offsets) for c in xy];geo=box(-161,18.6,-154,22.6)
parts=[]
for s in shapefile.Reader(str(next(Path('work/data/land').glob('*.shp')))).iterShapes():
 bb=s.bbox
 if bb[2]<-161 or bb[0]>-154 or bb[3]<18.6 or bb[1]>22.6:continue
 g=shape(s.__geo_interface__)
 g=g.intersection(geo)
 if not g.is_empty:parts.append(transform(pr.transform,g))
land=unary_union(parts);islands=list(land.geoms) if hasattr(land,'geoms') else [land]
refs={'Niʻihau':(-160.155,21.89),'Kauaʻi':(-159.53,22.045),'Oʻahu':(-157.98,21.48),'Molokaʻi':(-157.03,21.14),'Lānaʻi':(-156.93,20.83),'Maui':(-156.30,20.80),'Kahoʻolawe':(-156.61,20.56),'Hawaiʻi':(-155.50,19.62)}
igs={name:min(islands,key=lambda g:g.distance(Point(pr.transform(*p)))) for name,p in refs.items()}
print('Island areas',[(n,round(g.area/1e6)) for n,g in igs.items()],flush=True)
cache={}
def elev(lon,lat):
 z=9;n=2**z;xf=(lon+180)/360*n;yf=(1-np.arcsinh(np.tan(np.radians(lat)))/np.pi)/2*n;x=int(xf);y=int(yf)
 if (x,y) not in cache:
  f=D/'dem'/f'{z}-{x}-{y}.png'
  if not f.exists():
   import requests
   response=requests.get(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',timeout=60);response.raise_for_status();f.write_bytes(response.content)
  a=np.array(Image.open(D/'dem'/f'{z}-{x}-{y}.png')).astype(float);cache[x,y]=a[:,:,0]*256+a[:,:,1]+a[:,:,2]/256-32768
 return float(cache[x,y][min(255,int((yf-y)*256)),min(255,int((xf-x)*256))])
f=D/'rainfall/rfgrid_mm_state_ann.txt';hdr={}
with f.open() as q:
 for _ in range(6):a,b=q.readline().split();hdr[a.lower()]=float(b)
rain=np.loadtxt(f,skiprows=6);step=hdr['cellsize']
def rainfall(lon,lat):
 x=int((lon-hdr['xllcorner'])/step);y=int(hdr['nrows'])-1-int((lat-hdr['yllcorner'])/step)
 if 0<=y<rain.shape[0] and 0<=x<rain.shape[1] and rain[y,x]>=0:return float(rain[y,x])
 return None
# 37 samples within the hex, including center, catches slopes and narrow land bridges.
samples=[(0,0)]+[(r*math.cos(a),r*math.sin(a)) for r,count in [(P*.18,6),(P*.33,12),(P*.48,18)] for a in np.linspace(0,2*math.pi,count,endpoint=False)]
tiles=[]
for i,(c,loc,poly) in enumerate(zip(xy,ll,polys)):
 ss=np.array(samples)+c;sl=np.array(iv.transform(ss[:,0],ss[:,1])).T
 es=[elev(*v) for v in sl];rs=[r for v in sl if (r:=rainfall(*v)) is not None]
 overlap=poly.intersection(land).area/poly.area
 isl=max(igs,key=lambda n:poly.intersection(igs[n]).area) if overlap else ''
 tiles.append({'id':i,'lon':round(loc[0],6),'lat':round(loc[1],6),'elevation':round(es[0]),'relief':round(max(es)-min(es)),'local_relief':round(max(es[:7])-min(es[:7])),'max_elevation':round(max(es)),'min_elevation':round(min(es)),'land_fraction':round(overlap,3),'island':isl,'elevation_samples':[round(z) for z in es],'rainfall_mm':round(float(np.median(rs))) if rs else None})
print('Land tiles',sum(t['land_fraction']>=.4 for t in tiles),flush=True)
# Fill a no-data coastal/sliver hex from nearby real atlas pixels; Niihau is not in atlas.
rids=[t['id'] for t in tiles if t['rainfall_mm'] is not None];tree=cKDTree(xy[rids])
for t in tiles:
 if t['rainfall_mm'] is None and t['max_elevation']>-160:
  dist,k=tree.query(xy[t['id']]);t['rainfall_mm']=tiles[rids[k]]['rainfall_mm'] if dist<30000 else 500;t['rainfall_inferred']=True
norm=lambda coords:[[round((x-X0)/P,5),round((y-Y0)/P,5)] for x,y in coords]
coast=[norm(g.exterior.simplify(400).coords) for g in islands if g.area>1e6]
groups={}
major=json.load(open(D/'major_rivers.json'))['features']
major_names={f['properties']['gnis_name'] for f in major}
flows=[f for f in json.load(open(D/'perennial_rivers.json'))['features'] if f['properties']['gnis_name'] not in major_names]+[f for f in major if f['properties']['fcode'] in [46006,55800]]
for f in flows:
 name=f['properties']['gnis_name'];g=transform(lambda x,y,z=None:pr.transform(x,y),shape(f['geometry']))
 groups.setdefault(name,[]).append(g)
sources=[]
for name,gs in groups.items():
 g=unary_union(gs)
 if g.geom_type=='MultiLineString':g=linemerge(g)
 lines=list(g.geoms) if hasattr(g,'geoms') else [g]
 for l in lines:
  if l.geom_type!='LineString' or l.length<2500:continue
  sources.append({'name':name,'length_km':round(l.length/1000,2),'seasonal':False,'points':norm(l.simplify(500).coords)})
print('River lines',len(sources),[(r['name'],r['length_km']) for r in sorted(sources,key=lambda r:-r['length_km'])[:25]],flush=True)
out={'width':W,'height':H,'pitch_km':P/1000,'projection':crs.to_proj4(),'origin_m':[X0,Y0],'tiles':tiles,'coastlines':coast,'sourceRivers':sources,'island_references':refs,'sources':{'elevation':'Mapzen Terrarium z9, mixed-source modern terrain/bathymetry','coast':'Natural Earth 1:10m land','rainfall':'Giambelluca et al. Rainfall Atlas of Hawaii, 1978–2007 mean annual, 250m','rivers':'USGS NHD named perennial streams FCODE 46006; simplified 500m'}}
(O/'source_data/grid_inputs.json').write_text(json.dumps(out,separators=(',',':')))
