from pathlib import Path
import zipfile,json
import pandas as pd

root=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
archive=next((root/'datasets/allsettlements/raw').glob('*csv.zip'))
with zipfile.ZipFile(archive) as z:
 member=next(x for x in z.namelist() if x.endswith('.csv') and not x.startswith('__MACOSX'))
 s=pd.read_csv(z.open(member),sep=';',dtype=str,keep_default_na=False,usecols=['object_level','object_name','oktmo','oktmo_new','region','mun_upper','mun_lower','settlement','population'])
m=pd.read_csv(out/'municipal-upper-paired-2024.csv',dtype=str,keep_default_na=False)
report={'input_rows':len(s),'levels':s.object_level.value_counts().to_dict(),'key_warning':'No code-prefix inference or name fuzzy matching; match only explicit full OKTMO codes at compatible administrative level. Census reference population is not municipal population in2024.'}
print('levels',report['levels'])
upper=s[s.object_level.eq('Муниципалитет верхнего уровня')].copy()
report['candidate_census_upper_rows']=len(upper)
report['candidate_level_labels']=sorted(upper.object_level.unique())
for key in ['oktmo','oktmo_new']:
 valid=upper[upper[key].str.fullmatch(r'\d{8}')].copy()
 counts=valid.groupby(key).size()
 unique=valid[valid[key].isin(counts[counts==1].index)]
 joined=m.merge(unique,left_on='oktmo',right_on=key,how='inner',suffixes=('_municipal','_census'),validate='many_to_one')
 name='object_name_census' if 'object_name_census' in joined else 'object_name'
 report[key]={'unique_upper_codes':len(unique),'ambiguous_codes':int((counts>1).sum()),'matched_municipal_2024':len(joined),'municipal_base':len(m),'share':len(joined)/len(m),'population_numeric':int(pd.to_numeric(joined.population,errors='coerce').notna().sum()),'examples':joined[['municipality_road',name,'oktmo_municipal' if 'oktmo_municipal' in joined else 'oktmo','population']].head(8).to_dict('records')}
 joined.to_csv(out/f'municipal-population-strict-{key}.csv',index=False)
(out/'settlement-join-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
