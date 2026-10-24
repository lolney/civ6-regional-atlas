#!/usr/bin/env python3
"""Rebuild a native Civ6Map from editable JSON and refresh its offline inspector.
Uses only Python's standard library. Does not install or modify game files.
"""
import argparse,json,pathlib,sqlite3
ROOT=pathlib.Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=pathlib.Path,help='new native map path (required unless --viewer-only)')
p.add_argument('--viewer-only',action='store_true')
p.add_argument('--force',action='store_true',help='replace an existing output map')
a=p.parse_args()
d=json.loads((ROOT/'map_data.json').read_text())
if not a.viewer_only:
 if a.output is None:p.error('Pass --output PATH or --viewer-only')
 if a.output.exists() and not a.force:p.error('Output exists; choose another path or pass --force')
 if a.output.exists():a.output.unlink()
 c=sqlite3.connect(a.output);c.executescript((ROOT/'schema.sql').read_text())
 metadata=json.loads((ROOT/'native_metadata.json').read_text())
 for table,rows in metadata.items():
  if rows:c.executemany('INSERT INTO "'+table+'" VALUES('+','.join('?' for _ in rows[0])+')',rows)
 ts=d['tiles']
 c.executemany('INSERT INTO Plots VALUES(?,?,?,?)',[(t['id'],'TERRAIN_'+t['terrain'],'CONTINENT_NORTH_AMERICA' if t['terrain'] not in ['COAST','OCEAN'] else '',int('MOUNTAIN' in t['terrain'])) for t in ts])
 c.executemany('INSERT INTO PlotFeatures VALUES(?,?)',[(t['id'],'FEATURE_'+t['feature']) for t in ts if t['feature']])
 c.executemany('INSERT INTO PlotResources VALUES(?,?,?)',[(t['id'],'RESOURCE_'+t['resource'],t['quantity']) for t in ts if t['resource']])
 c.executemany('INSERT INTO PlotImprovements VALUES(?,?,?)',[(t['id'],'IMPROVEMENT_GOODY_HUT',-1) for t in ts if t['goody']])
 rivers={}
 for r in d['rivers']:
  row=rivers.setdefault(r['plot'],[r['plot'],0,0,0,-1,-1,-1]);flag,flow={'W':(2,4),'NW':(3,5),'NE':(1,6)}[r['side']];row[flag]=1;row[flow]=r['flow']
 c.executemany('INSERT INTO PlotRivers VALUES(?,?,?,?,?,?,?)',rivers.values());c.commit();c.execute('VACUUM');c.close();print('Wrote',a.output)
raw=json.dumps(d,separators=(',',':')).replace('</','<\\/')
(ROOT/'inspect.html').write_text((ROOT/'tools/viewer_template.html').read_text().replace('__MAP_DATA__',raw))
print('Refreshed',ROOT/'inspect.html')
