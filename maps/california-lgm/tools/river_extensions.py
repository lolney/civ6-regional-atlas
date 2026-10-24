# Inferred drainage across the exposed shelf: retain modern valleys inland.
extension_audit=[]
points=[(-121.9,38.05),(-122.12,38.02),(-122.23,38.05),(-122.42,37.88),(-122.5,37.8),(-122.8,37.74),(-123.05,37.65)]
g=LineString([proj.transform(*p) for p in points]);rawgroups['Sacramento'].append(g)
source_rivers.append({'name':'Sacramento — inferred exposed Bay/shelf valley','seasonal':False,'points':list(g.coords)})
extension_audit.append({'name':'Sacramento','basis':'Generalized exposed San Francisco Bay / shelf paleovalley'})
for name,parts in list(rawgroups.items()):
 if name in ['Sacramento','San Joaquin']:continue
 ends=[p for g in parts for p in [Point(g.coords[0]),Point(g.coords[-1])]]
 coastal=[p for p in ends if land.boundary.distance(p)<5000 and p.x<X0+W*P and p.y>Y0+P]
 if not coastal:continue
 p=min(coastal,key=lambda p:sea_kd.query([p.x,p.y])[0]);distance,k=sea_kd.query([p.x,p.y])
 if not 2500<distance<60000:continue
 q=Point(va[int(sea_nodes[k])]);g=LineString([p,q])
 # Do not cut a new valley through mainland terrain: this is a shelf extension.
 if g.intersection(land.buffer(-3000)).length>P*.5:continue
 rawgroups[name].append(g);source_rivers.append({'name':name+' — inferred shelf extension','seasonal':False,'points':list(g.coords)})
 extension_audit.append({'name':name,'length_km':round(g.length/1000,1),'basis':'Nearest exposed-shelf outlet; inferred, not mapped paleochannel'})
