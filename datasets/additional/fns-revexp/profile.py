from pathlib import Path
from collections import Counter
from decimal import Decimal
import hashlib,json,zipfile,xml.etree.ElementTree as ET
import pyarrow as pa
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'data/additional/fns-revexp'
raw=BASE/'raw/data-20261025-structure-20180110.zip'
schema=pa.schema([(c,pa.string()) for c in ['inn','organization_name','document_id','document_date','as_of_date','source_member']]+[(c,pa.decimal128(19,2)) for c in ['income_rub','expense_rub']])
out=BASE/'derived/income_expense_2025.parquet'
counts=Counter(); years=Counter(); dates=Counter(); inns=set(); zeros=Counter(); total=0
with zipfile.ZipFile(raw) as z,pq.ParquetWriter(out,schema,compression='zstd') as w:
    inventory=[{'name':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size,'crc32':f'{i.CRC:08x}'} for i in z.infolist()]
    
    for i in z.infolist():
        if not i.filename.lower().endswith('.xml'):continue
        rows=[]
        with z.open(i) as f:
            for event,e in ET.iterparse(f,events=['end']):
                if e.tag!='Документ':continue
                n=e.find('СведНП');v=e.find('СведДохРасх')
                row=dict(inn=n.attrib['ИННЮЛ'],organization_name=n.attrib['НаимОрг'],document_id=e.attrib['ИдДок'],document_date=e.attrib['ДатаДок'],as_of_date=e.attrib['ДатаСост'],source_member=i.filename,income_rub=Decimal(v.attrib['СумДоход']),expense_rub=Decimal(v.attrib['СумРасход']))
                rows.append(row);total+=1;years[row['as_of_date']]+=1;dates[row['document_date']]+=1;inns.add(row['inn'])
                for c in ['income_rub','expense_rub']:
                    if row[c]==0:zeros[c]+=1
                e.clear()
        counts[i.filename]=len(rows)
        w.write_table(pa.Table.from_pylist(rows,schema=schema))
profile={'rows':total,'unique_inn':len(inns),'duplicate_inn_rows':total-len(inns),'columns':[{ 'name':f.name,'type':str(f.type)} for f in schema],'as_of_date_counts':years,'document_date_counts':dates,'zero_counts':zeros,'xml_members':len(counts),'uncompressed_bytes':sum(x['bytes'] for x in inventory),'zip_crc_and_xml_parse':'all members read to EOF successfully','financial_values':'Source reported decimal ruble amounts; no imputation or rescaling. Income is not revenue line 2110.','geography':'No direct geographic fields; join string INN to RFSD; INN prefix is tax registration, not plant location.'}
(BASE/'derived/profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2))
(BASE/'derived/archive_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
print(json.dumps(profile,ensure_ascii=False,indent=2))
