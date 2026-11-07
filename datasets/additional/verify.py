import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
META = Path(__file__).resolve().parent
RAW = ROOT / 'data/additional'


def entries(value):
    if isinstance(value, dict):
        artifact_path = value.get('path', value.get('file'))
        if isinstance(artifact_path, str) and isinstance(value.get('sha256'), str):
            yield dict(value, path=artifact_path)
        for nested in value.values():
            yield from entries(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from entries(nested)


def main():
    actual = {}
    totals = Counter()
    partial_files = 0
    partial_allocated_bytes = 0
    for path in sorted(RAW.rglob('*')):
        if not path.is_file():
            continue
        if path.suffix in {'.part', '.partial'} or 'incomplete' in path.relative_to(RAW).parts:
            partial_files += 1
            partial_allocated_bytes += path.stat().st_blocks * 512
            continue
        relative = str(path.relative_to(ROOT))
        with path.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        actual[relative] = dict(path=relative, bytes=path.stat().st_size, sha256=digest)
        totals[path.relative_to(RAW).parts[0]] += path.stat().st_size
    checked = 0
    partial_references_excluded = 0
    failures = []
    for path in sorted(META.rglob('*.json')) + sorted(META.rglob('*.jsonl')):
        if path.name == 'verification.json':
            continue
        if path.suffix == '.jsonl':
            data = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            if data and all('url' in row for row in data):
                data = list({row['url']: row for row in data}.values())
        else:
            data = json.loads(path.read_text())
        current_entries = {entry['path']: entry for entry in entries(data)}
        for entry in current_entries.values():
            expected = entry['path']
            if not expected.startswith('data/additional/'):
                continue
            if Path(expected).suffix in {'.part', '.partial'} or 'incomplete' in Path(expected).parts:
                partial_references_excluded += 1
                if not (ROOT / expected).exists():
                    failures.append(dict(manifest=str(path.relative_to(ROOT)), path=expected, reason='missing_partial_checkpoint_file'))
                continue
            checked += 1
            observed = actual.get(expected)
            if observed is None or observed['sha256'] != entry['sha256']:
                failures.append(dict(manifest=str(path.relative_to(ROOT)), path=expected, reason='missing' if observed is None else 'sha256_mismatch'))
    with (META / 'local-files.csv').open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=['path', 'bytes', 'sha256'])
        writer.writeheader()
        writer.writerows(actual.values())
    result = dict(checked_at=datetime.now(timezone.utc).isoformat(), files=len(actual), total_bytes=sum(totals.values()), bytes_by_dataset=dict(totals), incomplete_files_excluded=partial_files, incomplete_allocated_bytes=partial_allocated_bytes, incomplete_manifest_references_excluded=partial_references_excluded, manifest_references_checked=checked, failures=failures)
    (META / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
