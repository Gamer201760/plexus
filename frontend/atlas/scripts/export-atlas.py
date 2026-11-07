"""Export repository CSVs into a compact, reproducible frontend dataset."""
import csv,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parents[1]/'public'
points={}; regions=[]; links=[]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
for f in sorted((root/'data_manual/regions_input').glob('*.csv')):
 rows=read(f)
 for r in rows:
  try: points[r['point_id']]={'id':r['point_id'],'name':r['name'],'lat':float(r['lat']),'lon':float(r['lon']),'pop':int(float(r['population'] or 0)),'region':f.stem}
  except ValueError:continue
 md=root/'data_manual/regions'/f'{f.stem}.md'
 name=md.read_text().splitlines()[0].lstrip('# ').split(' — ')[0].split(' —')[0] if md.exists() else 'Республика Тыва'
 name=re.sub(r'\s*\(\d+\).*','',name)
 name=name.replace(' — транспортная связанность','')
 if f.stem=='98000000':name='Республика Саха (Якутия)'
 regions.append({'id':f.stem,'name':name,'settlements':len(rows),'population':sum(points[r['point_id']]['pop'] for r in rows if r['point_id'] in points)})
for f in [*sorted((root/'data_manual/regions').glob('*.csv')),root/'data_manual/tuva_links.csv']:
 if f.stem.endswith('_remote'):continue
 for r in read(f):
  links.append({'id':str(len(links)),'region':f.stem if f.stem!='tuva_links' else '93000000',**{k:r.get(k,'') for k in ['from_id','to_id','from_name','to_name','mode','km','freq_per_week','freq_note','season','confidence','source_url','source_date','vehicle']}})
used={r[k] for r in links for k in ['from_id','to_id']}
for region in regions:
 candidates=sorted([p for p in points.values() if p['region']==region['id']],key=lambda p:-p['pop'])
 used.update(p['id'] for p in candidates[:5])
 region['center']=[sum(p['lon'] for p in candidates)/len(candidates),sum(p['lat'] for p in candidates)/len(candidates)] if candidates else [100,60]
 region['links']=sum(r['region']==region['id'] for r in links)
data={'regions':regions,'points':[p for k,p in points.items() if k in used],'links':links,'totals':{'regions':len(regions),'settlements':sum(r['settlements'] for r in regions),'links':len(links)},'indices':[]}
(out/'atlas.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
print('Exported',data['totals'],'mapped nodes',len(data['points']))
