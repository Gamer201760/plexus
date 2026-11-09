"""Download pinned source URLs; keep HTTP outcomes and hashes. Python stdlib only."""
import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'data/additional/transport-projects-ugra/raw'
SOURCES=[
 {'id':'capital_plan','url':'https://www.dumahmao.ru/povest/0750_3/06/252.pdf','filename':'capital-investment-plan-2026-2028.pdf','publisher':'Дума ХМАО — Югры','source_type':'government_budget_attachment'},
 {'id':'kumin_tynkul','url':'https://www.avtoban.ru/project/tumen-ntavda/','filename':'kumin-tynkul-contractor.html','publisher':'Автобан','source_type':'contractor_project_card'},
 {'id':'ob_opening','url':'https://npsgk.ru/news/dvizhenie-po-novomu-mostu-cherez-ob-v-surgute-otkryto/','filename':'ob-bridge-opening-2025.html','publisher':'Нацпроектстрой','source_type':'contractor_release','publication_date':'2025-10-15'},
 {'id':'ob_progress','url':'https://www.ugrador.ru/news/novosti_nacproekt/1596/','filename':'ob-bridge-progress-2025.html','publisher':'Управление автомобильных дорог Югры','source_type':'road_authority_release','publication_date':'2025-08-20'},
]
def get(s):
 p=OUT/s['filename']; tmp=p.with_suffix(p.suffix+'.partial')
 r=subprocess.run(['curl','-L','--retry','2','--connect-timeout','20','--max-time','100','-sS','-A','casechamp-research/0.1','-w','%{http_code}','-o',str(tmp),s['url']],capture_output=True,text=True)
 x={**s,'retrieved_at':datetime.now(timezone.utc).isoformat(),'http_status':r.stdout,'curl_exit':r.returncode}
 if r.returncode==0 and r.stdout=='200' and tmp.exists() and tmp.stat().st_size>100:
  if p.suffix=='.pdf' and not tmp.read_bytes().startswith(b'%PDF'): x.update(status='failed',error='not_pdf')
  else:
   tmp.replace(p);x.update(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='downloaded')
 else:x.update(status='failed',error=r.stderr[:500])
 return x
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 rows=list(ThreadPoolExecutor(max_workers=4).map(get,SOURCES))
 (HERE/'manifest.json').write_text(json.dumps({'sources':rows},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps([{k:r.get(k) for k in ['id','status','bytes','http_status','error']} for r in rows],ensure_ascii=False))
