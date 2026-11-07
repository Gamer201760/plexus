import csv
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
OUT = ROOT / 'data/additional/seasonal-closures'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = ROOT / 'datasets/additional/transport-operations/manifest.jsonl'
    sources = {row['url']: row for row in map(json.loads, manifest.read_text().splitlines())}
    articles = {}
    for source in sources.values():
        if source['status'] != 'downloaded' or 'mchs.gov.ru' not in source['url'] or not source['path'].endswith('.html'):
            continue
        soup = BeautifulSoup((ROOT / source['path']).read_bytes(), 'lxml')
        article = soup.select_one('article')
        if article is None:
            continue
        date = soup.select_one('[itemprop="datePublished"]')
        text = article.get_text(' ', strip=True)
        if not re.search('переправ|зимник', text, re.I):
            continue
        articles[source['url']] = dict(source_url=source['url'], source_sha256=source['sha256'], source_path=source['path'], published_at=date.get('content', '') if date else '', title=soup.title.get_text(' ', strip=True), text=text)
    (OUT / 'articles.json').write_text(json.dumps(list(articles.values()), ensure_ascii=False, indent=2) + '\n')
    events = []
    for annotation in json.loads((META / 'annotations.json').read_text()):
        matches = [article for url, article in articles.items() if url.endswith('/' + annotation['source_id']) and annotation['source_host'] in url]
        if len(matches) != 1:
            raise ValueError(f'Source ambiguous or missing: {annotation}')
        article = matches[0]
        normalized = re.sub(r'\s+', ' ', article['text'])
        if annotation['anchor'] not in normalized:
            raise ValueError(f'Anchor missing: {annotation}')
        events.append(dict(annotation, published_at=article['published_at'], source_url=article['source_url'], source_sha256=article['source_sha256'], source_path=article['source_path']))
    with (OUT / 'events.csv').open('w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=list(events[0]))
        writer.writeheader()
        writer.writerows(events)
    profile = dict(articles=len(articles), reviewed_observations=len(events), reviewed_regions=len({row['region'] for row in events}), event_date_rows=sum(bool(row['event_date']) for row in events), snapshot_rows=sum(not row['event_date'] for row in events), national_complete=False)
    (META / 'profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(profile))


if __name__ == '__main__':
    main()
