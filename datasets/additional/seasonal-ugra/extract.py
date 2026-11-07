from pathlib import Path
from bs4 import BeautifulSoup
import csv,json,re,zipfile,xml.etree.ElementTree as E,subprocess,datetime,hashlib
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/additional/seasonal-ugra'
RAW=OUT/'raw'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def write(name,rows):
 if not rows:return
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def iso(raw):
 m=re.search(r'(\d{2})[.\-](\d{2})[.\-](20\d{2})',raw)
 if m:
  try:return datetime.date(int(m[3]),int(m[2]),int(m[1])).isoformat()
  except ValueError:return ''
 return ''
def dates(t):return list(dict.fromkeys(iso(m[0]) for m in re.finditer(r'\d{2}\.\d{2}\.20\d{2}',t)))
def status(t,report):
 low=t.lower()
 if 'закрыт' in low:
  d=dates(t);future=bool(d and report and d[0]>report)
  return 'planned closure' if future else 'reported closed'
 if 'ограничен' in low:return 'weight or time restriction reported'
 return 'no closure claim extracted'
articles=[];events=[]
for p in sorted(RAW.glob('status-*.html')):
 s=BeautifulSoup(p.read_bytes(),'html.parser');dt=s.select_one('.news-item-date');body=s.select_one('.news-item-text')
 if not dt or not body:continue
 date=iso(dt.get_text());text=body.get_text('\n',strip=True);title=s.title.get_text(' ',strip=True)
 articles.append(dict(source_file=p.name,publication_date=date,title=title,body=text))
 (OUT/(p.stem+'.txt')).write_text(date+'\n'+title+'\n'+text)
 for n,line in enumerate(text.splitlines(),1):
  if any(k in line.lower() for k in ['закры','откры','введ','огранич','грузоподъем','грузоподъём','эксплуатац']):
   low=line.lower();classification='reported status'
   if any(k in low for k in ['будут','будет','планиру','закроют','предстоит']):classification='planned/announced'
   elif 'закрыт' in low:classification='reported closed'
   elif 'введен' in low or 'открыт' in low:classification='reported opening or restriction; read text'
   events.append(dict(source_file=p.name,publication_date=date,line_number=n,dates_mentioned=';'.join(dates(line)),classification=classification,text=line,precision='paragraph-level; dates may include order dates, not automatically effective dates'))
