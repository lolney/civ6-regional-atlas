import requests,json,pathlib,collections
p=pathlib.Path('work/hawaii/data');f=p/'major_rivers.json'
if not f.exists():
 names=['Wailuku River','Waimea River','Hanalei River','North Fork Wailua River','South Fork Wailua River','ʻĪao Stream','Hakalau Stream','Wainiha River','Hālawa Stream','Waipiʻo Stream','Hanawī Stream','Kīpapa Stream','ʻŌpaeʻula Stream']
 q={'f':'geojson','where':'GNIS_NAME IN ('+','.join("'"+n+"'" for n in names)+')','geometry':'-160.4,18.8,-154.7,22.5','geometryType':'esriGeometryEnvelope','inSR':4326,'outSR':4326,'outFields':'GNIS_NAME,FCODE','resultRecordCount':2000}
 r=requests.get('https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6/query',params=q,timeout=120);r.raise_for_status();f.write_text(r.text)
d=json.loads(f.read_text());print(len(d.get('features',[])),d.keys());print(collections.Counter((x['properties']['gnis_name'],x['properties']['fcode']) for x in d['features']))
