#!/usr/bin/env python3
"""Independent static native-schema, rule, topology, and inspector consistency checks."""
from pathlib import Path
import sqlite3,json,collections,math,re,sys
ROOT=Path(__file__).resolve().parent.parent
rules=json.loads((ROOT/'rules.json').read_text());rr=json.loads((ROOT/'resource_rules.json').read_text());checks=[];datasets={};ids=[]
def check(name,ok,detail=None):
 checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
def adjacent(i):
 x,y=i%84,i//84
 return [yy*84+xx for xx,yy in [(x-1,y),(x+1,y),(x+y%2-1,y-1),(x+y%2,y-1),(x+y%2-1,y+1),(x+y%2,y+1)] if 0<=xx<84 and 0<=yy<54]
def corners(i):
 x,y=i%84,i//84;cx,cy=2*x+y%2,3*y
 return [(cx+dx,cy+dy) for dx,dy in [(0,2),(1,1),(1,-1),(0,-2),(-1,-1),(-1,1)]]
def groups(nodes,adj):
 seen=set();out=[]
 for i in nodes:
  if i in seen:continue
  g={i};seen.add(i);q=[i]
  for u in q:
   for v in adj(u):
    if v in nodes and v not in seen:g.add(v);seen.add(v);q.append(v)
  out.append(g)
 return out
verts=collections.defaultdict(set);pairplots=collections.defaultdict(set)
for i in range(4536):
 vs=corners(i)
 for v in vs:verts[v].add(i)
 for a,b in zip(vs,vs[1:]+vs[:1]):pairplots[frozenset([a,b])].add(i)
