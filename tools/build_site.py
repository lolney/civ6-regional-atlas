#!/usr/bin/env python3
"""Build a portable static atlas and reproducible download bundles. No dependencies."""
from pathlib import Path
import hashlib,json,shutil,zipfile,re,sqlite3
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'site'
MAPS=[
 dict(id='california-modern',region='California',epoch='Modern',folder='california-modern',data='map_data.json',file='California_GatheringStorm.Civ6Map',size='Huge',description='Pacific coast, Sierra Nevada, fertile valleys, and the Basin and Range.',query=''),
 dict(id='california-lgm',region='California',epoch='Last Glacial Maximum',folder='california-lgm',data='map_data.json',file='California_LastGlacialMaximum.Civ6Map',size='Huge',description='Lower seas, pluvial lakes, shifted woodlands, and Sierra glaciers.',query='?epoch=lgm'),
 dict(id='hawaii-modern',region='Hawaiʻi',epoch='Modern',folder='hawaii',data='modern_data.json',file='Hawaii_Modern.Civ6Map',size='Standard',description='Eight main islands, volcanic summits, wet windward forests, and dry leeward slopes.',query='?epoch=modern'),
 dict(id='hawaii-lgm',region='Hawaiʻi',epoch='Last Glacial Maximum',folder='hawaii',data='lgm_data.json',file='Hawaii_LGM.Civ6Map',size='Standard',description='Expanded shores, connected Maui Nui, cooler biomes, and Mauna Kea’s ice cap.',query='?epoch=lgm'),
]
def archive(folder,target):
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f in sorted(folder.rglob('*')):
   if not f.is_file() or '__pycache__' in f.parts or f.suffix=='.pyc' or f.name=='.DS_Store':continue
   info=zipfile.ZipInfo((Path(folder.name)/f.relative_to(folder)).as_posix(),(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,f.read_bytes())
def preview(d,target):
 # Exact map geometry, drawn as a compact vector preview rather than a decorative image.
 import math
 w,h=d['width'],d['height'];Y=(h-1)*math.sqrt(3)/2;parts=[];colors={'OCEAN':'#16394c','COAST':'#4d8393','GRASS':'#90ac71','PLAINS':'#beac77','DESERT':'#dcc49a','TUNDRA':'#a9b2a7','SNOW':'#e9eeee'}
 for t in d['tiles']:
  if t['terrain']=='OCEAN':continue
  i=t['id'];x=i%w+.5*((i//w)%2);y=Y-i//w*math.sqrt(3)/2
  pts=' '.join(f'{x+math.cos(math.radians(90-j*60))/math.sqrt(3):.2f},{y-math.sin(math.radians(90-j*60))/math.sqrt(3):.2f}' for j in range(6));c=colors[t['terrain'].split('_')[0]]
  if t.get('glacier'):c='#d0f4ff'
  elif t['terrain'].endswith('MOUNTAIN'):c='#6a7465'
  elif t['feature'] in ['FOREST','JUNGLE']:c='#4b7757'
  parts.append(f'<polygon points="{pts}" fill="{c}"/>')
 for r in d['rivers']:
  pts=' '.join(f'{x:.2f},{Y-y:.2f}' for x,y in r['points']);parts.append(f'<polyline points="{pts}" fill="none" stroke="#80ceee" stroke-width=".14"/>')
 target.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 {w+1} {Y+2}" role="img"><title>{target.stem.replace("-"," ")}</title><rect x="-1" y="-1" width="{w+1}" height="{Y+2}" fill="#16394c"/>'+''.join(parts)+'</svg>')
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir();(OUT/'downloads').mkdir();(OUT/'previews').mkdir();(OUT/'maps').mkdir()
for folder in sorted({m['folder'] for m in MAPS}):
 src=ROOT/'maps'/folder
 shutil.copytree(src,OUT/'maps'/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
 archive(src,OUT/'downloads'/(folder+'-source.zip'))
 # Inspector navigation is owned by the atlas while embedded; standalone downloads retain the originals.
 path=OUT/'maps'/folder/'inspect.html';html=path.read_text()
 extra='''<script>(()=>{if(!new URLSearchParams(location.search).has('embedded'))return;const s=document.createElement('style');s.textContent='header{display:none!important}main{height:100vh;min-height:0}@media(max-width:760px){main{height:auto}#stage{height:72vh}}';document.head.append(s);const e=document.getElementById('epoch');if(e){e.style.display='none';if(e.previousElementSibling)e.previousElementSibling.style.display='none';if(e.nextElementSibling)e.nextElementSibling.style.display='none';}})();</script>'''
 path.write_text(html.replace('</body>',extra+'</body>'))
manifest=[]
for m in MAPS:
 src=ROOT/'maps'/m['folder'];d=json.loads((src/m['data']).read_text());native=src/m['file'];c=sqlite3.connect(native);assert c.execute('SELECT count(*) FROM Plots').fetchone()[0]==d['width']*d['height'];c.close()
 preview(d,OUT/'previews'/(m['id']+'.svg'))
 manifest.append({**m,'width':d['width'],'height':d['height'],'stats':d['stats'],'native_url':f'maps/{m["folder"]}/{m["file"]}','inspector_url':f'maps/{m["folder"]}/inspect.html{m["query"]}','package_url':f'downloads/{m["folder"]}-source.zip','preview_url':f'previews/{m["id"]}.svg','readme_url':f'maps/{m["folder"]}/README.md','sources_url':f'maps/{m["folder"]}/SOURCES.md','sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'bytes':native.stat().st_size})
# All native maps in one light download, with installation and attribution documents.
with zipfile.ZipFile(OUT/'downloads/all-native-maps.zip','w',zipfile.ZIP_DEFLATED) as z:
 for m in MAPS:
  z.write(ROOT/'maps'/m['folder']/m['file'],m['file'])
 for name in ['README.md','LICENSE','NOTICE.md']:z.write(ROOT/name,name)
(OUT/'maps.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
for f in (ROOT/'web').iterdir():
 if f.is_file():shutil.copyfile(f,OUT/f.name)
(OUT/'.nojekyll').write_text('')
checksums={m['file']:m['sha256'] for m in manifest};(OUT/'downloads/SHA256SUMS.txt').write_text('\n'.join(f'{v}  {k}' for k,v in checksums.items())+'\n')
print(f'Built {len(manifest)} maps in {OUT}; {sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())/1e6:.1f} MB')
