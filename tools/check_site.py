#!/usr/bin/env python3
"""Check generated assets, download integrity, local links and JavaScript syntax."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,subprocess,shutil,hashlib,zipfile,tempfile,re
ROOT=Path(__file__).resolve().parent.parent;SITE=ROOT/'site'
class Assets(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.scripts=[];self.current=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ['a','link','iframe','img','script']:
   for key in ['href','src']:
    if a.get(key):self.links.append(a[key])
  if tag=='script' and a.get('type','')!='application/json' and 'src' not in a:self.current=[]
 def handle_data(self,data):
  if self.current is not None:self.current.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.current is not None:self.scripts.append(''.join(self.current));self.current=None
node=shutil.which('node')
if not node:
 candidates=sorted((Path.home()/'.nvm/versions/node').glob('*/bin/node'));node=str(candidates[-1]) if candidates else None
assert node,'Node is required for JavaScript syntax verification.'
count=0
for f in SITE.rglob('*.html'):
 if 'source_data' in f.parts or 'tools' in f.parts:continue
 a=Assets();a.feed(f.read_text())
 for href in a.links:
  u=urlsplit(href)
  if u.scheme or u.netloc or not u.path:continue
  target=(SITE/u.path.lstrip('/')) if u.path.startswith('/') else f.parent/unquote(u.path)
  assert target.exists(),f'{f.relative_to(SITE)} links to missing {href}'
 for js in a.scripts:
  with tempfile.NamedTemporaryFile(suffix='.js',mode='w') as tmp:
   tmp.write(js);tmp.flush();subprocess.run([node,'--check',tmp.name],check=True,capture_output=True)
  count+=1
for f in (SITE/'atlas.js',):subprocess.run([node,'--check',str(f)],check=True,capture_output=True)
manifest=json.loads((SITE/'maps.json').read_text());assert len(manifest)==4
for m in manifest:
 for key in ['native_url','package_url','preview_url','readme_url','sources_url','inspector_url']:
  assert (SITE/urlsplit(m[key]).path).is_file(),(m['id'],key)
 assert hashlib.sha256((SITE/m['native_url']).read_bytes()).hexdigest()==m['sha256']
 with zipfile.ZipFile(SITE/m['package_url']) as z:
  assert z.testzip() is None
  filename=m['folder']+'/'+m['file'];assert hashlib.sha256(z.read(filename)).hexdigest()==m['sha256']
  assert any(n.endswith('/inspect.html') for n in z.namelist())
with zipfile.ZipFile(SITE/'downloads/all-native-maps.zip') as z:
 assert len([n for n in z.namelist() if n.endswith('.Civ6Map')])==4
 for m in manifest:assert hashlib.sha256(z.read(m['file'])).hexdigest()==m['sha256']
# Keep local machine receipts, credentials, and temp file paths out of public packages.
for f in (ROOT/'maps').rglob('*'):
 if f.is_file() and f.suffix in ['.json','.html','.py','.md','.txt']:
  text=f.read_text(errors='replace')
  assert '/Users/lolney/' not in text and '/var/folders/' not in text,f'Machine-specific path in {f}'
print(f'PASS: four map routes, local links, {count+1} JavaScript blocks, checksums, and download ZIP integrity.')