for epoch,filename in [('modern','Hawaii_Modern.Civ6Map'),('lgm','Hawaii_LGM.Civ6Map')]:
 d=json.loads((ROOT/(epoch+'_data.json')).read_text());datasets[epoch]=d;ts=d['tiles'];label=epoch+': ';c=sqlite3.connect(ROOT/filename)
 check(label+'SQLite integrity',c.execute('PRAGMA integrity_check').fetchall()==[('ok',)])
 template=sqlite3.connect(':memory:');template.executescript((ROOT/'schema.sql').read_text());expected={r[0]:r[1] for r in template.execute("SELECT name,sql FROM sqlite_master WHERE type='table'")};actual={r[0]:r[1] for r in c.execute("SELECT name,sql FROM sqlite_master WHERE type='table'")}
 check(label+'35-table WorldBuilder schema matches reference',expected==actual and len(actual)==35)
 check(label+'Standard 84 × 54 map',tuple(c.execute('SELECT * FROM Map').fetchone()[j] for j in [1,2,7])==(84,54,'MAPSIZE_STANDARD') and (d['width'],d['height'])==(84,54))
 attr=dict(c.execute('SELECT * FROM MapAttributes'));meta=dict(c.execute('SELECT * FROM MetaData'));ids.append(meta['ID'])
 check(label+'Gathering Storm loader and dependency',attr.get('Ruleset')=='RULESET_EXPANSION_2' and attr.get('MapScript')=='WorldBuilderMap.lua' and any(r[0]=='4873eb62-8ccc-4574-b784-dda455e74e68' for r in c.execute('SELECT * FROM ModDependencies')))
 check(label+'Independent Hawaii package identity','Hawai' in meta['DisplayName'] and meta['IsMod']=='1' and ('WorldBuilder','WORLDBUILDER','File','[self]') in list(c.execute('SELECT * FROM ModSettings_Items')))
 check(label+'No inherited cities, units, players, or forced starts',all(c.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]==0 for table in ['Cities','Units','Players','StartPositions']))
 plots=list(c.execute('SELECT * FROM Plots ORDER BY ID'));features=dict(c.execute('SELECT * FROM PlotFeatures'));resources={i:(r,n) for i,r,n in c.execute('SELECT * FROM PlotResources')}
 check(label+'Contiguous 4536 plot IDs',[t[0] for t in plots]==list(range(4536)) and [t['id'] for t in ts]==list(range(4536)))
 check(label+'Known terrain and Oceania continent',all(t in rules['terrains'] and (ct=='CONTINENT_OCEANIA' if t not in ['TERRAIN_COAST','TERRAIN_OCEAN'] else ct=='') for i,t,ct,imp in plots))
 check(label+'Impassability exactly matches mountain terrain',all(bool(imp)==t.endswith('MOUNTAIN') for i,t,ct,imp in plots))
 check(label+'Features legal on native terrain',all(f in rules['features'] and plots[i][1] in rules['features'][f] for i,f in features.items()))
 check(label+'Resources obey native terrain/feature placement rules',all(r in set(rr['terrains'])|set(rr['features']) and n>0 and (features[i] in rr['features'].get(r,[]) if i in features else plots[i][1] in rr['terrains'].get(r,[])) for i,(r,n) in resources.items()))
 check(label+'Native plots exactly match inspector',all(plots[t['id']][1]=='TERRAIN_'+t['terrain'] and features.get(t['id'],'')==('FEATURE_'+t['feature'] if t['feature'] else '') and resources.get(t['id'],('',0))==('RESOURCE_'+t['resource'] if t['resource'] else '',t['quantity']) for t in ts))
 native_edges=set()
 for row in c.execute('SELECT * FROM PlotRivers'):
  i,e,sw,se,ef,swf,sef=row
  for side,flag,flow in [('NE',e,sef),('W',sw,ef),('NW',se,swf)]:
   if flag:native_edges.add((i,side,flow))
 check(label+'Native river flags/flows exactly match inspector',native_edges=={(r['plot'],r['side'],r['flow']) for r in d['rivers']})
 check(label+'No duplicate river ownership',len({(r['plot'],r['side']) for r in d['rivers']})==len(d['rivers']))
 land={t['id'] for t in ts if t['terrain'] not in ['COAST','OCEAN']};mountain={t['id'] for t in ts if t['terrain'].endswith('MOUNTAIN')};riverland=set();ng=collections.defaultdict(lambda:collections.defaultdict(set));outs=collections.Counter();riverok=True;flows=True;pointmatch=True
 for r in d['rivers']:
  vs=corners(r['plot']);k={'W':1,'NW':2,'NE':3}[r['side']];a,b=vs[k],vs[k+1];owner=pairplots[frozenset([a,b])];riverland|=owner
  riverok &= len(owner)==2 and owner<=land and not owner&mountain
  flows &= r['flow'] in {'W':[0,3],'NW':[1,4],'NE':[2,5]}[r['side']]
  # Stored normalized vertices must decode to the exact native edge and flow direction.
  decoded=[(round(p[0]*2),round(p[1]*2*math.sqrt(3))) for p in r['points']];pointmatch &= set(decoded)=={a,b}
  u,v=decoded;dx,dy=v[0]-u[0],v[1]-u[1];flow=(0 if dy>0 else 3) if dx==0 else (1 if dy>0 else 2) if dx>0 else (5 if dy>0 else 4);flows &= flow==r['flow'];outs[u]+=1;ng[r['name']][a].add(b);ng[r['name']][b].add(a)
 check(label+'Rivers only on land–land, non-mountain edges',riverok)
 check(label+'Legal river flow directions',flows)
 check(label+'River rendered endpoints match native hex geometry',pointmatch)
 check(label+'No split downstream flow',max(outs.values(),default=0)<=1)
 connected=all(len(groups(set(g),lambda v:g[v]))==1 for g in ng.values());acyclic=all(sum(map(len,g.values()))//2==len(g)-1 for g in ng.values());mouths=all(any(len(n)==1 and any(i not in land for i in verts[v]) for v,n in g.items()) for g in ng.values())
 check(label+'Every named course contiguous and acyclic',connected and acyclic)
 check(label+'Every named river reaches a coast vertex',mouths)
 check(label+'Major Wailuku, Wailua, Waimea, and Hanalei rivers included',all(n in ng for n in ['Wailuku River','North Fork Wailua River','Waimea River','Hanalei River']))
 check(label+'Floodplains only on flat river-adjacent terrain',all(t['id'] in riverland and t['terrain'] in ['GRASS','PLAINS'] for t in ts if t['feature'].startswith('FLOODPLAINS')))
 check(label+'Reefs in coast and no sea ice',all(t['terrain']=='COAST' for t in ts if t['feature']=='REEF') and not any(t['feature']=='ICE' for t in ts))
 coast={t['id'] for t in ts if t['terrain']=='COAST'}
 check(label+'Every island coast reachable by coast-only navigation',len(groups(coast,adjacent))==1 and all(any(j in coast for i in g for j in adjacent(i)) for g in groups(land,adjacent)))
 check(label+'Navigation corridors convert only ocean water',all(t['terrain']=='COAST' and not t['feature'] and not t['resource'] for t in ts if t.get('game_coast_corridor')))
 cc=groups(land,adjacent);members=[{ts[i]['island'] for i in g if ts[i]['island']} for g in cc]
 check(label+'Expected separate island landmasses',len(cc)==(8 if epoch=='modern' else 6),{'landmasses':len(cc),'sizes':sorted(map(len,cc),reverse=True)})
 check(label+'All eight main islands represented',set.union(*members)==set(json.loads((ROOT/'source_data/grid_inputs.json').read_text())['island_references']))
 check(label+'Maui Nui connectivity appropriate to epoch',any({'Maui','Molokaʻi','Lānaʻi'}<=x for x in members)==(epoch=='lgm'))
 check(label+'Kahoʻolawe and Niʻihau remain separate',all(len(x)==1 for x in members if x&{'Kahoʻolawe','Niʻihau'}))
 check(label+'No land clipped by rectangular boundary',all(0<i%84<83 and 0<i//84<53 for i in land))
 check(label+'Mauna Kea mountain and epoch-specific ice',ts[d['landmarks']['Mauna Kea']]['terrain'].endswith('MOUNTAIN') and bool(ts[d['landmarks']['Mauna Kea']]['glacier'])==(epoch=='lgm') and sum(bool(t['glacier']) for t in ts)==(1 if epoch=='lgm' else 0))
 check(label+'Mauna Loa not asserted as confirmed glacier',not ts[d['landmarks']['Mauna Loa']]['glacier'])
 check(label+'Four native volcanic landmarks',sum(t['feature']=='VOLCANO' for t in ts)==4)
 st=d['starts'];check(label+'Six safe, separated suggested starts',len(st)==6 and all(s['id'] in land-mountain and 3<s['id']%84<80 and 3<s['id']//84<50 and (s['id'] in riverland or any(v not in land for v in adjacent(s['id']))) for s in st) and all(math.dist((a['id']%84+.5*((a['id']//84)%2),a['id']//84*math.sqrt(3)/2),(b['id']%84+.5*((b['id']//84)%2),b['id']//84*math.sqrt(3)/2))>=6 for j,a in enumerate(st) for b in st[j+1:]))
 check(label+'Start food and luxury access',all(s['metrics']['food_resources_ring3']>=4 and s['metrics']['luxury_types_ring3']>=2 for s in st),[s['metrics'] for s in st])
 check(label+'Documented resource audit placements retained',all(a.get('placed') and ts[a['plot']]['resource']==a['resource'] for a in d['notes']['resource_audit']))
 check(label+'Cattle and twelve other audited types represented',all(any(t['resource']==r for t in ts) for r in ['CATTLE','COCOA','COTTON','DEER','DYES','INCENSE','OLIVES','STONE','TEA','TOBACCO','TURTLES','WHEAT','WINE']))
 check(label+'No fabricated oil, coal, uranium deposits',not any(t['resource'] in ['OIL','COAL','URANIUM'] for t in ts))
 check(label+'No invented pluvial lakes',not d['lakes'] and not any(t['lake'] for t in ts))
 check(label+'Resource catalog includes absent standard resources',len(d['resource_catalog']['resources'])==44)
 check(label+'Statistics match contents',d['stats']['land']==len(land) and d['stats']['river_edges']==len(d['rivers']) and d['stats']['resource_tiles']==len(resources))
 c.close()
check('Different map identities',len(set(ids))==2)
m,l=datasets['modern'],datasets['lgm'];island=lambda t:t['terrain'] not in ['COAST','OCEAN']
check('LGM land contains all modern land',all(not island(a) or island(b) for a,b in zip(m['tiles'],l['tiles'])))
check('LGM exposed seabed count matches pairwise comparison',l['stats']['exposed_seabed_hexes']==sum(not island(a) and island(b) for a,b in zip(m['tiles'],l['tiles'])))
check('Cold climate reduces lowland rainforest footprint',l['stats']['rainforests']<m['stats']['rainforests'])
html=(ROOT/'inspect.html').read_text()
for element,epoch in [('data','lgm'),('modernData','modern')]:
 embedded=json.loads(re.search(r'<script id="'+element+r'" type="application/json">(.*?)</script>',html,re.S).group(1));check(epoch+': offline embedded dataset equals editable JSON',embedded==datasets[epoch])
check('Inspector has no external scripts or assets',not re.search(r'<(?:script|img|link)[^>]+(?:src|href)=["\']https?://',html))
report={'passed':all(c['passed'] for c in checks),'checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'scope':'Static SQLite/schema/rules/topology and native-to-viewer comparison. Not an in-game load test.','checks':checks}
(ROOT/'validation_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(f"{report['checks_passed']}/{len(checks)} checks passed")
for c in checks:
 if not c['passed']:print('FAIL:',c['check'],c.get('detail',''))
sys.exit(0 if report['passed'] else 1)
