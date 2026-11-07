"""Export existing idx_region values without recomputing or inventing them.
Usage: python scripts/export-indices.py /absolute/path/to/casechamp.duckdb
Requires duckdb from the parent ETL environment.
"""
import argparse,json,re
from pathlib import Path
import duckdb
parser=argparse.ArgumentParser();parser.add_argument('database',type=Path);args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
regions=json.loads((root/'public/atlas.json').read_text())['regions']
def norm(s):return re.sub(r'[^а-яё]','',s.lower().replace('республика','').replace('автономный округ','').replace('ао','').replace('область','').replace('край',''))
lookup={norm(r['name']):r['id'] for r in regions}
lookup.update({'ямалоненецкий':'71900000','хантымансийскийюгра':'71800000','севернаяосетияалания':'90000000','кемеровскаякузбасс':'32000000','чувашия':'97000000'})
con=duckdb.connect(str(args.database),read_only=True)
records=con.execute('select region, season, hansen_idx, aria, rai, gini from idx_region').fetchall()
output=[];unmatched=[]
for name,season,hansen,aria,rai,gini in records:
 code=name if name in {r['id'] for r in regions} else lookup.get(norm(name))
 if not code:unmatched.append(name);continue
 if hansen is None:continue
 output.append({'region_id':code,'season':season,'hansen_idx':hansen,'aria':aria,'rai':rai,'gini':gini})
if not output:raise SystemExit('No matching regional results; nothing written.')
(root/'public/indices.json').write_text(json.dumps(output,ensure_ascii=False,allow_nan=False,separators=(',',':')))
print('Exported',len(output),'rows. Unmatched regions:',sorted(set(unmatched)))
