#!/usr/bin/env python3
"""Select 12 generic major-civilization starts and top up nearby legal resources.
No modern city locations enter this algorithm. These remain inspector recommendations.
"""
import collections,json,math,pathlib,random,sqlite3
ROOT=pathlib.Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'map_data.json').read_text());T=D['tiles'];W=D['width'];H=D['height'];rng=random.Random(6192026)
rules=json.loads((ROOT/'rules.json').read_text())['resources']

def adj(i):
 x,y=i%W,i//W
 for a,b in [(x-1,y),(x+1,y),(x+y%2-1,y-1),(x+y%2,y-1),(x+y%2-1,y+1),(x+y%2,y+1)]:
  if 0<=a<W and 0<=b<H:yield b*W+a

def axial(i):
 x,y=i%W,i//W;return x-(y-y%2)//2,y
A=[axial(i) for i in range(len(T))]
def dist(i,j):
 a,b=A[i];c,d=A[j];return (abs(a-c)+abs(b-d)+abs(a+b-c-d))//2

def land(i):return T[i]['terrain'] not in ['COAST','OCEAN'] and 'MOUNTAIN' not in T[i]['terrain']

def disk(i,n):
 x,y=i%W,i//W
 return [b*W+a for b in range(max(0,y-n),min(H,y+n+1)) for a in range(max(0,x-n-1),min(W,x+n+2)) if dist(i,b*W+a)<=n]

riverbanks=set()
for r in D['rivers']:
 i=r['plot'];x,y=i%W,i//W;riverbanks.add(i)
 riverbanks.add({'W':i+1,'NW':(y-1)*W+x+y%2,'NE':(y-1)*W+x+y%2-1}[r['side']])
lake_counts=collections.Counter(t['lake'] for t in T if t['lake'])
fresh={i for i in range(len(T)) if i in riverbanks or any(T[j]['lake'] and lake_counts[T[j]['lake']]<=10 for j in adj(i))}
foodres={'WHEAT','RICE','CATTLE','SHEEP','FISH','CITRUS','TRUFFLES','FURS','SUGAR'};prodres={'STONE','COPPER','DEER','IRON','COAL','HORSES','ALUMINUM','URANIUM','OIL','OLIVES'};luxres={r['id'] for r in D['resource_catalog']['resources'] if r['class']=='luxury'}
def yields(i):
 t=T[i];b=t['terrain'].split('_')[0];f,p={'GRASS':(2,0),'PLAINS':(1,1),'DESERT':(0,0),'TUNDRA':(1,0),'SNOW':(0,0),'COAST':(1,0),'OCEAN':(1,0)}.get(b,(0,0))
 if 'MOUNTAIN' in t['terrain']:return 0,0
 if 'HILLS' in t['terrain']:p+=1
 if t['feature']=='FOREST':p+=1
 if t['feature']=='MARSH':f+=1
 if t['feature']=='FLOODPLAINS':f+=3
 if t['resource'] in foodres:f+=1
 if t['resource'] in prodres:p+=1
 # Basic farm/mine potential; purpose is comparing sites, not claiming UI yields.
 if land(i):
  if 'HILLS' in t['terrain']:p+=1
  elif b in ['GRASS','PLAINS'] or t['feature'].startswith('FLOODPLAINS'):f+=1
 return f,p

metrics={};r2={};r3={}
for i in sorted(fresh):
 x,y=i%W,i//W
 if not land(i) or not(6<=x<W-6 and 6<=y<H-6) or T[i]['resource']:continue
 d2=disk(i,2);d3=disk(i,3);pass2=sum(land(j) for j in d2);pass3=sum(land(j) for j in d3)
 if pass2<12 or pass3<25:continue
 vals=sorted((yields(j) for j in d2 if j!=i and land(j)),key=lambda z:1.65*z[0]+1.3*z[1],reverse=True)
 best=vals[:8];food=sum(f for f,p in best);prod=sum(p for f,p in best)
 if food<10 or prod<7:continue
 luxury=len({T[j]['resource'] for j in d3 if T[j]['resource'] in luxres})
 score=food*1.65+prod*1.3+min(pass3,32)*.45+min(luxury,3)*2
 metrics[i]={'score':round(score,1),'food_potential':food,'production_potential':prod,'passable_ring2':pass2,'passable_ring3':pass3,'luxury_types_ring3':luxury,'fresh_water':True}
 r2[i]=d2;r3[i]=d3

