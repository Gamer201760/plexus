"""Acquire pinned Geofabrik snapshot and verify supplier MD5; do not resume mutable latest."""
import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/additional/osm-ural/raw'
BASE='https://download.geofabrik.de/russia/'
NAME='ural-fed-district-261106.osm.pbf'
OUT.mkdir(parents=True,exist_ok=True)
files=[]
for name in [NAME+'.md5',NAME,'ural-fed-district.html']:
 p=OUT/name
 if not p.exists():
  tmp=p.with_suffix(p.suffix+'.partial')
  subprocess.run(['curl','-fL','--retry','3','--connect-timeout','30','--max-time','1800','-o',str(tmp),BASE+name],check=True)
  tmp.replace(p)
 files.append({'path':str(p.relative_to(ROOT)),'url':BASE+name,'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
expected=(OUT/(NAME+'.md5')).read_text().split()[0]
actual=hashlib.file_digest((OUT/NAME).open('rb'),'md5').hexdigest()
assert expected==actual,(expected,actual)
manifest={'retrieved_at':datetime.now(timezone.utc).isoformat(),'snapshot':'261106','geography':'Ural Federal District, includes Yugra and neighboring regions','license':'ODbL-1.0; OpenStreetMap contributors','supplier_md5_verified':True,'files':files}
(ROOT/'datasets/additional/osm-ural/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False))
