import requests,ssl,urllib3,time,json,hashlib,datetime,pathlib,concurrent.futures,sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse,unquote
ROOT=pathlib.Path(__file__).resolve().parent;RAW=ROOT.parents[2]/'data/additional/road-assets-ugra/raw'
class WeakTLSAdapter(requests.adapters.HTTPAdapter):
 def init_poolmanager(self,*a,**kw):
  ctx=ssl.create_default_context();ctx.set_ciphers('DEFAULT:@SECLEVEL=0');ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE;kw['ssl_context']=ctx;return super().init_poolmanager(*a,**kw)
def fetch(item):
 time.sleep(0.7);n,u=item;o=dict(filename=n,url=u,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),tls_verification=False,tls_fallback='Ugrador only: DEFAULT:@SECLEVEL=0; weak end-entity certificate; no credentials')
 try:
  assert urlparse(u).hostname=='www.ugrador.ru'
  s=requests.Session();s.mount('https://www.ugrador.ru',WeakTLSAdapter());r=s.get(u,verify=False,timeout=60);o.update(http_status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest());p=RAW/n;p.parent.mkdir(exist_ok=True);p.write_bytes(r.content);o['path']=str(p.relative_to(ROOT.parents[2]))
 except Exception as e:o.update(error=str(e))
 return o
def batch(items):
 rows=list(concurrent.futures.ThreadPoolExecutor(max_workers=1).map(fetch,items));p=ROOT/'downloads.json';old=json.loads(p.read_text()) if p.exists() else [];old.extend(rows);p.write_text(json.dumps(old,ensure_ascii=False,indent=2));print('Fetched',len(rows),'files; statuses:',{str(k):sum(x.get('http_status')==k for x in rows) for k in set(x.get('http_status') for x in rows)})
if __name__=='__main__':
 batch(json.loads((ROOT/'sources.json').read_text()))
