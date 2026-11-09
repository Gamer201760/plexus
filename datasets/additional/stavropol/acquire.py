import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
RAW = ROOT / 'data/additional/stavropol/raw'

def fetch(entry):
    path = RAW / entry['filename']
    result = dict(entry, retrieved_at=datetime.now(timezone.utc).isoformat())
    try:
        temporary = path.with_suffix(path.suffix + '.part')
        response = subprocess.run(['curl','--http1.1','-fsSL','--connect-timeout','20','--max-time','600','--max-filesize','250000000','--output',str(temporary),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}\n',entry['url']], capture_output=True,text=True)
        fields = response.stdout.splitlines()
        result.update(http_status=int(fields[0]) if fields else None, final_url=fields[1] if len(fields)>1 else None, content_type=fields[2] if len(fields)>2 else None, tls_verification=True, client='system curl HTTP1.1')
        if response.returncode:
            raise RuntimeError(response.stderr[-500:])
        temporary.replace(path)
        with path.open('rb') as source:
            digest = hashlib.file_digest(source,'sha256').hexdigest()
        result.update(status='downloaded', path=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=digest)
    except Exception as error:
        result.update(status='blocked', error=str(error))
    return result

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = META / 'downloads.json'
    old = json.loads(manifest.read_text()) if manifest.exists() else []
    obtained = {row['url'] for row in old if row['status']=='downloaded'}
    sources = json.loads((META / 'sources.json').read_text())
    pending = [row for row in sources if row['url'] not in obtained]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(fetch, entry) for entry in pending]):
            result = future.result()
            old.append(result)
            manifest.write_text(json.dumps(old, ensure_ascii=False, indent=2)+'\n')
            print(result['filename'], result['status'], result.get('bytes', result.get('error')), flush=True)

if __name__ == '__main__':
    main()
