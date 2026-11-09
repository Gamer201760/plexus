"""Read official OOXML directly; preserve source rows and separate registered/care addresses."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, re, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'data/additional/medical-ugra'
META = Path(__file__).resolve().parent
URL = 'https://www.ofoms.ru/uploads/files/7eb202f860af4b038bcfba67ec9e03ea/trmo052026.xlsx'
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
FIELDS = {'C':'organization_registry_id','D':'organization_registry_number','E':'oms_code',
 'F':'organization_name','G':'organization_short_name','H':'organization_inn','K':'organization_oid',
 'L':'organization_type','P':'ownership','R':'registered_address','S':'registered_address_gar',
 'V':'care_address','W':'care_address_gar','X':'department_code','Y':'department_registry_code',
 'Z':'department_name','AA':'department_oid','AB':'care_types','AC':'care_conditions',
 'AD':'care_profiles','AE':'registry_inclusion_date','AF':'registry_exclusion_date','AG':'exclusion_reason'}

def write(name, rows):
    target=BASE/'derived'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.with_suffix('.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    with target.with_suffix('.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    src=BASE/'raw/trmo052026.xlsx'
    with zipfile.ZipFile(src) as z:
        strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)]
        sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        sheet_name=ET.fromstring(z.read('xl/workbook.xml')).find('s:sheets/s:sheet',NS).get('name')
        core=ET.fromstring(z.read('docProps/core.xml'))
        modified=core.find('{http://purl.org/dc/terms/}modified').text
        rows=[]
        for row in sheet.findall('.//s:row',NS):
            n=int(row.get('r'))
            if n<4:continue
            cells={}
            for c in row.findall('s:c',NS):
                v=c.find('s:v',NS)
                if v is not None:
                    cells[re.sub(r'\d','',c.get('r'))]=(strings[int(v.text)] if c.get('t')=='s' else v.text).strip()
            if not cells.get('C'):continue
            record={out:cells.get(col) or None for col,out in FIELDS.items()}
            record.update(source_excel_row=n, source_sheet=sheet_name, source_url=URL,
                source_file='data/additional/medical-ugra/raw/trmo052026.xlsx',registry_year=2026,
                longitude=None,latitude=None,coordinate_source=None,opening_hours=None,
                address_role='address_of_care_as_published',
                current_operational_status='not_verified',
                emergency_surgical_capability='not_verified')
            rows.append(record)
    assert len({r['source_excel_row'] for r in rows})==len(rows)
    assert all(r['care_address'] for r in rows)
    orgs={}; sites={}
    for r in rows:
        oid=r['organization_registry_id']
        if oid not in orgs:
            orgs[oid]={k:r[k] for k in ['organization_registry_id','oms_code','organization_name','organization_short_name','organization_inn','organization_oid','organization_type','ownership','registered_address','registered_address_gar','registry_inclusion_date','registry_exclusion_date','exclusion_reason','source_url']}
        key=(oid,r['care_address'])
        site=sites.setdefault(key,dict(site_id=hashlib.sha256('|'.join(key).encode()).hexdigest()[:16],
            organization_registry_id=oid,organization_name=r['organization_name'],care_address=r['care_address'],
            latitude=None,longitude=None,opening_hours=None,source_url=URL,source_rows=[],department_oids=[],address_gar_ids=[]))
        site['source_rows'].append(r['source_excel_row'])
        for field,source in [('department_oids','department_oid'),('address_gar_ids','care_address_gar')]:
            if r[source] and r[source] not in site[field]:site[field].append(r[source])
    write('care_records_2026',rows)
    write('organizations_2026',list(orgs.values()))
    site_rows=[{**r, 'source_rows':';'.join(map(str,r['source_rows'])),
        'department_oids':';'.join(r['department_oids']), 'address_gar_ids':';'.join(r['address_gar_ids'])} for r in sites.values()]
    write('care_locations_exact_address_2026',site_rows)
    profile=dict(registry_year=2026,workbook_modified_utc=modified,source_rows=len(rows),organizations=len(orgs),
        exact_organization_address_pairs=len(sites),rows_with_care_address=sum(bool(r['care_address']) for r in rows),
        rows_with_care_profiles=sum(bool(r['care_profiles']) for r in rows),
        rows_with_department_oid=sum(bool(r['department_oid']) for r in rows),
        rows_with_exclusion_date=sum(bool(r['registry_exclusion_date']) for r in rows),
        rows_with_coordinates=0,rows_with_opening_hours=0,
        caveat='Registry inclusion and profiles do not establish current opening, emergency capability, operating theatre, staffing or capacity. Exact address groups are not deduplicated physical buildings.')
    (META/'profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
    manifest=[]
    urls={'ofoms-register-index.html':'https://www.ofoms.ru/страницы/реестры-и-справочники',
          'city-ugut.html':'https://www.ofoms.ru/организации/city/ugut','trmo052026.xlsx':URL}
    for p in sorted(BASE.rglob('*')):
        if p.is_file():manifest.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(),url=urls.get(p.name),
            downloaded_or_generated_at_utc=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),
            kind='primary' if p.parent.name=='raw' else 'derived'))
    (META/'manifest.json').write_text(json.dumps({'files':manifest,'profile':profile},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(profile,ensure_ascii=False))

if __name__=='__main__':main()
