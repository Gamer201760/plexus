from pathlib import Path
from bs4 import BeautifulSoup
import csv,json,re,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3];RAW=ROOT/'data/additional/northern-delivery/raw';OUT=ROOT/'data/additional/northern-delivery';OUT.mkdir(parents=True,exist_ok=True)
def write(name,rows):
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for p in RAW.glob('*.html'):
 s=BeautifulSoup(p.read_bytes(),'html.parser');(OUT/(p.stem+'.txt')).write_text(s.get_text('\n',strip=True))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
for p in RAW.glob('*.docx'):
 with zipfile.ZipFile(p) as z:r=ET.fromstring(z.read('word/document.xml'))
 paras=[''.join(t.text or '' for t in q.findall('.//w:t',ns)) for q in r.findall('.//w:p',ns)];(OUT/(p.stem+'.txt')).write_text('\n'.join(paras))
 if '286' in p.name:
  tab=max(r.findall('.//w:tbl',ns),key=lambda q:len(q.findall('./w:tr',ns)));rows=[];section='';subsection=''
  for idx,tr in enumerate(tab.findall('./w:tr',ns),1):
   cells=[' '.join(''.join(t.text or '' for t in q.findall('.//w:t',ns)) for q in tc.findall('./w:p',ns)).strip() for tc in tr.findall('./w:tc',ns)]
   if len(cells)==1:
    if re.match(r'^[IVX]+\.',cells[0]):section=cells[0];subsection=''
    if re.match(r'^\d+\.',cells[0]):subsection=cells[0]
   elif len(cells)==2 and idx>1:rows.append({'source_file':p.name,'source_table_row':idx,'section':section,'subsection':subsection,'object_group':cells[0],'region':cells[1],'effective_revision':'2025-09-18','status':'statutory infrastructure group; may enumerate multiple physical assets'})
  write('infrastructure-286r-2025.csv',rows)
s=BeautifulSoup((RAW/'territories-portal.html').read_bytes(),'html.parser');first=s.find('strong',string=lambda t:t and 'Перечень территорий' in t);container=first.parent.parent;rows=[];region='All covered islands';seq=0
for el in container.find_all(['p','li'],recursive=False):
 txt=el.get_text(' ',strip=True)
 if el.find('strong'):
  if 'Перечень территорий' not in txt:region=txt
  continue
 if txt and not txt.startswith('(Позиция'):
  seq+=1;rows.append({'entry':seq,'region':region,'territory_clause':txt,'revision':'2025-09-01','status':'official portal edition; superseded by 2026-07-27 amendment'})
rows=[];region='All covered islands';seq=0
for el in container.find_all(recursive=False):
 txt=el.get_text(' ',strip=True)
 if el.name=='p' and el.find('strong'):
  if 'Перечень территорий' not in txt:region=txt
 elif el.name=='ul':
  for li in el.find_all('li',recursive=False):
   seq+=1;rows.append(dict(entry=seq,region=region,territory_clause=li.get_text(' ',strip=True),revision='2025-09-01',status='official portal edition; superseded by 2026-07-27 amendment'))
 elif el.name=='p' and txt and not txt.startswith('(Позиция'):
  seq+=1;rows.append(dict(entry=seq,region=region,territory_clause=txt,revision='2025-09-01',status='official portal edition; superseded by 2026-07-27 amendment'))
write('territories-current-2025.csv',rows)
consolidated=RAW/'territories-consolidated-2026.html'
if consolidated.exists():
 soup=BeautifulSoup(consolidated.read_bytes(),'html.parser');updated=[]
 islands='Все острова Северного Ледовитого океана и его морей, а также острова Берингова и Охотского морей'
 if islands not in soup.get_text(' ',strip=True):raise ValueError('Island clause missing from consolidated source')
 updated.append(dict(region='All covered islands',territory_clause=islands,revision='2026-07-27',source='territories-consolidated-2026.html',status='consolidated legal mirror; complete island clause'))
 for row in soup.find('table').find_all('tr'):
  cells=[cell.get_text(' ',strip=True) for cell in row.find_all(['td','th'],recursive=False)]
  if len(cells)==3 and cells[0] and cells[2]:
   updated.append(dict(region=cells[0],territory_clause=cells[2],revision='2026-07-27',source='territories-consolidated-2026.html',status='consolidated legal mirror; complete regional clause'))
 write('territories-consolidated-2026.csv',updated)
raw=(RAW/'portal-main.html').read_text();raw=raw.replace('\\"','"').replace('\\"','"')
records=[]
for j,label in [(1,'all cargo'),(2,'fuel-energy resources'),(3,'fuels and lubricants')]:
 def val(k):
  m=re.search('"'+k+r'"\s*:\s*([0-9.]+)',raw);return float(m[1]) if m else None
 records.append(dict(coverage='All northern-delivery regions',year=2026,as_of='2026-11-01',metric=label,actual_thousand_tonnes=val('current_value_2_'+str(j)),plan_thousand_tonnes=val('maximum_value_2_'+str(j)),status='official public dashboard actual versus plan',source_file='portal-main.html',note='categories can overlap; do not sum them'))
write('dashboard-plan-actual-2026.csv',records)
specs=[('supply-rosatom-2026.html','2026-11-02','Хабаровский край',2026,'all cargo carried by unified maritime operator',23000,'greater_than','actual'),('supply-rosatom-2026.html','2026-11-02','Республика Саха (Якутия)',2026,'diesel delivered by unified maritime operator',16800,'reported','actual'),('supply-rosatom-2026.html','2026-11-02','Чукотский автономный округ',2026,'all cargo carried by unified maritime operator',226000,'greater_than','actual'),('supply-rosatom-2026.html','2026-11-02','Чукотский автономный округ',2025,'all cargo in operator pilot',159200,'reported','actual'),('supply-taymyr-2026.html','2026-10-14','Таймырский Долгано-Ненецкий муниципальный округ',2026,'fuels lubricants and coal',36000,'greater_than','actual'),('supply-chukotka-2026.html','2026-10-12','Чукотский автономный округ',2026,'food cargo from start of navigation',17900,'reported','actual; 85.7 percent of planned sea delivery'),('supply-sakhalin-2026.html','2026-09-11','Сахалинская область',2026,'all cargo',59420,'reported','plan'),('supply-yugra-2026.html','2026-07-16','Ханты-Мансийский автономный округ - Югра',2026,'fuel-energy cargo by Ob-Irtysh waterways',33000,'greater_than','actual'),('supply-yugra-2026.html','2026-07-16','Ханты-Мансийский автономный округ - Югра',2026,'petroleum products',11400,'reported','actual'),('supply-yugra-2026.html','2026-07-16','Ханты-Мансийский автономный округ - Югра',2026,'coal',21700,'reported','actual')]
write('regional-supply-volumes.csv',[dict(source_file=f,publication_date=d,region=r,year=y,cargo=c,value=v,unit='tonnes',qualifier=q,status=s,note='partial category/operator scope; do not add overlapping rows') for f,d,r,y,c,v,q,s in specs])
print({p.name:sum(1 for _ in csv.DictReader(p.open())) for p in OUT.glob('*.csv')})
