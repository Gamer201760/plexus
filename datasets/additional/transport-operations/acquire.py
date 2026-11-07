import argparse
import csv
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
RAW = ROOT / 'data/additional/transport-operations'
LOCK = threading.Lock()
HOST_LOCKS = {}


def inventory():
    sources = {}
    for path in sorted((ROOT / 'data_manual/regions').glob('*.csv')):
        if '_remote' in path.name:
            continue
        for row in csv.DictReader(path.open(encoding='utf-8-sig')):
            url = row.get('source_url', '').strip()
            if not url.startswith(('https://', 'http://')):
                continue
            entry = sources.setdefault(url, {'url': url, 'regions': [], 'kind': 'regional_transport_source'})
            if path.stem not in entry['regions']:
                entry['regions'].append(path.stem)
    for entry in json.loads((META / 'extra_sources.json').read_text()):
        sources[entry['url']] = entry
    return list(sources.values())


def extract(path, content_type):
    if path.suffix == '.pdf':
        reader = PdfReader(path)
        pages = [{'page': i + 1, 'text': page.extract_text()} for i, page in enumerate(reader.pages)]
        target = path.with_suffix('.pages.json')
        target.write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
        return {'extracted_path': str(target.relative_to(ROOT)), 'pages': len(pages)}
    if path.suffix != '.html':
        return {}
    soup = BeautifulSoup(path.read_bytes(), 'lxml')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text('\n', strip=True)
    target = path.with_suffix('.txt')
    target.write_text(text, encoding='utf-8')
    challenge = any(term in title.lower() for term in ['captcha', 'just a moment', 'access denied', '403 forbidden', 'ddos-guard'])
    return {'extracted_path': str(target.relative_to(ROOT)), 'title': title, 'text_chars': len(text), 'content_review': 'possible_access_challenge' if challenge or len(text) < 200 else 'not_manually_reviewed'}


def download(entry):
    result = dict(entry, retrieved_at=datetime.now(timezone.utc).isoformat())
    name = hashlib.sha256(entry['url'].encode()).hexdigest()[:20]
    host = urlparse(entry['url']).netloc
    with LOCK:
        gate = HOST_LOCKS.setdefault(host, threading.Semaphore(2))
    try:
        with gate, requests.get(entry['url'], timeout=(15, 45), stream=True, headers={'User-Agent': 'Mozilla/5.0 (compatible; research-data-archive/1.0)'}) as response:
            result.update(http_status=response.status_code, final_url=response.url, content_type=response.headers.get('Content-Type'), etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'))
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').lower()
            suffix = '.pdf' if 'pdf' in content_type or urlparse(response.url).path.lower().endswith('.pdf') else '.html' if 'html' in content_type else '.bin'
            path = RAW / (name + suffix)
            partial = path.with_suffix(suffix + '.part')
            size = 0
            digest = hashlib.sha256()
            with partial.open('wb') as output:
                for chunk in response.iter_content(262144):
                    size += len(chunk)
                    if size > 30 * 1024 * 1024:
                        raise ValueError('Per-source 30 MiB limit exceeded; partial removed')
                    output.write(chunk)
                    digest.update(chunk)
            partial.replace(path)
            result.update(status='downloaded', path=str(path.relative_to(ROOT)), bytes=size, sha256=digest.hexdigest())
            try:
                result.update(extract(path, content_type))
            except Exception as error:
                result['extraction_error'] = str(error)[:300]
            if result.get('content_review') == 'possible_access_challenge':
                result['status'] = 'needs_content_review'
    except Exception as error:
        result.update(status='blocked', error=str(error)[:400])
        for partial in RAW.glob(name + '*.part'):
            partial.unlink()
    with LOCK:
        with (META / 'manifest.jsonl').open('a', encoding='utf-8') as output:
            output.write(json.dumps(result, ensure_ascii=False) + '\n')
        print(result['status'], name, flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--retry-blocked', action='store_true')
    parser.add_argument('--retry-transient', action='store_true')
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = META / 'manifest.jsonl'
    previous = {row['url']: row for row in map(json.loads, manifest.read_text().splitlines())} if manifest.exists() else {}
    sources = inventory()
    (META / 'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n')
    pending = []
    for entry in sources:
        old = previous.get(entry['url'])
        transient = old and any(term in old.get('error', '') for term in ['timed out', '504 Server', '502 Server'])
        if old is None or (args.retry_blocked and old['status'] == 'blocked') or (args.retry_transient and transient):
            pending.append(entry)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(download, pending))


if __name__ == '__main__':
    main()
