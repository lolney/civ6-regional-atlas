#!/usr/bin/env python3
"""Place named economic regions on the existing geography; standard library only.
Run before balance_starts.py. Native resource IDs only; gold is omitted as requested.
Spawn-table exceptions preserve real terrain; improvement support is checked separately.
"""
import collections,json,math,pathlib,random,sqlite3
ROOT=pathlib.Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'map_data.json').read_text());T=D['tiles'];rules=json.loads((ROOT/'resource_rules.json').read_text());rng=random.Random(6192026)
STRATEGIC={'HORSES','IRON','NITER','COAL','OIL','ALUMINUM','URANIUM'}
anchors=[]
def add(name,res,lon,lat,count=1,radius=22,proxy='',sea=False):
 anchors.append(dict(name=name,resource=res,lon=lon,lat=lat,count=count,radius_km=radius,proxy=proxy,sea=sea))
# Approximate district/field centers; the output records actual snapping distances.
for n,x,y,c in [('Napa Valley',-122.30,38.50,2),('Sonoma / Russian River Valley',-122.85,38.45,2),('Alexander Valley',-122.88,38.70,1),('Mendocino / Ukiah',-123.20,39.10,2),('Lodi',-121.28,38.13,2),('Paso Robles',-120.66,35.63,2),('Santa Ynez Valley',-120.08,34.61,2),('Temecula Valley',-117.10,33.54,1),('Santa Lucia Highlands',-121.38,36.40,1),('Livermore Valley',-121.72,37.67,1),('Santa Cruz Mountains',-122.08,37.12,1)]:add(n,'WINE',x,y,c)
for n,x,y,c in [('Comstock Lode / Virginia City',-119.65,39.31,2),('Tonopah district',-117.23,38.07,2),('Cerro Gordo',-117.80,36.54,1),('Panamint district',-117.09,36.12,1)]:add(n,'SILVER',x,y,c)
for n,x,y in [('Los Angeles City oil field',-118.27,34.06),('Wilmington oil field',-118.23,33.78),('Long Beach / Signal Hill oil field',-118.16,33.80),('Kern River oil field / Bakersfield',-118.99,35.44),('Midway-Sunset oil field / Taft',-119.44,35.13),('Elk Hills oil field',-119.38,35.30),('Lost Hills oil field',-119.71,35.62),('South Belridge oil field',-119.69,35.43),('Coalinga oil field',-120.36,36.20),('Santa Maria / Cat Canyon oil fields',-120.30,34.82)]:add(n,'OIL',x,y)
for n,x,y in [('Santa Barbara Channel oil',-119.62,34.29),('Santa Barbara Channel / western fields',-120.02,34.33),('Southern California offshore oil',-118.10,33.61)]:add(n,'OIL',x,y,count=2,radius=28,sea=True)
for n,x,y in [('New Almaden quicksilver district',-121.87,37.18),('New Idria quicksilver district',-120.67,36.42),('Clear Lake quicksilver district',-122.65,38.88)]:add(n,'MERCURY',x,y)
for n,x,y in [('Copperopolis copper district',-120.64,37.98),('Yerington copper district',-119.17,38.99),('Ely / Robinson copper district',-114.87,39.25),('Bagdad copper district',-113.20,34.58),('Jerome copper district',-112.12,34.75)]:add(n,'COPPER',x,y)
for n,x,y in [('Badwater / Death Valley evaporites',-116.82,36.25),('Owens Lake evaporites',-117.96,36.42),('Searles Lake evaporites',-117.35,35.72)]:add(n,'SALT',x,y)
# Salt is a regional signature throughout the closed basins of the interior West.
for n,x,y,c,rad in [
 ('Bonneville Salt Flats',-113.83,40.76,5,30),
 ('Pilot Valley playa',-114.03,41.00,3,25),
 ('Great Salt Lake Desert / West Desert',-113.40,40.65,5,32),
 ('Great Salt Lake brine margins',-112.55,40.91,4,35),
 ('Sevier dry lake basin',-113.06,39.04,3,28),
 ('Carson Sink',-118.40,39.80,4,27),
 ('Humboldt Sink',-118.68,39.99,3,25),
 ('Black Rock Desert playa',-119.14,40.93,4,30),
 ('Smoke Creek Desert playa',-119.79,40.63,3,25),
 ('Columbus Salt Marsh',-118.06,38.08,2,23),
 ('Clayton Valley evaporites',-117.64,37.72,1,24),
 ('Bristol dry lake basin',-115.65,34.40,2,23),
 ('Soda Lake / Mojave evaporites',-116.09,35.13,2,23),
 ('Soda Lake / Carrizo Plain',-119.84,35.24,1,23)]:add(n,'SALT',x,y,c,rad)
# Remove generic placements that obscured the named regional concentrations.
for t in T:
 t.pop('deposit',None)
 r=t['resource']
 if r in {'WINE','OIL','MERCURY'} or (r=='SILVER' and (t['lon']< -120 or rng.random()<.80)):
  t['resource']='';t['quantity']=0
