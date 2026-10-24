import requests,pathlib,math,concurrent.futures,zipfile,io
p=pathlib.Path('work/hawaii/data');(p/'dem').mkdir(exist_ok=True)
def get_dem(t):
 z,x,y=t;f=p/'dem'/f'{z}-{x}-{y}.png'
 if not f.exists():
  r=requests.get(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',timeout=60);r.raise_for_status();f.write_bytes(r.content)
 return f.name
def grid():
 f=p/'rainfall.zip'
 if not f.exists():
  r=requests.get('https://atlas.uhtapis.org/rainfall/assets/files/GISLayers/StateASCIIGrids_mm.zip',timeout=180);r.raise_for_status();f.write_bytes(r.content)
 with zipfile.ZipFile(f) as z:
  names=z.namelist();print('Rainfall archive',names[:30],flush=True)
  for n in names:
   if 'annual' in n.lower():z.extract(n,p/'rainfall')
 return 'rainfall'
def rivers():
 f=p/'rivers.json'
 if not f.exists():
  q={'f':'geojson','where':"GNIS_NAME IS NOT NULL AND FTYPE = 460",'geometry':'-160.4,18.8,-154.7,22.5','geometryType':'esriGeometryEnvelope','inSR':4326,'outSR':4326,'outFields':'GNIS_NAME,FCODE','resultRecordCount':10000}
  r=requests.get('https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6/query',params=q,timeout=120);r.raise_for_status();f.write_text(r.text)
 d=__import__('json').loads(f.read_text());print('Rivers',len(d.get('features',[])),d.keys(),flush=True);return 'rivers'
z=9;ty=lambda lat:int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
coords=[(z,x,y) for x in range(int((-161+180)/360*2**z),int((-153.8+180)/360*2**z)+1) for y in range(ty(23),ty(18)+1)]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as e:
 fs=[e.submit(get_dem,t) for t in coords]+[e.submit(grid),e.submit(rivers)]
 for f in concurrent.futures.as_completed(fs):print(f.result(),flush=True)
