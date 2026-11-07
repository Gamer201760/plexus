from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from threading import Lock
import hashlib,json,os,re,subprocess,tempfile,time,sys

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'data/additional/rfsd'
raw=BASE/'raw'
revision=json.loads((raw/'dataset_info.json').read_text())['sha']
inventory=json.loads((raw/'source_inventory.json').read_text())
state=BASE/'derived/range_progress.json'
log=BASE/'derived/download_progress.log'
done=json.loads(state.read_text()) if state.exists() else {}
lock=Lock()
files=[x for x in inventory if x['path'].endswith('.parquet') and ('--all' in sys.argv or 'year=2025/' in x['path'])]
groups={}
for item in files:
    p=raw/item['path'];p.parent.mkdir(parents=True,exist_ok=True)
    backlog=raw/'backlog'/(item['path']+'.partial')
    if not p.exists() and backlog.exists():backlog.replace(p)
    if not state.exists():
        size=p.stat().st_size if p.exists() else 0
        done[item['path']]=[[0,size-1]] if size else []
    cursor=0;gaps=[];tasks=[]
    for a,b in sorted(done.get(item['path'],[])):
        if a>cursor:gaps.append((cursor,a-1))
        cursor=max(cursor,b+1)
    if cursor<item['size']:gaps.append((cursor,item['size']-1))
    for a,b in gaps:
        for lo in range(a,b+1,1024*1024):
            tasks.append((item,lo,min(lo+1024*1024,b+1)-1))
    groups[item['path']]=tasks
    if not p.exists():p.touch()
state.write_text(json.dumps(done,indent=2))

def record(path,lo,hi,code):
    with lock:
        done.setdefault(path,[]).append([lo,hi])
        tmp=state.with_suffix('.tmp');tmp.write_text(json.dumps(done,indent=2));tmp.replace(state)
        total=sum(b-a+1 for ranges in done.values() for a,b in ranges)
        event={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'path':path,'lo':lo,'hi':hi,'curl_code':code,'validated_bytes':total}
        with log.open('a') as f:f.write(json.dumps(event)+'\n')
        if total//(32*1024*1024)!=(total-(hi-lo+1))//(32*1024*1024):print(event,flush=True)

def transfer(task):
    item,lo,hi=task;fd=os.open(raw/item['path'],os.O_WRONLY)
    url=f"https://huggingface.co/datasets/irlspbru/RFSD/resolve/{revision}/{item['path']}?download=true"
    try:
        for attempt in range(16):
            if lo>hi:return
            with tempfile.TemporaryFile() as headers:
                proc=subprocess.Popen(['curl','--http1.1','-fsSL','--max-time','1800','--range',f'{lo}-{hi}','--dump-header',f'/dev/fd/{headers.fileno()}',url],stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=(headers.fileno(),))
                pos=lo;oversized=False
                while chunk:=proc.stdout.read(64*1024):
                    if pos+len(chunk)>hi+1:
                        proc.kill();oversized=True;break
                    os.pwrite(fd,chunk,pos);pos+=len(chunk)
                err=proc.stderr.read().decode();code=proc.wait();headers.seek(0);head=headers.read().decode()
                ranges=re.findall(r'content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)',head,re.I)
                valid=not oversized and ranges and tuple(map(int,ranges[-1]))==(lo,hi,item['size'])
                if valid and pos>lo:
                    record(item['path'],lo,pos-1,code);lo=pos
                    if lo>hi:return
                with lock:
                    with log.open('a') as f:f.write(json.dumps({'event':'retry','path':item['path'],'lo':lo,'hi':hi,'code':code,'bytes_received':pos-lo,'error':err[-300:]})+'\n')
                if attempt==15:raise RuntimeError(f'{item["path"]} {lo}-{hi} failed {code} {err[-200:]}')
    finally:os.close(fd)

latest=groups.pop('RFSD/year=2025/part-0.parquet',[])
historical=[]
for index in range(max(map(len,groups.values()),default=0)):
    for path in reversed(list(groups)):
        if index<len(groups[path]):historical.append(groups[path][index])
with ThreadPoolExecutor(max_workers=32 if not historical else 8) as current,ThreadPoolExecutor(max_workers=24) as history:
    futures=[current.submit(transfer,t) for t in latest]+[history.submit(transfer,t) for t in historical]
    for future in as_completed(futures):future.result()
for item in files:
    p=raw/item['path'];h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
    assert p.stat().st_size==item['size'] and h==item['lfs']['oid'],str(p)
print('REQUESTED FILES VERIFIED',len(files),flush=True)
