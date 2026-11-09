from pathlib import Path
from collections import Counter
import pandas as pd
import zipfile,json,time
root=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
archive=next((root/'datasets/municipal_transport/raw').glob('*.zip'))
counts=Counter();zero_codes=Counter();target=Counter();zero_examples=[];start=time.time()
with zipfile.ZipFile(archive) as z:
 member=next(x for x in z.namelist() if x.endswith('.csv') and not x.startswith('__MACOSX'))
 for chunk in pd.read_csv(z.open(member),sep=';',dtype=str,keep_default_na=False,usecols=['indicator_code','indicator_name','indicator_value','year','mun_level'],chunksize=100000):
  v=pd.to_numeric(chunk.indicator_value,errors='coerce');zero=v.eq(0)
  counts['rows']+=len(chunk);counts['numeric']+=int(v.notna().sum());counts['numeric_zero']+=int(zero.sum());counts['empty']+=int(chunk.indicator_value.eq('').sum());counts['negative']+=int(v.lt(0).sum())
  zero_codes.update(chunk.loc[zero,'indicator_code'])
  if len(zero_examples)<10:zero_examples+=chunk.loc[zero,['indicator_code','indicator_name','indicator_value','year']].head(10-len(zero_examples)).to_dict('records')
  for code in ['Y48106005','Y48155002']:
   mask=chunk.indicator_code.eq(code);target[(code,'rows')]+=int(mask.sum());target[(code,'zero')]+=int((mask&zero).sum());target[(code,'hundred')]+=int((mask&v.eq(100)).sum());target[(code,'empty')]+=int((mask&chunk.indicator_value.eq('')).sum())
result={'counts':dict(counts),'zero_codes':dict(zero_codes),'target':{f'{c}:{m}':n for (c,m),n in target.items()},'zero_examples':zero_examples,'seconds':time.time()-start,'meaning':'Direct scan of ALL raw source CSV rows. Absence of zero observations does not establish suppression mechanism or that missing rows denote zero.'}
(out/'raw-zero-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