# Keep a modest supply of balance strategics, distributed over the full landmass.
for r,cap in [('ALUMINUM',40),('URANIUM',28),('NITER',45),('IRON',60),('COAL',40)]:
 ids=[t['id'] for t in T if t['resource']==r];rng.shuffle(ids)
 for i in ids[cap:]:T[i]['resource']='';T[i]['quantity']=0

def km(t,a):
 return math.hypot((t['lon']-a['lon'])*111.32*math.cos(math.radians(a['lat'])),(t['lat']-a['lat'])*111.32)
def spawn_ok(t,r):
 r='RESOURCE_'+r
 return ('FEATURE_'+t['feature'] in rules['features'].get(r,[])) if t['feature'] else ('TERRAIN_'+t['terrain'] in rules['terrains'].get(r,[]))
def usable(t,a):
 if 'MOUNTAIN' in t['terrain'] or t.get('deposit'):return False
 if a['resource']=='SALT' and ('HILLS' in t['terrain'] or t['feature']):return False
 if a['sea']:return t['terrain']=='COAST' and not t['lake']
 return t['terrain'] not in ['COAST','OCEAN']
placed=[];exceptions=[]
for a in anchors:
 candidates=[t for t in T if usable(t,a) and km(t,a)<=a['radius_km']]
 # Native spawn compatibility is preferred within the same geographic district.
 # Oil and ore may be authored on grass/plains/hills: corresponding improvements support them.
 candidates.sort(key=lambda t:km(t,a)+(0 if spawn_ok(t,a['resource']) else 7)+(4 if t['resource'] else 0)+(3 if t['feature'].startswith('FLOODPLAINS') else 0))
 if len(candidates)<a['count']:raise RuntimeError('No nearby plots for '+a['name'])
 ids=[]
 for t in candidates[:a['count']]:
  t['resource']=a['resource'];t['quantity']=2 if a['resource'] in STRATEGIC else 1;t['goody']=False
  info=dict(name=a['name'],resource=a['resource'],proxy=a['proxy'],distance_km=round(km(t,a),2),anchor_lon=a['lon'],anchor_lat=a['lat'])
  t['deposit']=info;ids.append(t['id'])
  if not spawn_ok(t,a['resource']):
   exceptions.append(dict(plot=t['id'],resource=a['resource'],terrain=t['terrain'],feature=t['feature'],reason='Authored geographic deposit; outside procedural spawn filters. '+a['name']))
 placed.append({**a,'plots':ids})
# Regionally weighted agriculture: rice in the Sacramento Valley, citrus and ranches
# in California's valleys. These are economic-region abstractions, not ancient crops.
regions=[('RICE',-122.25,-121.35,38.6,39.7,9),('CITRUS',-119.65,-118.8,35.8,36.7,6),('CITRUS',-118.1,-117.1,33.7,34.3,4),('CATTLE',-122.2,-119.8,36.5,40.1,16)]
for res,x1,x2,y1,y2,n in regions:
 pool=[t for t in T if not t['resource'] and x1<t['lon']<x2 and y1<t['lat']<y2 and spawn_ok(t,res)]
 rng.shuffle(pool)
 for t in pool[:n]:t['resource']=res;t['quantity']=1;t['goody']=False
D['iconic_deposits']=placed;D['resource_placement_exceptions']=exceptions
D['notes']['resource_method']='Named wine, oil and mining districts anchor the resource layout. Gold is omitted as requested; standard Gathering Storm has no gold resource. Remaining deposits provide regional gameplay balance; they are not an exhaustive geological inventory.'
D['stats']['resource_tiles']=sum(bool(t['resource']) for t in T);D['stats']['goody_huts']=sum(t['goody'] for t in T);D['stats']['iconic_resource_tiles']=sum(bool(t.get('deposit')) for t in T)
(ROOT/'map_data.json').write_text(json.dumps(D,separators=(',',':')))
c=sqlite3.connect(ROOT/'California_GatheringStorm.Civ6Map');c.execute('DELETE FROM PlotResources');c.executemany('INSERT INTO PlotResources VALUES(?,?,?)',[(t['id'],'RESOURCE_'+t['resource'],t['quantity']) for t in T if t['resource']]);c.execute('DELETE FROM PlotImprovements');c.executemany('INSERT INTO PlotImprovements VALUES(?,?,?)',[(t['id'],'IMPROVEMENT_GOODY_HUT',-1) for t in T if t['goody']]);c.commit();c.close()
print(json.dumps({'districts':len(placed),'iconic_tiles':D['stats']['iconic_resource_tiles'],'spawn_filter_exceptions':len(exceptions),'resource_counts':dict(collections.Counter(t['resource'] for t in T if t['resource'])),'district_placements':placed},indent=2))
