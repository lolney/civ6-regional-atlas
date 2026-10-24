#!/usr/bin/env python3
"""Run all map validators and check portable inspector/source agreement."""
from pathlib import Path
import json,subprocess,sys,re,hashlib
ROOT=Path(__file__).resolve().parent.parent
commands=[['maps/california-modern/tools/validate_map.py','--report','maps/california-modern/validation_report.json'],['maps/california-lgm/tools/validate_map.py','--report','maps/california-lgm/validation_report.json'],['maps/hawaii/tools/validate_maps.py']]
for cmd in commands:subprocess.run([sys.executable,*cmd],cwd=ROOT,check=True)
for name in ['california-modern','california-lgm','hawaii']:
 p=ROOT/'maps'/name;s=(p/'inspect.html').read_text()
 targets={'data':'map_data.json'} if name!='hawaii' else {'data':'lgm_data.json','modernData':'modern_data.json'}
 if name=='california-lgm':targets['modernData']='modern_reference.json'
 for element,file in targets.items():
  match=re.search(r'<script id="'+element+r'" type="application/json">(.*?)</script>',s,re.S)
  assert match and json.loads(match.group(1))==json.loads((p/file).read_text()),(name,element,'embedded data mismatch')
 files=sorted(f for f in p.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt' and '__pycache__' not in f.parts and f.suffix!='.pyc')
 (p/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(p).as_posix() for f in files)+'\n')
print('All four maps and embedded datasets validated; checksums refreshed.')
