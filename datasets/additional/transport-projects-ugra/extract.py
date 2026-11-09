"""Rebuild a curated, source-checked project pilot from downloaded originals."""
import hashlib,json,re,subprocess
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
BASE=ROOT/'data/additional/transport-projects-ugra'; RAW=BASE/'raw'; OUT=BASE/'derived'; OUT.mkdir(exist_ok=True)
manifest=json.loads((HERE/'manifest.json').read_text()); sources={r['id']:r for r in manifest['sources']}
subprocess.run(['pdftotext','-layout',str(RAW/'capital-investment-plan-2026-2028.pdf'),str(RAW/'capital-investment-plan-2026-2028.txt')],check=True)
pages=(RAW/'capital-investment-plan-2026-2028.txt').read_text().split('\f')
class Plain(HTMLParser):
 def __init__(self): super().__init__(); self.parts=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style'):self.skip+=1
 def handle_endtag(self,t):
  if t in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,d):
  if not self.skip:self.parts.append(d)
html={}
for sid in ['kumin_tynkul','ob_opening']:
 p=Plain();p.feed((RAW/sources[sid]['filename']).read_text());html[sid]=' '.join(' '.join(p.parts).split())
 (OUT/(sid+'.txt')).write_text(html[sid]+'\n')
def norm(s):return re.sub(r'\s+',' ',s).replace('\xa0',' ')
def ref(sid,page=None,row=None):return dict(source_id=sid,url=sources[sid]['url'],page_pdf_1based=page,page_printed=2510+page if page else None,table_row=row)
projects=[
 dict(project_id='surgut_ob_bridge',name='Мостовой переход через реку Обь в районе Сургута',route_reference='Южный обход Сургута; река Обь',geometry=None,geometry_status='not_collected',sources=['capital_plan','ob_opening']),
 dict(project_id='surgut_east_exit',name='Восточная объездная дорога Сургута, 2 очередь: съезд на Нижневартовское шоссе',route_reference='Сургут; Восточная объездная дорога — Нижневартовское шоссе',geometry=None,geometry_status='not_collected',sources=['capital_plan']),
 dict(project_id='uray_bypass',name='Реконструкция объездной автомобильной дороги Урая',route_reference='Урай; объездная автомобильная дорога',geometry=None,geometry_status='not_collected',sources=['capital_plan']),
 dict(project_id='kumin_tynkul',name='Пусковой комплекс Куминский — Тынкуль',route_reference='Коридор Тюмень — Нижняя Тавда — Междуреченский — Урай — Нягань — Приобье',geometry=None,geometry_status='not_collected',sources=['kumin_tynkul'])]
budget=[]
# Values retained in source units: thousand RUB, prices of respective implementation years.
for pid,p,row,length,period,cost,remaining,annual,guard in [
 ('surgut_ob_bridge',43,9,45.56,'2022–2026 (СМР)','76491114.9','3308056.0',['3308056.0','0.0','0.0'],'76 491 114,9'),
 ('surgut_ob_bridge',43,10,45.56,'2019–2022 (ПИР); 2022–2026 (прочие затраты)','2646803.2','679934.1',['679934.1','0.0','0.0'],'2 646 803,2'),
 ('surgut_east_exit',19,26,2.266,'2023 (ПИР); 2025–2028 (СМР)','4293076.9','3254533.6',['1197919.4','1150064.3','906549.9'],'4 293 076,9'),
 ('uray_bypass',21,1,5.8,'2024–2025 (ПИР); 2026–2027 (СМР)','1013287.4','1013287.4',['315011.6','698275.8','0.0'],'1 013 287,4')]:
 assert guard in norm(pages[p-1]),(p,guard)
 from decimal import Decimal
 assert sum(map(Decimal,annual))==Decimal(remaining)
 budget.append(dict(budget_line_id=f'capital_plan_p{p}_r{row}',project_id=pid,length_km=length,length_scope='whole_project_not_bridge_span',work_period=period,planned_object_cost=cost,remaining_cost_at_2026_01_01=remaining,investments_by_year=dict(zip(['2026','2027','2028'],annual)),currency_unit='thousand_RUB',price_basis='prices_of_respective_implementation_years',classification='budget_plan_not_actual_expenditure',adoption_status='not_verified',source_asterisk=pid=='uray_bypass',provenance=ref('capital_plan',p,row)))
facts=[]
def fact(pid,metric,value,unit,period,kind,sid,guard,scope=None):
 assert guard in html[sid],(sid,guard)
 facts.append(dict(fact_id=f'{pid}_{metric}',project_id=pid,metric=metric,value=value,unit=unit,period=period,classification=kind,scope=scope,provenance=ref(sid)))
for metric,value,unit,guard in [('length',35.4,'km','35,4 км'),('lanes',2,'count','Число полос движения 2'),('road_category','III','category','Категория дороги III'),('bridge_count',1,'count','1/83,3'),('bridge_length',83.3,'m','1/83,3'),('contract_cost','3986849.92','thousand_RUB','3 986 849,92'),('construction_period','2018–2020','year_range','2018-2020'),('commissioned',True,'boolean','Сданный в эксплуатацию')]:
 fact('kumin_tynkul',metric,value,unit,'2018–2020','contractor_reported', 'kumin_tynkul',guard)
for metric,value,unit,kind,guard,scope in [('opening_date','2025-10-15','date','reported_event','15 октября 2025',None),('bridge_length',1.7,'km','reported_technical','длиной 1,7 км','rounded_bridge_length'),('lanes',4,'count','reported_technical','Четырехполосный мост',None),('planned_capacity',13000,'vehicles/day','design_capacity_not_observed_traffic','13 тысяч автомашин в сутки','South_bypass_road'),('spans',15,'count','reported_technical','15 пролетов',None),('supports',16,'count','reported_technical','16 опор',None)]:
 fact('surgut_ob_bridge',metric,value,unit,'2025-10-15',kind,'ob_opening',guard,scope)
for name,data in [('projects.json',projects),('budget_lines.json',budget),('project_facts.json',facts)]: (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
validation=dict(projects=len(projects),budget_lines=len(budget),technical_and_event_facts=len(facts),source_guards='passed',annual_totals_equal_remaining='passed',geometry_count=0,observed_traffic_records=0,roi_records=0)
(OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
outputs=[RAW/'capital-investment-plan-2026-2028.txt',*sorted(OUT.glob('*'))]
manifest['derived_files']=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in outputs if p.is_file()]
(HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(validation))
