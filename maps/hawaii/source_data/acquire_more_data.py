import pathlib,requests,json,zipfile
p=pathlib.Path('work/hawaii/data')
with zipfile.ZipFile(p/'rainfall.zip') as z:
 for n in z.namelist():
  if '_ann.' in n.lower():z.extract(n,p/'rainfall')
f=p/'perennial_rivers.json'
if not f.exists():
 features=[]
 for off in range(0,20000,2000):
  q={'f':'geojson','where':"GNIS_NAME IS NOT NULL AND FCODE = 46006",'geometry':'-160.4,18.8,-154.7,22.5','geometryType':'esriGeometryEnvelope','inSR':4326,'outSR':4326,'outFields':'GNIS_NAME,FCODE','resultRecordCount':2000,'resultOffset':off,'orderByFields':'OBJECTID'}
  r=requests.get('https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6/query',params=q,timeout=120);r.raise_for_status();d=r.json();features.extend(d.get('features',[]));print(off,len(d.get('features',[])),flush=True)
  if not d.get('exceededTransferLimit'):break
 f.write_text(json.dumps({'type':'FeatureCollection','features':features}))
 print('Total',len(features))
