"""Extract source tables without geocoding or inventing operational restrictions.
Requires pdfplumber==0.11.10 and system pdftotext. XLSX extraction uses stdlib.
"""
import csv, hashlib, json, re, subprocess, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import pdfplumber
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]; BASE=REPO/'data/additional/road-assets-ugra'; RAW=BASE/'raw'; OUT=BASE/'derived';OUT.mkdir(parents=True,exist_ok=True)
ROAD='Prikaz-po-protyazhennosti-na-01.01.2026-g..pdf'
def clean(x):return re.sub(r'\s+',' ',x or '').strip()
def dump(name,rows):
 (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
def csvout(name,rows):
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
tables=[];roads=[];section='';last=None
for p in sorted(RAW.iterdir()):
 if p.suffix.lower()!='.pdf':continue
 subprocess.run(['pdftotext','-layout',str(p),str(OUT/(p.stem+'.txt'))],check=True)
 with pdfplumber.open(p) as doc:
  for pi,page in enumerate(doc.pages,1):
   for ti,table in enumerate(page.extract_tables(),1):
    for ri,cells in enumerate(table,1):
     tables.append(dict(source_file=p.name,page=pi,table=ti,row=ri,cells=cells))
     if p.name!=ROAD:continue
     c=[clean(v) for v in cells]
     if len(c)!=8:continue
     if c[0] and all(not v for v in c[1:]) and ('дорог' in c[0].lower() or 'развяз' in c[0]):section=c[0]
     # Row 84 has its number below the road name in the source; retain both source rows.
     if ('71-100' in c[1]) or (c[2].startswith('Автомобильна дорога г.Когалым')):
      last=dict(record_id=f'ugrador-2026-p{pi}-r{ri}',source_file=p.name,source_page=pi,source_row=ri,as_of='2026-01-01',section=section,sequence_raw=c[0],road_id_raw=c[1],name=c[2],length_km_raw=c[3],district_raw=c[4],category_raw=c[5],design_axle_load_tonnes_raw=c[6],surface_raw=c[7],owner='Ханты-Мансийский автономный округ — Югра',operator='КУ ХМАО — Югры «Управление автомобильных дорог»',latitude='',longitude='',continuation_rows='')
      roads.append(last)
     elif last and (not c[1] and not c[2] and (not c[0] or c[0]=='84') and any(c[3:]) and c[4]!='район'):
      if c[0]:last['sequence_raw']=c[0]
      for idx,key in enumerate(['length_km_raw','district_raw','category_raw','design_axle_load_tonnes_raw','surface_raw'],3):
       if c[idx]:last[key]+=(' | ' if last[key] else '')+c[idx]
      last['continuation_rows']+=f'{pi}:{ri};'
dump('pdf-table-rows.jsonl',tables);csvout('roads-2026.csv',roads)
bridges=[r for r in roads if 'мост' in r['name'].lower()];csvout('bridge-named-roads-2026.csv',bridges)
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};sheetrows=[]
for p in sorted(RAW.glob('*.xlsx')):
 with zipfile.ZipFile(p) as z:
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   strings=[''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
  for sheet in z.namelist():
   if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml',sheet):continue
   for row in ET.fromstring(z.read(sheet)).findall('.//m:sheetData/m:row',ns):
    cells={}
    for c in row:
     v=c.find('m:v',ns);value=v.text if v is not None else ''
     if c.get('t')=='s':value=strings[int(value)] if value else ''
     elif c.get('t')=='inlineStr':value=''.join(c.itertext())
     if value:cells[c.get('r')]=value
    if cells:sheetrows.append(dict(source_file=p.name,sheet_xml=sheet,row=int(row.get('r')),cells=cells))
dump('xlsx-rows.jsonl',sheetrows)
dump('xlsx-bridge-mentioned-rows.jsonl',[r for r in sheetrows if 'мост' in ' '.join(r['cells'].values()).lower()])
downloads=json.loads((HERE/'downloads.json').read_text()); records=list(downloads)
for p in sorted(OUT.iterdir()):
 records.append(dict(path=str(p.relative_to(REPO)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),kind='derived',url=None,generated_by='datasets/additional/road-assets-ugra/extract.py'))
(HERE/'manifest.json').write_text(json.dumps(dict(schema_version=1,files=records,counts=dict(source_files=len(downloads),road_records=len(roads),bridge_named_road_records=len(bridges),pdf_table_rows=len(tables),xlsx_rows=len(sheetrows))),ensure_ascii=False,indent=2)+'\n')
print(json.loads((HERE/'manifest.json').read_text())['counts'])
