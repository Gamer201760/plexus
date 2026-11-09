import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
BASE = ROOT / 'data/additional/stavropol'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def paragraphs(element):
    return [''.join(t.text or '' for t in p.findall('.//w:t',NS)) for p in element.findall('.//w:p',NS)]

def main():
    sources = {row['filename']:row for row in json.loads((META/'sources.json').read_text())}
    rows = []
    profile = []
    for path in sorted((BASE/'raw').glob('road-archive-*.docx')):
        with ZipFile(path) as archive:
            root = ET.fromstring(archive.read('word/document.xml'))
        source = sources[path.name]
        text = '\n'.join(paragraphs(root))
        (BASE/'derived'/(path.stem+'.txt')).write_text(text+'\n')
        count = 0
        tables = root.findall('.//w:tbl',NS)
        for table_number, table in enumerate(tables,1):
            for row_number, row in enumerate(table.findall('w:tr',NS),1):
                cells = ['\n'.join(paragraphs(cell)) for cell in row.findall('w:tc',NS)]
                spans = [cell.find('w:tcPr/w:gridSpan',NS) for cell in row.findall('w:tc',NS)]
                merges = [cell.find('w:tcPr/w:vMerge',NS) for cell in row.findall('w:tc',NS)]
                rows.append(dict(source_file=path.name,source_url=source['url'],municipality_source_label=source['label'],published_date=source['published_date'],table_number=table_number,row_number=row_number,cells_json=json.dumps(cells,ensure_ascii=False),column_spans_json=json.dumps([int(s.get('{'+NS['w']+'}val')) if s is not None else 1 for s in spans]),vertical_merges_json=json.dumps([m.get('{'+NS['w']+'}val','continue') if m is not None else None for m in merges]),normalized=False))
                count += 1
        profile.append(dict(filename=path.name,label=source['label'],tables=len(tables),table_rows=count,publication_date='2017-07-14',content_period='mixed historical periods; consult document text and footnotes'))
    with (BASE/'derived/road_archive_tables.csv').open('w',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result = dict(documents=len(profile),tables=sum(r['tables'] for r in profile),source_table_rows=len(rows),normalized_numeric_metrics=False,files=profile)
    (META/'road-archive-profile.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='files'})

if __name__ == '__main__':
    main()
