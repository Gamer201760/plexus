"""Download the identified official snapshot; do not silently switch registry editions."""
from pathlib import Path
import json, subprocess
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'data/additional/medical-ugra/raw'
SOURCES={
 'ofoms-register-index.html':'https://www.ofoms.ru/страницы/реестры-и-справочники',
 'trmo052026.xlsx':'https://www.ofoms.ru/uploads/files/7eb202f860af4b038bcfba67ec9e03ea/trmo052026.xlsx',
 'city-ugut.html':'https://www.ofoms.ru/организации/city/ugut',
}
if __name__=='__main__':
    RAW.mkdir(parents=True,exist_ok=True); logs=[]
    for name,url in SOURCES.items():
        temp=RAW/(name+'.partial')
        r=subprocess.run(['curl','--fail','-L','--max-time','60','--retry','2','-sS',url,'-o',str(temp)],capture_output=True,text=True)
        logs.append(dict(url=url,path=str((RAW/name).relative_to(ROOT)),utc=datetime.now(timezone.utc).isoformat(),exit_code=r.returncode,error=r.stderr))
        if r.returncode==0:temp.replace(RAW/name)
    (Path(__file__).parent/'download-log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n')
    if any(r['exit_code'] for r in logs):raise SystemExit('Some downloads failed; inspect download-log.json')
