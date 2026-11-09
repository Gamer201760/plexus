from pathlib import Path
from datetime import datetime,timezone
import csv,json,zipfile,hashlib
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
ROAD='Y48106005'
SERVICE='Y48155002'
LEVEL='Муниципальное образование верхнего уровня'
DIM=['mest','vidres','okved2','strashod','okfs','vozr','indicator_unit','indicator_period']
MKEY=['region_id','region_name','mun_level','oktmo','oktmo_stable','year']+DIM

def output(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
def zip_csv(name):
    archive=next((ROOT/'datasets'/name/'raw').glob('*.zip'))
    with zipfile.ZipFile(archive) as z:
        member=next(x for x in z.namelist() if x.endswith('.csv') and not x.startswith('__MACOSX'))
        return pd.read_csv(z.open(member),sep=';',dtype=str,keep_default_na=False)
def numeric(df):
    raw=df['indicator_value'];v=pd.to_numeric(raw,errors='coerce')
    return v.mask(v.isin([-99999999,-77777777]))

municipal_path=ROOT/'datasets/municipal_transport/derived/municipal_transport_indicators.csv'
m=pd.read_csv(municipal_path,sep=';',dtype=str,keep_default_na=False)
m['number']=numeric(m)
m['year_int']=pd.to_numeric(m['year'],errors='coerce')
m['valid']=m['number'].between(0,100)
m['key_count']=m.groupby(MKEY+['indicator_code'],dropna=False)['indicator_value'].transform('size')
m['strict_valid']=m['valid'] & (m['key_count']==1)
output('municipal-audit.json',{'rows':len(m),'exact_duplicate_rows':int(m.drop(columns=['number','year_int','valid','key_count','strict_valid']).duplicated().sum()),'duplicate_key_rows':int((m['key_count']>1).sum()),'duplicate_key_groups':int(m.loc[m.key_count>1].groupby(MKEY+['indicator_code']).ngroups),'nonnumeric_tokens':m.loc[m['number'].isna(),'indicator_value'].value_counts().to_dict(),'out_of_range_rows':m.loc[m.number.notna() & ~m.valid,['indicator_code','region_name','municipality','oktmo','year','indicator_value','comment']].to_dict('records'),'comments':m['comment'].value_counts().to_dict(),'nontrivial_dimensions':{x:m[x].value_counts().to_dict() for x in DIM}})
dist=[]
for key,g in m.groupby(['indicator_code','mun_level','year']):
    v=g.loc[g.strict_valid,'number']
    dist.append({'indicator_code':key[0],'mun_level':key[1],'year':key[2],'rows':len(g),'valid_unique_rows':len(v),'numeric_missing':int(g.number.isna().sum()),'outside_0_100':int((g.number.notna() & ~g.valid).sum()),'ambiguous_key_rows':int((g.key_count>1).sum()),'zeros':int((v==0).sum()),'hundreds':int((v==100).sum()),'min':v.min(),'q25':v.quantile(.25),'median':v.median(),'q75':v.quantile(.75),'max':v.max()})
pd.DataFrame(dist).to_csv(OUT/'municipal-distributions.csv',index=False)

strict=m.loc[m.strict_valid].copy()
road=strict[strict.indicator_code==ROAD]
service=strict[strict.indicator_code==SERVICE]
paired=road.merge(service,on=MKEY,how='outer',suffixes=('_road','_service'),validate='one_to_one',indicator=True)
paired['has_both']=paired['_merge'].eq('both')
completeness=[]
for keys,g in paired.groupby(['region_id','region_name','mun_level','year']):
    v=g[g.has_both]
    completeness.append({'region_id':keys[0],'region_name':keys[1],'mun_level':keys[2],'year':keys[3],'observed_union':len(g),'road_valid':int(g['_merge'].ne('right_only').sum()),'service_valid':int(g['_merge'].ne('left_only').sum()),'paired_valid':len(v),'paired_share_of_observed_union':len(v)/len(g),'road_min':v['number_road'].min(),'road_max':v['number_road'].max(),'service_min':v['number_service'].min(),'service_max':v['number_service'].max(),'service_zero':int(v['number_service'].eq(0).sum()),'service_100':int(v['number_service'].eq(100).sum())})
comp=pd.DataFrame(completeness)
comp.to_csv(OUT/'municipal-paired-completeness.csv',index=False)
allpairs=paired[paired.has_both].copy()
latest=allpairs[(allpairs.year=='2024') & (allpairs.mun_level==LEVEL)].copy()
latest['road_compliance_pct']=100-latest['number_road']
latest['population_regular_service_pct']=100-latest['number_service']
cols=['region_id','region_name','mun_level','oktmo','oktmo_stable','year','municipality_road','municipality_service','number_road','number_service','road_compliance_pct','population_regular_service_pct','comment_road','comment_service','oktmo_history_road']
latest[cols].to_csv(OUT/'municipal-upper-paired-2024.csv',index=False)
coverage=comp[(comp.year.isin(['2023','2024','2025']))].groupby(['mun_level','year'])[['observed_union','road_valid','service_valid','paired_valid']].sum().reset_index()
coverage.to_csv(OUT/'municipal-year-level-summary.csv',index=False)

basekeys=['region_id','mun_level','oktmo','oktmo_stable']+DIM
balance=[]
for years in [['2023','2024'],['2022','2023','2024'],['2020','2021','2022','2023','2024']]:
    a=allpairs[(allpairs.year.isin(years)) & (allpairs.mun_level==LEVEL)]
    counts=a.groupby(basekeys)['year'].nunique()
    cohort=counts[counts==len(years)].reset_index()[basekeys]
    rows=a.merge(cohort,on=basekeys,how='inner',validate='many_to_one')
    balance.append({'years':years,'municipalities':len(cohort),'rows':len(rows),'regions':rows.region_name.nunique(),'key':'region_id, mun_level, oktmo, oktmo_stable + all dimensions; no administrative-code interpolation'})
    if len(years)==2:
        deltas=rows[rows.year==years[0]].merge(rows[rows.year==years[1]],on=basekeys,suffixes=('_2023','_2024'),validate='one_to_one')
        deltas['road_change_pp']=deltas.number_road_2024-deltas.number_road_2023
        deltas['service_change_pp']=deltas.number_service_2024-deltas.number_service_2023
        deltas[['region_name_2024','municipality_road_2024','oktmo','road_change_pp','service_change_pp','number_road_2023','number_road_2024','number_service_2023','number_service_2024']].to_csv(OUT/'municipal-balanced-changes-2023-2024.csv',index=False)
output('municipal-balanced-panels.json',balance)
examples=comp[(comp.year=='2024') & (comp.mun_level==LEVEL) & (comp.paired_valid>=10)].sort_values(['paired_share_of_observed_union','paired_valid'],ascending=False)
examples.to_csv(OUT/'municipal-region-options-2024.csv',index=False)

regional={name:zip_csv(name) for name in ['regional_transport','regional_grp','demography']}
regional_audit={}
for name,a in regional.items():
    a['number']=numeric(a)
    codekey=['object_oktmo','object_level','year','indicator_code','subsection','indicator_unit']
    key=['object_name']+codekey
    code_collisions=a[a.duplicated(codekey,False)][['object_name','object_oktmo','object_level']].drop_duplicates()
    code_collisions.to_csv(OUT/f'{name}-code-collisions.csv',index=False)
    a['key_count']=a.groupby(key)['indicator_value'].transform('size')
    a['valid']=a.number.notna() & a.key_count.eq(1)
    regional_audit[name]={'rows':len(a),'indicator_codes':a.indicator_code.nunique(),'years':sorted(a.year.unique()),'levels':a.object_level.value_counts().to_dict(),'sentinels':a.loc[pd.to_numeric(a.indicator_value,errors='coerce').isin([-99999999,-77777777]),'indicator_value'].value_counts().to_dict(),'nonnumeric':a.loc[pd.to_numeric(a.indicator_value,errors='coerce').isna(),'indicator_value'].value_counts().to_dict(),'duplicate_code_key_rows':int(a.duplicated(codekey,False).sum()),'duplicate_full_key_rows':int(a.key_count.gt(1).sum()),'indicator_units':a[['indicator_code','indicator_name','subsection','indicator_unit']].drop_duplicates().to_dict('records')}
    a.loc[a.key_count.gt(1)].to_csv(OUT/f'{name}-ambiguous-keys.csv',index=False)
    groups=[]
    for k,g in a[a.object_level=='Регион'].groupby(['year','indicator_code','indicator_name','subsection','indicator_unit']):
        groups.append({'year':k[0],'indicator_code':k[1],'indicator_name':k[2],'subsection':k[3],'indicator_unit':k[4],'rows':len(g),'region_definitions':g.object_name.nunique(),'valid':int(g.valid.sum()),'missing':int(g.number.isna().sum()),'minus99999999':int(pd.to_numeric(g.indicator_value,errors='coerce').eq(-99999999).sum()),'minus77777777':int(pd.to_numeric(g.indicator_value,errors='coerce').eq(-77777777).sum()),'min':g.loc[g.valid,'number'].min(),'max':g.loc[g.valid,'number'].max()})
    pd.DataFrame(groups).to_csv(OUT/f'{name}-indicator-year-coverage.csv',index=False)
output('regional-audit.json',regional_audit)

def disjoint(a):
    return a[~a.object_name.str.contains(r'\(с автономн',regex=True)]
transport=disjoint(regional['regional_transport']);grp=disjoint(regional['regional_grp']);demo=disjoint(regional['demography'])
cohorts=[]
for year in ['2023','2024']:
    t=transport[(transport.year==year)&(transport.object_level=='Регион')&transport.valid]
    g=grp[(grp.year==year)&(grp.object_level=='Регион')&grp.valid&(grp.indicator_code=='Y477110006')&(grp.subsection=='CD')]
    pop=demo[(demo.year==year)&(demo.object_level=='Регион')&demo.valid&(demo.indicator_code=='Y477010003')&(demo.subsection=='CD')]
    for code in sorted(t.indicator_code.unique()):
        tc=t[t.indicator_code==code]
        bykey=tc.groupby('object_oktmo').size()
        tc=tc[tc.object_oktmo.isin(bykey[bykey==1].index)]
        codes=set(tc.object_oktmo)&set(g.object_oktmo)
        populationcodes=codes&set(pop.object_oktmo)
        cohorts.append({'year':year,'transport_code':code,'transport_name':tc.indicator_name.iloc[0] if len(tc) else '', 'transport_valid_regions':len(tc),'grp_per_capita_valid_regions':len(g),'population_valid_regions':len(pop),'transport_grp_intersection':len(codes),'three_way_intersection':len(populationcodes)})
        if year=='2023' and code in ['Y477110295','Y477110296','Y477110292','Y477110294']:
            joined=tc.merge(g,on=['object_name','object_oktmo','object_level','year'],suffixes=('_transport','_grp'),validate='one_to_one')
            joined.to_csv(OUT/f'regional-2023-{code}-with-grp.csv',index=False)
pd.DataFrame(cohorts).to_csv(OUT/'regional-join-cohorts.csv',index=False)
output('summary.json',{'municipal_rows':len(m),'upper_paired_2024':len(latest),'upper_regions_2024':latest.region_name.nunique(),'year_level_summary':coverage.to_dict('records'),'balanced_panels':balance,'region_options_top':examples.head(12).to_dict('records'),'regional_cohorts':cohorts,'input_municipal_sha256':hashlib.sha256(municipal_path.read_bytes()).hexdigest(),'run_at':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'municipal_rows':len(m),'paired_2024_upper':len(latest),'regions':latest.region_name.nunique(),'year_level':coverage.to_dict('records'),'balanced':balance,'examples':examples.head(8).to_dict('records'),'regional_cohorts_2023':[x for x in cohorts if x['year']=='2023']},ensure_ascii=False,indent=2,default=str))
