import concurrent.futures,datetime,hashlib,json,pathlib,requests
from urllib.parse import urlparse
ROOT=pathlib.Path(__file__).resolve().parents[3]
META=pathlib.Path(__file__).resolve().parent
RAW=ROOT/'data/additional/northern-delivery/raw'
URLS={
 'documents-index.html':'https://szavoz.gov.ru/portal-main/documents/',
 'territories-decree-page.html':'https://szavoz.gov.ru/portal-main/documents/knaotq0gqxruj7gkuhyv1zyl/',
 'supply-rosatom-2026.html':'https://szavoz.gov.ru/portal-main/newsandevents/dia7bcavathuofe466mzobyr/',
 'supply-taymyr-2026.html':'https://szavoz.gov.ru/portal-main/newsandevents/s4j6hcnqhbdjgpoziakka15e/',
 'supply-chukotka-2026.html':'https://szavoz.gov.ru/portal-main/newsandevents/sdcj4a9omd3hcym2748i88d5/',
 'supply-nenets-2026.html':'https://szavoz.gov.ru/portal-main/newsandevents/vmeck70z2ex05mpz9ufa8bfa/',
 'supply-sakhalin-2026.html':'https://szavoz.gov.ru/portal-main/newsandevents/yvnlf5syh30e0vt42esuuqfl/',
 'supply-yugra-2026.html':'https://szavoz.gov.ru/portal-main/newsandevents/q6zo4li2iutkgs05xktsyrom/',
 'infrastructure-amendment.html':'https://meganorm.ru/mega_doc/dop1/85/rasporyazhenie_pravitelstva_rf_ot_09_02_2024_N_286-r_red_ot/0/rasporyazhenie_pravitelstva_rf_ot_18_09_2025_N_2560-r_o.html'}
def get(item):
 n,u=item;o={'filename':n,'url':u,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tls_verification':True}
 try:
  try:r=requests.get(u,timeout=60)
  except requests.exceptions.SSLError as error:
   if urlparse(u).hostname!='szavoz.gov.ru':raise
   o.update(tls_verification=False,initial_tls_error=str(error));r=requests.get(u,timeout=60,verify=False)
  r.raise_for_status();p=RAW/n;p.write_bytes(r.content);o.update(http_status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),path=str(p.relative_to(ROOT)))
 except Exception as e:o['error']=str(e)
 return o
if __name__=='__main__':
 RAW.mkdir(parents=True,exist_ok=True)
 rows=list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(get,URLS.items()));p=META/'downloads.json';old=json.loads(p.read_text());old.extend(rows);p.write_text(json.dumps(old,ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False,indent=2))
