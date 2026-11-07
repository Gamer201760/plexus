from pathlib import Path
import csv,json,re,subprocess
ROOT=Path(__file__).resolve().parents[3];RAW=ROOT/'data/additional/traffic-surveys/raw';OUT=ROOT/'data/additional/traffic-surveys';OUT.mkdir(exist_ok=True,parents=True)
def write(name,rows):
 if not rows:return
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for pdf in RAW.glob('*.pdf'):
 txt=OUT/(pdf.stem+'.txt');subprocess.run(['pdftotext','-layout',str(pdf),str(txt)],check=True)
 pages=txt.read_text().split('\f');pages=pages[:-1] if not pages[-1].strip() else pages
 with (OUT/(pdf.stem+'-pages.jsonl')).open('w') as f:
  for i,p in enumerate(pages,1):f.write(json.dumps({'source_file':pdf.name,'pdf_page':i,'text':p},ensure_ascii=False)+'\n')
 if pdf.stem=='nefteyugansk-ksodd':
  rows=[];active=False;pending=''
  for i,p in enumerate(pages,1):
   if 'Таблица 11 – Параметры' in p:active=True
   if active and i>94:break
   if not active:continue
   for line in p.splitlines():
    m=re.match(r'^\s*(.*?)\s{2,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+,\d+)\s*$',line)
    if m and any(c.isalpha() for c in m[1]):
     street=re.sub(r'^\d+\s+','',m[1]);rows.append({'pdf_page':i,'street':street,'speed_kmh':m[2],'intensity_pcu_per_hour':m[3],'density_vehicles_per_km':m[4],'capacity_pcu_per_hour':m[5],'load_ratio':m[6].replace(',','.'),'status':'observed intensity; other columns derived in report','table':11})
  write('nefteyugansk-observed-parameters.csv',rows)

p=OUT/'nefteyugansk-observed-parameters.csv'
with p.open() as f:rows=list(csv.DictReader(f))
for page,street,vals in [
 (90,'Нефтяников (от ул. Александра Филимонова)',[20,1242,62,1800,.69]),
 (90,'Александра Филимонова (от ул. Набережная)',[20,650,33,1440,.45]),
 (90,'Александра Филимонова (от ул. Мамонтовская)',[20,830,42,1440,.58]),
 (91,'Набережная (от ул. Александра Филимонова)',[25,2144,86,2880,.74]),
 (93,'Сургутская (от а/д Нефтеюганск - Левый берег р. Обь)',[60,1209,20,2400,.50])]:
 rows.append(dict(zip(rows[0], [page,street,*vals,'observed intensity; other columns derived in report',11])))
write('nefteyugansk-observed-parameters.csv',rows)
locations=['Каквинская / Черняховского / Загородка','Подъезд к г. Серов (км 349-км 352+770) / Соединительная дорога от км 349+047','Кутузова / Серов-Птицефабрика / съезд развязки км 0','Серов-Североуральск-Ивдель / Серов-Птицефабрика','Седова / Металлистов','Кирова / Победы','Кирова / Каквинская','Автодорожная / Западная','Победы / Ферросплавщиков','Каквинская / Угольная','Нансена / Фуфачева / Красноармейская / проспект Серова','Визе / Паровозников','Ленина / Льва Толстого','Карла Маркса / Каляева','Циолковского / Ленина']
values=[(2299,3600,25.5,.64),(2163,3600,24,.60),(1489,3600,16.5,.41),(637,3600,7.1,.35),(138,1800,5.2,.08),(223,1800,3.7,.12),(129,1800,2.2,.07),(53,1800,.8,.03),(756,1400,18.9,.54),(707,1400,17.7,.51),(522,1400,13.1,.37),(462,1400,11.6,.21),(306,1400,7.7,.22),(304,1400,7.6,.22),(230,1000,5.8,.23)]
rows=[]
for i,(loc,v) in enumerate(zip(locations,values),1):
 rows.append(dict(site_id=i,location=loc,intensity_pcu_per_hour=v[0],capacity_pcu_per_hour=v[1],density_reported_pcu=v[2],load_ratio=v[3],pdf_page=124 if i<8 else 125,table=25,period='September 2018; peak hour (see annex)',status='observed intensity; capacity/density/load derived as reported'))
write('serov-observed-parameters.csv',rows)
text=(OUT/'belovo-ksodd.txt').read_text();pages=text.split('\f');rows=[];site=0;sites=[]
for pi,page in enumerate(pages,1):
 if pi<195:continue
 matches=list(re.finditer(r'Таблица ([12]) [–-] Интенсивность движения транспортных потоков',page))
 for mi,m in enumerate(matches):
  tab=int(m[1]);site+=tab==1
  tail=page[m.end():]; next_table=re.search(r'Таблица \d+',tail); block=page[m.start():m.end()+next_table.start() if next_table else len(page)]
  total=next((l for l in block.splitlines() if 'ИТОГО, факт.ед.:' in l),None)
  if not total:continue
  nums=list(re.finditer(r'\d+|-',total[total.index(':')+1:]));offset=total.index(':')+1
  centers=[offset+(x.start()+x.end())/2 for x in nums]
  for line in block.splitlines():
   vm=re.match(r'\s*(трамвай|большой автобус|средний автобус|микроавтобус|легковой|грузовые\s*[<>]?\s*\d+(?:-\d+)?\s*т\.)',line)
   if not vm:continue
   vals=['']*len(centers)
   for token in re.finditer(r'\d+|-',line[vm.end():]):
    center=vm.end()+(token.start()+token.end())/2;col=min(range(len(centers)),key=lambda c:abs(centers[c]-center));vals[col]=token[0]
   for col,v in enumerate(vals,1):rows.append({'site_sequence':site,'pdf_page':pi,'table':tab,'peak_period':'morning' if tab==1 else 'evening','vehicle_type':vm[1],'column_index':col,'count_raw':v,'unit':'actual vehicles in reported peak survey interval','status':'observed','direction_mapping':'original fixed-width column index; consult same PDF page headers','missing_value_policy':'empty cell and dash preserved verbatim; neither converted to zero'})
  if tab==1:sites.append({'site_sequence':site,'counts_pdf_page':pi,'preceding_context':'\n'.join(pages[max(0,pi-4):pi-1])})
write('belovo-observed-vehicle-counts.csv',rows);write('belovo-survey-site-context.csv',sites)
print('Final CSV rows:',{p.name:sum(1 for _ in csv.DictReader(p.open())) for p in OUT.glob('*.csv')})