write('news-articles.csv',articles);write('news-status-statements.csv',events)
routes=[];crossings=[];aggregates=[];rawrows=[]
for p in sorted(RAW.glob('*.xlsx')):
 with zipfile.ZipFile(p) as z:
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(t.text or '' for t in a.findall('.//m:t',NS)) for a in E.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
  for sheet in sorted(n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+.xml',n)):
   rr=E.fromstring(z.read(sheet));sheetrows=[]
   for row in rr.findall('.//m:row',NS):
    vals={}
    for cell in row.findall('m:c',NS):
     v=cell.find('m:v',NS);value=v.text if v is not None else ''.join(t.text or '' for t in cell.findall('.//m:t',NS))
     if value and cell.get('t')=='s':value=strings[int(value)]
     if value:vals[re.sub(r'\d','',cell.get('r'))]=value
    if vals:sheetrows.append((int(row.get('r')),vals));rawrows.append(dict(source_file=p.name,sheet=sheet,row=int(row.get('r')),cells=vals))
   report=next((iso(v) for _,vs in sheetrows for v in vs.values() if 'по состоянию' in v.lower()),'');district='';parent='';parentid=''
   for row,vs in sheetrows:
    a=vs.get('A','').strip();name=vs.get('B','').strip()
    if 'район' in a.lower() and len(a)<70:district=a;continue
    common=dict(source_file=p.name,sheet=sheet,source_row=row,report_date=report,district=district)
    if name.lower().startswith(('всего','итого')):
     aggregates.append(dict(**common,label=name,road_km=vs.get('C',''),crossing_km=vs.get('D',''),readiness_percent=vs.get('E','')));continue
    if re.fullmatch(r'\d+',a) and name:
     parent=name;parentid=a;op=vs.get('K','');restriction=vs.get('M','');combined=restriction+' '+vs.get('H','')
     routes.append(dict(**common,route_number=a,route=name,road_km=vs.get('C',''),crossing_km=vs.get('D',''),readiness_percent=vs.get('E',''),ice_cm=vs.get('F',''),weight_limit_raw=vs.get('G',''),condition_raw=vs.get('H',''),opening_raw=op,opening_date=iso(op),restriction_raw=restriction,closure_date_candidate=iso(restriction) if 'закрыт' in restriction.lower() else '',classification=status(combined,report),date_policy='first restriction date only for explicit closed text; order dates remain in raw'))
    elif name and vs.get('D') and district:
     crossings.append(dict(**common,parent_route_number=parentid,parent_route=parent,crossing=name,crossing_km=vs.get('D',''),ice_cm=vs.get('F',''),weight_limit_raw=vs.get('G',''),opening_raw=vs.get('K',''),restriction_raw=vs.get('M',''),inheritance_policy='parent association only; merged parent dates not duplicated as independent crossing observations'))
with (OUT/'xlsx-rows.jsonl').open('w') as f:
 for r in rawrows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
route_lookup={(r['source_file'],r['sheet'],r['district'],r['route_number']):r for r in routes}
for crossing in crossings:
 parent=route_lookup.get((crossing['source_file'],crossing['sheet'],crossing['district'],crossing['parent_route_number']),{})
 crossing['parent_route_opening_date']=parent.get('opening_date','')
 crossing['parent_route_closure_date_candidate']=parent.get('closure_date_candidate','')
write('xlsx-route-status.csv',routes);write('xlsx-crossings.csv',crossings);write('xlsx-district-aggregates.csv',aggregates)
pdfrows=[];pagesout=[]
for p in sorted(RAW.glob('*.pdf')):
 out=OUT/(p.stem+'.txt');subprocess.run(['pdftotext','-layout',str(p),str(out)],check=True);text=out.read_text();report=iso(text[:1500]);pages=text.split('\f')
 for pi,page in enumerate(pages,1):
  if not page.strip():continue
  pagesout.append(dict(source_file=p.name,pdf_page=pi,report_date=report,text=page))
  lines=page.splitlines();markers=[]
  for li,line in enumerate(lines):
   cstart=56 if p.name.startswith(('status-930','status-934')) else 50; name=line[5:cstart].strip();measure=line[cstart:cstart+14].strip()
   if re.fullmatch(r'\d+[,.]\d{3}',measure) and not any(k in name.lower() for k in ['всего','итого']):
    start=li
    for back in range(1,4):
     if li>=back:
      prior=lines[li-back][5:cstart].strip()
      if prior and ('"' in prior or '«' in prior):start=li-back
    markers.append((start,li,measure))
  for n,(start,li,length) in enumerate(markers):
   end=markers[n+1][0] if n+1<len(markers) else len(lines);segment=lines[start:end];header=' '.join(x[5:51].strip() for x in segment[:3] if x[5:51].strip());kcol=185 if '1496' in p.name or '1210' in p.name else 189
   if p.name.startswith(('status-930','status-934')):kcol=185
   opening=' '.join(x[kcol:kcol+18].strip() for x in segment if x[kcol:kcol+18].strip());restr=' '.join(x[kcol+18:kcol+53].strip() for x in segment if x[kcol+18:kcol+53].strip())
   pdfrows.append(dict(source_file=p.name,pdf_page=pi,report_date=report,route_sequence_on_page=n+1,route_label_candidate=header,road_km_raw=length,block_text='\n'.join(segment),extraction_quality='candidate text block; vertically merged notes can overlap neighboring blocks; use verified-route-seasons.csv for normalized dates'))
with (OUT/'pdf-pages.jsonl').open('w') as f:
 for r in pagesout:f.write(json.dumps(r,ensure_ascii=False)+'\n')
write('pdf-route-blocks.csv',pdfrows)
print({p.name:sum(1 for _ in csv.DictReader(p.open())) for p in OUT.glob('*.csv')})
verified=[]
labels=['п.Белорусский - с.Ларьяк','с.Ларьяк - д.Чехломей - д.Большой Ларьяк','г.Нижневартовск - д.Вампугол - с.Былино','с.Былино - п.Зайцева Речка','д.Соснина - граница Томской области','с.Угут - д.Каюкова','с.Угут - д.Малоюганский','г.Сургут - п.Банный','с.Сытомино - п.Горный']
for year,src,report,opens,closes,lengths in [
 (2025,'status-1496-attachment-5.pdf','2025-04-07',['2024-12-19','2024-12-19','2024-12-29','2024-12-10','2024-12-09','2024-12-25','2025-01-10','2024-12-20','2024-12-25'],['','2025-04-05','2025-03-21','2025-04-03','2025-04-01','2025-04-01','2025-04-01','2025-04-01','2025-04-01'],[49.565,29.830,22.360,14.225,4,7.744,20.975,4,34.442]),
 (2026,'status-1924-attachment-4.pdf','2026-03-30',['2025-12-15','2025-12-15','2025-12-19','2025-12-03','2025-12-10','2025-12-12','2025-12-12','2025-12-20','2025-12-16'],['','','2026-03-27','','','2026-03-27','2026-03-27','2026-03-27','2026-03-27'],[49.565,29.830,22.360,14.225,2.9,7.744,20.975,2.06,34.442])]:
 for i,(label,op,cl,km) in enumerate(zip(labels,opens,closes,lengths)):
  limit=5 if not cl else ''
  verified.append(dict(source_file=src,pdf_page=1,report_date=report,season_end_year=year,district='Нижневартовский район' if i<5 else 'Сургутский район',route=label,road_km=km,opening_date=op,closure_date=cl,weight_limit_tonnes=limit,restriction_start_date=('2025-03-12' if year==2025 else '2026-03-14') if limit else '',status='closed actual as reported' if cl else 'operating with weight restriction as reported',verification='transcribed and checked against rendered PDF page; closure date kept separate from order date'))
write('verified-route-seasons.csv',verified)
districtrows=[]
for year,src,pub,items in [
 (2024,'status-991.html','2024-04-09',[('Кондинский район','2024-03-25'),('Ханты-Мансийский район','2024-04-05'),('Сургутский район','2024-04-08')]),
 (2025,'status-1498.html','2025-04-08',[(d,'') for d in ['Кондинский район','Белоярский район','Ханты-Мансийский район','Сургутский район','Октябрьский район','Березовский район']]),
 (2026,'status-1930.html','2026-04-06',[('Кондинский район','2026-03-26'),('Ханты-Мансийский район','2026-03-27'),('Сургутский район','2026-03-27'),('Октябрьский район','2026-04-01'),('Белоярский район','2026-04-01'),('Березовский район','2026-03-27')])]:
 for d,closed in items:districtrows.append(dict(source_file=src,publication_date=pub,season_end_year=year,district=d,effective_closure_date=closed,latest_confirmed_closed_date=pub,status='all district intermunicipal winter routes reported closed',precision='district aggregate; do not assign independently to every crossing'))
write('district-closure-history.csv',districtrows)
announcements=[dict(source_file='status-984.html',publication_date='2024-04-04',coverage='Ханты-Мансийский район; часть Октябрьского района',event_date='2024-04-05',classification='planned/announced closure',verification='announcement published before effective date'),dict(source_file='status-1498.html',publication_date='2025-04-08',coverage='п.Белорусский - с.Ларьяк; last operating regional winter road',event_date='2025-04-10',classification='planned/announced closure',verification='separate from later actual closure confirmation'),dict(source_file='status-1923.html',publication_date='2026-03-27',coverage='remaining Октябрьский район roads/crossings',event_date='2026-04-01',classification='planned/announced closure',verification='separate from later actual district confirmation')]
write('planned-closure-announcements.csv',announcements)
write('region-season-completion.csv',[dict(source_file='status-1002.html',publication_date='2024-04-16',season_end_year=2024,coverage='all intermunicipal winter roads and ice crossings of KhMAO-Yugra',status='all closed actual confirmation'),dict(source_file='status-1504.html',publication_date='2025-04-10',season_end_year=2025,coverage='all intermunicipal winter roads and ice crossings of KhMAO-Yugra',status='all closed actual confirmation')])
