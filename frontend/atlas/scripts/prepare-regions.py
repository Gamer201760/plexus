"""Prepare regional geometry, preserving source features and explicit coverage gaps."""
import json,math,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'public/geo/regions.json').read_text())
a=json.loads((root/'public/atlas.json').read_text())
def norm(s):return re.sub(r'[^а-яё]','',s.lower().replace('республика','').replace('автономный округ','').replace('ао',''))
alias={'Бурятия':'81000000','Ханты-Мансийский автономный округ - Югра':'71800000','Ямало-Ненецкий автономный округ':'71900000','Чувашия':'97000000','Северная Осетия - Алания':'90000000','Москва':'45000000','Санкт-Петербург':'40000000'}
lookup={norm(r['name']):r['id'] for r in a['regions']}
n=math.log(math.cos(math.radians(50))/math.cos(math.radians(70)))/math.log(math.tan(math.pi/4+math.radians(70)/2)/math.tan(math.pi/4+math.radians(50)/2))
F=math.cos(math.radians(50))*math.tan(math.pi/4+math.radians(50)/2)**n/n
rho0=F/math.tan(math.pi/4+math.radians(60)/2)**n
def proj(p):
 lon,lat=p[:2]
 if lon<0:lon+=360
 rho=F/math.tan(math.pi/4+math.radians(lat)/2)**n
 t=n*math.radians(lon-100)
 return [rho*math.sin(t),rho0-rho*math.cos(t)]
raw=[]
for f in d['features']:
 name=f['properties']['name'];code=alias.get(name,lookup.get(norm(name)))
 if not code:raise ValueError(name)
 polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
 rings=[[proj(p) for p in ring] for poly in polys for ring in poly]
 raw.append({'id':code,'name':name,'rings':rings})
coords=[p for r in raw for ring in r['rings'] for p in ring]
minx=min(p[0] for p in coords);maxx=max(p[0] for p in coords);miny=min(p[1] for p in coords);maxy=max(p[1] for p in coords)
scale=min(940/(maxx-minx),520/(maxy-miny))
def xy(p):return [round(500+(p[0]-(minx+maxx)/2)*scale,1),round(310-(p[1]-(miny+maxy)/2)*scale,1)]
out=[]
for r in raw:
 rings=[[xy(p) for p in ring] for ring in r['rings']]
 longest=max(rings,key=len)
 center=[sum(p[i] for p in longest)/len(longest) for i in [0,1]]
 path=' '.join('M'+'L'.join(f'{p[0]},{p[1]}' for p in ring)+'Z' for ring in rings)
 out.append({'id':r['id'],'name':r['name'],'path':path,'center':[round(v,1) for v in center]})
missing=[r['id'] for r in a['regions'] if r['id'] not in [f['id'] for f in out]]
(root/'public/geo/region-paths.json').write_text(json.dumps({'regions':out,'missing':missing,'source':'Click That Hood / OpenStreetMap, regional geometry snapshot 2013','source_url':'https://github.com/codeforamerica/click_that_hood/blob/master/public/data/russia.geojson'},ensure_ascii=False,separators=(',',':')))
print('Prepared',len(out),'regional boundaries; dataset without geometry:',missing)