candidates=sorted(metrics,key=lambda i:metrics[i]['score'],reverse=True)
if len(candidates)<12:raise RuntimeError('Too few viable starts')
# Maximin spacing over many deterministic seeds; weak isolated sites are discarded.
quality_floor=sorted(metrics[i]['score'] for i in candidates)[int(len(candidates)*.08)]
pool=[i for i in candidates if metrics[i]['score']>=quality_floor]
best=None
for separation in [12,11,10]:
 for trial in range(70):
  first=pool[trial%min(100,len(pool))] if trial<35 else rng.choice(pool)
  chosen=[first]
  while len(chosen)<12:
   valid=[i for i in pool if all(dist(i,j)>=separation for j in chosen)]
   if not valid:break
   qualitymax=max(metrics[i]['score'] for i in valid)
   def priority(i):
    gap=min(dist(i,j) for j in chosen)
    return .35*(metrics[i]['score']/qualitymax)+.65*min(gap,32)/32
   chosen.append(max(valid,key=priority))
  if len(chosen)<12:continue
  qs=[metrics[i]['score'] for i in chosen]
  mingap=min(dist(a,b) for k,a in enumerate(chosen) for b in chosen[k+1:])
  nearest=[min(dist(i,j) for j in chosen if j!=i) for i in chosen]
  isolation=max(nearest)
  objective=min(qs)*.8+sum(qs)/12-(max(qs)-min(qs))*.2+mingap*2-max(0,isolation-24)*4
  if best is None or objective>best[0]:best=(objective,chosen,separation)
 if best:break
if not best:raise RuntimeError('Cannot fit twelve viable starts')
chosen=sorted(best[1],key=lambda i:(-(i//W),i%W));changes=[]

def eligible(i,res):
 t=T[i];r='RESOURCE_'+res;f='FEATURE_'+t['feature'] if t['feature'] else ''
 if not land(i) or t['resource'] or i in chosen:return False
 return f in rules['features'].get(r,[]) if f else 'TERRAIN_'+t['terrain'] in rules['terrains'].get(r,[])

def place_near(start,options,radius):
 ids=sorted(disk(start,radius),key=lambda i:(dist(i,start),i))
 for i in ids:
  for res in options:
   if eligible(i,res):
    T[i]['resource']=res;T[i]['quantity']=2 if res in ['HORSES','IRON','NITER','COAL','OIL','ALUMINUM','URANIUM'] else 1;T[i]['goody']=False;changes.append({'start':start,'plot':i,'resource':res});return True
 return False

# Same minimum access guarantees for each start; no hills or rivers moved.
for i in chosen:
 for k in range(max(0,3-sum(T[j]['resource'] in foodres for j in r3[i]))):place_near(i,['WHEAT','RICE','CATTLE','SHEEP','CITRUS'],3)
 if not any(T[j]['resource'] in luxres for j in r3[i]):place_near(i,['CITRUS','WINE','SALT','GYPSUM','SILVER','TRUFFLES'],3)
 for res in ['HORSES','IRON']:
  if not any(T[j]['resource']==res for j in disk(i,6)):place_near(i,[res],6)
 # Starts should not consume a tribal village or have one on the immediate city ring.
 for j in disk(i,1):T[j]['goody']=False

D['starts']=[]
for k,i in enumerate(chosen,1):
 ns=[dist(i,j) for j in chosen if j!=i]
 m=metrics[i].copy();m['nearest_start_hexes']=min(ns);m['food_resources_ring3']=sum(T[j]['resource'] in foodres for j in r3[i]);m['luxury_types_ring3']=len({T[j]['resource'] for j in r3[i] if T[j]['resource'] in luxres});m['horses_within6']=any(T[j]['resource']=='HORSES' for j in disk(i,6));m['iron_within6']=any(T[j]['resource']=='IRON' for j in disk(i,6))
 best8=sorted((yields(j) for j in r2[i] if j!=i and land(j)),key=lambda z:1.65*z[0]+1.3*z[1],reverse=True)[:8]
 m['food_potential']=sum(f for f,p in best8);m['production_potential']=sum(p for f,p in best8)
 m['score']=round(m['food_potential']*1.65+m['production_potential']*1.3+min(m['passable_ring3'],32)*.45+min(m['luxury_types_ring3'],3)*2,1)
 D['starts'].append({'name':f'Start {k:02d}','id':i,'region':T[i]['ecoregion'],'metrics':m})
D['notes']['start_selection']={'method':'Twelve generic civ starts selected by freshwater, food/production potential, passable expansion area and maximin spacing; modern cities are not inputs. Scores are an approximate early-improvement heuristic, not the Civ VI engine fertility score.','edge_margin_hexes':6,'minimum_separation_hexes':best[2],'candidate_sites':len(candidates),'resource_additions':changes}
D['stats']['resource_tiles']=sum(bool(t['resource']) for t in T);D['stats']['goody_huts']=sum(t['goody'] for t in T)
(ROOT/'map_data.json').write_text(json.dumps(D,separators=(',',':')))
c=sqlite3.connect(ROOT/'California_GatheringStorm.Civ6Map');c.execute('DELETE FROM PlotResources');c.executemany('INSERT INTO PlotResources VALUES(?,?,?)',[(t['id'],'RESOURCE_'+t['resource'],t['quantity']) for t in T if t['resource']]);c.execute('DELETE FROM PlotImprovements');c.executemany('INSERT INTO PlotImprovements VALUES(?,?,?)',[(t['id'],'IMPROVEMENT_GOODY_HUT',-1) for t in T if t['goody']]);c.commit();c.close()
print(json.dumps({'candidate_sites':len(candidates),'minimum_separation':best[2],'added_resources':len(changes),'starts':D['starts']},indent=2))
